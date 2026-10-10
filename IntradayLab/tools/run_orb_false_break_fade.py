#!/usr/bin/env python3
"""Run exactly sixteen preregistered economic scenarios, C2 same-fill replacement."""
import argparse
from collections import Counter
import csv
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

import orb_false_break_fade_replay as engine
import audit_orb_false_break_fade as independent

D=Decimal
OUT=engine.LAB/'results/stage2_orb_false_break_fade_m5_v1'


def write_csv(path,rows):
    columns=sorted(set().union(*(r.keys() for r in rows))) if rows else ['signal_id']
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns);w.writeheader()
        w.writerows({k:('' if v is None else str(v)) for k,v in r.items()} for r in rows)


def summary(trades,cost):
    closed=sorted((t for t in trades if t['status']=='CLOSED'),key=lambda t:(t['resolved_at'],t['signal_id']))
    pnl=[t['net_'+cost] for t in closed]; rs=[t['net_R_'+cost] for t in closed]
    positive=sum((x for x in pnl if x>0),D(0)); negative=-sum((x for x in pnl if x<0),D(0))
    wins=[x for x in pnl if x>0];losses=[x for x in pnl if x<0]
    cash=peak=dd=D(0)
    for r in rs:
        cash+=r;peak=max(peak,cash);dd=max(dd,peak-cash)
    return dict(closed_trades=len(closed),gross=sum((t['gross'] for t in closed),D(0)),cost=sum((t['cost_'+cost] for t in closed),D(0)),net=sum(pnl,D(0)),net_R=sum(rs,D(0)),net_PF=positive/negative if negative else None,PF_no_losses=bool(wins and not losses),expectancy_price=sum(pnl,D(0))/len(pnl) if pnl else None,expectancy_R=sum(rs,D(0))/len(rs) if rs else None,
                win_rate=D(len(wins))/len(pnl) if pnl else None,average_win_price=sum(wins,D(0))/len(wins) if wins else None,average_loss_price=sum(losses,D(0))/len(losses) if losses else None,realized_reward_risk=(sum(wins,D(0))/len(wins))/(-sum(losses,D(0))/len(losses)) if wins and losses else None,max_drawdown_R=dd if rs else None,worst_trade_R=min(rs) if rs else None,largest_winner_share=max(wins)/positive if wins else None,top3_winners_share=sum(sorted(wins,reverse=True)[:3],D(0))/positive if wins else None,exit_reasons=dict(Counter(t['exit_reason'] for t in closed)))


