"""Independent fresh raw-source scalar verification, including every diagnostic table."""
import argparse,csv,json
from pathlib import Path
import common as C,control as G,scalar_diagnostics as D

KEYS={'signal_features':['instrument','signal_time'],'trade_features':['instrument','trade_id'],'open_features':['instrument','trade_id'],'summary':['scope','direction','year'],'monthly':['scope','direction','month'],'entry_cohorts':['scope','direction','year'],'cuts':['scope','direction','year','feature','bin'],'feature_distributions':['scope','direction','year','outcome','feature'],'funnel':['scope','direction','period','decision_reason'],'matched_dates':['instrument','MM_DD'],'matched_cohorts':['scope','direction','year'],'winner_entries':['instrument','trade_id'],'outcome_anatomy':['scope','direction','year','fate']}

def run(root,primary,output):
    output.mkdir(parents=True,exist_ok=True)
    scalars,sources=G.load(root,True);out=G.compute(scalars,['TRAIL_375'],True)
    G.persist(out,output/'replay');G.gate(out,output/'replay',True)
    cmp=C.Comparison()
    for name in G.NAMES:
        suffix='.json' if 'POSITIONS' in name else '.csv'
        path=primary/'control'/(name+suffix)
        expected=json.loads(path.read_text()) if suffix=='.json' else list(csv.DictReader(path.open()))
        fields={k for r in expected for k in r}
        keys=['instrument']+(['trade_id'] if name in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if name=='stop_decisions' else ['signal_time'] if name=='entry_opportunities' else ['current_close'] if name=='observed_gaps' else ['month'])
        cmp.rows([{k:r.get(k) for k in fields} for r in out[name]],expected,'REPLAY_'+name,keys)
    tables=D.calculate(out,scalars,sources);published=json.loads((primary/'TABLES.json').read_text())
    assert set(tables)==set(published)
    for name,rows in tables.items():
        csv_rows=list(csv.DictReader((primary/(name+'.csv')).open()))
        cmp.rows(rows,csv_rows,'CSV_'+name,KEYS[name]);cmp.rows(rows,published[name],'JSON_'+name,KEYS[name])
    C.write_csv(output/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables,'independence':'separate scalar source recursions, position machine, feature enrichment, windows, quantiles and aggregations; primary diagnostics/engine/metrics not imported; common metadata/serialization/comparison shared; same author; human review pending','CLOSED':len(out['trades']),'terminal_OPEN':len(out['OPEN_POSITIONS']),'stop_decisions':len(out['stop_decisions'])}
    C.write_json(output/'AUDIT_RESULT.json',result)
    assert not cmp.diffs,'INDEPENDENT_AUDIT_FAILED_STOP'
    print(json.dumps({k:result[k] for k in ('status','fields_compared','differences','max_numeric_delta')}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.data_root,a.primary,a.output)
