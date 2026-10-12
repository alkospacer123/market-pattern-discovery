"""Second implementation audit: standard-library indicators and replay.

Does not import engine.py, research.py, or TradingSystemLab. Independently parses
only the permitted prefix, derives features recursively and simulates positions.
External reviewer independence is still pending; this is algorithmic validation.
"""
import argparse
import ast
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
BASE = '7927d3d6b465ec1bceae51ec8121def5e7c7e191'
PIN = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1048576), b''):
            digest.update(b)
    return digest.hexdigest()


def prefix(path):
    data = []
    with path.open('rb') as f:
        assert f.readline().strip() == b'Ticker;Datetime;Open;High;Low;Close;Volume'
        while True:
            parts, separators = bytearray(), 0
            while separators < 2:
                b = f.read(1)
                if not b: break
                parts += b
                separators += b == b';'
            if not parts: break
            assert separators == 2
            stamp = parts.decode().split(';')[1]
            if stamp >= '2025-01-01': break
            tail = f.readline().decode().strip().split(';')
            if stamp < '2023-01-01': continue
            at = datetime.fromisoformat(stamp+'+03:00')+timedelta(minutes=15)
            if at.year >= 2025: continue
            data.append({'at':at, 'o':float(tail[0]),'h':float(tail[1]),'l':float(tail[2]),'c':float(tail[3])})
    assert all(a['at'] < b['at'] for a,b in zip(data,data[1:]))
    return data


def smooth(values, alpha, minimum):
    """Independent recursive adjust=False exponential average with NaN handling."""
    value, count, weight, out = None, 0, 1., []
    for x in values:
        finite = x is not None and math.isfinite(x)
        if value is None:
            if finite: value, count = x, 1
        else:
            weight *= 1-alpha
            if finite:
                value = (weight*value+alpha*x)/(weight+alpha)
                weight, count = 1., count+1
        out.append(value if count >= minimum else None)
    return out


def features(rows, p):
    def true_ranges(bars):
        previous = None
        out = []
        for b in bars:
            out.append(max(b['h']-b['l'], abs(b['h']-previous) if previous is not None else 0., abs(b['l']-previous) if previous is not None else 0.))
            previous = b['c']
        return out
    higher, group, date = [], [], None
    def emit(g):
        for k in range(0,len(g),4):
            b = g[k:k+4]
            if len(b)==4 and all(y['at']-x['at']==timedelta(minutes=15) for x,y in zip(b,b[1:])):
                higher.append({'at':b[-1]['at'], 'o':b[0]['o'], 'h':max(x['h'] for x in b), 'l':min(x['l'] for x in b), 'c':b[-1]['c']})
    for b in rows:
        if b['at'].date() != date:
            emit(group); group=[]; date=b['at'].date()
        group.append(b)
    emit(group)
    atr = smooth(true_ranges(rows), 1/p['atr_period'], p['atr_period'])
    ha = smooth(true_ranges(higher), 1/p['atr_period'], p['atr_period'])
    ema = smooth([b['c'] for b in higher],2/(p['ema_period']+1),p['ema_period'])
    up, down = [0.], [0.]
    for a,b in zip(higher,higher[1:]):
        u,d=b['h']-a['h'],a['l']-b['l']
        up.append(u if u>d and u>0 else 0.)
        down.append(d if d>u and d>0 else 0.)
    plus=smooth(up,1/p['adx_period'],p['adx_period'])
    minus=smooth(down,1/p['adx_period'],p['adx_period'])
    # The shared ATR denominator cancels algebraically in DX.
    dx=[100*abs(a-b)/(a+b) if a is not None and b is not None and a+b>0 else None for a,b in zip(plus,minus)]
    adx=smooth(dx,1/p['adx_period'],p['adx_period'])
    regimes=[]
    for i,b in enumerate(higher):
        slope=ema[i]-ema[i-p['slope_lookback']] if i>=p['slope_lookback'] and ema[i] is not None and ema[i-p['slope_lookback']] is not None else None
        window=ha[max(0,i-p['atr_average_period']+1):i+1]
        average=sum(window)/len(window) if len(window)==p['atr_average_period'] and all(v is not None for v in window) else None
        regime=0
        if slope is not None and adx[i] is not None and average is not None and adx[i]>p['adx_threshold'] and ha[i]>average:
            if b['c']>ema[i] and slope>0: regime=1
            if b['c']<ema[i] and slope<0: regime=-1
        regimes.append(regime)
    cursor=-1
    out=[]
    for i,b in enumerate(rows):
        while cursor+1<len(higher) and higher[cursor+1]['at']<=b['at']: cursor+=1
        regime=regimes[cursor] if cursor>=0 else 0
        previous=rows[max(0,i-p['breakout_period']):i]
        signal=0
        if len(previous)==p['breakout_period']:
            if regime==1 and b['c']>max(x['h'] for x in previous): signal=1
            if regime==-1 and b['c']<min(x['l'] for x in previous): signal=-1
        out.append(b|{'atr':atr[i],'signal':signal})
    return out


