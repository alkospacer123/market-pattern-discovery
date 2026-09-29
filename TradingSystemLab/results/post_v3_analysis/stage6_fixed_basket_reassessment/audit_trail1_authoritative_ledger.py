"""Fail-closed independent audit of the corrected A--F TRAIL1 trade ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from . import generate_reassessment as frozen
from . import materialize_trail1_authoritative_ledger as producer

HERE = Path(__file__).resolve().parent
TOL = 1e-10


def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _dd(v: pd.Series) -> float:
    curve = pd.concat([pd.Series([0.0]), pd.to_numeric(v).reset_index(drop=True).cumsum()], ignore_index=True)
    return float((curve - curve.cummax()).min())
def _pf(v: pd.Series) -> float:
    v = pd.to_numeric(v); losses = abs(v[v < 0].sum())
    return float(v[v > 0].sum() / losses) if len(v) >= 2 and losses else np.nan

def _equal_frame(left: pd.DataFrame, right: pd.DataFrame, label: str) -> None:
    if list(left.columns) != list(right.columns) or left.shape != right.shape: raise RuntimeError(f"{label}_SHAPE_OR_SCHEMA")
    for col in left:
        if pd.api.types.is_numeric_dtype(right[col]):
            if not np.allclose(pd.to_numeric(left[col]), pd.to_numeric(right[col]), atol=TOL, rtol=0, equal_nan=True): raise RuntimeError(f"{label}_{col}")
        elif col == "instrument_contribution":
            for a, b in zip(left[col], right[col]):
                aa, bb = json.loads(a), json.loads(b)
                if aa.keys() != bb.keys() or not np.allclose(list(aa.values()), list(bb.values()), atol=TOL, rtol=0): raise RuntimeError(f"{label}_{col}")
        elif not left[col].fillna("").astype(str).equals(right[col].fillna("").astype(str)): raise RuntimeError(f"{label}_{col}")

def independently_rebuild(ledger: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    registry = frozen.lifecycle_registry(); monthly_rows=[]; yearly_rows=[]
    views = frozen.annual_views()
    for basket, (members, path) in producer.BDF.items():
        source=ledger[ledger.instrument.isin(members)].copy(); source["exit"]=pd.to_datetime(source.exit_time, utc=True)
        for life in frozen.LIFECYCLES:
            subset=source[source.lifecycle == life]
            starts=[]; ends=[]
            for symbol in members:
                row=registry[(registry.lifecycle == life)&(registry.instrument == symbol)]
                starts.append(pd.to_datetime(row.start_timestamp, utc=True).min()); ends.append(pd.to_datetime(row.end_timestamp, utc=True).max())
            cumulative=0.0
            for period in pd.period_range(min(starts).tz_localize(None).to_period("M"), max(ends).tz_localize(None).to_period("M"), freq="M"):
                available=[s for s in members if pd.to_datetime(registry[(registry.lifecycle==life)&(registry.instrument==s)].start_timestamp,utc=True).min().tz_localize(None).to_period("M") <= period <= pd.to_datetime(registry[(registry.lifecycle==life)&(registry.instrument==s)].end_timestamp,utc=True).max().tz_localize(None).to_period("M")]
                if not available: continue
                g=subset[(subset.exit.dt.year==period.year)&(subset.exit.dt.month==period.month)]
                contrib={s:float(g.loc[g.instrument==s,"net_R_C1"].sum()) for s in available}; net=sum(contrib.values()); cumulative += net
                monthly_rows.append({"basket":basket,"path":path,"lifecycle":life,"year":period.year,"month":period.month,"available_instruments":"+".join(available),"trades":len(g),"net_R":net,"PF":_pf(g.net_R_C1),"cumulative_net_R":cumulative,"instrument_contribution":json.dumps(contrib,sort_keys=True),"month_sign":"POSITIVE" if net>0 else "NEGATIVE" if net<0 else "ZERO"})
        mon=pd.DataFrame(monthly_rows)
        for life,year,label in views:
            g=source[(source.lifecycle==life)&(source.exit.dt.year==year)].sort_values(["exit","instrument","trade_id"],kind="mergesort")
            m=mon[(mon.basket==basket)&(mon.lifecycle==life)&(mon.year==year)]; net=float(g.net_R_C1.sum()); drawdown=_dd(g.net_R_C1)
            contrib={s:float(g.loc[g.instrument==s,"net_R_C1"].sum()) for s in frozen.SYMBOLS}
            yearly_rows.append({"basket":basket,"path":path,"lifecycle":life,"year":year,"period_label":label,"trades":len(g),"net_R":net,"PF":_pf(g.net_R_C1),"expectancy_R":float(g.net_R_C1.mean()) if len(g) else 0.,"max_DD_R":drawdown,"recovery":net/abs(drawdown) if drawdown else np.nan,"win_rate":float((g.net_R_C1>0).mean()) if len(g) else 0.,"median_trade_R":float(g.net_R_C1.median()) if len(g) else 0.,"positive_months":int((m.net_R>0).sum()),"available_months":len(m),"positive_month_share":float((m.net_R>0).mean()),"worst_month_R":float(m.net_R.min()),"best_month_R":float(m.net_R.max()),"median_monthly_R":float(m.net_R.median()),"monthly_std_R":float(m.net_R.std(ddof=0)),"longest_negative_month_streak":frozen.consecutive_negative(m.net_R),**{f"{s}_net_R":contrib[s] for s in frozen.SYMBOLS}})
    return pd.DataFrame(yearly_rows), pd.DataFrame(monthly_rows)

def audit(data_root: Path, ledger_path: Path = HERE / producer.LEDGER, manifest_path: Path = HERE / producer.MANIFEST) -> dict:
    manifest=json.loads(manifest_path.read_text()); frozen.authenticate(data_root)
    identities={"starting_main_sha":producer.STARTING_MAIN_SHA,"t3_sha":frozen.T3_SHA,"parameter_sha":frozen.PARAM_SHA,"trail1_implementation_sha":frozen.TRAIL_SHA,"data_commit":frozen.DATA_COMMIT}
    for key,value in identities.items():
        if manifest.get(key)!=value: raise RuntimeError(f"IDENTITY_{key}_INVALID")
    if _sha(HERE.parent/"stage5_structural_validation/stage5_trail1_execution.py") != frozen.TRAIL_SHA: raise RuntimeError("TRAIL1_SHA_INVALID")
    if _sha(HERE.parent/"stage5_structural_validation/canonical_lifecycle_registry.csv") != manifest["lifecycle_registry_sha"]: raise RuntimeError("LIFECYCLE_REGISTRY_INVALID")
    for rel,digest in manifest["protected_stage5_and_stage6_1_to_6_5_hashes"].items():
        if _sha(HERE.parent/rel)!=digest: raise RuntimeError(f"PROTECTED_ARTIFACT_CHANGED:{rel}")
    for rel,digest in manifest["existing_af_hashes_before"].items():
        if _sha(HERE.parent/rel)!=digest: raise RuntimeError(f"AF_ARTIFACT_CHANGED:{rel}")
    auth=frozen.authenticate(data_root)
    if auth["source_hashes"] != manifest["raw_h1_source_hashes"]: raise RuntimeError("RAW_SOURCE_HASHES_INVALID")
    first,h1=frozen.raw_replays(data_root)
    replay1=first["TRAIL1"].sort_values(["lifecycle","fold_id","exit_time","instrument","trade_id"],kind="mergesort").reset_index(drop=True)
    if h1["TRAIL1"][0] != h1["TRAIL1"][1]: raise RuntimeError("REPLAY_NONDETERMINISTIC")
    ledger=pd.read_csv(ledger_path,keep_default_na=False)
    serialized_replay = pd.read_csv(StringIO(replay1.to_csv(index=False, lineterminator="\n", float_format=producer.FLOAT_FORMAT)), keep_default_na=False)
    _equal_frame(ledger,serialized_replay,"COMMITTED_LEDGER_REPLAY")
    if _sha(ledger_path)!=manifest["committed_file_sha256"] or producer.ledger_event_hash(ledger)!=manifest["event_hash"]: raise RuntimeError("LEDGER_IDENTITY_INVALID")
    year,mon=independently_rebuild(ledger)
    expected_y=pd.read_csv(HERE/"basket_yearly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    expected_m=pd.read_csv(HERE/"basket_monthly_metrics.csv").query("basket in ['B','D','F']").reset_index(drop=True)
    _equal_frame(year,expected_y,"FROZEN_YEARLY"); _equal_frame(mon,expected_m,"FROZEN_MONTHLY")
    if manifest.get("stage7_executed") is not False or manifest.get("old_trail1_reconciliation_used") or manifest.get("trail1_digest_used"): raise RuntimeError("SCOPE_VIOLATION")
    return {"status":"AUTHORITATIVE_TRAIL1_LEDGER_INDEPENDENT_AUDIT_PASSED","row_count":len(ledger),"event_hash":producer.ledger_event_hash(ledger),"replay_hashes":h1["TRAIL1"],"checks":{"source_authentication":True,"replay_twice":True,"committed_ledger_exact":True,"yearly_trade_count_net_pf_expectancy_dd_recovery_win_median_contribution":True,"monthly_trade_count_net_pf_cumulative_contribution":True,"protected_evidence_unchanged":True,"stage7_not_executed":True}}

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--data-root",type=Path); args=p.parse_args()
    if args.data_root is None:
        from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
        args.data_root,_=resolve_data_root()
    print(json.dumps(audit(args.data_root.resolve()),indent=2,sort_keys=True))
if __name__ == "__main__": main()
