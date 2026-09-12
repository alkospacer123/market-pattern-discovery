import json
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.audit_t3 import BASELINE_DIR, run_audit


def test_audit_reads_frozen_metrics_and_reconciles(tmp_path):
    frozen = json.loads((BASELINE_DIR / "metrics.json").read_text())
    result = run_audit(BASELINE_DIR, tmp_path / "audit")
    assert result["frozen_metrics_reconciled"] is True
    assert result["overall"]["net_profit"] == pytest.approx(frozen["net_profit"])
    assert result["overall"]["profit_factor"] == pytest.approx(frozen["profit_factor"])


def test_audit_creates_required_text_artifacts(tmp_path):
    output = tmp_path / "audit"
    run_audit(BASELINE_DIR, output)
    required = {"summary.md", "statistics.json", "equity_curve.svg", "r_distribution.svg",
                "monthly_returns.csv", "yearly_report.csv", "mae_mfe_analysis.csv"}
    assert {path.name for path in output.iterdir()} == required
    for name in ("equity_curve.svg", "r_distribution.svg"):
        content = (output / name).read_text(encoding="utf-8")
        assert content.startswith("<?xml")
        assert "<svg" in content
        assert "base64" not in content.lower()
    assert not list(output.glob("*.png"))
    assert not list(output.glob("*.jpg"))
    assert not list(output.glob("*.jpeg"))


def test_true_oos_is_rejected(tmp_path):
    source = tmp_path / "baseline"
    source.mkdir()
    for name in ("metrics.json", "trades.csv", "equity_curve.csv"):
        (source / name).write_bytes((BASELINE_DIR / name).read_bytes())
    trades = pd.read_csv(source / "trades.csv")
    trades.loc[0, "exit_time"] = "2025-01-01T00:00:00Z"
    trades.to_csv(source / "trades.csv", index=False)
    with pytest.raises(ValueError, match=r"2025\+"):
        run_audit(source, tmp_path / "audit")


def test_mae_mfe_are_not_fabricated(tmp_path):
    output = tmp_path / "audit"
    run_audit(BASELINE_DIR, output)
    excursions = pd.read_csv(output / "mae_mfe_analysis.csv")
    assert list(excursions.columns) == ["trade_number", "MAE", "MFE"]
    assert excursions[["MAE", "MFE"]].isna().all().all()
    summary = (output / "summary.md").read_text(encoding="utf-8")
    assert "MAE/MFE unavailable from frozen baseline artifacts." in summary
    assert "Intratrade OHLC path is required." in summary
