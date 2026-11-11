"""M15 step14: append-only durable receipts of independently validated broker GET.

Stores sanitized, account-bound proof fingerprints, not executable orders,
trading authority, invented fills or raw FINAM/account/token data.
The caller must supply authenticated FINAM GET snapshots for one account.
No network, credential, H1 path access or synthetic->production adoption.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3

from .account_boundary import validate_independent_binding
from .broker_fill_readonly import ExpectedEntry
from .broker_reconcile_gate import assess_entry_evidence
from .spec import EXECUTION_STATUS, ROBOT_ID


class M15BrokerReceiptError(RuntimeError):
    pass


_TABLES = frozenset({"metadata", "entry_receipts"})
_SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entry_receipts(
    cycle INTEGER PRIMARY KEY,
    observed_utc TEXT NOT NULL UNIQUE,
    order_sha256 TEXT NOT NULL,
    fill_set_sha256 TEXT NOT NULL,
    matched_quantity INTEGER NOT NULL CHECK(matched_quantity>=0),
    broker_position_quantity INTEGER NOT NULL,
    quantity_status TEXT NOT NULL,
    protection_status TEXT NOT NULL,
    active_entry_orders INTEGER NOT NULL CHECK(active_entry_orders>=0),
    active_sltp_count INTEGER NOT NULL CHECK(active_sltp_count>=0),
    receipt_sha256 TEXT NOT NULL
);
"""
_COLUMNS = {
    "metadata": ("key", "value"),
    "entry_receipts": (
        "cycle", "observed_utc", "order_sha256", "fill_set_sha256",
        "matched_quantity", "broker_position_quantity", "quantity_status",
        "protection_status", "active_entry_orders", "active_sltp_count",
        "receipt_sha256",
    ),
}
_FILENAME = "m15-broker-get-receipts-readonly.sqlite3"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class M15ReadOnlyBrokerReceiptStore:
    """Separated SQLite with restart-stable, fail-closed receipt history.

    The database has NO intent, fill, stop or trading-authority tables.
    A receipt is an observation, NOT evidence that LIVE protection is ready.
    """

    def __init__(
        self, *, runtime_root: Path, h1_runtime_root: Path,
        repository_root: Path, m15_account_id: str,
        h1_account_sha256: str,
    ):
        if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED":
            raise M15BrokerReceiptError("M15_RECEIPT_UNEXPECTED_LIVE_AUTHORITY")
        fp = validate_independent_binding(
            m15_account_id=m15_account_id,
            h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root,
            h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        self.identity = {
            "robot": ROBOT_ID,
            "account_sha256": fp,
            "environment": "BROKER_GET_READONLY_RECEIPTS",
            "authority": "NOT_LIVE_AUTHORIZED",
        }
        root = runtime_root.resolve()
        if runtime_root.is_symlink() or (root / "state").is_symlink():
            raise M15BrokerReceiptError("M15_RECEIPT_PATH_SYMLINK_FORBIDDEN")
        self.path = root / "state" / _FILENAME
        if self.path.is_symlink():
            raise M15BrokerReceiptError("M15_RECEIPT_DB_SYMLINK_FORBIDDEN")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existed = self.path.exists()
        self._db = sqlite3.connect(self.path, timeout=3)
        try:
            self._db.execute("PRAGMA busy_timeout=3000")
            self._db.execute("PRAGMA foreign_keys=ON")
            with self._db:
                self._db.executescript(_SCHEMA)
                tables = {row[0] for row in self._db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )}
                if tables != _TABLES:
                    raise M15BrokerReceiptError("M15_RECEIPT_SCHEMA_TABLES_INVALID")
                for name, columns in _COLUMNS.items():
                    actual = tuple(
                        row[1] for row in self._db.execute(f"PRAGMA table_info({name})")
                    )
                    if actual != columns:
                        raise M15BrokerReceiptError("M15_RECEIPT_SCHEMA_COLUMNS_INVALID")
                row = self._db.execute(
                    "SELECT value FROM metadata WHERE key='identity'"
                ).fetchone()
                if row is None:
                    if existed:
                        raise M15BrokerReceiptError("M15_RECEIPT_EXISTING_IDENTITY_MISSING")
                    self._db.execute(
                        "INSERT INTO metadata(key,value) VALUES('identity',?)",
                        (json.dumps(self.identity, sort_keys=True),),
                    )
                else:
                    try:
                        identity = json.loads(row[0])
                    except (ValueError, TypeError):
                        identity = None
                    if identity != self.identity:
                        raise M15BrokerReceiptError("M15_RECEIPT_ACCOUNT_IDENTITY_MISMATCH")
                if self._db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise M15BrokerReceiptError("M15_RECEIPT_INTEGRITY_FAIL")
        except Exception:
            self._db.close()
            raise

    @property
    def execution_authorized(self) -> bool:
        return False

    def close(self) -> None:
        self._db.close()

    def latest(self) -> dict | None:
        row = self._db.execute(
            "SELECT cycle,observed_utc,order_sha256,fill_set_sha256,"
            "matched_quantity,broker_position_quantity,quantity_status,"
            "protection_status,active_entry_orders,active_sltp_count,"
            "receipt_sha256 FROM entry_receipts ORDER BY cycle DESC LIMIT 1"
        ).fetchone()
        return dict(zip(_COLUMNS["entry_receipts"], row)) if row else None

    def observe(
        self, *, observed_at: datetime, expected: ExpectedEntry,
        expected_client_order_id: str, stop_trade_tag: str,
        account: dict, orders_response: dict, trades_response: dict,
        start: str, end: str, limit: int = 1000,
    ) -> dict:
        if (not isinstance(observed_at, datetime)
                or observed_at.tzinfo is None or observed_at.utcoffset() is None):
            raise M15BrokerReceiptError("M15_RECEIPT_OBSERVATION_CLOCK_INVALID")
        if not isinstance(expected, ExpectedEntry):
            raise M15BrokerReceiptError("M15_RECEIPT_EXPECTED_ORDER_REQUIRED")
        if _hash(expected.account_id) != self.identity["account_sha256"]:
            raise M15BrokerReceiptError("M15_RECEIPT_ACCOUNT_BOUNDARY_MISMATCH")
        # Validation happens BEFORE a single SQLite receipt is written.
        evidence = assess_entry_evidence(
            account=account, orders_response=orders_response,
            trades_response=trades_response, expected=expected,
            expected_client_order_id=expected_client_order_id,
            stop_trade_tag=stop_trade_tag, start=start, end=end, limit=limit,
        )
        if evidence.sqlite_adoption_authorized or evidence.live_authorized:
            raise M15BrokerReceiptError("M15_RECEIPT_AUTHORITY_ESCALATION_REFUSED")
        stamp = observed_at.astimezone(timezone.utc).isoformat()
        safe = {
            "observed_utc": stamp,
            "order_sha256": _hash(expected.order_id),
            "fill_set_sha256": evidence.fill_set_sha256,
            "matched_quantity": evidence.matched_fill_quantity,
            "broker_position_quantity": evidence.broker_position_quantity,
            "quantity_status": evidence.quantity_status,
            "protection_status": evidence.protection_status,
            "active_entry_orders": evidence.active_entry_orders,
            "active_sltp_count": evidence.active_sltp_count,
        }
        digest = _hash(json.dumps(safe, sort_keys=True, separators=(",", ":")))
        try:
            with self._db:
                latest = self.latest()
                if latest is not None and stamp <= latest["observed_utc"]:
                    if stamp == latest["observed_utc"] and digest == latest["receipt_sha256"]:
                        return {"cycle": latest["cycle"], "receipt_sha256": digest,
                                "appended": False, "live_authorized": False}
                    raise M15BrokerReceiptError("M15_RECEIPT_STALE_OR_CONFLICTING_CYCLE")
                cycle = latest["cycle"] + 1 if latest is not None else 1
                self._db.execute(
                    "INSERT INTO entry_receipts("
                    "cycle,observed_utc,order_sha256,fill_set_sha256,"
                    "matched_quantity,broker_position_quantity,quantity_status,"
                    "protection_status,active_entry_orders,active_sltp_count,"
                    "receipt_sha256) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (cycle, *(safe[key] for key in _COLUMNS["entry_receipts"][1:-1]), digest),
                )
        except sqlite3.DatabaseError:
            raise M15BrokerReceiptError("M15_RECEIPT_SQLITE_FAULT") from None
        return {"cycle": cycle, "receipt_sha256": digest,
                "appended": True, "live_authorized": False}
