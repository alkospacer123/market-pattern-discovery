import ast
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from TradingSystemLab.audit_perpetual_v3_baseline import audit


CANONICAL = Path("TradingSystemLab/results/perpetual_v3/baseline")
AUDIT_SOURCE = Path("TradingSystemLab/audit_perpetual_v3_baseline.py")
RUN = Path("T2/M30/USDRUBF")


def test_audit_has_no_production_runner_or_contract_imports():
    tree = ast.parse(AUDIT_SOURCE.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any("perpetual_v3_baseline" in name for name in imports)
    assert not any(name.startswith("TradingSystemLab") or name.startswith(".core") for name in imports)


def test_canonical_independent_audit_passes():
    result = audit(CANONICAL)
    assert result["verdict"] == "PASS"
    assert result["trade_ledgers_reconciled"] == 16
    assert result["total_trades"] == 1124


def mutate_json(path, callback):
    value = json.loads(path.read_text())
    callback(value)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def mutate_csv(path, callback):
    value = pd.read_csv(path)
    callback(value)
    value.to_csv(path, index=False)


def mutations():
    return [
        lambda root: mutate_json(root / RUN / "metrics.json", lambda x: x.__setitem__("PF", x["PF"] + 1)),
        lambda root: mutate_csv(root / RUN / "monthly_returns.csv", lambda x: x.loc.__setitem__((0, "net_R"), x.loc[0, "net_R"] + 1)),
        lambda root: mutate_csv(root / RUN / "yearly_report.csv", lambda x: x.loc.__setitem__((0, "expectancy_R"), x.loc[0, "expectancy_R"] + 1)),
        lambda root: mutate_csv(root / RUN / "direction_report.csv", lambda x: x.loc.__setitem__((0, "PF"), x.loc[0, "PF"] + 1)),
        lambda root: mutate_json(root / RUN / "manifest.json", lambda x: x.__setitem__("source_sha256", "0" * 64)),
        lambda root: mutate_json(root / RUN / "manifest.json", lambda x: x["baseline_parameters"].__setitem__("ema_fast", 21)),
        lambda root: mutate_json(root / RUN / "manifest.json", lambda x: x.__setitem__("true_oos_status", "READ")),
        lambda root: mutate_csv(root / "summary/baseline_matrix.csv", lambda x: x.loc.__setitem__((0, "net_R"), x.loc[0, "net_R"] + 1)),
        lambda root: mutate_csv(root / RUN / "monthly_returns.csv", lambda x: x.drop(index=0, inplace=True)),
        lambda root: mutate_csv(root / RUN / "trades.csv", lambda x: x.loc.__setitem__((0, "net_R"), x.loc[0, "net_R"] + 1)),
    ]


@pytest.mark.parametrize("mutation", mutations(), ids=[
    "metrics-pf", "monthly-net", "yearly-expectancy", "direction-pf", "source-hash",
    "baseline-parameter", "true-oos-status", "summary-metric", "missing-month", "trade-net"])
def test_audit_fails_closed_on_tampering(tmp_path, mutation):
    copied = tmp_path / "baseline"
    shutil.copytree(CANONICAL, copied)
    mutation(copied)
    with pytest.raises(AssertionError):
        audit(copied)
