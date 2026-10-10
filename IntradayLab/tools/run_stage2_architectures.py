#!/usr/bin/env python3
"""Freeze -> run bounded 2023 complete architectures; never write old outputs."""
import argparse
from collections import Counter
from datetime import datetime, timedelta
from decimal import Decimal as D
import json
from pathlib import Path

from independent_corrective_review import aggregate, coverage, encoded, sha, write_csv
from run_m5_baseline import inputs, csv_text, git
from m5_conditional_v2 import Replay, ZERO, END, windows
from stage2_architecture_analysis import (LAB, BASE, indicator_maps, attribution,
    diagnostics, read_table)
from stage2_architecture_replay import ArchitectureReplay, ARCHITECTURES

CONFIG=LAB/'config/stage2_complete_architectures_v1.json'
DEST=LAB/'results/stage2_complete_architectures_v1'
FROZEN=LAB/'results/stage2_m5_conditional_v2'


def manifest():
    m=json.loads(CONFIG.read_text()); digest=sha(CONFIG)
    assert digest==CONFIG.with_suffix('.sha256').read_text().split()[0], 'Manifest not frozen'
    assert tuple(m['architectures'])==ARCHITECTURES
    assert m['parent_head']==BASE
    original=json.loads((LAB/'config/stage2_m5_conditional_v2.json').read_text())
    for key in ('inputs','parameters','source_ref','run_matrix'):
        assert m[key]==original[key], key
    return m,digest


def implementation_hashes():
    names=['tools/stage2_architecture_analysis.py','tools/stage2_architecture_replay.py',
        'tools/run_stage2_architectures.py','tests/test_stage2_architectures.py',
        'tools/m5_conditional_v2.py','tools/run_m5_baseline.py','tools/session_mtf.py',
        'tools/independent_corrective_review.py']
    return {name:sha(LAB/name) for name in names}


def retained_hashes():
    paths=[]
    for directory in ('results/stage2_m5','results/stage2_m5_conditional_v2','results/stage2_m5_v2_corrective_review'):
        paths+=sorted((LAB/directory).iterdir())
    paths+=list((LAB/'config').glob('stage2_m5*'))
    return {str(p.relative_to(LAB)):sha(p) for p in paths if p.is_file()}


