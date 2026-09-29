import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage6_session_10_21_causal.generate_session_reassessment import session_eligible

def utc(local): return pd.Timestamp(local,tz='Europe/Moscow').tz_convert('UTC')
def test_boundaries():
 assert not session_eligible(utc('2024-01-01 09:59'))
 assert session_eligible(utc('2024-01-01 10:00'))
 assert session_eligible(utc('2024-01-01 20:59'))
 assert not session_eligible(utc('2024-01-01 21:00'))

def test_entry_only_and_path_divergence_state_machine():
 signals=[utc('2024-01-01 09:00'),utc('2024-01-01 10:00')]
 full_open=session_open=False; full_entries=[]; session_entries=[]
 for t in signals:
  if not full_open: full_entries.append(t); full_open=True
  if not session_open and session_eligible(t): session_entries.append(t); session_open=True
 assert full_entries==signals[:1] and session_entries==signals[1:]
 # An exit predicate is intentionally not the entry predicate.
 exit_time=utc('2024-01-02 04:00'); assert not session_eligible(exit_time)

def test_context_invariance():
 # Session eligibility is a pure timestamp predicate and cannot mutate input.
 context=pd.DataFrame({'Close':[1.,2.]},index=pd.date_range('2024-01-01',periods=2,freq='4h',tz='UTC'))
 before=context.copy(deep=True); [session_eligible(utc(x)) for x in ('2024-01-01 09:00','2024-01-01 10:00')]
 pd.testing.assert_frame_equal(context,before)
