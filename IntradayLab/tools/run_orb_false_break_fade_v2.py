#!/usr/bin/env python3
"""Pre-registered v2 ORB fade research: causal ATR + non-destructive M15 veto.

Strict v1 files are read-only. This standalone run is a conditional set of
independent trading-day experiments, never a continuous broker account curve.
"""
import argparse
from collections import Counter, deque
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import hashlib
import json

import orb_false_break_fade_replay as baseline
import run_orb_false_break_fade as reporting
import run_orb_false_break_fade_daywise as daywise
import audit_orb_false_break_fade as original_oracle

LAB=Path(__file__).resolve().parents[1]
CONFIG=LAB/"config/stage2_orb_false_break_fade_m5_v2_research.json"
ORIGINAL=LAB/"config/stage2_orb_false_break_fade_m5_v1.json"
OUT=LAB/"results/stage2_orb_false_break_fade_m5_v2_research"
FIVE=timedelta(minutes=5)
D=Decimal


def causal_atr14(rows):
    """All observed M5 up to current bar, no overnight/gap synthetic TR."""
    tr=deque(maxlen=14)
    out={}
    prev_at=prev_close=None
    for at in sorted(rows):
        r=rows[at]
        if not baseline.valid(r):
            prev_at=prev_close=None
            continue
        op,high,low,close,volume=r
        true_range=high-low
        if prev_at is not None and at==prev_at+FIVE:
            true_range=max(true_range,abs(high-prev_close),abs(low-prev_close))
        tr.append(true_range)
        prev_at,prev_close=at,close
        if len(tr)==14:
            out[at]=sum(tr,D(0))/14
    return out


def independent_atr_at(rows,at):
    """Independent backwards reconstruction, no production deque reuse."""
    stamps=sorted(t for t,b in rows.items() if t<=at and b is not None and b[4]>0)
    if at not in rows or at not in stamps or len(stamps)<14:
        return None
    observed=stamps[-14:]
    values=[]
    for idx,t in enumerate(observed):
        o,h,l,c,v=rows[t]
        tr=h-l
        # For the first TR we still need its preceding candle if adjacent.
        preceding=rows.get(t-FIVE)
        if preceding is not None and preceding[4]>0:
            tr=max(tr,abs(h-preceding[3]),abs(l-preceding[3]))
        values.append(tr)
    return sum(values,D(0))/14


