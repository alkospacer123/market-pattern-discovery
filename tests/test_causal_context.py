import pandas as pd
import pytest
from market_pattern_discovery.features.context import CausalContextEngine


def bars(times, tf):
    return pd.DataFrame({"timestamp": pd.to_datetime(times, utc=True), "symbol": "CNYRUBF",
        "timeframe": tf, "open": 1, "high": 2, "low": 1, "close": range(10, 10 + len(times)), "volume": 1})


@pytest.mark.parametrize("context_tf", ["M15", "H1", "D1"])
def test_context_is_supported_and_never_from_future(context_tf):
    context = bars(["2026-01-02 10:00"], context_tf)
    observations = bars(["2026-01-02 10:58", "2026-01-03 10:00"], "M1")
    aligned = CausalContextEngine().align(observations, context)
    available = aligned.context_close_time.notna()
    assert (aligned.loc[available].context_close_time <= aligned.loc[available].observation_close_time).all()


def test_h1_at_1059_is_unavailable_but_at_1100_is_available():
    context = bars(["2026-01-02 10:00"], "H1")
    # An M1 candle stamped 10:58 closes at 10:59; 10:59 closes at 11:00.
    result = CausalContextEngine().align(bars(["2026-01-02 10:58", "2026-01-02 10:59"], "M1"), context)
    assert pd.isna(result.iloc[0].context_close_time)
    assert result.iloc[1].context_H1_close == 10
