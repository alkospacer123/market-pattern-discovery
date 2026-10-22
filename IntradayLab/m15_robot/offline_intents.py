"""Isolated, order-incapable M15 rehearsal ledger: H1 durable intent model.

No FINAM API, token, order transport or re-arm method is imported. The ledger
accepts SYNTHETIC order/fill/stop receipts in tests, never claims real broker
authority. Reuse the H1 invariants: persist-before-POST, single idempotency key,
no uncertain retries, partial fill reconciliation, and 100% position SLTP
with tightening-first protective updates.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .account_boundary import validate_independent_binding
from .spec import INSTRUMENTS, ROBOT_ID, EXECUTION_STATUS

FILENAME = "m15-offline-intents.sqlite3"
KEY_FORMAT = re.compile(r"^m15:[A-Za-z0-9._:-]{1,123}$")
EXPECTED_COLUMNS = {
    "metadata": ("key", "value"),
    "intents": ("intent_key", "instrument", "direction", "planned_quantity",
                "status", "broker_order_id", "payload_sha256"),
    "fills": ("fill_id", "intent_key", "broker_order_id", "quantity", "price"),
    "protection": ("intent_key", "revision", "broker_order_id", "stop_price", "quantity_percent"),
}
SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE intents(
    intent_key TEXT PRIMARY KEY,
    instrument TEXT NOT NULL,
    direction TEXT NOT NULL,
    planned_quantity INTEGER NOT NULL CHECK(planned_quantity>0),
    status TEXT NOT NULL,
    broker_order_id TEXT,
    payload_sha256 TEXT NOT NULL
);
CREATE TABLE fills(
    fill_id TEXT PRIMARY KEY, intent_key TEXT NOT NULL,
    broker_order_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity>0), price TEXT NOT NULL,
    FOREIGN KEY(intent_key) REFERENCES intents(intent_key)
);
CREATE TABLE protection(
    intent_key TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision>=0),
    broker_order_id TEXT NOT NULL UNIQUE, stop_price TEXT NOT NULL,
    quantity_percent INTEGER NOT NULL CHECK(quantity_percent=100),
    PRIMARY KEY(intent_key,revision),
    FOREIGN KEY(intent_key) REFERENCES intents(intent_key)
);
"""
OPEN_STATES = frozenset(("PREPARED", "UNCERTAIN", "ACK", "PARTIAL_FILL", "FILLED"))
FINISHED_STATES = frozenset(("REJECTED", "CANCELLED", "CLOSED"))


class M15OfflineLedgerError(RuntimeError):
    pass


def _price(value) -> Decimal:
    try:
        d = Decimal(str(value))
    except (ValueError, InvalidOperation):
        raise M15OfflineLedgerError("M15_EXECUTION_PRICE_INVALID") from None
    if not d.is_finite() or d <= 0:
        raise M15OfflineLedgerError("M15_EXECUTION_PRICE_INVALID")
    return d


def _digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()).hexdigest()


