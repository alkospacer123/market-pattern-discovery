"""Phase 5A.2 contract-only validator; never opens market data."""
import json,subprocess
from market_pattern_discovery.discovery.execution_contract import load_execution_contract,execution_signature,remaining_execution_degrees

def validate():
 c=load_execution_contract(); counts={k:len(v) for k,v in c['feature_inventory'].items()}; unknown=[x for v in c['feature_inventory'].values() for x in v if x['representation'] not in c['representation_types']]
 remaining=remaining_execution_degrees(c)
 if counts!={'M1':241,'M5':220} or unknown or remaining:raise AssertionError('execution contract incomplete')
 if subprocess.run(['git','-C','/workspace/market-pattern-data','status','--short'],capture_output=True,text=True,check=True).stdout:raise AssertionError('market data dirty')
 return {'phase':'5A.2','status':'PASS','discovery_execution_version':c['discovery_execution_version'],'discovery_execution_signature':execution_signature(c),'upstream_signatures':c['upstream_signatures'],'feature_typing':counts,'unclassified':len(unknown),'remaining_execution_degrees_of_freedom':remaining,**c['safety'],'market_data_repo_clean':True}
def main():print(json.dumps(validate(),indent=2,sort_keys=True))
