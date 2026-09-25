import pandas as pd
from TradingSystemLab.true_oos.phase5_v2 import (BOOTSTRAP_ITERATIONS,BOOTSTRAP_SEED,
    INSTRUMENTS,STUDIES,TRUE_OOS_START,classify,four_bar_context)

def test_frozen_universe_and_contract():
    assert STUDIES==(("T2","M30"),("T2","H1"),("T3","M30"),("T3","H1"))
    assert INSTRUMENTS==("Si","CNY","GD","BR","MIX","NG")
    assert TRUE_OOS_START==pd.Timestamp("2025-01-01",tz="Europe/Moscow")
    assert (BOOTSTRAP_ITERATIONS,BOOTSTRAP_SEED)==(10_000,5102025)

def test_context_is_cold_complete_local_day_blocks():
    idx=pd.date_range("2025-01-01 10:30",periods=5,freq="30min",tz="Europe/Moscow")
    frame=pd.DataFrame({"Open":range(5),"High":range(1,6),"Low":range(5),"Close":range(1,6)},index=idx)
    context=four_bar_context(frame)
    assert len(context)==1 and context.index[0]==idx[3]
    assert context.index.min()>=TRUE_OOS_START

def test_exact_classification_boundaries():
    good={"total_trades":50,"expectancy":.1}
    assert classify(good,.95,5,3,True,True,.1)=="PASS"
    assert classify({**good,"total_trades":49},.95,5,3,True,True,.1)=="BORDERLINE"
    assert classify({**good,"expectancy":0},.99,5,5,True,True,.1)=="FAIL"
    assert classify(good,.50,5,5,True,True,.1)=="FAIL"
    for args in ((.94,5,5,True,True,.1),(.99,5,2,True,True,.1),(.99,5,5,False,True,.1),(.99,5,5,True,False,.1),(.99,5,5,True,True,0)):
        assert classify(good,*args)=="BORDERLINE"
