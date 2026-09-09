from pathlib import Path
import pytest

from market_pattern_discovery.data import CANONICAL_COLUMNS, MarketDataLoader, TIMEFRAMES
from market_pattern_discovery.data.finam import IngestionError


def source(tmp_path: Path, symbol="CNYRUBF", per=15):
    path = tmp_path / "bar.csv"
    path.write_text("<TICKER>;<PER>;<DATE>;<TIME>;<OPEN>;<HIGH>;<LOW>;<CLOSE>;<VOL>\n"
                    f"{symbol};{per};20260102;100000;10;12;9;11;5\n")
    return path


def test_registry_has_all_required_timeframes():
    assert tuple(TIMEFRAMES) == ("M1", "M5", "M15", "M30", "H1", "D1")
    assert TIMEFRAMES["D1"].finam_period == "D"


def test_loader_normalizes_and_preserves_metadata(tmp_path):
    result = MarketDataLoader(tmp_path).load("CNY", "M15", (source(tmp_path),))
    assert list(result) == CANONICAL_COLUMNS
    assert result.iloc[0].symbol == "CNYRUBF"
    assert result.attrs["metadata"]["finam_period"] == 15


def test_loader_rejects_invalid_ohlc(tmp_path):
    path = source(tmp_path)
    path.write_text(path.read_text().replace("10;12;9;11", "10;8;9;11"))
    with pytest.raises(IngestionError, match="OHLC"):
        MarketDataLoader(tmp_path).load("CNY", "M15", (path,))
