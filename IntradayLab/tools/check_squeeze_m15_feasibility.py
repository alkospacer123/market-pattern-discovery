#!/usr/bin/env python3
"""Pre-return technical counts only. No strategy, no P&L."""
import argparse,json
from pathlib import Path
from datetime import timedelta
from collections import Counter
from run_squeeze_m15 import read_inputs,CONFIG,encoded,sha
from squeeze_m15_replay import compose,windows,flat_slot,next_slot


def check(root):
    config=json.loads(CONFIG.read_text())
    data,provenance=read_inputs(root,config)
    rows=[]
    for symbol,bars in data.items():
        m15,h1=compose(bars,15),compose(bars,60)
        segments=Counter(); ready=0; feasible=Counter(); h1_eligible=Counter()
        for day in sorted({b.timestamp.date() for b in bars}):
            for w in windows(day):
                segment=[]
                for t,b in m15.items():
                    if not w[0]<=t<w[1]: continue
                    if b is None:
                        if segment: segments[len(segment)]+=1
                        segment=[];continue
                    segment.append(t)
                    ready+=len(segment)>=7
                    if len(segment)<9:continue
                    for delay in (10,15):
                        now=t+timedelta(minutes=10+delay); target=next_slot(now)
                        if target+timedelta(minutes=25)>flat_slot(w)-timedelta(minutes=5):continue
                        feasible[delay]+=1
                        eligible=[p for p in h1 if w[0]<=p and p+timedelta(minutes=60)<=w[1] and p+timedelta(minutes=55+delay)<=now]
                        if len(eligible)>=2 and all(h1[p] for p in eligible[-2:]):h1_eligible[delay]+=1
                if segment:segments[len(segment)]+=1
        rows.append(dict(instrument=symbol,complete_m15=sum(b is not None for b in m15.values()),incomplete_m15=sum(b is None for b in m15.values()),complete_h1=sum(b is not None for b in h1.values()),incomplete_h1=sum(b is None for b in h1.values()),continuous_segment_lengths=dict(sorted(segments.items())),ready_indicator_candles=ready,period20_possible=any(n>=20 for n in segments),hypothetical_signal_then_safe_open_T10=feasible[10],hypothetical_signal_then_safe_open_T15=feasible[15],h1_pair_ready_safe_opportunities_T10=h1_eligible[10],h1_pair_ready_safe_opportunities_T15=h1_eligible[15]))
    status='PASS' if all(r['ready_indicator_candles'] and r['hypothetical_signal_then_safe_open_T10'] and r['h1_pair_ready_safe_opportunities_T15'] for r in rows) else 'FEASIBILITY BLOCKED / INCONCLUSIVE'
    return dict(status=status,scope='TECHNICAL_PRE_RETURNS_ONLY_NO_SIGNALS_OR_PNL',config_sha256=sha(CONFIG.read_bytes()),inputs=provenance,instruments=rows,limitations='Accepted restricted research windows; native delivery and historical actual fill/GO unproved; not an economic verdict.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();r=check(a.data_root);a.output.write_text(encoded(r));print(r['status']);print([(x['instrument'],x['complete_m15'],x['complete_h1'],x['h1_pair_ready_safe_opportunities_T15']) for x in r['instruments']])