def checksums(dest=DEST):
    (dest/'SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted(dest.iterdir()) if p.is_file() and p.name!='SHA256SUMS'))


def prepare(root):
    m,digest=manifest(); _,provenance=inputs(root,m)
    assert not (DEST/'results.json').exists(), 'Do not refreeze after seeing returns'
    payload={'state':'FROZEN_BEFORE_ARCHITECTURE_RETURNS','manifest_sha256':digest,
        'source_ref':m['source_ref'],'inputs':provenance,'implementation_sha256':implementation_hashes(),
        'retained_artifacts_sha256':retained_hashes(),
        'MTF_gate_sha256':sha(LAB/'results/stage2_architecture_diagnostics/mtf_readiness.json'),
        'diagnostic_provenance_sha256':sha(LAB/'results/stage2_architecture_diagnostics/provenance.json')}
    DEST.mkdir(parents=True,exist_ok=True)
    path=DEST/'input_provenance.json'
    if path.exists(): assert json.loads(path.read_text())==json.loads(encoded(payload)), 'Freeze differs'
    path.write_text(encoded(payload)); print('FROZEN',digest,flush=True)


def verify_base(replays):
    for filename,attr in [('signals.csv','signals'),('execution_events.csv','events'),('trade_ledger.csv','ledger')]:
        rows=[]
        for r in replays: rows+=getattr(r,attr)
        fields=list(dict.fromkeys(k for r in rows for k in r))
        assert csv_text(rows,fields).encode()==(FROZEN/filename).read_bytes(), filename
    return {'signals':7813,'entries':2140,'closed':2058,'unknown':82,
        'signals_events_ledger':'BYTE_IDENTICAL_TO_FROZEN_V2'}


def metric_groups(replay,cov,architecture,scenario):
    rows=[]
    all_cov='COVERED' if all(c['coverage_status']=='COVERED' for c in cov.values()) else 'PARTIAL_COVERAGE'
    for period in ['2023']+list(sorted({key[1] for key in cov})):
        for direction in ('ALL','LONG','SHORT'):
            sub=[r for r in replay.ledger if (period=='2023' or r['entry_interval_start'][:7]==period) and (direction=='ALL' or r['direction']==direction)]
            coverage_status=all_cov if period=='2023' else cov[replay.symbol,period]['coverage_status']
            spanning=any(r['status']=='UNRESOLVED' and period!='2023' and r['entry_interval_start'][:7]<=period<=(r.get('model_flat_confirmed_at') or '2023-12')[:7] for r in replay.ledger)
            rec={'architecture':architecture,'scenario':scenario,'run':f'{replay.strategy}_{replay.symbol}',
                'strategy':replay.strategy,'instrument':replay.symbol,'group':'YEAR' if period=='2023' else 'MONTH',
                'period':period,'direction':direction}|aggregate(sub,coverage_status,spanning)
            if period!='2023': rec.update(cov[replay.symbol,period])
            closed=[r for r in sub if r['net_model_c1'] is not None]
            rec['net_R_closed_diagnostic']=sum((r['net_R'] for r in closed),ZERO) if closed else None
            rec['mean_net_R_closed_diagnostic']=rec['net_R_closed_diagnostic']/len(closed) if closed else None
            rec['gross_R_closed_diagnostic']=sum((r['gross_price_pnl']/r['initial_risk_price_units'] for r in closed),ZERO) if closed else None
            rec['entry_count']=len(sub)
            rec['stop_count']=sum(r['exit_reason']=='STOP' for r in sub)
            rec['take_count']=sum(r['exit_reason']=='TAKE' for r in sub)
            rec['BE_count']=sum(r['exit_reason']=='BREAKEVEN_STOP' for r in sub)
            rec['trailing_count']=sum(r['exit_reason']=='TRAIL_STOP' for r in sub)
            rec['mean_win']=sum((r['net_model_c1'] for r in closed if r['net_model_c1']>0),ZERO)/sum(r['net_model_c1']>0 for r in closed) if any(r['net_model_c1']>0 for r in closed) else None
            rec['mean_loss_magnitude']=-sum((r['net_model_c1'] for r in closed if r['net_model_c1']<0),ZERO)/sum(r['net_model_c1']<0 for r in closed) if any(r['net_model_c1']<0 for r in closed) else None
            rec['observed_close_MTM_DD_diagnostic']=(replay.mtm_drawdown if period=='2023' else replay.month_drawdowns.get(period)) if not replay.unknown_liability and coverage_status=='COVERED' else None
            rec['C2_closed_net_stress']=sum((r['gross_price_pnl']-2*r['c1_total'] for r in closed),ZERO) if closed else None
            c2=[r|{'net_model_c1':r['gross_price_pnl']-2*r['c1_total']} for r in closed]
            rec['C2_PF_closed_stress']=aggregate(c2,'PARTIAL_COVERAGE')['net_PF_closed_diagnostic']
            rec['C2_basis']='same C1-admitted trades; replace aggregate C1 by twice C1; no extra cost stack or requalification'
            rec['calendar_month_outcome']='NO_COVERAGE' if coverage_status=='NO_COVERAGE' else 'INCOMPLETE' if not rec['full_period_accounted'] else 'ZERO_TRADES' if not sub else 'POSITIVE' if rec['Net']>0 else 'NEGATIVE' if rec['Net']<0 else 'ZERO_NET'
            rows.append(rec)
    for rec in rows[:3]:
        months=[r for r in rows if r['group']=='MONTH' and r['direction']==rec['direction']]
        rec['closed_subset_positive_months']=sum(r['closed_subset_outcome']=='POSITIVE' for r in months)
        rec['closed_subset_negative_months']=sum(r['closed_subset_outcome']=='NEGATIVE' for r in months)
        rec['months_with_closed_trades']=sum(r['closed_accounted_trades']>0 for r in months)
        rec['complete_positive_calendar_months']=sum(r['calendar_month_outcome']=='POSITIVE' for r in months)
        rec['complete_negative_calendar_months']=sum(r['calendar_month_outcome']=='NEGATIVE' for r in months)
        rec['complete_calendar_months']=sum(r['full_period_accounted'] for r in months)
        rec['no_coverage_months']=sum(r['coverage_status']=='NO_COVERAGE' for r in months)
        rec['incomplete_covered_months']=sum(r['coverage_status']!='NO_COVERAGE' and not r['full_period_accounted'] for r in months)
        streak=max_streak=0
        for month in months:
            streak=streak+1 if month['calendar_month_outcome']=='NEGATIVE' else 0
            max_streak=max(max_streak,streak)
        rec['known_negative_calendar_month_streak_lower_bound']=max_streak
        first=datetime.fromisoformat(replay.ledger[0]['entry_interval_start']).date() if replay.ledger else None
        rec['full_economic_verdict']='NO ECONOMIC BASELINE PASS / REJECT CANDIDATE'
    return rows


def pairs(reference,candidate,reference_id,candidate_id):
    ref={r['signal_id']:r for r in reference.ledger}
    out=[]
    for r in candidate.ledger:
        a=ref.get(r['signal_id'])
        if not a: continue
        exact=a['entry_interval_start']==r['entry_interval_start'] and a['entry']==r['entry']
        known=a['net_model_c1'] is not None and r['net_model_c1'] is not None
        valid=exact and known
        out.append({'run':r['run'],'reference_architecture':reference_id,'candidate_architecture':candidate_id,
            'signal_id':r['signal_id'],'same_entry':exact,'both_known':known,
            'reference_status':a['status'],'candidate_status':r['status'],
            'reference_exit':a['exit_reason'],'candidate_exit':r['exit_reason'],
            'reference_net':a['net_model_c1'],'candidate_net':r['net_model_c1'],
            'paired_net_delta':r['net_model_c1']-a['net_model_c1'] if valid else None,
            'paired_delta_in_reference_R':(r['net_model_c1']-a['net_model_c1'])/a['initial_risk_price_units'] if valid else None,
            'baseline_winner_became_loser':a['net_model_c1']>0 and r['net_model_c1']<0 if valid else None,
            'baseline_loser_became_winner':a['net_model_c1']<0 and r['net_model_c1']>0 if valid else None,
            'profit_reduced':r['net_model_c1']<a['net_model_c1'] and a['net_model_c1']>0 if valid else None,
            'loss_reduced':r['net_model_c1']>a['net_model_c1'] and a['net_model_c1']<0 if valid else None,
            'selection_basis':'Intersection of both entered, exact same Open/time, both accounted; unknown outcomes excluded, no extrapolation'})
    return out


def frequency(replay,architecture,scenario,bars):
    counts=Counter(r['entry_interval_start'][:10] for r in replay.ledger)
    rows=[]; day=bars[0].timestamp.date()
    while day<END.date():
        if windows(day):
            rows.append({'architecture':architecture,'scenario':scenario,'run':f'{replay.strategy}_{replay.symbol}',
                'date':str(day),'model_entries':counts[str(day)],'basis':'Approved calendar day from source inception, includes zero/missing observations; no trading quota'})
        day+=timedelta(days=1)
    return rows


def run(root,out=DEST):
    m,digest=manifest(); frozen=json.loads((DEST/'input_provenance.json').read_text())
    assert frozen['manifest_sha256']==digest and frozen['implementation_sha256']==implementation_hashes(), 'Refuse unfrozen implementation'
    assert frozen['retained_artifacts_sha256']==retained_hashes()
    data,provenance=inputs(root,m); assert provenance==frozen['inputs']
    contexts=indicator_maps(data); indexes={s:{b.timestamp:b for b in bars} for s,bars in data.items()}
    raw={s:{at:(b.open,b.high,b.low,b.close,b.volume) for at,b in idx.items()} for s,idx in indexes.items()}
    cov=coverage(raw)
    out.mkdir(exist_ok=True,parents=True)
    signals=[];events=[];ledger=[];groups=[];attrib=[];amendments=[];paired=[];freq=[];summaries=[];baseline=[]
    for item in m['run_matrix']:
        s,st=item['instrument'],item['strategy']; replays={}
        for architecture in ARCHITECTURES:
            for scenario in ('C1_T10','C1_T15_DELAY'):
                p=m['parameters'] if scenario=='C1_T10' else m['parameters']|{'availability_minutes':15}
                replay=(Replay(s,st,p) if architecture=='FROZEN_V2' else ArchitectureReplay(s,st,p,architecture,m['defaults'])).run(data[s])
                if scenario=='C1_T10':
                    replays[architecture]=replay
                    if architecture=='FROZEN_V2': baseline.append(replay)
                meta={'architecture':architecture,'scenario':scenario}
                signals += [r|meta for r in replay.signals]; events += [r|meta for r in replay.events]
                ledger += [r|meta for r in replay.ledger]
                ms=metric_groups(replay,{k:v for k,v in cov.items() if k[0]==s},architecture,scenario)
                groups+=ms; summaries.append(ms[0]|{'signal_counts':dict(Counter(r['status'] for r in replay.signals)),
                    'filter_reasons':dict(Counter(r['reason'] for r in replay.signals if r['status']=='FILTERED')),
                    'execution_counts':replay.counts})
                smap={r['signal_id']:r for r in replay.signals}
                attrib += [attribution(r,smap[r['signal_id']],indexes[s],contexts[s])|meta for r in replay.ledger]
                amendments += [r|meta|{'run':f'{st}_{s}'} for r in getattr(replay,'amendments',[])]
                freq+=frequency(replay,architecture,scenario,data[s])
                print(architecture,scenario,st,s,ms[0]['closed_accounted_trades'],ms[0]['unresolved'],ms[0]['closed_only_net_c1'],ms[0]['net_PF_closed_diagnostic'],flush=True)
        for reference,candidate in [('FROZEN_V2','ENTRY'),('FROZEN_V2','MANAGEMENT'),('ENTRY','ENTRY_MANAGEMENT'),('MANAGEMENT','ENTRY_MANAGEMENT'),('ENTRY_MANAGEMENT','FULL_M5'),('FROZEN_V2','FULL_M5')]:
            paired+=pairs(replays[reference],replays[candidate],reference,candidate)
    verified=verify_base(baseline)
    for name,rows in [('signals.csv',signals),('execution_events.csv',events),('trade_ledger.csv',ledger),
        ('metrics.csv',groups),('trade_attribution.csv',attrib),('stop_amendments.csv',amendments),
        ('paired_contribution.csv',paired),('daily_frequency.csv',freq)]: write_csv(out/name,rows)
    segment_rows=[]
    for architecture in ARCHITECTURES:
        selected=[r for r in attrib if r['architecture']==architecture and r['scenario']=='C1_T10']
        segment_rows += [r|{'architecture':architecture} for r in diagnostics(selected)]
    write_csv(out/'pnl_segments.csv',segment_rows)
    results={'manifest_sha256':digest,'base_verification':verified,'runs':summaries,
        'original_82_unknown_outcomes':'Preserved byte-identically; candidate unknown counts independently reported, never recovered or zero-imputed',
        'MTF':'BLOCKED; 0 native contexts, no native/deduced context backtest',
        'unit':'Independent normalized quote-price units; never sum RUB-like units across different symbols as a portfolio',
        'verdict':'NO ECONOMIC BASELINE PASS / REJECT CANDIDATE',
        'next_strategy':'Volatility Squeeze Breakout, recommended only; unimplemented',
        'stages':'Stage2 only; no Stage3/WF/TRUE OOS/LIVE/merge'}
    (out/'results.json').write_text(encoded(results)); checksums(out)
    assert frozen['retained_artifacts_sha256']==retained_hashes()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.data_root)
    else:
        dest=a.output or DEST
        assert dest.resolve().is_relative_to(LAB.resolve()) or dest.resolve().is_relative_to(Path('/workspace/work'))
        run(a.data_root,dest)
