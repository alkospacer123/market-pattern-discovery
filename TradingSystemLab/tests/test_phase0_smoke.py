from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.core.instrument_specs import get_instrument_spec
from TradingSystemLab.phase0_smoke import load_development


def test_si_instrument_spec_contract() -> None:
    spec = get_instrument_spec("Si")
    assert (spec.lot_size, spec.price_step, spec.tick_value_rub, spec.currency) == (1000, 0.001, 1, "RUB")


def test_prefix_loader_stops_before_true_oos_and_validates_order(tmp_path: Path) -> None:
    source = tmp_path / "bars.csv"
    source.write_text("Datetime;Open;High;Low;Close;Volume\n"
                      "2024-12-31 23:00:00;1;3;0;2;10\n"
                      "2025-01-01 00:00:00;2;4;1;3;11\n"
                      "BROKEN LOCKED ROW\n", encoding="utf-8")
    frame = DataLoader().load_csv_prefix(source, start=pd.Timestamp("2020-01-01"),
                                         end_exclusive=pd.Timestamp("2025-01-01"))
    assert len(frame) == 1
    assert frame.index.tz is not None
    assert frame.index.max().year == 2024


def test_prefix_loader_rejects_duplicate_and_invalid_ohlc(tmp_path: Path) -> None:
    source = tmp_path / "bars.csv"
    source.write_text("Datetime;Open;High;Low;Close\n"
                      "2024-01-01 10:00:00;1;0;2;1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid OHLC"):
        DataLoader().load_csv_prefix(source, start=pd.Timestamp("2020-01-01"),
                                     end_exclusive=pd.Timestamp("2025-01-01"))


def test_declared_source_loads_only_development_data() -> None:
    frame, source, quality = load_development(Path("/workspace/market-pattern-data"))
    assert source.name == "Si_M30.csv"
    assert quality["status"] == "PASS"
    assert quality["timezone"] == "Europe/Moscow"
    assert quality["duplicate_timestamps"] == 0
    assert frame.index.min() >= pd.Timestamp("2020-01-01", tz="Europe/Moscow")
    assert frame.index.max() < pd.Timestamp("2025-01-01", tz="Europe/Moscow")
