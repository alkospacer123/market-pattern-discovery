"""V20-06.4: offline summary of 06.1, 06.2, 06.3 READONLY receipts.

No FINAM API, token, account ID inputs, H1/M15/Windows Task access or
repeated broker observation. A PARTIAL money/cleanliness observation remains
PARTIAL; this never authorizes LIVE entry.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

BASE = Path(__file__).resolve().parents[1] / "readonly-06"
BINDING = BASE / "ACCOUNT_BINDING_REPORT.json"
SPEC = BASE / "N4_SPECIFICATIONS_REPORT.json"
STATE = BASE / "ACCOUNT_STATE_REPORT.json"
OUTPUT = BASE / "BROKER_READONLY_REPORT.json"
FUNDED_STATE = BASE / "ACCOUNT_STATE_REPORT_FUNDED.json"
FUNDED_OUTPUT = BASE / "BROKER_READONLY_REPORT_FUNDED.json"
ROBOTS = ("v20-shallow", "v20-obv", "v20-inside")
N4 = ("USDRUBF", "CNYRUBF", "GLDRUBF", "IMOEXF")
COMPLETE = "BOUNDED_3_DAYS_COMPLETE_BY_LIMIT_AND_CURSOR"


def require(ok, reason):
    if not ok:
        raise RuntimeError("V20_06_4_" + reason)


def read(path):
    require(path.is_file(), "RECEIPT_MISSING")
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "RECEIPT_SCHEMA_INVALID")
    return data


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accounts(source, label):
    rows = source.get("accounts")
    require(isinstance(rows, list) and len(rows) == 3, label + "_COUNT_INVALID")
    require(all(isinstance(x, dict) and x.get("robot") in ROBOTS for x in rows),
            label + "_ROBOTS_INVALID")
    indexed = {x["robot"]: x for x in rows}
    require(len(indexed) == 3, label + "_DUPLICATE_ROBOTS")
    return indexed


def summarize(funded=False):
    state_path = FUNDED_STATE if funded else STATE
    output_path = FUNDED_OUTPUT if funded else OUTPUT
    require(not output_path.exists(), "REPORT_ALREADY_EXISTS_NO_OVERWRITE")
    if funded:
        require(OUTPUT.is_file() and STATE.is_file(), "BASELINE_MISSING")
    binding, spec, state = read(BINDING), read(SPEC), read(state_path)
    if funded:
        require(state.get("prior_06_3_report_sha256") == sha256(STATE),
                "FUNDED_BASELINE_HASH_MISMATCH")
    require(binding.get("status") == "PASS_3_OF_3"
            and binding.get("readonly_token_scope") == "ONE_SHARED_TOKEN_THREE_DISTINCT_ACCOUNTS",
            "BINDING_06_1_NOT_PASS")
    binding_rows = binding.get("results")
    require(isinstance(binding_rows, list) and len(binding_rows) == 3,
            "BINDING_RESULTS_INVALID")
    bound = {}
    for item in binding_rows:
        require(isinstance(item, dict) and item.get("robot") in ROBOTS
                and item.get("status") == "PASS_READONLY"
                and re.fullmatch(r"[0-9a-f]{64}", str(item.get("account_sha256", ""))) is not None,
                "BINDING_ROW_INVALID")
        require(item["robot"] not in bound, "BINDING_DUPLICATE")
        bound[item["robot"]] = item["account_sha256"]
    require(len(set(bound.values())) == 3, "BINDING_ACCOUNTS_NOT_INDEPENDENT")
    require(spec.get("schema") == "v20.n4.readonly_specifications.v1"
            and spec.get("status") == "PASS_READONLY_3_ACCOUNTS_4_N4_WITH_SLTP_EXECUTION_DEFERRED"
            and spec.get("06_1_receipt_sha256") == sha256(BINDING)
            and spec.get("new_orders") == 0 and spec.get("cancellations") == 0
            and spec.get("trading_authorized") is False,
            "SPEC_06_2_NOT_PASS")
    require(state.get("schema") == "v20.finam.readonly_account_state.v1"
            and state.get("source_06_2_report_sha256") == sha256(SPEC)
            and state.get("mode") == "READONLY"
            and state.get("new_orders") == 0 and state.get("cancellations") == 0
            and state.get("live_authorized") is False
            and state.get("status") in ("PASS_READONLY_3_OF_3",
                                        "PARTIAL_ACCOUNT_MONEY_OR_CLEANLINESS"),
            "STATE_06_3_INVALID")
    specs, states = accounts(spec, "SPECS"), accounts(state, "STATE")
    summary = []
    for robot in ROBOTS:
        a, b = specs[robot], states[robot]
        require(a.get("account_sha256") == b.get("account_sha256") == bound[robot]
                and a.get("status") == "PASS_4_OF_4"
                and isinstance(a.get("specifications"), dict)
                and set(a["specifications"]) == set(N4),
                "ACCOUNT_N4_IDENTITY_INVALID")
        require(b.get("broker_state_observation") == "PASS"
                and b.get("entry_ready") is False
                and b.get("risk_sized_entry_contracts") ==
                    "BLOCKED_UNTIL_SIGNAL_ENTRY_ATR_GRID_AND_COST",
                "STATE_EVIDENCE_INVALID")
        money, history = b.get("money"), b.get("history")
        require(isinstance(money, dict) and isinstance(history, dict)
                and money.get("status") in ("PASS", "BLOCKED")
                and history.get("coverage") == COMPLETE,
                "MONEY_OR_HISTORY_SCHEMA_INVALID")
        clean = b.get("account_clean")
        positions, orders = b.get("positions_nonzero"), b.get("active_orders")
        require(type(clean) is bool and type(positions) is int and positions >= 0
                and type(orders) is int and orders >= 0
                and clean == (positions == 0 and orders == 0),
                "CLEANLINESS_INCONSISTENT")
        reason = money.get("reason") if money["status"] == "BLOCKED" else None
        if reason is not None:
            require(isinstance(reason, str)
                    and re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,100}", reason) is not None,
                    "MONEY_REASON_INVALID")
        result = ("PASS_READONLY" if clean and money["status"] == "PASS"
                  else "PARTIAL_READONLY")
        summary.append({
            "robot": robot,
            "account_sha256": bound[robot],
            "n4_specifications": "PASS_4_OF_4",
            "money_status": money["status"],
            "money_block_reason": reason,
            "account_status": b.get("account_status"),
            "positions_nonzero": positions,
            "active_orders": orders,
            "account_clean": clean,
            "history_three_days": history.get("coverage"),
            "history_trades_count": history.get("trades"),
            "entry_risk_sized_quantity": "NOT_AUTHORIZED_NO_SIGNAL_OR_LIVE_LEDGER",
            "readonly_result": result,
        })
        print("V20_06_4_" + robot + "=" + result +
              " MONEY=" + money["status"] +
              " REASON=" + (reason or "NONE") +
              " POSITIONS=" + str(positions) +
              " ACTIVE_ORDERS=" + str(orders))
    successful = all(x["readonly_result"] == "PASS_READONLY" for x in summary)
    require(successful == (state["status"] == "PASS_READONLY_3_OF_3"),
            "STATE_AGGREGATE_MISMATCH")
    overall = "PASS_READONLY_3_OF_3" if successful else "PARTIAL_MONEY_OR_CLEANLINESS"
    report = {
        "schema": "v20.finam.broker_readonly_report.v1",
        "sources_sha256": {
            "06_1": sha256(BINDING), "06_2": sha256(SPEC), "06_3": sha256(state_path),
        },
        "source_observed_at_utc": state.get("observed_at_utc"),
        "status": overall,
        "stage_06_status": "PASS" if successful else "PARTIAL_NOT_CLOSED",
        "entry_authorized": False,
        "real_orders_sent_by_diagnostics": 0,
        "account_ids": "NOT_PERSISTED_PLAINTEXT; SHA256_RECEIPT_IDENTITIES_ONLY",
        "actual_sltp_execution_verified": False,
        "m15_open_label_authority_verified": False,
        "live_equity_ledger_reconciled": False,
        "accounts": summary,
        "operator_next": "FUNDING_OR_CLEANLINESS_RESOLUTION" if not successful
                         else "06_4_REPORT_READY_FOR_OPERATOR_REVIEW",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("V20_06_4_REPORT_GENERATED=PASS")
    print("V20_06_OVERALL=" + overall)
    print("V20_06_4_REPORT=" + str(output_path))
    return 0


if __name__ == "__main__":
    try:
        if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != "--funded"):
            raise RuntimeError("V20_06_4_UNSUPPORTED_ARGS")
        raise SystemExit(summarize(funded=len(sys.argv) == 2))
    except Exception as exc:
        message = str(exc)
        reason = (message if type(exc) is RuntimeError and
                  re.fullmatch(r"V20_06_4_[A-Z0-9_]{1,100}", message)
                  else type(exc).__name__)
        print("V20_06_4_FAIL=" + reason, file=sys.stderr)
        raise SystemExit(1)
