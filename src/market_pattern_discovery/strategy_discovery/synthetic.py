"""Small causal event recognizers intended only for synthetic semantic fixtures."""
from __future__ import annotations
import pandas as pd

def known_events(df: pd.DataFrame, *, level: float = 100.0, tolerance: float = .05,
                 session_open_bars: int = 5) -> pd.DataFrame:
    """Recognize events at the close that first makes every predicate observable."""
    x=df.copy(); prior_close=x.close.shift(1); prior_high=x.high.shift(1); prior_low=x.low.shift(1)
    touch=(x.low-tolerance<=level)&(x.high+tolerance>=level)
    x["round_rejection"]=touch & (((x.close>level)&(x.open<=level))|((x.close<level)&(x.open>=level)))
    x["round_breakout"]=((prior_close<=level)&(x.close>level))|((prior_close>=level)&(x.close<level))
    x["false_breakout"]=(((prior_high>level)&(prior_close<=level)&(x.close<level))|((prior_low<level)&(prior_close>=level)&(x.close>level)))
    breakout_seen=x.round_breakout.shift(1).fillna(False).cummax()
    x["breakout_retest"]=breakout_seen & touch & (x.close-level)*(prior_close-level)>=0
    x["repeated_tests"]=touch.rolling(4,min_periods=4).sum().ge(3)
    x["equal_high"]=x.high.sub(prior_high).abs().le(tolerance)
    x["equal_low"]=x.low.sub(prior_low).abs().le(tolerance)
    x["sweep"]=((x.high>prior_high+tolerance)&(x.close<=prior_high))|((x.low<prior_low-tolerance)&(x.close>=prior_low))
    ranges=x.high-x.low
    x["compression_expansion"]=ranges.shift(1).rolling(3,min_periods=3).max().lt(tolerance*4)&ranges.gt(tolerance*8)
    x["momentum"]=x.close.pct_change(3).abs().gt(.005)
    x["mean_reversion"]=x.close.sub(x.close.shift(1).rolling(3,min_periods=3).mean()).abs().gt(ranges.shift(1).rolling(3,min_periods=3).mean()*2)
    x["previous_high_low"]=((x.close>prior_high.shift(1).expanding().max())|(x.close<prior_low.shift(1).expanding().min()))
    opening_high=x.high.iloc[:session_open_bars].max(); opening_low=x.low.iloc[:session_open_bars].min()
    x["opening_range"]=False
    if len(x)>session_open_bars:
        idx=x.index[session_open_bars:]; x.loc[idx,"opening_range"]=(x.loc[idx,"close"]>opening_high)|(x.loc[idx,"close"]<opening_low)
    return x
