"""Synthetic SQLite tests only: no FINAM/DPAPI and no live files touched."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "V20-08" / "v20-08-obv-settled-post-recovery.py"
spec = importlib.util.spec_from_file_location("v20_obv_incident_recovery", SCRIPT)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)

ACCOUNT = "a" * 64
ENTRY = "v20:obv:fake-entry"


def fixture(db: Path, *, initial_halt=recovery.MARKER, risk="PASS", stop="80.92") -> None:
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE state(key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        con.execute("CREATE TABLE intents(idempotency_key TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,broker_order_id TEXT)")
        identity = {"schema_id":"v20.h1_state_store.real_intents.v1",
                    "robot_id":"v20-obv","strategy":"OBV_PRESSURE","account_sha256":ACCOUNT,
                    "mode":"V20_PRETRADE_UNAUTHORIZED"}
        assessment = {"status":risk,"reason":None if risk=="PASS" else "ACTUAL_FILL_EXCEEDS_R15",
                      "filled_quantity":2,"projected_stop":"80.92",
                      "actual_risk":"616.68","entry_risk_cap":"674.83470",
                      "account_risk_cap":"2699.3388","stop_conforms":True}
        protected = {"account_sha256":ACCOUNT, "broker_order_id":"test-entry-ack",
                     "broker_stop_id":"test-stop-ack","filled_quantity":2,
                     "broker_stop_percent":"100","installed_stop":stop,
                     "risk_assessment":assessment}
        for key, val in [
            ("database_identity",identity),("execution_halt",initial_halt),
            ("protected_fill:"+ENTRY,protected),
            ("entry_submission:"+ENTRY,{"account_sha256":ACCOUNT, "submitted_at":"2026-10-27T07:30:02+00:00"})
        ]:
            con.execute("INSERT INTO state(key,value) VALUES (?,?)",(key,json.dumps(val)))
        entry={"kind":"ENTRY","robot_id":"v20-obv","account_sha256":ACCOUNT,"symbol":"USDRUBF",
               "direction":"SHORT","entry_at":"2026-10-27T10:30:00","quantity":2}
        stop_payload={"kind":"STOP","entry_key":ENTRY,"account_sha256":ACCOUNT}
        for key,payload,status,oid in [
            (ENTRY,entry,"RECONCILED","test-entry-ack"),
            (ENTRY+":stop",stop_payload,"ACK","test-stop-ack")
        ]:
            con.execute("INSERT INTO intents VALUES (?,?,?,?)",
                        (key,json.dumps(payload),status,oid))


def halt_value(db: Path) -> object:
    with sqlite3.connect(db) as con:
        return json.loads(con.execute("SELECT value FROM state WHERE key='execution_halt'").fetchone()[0])


class ObvSettledCheckpointTests(unittest.TestCase):
    def test_verify_does_not_change_state_and_resolve_changes_only_marker(self):
        with tempfile.TemporaryDirectory() as root:
            db=Path(root)/"state.sqlite3"
            fixture(db)
            with sqlite3.connect(db) as con:
                before=con.execute("SELECT key,value FROM state ORDER BY key").fetchall()
                old_intents=con.execute("SELECT * FROM intents ORDER BY idempotency_key").fetchall()
            recovery.recover_sqlite(db, False)
            with sqlite3.connect(db) as con:
                self.assertEqual(con.execute("SELECT key,value FROM state ORDER BY key").fetchall(),before)
            recovery.recover_sqlite(db, True)
            self.assertIsNone(halt_value(db))
            with sqlite3.connect(db) as con:
                after=con.execute("SELECT key,value FROM state ORDER BY key").fetchall()
                self.assertEqual({k:v for k,v in before if k!="execution_halt"},
                                 {k:v for k,v in after if k!="execution_halt"})
                self.assertEqual(con.execute("SELECT * FROM intents ORDER BY idempotency_key").fetchall(),old_intents)
            with self.assertRaisesRegex(recovery.RecoveryBlocked,"DURABLE_HALT_CHANGED"):
                recovery.recover_sqlite(db, True)

    def test_never_clear_actual_risk_halt_or_unproven_stop(self):
        for opts,reason in [
            ({"initial_halt":"ACTUAL_FILL_EXCEEDS_R15"},"DURABLE_HALT_CHANGED"),
            ({"risk":"HALT_NEW_ENTRIES"},"RISK_STOP_OR_QUANTITY_INVALID"),
            ({"stop":"80.93"},"BROKER_STOP_PROOF_MISMATCH")
        ]:
            with self.subTest(opts=opts), tempfile.TemporaryDirectory() as root:
                db=Path(root)/"s.sqlite3"
                fixture(db, **opts)
                before=halt_value(db)
                with self.assertRaisesRegex(recovery.RecoveryBlocked,reason):
                    recovery.recover_sqlite(db,True)
                self.assertEqual(halt_value(db),before)


if __name__=="__main__":
    unittest.main()
