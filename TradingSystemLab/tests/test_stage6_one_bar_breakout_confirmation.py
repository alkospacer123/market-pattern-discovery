import pandas as pd
from TradingSystemLab.results.post_v3_analysis.stage6_one_bar_breakout_confirmation.generate_one_bar_reassessment import confirmation_transition

def test_confirmation_succeeds_same_direction():
 confirmed,pending,reason=confirmation_transition(('LONG',pd.Timestamp('2024-01-01 10:00Z')),'LONG')
 assert confirmed and pending is None and reason is None

def test_confirmation_disappears_and_expires_exactly_one_bar():
 assert confirmation_transition('LONG',None)==(False,None,'NONE')
 # t+2 LONG is necessarily a new pending event, not confirmation of expired t.
 assert confirmation_transition(None,'LONG')==(False,'LONG',None)

def test_confirmation_reverses_and_rearms_short():
 assert confirmation_transition('LONG','SHORT')==(False,'SHORT','OPPOSITE')
 assert confirmation_transition('SHORT','SHORT')==(True,None,None)

def test_context_invariance_and_confirmation_bar_inputs():
 context=pd.DataFrame({'Close':[100.,105.],'ATR':[2.,3.]},index=pd.date_range('2024-01-01',periods=2,freq='h',tz='UTC')); before=context.copy(deep=True)
 confirmed,_,_=confirmation_transition('LONG','LONG'); entry=context.iloc[1].Close; stop=entry-2.5*context.iloc[1].ATR
 assert confirmed and entry==105 and stop==97.5 and entry!=context.iloc[0].Close
 pd.testing.assert_frame_equal(context,before)
