"""Fresh scalar replay and independent aggregation from read-only raw prefix."""
import argparse,csv,json
from pathlib import Path
import common as C,control as G,run_control as R,scalar_analysis as A
KEYS={'summary':['variant','scope','direction','year'],'monthly':['variant','scope','direction','month'],'trade_comparison':['instrument','signal_time','direction'],'signal_comparison':['instrument','signal_time'],'cohort32':['instrument','signal_time'],'winner_retention':['instrument','signal_time'],'effect_summary':['scope','direction','year']}

def run(root,primary,output):
    freeze=json.loads((C.HERE/'FREEZE.json').read_text())
    for n,h in freeze['code_spec_sha256'].items():assert C.file_sha(C.HERE/n)==h,('FROZEN_CHANGED',n)
    output.mkdir(parents=True,exist_ok=True);frames,sources=G.load(root,True)
    baseline=G.compute(frames,['TRAIL_375'],True);G.persist(baseline,output/'control');G.gate(baseline,output/'control',True);R.latest_gate(baseline,output/'control')
    experiment=G.compute(frames,['EARLY_PROTECT_05'],True);G.persist(experiment,output/'experiment');cmp=C.Comparison()
    for label,path in [('control',baseline),('experiment',experiment)]:
        for name in G.NAMES:
            suffix='.json' if 'POSITIONS' in name else '.csv';p=primary/label/(name+suffix)
            ref=json.loads(p.read_text()) if suffix=='.json' else list(csv.DictReader(p.open()))
            keys=['instrument']+(['trade_id'] if name in ('trades','OPEN_POSITIONS') else ['bar_close_time'] if name=='stop_decisions' else ['signal_time'] if name=='entry_opportunities' else ['current_close'] if name=='observed_gaps' else ['month'])
            fields={k for r in ref for k in r};cmp.rows([{k:r.get(k) for k in fields} for r in path[name]],ref,label+'_'+name,keys)
    tables=A.calculate(baseline,experiment,sources);published=json.loads((primary/'TABLES.json').read_text());assert tables.keys()==published.keys()
    for name,rows in tables.items():
        C.write_csv(output/(name+'.csv'),rows);cmp.rows(rows,list(csv.DictReader((primary/(name+'.csv')).open())),'CSV_'+name,KEYS[name]);cmp.rows(rows,published[name],'JSON_'+name,KEYS[name])
    C.write_json(output/'TABLES.json',tables)
    # Exhaustive causal invariants on both paths, independent from the primary engine.
    causal=0
    for path,early in [(baseline,False),(experiment,True)]:
        previous={};trades={(t['instrument'],t['trade_id']):t for t in path['trades']+path['OPEN_POSITIONS']}
        for r in path['stop_decisions']:
            causal+=1
            # Direction is resolved from entry identities, not OHLC.
            t=trades[r['instrument'],r['trade_id']];side=1 if t['direction']=='LONG' else -1;k=r['instrument'],r['trade_id'];old=previous.get(k)
            if old is not None:assert r['active_stop']==old['active_stop_next_bar']
            opening=side*(r['open']-r['active_stop'])<=0;hit=opening or (r['low']<=r['active_stop'] if side==1 else r['high']>=r['active_stop'])
            assert hit==r['stop_hit']
            if r['phase']=='EXIT':
                assert r['extreme_after'] is None and not r['threshold_activated_now']
                if early:assert not r['early_activated_now'] and not r['early_stop_changed']
            else:
                assert side*(r['active_stop_next_bar']-r['active_stop'])>=-1e-12
                if early:
                    assert r['early_activated_after']==(r['early_activated_before'] or r['favorable_R_after']>=.5)
                    if r['early_activated_now']:assert r['early_activation_time_after']==r['bar_close_time'] and not r['early_activated_before']
                    if r['early_activated_after']:assert side*(r['active_stop_next_bar']-(t['entry_price']-side*.5*t['initial_risk']))>=-1e-10
                previous[k]=r
    C.write_csv(output/'DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not cmp.diffs else 'FAIL','fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0),'absolute_tolerance':1e-8,'tables':cmp.tables,'causal_bars_checked':causal,'independence':'stdlib timestamp-first scalar indicators/dict position state machine; separate joins and metrics; primary engine/analysis/metrics never imported; common metadata/serialization/comparison and control reference gates shared; same author; external human review PENDING'}
    C.write_json(output/'AUDIT_RESULT.json',result);assert not cmp.diffs,'AUDIT_FAILED'
    print(json.dumps({k:result[k] for k in ['status','fields_compared','differences','max_numeric_delta','causal_bars_checked']}),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,default=Path('/workspace/market-pattern-data'));p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--output',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.data_root,a.primary,a.output)
