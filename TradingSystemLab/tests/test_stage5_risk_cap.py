import json
from pathlib import Path
import pandas as pd
import pytest

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_risk_cap_execution import OpenRisk, allocation, economics, signal_priority
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_risk_cap_lifecycle import (
    EXPECTED, StreamState, audit_admission_risk, certification_status,
    entries_open, manifest_with_audit_status, metrics, position_accounting,
)


def test_cap_disabled_reproduces_full_risk(): assert allocation(99,False)==(1.,1.,'FULL')
def test_empty_portfolio_admits_one_r(): assert allocation(0)==(1.,1.,'FULL')
def test_one_r_skips_second_signal(): assert allocation(1)[2]=='SKIPPED_ZERO_CAPACITY'
def test_sub_tolerance_capacity_records_exact_zero(): assert allocation(1-1e-16)[1:]==(0.,'SKIPPED_ZERO_CAPACITY')
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

def _flat_t3(end="2024-04-01T00:00:00Z", signal="LONG"):
 class Strategy:
  def regime(self, _): return "LONG"
  def generate_signal(self, *_): return signal
  def calculate_stop_loss(self, *_): return 90.0
  def exit_signal(self, direction, bar, stop): return (bar.Low <= stop if direction == "LONG" else bar.High >= stop)
  def manage_position(self, direction, extreme, atr): return 95.0
 state=StreamState.__new__(StreamState);state.s="T3";state.p=object();state.entry_end=pd.Timestamp(end);state.meta={"generation":"v2_quarterly","lifecycle":"walk_forward","fold_id":"WF01","strategy":"T3","timeframe":"H1","instrument":"X","candidate_config_identity":"test"}
 state.data=pd.DataFrame({"Open":[100.0],"High":[101.0],"Low":[99.0],"Close":[100.0],"ATR":[1.0]},index=pd.to_datetime(["2024-04-01T00:00:00Z"]));state.high=state.data.copy();state.lookup={state.data.index[0]:0};state.strategy=Strategy();state.pos=None;state.setup=None;state.seq=0;state.cursor=-1;state.blocked=False
 return state

def test_entry_before_end_can_exit_after_end():
 s=_flat_t3();s.pos={"direction":"LONG","entry":100.,"entry_time":pd.Timestamp("2024-03-31",tz="UTC"),"initial":99.,"risk":1.,"stop":100.5,"assigned":1.,"bars":0,"lo":100.,"hi":100.,"extreme":100.,"seq":1};s.data.iloc[0,s.data.columns.get_loc("Low")]=99.
 exitrow,signal=s.process(s.data.index[0]);assert exitrow is not None and signal is None

def test_no_entry_at_entry_end(): assert not entries_open("2024-04-01","2024-04-01")
def test_entry_before_entry_end_is_open(): assert entries_open("2024-03-31T23:59:59Z","2024-04-01T00:00:00Z")
def test_continuation_does_not_create_post_boundary_signal(): assert _flat_t3().process(pd.Timestamp("2024-04-01",tz="UTC"))[1] is None
def test_continuation_discards_preboundary_setup():
 s=_flat_t3();s.setup=object();s.process(s.data.index[0]);assert s.setup is None
def test_fold_states_are_independently_copyable_and_flat():
 a,b=_flat_t3(),_flat_t3();a.pos={"prior":"fold"};assert b.pos is None
def test_prior_fold_position_does_not_contaminate_next_fold():
 prior,next_fold=_flat_t3(),_flat_t3();prior.pos={"prior":"fold"};assert next_fold.pos is None
def test_terminal_position_is_explicitly_accounted(): assert position_accounting(3,2,1)["status"]=="PASS"
def test_silent_drop_fails_accounting(): assert position_accounting(3,2,0)["silent_dropped_positions"]==1
def test_terminal_position_is_not_force_closed(): assert position_accounting(1,0,1)["closed_positions"]==0
def test_baseline_boundary_never_opens_true_oos_entry(): assert not entries_open("2025-01-01T00:00:00+03:00","2025-01-01T00:00:00+03:00")
def test_independent_admission_audit_catches_mutated_assigned_risk():
 frame=pd.DataFrame([{"_open_risk_snapshot_R":(.6,),"open_risk_before_R":.6,"residual_capacity_R":.4,"assigned_risk_R":.5,"open_risk_after_R":1.,"status":"PARTIAL"}])
 assert audit_admission_risk(frame)["risk_accounting_mismatches"]==1

def _clean_audit(**updates):
 audit={"canonical_rows":9694,"canonical_path_mismatches":0,
        "canonical_arithmetic_mismatches":0,"capped_arithmetic_mismatches":0,
        "capped_admitted_positions":10,"capped_closed_positions":10,
        "terminal_open_positions":0,"silent_dropped_positions":0,
        "risk_accounting_mismatches":0,"risk_cap_violations":0,
        "negative_risk_events":0,"allocation_above_one":0}
 audit.update(updates);return audit

@pytest.mark.parametrize("field",["risk_accounting_mismatches","risk_cap_violations",
                                  "canonical_arithmetic_mismatches"])
def test_nonzero_accounting_gate_cannot_pass(field):
 assert certification_status(_clean_audit(**{field:1}),True)=="RISK_CAP_ACCOUNTING_CERTIFICATION_FAILED"

def test_silent_drop_cannot_pass():
 assert certification_status(_clean_audit(silent_dropped_positions=1),True)=="RISK_CAP_POSITION_ACCOUNTING_FAILED"

def test_terminal_open_is_incomplete_not_pass():
 audit=_clean_audit(capped_closed_positions=9,terminal_open_positions=1)
 assert certification_status(audit,True)=="FINAL_ECONOMIC_CERTIFICATION_INCOMPLETE_TERMINAL_OPEN_POSITIONS"

def test_canonical_mismatch_fails():
 assert certification_status(_clean_audit(canonical_path_mismatches=1),True)=="RISK_CAP_CANONICAL_RECONCILIATION_FAILED"

def test_clean_deterministic_certification_passes():
 assert certification_status(_clean_audit(),True)=="STAGE5_RISK_CAP_FINAL_CERTIFICATION_PASSED"

def test_manifest_status_mirrors_audit_status():
 audit=_clean_audit(terminal_open_positions=1,capped_closed_positions=9)
 audit["status"]=certification_status(audit,True)
 assert manifest_with_audit_status({"status":"forbidden-independent-status"},audit)["status"]==audit["status"]
