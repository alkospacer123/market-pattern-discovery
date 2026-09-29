"""Generate the deterministic Stage 6.5 SESSION_10_21 + LOCK1_AFTER_2R study."""
from __future__ import annotations

import hashlib, json, os, subprocess
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend
from TradingSystemLab.results.post_v3_analysis.stage6_fixed_basket_reassessment import generate_reassessment as frozen
from TradingSystemLab.results.post_v3_analysis.stage6_lock1_after_2r import generate_lock1_reassessment as base

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[3]
STARTING_MAIN_SHA="59a3bd6869fde3d14d15c2fd1f0bf521cbe2ab18"
PATHS=("FULL_CANONICAL","STRUCTURAL_STACK_V1"); SYMBOLS=frozen.SYMBOLS
TZ=ZoneInfo("Europe/Moscow"); TICK=.001

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def frame_sha(f): return base.frame_sha(f)
def session_eligible(t):
    t=pd.Timestamp(t)
    if t.tzinfo is None: raise ValueError("ENTRY_TIMESTAMP_MUST_BE_TIMEZONE_AWARE")
    m=t.tz_convert(TZ).hour*60+t.tz_convert(TZ).minute
    return 600 <= m < 1260

def replay_t3(frame,meta,stack=False):
    """Independent causal replay; lock state is snapshotted before each event."""
    strategy=T3MTFTrend(base._parameters()); high=DataLoader.h4_from_h1(frame)
    low,high=strategy.calculate_indicators(frame,high); cursor=-1; pos=None; out=[]; signals=[]
    for t,b in low.iterrows():
        while cursor+1<len(high) and high.index[cursor+1]<=t: cursor+=1
        regime=strategy.regime(high.iloc[cursor]) if cursor>=0 else None
        if pos is not None:
            active=bool(pos['armed']); canonical=pos['stop']; effective,binding=base.lock_levels(pos['direction'],pos['entry'],pos['risk'],canonical,stack and active)
            if active and pos['activation_time'] is None: pos['activation_time']=t
            if strategy.exit_signal(pos['direction'],b,effective):
                price=min(float(b.Open),effective) if pos['direction']=='LONG' else max(float(b.Open),effective)
                reason='LOCK1_STOP' if binding else ('INITIAL_STOP' if effective==pos['initial'] else 'ATR_TRAILING_STOP')
                trade=base._record(meta,pos,t,price,reason); trade.update(reached_2r=pos['trigger_time'] is not None,lock1_became_binding=pos['ever_binding'] or binding,trigger_event_time=pos['trigger_time'],first_lock1_active_event=pos['activation_time'])
                out.append(trade); pos=None
            else:
                pos['ever_binding'] |= binding; pos['bars']+=1
                pos['extreme']=max(pos['extreme'],float(b.High)) if pos['direction']=='LONG' else min(pos['extreme'],float(b.Low))
                candidate=float(strategy.manage_position(pos['direction'],pos['extreme'],b.ATR))
                pos['stop']=max(canonical,candidate) if pos['direction']=='LONG' else min(canonical,candidate)
                reached=pos['extreme']>=pos['trigger'] if pos['direction']=='LONG' else pos['extreme']<=pos['trigger']
                if reached and not pos['armed']: pos['armed']=True; pos['trigger_time']=t
        if pos is None and pd.notna(b.ATR):
            signal=strategy.generate_signal(b,regime)
            if signal:
                allowed=(not stack) or session_eligible(t); signals.append({'lifecycle':meta['lifecycle'],'instrument':meta['instrument'],'time':t,'direction':signal,'allowed':allowed})
                if allowed:
                    entry=float(b.Close); stop=float(strategy.calculate_stop_loss(signal,entry,float(b.ATR))); risk=abs(entry-stop)
                    pos={'direction':signal,'entry':entry,'entry_time':t,'initial':stop,'risk':risk,'stop':stop,'extreme':entry,'bars':0,'seq':len(out)+1,'armed':False,'trigger_time':None,'activation_time':None,'trigger':entry+(2*risk if signal=='LONG' else -2*risk),'ever_binding':False}
    cols=base.EVENT_COLUMNS+['reached_2r','lock1_became_binding','trigger_event_time','first_lock1_active_event']
    return pd.DataFrame(out).reindex(columns=cols),pd.DataFrame(signals)

