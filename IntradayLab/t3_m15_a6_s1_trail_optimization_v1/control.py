"""Mandatory #504 raw-journal and six-decimal published control gates."""
import json,csv,io
from pathlib import Path
import common as C
NAMES=('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')
CONTROLS={'TRAIL_300':'BASELINE','TRAIL_350':'OPTIMIZED'}
TARGETS={'TRAIL_300':(2.008704,1.511087,1.666690,155.290654,510,19,10.967348),'TRAIL_350':(2.089169,1.607206,1.759200,179.356582,495,17,15.142765)}

def load(root,scalar=False):
    if scalar:return C.load_sources(root)
    import engine as E
    assert C.git('rev-parse','HEAD',root=root).decode().strip()==C.DATA_SHA
    assert not C.git('status','--porcelain',root=root).strip()
    sources=json.loads((C.HERE/'SPEC.json').read_text())['sources'];frames={}
    for s in sources:
        p=root/s['path'];assert C.file_sha(p)==s['full_sha256']
        assert C.git('hash-object','--',str(p),root=root).decode().strip()==s['git_blob_sha']
        f=E.read_source(p)
        assert len(f)==s['used_candles'] and f.index[0].isoformat()==s['first_close'] and f.index[-1].isoformat()==s['last_close']
        frames[s['instrument']]=E.features(f)
    return frames,sources

def compute(frames,versions,scalar=False):
    assert set(versions)<=set(C.VERSIONS)
    if scalar:
        import scalar as S
        replay=S.simulate
    else:
        import engine as E
        replay=E.replay
    out={k:[] for k in NAMES}
    for v in versions:
        for symbol in C.SYMBOLS:
            result=replay(frames[symbol],symbol,v,'C1','NEXT_OPEN')
            for k,rows in zip(out,result):out[k].extend(([rows] if rows else []) if k=='OPEN_POSITIONS' else rows)
    return out

def persist(out,d):
    d.mkdir(parents=True,exist_ok=True)
    for k,rows in out.items():
        if 'POSITIONS' in k:C.write_json(d/(k+'.json'),rows)
        else:C.write_csv(d/(k+'.csv'),rows)

def gate(out,d,scalar=False):
    from scalar_metrics import stats
    cmp=C.Comparison();summary=[]
    for k in NAMES:
        path='IntradayLab/t3_m15_execution_sensitivity_v1/results/next_open/'+k+('.json' if 'POSITIONS' in k else '.csv')
        raw=C.historical(path)
        ref=json.loads(raw) if 'POSITIONS' in k else list(csv.DictReader(io.StringIO(raw.decode())))
        ref=[r for r in ref if r['rule']=='C1']
        actual=[r|{'version':CONTROLS[r['version']]} for r in out[k]]
        keys=['version','instrument']+(['trade_id'] if k in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if k=='stop_decisions' else ['signal_time'] if k=='entry_opportunities' else ['current_close'] if k=='observed_gaps' else ['month'])
        fields={field for row in ref for field in row}
        actual=[{field:row.get(field) for field in fields} for row in actual]
        cmp.rows(actual,ref,'PR504_'+k,keys)
    for v,expected in TARGETS.items():
        t=[r for r in out['trades'] if r['version']==v]
        m=stats(t,C.CALENDAR);a=stats([r for r in t if r['exit_time'].year==2023],C.CALENDAR[:12]);b=stats([r for r in t if r['exit_time'].year==2024],C.CALENDAR[12:])
        vals=(a['gross_PF'],b['gross_PF'],m['gross_PF'],m['gross_R'],m['closed'],m['positive_months'],m['closed_R_drawdown'])
        for key,x,y in zip(('PF2023','PF2024','PF_ALL','R_ALL','CLOSED','positive_months','DD'),vals,expected):cmp.value(round(x,6),y,'PUBLISHED',v,key)
        summary.append({'variant':v,'PF2023':a['gross_PF'],'PF2024':b['gross_PF']}|m)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','implementation':'scalar' if scalar else 'primary','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables,'summary':summary}
    C.write_csv(d/'CONTROL_DIFF.csv',cmp.diffs,['table','row','field','actual','expected']);C.write_json(d/'CONTROL_GATE.json',result)
    assert not cmp.diffs,'CONTROL_MISMATCH_STOP_OPTIMIZATION'
    return result
