"""FINAM H1 normalization with completed-candle and stale-data enforcement."""
from datetime import datetime,timedelta
from typing import Protocol,Iterable
from zoneinfo import ZoneInfo
from .strategy_core import CompletedBar,validate_bar
class MarketData(Protocol):
    def completed_h1(self,instrument:str,since:datetime)->Iterable[CompletedBar]: ...
def normalize_finam_h1(payload:dict,now:datetime)->list[CompletedBar]:
    rows=payload.get("candles",payload.get("data",payload if isinstance(payload,list) else [])); result=[]
    current=now.astimezone(ZoneInfo("Europe/Moscow"))
    for row in rows:
        opened=datetime.fromisoformat(str(row.get("timestamp",row.get("time"))).replace("Z","+00:00")).astimezone(ZoneInfo("Europe/Moscow"))
        closed=opened+timedelta(hours=1)
        if closed>current: continue
        result.append(CompletedBar(closed,float(row["open"]),float(row["high"]),float(row["low"]),float(row["close"]),float(row.get("atr",1)),completed=True))
    return validate_stream(result,now)
def validate_stream(bars:Iterable[CompletedBar],now:datetime,stale_after:timedelta=timedelta(hours=2))->list[CompletedBar]:
    accepted=[]; previous=None
    for bar in bars: validate_bar(bar,now,previous); accepted.append(bar); previous=bar.timestamp
    if not accepted or now.astimezone(ZoneInfo("Europe/Moscow"))-accepted[-1].timestamp>stale_after: raise ValueError("MARKET_DATA_STALE")
    return accepted