def replay_all(root,path):
    trades=[]; signals=[]
    for r in base.registry_rows():
        raw=DataLoader(forbid_true_oos=False).load_csv(Path(root)/'forever'/r['instrument']/f"{r['instrument']}_H1.csv")
        frame=DataLoader.close_index(raw,'1h').loc[r['start_timestamp']:r['end_timestamp']].copy()
        meta={k:r[k] for k in ('generation','lifecycle','fold_id','strategy','timeframe','instrument','candidate_config_identity')}
        a,s=replay_t3(frame,meta,path==PATHS[1]); trades.append(a); signals.append(s)
    t=pd.concat(trades,ignore_index=True).sort_values(['lifecycle','fold_id','exit_time','instrument','trade_id'],kind='mergesort').reset_index(drop=True)
    return t,pd.concat(signals,ignore_index=True)

def reconcile(paths):
    rows=[]
    for life in frozen.LIFECYCLES:
      for sym in SYMBOLS:
        a=paths[PATHS[0]].query('lifecycle==@life and instrument==@sym'); b=paths[PATHS[1]].query('lifecycle==@life and instrument==@sym'); keys=['direction','entry_time','entry_price']
        z=a.merge(b,on=keys,how='outer',suffixes=('_full','_stack'),indicator=True); both=z[z._merge=='both']; same=(both.exit_time_full==both.exit_time_stack)&np.isclose(both.exit_price_full,both.exit_price_stack)
        rows.append({'instrument':sym,'lifecycle':life,'FULL_trades':len(a),'STACK_trades':len(b),'matched_entries':len(both),'FULL_only_entries':(z._merge=='left_only').sum(),'STACK_only_entries':(z._merge=='right_only').sum(),'same_exits':same.sum(),'changed_exits':(~same).sum(),'FULL_net_R':a.net_R_C1.sum(),'STACK_net_R':b.net_R_C1.sum(),'delta_R':b.net_R_C1.sum()-a.net_R_C1.sum()})
    return pd.DataFrame(rows)

def session_funnel(signals,stack,rec):
    rows=[]
    for (life,sym),g in signals.groupby(['lifecycle','instrument']):
        q=stack.query('lifecycle==@life and instrument==@sym'); rr=rec.query('lifecycle==@life and instrument==@sym').iloc[0]
        rows.append({'instrument':sym,'lifecycle':life,'canonical_entry_signals':len(g),'in_session_entries':int(g.allowed.sum()),'out_of_session_rejected_signals':int((~g.allowed).sum()),'STACK_entries':len(q),'STACK_only_entries':int(rr.STACK_only_entries),'net_R':q.net_R_C1.sum()})
    return pd.DataFrame(rows)

def lock_funnel(stack):
    rows=[]
    for (sym,life,d),g in stack.groupby(['instrument','lifecycle','direction']):
        rows.append({'instrument':sym,'lifecycle':life,'direction':d,'STACK_trades':len(g),'reaching_2R':int(g.reached_2r.sum()),'lock_binding':int(g.lock1_became_binding.sum()),'LOCK1_STOP':int((g.exit_reason=='LOCK1_STOP').sum()),'resulting_net_R':g.net_R_C1.sum()})
    return pd.DataFrame(rows)

def component_table(stack_comp):
    files={'FULL_CANONICAL':HERE.parent/'stage6_session_10_21_causal/session_decision_comparison.csv','SESSION_10_21_CAUSAL':HERE.parent/'stage6_session_10_21_causal/session_decision_comparison.csv','LOCK1_AFTER_2R':HERE.parent/'stage6_lock1_after_2r/lock1_decision_comparison.csv'}
    rows=[]
    for name,p in files.items():
        x=pd.read_csv(p); source='FULL_CANONICAL' if name=='FULL_CANONICAL' else name; r=x[x.path==source].iloc[0].to_dict(); r['path']=name; rows.append(r)
    rows.append(stack_comp[stack_comp.path==PATHS[1]].iloc[0].to_dict()); return pd.DataFrame(rows)

