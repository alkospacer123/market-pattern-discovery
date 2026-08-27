"""Signed, target-independent Discovery Execution Contract v1.0."""
from __future__ import annotations
import hashlib,json,itertools
from pathlib import Path
from typing import Any,Iterable
import numpy as np
import pandas as pd
from .protocol import quantile_states,apply_cutpoints,continuous_effect,binary_effect,benjamini_hochberg
ROOT=Path(__file__).resolve().parents[3]; PATH=ROOT/'config/discovery_execution_v1.json'
def canonical_bytes(v:Any)->bytes:return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def execution_signature(v:dict)->str:return hashlib.sha256(canonical_bytes({k:x for k,x in v.items() if k!='signature_sha256'})).hexdigest()
def load_execution_contract(path:Path=PATH)->dict:
 v=json.loads(path.read_text());
 if execution_signature(v)!=v.get('signature_sha256'):raise ValueError('Discovery Execution signature drift')
 for key,sig in v['upstream_signatures'].items():
  fn={'feature_set':'feature_set_v1.json','behavior_target_set':'behavior_target_set_v1.json','target_definitions':'target_definitions_v1.json','discovery_protocol':'discovery_protocol_v1.json','discovery_target_mapping':'discovery_target_mapping_v1.json'}.get(key)
  if fn and json.load(open(ROOT/'config'/fn))['signature_sha256']!=sig:raise ValueError(f'{key} signature drift')
 return v
def feature_inventory(tf:str)->list[dict]:return load_execution_contract()['feature_inventory'][tf]
def canonical_categories(values:Iterable)->list:
 vals=[x for x in values if not pd.isna(x)]; return sorted(set(vals),key=lambda x:canonical_bytes(x))+(['MISSING'] if any(pd.isna(x) for x in values) else [])
def states_for(entry:dict,categories:Iterable=())->list:
 t=entry['representation']; order=load_execution_contract()['state_order'][t]
 if isinstance(order,list):return order
 return canonical_categories(categories)
def hypothesis_id(method:str,ordinal:int)->str:
 if ordinal<1:raise ValueError('ordinal starts at one')
 letter={"univariate":"U","interaction":"I","subgroup":"S"}[method]; return f"HYP-{letter}-{ordinal:09d}"
def effect_id(method:str,ordinal:int)->str:return hypothesis_id(method,ordinal).replace('HYP','EFF',1)
def enumerate_pairs(features:list[str],cap:int=500)->list[tuple[str,str]]:
 return list(itertools.islice(((features[i],features[j]) for i in range(len(features)) for j in range(i+1,len(features))),cap))
def interaction_states(a:Iterable,b:Iterable):return list(itertools.product(a,b))
def subgroup_rules(features:list[tuple[str,list]],cap:int=100000):
 out=[]
 for depth in (2,3):
  for combo in itertools.combinations(features,depth):
   for states in itertools.product(*(x[1] for x in combo)):
    out.append(tuple((combo[i][0],states[i]) for i in range(depth)))
    if len(out)>=cap:return out
 return out
def univariate_count(inventory:list[dict],state_counts:dict[str,int],target_units:int)->int:return sum(state_counts[x['feature']] for x in inventory)*target_units
def interaction_state_count(pairs, state_counts,target_units):return sum(state_counts[a]*state_counts[b] for a,b in pairs)*target_units
def fit_full_discovery(values:pd.Series):return quantile_states(values)
def fit_train_apply_validate(train:pd.Series,validate:pd.Series):
 train_state,cuts=quantile_states(train);return train_state,apply_cutpoints(validate,cuts),cuts
def primary_effect(candidate,baseline,kind='continuous'):
 d=continuous_effect(candidate,baseline) if kind=='continuous' else binary_effect(candidate,baseline); signed=d['median_difference' if kind=='continuous' else 'probability_difference'];return {'primary_effect_signed':signed,'primary_effect_absolute':abs(signed),**d}
def null_p_value(frame:pd.DataFrame,mask:pd.Series,target:str,kind='continuous',replications=1000,seed=20260401):
 """Permute complete outcome-day blocks against fixed membership blocks."""
 days=list(pd.unique(frame.moscow_trading_date)); groups={d:frame.loc[frame.moscow_trading_date.eq(d),target].to_numpy() for d in days}; observed=primary_effect(frame.loc[mask,target],frame[target],kind)['primary_effect_signed']; rng=np.random.default_rng(seed); null=[]
 for _ in range(replications):
  perm=rng.permutation(days); mapped={d:groups[p] for d,p in zip(days,perm)}; y=np.concatenate([mapped[d] for d in days]); m=np.concatenate([mask.loc[frame.moscow_trading_date.eq(d)].to_numpy()[:len(mapped[d])] for d in days]); n=min(len(y),len(m)); null.append(primary_effect(y[:n][m[:n]],y[:n],kind)['primary_effect_signed'])
 return (1+sum(abs(x)>=abs(observed) for x in null))/(replications+1)
