"""Three real-shaped V20 frozen-position checkpoint recovery cases. Offline only."""
from __future__ import annotations
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from V20_TradingSystem_M15.v20_runtime.tests.test_obv_settled_post_recovery import fixture, halt_value

SCRIPT = Path(__file__).resolve().parents[2] / "V20-08" / "v20-08-three-protected-post-recovery.py"
spec = importlib.util.spec_from_file_location("v20_three_position_checkpoint_recovery", SCRIPT)
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


def adapt(db: Path, name: str) -> None:
    strategy, symbol, side, when, quantity, stop = recovery.CASES[name]
    with closing(sqlite3.connect(db)) as conn, conn:
        identity = json.loads(conn.execute(
            "SELECT value FROM state WHERE key='database_identity'").fetchone()[0])
        identity.update(robot_id=name, strategy=strategy)
        conn.execute("UPDATE state SET value=? WHERE key='database_identity'",
                     (json.dumps(identity),))
        entry = conn.execute("SELECT idempotency_key,payload FROM intents WHERE status='RECONCILED'").fetchone()
        key, encoded = entry
        payload = json.loads(encoded)
        payload.update(robot_id=name,symbol=symbol,direction=side,
                       entry_at=when,quantity=quantity)
        conn.execute("UPDATE intents SET payload=? WHERE idempotency_key=?",
                     (json.dumps(payload),key))
        proof = json.loads(conn.execute("SELECT value FROM state WHERE key=?",
                                       ("protected_fill:"+key,)).fetchone()[0])
        proof.update(filled_quantity=quantity, installed_stop=str(stop))
        assessment = proof["risk_assessment"]
        assessment.update(filled_quantity=quantity, projected_stop=str(stop))
        conn.execute("UPDATE state SET value=? WHERE key=?",
                     (json.dumps(proof),"protected_fill:"+key))


class ThreeProtectedCheckpointTests(unittest.TestCase):
    def test_all_three_recover_only_verified_resolved_checkpoint(self):
        for robot in recovery.CASES:
            with self.subTest(robot=robot), TemporaryDirectory() as td:
                recovery.select_robot(robot)
                db = Path(td) / "test.sqlite3"
                fixture(db)
                adapt(db,robot)
                with closing(sqlite3.connect(db)) as conn:
                    original = conn.execute("SELECT key,value FROM state ORDER BY key").fetchall()
                    entries = conn.execute("SELECT * FROM intents").fetchall()
                recovery.recover_sqlite(db,False)
                self.assertEqual(halt_value(db),recovery.MARKER)
                recovery.recover_sqlite(db,True)
                self.assertIsNone(halt_value(db))
                with closing(sqlite3.connect(db)) as conn:
                    latest = conn.execute("SELECT key,value FROM state ORDER BY key").fetchall()
                    self.assertEqual({k:v for k,v in original if k!='execution_halt'},
                                     {k:v for k,v in latest if k!='execution_halt'})
                    self.assertEqual(entries,conn.execute("SELECT * FROM intents").fetchall())

    def test_all_three_reject_unknown_risk_or_missing_stop(self):
        for robot in recovery.CASES:
            with self.subTest(robot=robot), TemporaryDirectory() as td:
                recovery.select_robot(robot)
                db=Path(td)/"test.sqlite3"
                fixture(db,initial_halt="ACTUAL_FILL_EXCEEDS_R15")
                adapt(db,robot)
                with self.assertRaisesRegex(recovery.RecoveryBlocked,"DURABLE_HALT_CHANGED"):
                    recovery.recover_sqlite(db,True)
                self.assertEqual(halt_value(db),"ACTUAL_FILL_EXCEEDS_R15")


if __name__ == "__main__":
    unittest.main()