def attribution(paths):
    sess=pd.read_csv(HERE.parent/'stage6_session_10_21_causal/session_10_21_trades.csv'); lock=pd.read_csv(HERE.parent/'stage6_lock1_after_2r/lock1_after_2r_trades.csv'); rows=[]
    for life in frozen.LIFECYCLES:
      for sym in SYMBOLS:
        val=lambda x:float(x.loc[(x.lifecycle==life)&(x.instrument==sym),'net_R_C1'].sum())
        f=val(paths[PATHS[0]]); sd=val(sess)-f; ld=val(lock)-f; actual=val(paths[PATHS[1]])-f
        rows.append({'lifecycle':life,'instrument':sym,'session_standalone_delta_R':sd,'LOCK1_standalone_delta_R':ld,'standalone_arithmetic_sum_R':sd+ld,'actual_STACK_delta_R':actual,'interaction_residual_R':actual-sd-ld})
    return pd.DataFrame(rows)

def comparison(year,life,roll,mon,conc):
    rows=[]
    for path in PATHS:
        y=year[year.path==path]; cal=y[y.lifecycle!='walk_forward']; lf=life[life.path==path]; rr=roll[roll.path==path]; mm=mon[mon.path==path]; cc=conc[conc.path==path]
        rows.append({'path':path,'all_annual_gates_pass':bool((y.net_R>0).all()),'annual_floor_R':cal.net_R.min(),'worst_12M_R':rr.worst_12M_R.min(),'worst_6M_R':rr.worst_6M_R.min(),'worst_DD_R':lf.max_DD_R.min(),'minimum_recovery_factor':lf.recovery_factor.min(),'positive_month_share':(mm.net_R>0).mean(),'median_monthly_R':mm.net_R.median(),'longest_negative_month_streak':max(base.streak(g.net_R) for _,g in mm.groupby('lifecycle')),'top_3_positive_month_concentration':cc.top_3_share_of_positive_R.max(),'chronological_net_R':cal.net_R.sum()})
    out=pd.DataFrame(rows); cols=['annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','median_monthly_R','longest_negative_month_streak','top_3_positive_month_concentration','chronological_net_R']; asc=[False]*7+[True,True,False]
    eligible=out[out.all_annual_gates_pass]; preferred=eligible.sort_values(cols,ascending=asc,kind='mergesort').iloc[0].path if len(eligible) else PATHS[0]; equal=all(np.isclose(out.iloc[0][x],out.iloc[1][x],atol=1e-9,rtol=0,equal_nan=True) for x in cols)
    decision='STRUCTURAL_STACK_V1_NO_MATERIAL_DIFFERENCE' if equal else ('STRUCTURAL_STACK_V1_ADMITTED' if preferred==PATHS[1] and bool(out.iloc[1].all_annual_gates_pass) else 'STRUCTURAL_STACK_V1_REJECTED_FULL_REMAINS_BENCHMARK')
    out['preferred_path']=preferred; out['computed_decision']=decision; out['tolerance']=1e-9; return out,decision

def authenticate(root):
    prior={d:{p.name:sha(p) for p in (HERE.parent/d).iterdir() if p.is_file()} for d in ['stage6_session_10_21_causal','stage6_one_bar_breakout_confirmation','stage6_exit_on_opposite_regime','stage6_lock1_after_2r']}
    source=json.loads((HERE.parent/'stage5_structural_validation/trail1/manifest_trail1.json').read_text())['source_hashes']; sources={k:v for k,v in source.items() if k.endswith('_H1.csv') and any(f'/{s}/' in k for s in SYMBOLS)}
    auth={'source_hashes':sources,'benchmark_hashes':{p.name:sha(p) for p in base.BENCH.iterdir() if p.is_file()}}
    checks={'strategy':sha(ROOT/'TradingSystemLab/strategies/trend/T3_MTF_Trend.py')==base.T3_SHA,'parameters':set(frozen.lifecycle_registry().query("lifecycle!='baseline'").strategy_parameter_hash)=={base.PARAM_SHA},'sources':len(sources)==4 and all(sha(Path(root)/p)==h for p,h in sources.items()),'old_stage6':sha(base.OLD_STAGE6)==base.OLD_STAGE6_SHA}
    if not all(checks.values()): raise RuntimeError(f'AUTHENTICATION_FAILED:{checks}')
    auth['starting_main_sha']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    if auth['starting_main_sha']!=STARTING_MAIN_SHA: raise RuntimeError('STARTING_MAIN_MISMATCH')
    auth['prior_stage_hashes']=prior; return auth

