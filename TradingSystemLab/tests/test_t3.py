import pandas as pd
import pytest

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend


def test_h4_is_available_only_at_fourth_close_and_resets_each_day():
    index = pd.date_range("2024-01-02 10:00", periods=5, freq="h", tz="Europe/Moscow")
    frame = pd.DataFrame({"Open": range(5), "High": range(1, 6), "Low": range(5),
                          "Close": range(1, 6), "Volume": 1}, index=index)
    result = DataLoader.h4_from_h1(frame)
    assert list(result.index) == [index[3]]
    assert result.iloc[0].to_dict() == {"Open": 0, "High": 4, "Low": 0, "Close": 4, "Volume": 4}


def test_breakout_excludes_signal_bar():
    index = pd.date_range("2024-01-01", periods=21, freq="h", tz="UTC")
    h1 = pd.DataFrame({"Open": 1.0, "High": 2.0, "Low": 0.0, "Close": 1.0}, index=index)
    h1.iloc[-1, h1.columns.get_loc("High")] = 10
    h1.iloc[-1, h1.columns.get_loc("Close")] = 9
    h4 = h1.copy()
    low, _ = T3MTFTrend().calculate_indicators(h1, h4)
    assert low.iloc[-1]["PriorHigh"] == 2


def test_loader_rejects_true_oos_before_research(tmp_path):
    path = tmp_path / "bars.csv"
    path.write_text("Date,Time,Open,High,Low,Close\n20250101,100000,1,2,0,1\n")
    with pytest.raises(ValueError, match="TRUE OOS"):
        DataLoader(timezone="UTC").load_csv(path)