def reports(config,signals,trades,daily,coverage):
    metrics={};monthly=[]; cov=[];comparisons=[]
    for arch in config['architectures']:
        for symbol in config['instruments']:
            key=arch+'_'+symbol
            ss=[s for s in signals if s['architecture']==arch and s['instrument']==symbol]
            tt=[t for t in trades if t['architecture']==arch and t['instrument']==symbol]
            cc=[c for c in coverage if c['instrument']==symbol]
            dd=[d for d in daily if d['instrument']==symbol]
            observed=sum(d['observed'] for d in dd);fill=[t for t in tt if t['model_filled']]
            unknown=[t for t in tt if t['status']=='UNKNOWN']
            incomplete=any(c['status']!='COMPLETE' for c in cc)
            full=not unknown and not incomplete
            diagnostics={cost:summary(tt,cost) for cost in ('c1','c2')}
            signs=Counter()
            for month in range(1,13):
                name=f'2023-{month:02d}'
                mt=[t for t in tt if str(t['signal_at']).startswith(name)]
                ms=[s for s in ss if s['date'].startswith(name)]
                mc=[c for c in cc if c['date'].startswith(name)]
                md=[d for d in dd if d['date'].startswith(name)]
                obs=sum(d['observed'] for d in md);u=sum(t['status']=='UNKNOWN' for t in mt)
                ds={cost:summary(mt,cost) for cost in ('c1','c2')}
                covered=sum(c['valid_bars'] for c in mc)>0
                missing=sum(c['missing_bars']+c['zero_volume_bars'] for c in mc)
                complete=covered and all(c['status']=='COMPLETE' for c in mc) and not u
                value=ds['c1']['net']
                sign='NO_COVERAGE' if not covered else 'POSITIVE' if value>0 else 'NEGATIVE' if value<0 else 'ZERO'
                signs[sign]+=1
                classification='NO_COVERAGE' if not covered else 'UNKNOWN' if u else 'PARTIAL_COVERAGE' if not complete else 'NO_TRADES' if not mt else 'COMPLETE'
                monthly.append(dict(architecture=arch,instrument=symbol,month=name,classification=classification,diagnostic_sign=sign,observed_days=obs,expected_days=len(md),raw_signals=sum(s['base_reason']=='SIGNAL' for s in ms),admitted_orders=sum(s['order_admitted'] for s in ms),model_fills=sum(t['model_filled'] for t in mt),closed_trades=ds['c1']['closed_trades'],unknown=u,missing_bars=missing,
                                    full_net_c1=ds['c1']['net'] if complete else None,full_PF_c1=ds['c1']['net_PF'] if complete else None,full_DD_R_c1=ds['c1']['max_drawdown_R'] if complete else None,
                                    diagnostic_net_c1=value,diagnostic_net_R_c1=ds['c1']['net_R'],diagnostic_PF_c1=ds['c1']['net_PF'],diagnostic_net_c2=ds['c2']['net'],diagnostic_PF_c2=ds['c2']['net_PF'],diagnostic_expectancy_R_c1=ds['c1']['expectancy_R'],diagnostic_expectancy_R_c2=ds['c2']['expectancy_R']))
            entry_days={t['entry_at'].date() for t in fill}
            m=dict(architecture=arch,instrument=symbol,annual_complete=full,annual_net_c1=diagnostics['c1']['net'] if full else None,annual_net_PF_c1=diagnostics['c1']['net_PF'] if full else None,annual_max_DD_R_c1=diagnostics['c1']['max_drawdown_R'] if full else None,
                   annual_net_c2=diagnostics['c2']['net'] if full else None,annual_net_PF_c2=diagnostics['c2']['net_PF'] if full else None,annual_max_DD_R_c2=diagnostics['c2']['max_drawdown_R'] if full else None,closed_only_diagnostic=diagnostics,
                   observed_trading_days=observed,expected_days_after_inception=len(dd),or_days=sum(d['or_available'] for d in dd),raw_signals=sum(s['base_reason']=='SIGNAL' for s in ss),sweep_attempts=sum(s['direction']!=0 for s in ss),admitted_orders=sum(s['order_admitted'] for s in ss),model_fills=len(fill),closed_trades=sum(t['status']=='CLOSED' for t in tt),unknown=len(unknown),unknown_entry_orders=sum(not t['model_filled'] for t in unknown),unknown_exposed_trades=sum(t['model_filled'] for t in unknown),long_fills=sum(t['direction']==1 for t in fill),short_fills=sum(t['direction']==-1 for t in fill),entry_days=len(entry_days),days_without_entries=observed-len(entry_days),fills_per_observed_day=D(len(fill))/observed if observed else None,
                   reasons=dict(Counter(s['reason'] for s in ss if s['reason'])),exit_reasons=dict(Counter(t['exit_reason'] for t in tt)),diagnostic_month_signs=dict(signs),classification='INCONCLUSIVE_UNRESOLVED' if not full else 'NO_ECONOMIC_BASELINE_PASS')
            metrics[key]=m
            cov.append(dict(architecture=arch,instrument=symbol,first_source=config['inputs'][symbol]['first'],source_rows_2023=config['inputs'][symbol]['rows_2023'],expected_days_after_inception=len(dd),observed_days=observed,pre_inception_days=sum(c['status']=='PRE_INCEPTION' for c in cc),missing_bars=sum(c['missing_bars'] for c in cc),zero_volume_bars=sum(c['zero_volume_bars'] for c in cc),complete_days=sum(c['status']=='COMPLETE' for c in cc),incomplete_days=sum(c['status']=='INCOMPLETE' for c in cc),no_OR_days=sum(not d['or_available'] for d in dd),unknown_entries=m['unknown_entry_orders'],unknown_exposed=m['unknown_exposed_trades'],annual_complete=full,annual_net=None if not full else diagnostics['c1']['net']))
    for before,after in (('A_BASE','B_IND'),('A_BASE','C_MTF'),('B_IND','D_MTF_IND'),('C_MTF','D_MTF_IND')):
        for symbol in config['instruments']:
            a=metrics[before+'_'+symbol];b=metrics[after+'_'+symbol];x=a['closed_only_diagnostic']['c1'];y=b['closed_only_diagnostic']['c1']
            aa={t['signal_id'] for t in trades if t['architecture']==before and t['instrument']==symbol and t['model_filled']};bb={t['signal_id'] for t in trades if t['architecture']==after and t['instrument']==symbol and t['model_filled']}
            comparisons.append(dict(instrument=symbol,comparison=before+'->'+after,before_fills=a['model_fills'],after_fills=b['model_fills'],delta_fills=b['model_fills']-a['model_fills'],common_fills=len(aa&bb),before_only_fills=len(aa-bb),after_only_fills=len(bb-aa),delta_diagnostic_net_R=y['net_R']-x['net_R'],before_diagnostic_PF=x['net_PF'],after_diagnostic_PF=y['net_PF'],delta_diagnostic_expectancy_R=y['expectancy_R']-x['expectancy_R'] if x['expectancy_R'] is not None and y['expectancy_R'] is not None else None,annual_evidence_complete=a['annual_complete'] and b['annual_complete']))
    return metrics,monthly,cov,comparisons