def report(a,m):
    y=a['yearly_metrics.csv']; c=a['structural_stack_decision_comparison.csv']; head=c.copy()
    for life,yr,label in base.views(): head[label]=head.path.map(lambda p,life=life,yr=yr: y.loc[(y.path==p)&(y.lifecycle==life)&(y.year==yr),'net_R'].iloc[0])
    cols=['path','Baseline 2023','Baseline 2024','WF 2024','OOS 2025','OOS 2026 YTD','annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','chronological_net_R','all_annual_gates_pass']
    lines=['# Final Stage 6.5 Structural Stack Report','',head[cols].to_markdown(index=False,floatfmt='.6f'),'','## Read-only component comparison','',a['stack_vs_components.csv'].to_markdown(index=False,floatfmt='.6f'),'','## Provenance and methodology',f"Starting main `{STARTING_MAIN_SHA}`; T3 `{base.T3_SHA}`; parameters `{base.PARAM_SHA}`. Original v1 H1 methodology applied independently to the v3 perpetual research generation. C1, tick 0.001.",'','## Exact definition and causal semantics','`STRUCTURAL_STACK_V1 = SESSION_10_21 + LOCK1_AFTER_2R`. Entries alone require 10:00 inclusive to 21:00 exclusive Europe/Moscow. A surviving +2R completed event arms the +1R floor/ceiling for the next event. Canonical ATR trailing can remain tighter; exits and gap handling are unrestricted. No ONE_BAR, opposite-regime exit, TRAIL1, or BE1.','',f"Two isolated raw replays matched: FULL `{m['deterministic_replay_hashes'][PATHS[0]][0]}`, STACK `{m['deterministic_replay_hashes'][PATHS[1]][0]}`. FULL core matches frozen canonical: `{m['full_core_match']}`.",'']
    sections=[('Frozen structural registry','structural_stack_registry.csv'),('FULL vs STACK yearly comparison','yearly_metrics.csv'),('Complete monthly FULL and STACK tables','monthly_metrics.csv'),('Instrument × month matrices — who earns and loses every month','instrument_monthly_metrics.csv'),('Instrument × year','instrument_yearly_metrics.csv'),('Direction results','direction_metrics.csv'),('Session funnel','stack_session_funnel.csv'),('LOCK1 funnel','stack_lock1_funnel.csv'),('Structural interaction','structural_stack_interaction.csv'),('Exit reasons','exit_reason_comparison.csv'),('Holding buckets','holding_bucket_comparison.csv'),('Trade-path reconciliation','full_vs_structural_stack_trade_path_reconciliation.csv'),('Interaction attribution','stack_interaction_attribution.csv'),('Rolling 3/6/12M','rolling_stability.csv'),('DD/recovery','lifecycle_metrics.csv'),('Monthly concentration','monthly_concentration.csv'),('Annual gates and frozen hierarchy','structural_stack_decision_comparison.csv')]
    for title,n in sections: lines += [f'## {title}','',a[n].to_markdown(index=False,floatfmt='.6f'),'']
    lines += ['## Complete frozen A–F monthly appendix','',pd.read_csv(base.BENCH/'basket_monthly_metrics.csv').to_markdown(index=False,floatfmt='.6f'),'','## Computed decision',f"**`{m['decision']}`**. The independent auditor recomputes this result rather than trusting it.",'','## Limitations and next step','This is retrospective evidence: 2025–2026 are revealed and 2026 is partial. WF remains separate. Stage 7 was not executed. The next roadmap step is basket-size research; it was not started.']
    return '\n'.join(lines)+'\n'

