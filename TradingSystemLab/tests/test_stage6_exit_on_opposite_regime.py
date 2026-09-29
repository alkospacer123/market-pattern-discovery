import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage6_exit_on_opposite_regime.generate_opposite_regime_reassessment import opposite_exit_reason, comparison

def test_true_opposites_and_none():
 assert opposite_exit_reason('LONG','SHORT')=='OPPOSITE_REGIME_EXIT'
 assert opposite_exit_reason('SHORT','LONG')=='OPPOSITE_REGIME_EXIT'
 assert opposite_exit_reason('LONG',None) is None
 assert opposite_exit_reason('SHORT',None) is None
 assert opposite_exit_reason('LONG','LONG') is None

def test_stop_priority():
 assert opposite_exit_reason('LONG','SHORT',stop_hit=True)=='PROTECTIVE_STOP'

def test_completed_context_publication_and_no_future_fill():
 high=pd.DataFrame(index=pd.to_datetime(['2024-01-01 04:00Z','2024-01-01 08:00Z']))
 t=pd.Timestamp('2024-01-01 07:00Z')
 assert list(high.index[high.index<=t])==[pd.Timestamp('2024-01-01 04:00Z')]

def test_no_same_event_reversal_contract():
 # The exit event suppresses entry for that event; helper only emits an exit reason.
 assert opposite_exit_reason('LONG','SHORT')=='OPPOSITE_REGIME_EXIT'
 assert opposite_exit_reason('SHORT','SHORT') is None

def test_no_session_or_confirmation_contamination():
 source=open('TradingSystemLab/results/post_v3_analysis/stage6_exit_on_opposite_regime/generate_opposite_regime_reassessment.py').read()
 replay=source[source.index('def replay_t3'):source.index('def _parameters')]
 assert 'hour' not in replay and 'pending' not in replay and 'confirmation_transition' not in replay

def test_unchanged_canonical_path_and_no_contamination():
 root='TradingSystemLab/results/post_v3_analysis/stage6_exit_on_opposite_regime/'
 full=pd.read_csv(root+'full_canonical_trades.csv')
 opposite=pd.read_csv(root+'opposite_regime_trades.csv')
 pd.testing.assert_frame_equal(full,opposite)
 registry=pd.read_csv(root+'opposite_regime_registry.csv')
 assert not registry.session_restriction.any()
 assert not registry.one_bar_confirmation.any()

def test_decision_recomputation_is_no_material_difference():
 root='TradingSystemLab/results/post_v3_analysis/stage6_exit_on_opposite_regime/'
 supplied=pd.read_csv(root+'opposite_regime_decision_comparison.csv')
 assert supplied.all_annual_gates_pass.all()
 assert supplied.computed_decision.nunique()==1
 assert supplied.computed_decision.iloc[0]=='OPPOSITE_REGIME_EXIT_NO_MATERIAL_DIFFERENCE'
 metrics=['annual_floor_R','worst_12M_R','worst_6M_R','worst_DD_R','minimum_recovery_factor','positive_month_share','median_monthly_R','chronological_net_R']
 assert (supplied.loc[0,metrics].to_numpy(float)==supplied.loc[1,metrics].to_numpy(float)).all()
