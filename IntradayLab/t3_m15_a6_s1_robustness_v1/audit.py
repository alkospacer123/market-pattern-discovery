"""Fresh scalar raw replay plus separately computed diagnostics and presentation verification."""
import argparse,csv,io,json,re
from pathlib import Path
from datetime import datetime
import common as C,control as G,integrity as F,scalar_analysis as I

def read_csv(path):return list(csv.DictReader(Path(path).open()))

def presentation(primary,independent,d):
    cmp=C.Comparison();tables=0;cells=0;rows=0
    keys={'summary':['scope','direction','year'],'scenario_summary':['scenario','scope','direction','year'],
          'top_winners':['year','direction','rank'],'november2024':['scope','direction'],'monthly':['scope','direction','year','month']}
    for filename in ['REPORT.md','MONTHLY_DETAIL.md']:
        lines=(primary/filename).read_text().splitlines();i=0
        while i<len(lines):
            if not lines[i].startswith('<!-- table:'):i+=1;continue
            name=lines[i][11:-4].strip();i+=1
            fields=[s.strip() for s in lines[i].strip('|').split('|')];i+=2;actual=[]
            while i<len(lines) and lines[i].startswith('|'):
                values=[s.strip() for s in lines[i].strip('|').split('|')];assert len(values)==len(fields)
                actual.append(dict(zip(fields,values)));i+=1
            references=independent[name]
            cmp.value(len(actual),len(references),filename+':'+name,0,'row_count')
            lookup={tuple(str(C.plain(r[k])) for k in keys[name]):r for r in references}
            for index,r in enumerate(actual):
                key=tuple(r[k] for k in keys[name]);assert key in lookup,(name,key)
                reference=lookup[key]
                for field,value in r.items():
                    original=reference[field]
                    if isinstance(original,float):expected=f'{original:.6f}'
                    elif original is None:expected='N/A'
                    else:expected=str(original)
                    if isinstance(original,(int,float)) and not isinstance(original,bool):
                        cmp.value(float(value),float(expected),filename+':'+name,index,field)
                    else:cmp.value(value,expected,filename+':'+name,index,field)
                    cells+=1
            tables+=1;rows+=len(actual)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','tables':tables,'rows':rows,'cells':cells,'differences':len(cmp.diffs)}
    C.write_json(d/'PRESENTATION_AUDIT.json',result);C.write_csv(d/'PRESENTATION_DIFF.csv',cmp.diffs,['table','row','field','actual','expected'])
    assert not cmp.diffs,'PRESENTATION_FAIL';return result

def audit(root,primary,d):
    F.freeze_guard();d.mkdir(parents=True,exist_ok=True)
    frames,sources=C.load_sources(root) # streaming scalar indicators; no dataframe features
    out=G.compute(frames,['TRAIL_375'],True);G.persist(out,d/'control')
    gate=G.gate(out,d/'control',True);multi=G.multi_gate(out,d/'control')
    C.write_json(d/'CAUSAL_INVARIANTS.json',F.causal(out))
    cmp=C.Comparison()
    for name in G.NAMES:
        expected=json.loads((primary/'control'/(name+'.json')).read_text()) if 'POSITIONS' in name else read_csv(primary/'control'/(name+'.csv'))
        fields=sorted(set(k for r in expected for k in r)|set(k for r in out[name] for k in r))
        actual=[{k:r.get(k) for k in fields} for r in out[name]]
        expected=[{k:r.get(k) for k in fields} for r in expected]
        keys=['instrument']+(['trade_id'] if name in ['trades','OPEN_POSITIONS'] else ['bar_close_time'] if name=='stop_decisions' else ['signal_time'] if name=='entry_opportunities' else ['current_close'] if name=='observed_gaps' else ['month'])
        cmp.rows(actual,expected,'PRIMARY_SCALAR_'+name,keys)
    independent=I.evaluate(out)
    primary_json=json.loads((primary/'TABLES.json').read_text())
    for name,rows in independent.items():
        C.write_csv(d/(name+'.csv'),rows)
        # Identity-only keys prevent tiny independent floating-point deltas changing order.
        keys={'summary':['scope','direction','year'],'monthly':['scope','direction','year','month'],
              'loss_runs':['scope','direction','year','series_type','start','end'],
              'scenario_summary':['scenario','scope','direction','year'],
              'scenario_monthly':['scenario','scope','direction','year','month'],
              'scenario_ledger':['scenario','scope','direction','year','instrument','trade_id'],
              'top_winners':['year','direction','rank'],'november2024':['scope','direction']}[name]
        ref=read_csv(primary/(name+'.csv'))
        normalized=[{k:datetime.fromisoformat(v) if k in ['exit_time','entry_time','signal_time'] and v else v for k,v in r.items()} for r in ref]
        cmp.rows(rows,normalized,name+'_CSV',keys)
        j=primary_json[name]
        normalized=[{k:datetime.fromisoformat(v) if k in ['exit_time','entry_time','signal_time'] and v else v for k,v in r.items()} for r in j]
        cmp.rows(rows,normalized,name+'_JSON',keys)
    C.write_json(d/'TABLES.json',independent)
    shown=presentation(primary,independent,d)
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),
        'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables,
        'fresh_raw_scalar_CONTROL':gate['status'],'PR506_508':multi['status'],'presentation':shown['status'],
        'primary_engine_analysis_metrics_imported':False,'independence':'computational; one author; external human review PENDING'}
    C.write_json(d/'AUDIT_RESULT.json',result);C.write_csv(d/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    assert not cmp.diffs,'INDEPENDENT_AUDIT_FAIL'
    print(json.dumps({k:result[k] for k in ['status','fields_compared','differences','max_numeric_delta','presentation']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit')
    a=p.parse_args();audit(a.data_root,a.primary,a.output)