def same_direction_summary(full_effect:float,folds:list[float])->dict:
 valid=np.array([x for x in folds if np.isfinite(x)]); same=int(sum((np.sign(valid)==np.sign(full_effect))&(valid!=0)&(full_effect!=0)));return {'valid_fold_count':len(valid),'same_direction_fold_count':same,'median_fold_effect':float(np.median(valid)) if len(valid) else np.nan,'worst_signed_fold_effect':float(np.min(valid*np.sign(full_effect))) if len(valid) else np.nan,'fold_effect_dispersion':float(np.std(valid,ddof=1)) if len(valid)>1 else np.nan}
def classify_replication(source,effect,coverage,days,uncertainty_finite,transferable=True,tested=True):
 if not transferable:return 'not_applicable'
 if not tested or not np.isfinite(effect):return 'not_tested'
 if np.sign(effect)!=np.sign(source) or effect==0:return 'failed_replication'
 if coverage>=.01 and days>=10 and uncertainty_finite and abs(effect)>=.5*abs(source):return 'strong_replication'
 return 'directionally_consistent' if coverage>=.01 and days>=10 else 'failed_replication'
def checkpoint_id(experiment_id,batch_id,first,last):return hashlib.sha256(canonical_bytes([experiment_id,batch_id,first,last])).hexdigest()[:24]
def remaining_execution_degrees(contract:dict)->list[str]:
 checks={
  'data_scope':contract.get('baseline','').endswith('DISCOVERY interval'),
  'feature_universe':set(contract.get('feature_inventory',{}))=={'M1','M5'},
  'feature_type':all(x.get('representation') in contract.get('representation_types',[]) for v in contract.get('feature_inventory',{}).values() for x in v),
  'feature_state':set(contract.get('state_order',{}))=={'continuous_quantile','binary','categorical','integer_categorical'},
  'state_fitting':'walk_forward' in contract.get('quantile_fitting',{}), 'state_ordering':bool(contract.get('state_order')),
  'target_mapping':'discovery_target_mapping' in contract.get('upstream_signatures',{}), 'target_contrasts':bool(contract.get('fdr_family')),
  'valid_domain':'target-valid' in contract.get('baseline',''), 'baseline':bool(contract.get('baseline')),
  'hypothesis_enumeration':bool(contract.get('orders')), 'hypothesis_ids':set(contract.get('ids',{}))=={'univariate','interaction','subgroup','effect'},
  'pair_enumeration':contract.get('interaction_pair_cap')==500, 'interaction_states':'interaction' in contract.get('orders',{}),
  'subgroup_enumeration':'subgroup' in contract.get('orders',{}), 'subgroup_cap':isinstance(contract.get('subgroup_rule_cap'),int),
  'effect_metrics':bool(contract.get('ranking')), 'uncertainty':contract.get('bootstrap',{}).get('replications')==1000,
  'null_inference':bool(contract.get('null',{}).get('method')), 'p_value':'B + 1' in contract.get('null',{}).get('p_value',''),
  'fdr':len(contract.get('fdr_family',[]))==5, 'walk_forward':contract.get('walk_forward')==['WF-01','WF-02','WF-03','WF-04'],
  'eligibility':len(contract.get('eligibility',{}))==6, 'screening':contract.get('eligibility',{}).get('promotion_minimum_coverage')==.01,
  'screening_statuses':'promoted' in contract.get('statuses',[]), 'candidate_creation':'research.registry.create_candidate' in contract.get('candidate_path',''),
  'candidate_lifecycle':contract.get('candidate_path','').endswith('discovered -> screened'), 'candidate_ids':'candidate' in contract.get('candidate_path',''),
  'replication':bool(contract.get('replication')), 'replication_classes':len(contract.get('replication',{}).get('classes',[]))==5,
  'ranking':len(contract.get('ranking',[]))==8, 'shortlist':contract.get('shortlist',{}).get('total_cap')==50,
  'experiment_preregistration':len(contract.get('experiment_methods',[]))==3, 'experiment_finalization':len(contract.get('final_statuses',[]))==3,
  'batching':bool(contract.get('batch_keys')), 'checkpoint_resume':contract.get('checkpoint_root')=='results/',
  'artifact_schemas':len(contract.get('artifact_schemas',[]))==8, 'completeness_reconciliation':len(contract.get('completeness_checks',[]))==38,
 }
 required=set(contract.get('completeness_checks',[])); return sorted(name for name in required if not checks.get(name,False))