def independent_metrics_audit(metrics,monthly,trades,signals,coverage):
    errors=[]
    for key,m in metrics.items():
        ledger=[t for t in trades if t['architecture']==m['architecture'] and t['instrument']==m['instrument']]
        for cost in ('c1','c2'):
            closed=[t for t in ledger if t['status']=='CLOSED'];amounts=[t['direction']*(t['exit_price']-t['entry_price'])-(1 if cost=='c1' else 2)*(independent.grid(t['instrument'],t['entry_at'])+independent.grid(t['instrument'],t['exit_interval_start'])) for t in closed]
            a=m['closed_only_diagnostic'][cost];net=sum(amounts,D(0));gain=sum((x for x in amounts if x>0),D(0));loss=-sum((x for x in amounts if x<0),D(0))
            expected={'closed_trades':len(closed),'net':net,'net_R':sum((x/t['risk'] for x,t in zip(amounts,closed)),D(0)),'net_PF':gain/loss if loss else None,'expectancy_R':sum((x/t['risk'] for x,t in zip(amounts,closed)),D(0))/len(closed) if closed else None}
            for k,v in expected.items():
                if a[k]!=v:errors.append((key,cost,k))
        mm=[r for r in monthly if r['architecture']==m['architecture'] and r['instrument']==m['instrument']]
        if len(mm)!=12 or {x['month'] for x in mm}!={f'2023-{i:02d}' for i in range(1,13)}:errors.append((key,'MONTHS'))
        for row in mm:
            subset=[t for t in ledger if str(t['signal_at']).startswith(row['month'])]
            for cost in ('c1','c2'):
                total=sum((t['net_'+cost] for t in subset if t['status']=='CLOSED'),D(0))
                if total!=row['diagnostic_net_'+cost]:errors.append((key,row['month'],cost))
            if sum(t['model_filled'] for t in subset)!=row['model_fills'] or sum(t['status']=='UNKNOWN' for t in subset)!=row['unknown']:errors.append((key,row['month'],'COUNTS'))
        if not m['annual_complete'] and any(m[k] is not None for k in ('annual_net_c1','annual_net_PF_c1','annual_max_DD_R_c1')):errors.append((key,'ANNUAL_NULL'))
    return {'status':'PASS' if not errors else 'FAIL','discrepancies':errors,'monthly_rows':len(monthly)}


def fmt(x,n=3):return 'null' if x is None else f'{x:.{n}f}'


