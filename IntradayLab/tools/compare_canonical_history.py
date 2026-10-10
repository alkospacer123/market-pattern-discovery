"""Read immutable #463 ledgers via git show; never load its code as a module."""
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
import io
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PREFIX='IntradayLab/results/stage2_orb_false_break_fade_m5_v2_research/'


def normalized(value):
    if value in ('',None):
        return None
    if '2023-' in value and (' ' in value or 'T' in value):
        return datetime.fromisoformat(value).replace(tzinfo=None).isoformat(sep=' ')
    try:
        return Decimal(value)
    except InvalidOperation:
        return value


def compare(output, config):
    history={name:list(csv.DictReader(io.StringIO(subprocess.check_output(
        ['git','-C',str(ROOT),'show',config['historical_reference']+':'+PREFIX+name+'.csv'],text=True))))
        for name in ('trades','signals')}
    source=list(csv.DictReader((output/'coverage_daily.csv').open()))
    complete={(r['instrument'],r['date']) for r in source if r['status']=='COMPLETE'}
    discrepancies=[]; incomplete=[];counts={}; ntrades=0;by_instrument={}
    keys={
        'trades':('direction','signal_at','reclaim_start','sweep_start','waiting_bar_closed_at','order_sent_at',
                  'planned_execution_at','entry_at','entry_price','stop','take','risk','exit_at',
                  'exit_interval_start','exit_interval_end','exit_price','exit_reason','status',
                  'model_filled','cost_entry_c1','cost_c1','net_c1','net_R_c1'),
        'signals':('direction','sweep_start','signal_at','base_reason','status','reason','order_admitted','model_filled','stop')}
    for name in ('trades','signals'):
        actual=list(csv.DictReader((output/f'{name}.csv').open()))
        old={r['signal_id']:r for r in history[name] if r['architecture']=='A_BASE'}
        new={r['signal_id']:r for r in actual}
        compared=0
        for sid in sorted(set(old)|set(new)):
            record=new.get(sid,old.get(sid))
            day=str(record.get('signal_at') or record.get('sweep_start'))[:10]
            full=(record['instrument'],day) in complete
            if full:
                compared+=1
                if name=='trades':ntrades+=1
            failures=[]
            if sid not in old or sid not in new:
                failures.append(dict(table=name,signal_id=sid,field='ROW_SET',old=sid in old,new=sid in new))
            else:
                for key in keys[name]:
                    a,b=new[sid].get(key),old[sid].get(key)
                    if normalized(a)!=normalized(b):
                        failures.append(dict(table=name,signal_id=sid,field=key,old=b,new=a))
            (discrepancies if full else incomplete).extend(failures)
        counts[name]=compared
        for symbol in config['instruments']:
            item=by_instrument.setdefault(symbol,dict(complete_days=sum(s==symbol for s,d in complete)))
            item['complete_day_'+name]=sum(r['instrument']==symbol and
                (symbol,str(r.get('signal_at') or r.get('sweep_start'))[:10]) in complete for r in actual)
    return dict(status='PASS' if not discrepancies else 'FAIL',
                historical_commit=config['historical_reference'],complete_days=len(complete),
                complete_day_trades=ntrades,complete_day_rows=counts,by_instrument=by_instrument,
                discrepancies=discrepancies,incomplete_day_discrepancies=incomplete,
                numeric_comparison='Exact Decimal values; timestamps normalized MSK start labels',
                criterion='Exact agreement on fully sufficient source days; parameters unchanged')