def execute(root,out=HERE):
    out=Path(out); auth=authenticate(root); paths={}; hashes={}; stack_signals=None
    for p in PATHS:
        a,s=replay_all(root,p); b,_=replay_all(root,p); hashes[p]=[frame_sha(a),frame_sha(b)]
        if hashes[p][0]!=hashes[p][1]: raise RuntimeError('NONDETERMINISTIC_REPLAY')
        paths[p]=a
        if p==PATHS[1]: stack_signals=s
    prior=pd.read_csv(HERE.parent/'stage6_lock1_after_2r/full_canonical_trades.csv'); core=base.EVENT_COLUMNS
    full_match=frame_sha(paths[PATHS[0]][core])==frame_sha(prior[core])
    if not full_match: raise RuntimeError('FULL_CORE_MISMATCH')
    mon=base.monthly(paths); year=base.yearly(paths,mon); inst=base.instrument_yearly(paths); roll=base.rolling(mon); conc=base.concentration(mon)
    life=pd.DataFrame([{'path':p,'lifecycle':l,**base.metrics(g)} for p,x in paths.items() for l,g in x.groupby('lifecycle')]); direction=pd.DataFrame([{'path':p,'lifecycle':l,'direction':d,**base.metrics(g)} for p,x in paths.items() for (l,d),g in x.groupby(['lifecycle','direction'])]); comp,decision=comparison(year,life,roll,mon,conc)
    rec=reconcile(paths); sf=session_funnel(stack_signals,paths[PATHS[1]],rec); lf=lock_funnel(paths[PATHS[1]]); attr=attribution(paths)
    interaction=sf.merge(lf.groupby(['instrument','lifecycle']).agg({'reaching_2R':'sum','lock_binding':'sum','LOCK1_STOP':'sum'}).reset_index(),on=['instrument','lifecycle']).rename(columns={'canonical_entry_signals':'canonical_signals','out_of_session_rejected_signals':'session_rejected_entries','in_session_entries':'session_allowed_entries'}); interaction['later_STACK_only_after_session_rejection']=interaction['STACK_only_entries']; interaction['later_STACK_only_after_early_LOCK1_exit_identifiable']=0
    registry=pd.DataFrame([{'path':p,'rule':'FULL_CANONICAL' if p==PATHS[0] else 'SESSION_10_21 + LOCK1_AFTER_2R','session_timezone':'Europe/Moscow','start_inclusive':'10:00','end_exclusive':'21:00','entry_only':True,'trigger_R':2,'lock_R':1,'next_event_activation':True,'C1_tick':TICK} for p in PATHS])
    artifacts={'structural_stack_registry.csv':registry,'full_canonical_trades.csv':paths[PATHS[0]],'structural_stack_v1_trades.csv':paths[PATHS[1]],'full_vs_structural_stack_trade_path_reconciliation.csv':rec,'structural_stack_interaction.csv':interaction,'stack_vs_components.csv':component_table(comp),'stack_interaction_attribution.csv':attr,'stack_session_funnel.csv':sf,'stack_lock1_funnel.csv':lf,'exit_reason_comparison.csv':base.exit_reasons(paths),'holding_bucket_comparison.csv':base.holding_buckets(paths),'yearly_metrics.csv':year,'monthly_metrics.csv':mon.drop(columns=[f'{s}_net_R' for s in SYMBOLS]),'instrument_yearly_metrics.csv':inst,'instrument_monthly_metrics.csv':mon[['path','lifecycle','year','month',*[f'{s}_net_R' for s in SYMBOLS],'net_R']].rename(columns={'net_R':'Total'}),'direction_metrics.csv':direction,'rolling_stability.csv':roll,'lifecycle_metrics.csv':life,'monthly_concentration.csv':conc,'structural_stack_decision_comparison.csv':comp}
    out.mkdir(parents=True,exist_ok=True)
    for n,f in artifacts.items(): f.to_csv(out/n,index=False,lineterminator='\n',float_format='%.12g')
    manifest={'starting_main_sha':STARTING_MAIN_SHA,'strategy_sha':base.T3_SHA,'parameter_sha':base.PARAM_SHA,'source_hashes':auth['source_hashes'],'old_stage6_sha':base.OLD_STAGE6_SHA,'benchmark_hashes':auth['benchmark_hashes'],'prior_stage_hashes':auth['prior_stage_hashes'],'deterministic_replay_hashes':hashes,'full_core_match':full_match,'decision':decision,'stage7_executed':False}
    (out/'FINAL_STRUCTURAL_STACK_REPORT.md').write_text(report(artifacts,manifest)); manifest['artifact_hashes']={n:sha(out/n) for n in [*artifacts,'FINAL_STRUCTURAL_STACK_REPORT.md']}; (out/'audit_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n'); return artifacts,manifest

if __name__=='__main__':
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.run_stage5_trail1 import resolve_data_root
    root,_=resolve_data_root(); _,m=execute(root,os.environ.get('STAGE6_STACK_OUTPUT_DIR',HERE)); print(json.dumps({'decision':m['decision'],'hashes':m['deterministic_replay_hashes']},sort_keys=True))