def simulate(rows,p,unit):
    trades, pos = [],None
    for i,b in enumerate(rows):
        if pos:
            sign=pos['sign']
            stop=pos['stop']
            if (sign==1 and b['l']<=stop) or (sign==-1 and b['h']>=stop):
                exit_price=min(b['o'],stop) if sign==1 else max(b['o'],stop)
                entry=pos['entry']; risk=abs(entry-pos['initial_stop'])
                path=rows[pos['index']+1:i]
                highs=[entry]+[r['h'] for r in path]; lows=[entry]+[r['l'] for r in path]
                mae=max(0.,entry-min(lows) if sign==1 else max(highs)-entry,sign*(entry-exit_price))/risk
                mfe=max(0.,max(highs)-entry if sign==1 else entry-min(lows))/risk
                gross=sign*(exit_price-entry)/risk
                trades.append({'entry_time':pos['at'].isoformat(), 'exit_time':b['at'].isoformat(),
                    'direction':'LONG' if sign==1 else 'SHORT', 'entry_price':entry, 'initial_stop':pos['initial_stop'],
                    'initial_risk':risk, 'exit_price':exit_price, 'gross_R':gross, 'net_R':gross-2*unit/risk,
                    'C1_R':2*unit/risk,'MAE_R':mae,'MFE_R':mfe,'bars_held':i-pos['index'],
                    'holding_minutes':(b['at']-pos['at']).total_seconds()/60,
                    'exit_type':'INITIAL_STOP' if stop==pos['initial_stop'] else 'RATCHETED_STOP'})
                pos=None
            else:
                extreme=max([pos['entry']]+[r['h'] for r in rows[pos['index']+1:i+1]]) if sign==1 else min([pos['entry']]+[r['l'] for r in rows[pos['index']+1:i+1]])
                candidate=extreme-sign*p['trail_atr']*b['atr']
                pos['stop']=max(stop,candidate) if sign==1 else min(stop,candidate)
        if pos is None and b['atr'] is not None and b['signal']:
            stop=b['c']-b['signal']*p['stop_atr']*b['atr']
            pos={'sign':b['signal'],'entry':b['c'],'initial_stop':stop,'stop':stop,'at':b['at'],'index':i}
    return trades,pos


