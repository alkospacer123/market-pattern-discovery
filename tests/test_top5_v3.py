import copy,csv,json
from pathlib import Path
import numpy as np,pandas as pd,pytest
from market_pattern_discovery.data.finam import load_finam_window,IngestionError,SCHEMA
from market_pattern_discovery.backtest.top5 import *
from market_pattern_discovery.backtest.top5 import _signal

def write_csv(path,rows,header=SCHEMA):
 with path.open('w',newline='') as f:
  w=csv.writer(f,delimiter=';');w.writerow(header);w.writerows(rows)
def row(tm,o=10,h=11,l=9,c=10,v=1,t='CNYRUBF'):return [t,1,20260105,tm,o,h,l,c,v]
def tiny(n=8):
 t=pd.date_range('2026-01-05 10:00',periods=n,freq='min',tz='Europe/Moscow');c=np.ones(n)*10
 return pd.DataFrame(dict(open_time=t,close_time=t+pd.Timedelta(minutes=1),open=c,high=c+.1,low=c-.1,close=c,volume=1,trading_date=t.date,instrument='CNYRUBF'))

def test_window_boundaries_and_prefix(tmp_path):
 p=tmp_path/'x.csv';write_csv(p,[row(95900),row(100000),row(100100),row(100200)])
 r=load_finam_window(p,'CNYRUBF','M1',pd.Timestamp('2026-01-05 10:00',tz='Europe/Moscow'),pd.Timestamp('2026-01-05 10:02',tz='Europe/Moscow'))
 assert list(r.frame.open_time.dt.minute)==[0,1] and list(r.frame.source_row)==[3,4]
def test_window_malformed_schema(tmp_path):
 p=tmp_path/'x';write_csv(p,[row(100000)],SCHEMA[:-1]);
 with pytest.raises(IngestionError):load_finam_window(p,'CNYRUBF','M1',pd.Timestamp('2026-01-05',tz='Europe/Moscow'),pd.Timestamp('2026-01-06',tz='Europe/Moscow'))
def test_window_bad_ohlc(tmp_path):
 p=tmp_path/'x';write_csv(p,[row(100000,h=8)])
 with pytest.raises(IngestionError):load_finam_window(p,'CNYRUBF','M1',pd.Timestamp('2026-01-05',tz='Europe/Moscow'),pd.Timestamp('2026-01-06',tz='Europe/Moscow'))
def test_window_equivalent_duplicate(tmp_path):
 p=tmp_path/'x';write_csv(p,[row(100000),row(100000)])
 r=load_finam_window(p,'CNYRUBF','M1',pd.Timestamp('2026-01-05',tz='Europe/Moscow'),pd.Timestamp('2026-01-06',tz='Europe/Moscow'));assert len(r.frame)==1 and r.equivalent_duplicates==1
def test_window_conflicting_duplicate(tmp_path):
 p=tmp_path/'x';write_csv(p,[row(100000),row(100000,c=10.5)])
 with pytest.raises(IngestionError):load_finam_window(p,'CNYRUBF','M1',pd.Timestamp('2026-01-05',tz='Europe/Moscow'),pd.Timestamp('2026-01-06',tz='Europe/Moscow'))
@pytest.mark.parametrize('value,expected',[(1.234,1.234),(1.2345,1.235),(1.2344999999999999,1.235)])
def test_round_tick(value,expected):assert round_to_tick(value,.001)==expected
def test_bad_tick():
 with pytest.raises(ValueError):round_to_tick(1,0)
def test_m5_duplicate_rejected():
 x=tiny(5);x.loc[4,'open_time']=x.loc[3,'open_time']
 with pytest.raises(ValueError):causal_m5(x)
def test_m5_missing_minute_incomplete():assert causal_m5(tiny(5).drop(2)).empty
def test_m5_trading_date_boundary():
 x=tiny(5);x.loc[3:,'trading_date']=pd.Timestamp('2026-01-06').date();assert causal_m5(x).empty
def test_flat_top_first_only():
 x=pd.DataFrame({'high':[1,2,3,3,2,1],'low':[.5]*6,'close_time':pd.date_range('2026-01-05',periods=6,freq='5min',tz='Europe/Moscow')});p=confirmed_pivots(x);assert list(p[p.side.eq('HIGH')].pivot_index)==[2]
def test_flat_bottom_first_only():
 x=pd.DataFrame({'high':[5]*6,'low':[3,2,1,1,2,3],'close_time':pd.date_range('2026-01-05',periods=6,freq='5min',tz='Europe/Moscow')});p=confirmed_pivots(x);assert list(p[p.side.eq('LOW')].pivot_index)==[2]
def test_orb_unknown_stop():
 with pytest.raises(ValueError):orb_signals(tiny(), 'CNYRUBF',5,stop_mode='NOPE')
def test_exact_open_gap_diagnostic():
 x=tiny(5);s=pd.DataFrame([_signal('X','Y','CNYRUBF',x.close_time.iloc[-1]+pd.Timedelta(minutes=2),1,10,9,2)]);l=simulate_explicit_orders(x,s,.001);assert l.empty
def test_ambiguous_signal_diagnostic():
 x=tiny(6);s=pd.DataFrame([_signal('X','Y','CNYRUBF',x.close_time.iloc[0],1,10,9,2)]*2);l=simulate_explicit_orders(x,s,.001);assert l.empty and l.attrs['skip_diagnostics'][0]['reason']=='AMBIGUOUS_SIMULTANEOUS_SIGNAL'
def test_day_end_reason():
 x=tiny(3);s=pd.DataFrame([_signal('X','Y','CNYRUBF',x.close_time.iloc[0],1,10,9,20)]);l=simulate_explicit_orders(x,s,.001);assert set(l.exit_reason)=={'DAY_END'}
def test_pair_threshold_cross_rearm(monkeypatch):
 z=[0,2.1,2.2,1,2.3];x=tiny(5);f=x.rename(columns={'open_time':'open_time_cny'}).copy();f['open_time_si']=f.open_time_cny;f['open_time']=f.open_time_cny;f['z']=z;f['beta']=1.;f['spread']=z
 monkeypatch.setattr('market_pattern_discovery.backtest.top5.pair_features',lambda *a,**k:f)
 s=pair_signals(x,x,1,2,'DISTANCE');assert len(s)==2
def test_contract_mutations_fail():
 c=json.loads(Path('results/top5_real_strategies_v3/strategy_contract.json').read_text());assert validate_contract(c)
 for key in ('commission_model','tick_rounding'):
  b=copy.deepcopy(c);b[key]='MUTATED'
  with pytest.raises(ValueError):validate_contract(b)
def test_contract_missing_key_fails():
 c=json.loads(Path('results/top5_real_strategies_v3/strategy_contract.json').read_text());del c['execution']
 with pytest.raises(ValueError):validate_contract(c)
def test_gerchik_contract_fidelity():
 c=json.loads(Path('results/top5_real_strategies_v3/strategy_contract.json').read_text());assert c['source_fidelity']['GERCHIK_A_M5_PROXY']['source_fidelity']=='PROXY_NOT_EXACT_SOURCE_REPLICATION'
def test_failed_diagnostic_ineligible():
 c=json.loads(Path('results/top5_real_strategies_v3/strategy_contract.json').read_text());assert c['selection_policy']['diagnostic_selection_eligible'] is False
def test_bollinger_hold_is_60():
 c=json.loads(Path('results/top5_real_strategies_v3/strategy_contract.json').read_text());assert c['max_holding']['BOLLINGER_RSI']==60
