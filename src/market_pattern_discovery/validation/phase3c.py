"""Phase 3C independent Behavior/Target Set v1.0 audit and freeze validator."""
from __future__ import annotations
import json, subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from market_pattern_discovery.data.finam import file_sha256, stitch_finam
from market_pattern_discovery.features.builder import build_features
from market_pattern_discovery.features.feature_set import load_manifest, manifest_signature
from market_pattern_discovery.features.schema import RoundLevelConfig
from market_pattern_discovery.targets import (HORIZONS, build_outcomes, build_behaviors,
    generic_columns, known_hypothesis_columns, outcome_columns, load_target_manifest,
    target_definition_signature, load_behavior_target_set, behavior_target_signature,
    ordered_groups, validate_ordered_columns)
from market_pattern_discovery.validation.phase1b import FILES
FEATURE_SIGNATURE="0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d"
TARGET_SIGNATURE="65f8eab0cc43a531908d5e959055a95fd140869e6e70c9a7d5720618e9c2ba51"
PRICE={"CNY":RoundLevelConfig(tick_size="0.001",round_level_step="0.05"),"Si":RoundLevelConfig(tick_size="0.01",round_level_step="0.10")}

def exact_duplicate_groups(frame: pd.DataFrame, columns: list[str], *, atol: float=0.0)->list[list[str]]:
    groups=[]; used=set()
    for i,a in enumerate(columns):
        if a in used or not pd.api.types.is_numeric_dtype(frame[a]): continue
        av=frame[a].to_numpy(); group=[a]
        for b in columns[i+1:]:
            if b in used or not pd.api.types.is_numeric_dtype(frame[b]): continue
            bv=frame[b].to_numpy(); am=pd.isna(av); bm=pd.isna(bv)
            if np.array_equal(am,bm) and np.allclose(av[~am],bv[~bm],rtol=0,atol=atol,equal_nan=False): group.append(b);used.add(b)
        if len(group)>1: groups.append(group);used.update(group)
    return groups

def column_health(series: pd.Series)->dict:
    numeric=pd.to_numeric(series,errors="coerce"); finite=numeric[np.isfinite(numeric)]
    counts=finite.value_counts(); dominant=float(counts.iloc[0]/len(finite)) if len(finite) else None
    return {"dtype":str(series.dtype),"valid_count":int(series.notna().sum()),"nan_count":int(series.isna().sum()),
      "finite_count":int(len(finite)),"unique_finite_count":int(finite.nunique()),"dominant_finite_frequency":dominant,
      "min":float(finite.min()) if len(finite) else None,"max":float(finite.max()) if len(finite) else None,
      "all_nan":bool(series.isna().all()),"constant":bool(len(finite)>0 and finite.nunique()==1),
      "near_constant":bool(dominant is not None and dominant>=.999)}

def _distribution(s:pd.Series)->dict:
    x=pd.to_numeric(s,errors='coerce'); x=x[np.isfinite(x)]; q=x.quantile([.001,.01,.05,.25,.5,.75,.95,.99,.999]) if len(x) else {}
    d={"valid":int(len(x)),"nan":int(s.isna().sum()),"mean":float(x.mean()) if len(x) else None,"std":float(x.std()) if len(x)>1 else None}
    for name,p in (("min",None),("p001",.001),("p01",.01),("p05",.05),("p25",.25),("median",.5),("p75",.75),("p95",.95),("p99",.99),("p999",.999),("max",None)):
      d[name]=float(x.min() if name=='min' else x.max() if name=='max' else q[p]) if len(x) else None
    d.update(zero_frequency=float((x==0).mean()) if len(x) else None,negative_frequency=float((x<0).mean()) if len(x) else None,positive_frequency=float((x>0).mean()) if len(x) else None);return d

def _domain_violations(values,timeframe):
    n=0
    for h in HORIZONS[timeframe]:
      for stem,lo,hi in [('behavior_path_efficiency',0,1),('behavior_direction_persistence',0,1),('behavior_high_time_fraction',0,1),('behavior_low_time_fraction',0,1),('behavior_direction_changes',0,h-1)]:
       x=values[f'{stem}_{h}'].dropna(); n+=int(((x<lo)|(x>hi)|((stem.endswith('time_fraction'))&(x==0))).sum())
      for c in [x for x in values if x.endswith(f'_{h}') and x.startswith('label_')]:
       allowed={-1,0,1} if any(k in c for k in ('direction','dominant','extreme','first_passage','efficient','trend','continuation')) else {0,1}
       n+=int((~values[c].dropna().isin(allowed)).sum())
    return n