def independent_m15_close(rows, s):
    """Recompute the latest complete exact M15 from raw M5 at signal close."""
    close_time=s["signal_at"]
    aligned=close_time.replace(minute=(close_time.minute//15)*15,
                               second=0,microsecond=0)
    parent_start=aligned-timedelta(minutes=15)
    windows=baseline.windows(close_time.date())
    eligible=next((w for w in windows
                   if w[0]<=parent_start and close_time<=w[1]),None)
    if eligible is None:
        return None
    t=parent_start
    while t<close_time:
        if not baseline.valid(rows.get(t)):
            return None
        t+=FIVE
    return rows[parent_start+2*FIVE][3]


def risk_tick_diagnostic(trades, symbol):
    """Historical cost/Stop-size diagnostics only; never filter by risk band."""
    bands={"LE_2_TICKS":[],"GT_2_LE_5_TICKS":[],"GT_5_TICKS":[]}
    for t in trades:
        if not t.get("model_filled") or t.get("risk") is None:
            continue
        ticks=t["risk"]/baseline.tick(symbol,t["entry_at"])
        name=("LE_2_TICKS" if ticks<=2 else
              "GT_2_LE_5_TICKS" if ticks<=5 else "GT_5_TICKS")
        bands[name].append(t)
    return {name:{
        "fills":len(group),
        "closed":sum(t["status"]=="CLOSED" for t in group),
        "unknown":sum(t["status"]=="UNKNOWN" for t in group),
        "c1_cost_to_gross_risk_ratio_mean":(
            sum((t["cost_c1"]/t["risk"] for t in group
                 if t["status"]=="CLOSED"),D(0))/
            sum(t["status"]=="CLOSED" for t in group)
            if any(t["status"]=="CLOSED" for t in group) else None
        ),
        "closed_only_diagnostic_c1":reporting.summary(group,"c1")
    } for name,group in bands.items()}


def derive_filters(original_records,rows,symbol):
    """Annotate all common ORB episodes BEFORE choosing one of four arms."""
    atrs=causal_atr14(rows)
    enriched=[]
    for old in original_records:
        s=dict(old)
        s["v2_original_base_reason"]=old["base_reason"]
        if old["base_reason"]=="SIGNAL":
            at=old["sweep_start"]
            a=atrs.get(at)
            independent=independent_atr_at(rows,at)
            if a!=independent:
                raise AssertionError("Independent ATR mismatch %s %s" %(symbol,at))
            checked_parent=independent_m15_close(rows,old)
            if checked_parent!=old.get("m15_close"):
                raise AssertionError("Independent M15 parent mismatch %s %s" %(symbol,at))
            step=baseline.tick(symbol,at)
            s["v2_atr14"]=a
            s["v2_atr_ready"]=a is not None
            s["v2_atr_pass"]=a is not None and old["sweep_size"]>=max(step,D(".30")*a)
            parent=old.get("m15_close")
            # The M15 has to be an exact, already-completed parent (v1 oracle).
            rejected = (parent is not None and (
                (old["direction"] == -1 and parent>old["or_high"]) or
                (old["direction"] == 1 and parent<old["or_low"])
            ))
            s["v2_m15_context_available"]=parent is not None
            s["v2_m15_breakout_accepted_veto"]=rejected
        enriched.append(s)
    return enriched


def select_architecture(events, spec):
    result=[]
    for original in events:
        r=dict(original)
        r["v2_filter_reason"]="SIGNAL" if r["base_reason"]=="SIGNAL" else r["base_reason"]
        if r["base_reason"]=="SIGNAL":
            if spec["atr"] and not r["v2_atr_ready"]:
                r["base_reason"]=r["v2_filter_reason"]="V2_ATR_UNAVAILABLE"
            elif spec["atr"] and not r["v2_atr_pass"]:
                r["base_reason"]=r["v2_filter_reason"]="V2_ATR_SWEEP_TOO_SMALL"
            elif spec["mtf"] and r["v2_m15_breakout_accepted_veto"]:
                r["base_reason"]=r["v2_filter_reason"]="V2_M15_ACCEPTED_BREAKOUT_VETO"
            elif spec["mtf"] and not r["v2_m15_context_available"]:
                r["v2_filter_reason"]="M15_NO_CONTEXT_NEUTRAL_ALLOWED"
        result.append(r)
    return result


def comparisons(trades,prior):
    now=daywise.compact_metrics(trades)
    p=daywise.compact_metrics(prior)
    return {
        "v1_daywise_fills":p["model_fills"],
        "v1_daywise_closed":p["closed"],
        "v1_daywise_unknown":p["unknown"],
        "v2_daywise_fills":now["model_fills"],
        "v2_daywise_closed":now["closed"],
        "v2_daywise_unknown":now["unknown"],
        "v1_c1_diagnostic_PF":p["conditional_closed_only_c1"]["net_PF"],
        "v2_c1_diagnostic_PF":now["conditional_closed_only_c1"]["net_PF"],
        "v1_c1_diagnostic_expectancy_R":p["conditional_closed_only_c1"]["expectancy_R"],
        "v2_c1_diagnostic_expectancy_R":now["conditional_closed_only_c1"]["expectancy_R"],
        "NOT_comparable_as_live_portfolio":True
    }


def run(data_root, output_dir=OUT):
    if output_dir.resolve()!=OUT.resolve():
        raise ValueError("Only isolated IntradayLab v2 directory is writable")
    config=json.loads(CONFIG.read_text())
    v1=json.loads(ORIGINAL.read_text())
    if (config["id"]!="stage2_orb_false_break_fade_m5_v2_research"
            or config["source_ref"]!=v1["source_ref"]
            or config["instruments"]!=v1["instruments"]
            or config["architectures"]!=v1["architectures"]):
        raise ValueError("V2_SOURCE_OR_ARCHITECTURE_CONTRACT")
    raw,read_receipts=baseline.read_source(data_root,v1)
    independent_raw=original_oracle.source(data_root,v1)
    if raw!=independent_raw:
        raise AssertionError("Two raw input readers disagree")
    all_signals=[];all_trades=[];all_days=[];months=[];audit_rows=0
    metrics={};cmp={};eligibility=[]
    for symbol in config["instruments"]:
        original_events, _,coverage=baseline.base_signals(symbol,raw[symbol])
        expected=original_oracle.oracle_signals(symbol,independent_raw[symbol])
        bad=original_oracle.compare_rows(original_events,expected,
                                        original_oracle.SIGNAL_KEYS,"original_events")
        if bad:
            raise AssertionError("v1 ORB base disagrees with oracle: "+str(bad[:3]))
        enriched=derive_filters(original_events,raw[symbol],symbol)
        base_count=sum(x["base_reason"]=="SIGNAL" for x in enriched)
        for arch,spec in config["architectures"].items():
            v2events=select_architecture(enriched,spec)
            # External event gate handles v2 filters; identical original
            # position-entry-exit engine handles all actual entries.
            ss,tt,dd,checked=daywise.evaluate_symbol(symbol,raw[symbol],
                    v2events,arch,{"atr":False,"mtf":False},audit=True)
            _,prior_tt,_,_ =daywise.evaluate_symbol(symbol,raw[symbol],
                    original_events,arch,spec,audit=True)
            if arch=="A_BASE":
                strict_keys=("signal_id","status","model_filled","entry_at",
                             "entry_price","stop","take","exit_price",
                             "exit_reason","net_c1","net_c2","net_R_c1")
                v2_control=sorted(tuple(t.get(k) for k in strict_keys)
                                  for t in tt)
                v1_control=sorted(tuple(t.get(k) for k in strict_keys)
                                  for t in prior_tt)
                if v2_control!=v1_control:
                    raise AssertionError("A BASE must be identical in both daywise engines")
            audit_rows+=checked
            key=arch+"_"+symbol
            metrics[key]=daywise.compact_metrics(tt)
            metrics[key].update({
                "risk_tick_bands":risk_tick_diagnostic(tt,symbol),
                "common_reclaim_signals":base_count,
                "atr14_v2_ready":sum(x.get("v2_atr_ready",False) for x in enriched),
                "atr14_v2_pass":sum(x.get("v2_atr_pass",False) for x in enriched),
                "m15_veto":sum(x.get("v2_m15_breakout_accepted_veto",False)
                                    for x in enriched),
                "accepted_signals":sum(x["base_reason"]=="SIGNAL" for x in v2events),
                "rejection_reasons":dict(Counter(
                   x["v2_filter_reason"] for x in v2events
                   if x.get("v2_original_base_reason")=="SIGNAL")),
                "research_type":"INDEPENDENT_DAYS_COUNTERFACTUAL_AFTER_UNKNOWN"
            })
            cmp[key]=comparisons(tt,prior_tt)
            all_signals.extend(ss);all_trades.extend(tt);all_days.extend(dd)
            months+=daywise.monthly(symbol,arch,tt,coverage)
            eligibility.append({"architecture":arch,"instrument":symbol,
                               "common_reclaim_signals":base_count,
                               "atr_ready":metrics[key]["atr14_v2_ready"],
                               "atr_pass":metrics[key]["atr14_v2_pass"],
                               "m15_veto":metrics[key]["m15_veto"],
                               "accepted_signals":metrics[key]["accepted_signals"],
                               "model_fills":metrics[key]["model_fills"],
                               "closed":metrics[key]["closed"],
                               "unknown":metrics[key]["unknown"]})
    output_dir.mkdir(parents=True,exist_ok=True)
    reporting.write_csv(output_dir/"signals.csv",all_signals)
    reporting.write_csv(output_dir/"trades.csv",all_trades)
    reporting.write_csv(output_dir/"days.csv",all_days)
    reporting.write_csv(output_dir/"monthly.csv",months)
    reporting.write_csv(output_dir/"eligibility.csv",eligibility)
    baseline.dump(output_dir/"metrics.json",metrics)
    baseline.dump(output_dir/"comparison_v1_daywise_vs_v2.json",cmp)
    baseline.dump(output_dir/"audit.json",{
        "status":"INDEPENDENT_ORACLE_PASS",
        "v2_atr_reconstructed_independently":True,
        "v2_m15_parent_reconstructed_from_raw_m5":True,
        "stop_risk_tick_strata_reported_without_filtering":True,
        "v1_orb_signals_checked_by_separate_oracle":True,
        "v2_selected_trades_checked_by_separate_state_machine":True,
        "trade_signal_rows_independently_compared":audit_rows,
        "annual_pf_net_dd_claim":None,
        "v1_results_rewritten":False,
        "real_broker_position_reconciled":False,
        "research_after_unknown":"COUNTERFACTUAL_ONLY"
    })
    baseline.dump(output_dir/"input_provenance.json",{
        "data_repo":config["source_repository"],
        "source_ref":config["source_ref"],
        "prefixes":read_receipts,
        "config_sha256":hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "previous_v1_config_sha256":hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),
        "all_2024_plus_bytes_read":0
    })
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output_dir.iterdir() if p.is_file()}
    baseline.dump(output_dir/"sha256.json",hashes)
    print(json.dumps({
        "status":"RESEARCH_DIAGNOSTIC_REQUIRES_EXTERNAL_ACCEPTANCE",
        "scenarios":len(metrics),
        "monthly_rows":len(months),
        "oracle":"PASS",
        "comparison_v1_daywise_vs_v2":cmp,
        "result_path":str(output_dir),
    },default=baseline.encode,ensure_ascii=False,indent=2))
    return metrics


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root",type=Path,required=True)
    args=parser.parse_args()
    run(args.data_root.resolve())