def main(data_root, root):
    results=[]
    manifest=json.loads((root/'SOURCE_MANIFEST.json').read_text())
    configs=json.loads((root/'BASELINE_CONFIGS.json').read_text())['fixed_control_versions']
    specs=json.loads((HERE/'SPEC_EVIDENCE.json').read_text())['instruments']
    with (root/'trades.csv').open() as f: actual=list(csv.DictReader(f))
    opened=json.loads((root/'OPEN_POSITIONS.json').read_text())
    open_count=0
    for source in manifest['sources']:
        symbol=source['instrument']; path=data_root/source['path']
        assert sha(path)==source['full_sha256']
        blob=subprocess.check_output(['git','-C',str(data_root),'rev-parse',f"{PIN}:{source['path']}"]).decode().strip()
        assert blob==source['git_blob_sha']
        data=prefix(path)
        assert len(data)==source['used_candles']
        unit=specs[symbol]['research_c1_unit']
        if symbol in ('GLDRUBF','IMOEXF'):
            assert all(Decimal(str(b[c]))%Decimal(str(unit))==0 for b in data for c in ['o','h','l','c'])
        for v,p in configs.items():
            expected,residual=simulate(features(data,p['parameters']),p['parameters'],unit)
            saved_open=[r for r in opened if r['instrument']==symbol and r['version']==v]
            assert len(saved_open)==int(residual is not None)
            if residual:
                open_count+=1
                assert datetime.fromisoformat(saved_open[0]['entry_time'])==residual['at']
                assert abs(saved_open[0]['entry_price']-residual['entry'])<1e-8
                assert abs(saved_open[0]['initial_stop']-residual['initial_stop'])<1e-8
            saved=[r for r in actual if r['instrument']==symbol and r['version']==v]
            assert len(expected)==len(saved),(symbol,v,len(expected),len(saved))
            max_delta=0.
            for a,b in zip(expected,saved):
                for field,value in a.items():
                    if field.endswith('_time'):
                        assert datetime.fromisoformat(value)==datetime.fromisoformat(b[field])
                    elif isinstance(value,str): assert value==b[field],(symbol,v,field)
                    else:
                        delta=abs(value-float(b[field])); max_delta=max(max_delta,delta)
                        assert delta<=1e-8,(symbol,v,field,delta)
            results.append({'version':v,'instrument':symbol,'trades':len(saved),'maximum_numeric_difference':max_delta,'independent_replay':'PASS'})
    for file in ('engine.py','research.py','audit.py','test_research.py'):
        tree=ast.parse((HERE/file).read_text())
        imports=[node.module or '' for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        imports += [n.name for node in ast.walk(tree) if isinstance(node,ast.Import) for n in node.names]
        assert not any('TradingSystemLab' in name for name in imports)
    hashes=json.loads((root/'ARTIFACT_SHA256.json').read_text())
    assert all(sha(root/name)==value for name,value in hashes.items())
    # Independently reconcile every calendar/instrument/direction report total.
    reconciled=0
    for filename in ('yearly_report.csv','quarterly_report.csv','monthly_report.csv','instrument_report.csv','direction_report.csv','exit_diagnostics.csv','mae_mfe_report.csv'):
        with (root/filename).open() as f:
            for row in csv.DictReader(f):
                if row.get('status')=='BLOCKED':continue
                selected=[r for r in actual if r['version']==row['version'] and (r['instrument']==row['instrument'] or row['instrument']=='ALL_FOUR' or (row['instrument']=='Si_CNY' and r['instrument'] in ('USDRUBF','CNYRUBF')))]
                if row.get('year'): selected=[r for r in selected if datetime.fromisoformat(r['exit_time']).year==int(row['year'])]
                if row.get('direction'):selected=[r for r in selected if r['direction']==row['direction']]
                if row.get('exit_type'):selected=[r for r in selected if r['exit_type']==row['exit_type']]
                if row.get('period'):
                    def period(r):
                        at=datetime.fromisoformat(r['exit_time'])
                        return f'{at.year}Q{(at.month-1)//3+1}' if 'Q' in row['period'] else f'{at.year}-{at.month:02d}'
                    selected=[r for r in selected if period(r)==row['period']]
                assert len(selected)==int(row['trades'])
                if 'net_R' in row:assert abs(sum(float(r['net_R']) for r in selected)-float(row['net_R']))<1e-8
                if row.get('PF'):
                    vals=[float(r['net_R']) for r in selected]
                    pf=sum(v for v in vals if v>0)/-sum(v for v in vals if v<0)
                    assert abs(pf-float(row['PF']))<1e-9
                vals=[float(r['net_R']) for r in selected]
                if vals:
                    equity=peak=drawdown=0.
                    streak=longest=0
                    for v in vals:
                        equity+=v;peak=max(peak,equity);drawdown=max(drawdown,peak-equity)
                        streak=streak+1 if v<0 else 0;longest=max(longest,streak)
                    checks={'gross_R':sum(float(r['gross_R']) for r in selected),
                        'expectancy_R':sum(vals)/len(vals), 'C1_total_R':sum(float(r['C1_R']) for r in selected),
                        'C1_mean_R':sum(float(r['C1_R']) for r in selected)/len(vals),
                        'win_rate':sum(v>0 for v in vals)/len(vals), 'max_drawdown_R':drawdown,
                        'max_losing_streak':longest, 'net_R_without_top5':sum(sorted(vals)[:-5]),
                        'mean_MAE_R':sum(float(r['MAE_R']) for r in selected)/len(vals),
                        'mean_MFE_R':sum(float(r['MFE_R']) for r in selected)/len(vals),
                        'mean_holding_minutes':sum(float(r['holding_minutes']) for r in selected)/len(vals),
                        'initial_stop_exits':sum(r['exit_type']=='INITIAL_STOP' for r in selected),
                        'ratcheted_stop_exits':sum(r['exit_type']=='RATCHETED_STOP' for r in selected)}
                    for threshold,col in [(0.5,'MFE_ge_0_5R_share'),(1,'MFE_ge_1R_share'),(2,'MFE_ge_2R_share')]:
                        checks[col]=sum(float(r['MFE_R'])>=threshold for r in selected)/len(vals)
                    checks['MFE_lt_0_5R_share']=sum(float(r['MFE_R'])<0.5 for r in selected)/len(vals)
                    for col,value in checks.items():
                        if row.get(col):assert abs(value-float(row[col]))<1e-8,(filename,col,value,row[col])
                reconciled+=1
    value={'status':'PASS','audit_type':'Independent standard-library indicator/replay implementation and report reconciliation; same author, external reviewer pending', 'record_checks':results,'closed_trades_checked':len(actual),'open_terminal_positions_checked':open_count,'report_rows_reconciled':reconciled,'artifact_hashes_verified':len(hashes),'no_executable_TradingSystemLab_imports':True,'tolerance_absolute':1e-8,'reviewer_independence':'PENDING_EXTERNAL_REVIEW'}
    (root/'AUDIT_RESULTS.json').write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
    print(json.dumps(value,sort_keys=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=HERE)
    args=parser.parse_args()
    main(args.data_root,args.output)
