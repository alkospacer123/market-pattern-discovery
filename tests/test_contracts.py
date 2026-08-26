from pathlib import Path
import pandas as pd
import pytest

from market_pattern_discovery.backtest import CostModel
from market_pattern_discovery.data.finam import IngestionError, stitch_finam
from market_pattern_discovery.validation.causal import latest_closed_m5
from market_pattern_discovery.validation.temporal import DEV_END, DEV_START, sequential_split

HEADER = "<TICKER>;<PER>;<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL>\n"
def row(ticker="CNYRUBF", per=1, date="20260101", time="100000", o="10", h="12", l="9", c="11", v="5"):
    return f"{ticker};{per};{date};{time};{o};{h};{l};{c};{v}\n"
def source(tmp_path, content, name="x.csv"):
    path = tmp_path/name; path.write_text(content); return path
def load(tmp_path, content, instrument="CNY", tf="M1", name="x.csv"):
    return stitch_finam([source(tmp_path, content, name)], instrument, tf)

def test_valid_csv_and_timezone_and_m1_close(tmp_path):
    result = load(tmp_path, HEADER + row())
    candle = result.frame.iloc[0]
    assert str(candle.open_time.tz) == "Europe/Moscow"
    assert str(candle.open_utc.tz) == "UTC"
    assert candle.open_local.tzinfo is None
    assert candle.close_time - candle.open_time == pd.Timedelta(minutes=1)

def test_m5_close(tmp_path):
    candle = load(tmp_path, HEADER + row(per=5), tf="M5").frame.iloc[0]
    assert candle.close_time - candle.open_time == pd.Timedelta(minutes=5)

@pytest.mark.parametrize("content,match", [
    ("bad;schema\n1;2\n", "schema"),
    (HEADER + row(per=5), "wrong PER"),
    (HEADER + row(h="10"), "OHLC"),
    (HEADER + row(v="-1"), "volume"),
    (HEADER + row(o="nan"), "non-finite"),
    (HEADER + row(o="inf"), "non-finite"),
])
def test_invalid_rows(tmp_path, content, match):
    with pytest.raises(IngestionError, match=match): load(tmp_path, content)

@pytest.mark.parametrize("alias,ticker", [("CNY", "CNYRUBF"), ("CNYRUBF", "CNYRUBF"), ("Si", "USDRUBF"), ("USDRUBF", "USDRUBF")])
def test_aliases(tmp_path, alias, ticker):
    assert load(tmp_path, HEADER + row(ticker=ticker), alias).frame.instrument.iloc[0] == ticker

def test_development_boundaries(tmp_path):
    content = HEADER + row(date="20260101", time="000000") + row(date="20260701", time="235959")
    result = load(tmp_path, content)
    assert result.frame.open_time.iloc[0] == DEV_START
    assert result.frame.open_time.iloc[-1] <= DEV_END

@pytest.mark.parametrize("date", ["20251231", "20260702"])
def test_oos_and_outside_development_rejected(tmp_path, date):
    with pytest.raises(IngestionError, match="development interval"):
        load(tmp_path, HEADER + row(date=date))

def test_equivalent_overlap_is_deterministic(tmp_path):
    a=source(tmp_path, HEADER+row(), "q1.csv"); b=source(tmp_path, HEADER+row(), "q2.csv")
    result=stitch_finam([b,a], "CNY", "M1")
    assert len(result.frame)==1 and result.equivalent_duplicates==1
    assert result.frame.source_filename.iloc[0]=="q1.csv"

def test_conflicting_duplicate_reports_provenance(tmp_path):
    a=source(tmp_path, HEADER+row(), "q1.csv"); b=source(tmp_path, HEADER+row(c="10"), "q2.csv")
    with pytest.raises(IngestionError, match=r"q1.csv.*source_row.*q2.csv"):
        stitch_finam([a,b], "CNY", "M1")

def test_unsorted_source_sorted_and_reported(tmp_path):
    result=load(tmp_path, HEADER+row(time="100100")+row(time="100000"))
    assert result.frame.open_time.is_monotonic_increasing
    assert result.provenance[0]["originally_sorted"] is False

def test_gap_detection_does_not_fill(tmp_path):
    result=load(tmp_path, HEADER+row(time="100000")+row(time="100200"))
    assert len(result.frame)==2 and result.frame.gap_from_previous.sum()==1

def test_weekend_accounting(tmp_path):
    assert load(tmp_path, HEADER+row(date="20260103")).frame.is_weekend.sum()==1

def test_instrument_mixing(tmp_path):
    with pytest.raises(IngestionError, match="mixing"):
        load(tmp_path, HEADER+row()+row(ticker="USDRUBF"))

def test_temporal_split_and_naive_rejection():
    times=pd.Series(pd.date_range("2026-01-01", periods=3, tz="Europe/Moscow"))
    train,test=sequential_split(times, times.iloc[1])
    assert train.tolist()==[True,False,False] and test.tolist()==[False,True,True]
    with pytest.raises(ValueError, match="timezone-aware"): sequential_split(times, pd.Timestamp("2026-01-02"))

def test_cost_validation():
    assert CostModel(1, 2).slippage==2
    with pytest.raises(ValueError): CostModel(-1, 0)
    with pytest.raises(ValueError): CostModel(0, -1)

def test_exact_causal_m5_boundary():
    opened=pd.Timestamp("2026-01-05 10:10", tz="Europe/Moscow")
    m5=pd.DataFrame({"close_time":[opened+pd.Timedelta(minutes=5)], "value":[7]})
    assert latest_closed_m5(m5, pd.Timestamp("2026-01-05 10:14", tz="Europe/Moscow")) is None
    assert latest_closed_m5(m5, pd.Timestamp("2026-01-05 10:15", tz="Europe/Moscow")).value==7

def test_causal_rejects_naive_and_unordered():
    ordered=pd.DataFrame({"close_time":pd.to_datetime(["2026-01-01 10:05","2026-01-01 10:10"], utc=True)})
    with pytest.raises(ValueError, match="timezone-aware"): latest_closed_m5(ordered, pd.Timestamp("2026-01-01"))
    with pytest.raises(ValueError, match="ordered"): latest_closed_m5(ordered.iloc[::-1], pd.Timestamp("2026-01-02", tz="UTC"))

