"""M15 №14: durable, account-bound FINAM GET fill checkpoint (NO trading authority).

Persists only sanitized, independently cross-checked entry fill facts. It is
NOT the trading position ledger: a checkpoint cannot recover LIVE positions,
prove SLTP ACK or authorize any broker request without a fresh GET cycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sqlite3

from .account_boundary import validate_independent_binding
from .broker_fill_readonly import ExpectedEntry, analyze_account_trades
from .broker_reconcile_gate import assess_entry_evidence
from .spec import EXECUTION_STATUS, ROBOT_ID


class M15FillCheckpointError(RuntimeError):
    pass


_DB_NAME = "m15-broker-fills-get-checkpoint.sqlite3"
_SCHEMA = """
CREATE TABLE IF NOT EXISTS identity(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints(
    order_sha256 TEXT NOT NULL,
    sequence INTEGER NOT NULL CHECK(sequence>0),
    observed_utc TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    expected_quantity INTEGER NOT NULL CHECK(expected_quantity>0),
    filled_quantity INTEGER NOT NULL CHECK(filled_quantity>0),
    broker_position_quantity INTEGER NOT NULL,
    fill_set_sha256 TEXT NOT NULL,
    vwap_numerator TEXT NOT NULL,
    vwap_denominator TEXT NOT NULL,
    protection_status TEXT NOT NULL,
    PRIMARY KEY(order_sha256,sequence)
);
"""
_COLUMNS = {
    "identity": ("key", "value"),
    "checkpoints": ("order_sha256", "sequence", "observed_utc", "symbol", "side",
                    "expected_quantity", "filled_quantity", "broker_position_quantity",
                    "fill_set_sha256", "vwap_numerator", "vwap_denominator",
                    "protection_status"),
}


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class M15FillCheckpoint:
    order_sha256: str
    filled_quantity: int
    exact_vwap: Fraction
    fill_set_sha256: str
    sequence: int
    newly_appended: bool
    protection_status: str
    # Persisted facts are NEVER a broker order ACK or recoverable trading state.
    broker_snapshot_freshness_proven: bool = False
    sqlite_trading_adoption_authorized: bool = False
    broker_stop_acknowledged: bool = False
    order_submission_authorized: bool = False
    live_authorized: bool = False


class M15BrokerFillCheckpointStore:
    """Separate M15-only GET checkpoint; no H1/FINAM/orders/production ledger."""

    def __init__(self, *, runtime_root: Path, h1_runtime_root: Path,
                 repository_root: Path, m15_account_id: str,
                 h1_account_sha256: str):
        if EXECUTION_STATUS != "NOT_LIVE_AUTHORIZED":
            raise M15FillCheckpointError("M15_CHECKPOINT_LIVE_STATUS_FORBIDDEN")
        fingerprint = validate_independent_binding(
            m15_account_id=m15_account_id, h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        root = runtime_root.resolve()
        if runtime_root.is_symlink() or (root / "state").is_symlink():
            raise M15FillCheckpointError("M15_CHECKPOINT_SYMLINK_FORBIDDEN")
        self.path = root / "state" / _DB_NAME
        if self.path.is_symlink():
            raise M15FillCheckpointError("M15_CHECKPOINT_DB_SYMLINK_FORBIDDEN")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists()
        self.account_sha256 = fingerprint
        self._identity = {"robot": ROBOT_ID, "account_sha256": fingerprint,
                          "purpose": "M15_GET_FILL_CHECKPOINT_ONLY",
                          "authorization": "NOT_LIVE_AUTHORIZED"}
        self.db = sqlite3.connect(self.path, timeout=3)
        try:
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA busy_timeout=3000")
            with self.db:
                self.db.executescript(_SCHEMA)
                tables = {row[0] for row in self.db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if tables != set(_COLUMNS):
                    raise M15FillCheckpointError("M15_CHECKPOINT_TABLE_SCHEMA_INVALID")
                for name, columns in _COLUMNS.items():
                    found = tuple(row[1] for row in self.db.execute(
                        f"PRAGMA table_info({name})"))
                    if found != columns:
                        raise M15FillCheckpointError("M15_CHECKPOINT_COLUMNS_INVALID")
                row = self.db.execute(
                    "SELECT value FROM identity WHERE key='binding'").fetchone()
                if row is None:
                    if exists:
                        raise M15FillCheckpointError("M15_CHECKPOINT_EXISTING_BINDING_MISSING")
                    self.db.execute("INSERT INTO identity(key,value) VALUES('binding',?)",
                                    (json.dumps(self._identity, sort_keys=True),))
                else:
                    try:
                        stored = json.loads(row[0])
                    except (ValueError, TypeError):
                        stored = None
                    if stored != self._identity:
                        raise M15FillCheckpointError("M15_CHECKPOINT_ACCOUNT_BINDING_MISMATCH")
                if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise M15FillCheckpointError("M15_CHECKPOINT_INTEGRITY_INVALID")
        except Exception:
            self.db.close()
            raise

    @property
    def execution_authorized(self) -> bool:
        return False

    def close(self) -> None:
        self.db.close()

    def observe(self, *, observed_at: datetime, expected: ExpectedEntry,
                expected_client_order_id: str, stop_trade_tag: str,
                account: dict, orders_response: dict, trades_response: dict,
                start: str, end: str, limit: int = 1000) -> M15FillCheckpoint:
        if (not isinstance(observed_at, datetime) or observed_at.tzinfo is None
                or observed_at.utcoffset() is None):
            raise M15FillCheckpointError("M15_CHECKPOINT_CLOCK_UNPROVEN")
        if (not isinstance(expected, ExpectedEntry)
                or _sha(expected.account_id) != self.account_sha256):
            raise M15FillCheckpointError("M15_CHECKPOINT_DIFFERENT_ACCOUNT")
        # Two independent parsing paths must agree BEFORE writing one row.
        evidence = assess_entry_evidence(
            account=account, orders_response=orders_response,
            trades_response=trades_response, expected=expected,
            expected_client_order_id=expected_client_order_id,
            stop_trade_tag=stop_trade_tag, start=start, end=end, limit=limit,
        )
        fills = analyze_account_trades(
            trades_response, expected, start=start, end=end, limit=limit,
        )
        quantity = evidence.matched_fill_quantity
        if (quantity <= 0 or evidence.broker_position_quantity !=
                (quantity if expected.side == "SIDE_BUY" else -quantity)
                or quantity != fills["matched_quantity"]
                or evidence.fill_set_sha256 != fills["fill_set_sha256"]
                or not fills["verified_fill"]
                or fills["weighted_price_exact"] is None
                or evidence.sqlite_adoption_authorized or evidence.live_authorized
                or fills["sqlite_reconciled"] or fills["live_authorized"]):
            raise M15FillCheckpointError("M15_CHECKPOINT_BROKER_FILL_UNPROVEN")
        exact = fills["weighted_price_exact"]
        vwap = Fraction(int(exact["numerator"]), int(exact["denominator"]))
        if vwap <= 0:
            raise M15FillCheckpointError("M15_CHECKPOINT_VWAP_INVALID")
        order_sha = _sha(expected.order_id)
        stamp = observed_at.astimezone(timezone.utc).isoformat()
        try:
            with self.db:
                self.db.execute("BEGIN IMMEDIATE")
                last = self.db.execute(
                    "SELECT sequence, observed_utc, symbol, side, expected_quantity,"
                    "filled_quantity, broker_position_quantity, fill_set_sha256,"
                    "vwap_numerator,vwap_denominator,protection_status "
                    "FROM checkpoints WHERE order_sha256=? "
                    "ORDER BY sequence DESC LIMIT 1", (order_sha,),
                ).fetchone()
                newly = True
                seq = 1
                if last is not None:
                    (previous_seq, previous_time, symbol, side, planned,
                     previous_qty, previous_signed, previous_set,
                     numerator, denominator, previous_protection) = last
                    if (symbol != expected.symbol or side != expected.side
                            or planned != expected.quantity):
                        raise M15FillCheckpointError("M15_CHECKPOINT_ORDER_IDENTITY_CHANGED")
                    if stamp < previous_time or quantity < previous_qty:
                        raise M15FillCheckpointError("M15_CHECKPOINT_STALE_OR_SHRUNK_FILLS")
                    if quantity == previous_qty:
                        if (fills["fill_set_sha256"] != previous_set
                                or vwap != Fraction(int(numerator), int(denominator))
                                or evidence.broker_position_quantity != previous_signed):
                            raise M15FillCheckpointError("M15_CHECKPOINT_EQUAL_QTY_CONFLICT")
                        newly = False
                        seq = previous_seq
                    else:
                        if stamp <= previous_time:
                            raise M15FillCheckpointError("M15_CHECKPOINT_NEW_FILL_CLOCK_REPLAY")
                        seq = previous_seq + 1
                if newly:
                    self.db.execute(
                        "INSERT INTO checkpoints VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (order_sha, seq, stamp, expected.symbol, expected.side,
                         expected.quantity, quantity, evidence.broker_position_quantity,
                         fills["fill_set_sha256"], str(vwap.numerator),
                         str(vwap.denominator), evidence.protection_status),
                    )
        except sqlite3.DatabaseError:
            raise M15FillCheckpointError("M15_CHECKPOINT_SQLITE_FAILURE") from None
        # Even with an active SLTP GET this does NOT prove its ACK time/coverage.
        return M15FillCheckpoint(
            order_sha, quantity, vwap, fills["fill_set_sha256"], seq,
            newly, evidence.protection_status,
        )
