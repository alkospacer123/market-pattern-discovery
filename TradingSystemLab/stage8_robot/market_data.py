"""Market data protocol and strict H1 stream validator."""
from datetime import datetime,timedelta
from typing import Protocol,Iterable
from .strategy_core import CompletedBar,validate_bar
class MarketData(Protocol):
    def completed_h1(self,instrument:str,since:datetime)->Iterable[CompletedBar]: ...
def validate_stream(bars:Iterable[CompletedBar],now:datetime,stale_after:timedelta=timedelta(hours=2))->list[CompletedBar]:
    accepted=[]; previous=None
    for bar in bars: validate_bar(bar,now,previous); accepted.append(bar); previous=bar.timestamp
    if not accepted or now-accepted[-1].timestamp>stale_after: raise ValueError("MARKET_DATA_STALE")
    return accepted
