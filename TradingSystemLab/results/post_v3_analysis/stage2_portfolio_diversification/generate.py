#!/usr/bin/env python3
"""Build deterministic, artifact-only Stage 2 portfolio evidence.

Only immutable trade ledgers already authenticated by the Stage 1 manifest are
read.  No strategy package, market data, weighting, or selection logic is used.
"""
from __future__ import annotations

import csv, hashlib, itertools, json, math, statistics
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S1 = HERE.parent / "stage1_master_evidence"
PROVENANCE = "05e2cdb30ba8ec341403583d37e02712d179a6a7"
PASS1 = "POST_V3_STAGE_1_MASTER_EVIDENCE_AUDIT_PASSED"
UNIVERSES = {"v2": ("quarterly", ("Si", "CNY", "GD", "BR", "MIX", "NG")),
             "v3": ("perpetual", ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF"))}
# Authenticated market-history boundaries.  These are provenance, not properties
# of a strategy ledger, and consequently never depend on the first trade.
COVERAGE_START = {
    "v2": {"Si": date(2020, 1, 1), "GD": date(2020, 1, 1),
           "BR": date(2020, 1, 1), "MIX": date(2020, 1, 1),
           "NG": date(2020, 2, 3), "CNY": date(2022, 4, 21)},
    # Canonical v3 baseline manifests record these first source bars (the date
    # is identical for M30/H1 and all strategies).
    "v3": {"USDRUBF": date(2023, 1, 3), "CNYRUBF": date(2023, 1, 3),
           "GLDRUBF": date(2023, 7, 11), "IMOEXF": date(2023, 11, 14)},
}
STAGES = ("baseline", "walk_forward", "true_oos")
OUTPUTS = ("monthly_instrument_matrix.csv", "monthly_portfolio_summary.csv",
           "portfolio_stability_summary.csv", "instrument_stability_summary.csv",
           "pairwise_monthly_correlation.csv", "pairwise_co_loss_statistics.csv",
           "instrument_contribution_summary.csv", "leave_one_instrument_out.csv",
           "v2_v3_portfolio_comparison.csv", "true_oos_portfolio_summary.csv",
           "Stage_2_Portfolio_Diversification_Report.md")

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def f(x):
    if x is None or isinstance(x, float) and not math.isfinite(x): return "NA"
    if isinstance(x, bool): return str(x).lower()
    if isinstance(x, float): return format(x, ".12g")
    return str(x)
def write(name, fields, rows):
    with (HERE/name).open("w", newline="", encoding="utf-8") as h:
        w=csv.DictWriter(h, fieldnames=fields, lineterminator="\n"); w.writeheader()
        for r in rows: w.writerow({k:f(r.get(k)) for k in fields})
def mean(v): return statistics.fmean(v) if v else 0.0
def median(v): return statistics.median(v) if v else 0.0
def std(v): return statistics.stdev(v) if len(v)>1 else 0.0
def streak(v, pred):
    best=run=0
    for x in v: run=run+1 if pred(x) else 0; best=max(best,run)
    return best
def dd(v):
    eq=peak=worst=0.0
    for x in v: eq+=x; peak=max(peak,eq); worst=min(worst,eq-peak)
    return worst
def pct(n,d): return n/d if d else 0.0

def validate_stage1():
    audit=json.loads((S1/"audit_result.json").read_text())
    man=json.loads((S1/"manifest.json").read_text())
    if audit.get("status") != PASS1 or man.get("audit_status") != PASS1: raise RuntimeError("Stage 1 is not audit-passed")
    for name,digest in man["artifacts"].items():
        if sha(S1/name)!=digest: raise RuntimeError(f"modified Stage 1 artifact: {name}")
    for item in man["source_files_used"]:
        p=ROOT/item["path"]
        if not p.is_file() or sha(p)!=item["sha256"]: raise RuntimeError(f"modified Stage 1 source: {item['path']}")
    return man

def studies(man):
    files=[ROOT/x["path"] for x in man["source_files_used"] if x["path"].endswith(".csv")]
    for gen in UNIVERSES:
      for stage in STAGES:
       for strategy in ("T2","T3"):
        for tf in ("M30","H1"):
         if gen=="v2":
          token={"baseline":"/baseline_v2/","walk_forward":"/walk_forward_v2/","true_oos":"/true_oos_v2/"}[stage]
         else: token=f"/perpetual_v3/{stage}/"
         chosen=[]
         for p in files:
          s="/"+p.relative_to(ROOT).as_posix()
          if token in s and f"/{strategy}/" in s and f"/{tf}/" in s and (s.endswith("/trades.csv") or s.endswith("_trades.csv")): chosen.append(p)
         if not chosen: raise RuntimeError(f"missing authenticated ledgers {(gen,stage,strategy,tf)}")
         yield gen,stage,strategy,tf,sorted(set(chosen))

def rval(r,gen,stage):
    col={('v2','baseline'):'net_R',('v2','walk_forward'):'net_R_C1',('v2','true_oos'):'R_result',
         ('v3','baseline'):'net_R',('v3','walk_forward'):'net_R_C1',('v3','true_oos'):'R_result'}[(gen,stage)]
    if r.get(col) in (None,""): raise RuntimeError(f"missing canonical C1 {col}")
    return float(r[col])

def load(paths,gen,stage):
    out=[]
    for p in paths:
      with p.open(newline="",encoding="utf-8") as h:
       for r in csv.DictReader(h):
        inst=r.get("instrument") or r.get("symbol")
        t=datetime.fromisoformat(r["exit_time"]); pt=datetime.fromisoformat(r["entry_time"]) if t.hour==0 else t
        out.append((pt.strftime("%Y-%m"),inst,rval(r,gen,stage)))
    return out

def portfolio_metrics(vals):
    n=len(vals); pos=sum(x>0 for x in vals); neg=sum(x<0 for x in vals)
    return dict(months_observed=n,positive_months=pos,negative_months=neg,flat_months=n-pos-neg,
      positive_month_share=pct(pos,n),negative_month_share=pct(neg,n),total_net_R=sum(vals),
      mean_monthly_R=mean(vals),median_monthly_R=median(vals),monthly_R_std=std(vals),
      best_month_R=max(vals,default=0),worst_month_R=min(vals,default=0),
      longest_positive_month_streak=streak(vals,lambda x:x>0),longest_negative_month_streak=streak(vals,lambda x:x<0),
      monthly_downside_deviation=math.sqrt(mean([min(0,x)**2 for x in vals])),
      monthly_R_q25=statistics.quantiles(vals,n=4,method='inclusive')[0] if vals else 0,
      monthly_R_q75=statistics.quantiles(vals,n=4,method='inclusive')[2] if vals else 0,
      monthly_equity_max_drawdown_R=dd(vals))

def build():
    man=validate_stage1(); s1inst=list(csv.DictReader((S1/"instrument_statistics.csv").open()))
    s1idx={(r['generation'],r['lifecycle_stage'],r['strategy'],r['timeframe'],r['instrument']):r for r in s1inst}
    matrix=[]; portfolios=[]; stability=[]; inststats=[]; corrs=[]; coloss=[]; contributions=[]; loo=[]
    study_data={}
    for gen,stage,strategy,tf,paths in studies(man):
      future,universe=UNIVERSES[gen]; trades=load(paths,gen,stage)
      unknown={i for _,i,_ in trades}-set(universe)
      if unknown: raise RuntimeError(f"unexpected instruments {unknown}")
      months=sorted({m for m,_,_ in trades})
      grouped=defaultdict(list)
      for m,i,r in trades: grouped[m,i].append(r)
      cells={}; rows=[]
      for m in months:
       for i in universe:
        coverage_start=COVERAGE_START[gen][i]; coverage_month=coverage_start.strftime("%Y-%m")
        if m<coverage_month: available=False; status="NOT_YET_AVAILABLE"; vals=[]; net=0.0
        else:
         available=True; vals=grouped[m,i]; net=sum(vals); status="AVAILABLE" if vals else "NO_TRADES"
        rec=dict(generation=gen,futures_type=future,lifecycle_stage=stage,strategy=strategy,timeframe=tf,**{"YYYY-MM":m},instrument=i,
          coverage_start_date=coverage_start.isoformat(),instrument_available=available,
          partial_coverage_month=available and m==coverage_month and coverage_start.day!=1,
          coverage_status=status,trades=len(vals),net_R=net,
          positive_month=net>0,negative_month=net<0,zero_month=available and net==0)
        rows.append(rec); matrix.append(rec); cells[m,i]=rec
      pvals=[]
      for m in months:
       active=[cells[m,i] for i in universe if cells[m,i]['instrument_available']]; trading=[x for x in active if x['trades']]
       nets=[x['net_R'] for x in active]; total=sum(nets); pvals.append(total)
       best=max(active,key=lambda x:(x['net_R'],x['instrument'])) if active else None
       worst=min(active,key=lambda x:(x['net_R'],x['instrument'])) if active else None
       portfolios.append(dict(generation=gen,futures_type=future,lifecycle_stage=stage,strategy=strategy,timeframe=tf,**{"YYYY-MM":m},
        active_instruments=len(active),trading_instruments=len(trading),total_trades=sum(x['trades'] for x in active),portfolio_net_R=total,
        positive_instruments=sum(x['net_R']>0 for x in active),negative_instruments=sum(x['net_R']<0 for x in active),zero_instruments=sum(x['net_R']==0 for x in active),
        best_instrument=best['instrument'] if best else 'NA',best_instrument_R=best['net_R'] if best else 0,
        worst_instrument=worst['instrument'] if worst else 'NA',worst_instrument_R=worst['net_R'] if worst else 0,
        max_single_instrument_positive_contribution=max([0]+[x['net_R'] for x in active]),max_single_instrument_negative_contribution=min([0]+[x['net_R'] for x in active]),
        same_sign_loss_count=len(active) if active and all(x['net_R']<0 for x in active) else 0,
        same_sign_gain_count=len(active) if active and all(x['net_R']>0 for x in active) else 0))
      pm=portfolio_metrics(pvals); prs=portfolios[-len(months):]
      offset=sum(r['positive_instruments']>0 and r['negative_instruments']>0 for r in prs)
      rescue=sum(r['negative_instruments']>0 and r['portfolio_net_R']>0 for r in prs)
      reduction=sum(r['portfolio_net_R']<0 and r['positive_instruments']>0 for r in prs)
      extra=dict(months_all_active_instruments_negative=sum(r['same_sign_loss_count']>0 for r in prs),months_all_active_instruments_positive=sum(r['same_sign_gain_count']>0 for r in prs),
       max_number_simultaneously_negative=max((r['negative_instruments'] for r in prs),default=0),average_number_negative_per_month=mean([r['negative_instruments'] for r in prs]),
       max_number_simultaneously_positive=max((r['positive_instruments'] for r in prs),default=0),average_number_positive_per_month=mean([r['positive_instruments'] for r in prs]),
       offset_months=offset,offset_month_share=pct(offset,len(months)),loss_rescue_months=rescue,loss_rescue_share=pct(rescue,sum(r['negative_instruments']>0 for r in prs)),
       loss_reduction_months=reduction,all_negative_months=sum(r['same_sign_loss_count']>0 for r in prs),all_positive_months=sum(r['same_sign_gain_count']>0 for r in prs))
      base=dict(generation=gen,futures_type=future,lifecycle_stage=stage,strategy=strategy,timeframe=tf,instruments='|'.join(universe)); stability.append(base|pm|extra)
      study_data[(gen,stage,strategy,tf)]=(universe,months,cells,base|pm|extra)
      # Instrument summaries and drawdown-episode attribution.
      equity=peak=0.; ddmonths=[]
      for m,v in zip(months,pvals): equity+=v; peak=max(peak,equity); ddmonths.append(equity<peak)
      for i in universe:
       avail=[cells[m,i] for m in months if cells[m,i]['instrument_available']]; vals=[x['net_R'] for x in avail]
       src=s1idx.get((gen,stage,strategy,tf,i),{})
       bestn=sum(cells[m,i]['instrument_available'] and cells[m,i]['instrument']==portfolios[-len(months)+k]['best_instrument'] for k,m in enumerate(months))
       worstn=sum(cells[m,i]['instrument_available'] and cells[m,i]['instrument']==portfolios[-len(months)+k]['worst_instrument'] for k,m in enumerate(months))
       neg=sum(x for x in vals if x<0); pos=sum(x for x in vals if x>0)
       rec=base|dict(instrument=i,months_observed=len(vals),months_with_trades=sum(x['trades']>0 for x in avail),total_trades=sum(x['trades'] for x in avail),total_net_R=sum(vals),
        PF=float(src['PF']) if src and src['PF']!='NA' else None,expectancy_R=float(src['expectancy_R']) if src else None,positive_months=sum(x>0 for x in vals),negative_months=sum(x<0 for x in vals),
        positive_month_share=pct(sum(x>0 for x in vals),len(vals)),mean_monthly_R=mean(vals),median_monthly_R=median(vals),monthly_R_std=std(vals),best_month_R=max(vals,default=0),worst_month_R=min(vals,default=0),
        longest_negative_month_streak=streak(vals,lambda x:x<0),contribution_to_portfolio_total_R=pct(sum(vals),sum(pvals)),contribution_to_positive_R=pct(pos,sum(max(0,x) for x in pvals)),
        contribution_to_negative_R=pct(neg,sum(min(0,x) for x in pvals)),share_of_portfolio_losses=pct(abs(neg),sum(abs(min(0,cells[m,j]['net_R'])) for m in months for j in universe if cells[m,j]['instrument_available'])),
        number_of_months_in_which_instrument_was_worst=worstn,number_of_months_in_which_instrument_was_best=bestn)
       inststats.append(rec)
       othloss=[m for m in months if sum(cells[m,j]['net_R'] for j in universe if j!=i and cells[m,j]['instrument_available'])<0]
       contributions.append(base|dict(instrument=i,total_net_R=sum(vals),positive_R_contribution=pos,negative_R_contribution=neg,worst_month_R=min(vals,default=0),
        monthly_equity_drawdown_contribution=sum(cells[m,i]['net_R'] for k,m in enumerate(months) if ddmonths[k] and cells[m,i]['instrument_available']),
        months_contributing_to_portfolio_drawdown=sum(ddmonths[k] and cells[m,i]['instrument_available'] and cells[m,i]['net_R']<0 for k,m in enumerate(months)),
        months_offsetting_portfolio_loss=sum(cells[m,i]['net_R']>0 for m in othloss if cells[m,i]['instrument_available']),offset_R_during_other_instrument_losses=sum(max(0,cells[m,i]['net_R']) for m in othloss if cells[m,i]['instrument_available'])))
      # Pairwise calculations: both-available months only.
      for a,b in itertools.combinations(sorted(universe),2):
       ov=[m for m in months if cells[m,a]['instrument_available'] and cells[m,b]['instrument_available']]; av=[cells[m,a]['net_R'] for m in ov]; bv=[cells[m,b]['net_R'] for m in ov]
       pear=statistics.correlation(av,bv) if len(av)>1 and std(av)>0 and std(bv)>0 else None; cov=statistics.covariance(av,bv) if len(av)>1 else None
       same=sum((x>0 and y>0) or (x<0 and y<0) or (x==0 and y==0) for x,y in zip(av,bv)); opp=sum(x*y<0 for x,y in zip(av,bv)); bn=sum(x<0 and y<0 for x,y in zip(av,bv)); bp=sum(x>0 and y>0 for x,y in zip(av,bv))
       partial=sum(cells[m,a]['partial_coverage_month'] or cells[m,b]['partial_coverage_month'] for m in ov)
       key=base|dict(instrument_a=a,instrument_b=b,overlapping_months=len(ov),partial_overlap_months=partial)
       corrs.append(key|dict(pearson_monthly_R=pear,covariance_monthly_R=cov,same_sign_months=same,opposite_sign_months=opp,same_sign_share=pct(same,len(ov)),opposite_sign_share=pct(opp,len(ov)),both_negative_months=bn,both_positive_months=bp,sample_flag='ADEQUATE' if len(ov)>=6 else 'LOW_SAMPLE'))
       both=[x+y for x,y in zip(av,bv) if x<0 and y<0]; opposite=[x+y for x,y in zip(av,bv) if x*y<0]
       an=sum(x<0 for x in av); bneg=sum(x<0 for x in bv)
       coloss.append(key|dict(instrument_a_negative_months=an,instrument_b_negative_months=bneg,both_negative_months=bn,either_negative_months=sum(x<0 or y<0 for x,y in zip(av,bv)),both_positive_months=bp,opposite_sign_months=opp,
        probability_both_negative_given_a_negative=pct(bn,an),probability_both_negative_given_b_negative=pct(bn,bneg),average_combined_R_when_both_negative=mean(both),worst_combined_R_when_both_negative=min(both) if both else 0,average_combined_R_when_opposite_sign=mean(opposite)))
      for removed in universe:
       vals=[sum(cells[m,i]['net_R'] for i in universe if i!=removed and cells[m,i]['instrument_available']) for m in months]; lm=portfolio_metrics(vals)
       loo.append(base|dict(original_instrument_count=len(universe),removed_instrument=removed,remaining_instruments='|'.join(i for i in universe if i!=removed),**{k:lm[k] for k in ('months_observed','total_net_R','mean_monthly_R','median_monthly_R','positive_month_share','monthly_R_std','worst_month_R','monthly_equity_max_drawdown_R','longest_negative_month_streak')},
        delta_total_R_vs_full=lm['total_net_R']-pm['total_net_R'],delta_positive_month_share=lm['positive_month_share']-pm['positive_month_share'],delta_monthly_std=lm['monthly_R_std']-pm['monthly_R_std'],delta_worst_month_R=lm['worst_month_R']-pm['worst_month_R'],delta_monthly_equity_DD=lm['monthly_equity_max_drawdown_R']-pm['monthly_equity_max_drawdown_R']))
    identity=['generation','futures_type','lifecycle_stage','strategy','timeframe']
    write('monthly_instrument_matrix.csv',identity+['YYYY-MM','instrument','coverage_start_date','instrument_available','partial_coverage_month','coverage_status','trades','net_R','positive_month','negative_month','zero_month'],matrix)
    write('monthly_portfolio_summary.csv',identity+['YYYY-MM','active_instruments','trading_instruments','total_trades','portfolio_net_R','positive_instruments','negative_instruments','zero_instruments','best_instrument','best_instrument_R','worst_instrument','worst_instrument_R','max_single_instrument_positive_contribution','max_single_instrument_negative_contribution','same_sign_loss_count','same_sign_gain_count'],portfolios)
    stabfields=identity+['instruments']+[k for k in stability[0] if k not in identity+['instruments']]; write('portfolio_stability_summary.csv',stabfields,stability)
    write('instrument_stability_summary.csv',identity+['instrument']+[k for k in inststats[0] if k not in identity+['instruments','instrument']],inststats)
    write('instrument_contribution_summary.csv',identity+['instrument']+[k for k in contributions[0] if k not in identity+['instruments','instrument']],contributions)
    pairbase=identity+['instrument_a','instrument_b','overlapping_months','partial_overlap_months']; write('pairwise_monthly_correlation.csv',pairbase+[k for k in corrs[0] if k not in pairbase+['instruments']],corrs); write('pairwise_co_loss_statistics.csv',pairbase+[k for k in coloss[0] if k not in pairbase+['instruments']],coloss)
    write('leave_one_instrument_out.csv',identity+['removed_instrument']+[k for k in loo[0] if k not in identity+['instruments','removed_instrument']],loo)
    comparisons=[]
    for stage in STAGES:
     for strategy in ('T2','T3'):
      for tf in ('M30','H1'):
       a=next(x for x in stability if (x['generation'],x['lifecycle_stage'],x['strategy'],x['timeframe'])==('v2',stage,strategy,tf)); b=next(x for x in stability if (x['generation'],x['lifecycle_stage'],x['strategy'],x['timeframe'])==('v3',stage,strategy,tf))
       r=dict(strategy=strategy,timeframe=tf,lifecycle_stage=stage,v2_futures_type='quarterly',v3_futures_type='perpetual')
       mapping={'instruments':'instruments','months_observed':'months_observed','total_net_R':'total_net_R','positive_month_share':'positive_month_share','mean_monthly_R':'mean_monthly_R','median_monthly_R':'median_monthly_R','monthly_R_std':'monthly_R_std','worst_month_R':'worst_month_R','monthly_equity_max_drawdown_R':'monthly_equity_max_drawdown_R','longest_negative_month_streak':'longest_negative_month_streak','loss_rescue_share':'loss_rescue_share','all_negative_months':'all_negative_months'}
       for prefix,x in [('v2',a),('v3',b)]:
        for outk,ink in mapping.items(): r[f'{prefix}_{outk}']=x[ink]
       r['comparability']='PARTIALLY_COMPARABLE'; comparisons.append(r)
    write('v2_v3_portfolio_comparison.csv',list(comparisons[0]),comparisons)
    oos=[]
    for s in stability:
     if s['lifecycle_stage']!='true_oos': continue
     cs=[x for x in contributions if all(x[k]==s[k] for k in ('generation','lifecycle_stage','strategy','timeframe'))]
     oos.append(dict(generation=s['generation'],strategy=s['strategy'],timeframe=s['timeframe'],instruments=s['instruments'],months=s['months_observed'],total_R=s['total_net_R'],positive_month_share=s['positive_month_share'],median_monthly_R=s['median_monthly_R'],monthly_std=s['monthly_R_std'],worst_month=s['worst_month_R'],monthly_equity_DD=s['monthly_equity_max_drawdown_R'],loss_rescue_share=s['loss_rescue_share'],synchronized_loss_months=s['all_negative_months'],largest_positive_contributor=max(cs,key=lambda x:(x['positive_R_contribution'],x['instrument']))['instrument'],largest_negative_contributor=min(cs,key=lambda x:(x['negative_R_contribution'],x['instrument']))['instrument']))
    write('true_oos_portfolio_summary.csv',list(oos[0]),oos)
    make_report(stability,corrs,coloss,inststats,loo,comparisons)
    hashes={x:sha(HERE/x) for x in OUTPUTS}; rows={x:sum(1 for _ in (HERE/x).open())-1 for x in OUTPUTS if x.endswith('.csv')}
    manifest={'status':'POST_V3_STAGE_2_PORTFOLIO_DIVERSIFICATION_COMPLETE','audit_status':'PENDING_INDEPENDENT_AUDIT','stage1_canonical_provenance':PROVENANCE,'stage1_audit_status':PASS1,
      'stage1_files_used':['master_study_comparison.csv','instrument_statistics.csv','direction_statistics.csv','chronological_monthly_statistics.csv','calendar_month_of_year_statistics.csv','yearly_statistics.csv','quarterly_statistics.csv','monthly_stability_summary.csv','comparability_matrix.csv','manifest.json','audit_result.json'],
      'stage1_artifact_sha256':man['artifacts'],'source_sha256':{x['path']:x['sha256'] for x in man['source_files_used']},'output_sha256':hashes,'row_counts':rows,
      'controls':{'no_strategy_execution':True,'no_optimization':True,'no_ranking':True,'no_production_selection':True,'no_trade_modification':True,'no_risk_weighting':True,'deterministic_rerun':True,
                  'coverage_dates_verified':False,'availability_not_derived_from_first_trade':False,'partial_coverage_months_explicit':False,'pairwise_overlap_coverage_verified':False}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')

def make_report(stability,corrs,coloss,inststats,loo,comp):
    o=["# Stage 2 — Portfolio / Diversification Analysis","","## 1. Scope","","Artifact-only descriptive analysis of Stage 1-authenticated committed C1 ledgers. No strategy execution, optimization, ranking, weighting, production selection, or trade modification was performed.","",
    "## 2. Research history","","v2 is the quarterly-futures diversification experiment (Si, CNY, GD, BR, MIX, NG). v3 is the perpetual-futures stability replication (USDRUBF, CNYRUBF, GLDRUBF, IMOEXF). Cross-generation results are `PARTIALLY_COMPARABLE`.","",
    "## Historical Availability Contract","","Availability describes authenticated instrument history, not the first strategy trade. Canonical v2 starts are Si: 2020-01-01; GD: 2020-01-01; BR: 2020-01-01; MIX: 2020-01-01; NG: 2020-02-03; CNY: 2022-04-21. Canonical v3 starts from source provenance are USDRUBF: 2023-01-03; CNYRUBF: 2023-01-03; GLDRUBF: 2023-07-11; IMOEXF: 2023-11-14.","","A pre-coverage month is `NOT_YET_AVAILABLE`; an available zero-trade month is `NO_TRADES`; a month with trades is `AVAILABLE`. The first available calendar month is retained and `partial_coverage_month=true` when coverage starts after its first day. Pairwise samples include `NO_TRADES` as zero R, exclude `NOT_YET_AVAILABLE`, and report overlaps containing either instrument's partial month.","",
    "## 3. Portfolio monthly behavior","","The tables preserve generation, lifecycle, strategy, and timeframe. TRUE OOS is presented first below, then Walk Forward; baseline is context only.",""]
    for stage in ('true_oos','walk_forward','baseline'):
     o += [f"### {stage}","","| generation | study | months | total R | positive share | std | worst | monthly equity DD |","|---|---:|---:|---:|---:|---:|---:|---:|"]
     for x in stability:
      if x['lifecycle_stage']==stage:o.append(f"| {x['generation']} | {x['strategy']}/{x['timeframe']} | {x['months_observed']} | {x['total_net_R']:.4f} | {x['positive_month_share']:.3f} | {x['monthly_R_std']:.4f} | {x['worst_month_R']:.4f} | {x['monthly_equity_max_drawdown_R']:.4f} |")
     o.append("")
    o += ["## 4. Cross-instrument relationships","","Correlation uses only months where both instruments are historically available. A zero is retained for a valid available no-trade month; pre-availability months are excluded. `LOW_SAMPLE` means fewer than six overlaps. Co-loss, opposite-sign, offset, rescue, and reduction fields are descriptive protection evidence, not quality labels.","",
    "## 5. Instrument stability","","`instrument_stability_summary.csv` keeps profitability (R, PF, expectancy), monthly stability, and diversification contribution separate. `instrument_contribution_summary.csv` identifies positive/negative contribution, drawdown-episode contribution, and offsets. These facts are not DROP/KEEP decisions.","",
    "## 6. Quarterly versus perpetual","","Does v3 appear more stable? Evidence is mixed and study-specific. Supporting cases are those where v3 has a higher positive-month share, smaller dispersion/worst month/monthly-equity drawdown, shorter losing streak, fewer synchronized losses, or more loss rescue. Complications are visible wherever those signs reverse. v3 also has fewer instruments and different periods and coverage, so higher standalone profitability cannot establish construction superiority. Every comparison remains `PARTIALLY_COMPARABLE`.","",
    "## 7. T2 versus T3","","T2 and T3 remain separate in every artifact. Their distributions may be compared descriptively, but no strategy rank or winner is produced.","",
    "## 8. M30 versus H1","","M30 and H1 remain separate in every artifact. Differences in monthly dispersion, synchronized loss, and offset behavior are evidence only, not selection.","",
    "## 9. Leave-one-out diagnostics","","Each row removes exactly one instrument from the full equal-unit-R universe. Deltas report the factual change in total R, positive-month share, monthly standard deviation, worst month, and monthly-equity drawdown. They do not prescribe elimination.","",
    "## 10. Stage 3 implications","","Stage 3 should investigate why repeated bad months occur and whether losses cluster by session, direction, holding time, MAE/MFE, or exit reason. None of those trade-anatomy hypotheses is tested here.","",
    "## Definitions","","* Portfolio monthly R is the unweighted sum of canonical instrument R.","* `AVAILABLE` has trades; `NO_TRADES` is an available month with zero trades; `NOT_YET_AVAILABLE` precedes canonical authenticated instrument coverage and is excluded from pair calculations.","* Offset: at least one positive and one negative instrument. Rescue: a loss exists but portfolio R is positive. Reduction: portfolio R remains negative while a positive instrument offsets part of losses.","* All-negative/all-positive requires every currently available instrument to have that strict sign. `same_sign_*_count` is the available-instrument count in such a month, otherwise zero.","* `monthly_equity_max_drawdown_R` is peak-to-trough drawdown of cumulative monthly R, not trade-level drawdown."]
    (HERE/'Stage_2_Portfolio_Diversification_Report.md').write_text('\n'.join(o)+'\n')

if __name__=='__main__': build()
