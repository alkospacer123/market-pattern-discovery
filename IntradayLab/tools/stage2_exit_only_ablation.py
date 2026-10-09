"""Pure exit contribution on frozen accounted entries/stops; not a strategy run.

Each original known entry is an independent counterfactual seed; seeds may
physically overlap, so no portfolio PF/DD/frequency or economic PASS is claimed.
The complete new exit bundle is reused without changing its constants. Initial
Stop, entry Open/time and original risk are held equal to frozen v2. The 82
unknown original outcomes are excluded unchanged, not rescanned/reconciled.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime,timedelta
from decimal import Decimal as D
import json
from pathlib import Path

from stage2_architecture_replay import ArchitectureReplay
from stage2_architecture_analysis import LAB, read_table, indicator_maps
from m5_conditional_v2 import FIVE, allowed, close_submission_deadline
from run_stage2_architectures import inputs, retained_hashes, sha, encoded, write_csv, checksums

CONFIG=LAB/'config/stage2_exit_only_ablation_v1.json'
DEST=LAB/'results/stage2_exit_only_ablation_v1'


def implementation():
    return {name:sha(LAB/name) for name in ('tools/stage2_exit_only_ablation.py','tools/stage2_architecture_replay.py','tools/stage2_architecture_analysis.py')}


def load():
    m=json.loads(CONFIG.read_text());digest=sha(CONFIG)
    assert digest==CONFIG.with_suffix('.sha256').read_text().split()[0]
    p=json.loads((LAB/'config/stage2_complete_architectures_v1.json').read_text())
    for k in ('inputs','source_ref','parameters','defaults'):assert m[k]==p[k]
    return m,digest


def prepare(root):
    m,digest=load();_,prov=inputs(root,m);DEST.mkdir(exist_ok=True,parents=True)
    assert not (DEST/'results.json').exists()
    payload={'manifest_sha256':digest,'implementation_sha256':implementation(),'inputs':prov,
        'retained_artifacts_sha256':retained_hashes(),'state':'FROZEN_BEFORE_EXIT_ONLY_COUNTERFACTUALS'}
    (DEST/'input_provenance.json').write_text(encoded(payload))
    print('FROZEN',digest)


def null_outcome(replay,reason):
    row=replay.position.row
    row.update(status='UNRESOLVED',exit=None,exit_interval_start=None,exit_interval_end=None,
        exit_reason='UNKNOWN_COUNTERFACTUAL_PATH',gross_price_pnl=None,c1_exit=None,c1_total=None,
        net_model_c1=None,net_R=None,unresolved_reasons=reason,
        funding_and_emergency_costs='UNRESOLVED')
    replay.position=None


def run(root,out=DEST):
    m,digest=load();prep=json.loads((DEST/'input_provenance.json').read_text())
    assert prep['manifest_sha256']==digest and prep['implementation_sha256']==implementation()
    assert prep['retained_artifacts_sha256']==retained_hashes()
    data,prov=inputs(root,m);assert prov==prep['inputs']
    context=indicator_maps(data);indexes={s:{b.timestamp:b for b in bars} for s,bars in data.items()}
    originals=read_table(LAB/'results/stage2_m5_conditional_v2/trade_ledger.csv')
    known=[r for r in originals if r['net_model_c1'] is not None]
    assert len(known)==2058 and len(originals)-len(known)==82
    signals={s['signal_id']:s for s in read_table(LAB/'results/stage2_m5_conditional_v2/signals.csv')}
    trades=[];comparison=[];amendments=[];events=[];recorded_signals=[]
    meta={'architecture':'EXIT_ONLY_FROZEN_ENTRIES','scenario':'C1_T10'}
    for original in known:
        symbol=original['instrument'];strategy=original['strategy'];index=indexes[symbol]
        signal=signals[original['signal_id']].copy()
        signal_at=datetime.fromisoformat(signal['signal_at'])
        recent=[index[signal_at-i*FIVE] for i in (2,1,0)]
        signal.update(swing_low=min(b.low for b in recent),swing_high=max(b.high for b in recent))
        r=ArchitectureReplay(symbol,strategy,m['parameters'],'MANAGEMENT',m['defaults'])
        r.signals=[signal]
        start=datetime.fromisoformat(original['entry_interval_start']);now=start+2*FIVE
        r.entry_order={'target':start,'signal':signal}
        r.execute(index[start],now)
        if r.position:
            boundary=r.position.boundary
            now+=FIVE
            while r.position and now<boundary+2*FIVE:
                expected=now-2*FIVE
                if not allowed(symbol,expected):
                    now+=FIVE;continue
                b=index.get(expected)
                if b is None:
                    null_outcome(r,'UNKNOWN_NEW_COUNTERFACTUAL_PATH_NO_RECONSTRUCTION')
                    break
                r.execute(b,now)
                if r.position:
                    p=r.position
                    if now>=close_submission_deadline(p.boundary,r.p):r.close_request(now,'SESSION_FLAT')
                    elif now>=p.deadline-FIVE:r.close_request(now,'MAX_HOLD')
                    if not r.close_order:
                        r.current_context=context[symbol].get(expected,{})
                        r.manage(b,now,None)
                now+=FIVE
            if r.position:null_outcome(r,'UNCONFIRMED_EXIT_WITHIN_APPROVED_WINDOW')
        row=r.ledger[0]
        assert row['entry']==original['entry'] and row['stop']==original['stop'] and row['initial_risk_price_units']==original['initial_risk_price_units']
        trades.append(row|meta);events += [e|meta for e in r.events]
        recorded_signals.append(signal|meta)
        amendments += [a|meta|{'run':original['run']} for a in r.amendments]
        valid=row['net_model_c1'] is not None
        comparison.append({'run':original['run'],'signal_id':original['signal_id'],
            'reference_net':original['net_model_c1'],'candidate_net':row['net_model_c1'],
            'reference_exit':original['exit_reason'],'candidate_exit':row['exit_reason'],
            'same_entry_and_initial_stop':True,'candidate_status':row['status'],
            'paired_net_delta':row['net_model_c1']-original['net_model_c1'] if valid else None,
            'winner_became_loser':original['net_model_c1']>0 and row['net_model_c1']<0 if valid else None,
            'loser_became_winner':original['net_model_c1']<0 and row['net_model_c1']>0 if valid else None,
            'winner_profit_reduced':original['net_model_c1']>0 and row['net_model_c1']<original['net_model_c1'] if valid else None,
            'loser_loss_reduced':original['net_model_c1']<0 and row['net_model_c1']>original['net_model_c1'] if valid else None})
    summaries=[]
    for run_id in sorted({r['run'] for r in trades}):
        sub=[r for r in comparison if r['run']==run_id];valid=[r for r in sub if r['paired_net_delta'] is not None]
        t=[r for r in trades if r['run']==run_id and r['net_model_c1'] is not None]
        wins=[r['net_model_c1'] for r in t if r['net_model_c1']>0]
        losses=[r['net_model_c1'] for r in t if r['net_model_c1']<0]
        summaries.append({'run':run_id,'original_known_seeds':len(sub),'both_known':len(valid),'new_unknown_counterfactuals':len(sub)-len(valid),
            'paired_reference_net':sum((r['reference_net'] for r in valid),D(0)),
            'paired_exit_only_net':sum((r['candidate_net'] for r in valid),D(0)),
            'paired_delta_net':sum((r['paired_net_delta'] for r in valid),D(0)),
            'winners_became_losers':sum(r['winner_became_loser'] for r in valid),
            'losers_became_winners':sum(r['loser_became_winner'] for r in valid),
            'winners_profit_reduced':sum(r['winner_profit_reduced'] for r in valid),
            'losers_loss_reduced':sum(r['loser_loss_reduced'] for r in valid),
            'mean_exit_only_win':sum(wins,D(0))/len(wins) if wins else None,
            'mean_exit_only_loss_magnitude':-sum(losses,D(0))/len(losses) if losses else None,
            'exit_reasons':dict(Counter(r['exit_reason'] for r in trades if r['run']==run_id)),
            'full_Net':None,'full_PF':None,'full_DD':None,
            'basis':'Independent overlapping known-entry counterfactual seeds, original Stop and R fixed; no strategy/portfolio Net/PF/DD or PASS'})
    out.mkdir(exist_ok=True,parents=True)
    for filename,table in [('trade_ledger.csv',trades),('paired_exit_only.csv',comparison),('summary.csv',summaries),('stop_amendments.csv',amendments),('signals.csv',recorded_signals),('execution_events.csv',events)]:write_csv(out/filename,table)
    (out/'results.json').write_text(encoded({'manifest_sha256':digest,'summaries':summaries,
        'original_unknown_outcomes_excluded_unchanged':82,'comparison':'Exit-only bundle with frozen entries and initial Stop; not an executable strategy portfolio or economic acceptance',
        'implementation_sha256':implementation()}));checksums(out)
    assert retained_hashes()==prep['retained_artifacts_sha256']
    print(encoded(summaries))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.data_root)
    else:
        dest=a.output or DEST
        assert dest.resolve().is_relative_to(LAB.resolve()) or dest.resolve().is_relative_to(Path('/workspace/work'))
        run(a.data_root,dest)
