import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from market_pattern_discovery.targets import (load_behavior_target_set,behavior_target_signature,ordered_groups,validate_ordered_columns,outcome_columns,generic_columns,known_hypothesis_columns)
from market_pattern_discovery.validation.phase3c import exact_duplicate_groups,column_health,_domain_violations

def test_manifest_serialization_signature_and_compatibility():
 m=load_behavior_target_set(); assert behavior_target_signature(m)==m['signature_sha256']; assert json.dumps(m,sort_keys=True,separators=(',',':'))==json.dumps(json.loads(json.dumps(m)),sort_keys=True,separators=(',',':'))
 assert m['feature_set_signature']=='0b5ffb328d217e5e8d575ff0b84be794647bc0850e548b354d737ce91342024d'; assert m['phase3b_target_definition_signature']=='65f8eab0cc43a531908d5e959055a95fd140869e6e70c9a7d5720618e9c2ba51';assert m['phase3a_version']=='1.0'

def test_exact_order_classification_and_removals():
 m=load_behavior_target_set()
 for t in ('M1','M5'):
  a,g,k=ordered_groups(m,t);assert a==[c for c in outcome_columns(t) if c in set(a)];assert g==[c for c in generic_columns(t) if c in set(g)];assert k==[c for c in known_hypothesis_columns(t) if c in set(k)];assert not set(g)&set(k)
 assert len(m['removals'])==14

def test_order_duplicate_missing_and_extra_policy():
 m=load_behavior_target_set(); expected=ordered_groups(m,'M5')[1]
 validate_ordered_columns(expected,'M5',layer='generic')
 with pytest.raises(ValueError,match='duplicate'):validate_ordered_columns(expected+[expected[0]],'M5',layer='generic')
 with pytest.raises(ValueError,match='missing'):validate_ordered_columns(expected[:-1],'M5',layer='generic')
 with pytest.raises(ValueError,match='extra'):validate_ordered_columns(expected+['x'],'M5',layer='generic')
 validate_ordered_columns(['x']+expected+['y'],'M5',layer='generic',allow_extra=True)
 with pytest.raises(ValueError,match='order'):validate_ordered_columns(list(reversed(expected)),'M5',layer='generic')

def test_duplicate_nan_mask_constant_all_nan_near_constant():
 f=pd.DataFrame({'a':[1.,np.nan,2.],'b':[1.,np.nan,2.],'c':[1.,2.,np.nan]});assert exact_duplicate_groups(f,list(f))==[['a','b']]
 assert column_health(pd.Series([3.,3.]))['constant'];assert column_health(pd.Series([np.nan,np.nan]))['all_nan'];assert column_health(pd.Series([0.]*1000+[1.]))['near_constant']

def test_domain_validator_accepts_documented_fixture():
 cols={}
 from market_pattern_discovery.targets import HORIZONS
 for h in HORIZONS['M5']:
  cols.update({f'behavior_path_efficiency_{h}':[0.,1.],f'behavior_direction_persistence_{h}':[.5,1.],f'behavior_high_time_fraction_{h}':[1/h,1.],f'behavior_low_time_fraction_{h}':[1/h,1.],f'behavior_direction_changes_{h}':[0,h-1]})
 assert _domain_violations(pd.DataFrame(cols),'M5')==0

def test_feature_isolation_and_sealed_oos_contract():
 text=Path('src/market_pattern_discovery/features').read_text() if Path('src/market_pattern_discovery/features').is_file() else ''
 assert 'behavior_target_set' not in text
 assert load_behavior_target_set()['behavior_target_set_version']=='1.0'
