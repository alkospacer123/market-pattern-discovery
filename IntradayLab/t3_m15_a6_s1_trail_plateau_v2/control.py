"""Mandatory full #505 frozen-journal and published-economy controls before candidates."""
import json,csv,io
from pathlib import Path
import common as C
from scalar_metrics import stats
NAMES=('trades','OPEN_POSITIONS','stop_decisions','entry_opportunities','observed_gaps','PERIOD_END_OPEN_POSITIONS')
CONTROLS={'TRAIL_350':'TRAIL_350','TRAIL_375':'TRAIL_375'}
SOURCE='IntradayLab/t3_m15_a6_s1_trail_optimization_v1/results/'

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
    cmp=C.Comparison();summary=[]
    for k in NAMES:
        raw=C.historical(SOURCE+'replay/'+k+('.json' if 'POSITIONS' in k else '.csv'))
        ref=json.loads(raw) if 'POSITIONS' in k else list(csv.DictReader(io.StringIO(raw.decode())))
        ref=[r for r in ref if r['version'] in CONTROLS]
        keys=['version','instrument']+(['trade_id'] if k in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if k=='stop_decisions' else ['signal_time'] if k=='entry_opportunities' else ['current_close'] if k=='observed_gaps' else ['month'])
        fields={field for row in ref for field in row}
        actual=[{field:row.get(field) for field in fields} for row in out[k]]
        cmp.rows(actual,ref,'PR505_'+k,keys)
    sources=json.loads((C.HERE/'SPEC.json').read_text())['sources']
    for name in ('summary','monthly'):
        ref=[r for r in C.reference(SOURCE+name+'.csv') if r['variant'] in CONTROLS];actual=[]
        assert len(ref)==len(CONTROLS)*5*3*(3 if name=='summary' else 24)
        for r in ref:
            v=r['variant'];symbols=C.SYMBOLS if r['scope']=='ALL_FOUR' else [r['scope']]
            t=[x for x in out['trades'] if x['version']==v and x['instrument'] in symbols and (r['direction']=='ALL' or x['direction']==r['direction'])]
            calendar=C.CALENDAR
            if name=='summary' and r['year']!='ALL':calendar=[m for m in calendar if m.startswith(r['year'])];t=[x for x in t if str(x['exit_time'].year)==r['year']]
            if name=='monthly':calendar=[r['month']];t=[x for x in t if x['exit_time'].strftime('%Y-%m')==r['month']]
            a={k:r[k] for k in ('variant','scope','direction')}|{'trail_atr':C.VERSIONS[v]}|stats(t,calendar)
            if name=='summary':
                o=out['OPEN_POSITIONS'] if r['year']=='ALL' else [x for x in out['PERIOD_END_OPEN_POSITIONS'] if x['month']==r['year']+'-12']
                a.update(year=r['year'],period_end_OPEN=sum(x['version']==v and x['instrument'] in symbols and (r['direction']=='ALL' or x['direction']==r['direction']) for x in o))
            else:
                first=min(s['first_close'][:7] for s in sources if s['instrument'] in symbols)
                a.update(month=r['month'],coverage='NO_COVERAGE' if r['month']<first else 'AVAILABLE_PARTIAL_START' if r['month']==first and r['scope'] in ('GLDRUBF','IMOEXF') else 'AVAILABLE')
            actual.append(a)
        cmp.rows(actual,ref,'PR505_'+name,['variant','scope','direction','year' if name=='summary' else 'month'])
    for v in CONTROLS:
        t=[r for r in out['trades'] if r['version']==v];m=stats(t,C.CALENDAR)
        a=stats([r for r in t if r['exit_time'].year==2023],C.CALENDAR[:12]);b=stats([r for r in t if r['exit_time'].year==2024],C.CALENDAR[12:])
        op=sum(r['version']==v for r in out['OPEN_POSITIONS']);nov=sum(r['gross_R'] for r in t if r['exit_time'].year==2024 and r['exit_time'].month==11)/b['gross_R']
        summary.append({'variant':v,'PF2023':a['gross_PF'],'PF2024':b['gross_PF'],'OPEN':op,'positive2023':a['positive_months'],'positive2024':b['positive_months'],'november_share_2024_R':nov}|m)
        if v=='TRAIL_375':
            targets=json.loads((C.HERE/'SPEC.json').read_text())['leader_checks']
            values={'PF2023':round(a['gross_PF'],10),'PF2024':round(b['gross_PF'],10),'PF_ALL':round(m['gross_PF'],10),'R_ALL':round(m['gross_R'],6),'CLOSED':m['closed'],'OPEN':op,'positive2023':a['positive_months'],'positive2024':b['positive_months'],'positive_ALL':m['positive_months'],'DD_ALL':round(m['closed_R_drawdown'],6),'november_share_2024_percent':round(100*nov,4)}
            for key,value in values.items():cmp.value(value,targets[key],'USER_FROZEN_LEADER',v,key)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','implementation':'scalar' if scalar else 'primary','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables,'summary':summary,'full_published_journals_checked':True,'published_summary_monthly_all_fields_checked':True,'frozen_leader_parameters_unchanged':True}
    C.write_csv(d/'CONTROL_DIFF.csv',cmp.diffs,['table','row','field','actual','expected']);C.write_json(d/'CONTROL_GATE.json',result)
    assert not cmp.diffs,'CONTROL_MISMATCH_STOP_PLATEAU'
    return result

def feature_gate(primary,scalar,output):
    """All source bars, indicators, H1 availability and signal identities before candidates."""
    import pandas as pd
    cmp=C.Comparison()
    for symbol in C.SYMBOLS:
        actual=[];expected=[]
        for at,row in primary[symbol].iterrows():
            actual.append({'at':at}|{k:None if pd.isna(v) else int(v) if k=='Signal' else v for k,v in row.items()})
        for b in scalar[symbol]:
            r={'at':b['at']}|{k:b[v] for k,v in [('Open','o'),('High','h'),('Low','l'),('Close','c'),('Volume','v'),('ATR','atr'),('PreviousATR','previous_atr'),('PriorHigh','upper'),('PriorLow','lower'),('Signal','signal')]}
            for label,key in [('ADX','adx'),('Slope','slope'),('ATRRatio','ratio'),('AvailableAt','at')]:
                r['H1'+label]=b['h1'][key] if b['h1'] else None;r['H1Previous'+label]=b['previous_h1'][key] if b['previous_h1'] else None
            expected.append(C.plain(r))
        cmp.rows(actual,expected,symbol+'_FEATURES',['at'])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','bars':sum(len(x) for x in scalar.values()),'fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables}
    C.write_json(output/'FEATURE_CONTROL.json',result);C.write_csv(output/'FEATURE_CONTROL_DIFF.csv',cmp.diffs,['table','row','field','actual','expected']);assert not cmp.diffs,'FEATURE_CONTROL_STOP'
    return result