def report(metrics,comparisons,audit,config):
    lines=['# ORB_FALSE_BREAK_FADE_M5 — Stage 2 four architectures','', '**INCONCLUSIVE_UNRESOLVED — no economic Baseline PASS.** Complete fixed-rule 2023 replay finished; incomplete historical coverage and unresolved paths prevent full annual claims. No parameters changed after P&L.','',f"Base main `{config['base_main']}`; pre-P&L freeze `{engine.FREEZE}`. Fixed A BASE / B ATR14 / C completed M15 / D both; exactly16 C1 scenarios, C2 replacement on identical fills.",'', 'All PF/expectancy/month signs in the following table are **closed-only diagnostics**, not complete annual performance. Expectancy is normalized Net R per closed trade; raw quote units remain separate by instrument. Annual Net/PF/DD are null in every incomplete scenario. Intrabar outcomes have an interval, not an invented exact fill time.','', '| Architecture | Instrument | Fills / closed / unknown | C1 PF | C1 exp R | C2 PF | C2 exp R | + / − / 0 / uncovered months |','|---|---|---:|---:|---:|---:|---:|---|']
    for m in metrics.values():
        a=m['closed_only_diagnostic']['c1'];b=m['closed_only_diagnostic']['c2'];s=m['diagnostic_month_signs']
        lines.append(f"| {m['architecture']} | {m['instrument']} | {m['model_fills']} / {m['closed_trades']} / {m['unknown']} | {fmt(a['net_PF'])} | {fmt(a['expectancy_R'])} | {fmt(b['net_PF'])} | {fmt(b['expectancy_R'])} | {s.get('POSITIVE',0)} / {s.get('NEGATIVE',0)} / {s.get('ZERO',0)} / {s.get('NO_COVERAGE',0)} |")
    lines+=['','Month signs describe known closed cohorts even when the monthly classification is UNKNOWN/PARTIAL_COVERAGE. `monthly_report.csv` contains all192 rows and full-null versus diagnostic fields. GLD starts July11, IMOEX November14; uncovered months are never zero-profit months. Unexpected halts/missing rows remain gaps; no synthetic prices.','', '## Factor contribution (fixed architecture comparisons)','', '| Change | Instrument | Fills before → after | Diagnostic ΔNet R | Diagnostic PF before → after |','|---|---|---:|---:|---:|']
    for x in comparisons:
        lines.append(f"| {x['comparison']} | {x['instrument']} | {x['before_fills']} → {x['after_fills']} | {fmt(x['delta_diagnostic_net_R'])} | {fmt(x['before_diagnostic_PF'])} → {fmt(x['after_diagnostic_PF'])} |")
    lines+=['','ATR14 and M15 change admission to shared first-attempt episodes; rejected attempts are not recycled. Trade membership may also differ because occupancy/UNKNOWN blocking differs. D must be assessed against both individual factors, not selected for maximum PF. Filter attribution is descriptive 2023 evidence and is not causal proof of improvement or permission for optimization.','', '## Execution and limitations','', 'Signal = reclaim close; one full subsequent M5 closes; submit and hypothetical exact boundary Open fill. Waiting-bar prices provide no extra confirmation. Stop is known history extreme plus/minus dated tick, TP1.5 gross R outward grid; no old T10/T15/FAST or 3R net rule. Resident Stop-first; entry-bar TP forbidden; adverse Stop gaps use worse Open; favorable Take gaps receive no improvement. Time=60 calendar minutes or B−5 Session Flat. Missing entry=UNKNOWN, missing exposure=UNKNOWN; fail-closed per architecture/instrument through end2023. Unknowns never become NONFILL/zero P&L.','', 'CNY tick0.01 before 2023-09-27 19:00 MSK and0.001 thereafter. Strategy windows finish18:50, so the exact transition is validated synthetically; real post-switch fills use0.001. No M1 accessed. Both production and independent source readers read exact2023 prefixes and zero2024+ bytes.','', '## Audit and integrity','',f"Independent algorithm audit: **{audit['status']}**, {audit['checked_fields']} compared fields, {len(audit['discrepancies'])} discrepancies. Raw-source backward features and chronological order/position oracle import no production strategy/outcome functions. Metric/month reconciliation saved separately. External independent review is still pending.",'', 'Protected root trees and every existing main IntradayLab blob are compared unchanged in the manifest. New files only; source repository remains read-only. Frozen pre-P&L fingerprint and implementation SHA are in manifest. Deterministic repeated artifact hashes and synthetic/full IntradayLab tests are saved in validation artifacts.','', '## Decision','', '**INCONCLUSIVE_UNRESOLVED.** No full-year Net PF≥1.6 evidence or accepted stable economic plateau can be claimed from incomplete/unknown histories. Closed-only results may diagnose weakness or a promising subset; they do not establish Baseline PASS. Historical Cycle18 selected2026 CNY M1 survivor is a different data/execution experiment and not verification here. Stop at one Draft PR: no merge, Stage3, next strategy,2024 WF,2025+ TRUE OOS or LIVE.']
    return '\n'.join(lines)+'\n'


