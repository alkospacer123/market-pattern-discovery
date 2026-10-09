"""Separately frozen VWAP follow-up: payable order price, unchanged VWAP TP.

The earlier reject-at-original-cap variant produced zero entries. This changes
order architecture rather than any parameter: direction-adjusted net reward
must cover net risk at the worst permitted price. No unobserved limit touch is
filled: only the one exact scheduled observed Open can pass the pre-known cap.
"""
import argparse
from collections import Counter
from decimal import Decimal as D
import json
from pathlib import Path

from m5_conditional_v2 import tick, rounded
from stage2_architecture_replay import ArchitectureReplay
from stage2_architecture_analysis import (LAB, indicator_maps, attribution, diagnostics)
from run_stage2_architectures import (inputs, encoded, sha, retained_hashes, metric_groups,
    coverage, pairs, frequency, write_csv, checksums)

CONFIG=LAB/'config/stage2_vwap_payable_cap_v1.json'
DEST=LAB/'results/stage2_vwap_payable_cap_v1'


class PayableCapReplay(ArchitectureReplay):
    def __init__(self,symbol,params,mode,defaults):
        if mode not in ('PAYABLE_CAP_ENTRY','PAYABLE_CAP_FULL_M5'):
            raise ValueError('Undeclared payable-cap architecture')
        super().__init__(symbol,'VWAP_MR',params,'ENTRY' if mode=='PAYABLE_CAP_ENTRY' else 'FULL_M5',defaults)
        self.mode=mode
        self.planning=False

    def decision(self,b,now,f):
        self.planning=True
        try:
            super().decision(b,now,f)
        finally:
            self.planning=False

    def gate_entry(self,s,price):
        if self.planning:
            from datetime import datetime
            d=s['direction_sign'];step=tick(self.symbol,datetime.fromisoformat(s['planned_execution_at']))
            # For long: TP-P-C >= P-SL+C => P <= (TP+SL-2C)/2.
            # Short symmetric. C=2 ticks. Price bound rounded toward eligibility
            # safety and combined with the original absolute adverse cap.
            raw=(s['take']+s['stop']-d*4*step)/2
            bound=rounded(raw,step,d==-1)
            s['cap']=min(s['cap'],bound) if d==1 else max(s['cap'],bound)
            s['payable_cap']=s['cap']
            s['payable_cap_basis']='Net reward >= net risk, C1=2 dated ticks; price rounded toward safety'
            price=s['cap']
        return super().gate_entry(s,price)


def load():
    m=json.loads(CONFIG.read_text());digest=sha(CONFIG)
    assert digest==CONFIG.with_suffix('.sha256').read_text().split()[0]
    parent=json.loads((LAB/'config/stage2_complete_architectures_v1.json').read_text())
    for k in ('inputs','parameters','source_ref','defaults'):assert m[k]==parent[k]
    return m,digest


def hashes():
    files=['tools/stage2_vwap_payable_cap.py','tests/test_stage2_vwap_payable_cap.py',
        'tools/stage2_architecture_replay.py','tools/run_stage2_architectures.py',
        'tools/stage2_architecture_analysis.py']
    return {name:sha(LAB/name) for name in files}


def prepare(root):
    m,digest=load();_,provenance=inputs(root,m)
    assert not (DEST/'results.json').exists()
    DEST.mkdir(exist_ok=True,parents=True)
    payload={'manifest_sha256':digest,'implementation_sha256':hashes(),'inputs':provenance,
        'retained_artifacts_sha256':retained_hashes(),
        'prior_architecture_results_sha256':sha(LAB/'results/stage2_complete_architectures_v1/results.json'),
        'state':'FROZEN_BEFORE_PAYABLE_CAP_RETURNS'}
    path=DEST/'input_provenance.json'
    if path.exists():assert json.loads(path.read_text())==json.loads(encoded(payload))
    path.write_text(encoded(payload));print('FROZEN',digest)


def run(root,out=DEST):
    from datetime import datetime
    from m5_conditional_v2 import Replay
    from stage2_architecture_replay import ArchitectureReplay
    m,digest=load();prepared=json.loads((DEST/'input_provenance.json').read_text())
    assert prepared['manifest_sha256']==digest and prepared['implementation_sha256']==hashes()
    assert prepared['retained_artifacts_sha256']==retained_hashes()
    data,provenance=inputs(root,m);assert provenance==prepared['inputs']
    contexts=indicator_maps(data);idx={s:{b.timestamp:b for b in bars} for s,bars in data.items()}
    cov=coverage({s:{t:(b.open,b.high,b.low,b.close,b.volume) for t,b in index.items()} for s,index in idx.items()})
    out.mkdir(exist_ok=True,parents=True)
    signals=[];events=[];ledger=[];metrics=[];attrs=[];paired=[];freq=[];summaries=[]
    for symbol in sorted(data):
        for mode in m['architectures']:
            for scenario in ('C1_T10','C1_T15_DELAY'):
                p=m['parameters'] if scenario=='C1_T10' else m['parameters']|{'availability_minutes':15}
                replay=PayableCapReplay(symbol,p,mode,m['defaults']).run(data[symbol])
                meta={'architecture':mode,'scenario':scenario}
                signals += [r|meta for r in replay.signals];events += [r|meta for r in replay.events];ledger += [r|meta for r in replay.ledger]
                ms=metric_groups(replay,{k:v for k,v in cov.items() if k[0]==symbol},mode,scenario)
                metrics+=ms;summaries.append(ms[0]|{'signal_counts':dict(Counter(r['status'] for r in replay.signals)),
                    'execution_counts':replay.counts,'filter_reasons':dict(Counter(r['reason'] for r in replay.signals if r['status']=='FILTERED'))})
                smap={r['signal_id']:r for r in replay.signals}
                attrs += [attribution(r,smap[r['signal_id']],idx[symbol],contexts[symbol])|meta for r in replay.ledger]
                freq+=frequency(replay,mode,scenario,data[symbol])
                if scenario=='C1_T10':
                    ref=Replay(symbol,'VWAP_MR',p).run(data[symbol])
                    paired += pairs(ref,replay,'FROZEN_V2',mode)
                print(mode,scenario,symbol,ms[0]['closed_accounted_trades'],ms[0]['unresolved'],ms[0]['closed_only_net_c1'],ms[0]['net_PF_closed_diagnostic'],flush=True)
    for name,rows in [('signals.csv',signals),('execution_events.csv',events),('trade_ledger.csv',ledger),('metrics.csv',metrics),
        ('trade_attribution.csv',attrs),('paired_contribution.csv',paired),('daily_frequency.csv',freq)]:write_csv(out/name,rows)
    segments=[]
    for mode in m['architectures']:
        segments += [r|{'architecture':mode} for r in diagnostics([r for r in attrs if r['architecture']==mode and r['scenario']=='C1_T10'])]
    write_csv(out/'pnl_segments.csv',segments)
    (out/'results.json').write_text(encoded({'manifest_sha256':digest,'runs':summaries,
        'prior_trial_retained':'Original reject-at-cap is unchanged; zero MR entries',
        'MTF':'BLOCKED; M5-only full fallback',
        'verdict':'NO ECONOMIC BASELINE PASS / REJECT CANDIDATE',
        'original_unknown_outcomes':'82 original unknown outcomes unchanged; none recovered'}));checksums(out)
    assert retained_hashes()==prepared['retained_artifacts_sha256']

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.data_root)
    else:
        dest=a.output or DEST
        assert dest.resolve().is_relative_to(LAB.resolve()) or dest.resolve().is_relative_to(Path('/workspace/work'))
        run(a.data_root,dest)
