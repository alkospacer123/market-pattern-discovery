"""Only the frozen control is replayed. Any discrepancy stops the task."""
import json, csv, io
from pathlib import Path
import common as C, control as G
from scalar_metrics import stats

def latest_gate(out, output):
    cmp=C.Comparison()
    for name in G.NAMES:
        suffix='.json' if 'POSITIONS' in name else '.csv'
        raw=C.historical('IntradayLab/t3_m15_a6_s1_trail_plateau_v2/results/replay/'+name+suffix)
        ref=json.loads(raw) if suffix=='.json' else list(csv.DictReader(io.StringIO(raw.decode())))
        ref=[r for r in ref if r['version']=='TRAIL_375']
        fields={k for r in ref for k in r}
        keys=['instrument']+(['trade_id'] if name in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if name=='stop_decisions' else ['signal_time'] if name=='entry_opportunities' else ['current_close'] if name=='observed_gaps' else ['month'])
        cmp.rows([{k:r.get(k) for k in fields} for r in out[name]],ref,'PR506_'+name,keys)
    for year,targets in [(2023,{'gross_PF':2.207278,'gross_R':90.390672}),(2024,{'gross_PF':1.772134,'gross_R':122.131984})]:
        m=stats([r for r in out['trades'] if r['exit_time'].year==year], [x for x in C.CALENDAR if x.startswith(str(year))])
        for k,v in targets.items():cmp.value(round(m[k],6),v,'USER_ANNUAL',year,k)
    m=stats([r for r in out['trades'] if r['exit_time'].year==2024 and r['direction']=='SHORT'],C.CALENDAR[12:])
    for k,v in {'closed':148,'gross_PF':1.473497,'gross_R':38.321290}.items():cmp.value(round(m[k],6),v,'USER_SHORT_2024',2024,k)
    for month,target in [('2024-05',-2.872841),('2024-10',0.209898)]:
        r=stats([r for r in out['trades'] if r['exit_time'].strftime('%Y-%m')==month],[month])
        cmp.value(round(r['gross_R'],6),target,'USER_WEAK_MONTH',month,'gross_R')
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'tables':cmp.tables,'short_2024':m}
    C.write_json(output/'PR506_GATE.json',result);C.write_csv(output/'PR506_DIFF.csv',cmp.diffs,['table','row','field','actual','expected'])
    assert not cmp.diffs,'CONTROL_MISMATCH_STOP_ENTRY_DIAGNOSTICS'
    return result

def run(root,output):
    output.mkdir(parents=True,exist_ok=True)
    primary,sources=G.load(root);scalar,_=G.load(root,True)
    feature=G.feature_gate(primary,scalar,output)
    a=G.compute(primary,['TRAIL_375']);G.persist(a,output/'control')
    p=G.gate(a,output/'control');p506=latest_gate(a,output/'control')
    b=G.compute(scalar,['TRAIL_375'],True);G.persist(b,output/'control_scalar')
    s=G.gate(b,output/'control_scalar',True);s506=latest_gate(b,output/'control_scalar')
    print(json.dumps({'control_primary':p['status'],'control_scalar':s['status'],'PR506_primary':p506['status'],'PR506_scalar':s506['status'],'feature':feature['status'],'closed':len(a['trades']),'stops':len(a['stop_decisions']),'signals':len(a['entry_opportunities'])}),flush=True)
    return primary,scalar,a,b,sources

if __name__=='__main__':run(Path('/workspace/market-pattern-data'),C.HERE/'results')
