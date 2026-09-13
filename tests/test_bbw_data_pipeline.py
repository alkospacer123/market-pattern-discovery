import json
from pathlib import Path
import pandas as pd
import pytest

from bbw_system.data_pipeline import (CANONICAL_COLUMNS, CalendarConfig, NormalizationConfig,
    build_manifest, dataframe_sha256, liquidity_profile, normalize, setup_crosses_rollover,
    coverage_report)
from bbw_system.preflight import baseline_preflight


def raw(times):
    n=len(times)
    return pd.DataFrame({'timestamp':times,'open':[10.]*n,'high':[11.]*n,'low':[9.]*n,'close':[10.5]*n,'volume':[1.]*n})

def cfg(**kw):
    values=dict(symbol='BR',timeframe='H1',source_timezone='UTC',exchange_timezone='Europe/Moscow',session_start='10:00',session_end='23:00')
    values.update(kw); return NormalizationConfig(**values)

def test_canonical_schema(): assert CANONICAL_COLUMNS == ('timestamp','open','high','low','close','volume','symbol','timeframe')
def test_duplicate_detection():
    out,r=normalize(raw(['2024-01-08 07:00']*2),cfg()); assert r['duplicates']==1 and out.reason_code.eq('DUPLICATE').sum()==1
def test_ohlc_validation():
    x=raw(['2024-01-08 07:00']); x.loc[0,'high']=1; out,r=normalize(x,cfg()); assert out.status.iloc[0]=='ERROR' and r['invalid_ohlc']==1
def test_timezone_normalization():
    out,_=normalize(raw(['2024-01-08 07:00']),cfg()); assert str(out.timestamp.dt.tz)=='Europe/Moscow' and out.timestamp.dt.hour.iloc[0]==10
def test_timezone_is_not_guessed():
    with pytest.raises(ValueError): normalize(raw(['2024-01-08']),cfg(source_timezone=None))
def test_weekend_exclusion():
    out,_=normalize(raw(['2024-01-06 07:00']),cfg()); assert out.reason_code.iloc[0]=='WEEKEND'
def test_explicit_holiday_exclusion():
    c=CalendarConfig(holiday_dates=('2024-01-08',)); out,_=normalize(raw(['2024-01-08 07:00']),cfg(calendar=c)); assert out.reason_code.iloc[0]=='HOLIDAY'
def test_shortened_session_handling():
    c=CalendarConfig(shortened_session_dates={'2024-01-08':'12:00'}); out,_=normalize(raw(['2024-01-08 11:00']),cfg(calendar=c)); assert out.reason_code.iloc[0]=='OUTSIDE_SESSION'
def test_session_breaks():
    out,_=normalize(raw(['2024-01-08 10:30']),cfg(breaks=(('13:00','14:00'),))); assert out.reason_code.iloc[0]=='OUTSIDE_SESSION'
def test_zero_volume_reporting():
    x=raw(['2024-01-08 07:00']); x.volume=0; out,r=normalize(x,cfg()); assert r['zero_volume_bars']==1 and liquidity_profile(out).zero_volume_pct.iloc[0]==100
def test_missing_bar_reporting():
    out,r=normalize(raw(['2024-01-08 07:00','2024-01-08 10:00']),cfg()); assert r['large_gaps']==1 and coverage_report(out,'H1').missing_expected_intervals.iloc[0]==2
def test_hash_manifest_stability(tmp_path):
    p=tmp_path/'x.csv'; p.write_text('x\n1\n'); out,_=normalize(raw(['2024-01-08 07:00']),cfg()); assert build_manifest(p,out,cfg())==build_manifest(p,out,cfg()) and dataframe_sha256(out)==dataframe_sha256(out.copy())
def test_rollover_flag_preservation():
    x=raw(['2024-01-08 07:00']); x['roll_flag']=True; out,_=normalize(x,cfg()); assert bool(out.roll_flag.iloc[0])
def test_setup_crossing_rollover_blocked():
    x=raw(['2024-01-08 07:00']); x['roll_flag']=True; out,_=normalize(x,cfg()); assert setup_crosses_rollover(out,out.timestamp.iloc[0],out.timestamp.iloc[0],'continuous_unadjusted','reject_crossing_setup')
def test_series_classification_plumbing():
    x=raw(['2024-01-08 07:00']); out,_=normalize(x,cfg()); t=out.timestamp.iloc[0]; assert not setup_crosses_rollover(out,t,t,'continuous_adjusted','allow_adjusted_series') and setup_crosses_rollover(out,t,t,'continuous_adjusted','individual_contract_only')
def passport(**updates):
    keys=('source_timezone','exchange_timezone','session','tick_size','tick_value_per_contract','go_per_contract','commission_value','rollover_policy'); p={k:{'value':1,'verified':True} for k in keys}; p.update(updates); return p
def strategy():
    keys=('bbw_period','bbw_std','threshold_trading_days','threshold_minima','ema','ema_slope','atr','range_bars','atr_range_bounds','max_width_pct','retest_min_bars','retest_max_bars','penetration','stop_offset','stop_min_max','entry_extension','confirmation_candle_limit','risk_pct','margin_limit','commissions','slippage','tp_allocations'); return {k:{'status':'FIXED','value':1} for k in keys}
def test_preflight_unknown_tick_size(): assert any('tick_size' in x for x in baseline_preflight(passport(tick_size={'value':None,'verified':False}),strategy()))
def test_preflight_unknown_tick_value(): assert any('tick_value' in x for x in baseline_preflight(passport(tick_value_per_contract={'value':None,'verified':False}),strategy()))
def test_no_silent_go_or_commission():
    errors=baseline_preflight(passport(go_per_contract={'value':None,'verified':False},commission_value={'value':None,'verified':False}),strategy()); assert any('go_per' in x for x in errors) and any('commission' in x for x in errors)
def test_market_directories_ignored():
    text=Path('.gitignore').read_text(); assert all(x in text for x in ('bbw_system/data/raw/','bbw_system/data/normalized/','bbw_system/results/','bbw_system/cache/'))
