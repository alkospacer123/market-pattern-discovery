import numpy as np,pandas as pd
from market_pattern_discovery.discovery.execution_contract import *
def test_contract_inventory_and_readiness():
 c=load_execution_contract();assert [len(c['feature_inventory'][x]) for x in ('M1','M5')]==[241,220];assert remaining_execution_degrees(c)==[]
def test_ids_pairs_subgroups():
 assert hypothesis_id('univariate',1)=='HYP-U-000000001'; assert enumerate_pairs(['b','a','c'],2)==[('b','a'),('b','c')]; assert len(subgroup_rules([('a',[0,1]),('b',[0]),('c',[1])],3))==3
def test_quantile_train_only_and_categories():
 tr=pd.Series(range(100));va=pd.Series([10000]);_,s,c=fit_train_apply_validate(tr,va);assert s.iloc[0]=='GE_P90' and max(c)<100;assert canonical_categories([2,1,np.nan])==[1,2,'MISSING']
def test_effect_bh_direction_replication():
 e=primary_effect([4,5],[1,2,3]);assert e['primary_effect_signed']>0 and e['primary_effect_absolute']==abs(e['primary_effect_signed']);assert np.allclose(benjamini_hochberg([.01,.04]),[.02,.04]);assert same_direction_summary(1,[1,-1,0,np.nan])['same_direction_fold_count']==1;assert classify_replication(2,1,.02,12,True)=='strong_replication'
def test_validator():
 from market_pattern_discovery.validation.phase5a2 import validate
 assert validate()['remaining_execution_degrees_of_freedom']==[]
