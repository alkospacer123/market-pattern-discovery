from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from . import engine, scalar, study


def synthetic():
    idx=pd.date_range('2024-01-02 11:00',periods=4,freq='h',tz='Europe/Moscow')
    frame=pd.DataFrame({'Open':[100.,104.,104.,99.], 'High':[200.,107.,106.,100.],
                        'Low':[1.,100.,102.,98.], 'Close':[104.,106.,104.,99.], 'Volume':1.},index=idx)
    low=frame.assign(ATR=2.,PriorHigh=103.,PriorLow=90.)
    high=pd.DataFrame({'Close':[110.], 'EMA100':[100.], 'EMA100Slope':[1.], 'ADX':[30.],
                       'ATR':[3.], 'ATRMean20':[2.]},index=idx[:1])
    return frame,(low,high)


def test_authenticate_frozen_sources_and_candidate():
    assert study.authenticate()
    assert engine.PARAMETERS['stop_atr']==2.5


def test_entry_bar_extreme_excluded_delayed_trail_and_gap_fill():
    frame,prepared=synthetic()
    trades,trace,opened=engine.run(frame,'LONG_SHORT_C1',prepared)
    first=trades.iloc[0]
    assert first.entry_time==frame.index[0]
    assert first.exit_time==frame.index[3]
    assert first.trigger_bar_time==frame.index[1] or not first.trail1_triggered
    # +1R is 109, not reached by any later high, so entry high=200 must not trigger.
    assert not first.trail1_triggered and first.exit_price==99.
    assert opened is None


@pytest.mark.parametrize('direction', ['LONG','SHORT'])
def test_trigger_not_retroactive_stop_and_activation_before_next_bar(direction):
    from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State
    s=Trail1State(direction,100.,95. if direction=='LONG' else 105.)
    candidate=102. if direction=='LONG' else 98.
    assert s.observe_completed_bar('a',106.,94.,candidate,s.initial_stop_price)
    assert s.activate_before_event('a',s.initial_stop_price)==s.initial_stop_price
    assert s.activate_before_event('b',s.initial_stop_price)==candidate
    assert s.stop_fill(90. if direction=='LONG' else 110.,candidate)==(90. if direction=='LONG' else 110.)


def test_stop_test_precedes_trigger_extremes():
    frame,(low,high)=synthetic()
    low.loc[frame.index[1],['High','Low']]=[200.,90.]
    trades,_,_=engine.run(frame,'LONG_SHORT_C1',(low,high))
    assert not trades.iloc[0].trail1_triggered
    assert trades.iloc[0].exit_time==frame.index[1]


def test_no_forced_end_exit():
    frame,prepared=synthetic()
    a,_,opened=engine.run(frame.iloc[:1],'LONG_ONLY_C1',(prepared[0].iloc[:1],prepared[1]))
    assert len(a)==0 and opened['status']=='OPEN' and opened['realized_net_R'] is None


def test_long_only_is_a_separate_path_not_filtered_long_short_trades():
    frame,(low,high)=synthetic()
    high=pd.concat([high,high.set_axis(frame.index[1:2])])
    high.loc[frame.index[0],['Close','EMA100Slope']]=[90.,-1.]
    low.loc[frame.index[0],'PriorLow']=105.
    ls,_,opened=engine.run(frame,'LONG_SHORT_C1',(low,high))
    lo,_,_=engine.run(frame,'LONG_ONLY_C1',(low,high))
    assert len(ls)==0 and opened['direction']=='SHORT'
    assert len(lo)==1 and lo.iloc[0].direction=='LONG'


@pytest.mark.parametrize('direction,price,expected',[('LONG',100.019,100.01),('SHORT',100.011,100.02)])
def test_stock_rounding_outwards(direction,price,expected):
    assert engine.project(direction,price,.01)==expected


def test_scalar_features_against_frozen_causal_features():
    index=pd.date_range('2022-01-01 01:00',periods=1100,freq='h',tz='Europe/Moscow')
    x=100+np.arange(1100)*.1+np.sin(np.arange(1100)/5)
    frame=pd.DataFrame({'Open':x,'High':x+1,'Low':x-1,'Close':x+.2,'Volume':1},index=index)
    for a,b in zip(engine.features(frame),scalar.features(frame)):
        assert a.index.equals(b.index)
        for col in b:
            assert a[col].isna().equals(b[col].isna())
            assert np.allclose(a[col],b[col],atol=1e-9,rtol=0,equal_nan=True)


def test_context_uses_close_date_and_four_rows_across_intraday_gap():
    index=pd.DatetimeIndex(['2024-01-01 23:00','2024-01-02 00:00','2024-01-02 10:00','2024-01-02 11:00','2024-01-02 12:00'],tz='Europe/Moscow')
    frame=pd.DataFrame({'Open':1.,'High':2.,'Low':1.,'Close':2.},index=index)
    _,h=engine.features(frame)
    assert list(h.index)==[index[-1]]
    assert scalar.features(frame)[1].index.equals(h.index)


def test_closed_r_dd_pf_and_empty_denominator():
    f=pd.DataFrame({'net_R':[2.,-1.,-3.,5.],'gross_R':[2.1,-.9,-2.9,5.1],'cost_R':.1})
    assert study.metrics(f)['max_closed_R_DD']==-4.
    assert study.metrics(f)['net_PF']==7/4
    assert study.metrics(f.iloc[:1])['net_PF'] is None
    assert study.metrics(f.iloc[:0])['trades']==0


def test_prefix_does_not_parse_heldout_prices(tmp_path,monkeypatch):
    p=tmp_path/'data.csv'
    p.write_text('Datetime;Open;High;Low;Close;Volume\n2024-12-30 10:00:00;1;2;1;2;1\n2025-01-01 10:00:00;SECRET_INVALID;X;X;X;X\n')
    monkeypatch.setattr(study,'DATA_SHA',study.sha(p))
    raw,closed,excluded=study.load(p,False)
    assert len(raw)==1 and len(closed)==1 and not len(excluded)
    with pytest.raises(ValueError):study.load(p,True)


def test_mismatch_audit_detects_changed_trade():
    frame,prepared=synthetic()
    a,_,_=engine.run(frame,'LONG_SHORT_C1',prepared)
    b=a.copy();b.loc[0,'exit_price']+=1
    assert study.compare(a,b,'mutation')['status']=='FAIL'