def run(root,out):
    cfg=json.loads(engine.CONFIG.read_text());fingerprint=hashlib.sha256(engine.CONFIG.read_bytes()).hexdigest()
    if fingerprint!=engine.CONFIG.with_suffix('.sha256').read_text().split()[0]:raise ValueError('CONFIG_CHANGED')
    git=lambda *a:subprocess.check_output(['git','-C',str(engine.LAB.parent),*a],text=True).strip()
    if git('show',engine.FREEZE+':IntradayLab/config/'+engine.CONFIG.name)!=engine.CONFIG.read_text().strip():raise ValueError('FREEZE_MISMATCH')
    raw,receipts=engine.read_source(root,cfg);base={};signals=[];trades=[];daily=[];coverage=[]
    for symbol in cfg['instruments']:
        events,dd,cc=engine.base_signals(symbol,raw[symbol]);base[symbol]=events;daily+=dd;coverage+=cc
        for arch,spec in cfg['architectures'].items():
            ss,tt=engine.replay(symbol,raw[symbol],events,arch,spec);signals+=ss;trades+=tt
    # Fresh, independent reader: no reuse of production parsed market rows.
    oracle_raw=independent.source(root,cfg)
    audit=independent.audit(cfg,oracle_raw,base,signals,trades)
    metrics,monthly,cov,comparisons=reports(cfg,signals,trades,daily,coverage)
    audit['metrics_audit']=independent_metrics_audit(metrics,monthly,trades,signals,coverage)
    if audit['metrics_audit']['status']!='PASS':audit['status']='FAIL'
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('trades',trades),('signals',signals),('monthly_report',monthly),('architecture_comparison',comparisons),('coverage_report',cov),('daily_coverage',coverage),('daily_report',daily)]:write_csv(out/(name+'.csv'),rows)
    engine.dump(out/'metrics.json',metrics);engine.dump(out/'independent_audit.json',audit);engine.dump(out/'input_provenance.json',receipts)
    (out/'REPORT.md').write_text(report(metrics,comparisons,audit,cfg))
    changed=git('diff','--name-status',cfg['base_main'],'HEAD')
    old_files=git('ls-tree','-r','--name-only',cfg['base_main'],'IntradayLab').splitlines()
    altered_old=[f for f in old_files if git('rev-parse',cfg['base_main']+':'+f)!=git('hash-object',f)]
    roots={line.split()[3]:line.split()[2] for line in git('ls-tree','HEAD').splitlines() if line.split()[3]!='IntradayLab'}
    if roots!=cfg['protected_root_trees'] or altered_old:raise ValueError('PROTECTED_FILES_CHANGED')
    files=[engine.CONFIG,engine.CONFIG.with_suffix('.sha256'),engine.LAB/'reports/STAGE2_ORB_FALSE_BREAK_FADE_M5_PREREGISTRATION.md',*[engine.LAB/'tools'/f for f in ('orb_false_break_fade_replay.py','audit_orb_false_break_fade.py','run_orb_false_break_fade.py')],*sorted(out.iterdir())]
    engine.dump(out/'manifest.json',dict(schema=1,strategy=cfg['strategy'],base_main=cfg['base_main'],pre_pnl_commit=engine.FREEZE,implementation_commit=git('rev-parse','HEAD'),config_sha256=fingerprint,source_ref=cfg['source_ref'],source_repository=cfg['source_repository'],input_provenance=receipts,architectures=cfg['architectures'],C1_C2_fill_identity='One trade ledger, costs replaced algebraically; no C2 signal/execution run',protected_root_trees=roots,altered_existing_IntradayLab_files=altered_old,committed_changes=changed,classification='INCONCLUSIVE_UNRESOLVED',files={str(f.relative_to(engine.LAB)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.name!='manifest.json'}))
    print(json.dumps({'audit':audit['status'],'discrepancies':len(audit['discrepancies']),'trades':len(trades),'monthly_rows':len(monthly)}))
    if audit['status']!='PASS':raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=OUT)
    args=p.parse_args();run(args.data_root,args.output)