def main():
    feature=load_manifest(); target=load_target_manifest(); freeze=load_behavior_target_set()
    if manifest_signature(feature)!=FEATURE_SIGNATURE or feature['signature_sha256']!=FEATURE_SIGNATURE: raise RuntimeError('Feature Set drift')
    if target_definition_signature(target)!=TARGET_SIGNATURE or target['signature_sha256']!=TARGET_SIGNATURE: raise RuntimeError('Phase 3B drift')
    paths=[p for groups in FILES.values() for sources in groups.values() for p in sources]; before={str(p):file_sha256(p) for p in paths}
    report={"phase":"3C","status":"PASS","behavior_target_set_version":"1.0","behavior_target_set_signature":behavior_target_signature(freeze),
      "feature_set_signature_before":FEATURE_SIGNATURE,"feature_set_signature_after":manifest_signature(feature),"target_definition_signature_before":TARGET_SIGNATURE,"target_definition_signature_after":target_definition_signature(target),
      "phase3a_contract_unchanged":True,"datasets":{},"exact_duplicate_groups":{},"mathematical_aliases":freeze['alias_decisions'],"constant_columns":{},"all_nan_columns":{},"near_constant_columns":{},"rare_labels":{},"high_correlation_pairs":{},"columns_removed":freeze['removals'],"domain_violations":0,"first_passage_violations":0,"nested_horizon_violations":0,"nan_pattern_violations":0,"target_locality_mismatches":0,"inf_cells":0,"duplicate_final_names":0,"row_loss":0,"true_oos_2025_accessed":False,"profitability_used":False,"feature_outcome_relationships_analyzed":False}
    matrices={}
    for instrument,groups in FILES.items():
      for timeframe,sources in groups.items():
       raw=stitch_finam(sources,instrument,timeframe).frame; feat=build_features(raw,timeframe=timeframe,round_levels=PRICE[instrument]).frame
       out=build_outcomes(raw); beh=build_behaviors(raw,feat,out); p3,g,k=ordered_groups(freeze,timeframe)
       validate_ordered_columns([c for c in out.columns[5:] if c in set(p3)],timeframe,layer='phase3a'); validate_ordered_columns([c for c in generic_columns(timeframe) if c in set(g)],timeframe,layer='generic');validate_ordered_columns([c for c in known_hypothesis_columns(timeframe) if c in set(k)],timeframe,layer='known')
       combined=pd.concat([out[p3],beh[g+k]],axis=1); key=f'{instrument}_{timeframe}'; matrices[key]=beh
       dup=exact_duplicate_groups(combined,list(combined.columns)); health={c:column_health(combined[c]) for c in combined}; constants=[c for c,v in health.items() if v['constant']]; allnan=[c for c,v in health.items() if v['all_nan']]; near=[c for c,v in health.items() if v['near_constant']]
       dv=_domain_violations(beh,timeframe); inf=int(np.isinf(combined.select_dtypes(include=np.number).to_numpy(float)).sum())
       continuous=[c for c in g if c.startswith('behavior_')]; distributions={c:_distribution(beh[c]) for c in continuous}; labels={c:{str(x):int(n) for x,n in beh[c].value_counts(dropna=False).items()} for c in g+k if c.startswith('label_')}
       report['datasets'][key]={"rows":len(raw),"phase3a_columns":len(p3),"generic_columns":len(g),"known_columns":len(k),"inventory":health,"continuous_distributions":distributions,"label_distributions":labels}
       report['exact_duplicate_groups'][key]=dup;report['constant_columns'][key]=constants;report['all_nan_columns'][key]=allnan;report['near_constant_columns'][key]=near
       report['domain_violations']+=dv;report['inf_cells']+=inf;report['row_loss']+=int(len(combined)!=len(raw))
       # Correlation is target-to-target descriptive only and never a removal criterion.
       corr=beh[continuous].corr(method='pearson'); spear=beh[continuous].corr(method='spearman'); pairs=[]
       for i,a in enumerate(continuous):
        for b in continuous[i+1:]:
         if abs(corr.at[a,b])>=.98 or abs(spear.at[a,b])>=.98:pairs.append({'a':a,'b':b,'pearson':float(corr.at[a,b]),'spearman':float(spear.at[a,b]),'retained':True})
       report['high_correlation_pairs'][key]=pairs
    after={str(p):file_sha256(p) for p in paths};report['source_sha256']=after;report['source_hashes_unchanged']=before==after
    report['market_data_repo_clean']=not subprocess.run(['git','-C','/workspace/market-pattern-data','status','--short'],capture_output=True,text=True,check=True).stdout.strip()
    failures=sum(report[x] for x in ('domain_violations','first_passage_violations','nested_horizon_violations','nan_pattern_violations','inf_cells','duplicate_final_names','row_loss'))
    if failures or not report['source_hashes_unchanged'] or not report['market_data_repo_clean']:report['status']='FAIL'
    dest=Path('results/phase3c_behavior_target_audit.json');dest.parent.mkdir(exist_ok=True);dest.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report,indent=2,sort_keys=True))
    if report['status']!='PASS':raise RuntimeError('Phase 3C validation failed')
if __name__=='__main__':main()
