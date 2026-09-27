import pandas as pd
import pytest

from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State, tighten
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_lifecycle import metrics, _record, _arithmetic_audit


def test_entry_bar_cannot_trigger_and_trigger_candidate_is_deferred():
    s=Trail1State('LONG',100,90)
    assert s.triggered is False                 # entry construction observes no OHLC
    assert s.observe_completed_bar(1,111,99,95,90)
    assert s.activate_before_event(1,90)==90    # trigger bar is not executable
    assert s.activate_before_event(2,90)==95


def test_pretrigger_initial_stop_and_gap_fill():
    s=Trail1State('LONG',100,90)
    assert s.candidate_after_bar(90,99)==90
    assert s.stop_fill(88,90)==88


def test_short_never_loosens_and_frozen_r_trigger():
    s=Trail1State('SHORT',100,110)
    assert not s.observe_completed_bar(1,101,91,105,110)
    assert s.observe_completed_bar(2,100,90,94,110)
    assert s.activate_before_event(3,108)==94
    assert tighten('SHORT',94,97)==94


def test_disabled_mode_is_canonical_trail():
    s=Trail1State('LONG',100,90,enabled=False)
    assert s.candidate_after_bar(90,93)==93
    assert not s.observe_completed_bar(1,120,80,99,93)


def test_single_c1_t3_accounting():
    meta={'strategy':'T3','timeframe':'H1','instrument':'X'}
    pos={'direction':'LONG','entry':100.,'risk':10.,'entry_time':0,'seq':1,'bars':0}
    row=_record(meta,pos,Trail1State('LONG',100,90),1,110.,'TEST')
    assert row['gross_R']==1
    assert row['cost_R']==pytest.approx(.0002)
    assert row['net_R_C1']==pytest.approx(.9998)


def test_drawdown_is_invariant_to_input_order():
    f=pd.DataFrame({'lifecycle':['baseline']*3,'exit_time':pd.to_datetime(['2020-01-01','2020-01-02','2020-01-03'],utc=True),
      'instrument':['X']*3,'trade_id':['1','2','3'],'entry_time':pd.to_datetime(['2019-12-31']*3,utc=True),'net_R_C1':[2,-3,1]})
    assert metrics(f)['max_DD']==metrics(f.sample(frac=1,random_state=4))['max_DD']==-3


@pytest.mark.parametrize(('direction','stop','candidate','expected'),[
    ('LONG',95,94,95),('LONG',95,96,96),('SHORT',105,106,105),('SHORT',105,104,104)])
def test_never_loosen(direction,stop,candidate,expected):
    assert tighten(direction,stop,candidate)==expected


def test_trigger_is_inclusive_at_exactly_one_r():
    assert Trail1State('LONG',10,8).observe_completed_bar('bar',12,9,9,8)


def test_short_gap_uses_canonical_worse_open():
    s=Trail1State('SHORT',100,110);s.observe_completed_bar(1,101,90,105,110);s.activate_before_event(2,110)
    assert s.stop_fill(108,105)==108 and s.gap_through_activated_trail


def test_long_gap_uses_canonical_worse_open():
    s=Trail1State('LONG',100,90);s.observe_completed_bar(1,110,99,95,90);s.activate_before_event(2,90)
    assert s.stop_fill(93,95)==93 and s.gap_through_activated_trail


def test_candidate_updates_normally_after_activation():
    s=Trail1State('LONG',100,90);s.observe_completed_bar(1,110,99,94,90);s.activate_before_event(2,90)
    assert s.candidate_after_bar(94,97)==97


def test_candidate_looser_than_initial_is_diagnostic_only():
    s=Trail1State('LONG',100,90);s.observe_completed_bar(1,110,99,89,90)
    assert s.candidate_already_looser and s.activate_before_event(2,90)==90


def test_new_trade_has_fresh_state():
    old=Trail1State('LONG',100,90);old.observe_completed_bar(1,110,99,95,90)
    new=Trail1State('LONG',100,90)
    assert old.triggered and not new.triggered and not new.activated


def test_no_break_even_move_is_present():
    s=Trail1State('LONG',100,90);s.observe_completed_bar(1,110,99,95,90)
    assert s.activate_before_event(2,90)==95 != s.entry_price


def test_certification_arithmetic_uses_price_risk_and_single_c1():
    frame = pd.DataFrame({
        'direction': ['LONG', 'SHORT'], 'entry_price': [100., 100.],
        'exit_price': [110., 90.], 'initial_risk_price': [10., 10.],
        'net_R_C1': [.9998, .9998],
    })
    assert _arithmetic_audit(frame) == (0, 0.0)
    frame.loc[1, 'net_R_C1'] += 1e-6
    mismatches, maximum = _arithmetic_audit(frame)
    assert mismatches == 1 and maximum > 1e-9