class OfflineIntentLedger:
    """Durable synthetic transition proofs. No real order authority, ever."""

    def __init__(
        self, *, runtime_root: Path, h1_runtime_root: Path,
        repository_root: Path, m15_account_id: str, h1_account_sha256: str,
    ):
        account_hash = validate_independent_binding(
            m15_account_id=m15_account_id, h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        self.identity = {
            "robot": ROBOT_ID, "broker": "SYNTHETIC_ONLY",
            "account_sha256": account_hash, "environment": "M15_OFFLINE_REHEARSAL",
            "authorization": EXECUTION_STATUS,
        }
        self.path = runtime_root.resolve() / "state" / FILENAME
        if self.path.is_symlink():
            raise M15OfflineLedgerError("M15_LEDGER_SYMLINK_FORBIDDEN")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existed_before_open = self.path.exists()
        self.db = sqlite3.connect(self.path)
        self.db.execute("PRAGMA foreign_keys=ON")
        try:
            with self.db:
                self.db.executescript(SCHEMA.replace("CREATE TABLE ", "CREATE TABLE IF NOT EXISTS "))
                objects = {r[0] for r in self.db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                if objects != set(EXPECTED_COLUMNS):
                    raise M15OfflineLedgerError("M15_LEDGER_SCHEMA_INVALID")
                for name, expected in EXPECTED_COLUMNS.items():
                    current = tuple(row[1] for row in self.db.execute(f"PRAGMA table_info({name})"))
                    if current != expected:
                        raise M15OfflineLedgerError("M15_LEDGER_COLUMNS_INVALID")
                present = self.db.execute("SELECT value FROM metadata WHERE key='identity'").fetchone()
                if present is None:
                    # Lost identity in an existing store is NEVER reset/rebound,
                    # including a store with zero intents (H1 authority pattern).
                    if existed_before_open:
                        raise M15OfflineLedgerError("M15_LEDGER_EXISTING_IDENTITY_MISSING")
                    if any(self.db.execute(f"SELECT EXISTS(SELECT 1 FROM {table})").fetchone()[0]
                           for table in ("intents", "fills", "protection")):
                        raise M15OfflineLedgerError("M15_LEDGER_IDENTITY_MISSING")
                    self.db.execute(
                        "INSERT INTO metadata(key,value) VALUES('identity',?)",
                        (json.dumps(self.identity, sort_keys=True),),
                    )
                elif json.loads(present[0]) != self.identity:
                    raise M15OfflineLedgerError("M15_LEDGER_ACCOUNT_IDENTITY_MISMATCH")
                if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise M15OfflineLedgerError("M15_LEDGER_INTEGRITY_INVALID")
        except Exception:
            self.db.close()
            raise

    @property
    def execution_authorized(self) -> bool:
        return False

    def close(self) -> None:
        self.db.close()

    def intent(self, key: str) -> dict | None:
        row = self.db.execute(
            "SELECT instrument,direction,planned_quantity,status,broker_order_id,payload_sha256 "
            "FROM intents WHERE intent_key=?", (key,)
        ).fetchone()
        return None if row is None else dict(zip((
            "instrument", "direction", "planned_quantity", "status", "broker_order_id", "payload_sha256",
        ), row))

    def prepare(self, *, key: str, instrument: str, direction: str, quantity: int) -> bool:
        if (
            not isinstance(key, str) or KEY_FORMAT.fullmatch(key) is None
            or instrument not in INSTRUMENTS or direction not in ("LONG", "SHORT")
            or type(quantity) is not int or quantity <= 0
        ):
            raise M15OfflineLedgerError("M15_INTENT_INVALID")
        payload = {"robot": ROBOT_ID, "key": key, "instrument": instrument,
                   "direction": direction, "quantity": quantity}
        digest = _digest(payload)
        with self.db:
            existing = self.intent(key)
            if existing is not None:
                if existing["payload_sha256"] != digest:
                    raise M15OfflineLedgerError("M15_IDEMPOTENCY_KEY_CONFLICT")
                return False  # Same intent, no new synthetic submission.
            # One position / instrument, no synthetic pyramiding.
            occupied = self.db.execute(
                "SELECT intent_key FROM intents WHERE instrument=? "
                "AND status NOT IN ('REJECTED','CANCELLED','CLOSED') LIMIT 1",
                (instrument,)
            ).fetchone()
            if occupied:
                raise M15OfflineLedgerError("M15_INSTRUMENT_ALREADY_OCCUPIED")
            self.db.execute(
                "INSERT INTO intents VALUES(?,?,?,?,?,?,?)",
                (key, instrument, direction, quantity, "PREPARED", None, digest),
            )
        return True

    def uncertain(self, key: str) -> None:
        # In real H1, POST uncertainty requires broker proof, NEVER retry.
        with self.db:
            cur = self.db.execute(
                "UPDATE intents SET status='UNCERTAIN' "
                "WHERE intent_key=? AND status='PREPARED'", (key,)
            )
            if cur.rowcount != 1:
                raise M15OfflineLedgerError("M15_UNCERTAIN_TRANSITION_DENIED")

    def synthetic_ack(self, key: str, synthetic_broker_order_id: str) -> None:
        if not isinstance(synthetic_broker_order_id, str) or not synthetic_broker_order_id.startswith("sim-"):
            raise M15OfflineLedgerError("M15_SYNTHETIC_BROKER_ACK_REQUIRED")
        with self.db:
            current = self.intent(key)
            if current is None or current["status"] not in ("PREPARED", "UNCERTAIN"):
                raise M15OfflineLedgerError("M15_ACK_TRANSITION_DENIED")
            if self.db.execute("SELECT 1 FROM intents WHERE broker_order_id=? AND intent_key!=?",
                               (synthetic_broker_order_id, key)).fetchone():
                raise M15OfflineLedgerError("M15_ORDER_ID_REUSE")
            self.db.execute(
                "UPDATE intents SET status='ACK',broker_order_id=? WHERE intent_key=?",
                (synthetic_broker_order_id, key)
            )

    def synthetic_fill(
        self, *, key: str, fill_id: str, broker_order_id: str,
        quantity: int, price,
    ) -> bool:
        if not isinstance(fill_id, str) or not fill_id.startswith("sim-fill-"):
            raise M15OfflineLedgerError("M15_SYNTHETIC_FILL_ID_REQUIRED")
        if type(quantity) is not int or quantity <= 0:
            raise M15OfflineLedgerError("M15_FILL_QUANTITY_INVALID")
        value = str(_price(price))
        with self.db:
            previous = self.db.execute(
                "SELECT intent_key,broker_order_id,quantity,price FROM fills WHERE fill_id=?",
                (fill_id,)
            ).fetchone()
            receipt = (key, broker_order_id, quantity, value)
            if previous is not None:
                if previous != receipt:
                    raise M15OfflineLedgerError("M15_CONFLICTING_DURABLE_FILL")
                return False
            info = self.intent(key)
            if (info is None or info["status"] not in ("ACK", "PARTIAL_FILL")
                    or info["broker_order_id"] != broker_order_id):
                raise M15OfflineLedgerError("M15_FILL_BROKER_PROOF_MISMATCH")
            filled = self.filled_quantity(key)
            if filled + quantity > info["planned_quantity"]:
                raise M15OfflineLedgerError("M15_OVERFILL_REFUSED")
            self.db.execute(
                "INSERT INTO fills VALUES(?,?,?,?,?)",
                (fill_id, key, broker_order_id, quantity, value)
            )
            self.db.execute(
                "UPDATE intents SET status=? WHERE intent_key=?",
                ("FILLED" if filled + quantity == info["planned_quantity"] else "PARTIAL_FILL", key)
            )
        return True

    def filled_quantity(self, key: str) -> int:
        row = self.db.execute("SELECT COALESCE(SUM(quantity),0) FROM fills WHERE intent_key=?", (key,)).fetchone()
        return int(row[0])

    def synthetic_vwap(self, key: str) -> Decimal:
        rows = self.db.execute("SELECT quantity,price FROM fills WHERE intent_key=?", (key,)).fetchall()
        if not rows:
            raise M15OfflineLedgerError("M15_NO_EXECUTION_PRICE")
        total = sum((Decimal(price) * qty for qty, price in rows), Decimal("0"))
        return total / sum(qty for qty, _ in rows)

    def synthetic_stop_ack(self, *, key: str, stop_price, synthetic_order_id: str) -> int:
        if not isinstance(synthetic_order_id, str) or not synthetic_order_id.startswith("sim-stop-"):
            raise M15OfflineLedgerError("M15_SYNTHETIC_STOP_ACK_REQUIRED")
        stop = _price(stop_price)
        with self.db:
            info = self.intent(key)
            if info is None or info["status"] not in ("PARTIAL_FILL", "FILLED") or self.filled_quantity(key) <= 0:
                raise M15OfflineLedgerError("M15_PROTECTION_WITHOUT_FILL")
            entry = self.synthetic_vwap(key)
            if info["direction"] == "LONG" and stop >= entry:
                # This rehearsal is initial-stop only; tightening past entry
                # requires the later verified trailing state machine.
                if not self.db.execute("SELECT 1 FROM protection WHERE intent_key=?", (key,)).fetchone():
                    raise M15OfflineLedgerError("M15_INITIAL_STOP_WRONG_SIDE")
            if info["direction"] == "SHORT" and stop <= entry:
                if not self.db.execute("SELECT 1 FROM protection WHERE intent_key=?", (key,)).fetchone():
                    raise M15OfflineLedgerError("M15_INITIAL_STOP_WRONG_SIDE")
            last = self.db.execute(
                "SELECT revision,stop_price FROM protection WHERE intent_key=? "
                "ORDER BY revision DESC LIMIT 1", (key,)
            ).fetchone()
            if last is not None:
                previous = Decimal(last[1])
                if not (stop > previous if info["direction"] == "LONG" else stop < previous):
                    raise M15OfflineLedgerError("M15_STOP_NOT_TIGHTER")
            if self.db.execute("SELECT 1 FROM protection WHERE broker_order_id=?", (synthetic_order_id,)).fetchone():
                raise M15OfflineLedgerError("M15_STOP_ID_REUSE")
            revision = (last[0] + 1) if last is not None else 0
            # The FINAM SLTP semantics reused from H1 always use 100% of position.
            self.db.execute(
                "INSERT INTO protection VALUES(?,?,?,?,?)",
                (key, revision, synthetic_order_id, str(stop), 100)
            )
            return revision

    def latest_stop(self, key: str) -> dict | None:
        row = self.db.execute(
            "SELECT revision,broker_order_id,stop_price,quantity_percent "
            "FROM protection WHERE intent_key=? ORDER BY revision DESC LIMIT 1", (key,)
        ).fetchone()
        return None if row is None else dict(
            zip(("revision", "broker_order_id", "stop_price", "quantity_percent"), row)
        )

    def unsafe_for_live(self) -> bool:
        # A synthetic ACK/stop is never broker evidence, and this package has
        # no real transport, authorization, or task/start controls.
        return True
