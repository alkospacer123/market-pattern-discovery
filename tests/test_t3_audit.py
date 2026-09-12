import json
from pathlib import Path
import pandas as pd
from TradingSystemLab.audit_t3 import REQUIRED_OUTPUTS, generate_audit
BASELINE = Path(__file__).parents[1] / "TradingSystemLab" / "results" / "T3_baseline"
def test_t3_audit_reads_metrics_and_creates_all_reports(tmp_path):
    baseline=tmp_path/"T3_baseline"; baseline.mkdir()
    for name in ("trades.csv","metrics.json","equity_curve.csv"): (baseline/name).write_bytes((BASELINE/name).read_bytes())
    source=json.loads((baseline/"metrics.json").read_text()); assert source["trades"]==109
    audit=generate_audit(baseline); assert audit.is_dir(); assert all((audit/name).is_file() for name in REQUIRED_OUTPUTS)
    stats=json.loads((audit/"statistics.json").read_text()); assert stats["overall"]["trades"]==source["trades"]
    assert stats["audit_scope"]["true_oos_2025_read"] is False
    assert all(stats["audit_scope"]["source_metrics_reconciliation"].values())
    assert (audit/"equity_curve.svg").read_text().startswith("<svg")
    assert "base64" not in (audit/"equity_curve.svg").read_text()
    assert list(pd.read_csv(audit/"yearly_report.csv").columns)==["year","trades","net_profit","PF","winrate","average_R","max_DD"]
    assert list(pd.read_csv(audit/"monthly_returns.csv").columns)==["month","return_R","trades","drawdown"]
