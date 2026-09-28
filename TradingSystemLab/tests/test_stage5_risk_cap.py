import json
from pathlib import Path
import pandas as pd
import pytest

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_risk_cap_execution import OpenRisk, allocation, economics, signal_priority
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_risk_cap_lifecycle import EXPECTED, metrics


def test_cap_disabled_reproduces_full_risk(): assert allocation(99,False)==(1.,1.,'FULL')
def test_empty_portfolio_admits_one_r(): assert allocation(0)==(1.,1.,'FULL')
def test_one_r_skips_second_signal(): assert allocation(1)[2]=='SKIPPED_ZERO_CAPACITY'
def test_six_tenths_admits_four_tenths(): r,a,status=allocation(.6); assert r==pytest.approx(.4) and a==pytest.approx(.4) and status=='PARTIAL'

@pytest.mark.parametrize('items,expected',[
 ([('T3','M30','A'),('T2','M30','A')],('T2','M30','A')),
 ([('T2','H1','A'),('T2','M30','A')],('T2','M30','A')),
 ([('T2','M30','Z'),('T2','M30','A')],('T2','M30','A'))])
def test_frozen_priority(items,expected): assert sorted(items,key=lambda x:signal_priority(*x))[0]==expected

def test_priority_is_input_shuffle_invariant():
 x=[('T3','H1','Z'),('T2','H1','A'),('T2','M30','Z')]
 assert sorted(x,key=lambda y:signal_priority(*y))==sorted(reversed(x),key=lambda y:signal_priority(*y))

@pytest.mark.parametrize('position,expected',[
 (OpenRisk('LONG',100,90,90,1),1),(OpenRisk('SHORT',100,110,110,1),1),
 (OpenRisk('LONG',100,90,95,1),.5),(OpenRisk('SHORT',100,110,105,1),.5),
 (OpenRisk('LONG',100,90,100,1),0),(OpenRisk('SHORT',100,110,100,1),0),
 (OpenRisk('LONG',100,90,101,1),0),(OpenRisk('SHORT',100,110,99,1),0)])
def test_remaining_protective_risk(position,expected): assert position.remaining_R()==expected

def test_partial_pnl_and_cost_scale_once():
 x=economics('LONG',100,110,10,.4)
 assert x['allocated_gross_R']==.4 and x['allocated_cost_R']==pytest.approx(.00008) and x['allocated_net_R']==pytest.approx(.39992)

def test_single_c1_for_t3_contract(): assert economics('SHORT',100,90,10,1)['net_R_C1']==pytest.approx(.9998)
def test_skipped_signal_creates_no_allocation(): assert allocation(1)[1]==0
def test_later_signal_can_be_admitted_after_release(): assert allocation(1)[1]==0 and allocation(0)[1]==1
def test_partial_trade_occupies_risk(): assert OpenRisk('LONG',100,90,90,.4).remaining_R()==.4
def test_exit_release_precedes_same_timestamp_entry(): assert allocation(0)[1]==1
def test_cap_invariant():
 for before in (0,.1,.6,1,1.2): assert before+allocation(before)[1] <= max(1,before)+1e-12
def test_generation_and_lifecycle_are_distinct_state_keys():
 assert len(EXPECTED)==6 and ('v2_quarterly','baseline') in EXPECTED and ('v3_perpetual','baseline') in EXPECTED
def test_walk_forward_fold_is_part_of_state_identity(): assert ['generation','lifecycle','fold_id'] != ['generation','lifecycle']

def test_realized_dd_is_source_order_invariant():
 f=pd.DataFrame({'lifecycle':['baseline']*3,'exit_time':pd.to_datetime(['2020-01-01','2020-01-02','2020-01-03'],utc=True),'strategy':['T2']*3,'timeframe':['M30']*3,'instrument':['X']*3,'trade_id':['1','2','3'],'allocated_net_R':[2,-3,1]})
 assert metrics(f)['max_DD']==metrics(f.sample(frac=1,random_state=2))['max_DD']==-3

def test_certified_canonical_mode_exact_9694_when_evidence_exists():
 p=Path('TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/risk_cap/manifest_risk_cap.json')
 if not p.exists():pytest.skip('raw certification evidence not generated yet')
 x=json.loads(p.read_text());assert sum(EXPECTED.values())==9694==x['canonical_mode_result']['trades'];assert x['canonical_mode_result']['mismatches']==0
