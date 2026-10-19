"""Independent published-ledger and table audit using csv/statistics, no metrics imports."""
from __future__ import annotations
import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import json
import math
from statistics import mean


def read(path):
    with path.open(newline='') as f:return list(csv.DictReader(f))


def dd(values):
    total=peak=0.
    worst=0.
    for x in values:
        total+=x;peak=max(peak,total);worst=min(worst,total-peak)
    return worst


def audit(out):
    rows=read(out/'all_trades.csv')
    errors=[]
    comparisons=0
    maximum=0.
    def equal(x,y,label,tolerance=1e-7):
        nonlocal comparisons,maximum
        comparisons+=1
        delta=abs(x-y);maximum=max(maximum,delta)
        if delta>tolerance:errors.append({'label':label,'actual':x,'expected':y,'delta':delta})
    for scenario in sorted(set(r['scenario'] for r in rows)):
        group=[r for r in rows if r['scenario']==scenario]
        previous=None
        directions={r['trade_id']:r['direction'] for r in group}
        for r in group:
            entry,exit=datetime.fromisoformat(r['entry_time']),datetime.fromisoformat(r['exit_time'])
            if entry>=exit:errors.append({'label':'EXIT_NOT_LATER_THAN_ENTRY','trade':r['trade_id']})
            if previous and entry<previous:errors.append({'label':'OVERLAPPING_POSITIONS','trade':r['trade_id']})
            previous=exit
            risk=float(r['initial_risk_price'])
            equal(risk,abs(float(r['entry_price'])-float(r['initial_stop_price'])),'risk')
            gross=(1 if r['direction']=='LONG' else -1)*(float(r['exit_price'])-float(r['entry_price']))/risk
            equal(float(r['gross_R']),gross,'gross')
            equal(float(r['cost_R']),(.02 if scenario.endswith('STOCK_PROXY') else .002)/risk,'cost')
            equal(float(r['net_R']),gross-float(r['cost_R']),'net')
            if r['trigger_bar_time'] and datetime.fromisoformat(r['trigger_bar_time'])<=entry:errors.append({'label':'ENTRY_BAR_TRIGGER'})
            if r['trail1_activation_time'] and datetime.fromisoformat(r['trail1_activation_time'])<=datetime.fromisoformat(r['trigger_bar_time']):errors.append({'label':'ACTIVATION_NOT_DELAYED'})
            if scenario.endswith('STOCK_PROXY'):
                for k in ['initial_stop_price','final_stop']:
                    if Decimal(r[k])%Decimal('.01'):errors.append({'label':'STOCK_STOP_OFF_GRID','trade':r['trade_id']})
        for r in read(out/(scenario+'_trace.csv')):
            if not r['stop_before'] or not r['stop_after']:continue
            before,after=float(r['stop_before']),float(r['stop_after'])
            direction=directions.get(r['trade_id'])
            if direction and ((direction=='LONG' and after<before-1e-9) or (direction=='SHORT' and after>before+1e-9)):
                errors.append({'label':'STOP_LOOSENED','trade':r['trade_id']})
    for file,key in [('annual.csv','year'),('monthly.csv','month'),('quarterly.csv','quarter'),('directions.csv','direction'),('summary.csv','period'),('entry_cohorts.csv','cohort')]:
        for r in read(out/file):
            g=[x for x in rows if x['scenario']==r['scenario']]
            if key=='direction':g=[x for x in g if x['direction']==r[key]]
            elif key in ('period','cohort'):
                if r[key]!='FULL':
                    before=r[key] in ('2011_2024','ENTRY_BEFORE_2025')
                    timekey='entry_time' if key=='cohort' else 'exit_time'
                    g=[x for x in g if (x[timekey][:4]<'2025')==before]
            else:
                def label(x):
                    t=x['exit_time'];return t[:4] if key=='year' else t[:7] if key=='month' else t[:4]+'Q'+str((int(t[5:7])-1)//3+1)
                g=[x for x in g if label(x)==r[key]]
            x=[float(t['net_R']) for t in g]
            equal(float(r['trades']),len(g),file+':count',0)
            equal(float(r['net_R']),sum(x),file+':sum')
            equal(float(r['gross_R']),sum(float(t['gross_R']) for t in g),file+':gross')
            equal(float(r['cost_R']),sum(float(t['cost_R']) for t in g),file+':cost')
            equal(float(r['max_closed_R_DD']),dd(x),file+':dd')
            if x:equal(float(r['expectancy_R']),mean(x),file+':mean')
            wins=[v for v in x if v>0];losses=[v for v in x if v<0]
            if losses:equal(float(r['net_PF']),sum(wins)/-sum(losses),file+':PF')
            elif r['net_PF']:errors.append({'label':'UNDEFINED_PF_SHOULD_BE_EMPTY'})
            if x:equal(float(r['win_rate']),len(wins)/len(x),file+':win_rate')
    result={'status':'FAIL' if errors else 'PASS','comparisons':comparisons,'max_roundtrip_csv_numeric_delta':maximum,
            'tolerance':1e-7,'errors':errors,'implementation':'independent csv/statistics arithmetic and temporal audit'}
    (out/'independent_table_audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result))
    if errors:raise SystemExit(1)


if __name__=='__main__':
    import sys
    audit(Path(sys.argv[1]))
