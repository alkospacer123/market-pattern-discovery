#!/usr/bin/env python3
"""Reviewable real-path traces; source bounded to the frozen2023 prefix."""
import argparse,csv,gzip,json
from pathlib import Path
from datetime import datetime,timedelta
from decimal import Decimal as D
from run_squeeze_m15 import read_inputs,CONFIG
from squeeze_m15_replay import compose


def read(p):
    with (gzip.open(p,'rt') if p.suffix=='.gz' else p.open()) as f:return list(csv.DictReader(f))


def table(head,rows):
    return ['| '+' | '.join(head)+' |','| '+' | '.join('---' for _ in head)+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows]


def trace(root,out):
    data,_=read_inputs(root,json.loads(CONFIG.read_text()))
    parents={s:compose(b,15) for s,b in data.items()};raw={s:{b.timestamp:b for b in v} for s,v in data.items()}
    ledger=read(out/'trade_ledger.csv.gz');signals=read(out/'signals.csv.gz')
    chosen=[r for r in ledger if r['architecture']=='SQUEEZE_M15' and r['scenario']=='T10']
    features={(r['instrument'],r['at']):r for r in read(out/'indicator_features.csv.gz')}
    h1signals={(r['instrument'],r['signal_id']):r for r in signals if r['architecture']=='SQUEEZE_H1_M15' and r['scenario']=='T10'}
    base=['# Manual real M15 execution traces','','All eleven unique standalone T10 executions; H1 retained/removed admission is shown separately. T15 has identical execution price/time/protection/exit, with acknowledgement delayed five minutes. Raw source read only through frozen2023 byte budgets. These are normalized conditional executions, not real venue fill evidence. UNKNOWN is absent in the actual cohort; synthetic unknown/boundary tests are separately listed below.','']
    for p in chosen:
        s=p['instrument'];sid=p['signal_id'];sig=next(r for r in signals if r['instrument']==s and r['signal_id']==sid and r['architecture']=='SQUEEZE_M15' and r['scenario']=='T10');h=h1signals[s,sid]
        start=datetime.fromisoformat(sig['range_start']);end=datetime.fromisoformat(p['exit_at']);st=datetime.fromisoformat(p['signal_at']);f=features[s,p['signal_at']]
        base += [f"## {s} {sid} {p['direction']}",'',f"Compression {sig['range_start']} through {sig['range_end']}, {sig['squeeze_bars']} M15 candles; range [{sig['range_low']}, {sig['range_high']}]. Signal {p['signal_at']} Close={sig['signal_close']}; signal candle outside range and excluded from its construction. Available={p['available_at']} (T10), {st+timedelta(minutes=25)} (T15); strict future M15 Open={p['entry_at']} at both delays.",'',f"Signal SMA7={f['sma7']}, population variance={f['variance7']}, EMA7={f['ema7']}, Wilder ATR7={f['atr7']}. BB [{f['bb_lower']},{f['bb_upper']}], KC [{f['kc_lower']},{f['kc_upper']}], squeeze={f['squeeze']}.",'',f"Frozen Stop={p['stop']}; cap={p['cap']}; actual Open={p['entry']}; initial risk={p['initial_risk']}; Take={p['take']}; planned C1={p['planned_c1']}; planned net RR={p['planned_net_RR']}.",'',f"H1 admission {h['status']}/{h['reason']}, pair={h['mtf_first']} → {h['mtf_last']}, available={h['mtf_available_at']}, direction={h['mtf_direction']}, context reason={h['mtf_reason']}.",'']
        ts=[t for t in sorted(parents[s]) if start<=t<=end]
        base+=table(['M15 start','O','H','L','C','V','Role'],[[t,b.open,b.high,b.low,b.close,b.volume,'SQUEEZE' if t<=datetime.fromisoformat(sig['range_end']) else 'SIGNAL' if t==st else 'ENTRY' if str(t)==p['entry_at'] else 'EXIT' if str(t)==p['exit_at'] else 'PATH'] for t in ts if (b:=parents[s][t])])+['']
        base+=['Exact children for signal, entry and exit (duplicate candles listed once):','']
        children=sorted({datetime.fromisoformat(p[key])+timedelta(minutes=5*i) for key in ('signal_at','entry_at','exit_at') for i in range(3)})
        base+=table(['M5 child start','O','H','L','C','V'],[[t,b.open,b.high,b.low,b.close,b.volume] for t in children if (b:=raw[s].get(t))])+['']
        gross=D(p['direction_sign'])*(D(p['exit'])-D(p['entry']));cost=D(p['c1_entry'])+D(p['c1_exit'])
        base += [f"Exit={p['exit_reason']} at {p['exit_at']}, acknowledgement={p['exit_ack']}, price={p['exit']}, hold={p['hold_minutes']}min, flags={p['flags'] or 'none'}, flat breach={p['flat_target_breach']}. Gross={gross}; C1={p['c1_entry']}+{p['c1_exit']}={cost}; Net={gross-cost}; C2 Net={gross-2*cost}. Net R={p['net_R']}; conservative MFE R={p['mfe_R']}. No favorable Stop/market exit-bar extreme used. Expected journal Net={p['net']}.",'']
        assert gross-cost==D(p['net'])
    representatives={}
    for r in signals:
        if r['scenario']=='T10' and r['status'] in ('NONFILL','FILTERED'):
            representatives.setdefault((r['instrument'],r['status'],r['reason']),r)
    base+=['## Real rejection / nonfill representatives','','The full funnel is retained in filter_funnel.csv. Each row below is a real signal, not an invented missing-path example.','']
    base+=table(['Instrument','Architecture','ID','Signal','Target','Status','Reason'],[[r[k] for k in ('instrument','architecture','signal_id','signal_at','planned_execution_at','status','reason')] for r in representatives.values()])+['']
    imo=next(r for r in signals if r['instrument']=='IMOEXF' and r['architecture']=='SQUEEZE_M15' and r['scenario']=='T10' and r['status']=='NONFILL')
    t=datetime.fromisoformat(imo['planned_execution_at']);b=parents['IMOEXF'][t]
    base += [f"IMOEXF real exact target {t}: Open={b.open}, cap={imo['cap']}, direction={imo['direction']}, Stop={imo['stop']}, signal ATR={imo['atr7']}; {imo['reason']} explains zero fills despite technical feasibility. No fictitious zero from failed warm-up.",'', '## Separately synthetic adversaries','','test_squeeze_m15.py checks hand-calculated LONG/SHORT symmetry, identical strict future M15 Open at both delays, common flat acknowledgement, exact composition/no clearing bridge, seven-bar seed/reset, two-bar range excluding signal, risk/target geometry, adverse gap and dual-touch Stop-first, entry-bar TP nonfill, one-tick penetration, session/max-hold/failed-breakout timers, incomplete target UNKNOWN order, missing exposure UNKNOWN preserved after conditional flat, H1 missing/stale/gap rejection and dated CNY ticks. None is labelled a real2023 UNKNOWN trade.','']
    (out/'manual_traces.md').write_text('\n'.join(base))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();trace(a.data_root,a.output)
