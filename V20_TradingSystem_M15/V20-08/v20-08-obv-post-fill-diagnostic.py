"""OBV incident, 27 Oct 2026: local SQLite read-only diagnostic.
No FINAM network/API, no orders, no token/DPAPI reads, no state changes.
Prints neither account identifiers/hashes nor broker order/trade IDs.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3

DB = Path(r"C:\V20Lab\robots\obv\state\v20-real-intents.sqlite3")

def main() -> int:
    if os.name != "nt" or os.environ.get("COMPUTERNAME", "").upper() != "URIU-PC":
        raise RuntimeError("V20_OBV_DIAGNOSTIC_WRONG_INTEL")
    if not DB.is_file() or DB.is_symlink() or DB.parent.is_symlink():
        raise RuntimeError("V20_OBV_DIAGNOSTIC_DB_INVALID")
    print("v20_obv_readonly_sqlite_open=YES")
    with sqlite3.connect(DB.as_uri() + "?mode=ro", uri=True, timeout=3) as conn:
        conn.execute("PRAGMA query_only=ON")
        identity_row = conn.execute("SELECT value FROM state WHERE key='database_identity'").fetchone()
        if not identity_row:
            raise RuntimeError("V20_OBV_IDENTITY_MISSING")
        identity = json.loads(identity_row[0])
        if identity.get("robot_id") != "v20-obv" or identity.get("strategy") != "OBV_PRESSURE" or identity.get("schema_id") != "v20.h1_state_store.real_intents.v1":
            raise RuntimeError("V20_OBV_IDENTITY_MISMATCH")
        print("v20_obv_sqlite_identity=PASS_OBV_NO_SECRET_OUTPUT")
        halt = conn.execute("SELECT value FROM state WHERE key='execution_halt'").fetchone()
        value = json.loads(halt[0]) if halt else None
        print("v20_obv_durable_execution_halt=" + str(value))
        intents = conn.execute("SELECT payload,status FROM intents ORDER BY updated_at").fetchall()
        print("v20_obv_total_intents=" + str(len(intents)))
        by_status: dict[str, int] = {}
        for raw, status in intents:
            record = json.loads(raw)
            kind = record.get("kind", "UNKNOWN")
            by_status[str(kind) + ":" + str(status)] = by_status.get(str(kind) + ":" + str(status), 0) + 1
            if kind == "ENTRY":
                print("v20_obv_entry=" + " symbol=" + str(record.get("symbol")) +
                      " direction=" + str(record.get("direction")) +
                      " qty=" + str(record.get("quantity")) + " status=" + str(status) +
                      " entry_at=" + str(record.get("entry_at")))
        for name, count in sorted(by_status.items()):
            print("v20_obv_intent_count_" + name.replace(":", "_") + "=" + str(count))
        rows = conn.execute("SELECT value FROM state WHERE key LIKE 'protected_fill:%'").fetchall()
        print("v20_obv_protected_fill_records=" + str(len(rows)))
        for index, (encoded,) in enumerate(rows, 1):
            obs = json.loads(encoded)
            assessment = obs.get("risk_assessment") or {}
            print("v20_obv_protected_" + str(index) + "_filled_quantity=" + str(obs.get("filled_quantity")))
            print("v20_obv_protected_" + str(index) + "_observed_stop=" + str(obs.get("installed_stop")))
            print("v20_obv_protected_" + str(index) + "_stop_100_percent=" + str(obs.get("broker_stop_percent")))
            for field in ("status", "reason", "actual_risk", "entry_risk_cap",
                          "account_risk_cap", "stop_conforms", "projected_stop",
                          "average_price", "filled_quantity"):
                print("v20_obv_risk_" + str(index) + "_" + field + "=" + str(assessment.get(field)))
        print("v20_obv_sqlite_readonly_diagnostic=PASS_NO_MUTATION_NO_FINAM")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
