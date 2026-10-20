"""M15-only H1-style execution adapter, staged behind an absolute LIVE gate.

Ported concepts from Stage8 H1 live_execution.py (read-only reference):
exact account-bound authorization, session identity, no retry of uncertain
POST, durable intent BEFORE POST, broker-confirmed risk-reducing requests.

NOT a runnable robot: frozen M15 EXECUTION_STATUS is NOT_LIVE_AUTHORIZED.
Constructing, connecting or calling this adapter cannot submit anything now.
No H1 module/runtime/token/Task is imported or mutated here.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from decimal import Decimal
from fractions import Fraction
from typing import Any

from .broker_fill_readonly import ExpectedEntry, analyze_account_trades
from .broker_risk_readonly import check_account, check_instrument
from .bar_bridge import MOSCOW, trading_windows
from .cashflow_reconcile_gate import CashflowWindow, propose_realized_capital
from .exchange_contract import contract_from_moex_and_finam, MOEX_N4_2026_10_18
from .broker_snapshot import order_views, position_quantities, unique_order_by_client_id
from .broker_reconcile_gate import assess_entry_evidence
from .grid_risk import ContractAuthority, SizedOrder, TrailingState, initial_stop, project_stop
from .risk_batch import M15BatchRiskBudget
from .protective_gate import BrokerProtection
from .trailing_gate import PendingTrail, propose_trail
from .spec import INITIAL_STOP_ATR
from .trade_draft_contract import M15OfflineTradeDrafts

from .account_boundary import validate_independent_binding
from .spec import (EXECUTION_STATUS, INSTRUMENTS, ROBOT_ID,
                   SIGNAL_START_MSK_MINUTE, SIGNAL_END_MSK_MINUTE)
from .trade_draft_contract import M15Draft

_SHA40 = re.compile(r"^[0-9a-f]{40}$")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")
_CLIENT_ID = re.compile(r"^m15[0-9a-f]{17}$")
_KEY = re.compile(r"^m15:[A-Za-z0-9._:-]{1,123}$")
_AUTH_FILENAME = "m15-execution-authorization.json"
_DB_FILENAME = "m15-production-outbound-intents.sqlite3"


class M15ExecutionError(RuntimeError):
    pass


class M15PrePostRefused(M15ExecutionError):
    """Definitely refused before sending any order to FINAM."""


class M15SubmissionUncertain(M15ExecutionError):
    """After the POST boundary a failure MUST be reconciled, NEVER retried."""


def _rest_value_equals(value: Any, expected: str) -> bool:
    """FINAM REST decimal object; equal numeric value need not share text scale."""
    if (not isinstance(value, dict) or set(value) != {"value"}
            or not isinstance(value["value"], str)):
        return False
    try:
        got = Decimal(value["value"])
        want = Decimal(expected)
    except (ValueError, TypeError, ArithmeticError):
        return False
    return got.is_finite() and want.is_finite() and got == want


def _digest(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _valid_draft(draft: M15Draft, *, account_hash: str, key: str) -> None:
    if (not isinstance(draft, M15Draft)
            or draft.account_fingerprint != account_hash
            or draft.live_authorized or draft.submitted
            or not isinstance(key, str) or _KEY.fullmatch(key) is None):
        raise M15ExecutionError("M15_OUTBOUND_DRAFT_IDENTITY_INVALID")
    body = draft.payload
    if not isinstance(body, dict):
        raise M15ExecutionError("M15_OUTBOUND_PAYLOAD_INVALID")
    symbol = body.get("symbol")
    if symbol not in {name + "@RTSX" for name in INSTRUMENTS}:
        raise M15ExecutionError("M15_OUTBOUND_SYMBOL_FORBIDDEN")
    expected_id = "m15" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:17]
    if body.get("client_order_id") != expected_id or _CLIENT_ID.fullmatch(expected_id) is None:
        raise M15ExecutionError("M15_OUTBOUND_CLIENT_ID_MISMATCH")
    if draft.kind in {"ENTRY", "EMERGENCY_EXIT"}:
        if draft.endpoint != "REGULAR_ORDER_DRAFT" or set(body) != {
                "symbol", "side", "quantity", "type", "time_in_force", "client_order_id"}:
            raise M15ExecutionError("M15_OUTBOUND_MARKET_SHAPE_INVALID")
        if (body["side"] not in {"SIDE_BUY", "SIDE_SELL"}
                or body["type"] != "ORDER_TYPE_MARKET"
                or body["time_in_force"] != "TIME_IN_FORCE_DAY"):
            raise M15ExecutionError("M15_OUTBOUND_MARKET_PARAMS_INVALID")
        try:
            quantity = int(body["quantity"]["value"])
        except (TypeError, ValueError, KeyError):
            raise M15ExecutionError("M15_OUTBOUND_QUANTITY_INVALID") from None
        if (type(body["quantity"]["value"]) is not str
                or str(quantity) != body["quantity"]["value"] or quantity <= 0):
            raise M15ExecutionError("M15_OUTBOUND_QUANTITY_INVALID")
    elif draft.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
        if draft.endpoint != "SLTP_ORDER_DRAFT" or set(body) != {
                "symbol", "side", "quantity_sl", "sl_qty_measure",
                "sl_price", "valid_before", "client_order_id", "comment"}:
            raise M15ExecutionError("M15_OUTBOUND_STOP_SHAPE_INVALID")
        if (body.get("side") not in {"SIDE_BUY", "SIDE_SELL"}
                or body.get("comment") != key
                or body.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
                or body.get("quantity_sl") != {"value": "100"}
                or body.get("valid_before") != "VALID_BEFORE_GOOD_TILL_CANCEL"):
            raise M15ExecutionError("M15_OUTBOUND_STOP_PARAMS_INVALID")
        try:
            from decimal import Decimal
            price = Decimal(body["sl_price"]["value"])
        except (ValueError, TypeError, KeyError, ArithmeticError):
            raise M15ExecutionError("M15_OUTBOUND_STOP_PRICE_INVALID") from None
        if not price.is_finite() or price <= 0:
            raise M15ExecutionError("M15_OUTBOUND_STOP_PRICE_INVALID")
    else:
        raise M15ExecutionError("M15_OUTBOUND_KIND_FORBIDDEN")


def load_execution_authorization(*, runtime_root: Path, expected_commit: str,
                                 account_hash: str) -> dict:
    """H1-style external exact authorization; NO writer in this module."""
    # This immutable freeze is checked FIRST: a stray JSON cannot arm M15.
    if EXECUTION_STATUS != "LIVE_AUTHORIZED":
        raise M15PrePostRefused("M15_LIVE_NOT_AUTHORIZED_STATIC_FREEZE")
    if (not isinstance(expected_commit, str) or not _SHA40.fullmatch(expected_commit)
            or not isinstance(account_hash, str) or not _SHA64.fullmatch(account_hash)):
        raise M15ExecutionError("M15_AUTHORIZATION_IDENTITY_INVALID")
    path = runtime_root.resolve() / "safety" / _AUTH_FILENAME
    if path.is_symlink() or not path.is_file():
        raise M15ExecutionError("M15_AUTHORIZATION_MISSING")
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise M15ExecutionError("M15_AUTHORIZATION_INVALID") from None
    required = {
        "schema": "m15_execution_authorization.v1",
        "status": "AUTHORIZED",
        "robot_id": ROBOT_ID,
        "accepted_commit": expected_commit,
        "account_sha256": account_hash,
        "execution_authorized": True,
    }
    if not isinstance(body, dict) or any(body.get(k) != v for k, v in required.items()):
        raise M15ExecutionError("M15_AUTHORIZATION_BINDING_MISMATCH")
    when = body.get("authorized_utc")
    try:
        stamp = datetime.fromisoformat(when.replace("Z", "+00:00"))
    except (TypeError, AttributeError, ValueError):
        raise M15ExecutionError("M15_AUTHORIZATION_TIME_INVALID") from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise M15ExecutionError("M15_AUTHORIZATION_TIME_INVALID")
    return body


class M15OutboundJournal:
    """Separate durable entry/SLTP/EXIT intents, NOT a fill or position ledger.

    For synthetic tests, construct only with a unique temp M15 root. This
    object never sends orders. Production authorization is independently
    checked by M15AuthorizedExecutionTransport on EVERY broker operation.
    """

    def __init__(self, *, runtime_root: Path, h1_runtime_root: Path,
                 repository_root: Path, m15_account_id: str,
                 h1_account_sha256: str):
        account_hash = validate_independent_binding(
            m15_account_id=m15_account_id, h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        root = runtime_root.resolve()
        if runtime_root.is_symlink() or (root / "state").is_symlink():
            raise M15ExecutionError("M15_OUTBOUND_JOURNAL_SYMLINK")
        self.path = root / "state" / _DB_FILENAME
        if self.path.is_symlink():
            raise M15ExecutionError("M15_OUTBOUND_DB_SYMLINK")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.account_hash = account_hash
        self.identity = {
            "robot": ROBOT_ID, "account_hash": account_hash,
            "kind": "M15_OUTBOUND_INTENT_NOT_BROKER_FILL",
        }
        existed = self.path.exists()
        self.db = sqlite3.connect(self.path, timeout=3, isolation_level=None)
        try:
            self.db.execute("PRAGMA busy_timeout=3000")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbound (
                    intent_key TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('PREPARED','UNCERTAIN','ACK')),
                    broker_order_sha256 TEXT
                );
                CREATE TABLE IF NOT EXISTS broker_fills (
                    trade_sha256 TEXT PRIMARY KEY,
                    intent_key TEXT NOT NULL REFERENCES outbound(intent_key),
                    broker_order_sha256 TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity>0),
                    price TEXT NOT NULL,
                    trade_timestamp TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS protective_prepost (
                    intent_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    signed_position_quantity INTEGER NOT NULL CHECK(signed_position_quantity!=0),
                    prior_stop_sha256 TEXT
                );
                CREATE TABLE IF NOT EXISTS protective_coverage (
                    intent_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    broker_stop_sha256 TEXT NOT NULL,
                    covered_quantity_at_ack INTEGER NOT NULL CHECK(covered_quantity_at_ack>0),
                    stop_price TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS entry_r15_basis (
                    intent_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    account_sha256 TEXT NOT NULL,
                    account_observed_utc TEXT NOT NULL,
                    cashflow_sha256 TEXT NOT NULL,
                    realized_equity TEXT NOT NULL,
                    available_cash TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    reference_entry TEXT NOT NULL,
                    stop_price TEXT NOT NULL,
                    quantity INTEGER NOT NULL CHECK(quantity>0),
                    nominal_initial_risk TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS exit_prepost (
                    intent_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    entry_key TEXT NOT NULL REFERENCES outbound(intent_key),
                    stop_key TEXT NOT NULL REFERENCES outbound(intent_key),
                    signed_position_quantity INTEGER NOT NULL CHECK(signed_position_quantity!=0),
                    protected_stop_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS broker_flat (
                    entry_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    stop_key TEXT NOT NULL REFERENCES outbound(intent_key),
                    exit_key TEXT REFERENCES outbound(intent_key),
                    confirmed_stop_sha256 TEXT NOT NULL,
                    observed_at_utc TEXT NOT NULL,
                    reason TEXT NOT NULL CHECK(reason IN ('EMERGENCY_EXIT','PROTECTIVE_EXECUTED'))
                );
                CREATE TABLE IF NOT EXISTS flat_stop_cleanup (
                    entry_key TEXT PRIMARY KEY REFERENCES outbound(intent_key),
                    stop_key TEXT NOT NULL REFERENCES outbound(intent_key),
                    broker_stop_sha256 TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN ('UNCERTAIN','RECONCILED'))
                );
            """)
            tables = {r[0] for r in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if tables != {"metadata", "outbound", "broker_fills", "protective_prepost", "protective_coverage", "entry_r15_basis", "exit_prepost", "broker_flat", "flat_stop_cleanup"}:
                raise M15ExecutionError("M15_OUTBOUND_SCHEMA_TABLES_INVALID")
            expected = {
                "metadata": ("key", "value"),
                "outbound": ("intent_key", "kind", "symbol", "payload_sha256",
                             "state", "broker_order_sha256"),
                "broker_fills": ("trade_sha256", "intent_key", "broker_order_sha256",
                                 "quantity", "price", "trade_timestamp"),
                "protective_prepost": ("intent_key", "signed_position_quantity",
                                       "prior_stop_sha256"),
                "protective_coverage": ("intent_key", "broker_stop_sha256",
                                        "covered_quantity_at_ack", "stop_price"),
                "entry_r15_basis": ("intent_key", "account_sha256", "account_observed_utc",
                                    "cashflow_sha256", "realized_equity", "available_cash",
                                    "symbol", "direction", "reference_entry", "stop_price",
                                    "quantity", "nominal_initial_risk"),
                "exit_prepost": ("intent_key", "entry_key", "stop_key",
                                 "signed_position_quantity", "protected_stop_sha256"),
                "broker_flat": ("entry_key", "stop_key", "exit_key",
                                "confirmed_stop_sha256", "observed_at_utc", "reason"),
                "flat_stop_cleanup": ("entry_key", "stop_key",
                                      "broker_stop_sha256", "state"),
            }
            for table, cols in expected.items():
                found = tuple(row[1] for row in self.db.execute(f"PRAGMA table_info({table})"))
                if found != cols:
                    raise M15ExecutionError("M15_OUTBOUND_SCHEMA_COLUMNS_INVALID")
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute(
                "SELECT value FROM metadata WHERE key='identity'").fetchone()
            if old is None:
                if existed:
                    raise M15ExecutionError("M15_OUTBOUND_EXISTING_IDENTITY_MISSING")
                self.db.execute("INSERT INTO metadata VALUES('identity',?)",
                                (json.dumps(self.identity, sort_keys=True),))
            elif json.loads(old[0]) != self.identity:
                raise M15ExecutionError("M15_OUTBOUND_ACCOUNT_MISMATCH")
            if self.db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                raise M15ExecutionError("M15_OUTBOUND_DB_INTEGRITY_FAIL")
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            self.db.close()
            raise

    @property
    def execution_authorized(self) -> bool:
        return False  # A journal alone can NEVER authorize broker submissions.

    def close(self) -> None:
        self.db.close()

    def inspect(self, key: str) -> dict | None:
        row = self.db.execute(
            "SELECT kind,symbol,payload_sha256,state,broker_order_sha256 "
            "FROM outbound WHERE intent_key=?", (key,)
        ).fetchone()
        return None if row is None else dict(zip(
            ("kind", "symbol", "payload_sha256", "state", "broker_order_sha256"), row))

    def prepare(self, *, key: str, draft: M15Draft) -> bool:
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        sha = _digest(draft.payload)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.inspect(key)
            if existing is not None:
                if (existing["kind"] != draft.kind or existing["symbol"] != draft.payload["symbol"]
                        or existing["payload_sha256"] != sha):
                    raise M15ExecutionError("M15_OUTBOUND_IDEMPOTENCY_CONFLICT")
                self.db.execute("COMMIT")
                return False
            if draft.kind == "ENTRY":
                occupied = self.db.execute(
                    "SELECT 1 FROM outbound o WHERE o.symbol=? AND o.kind='ENTRY' "
                    "AND o.state IN ('PREPARED','UNCERTAIN','ACK') "
                    "AND NOT EXISTS (SELECT 1 FROM broker_flat c WHERE c.entry_key=o.intent_key) LIMIT 1",
                    (draft.payload["symbol"],),
                ).fetchone()
                if occupied:
                    raise M15ExecutionError("M15_OUTBOUND_INSTRUMENT_OCCUPIED")
            if draft.kind == "EMERGENCY_EXIT":
                if self.db.execute(
                    "SELECT 1 FROM outbound o WHERE o.symbol=? AND "
                    "o.kind='EMERGENCY_EXIT' AND NOT EXISTS "
                    "(SELECT 1 FROM broker_flat b WHERE b.exit_key=o.intent_key) "
                    "LIMIT 1",
                    (draft.payload["symbol"],),
                ).fetchone():
                    raise M15ExecutionError("M15_EXIT_DUPLICATE_OR_UNRESOLVED")
            if draft.kind == "PROTECTIVE_STOP_INSTALL":
                existing_stop = self.db.execute(
                    "SELECT 1 FROM outbound WHERE symbol=? AND "
                    "kind='PROTECTIVE_STOP_INSTALL' AND "
                    "state IN ('PREPARED','UNCERTAIN','ACK') LIMIT 1",
                    (draft.payload["symbol"],),
                ).fetchone()
                if existing_stop:
                    raise M15ExecutionError("M15_OUTBOUND_DUPLICATE_INITIAL_STOP")
            self.db.execute(
                "INSERT INTO outbound VALUES(?,?,?,?,?,NULL)",
                (key, draft.kind, draft.payload["symbol"], sha, "PREPARED"),
            )
            self.db.execute("COMMIT")
            return True
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def begin_post_uncertain(self, *, key: str, draft: M15Draft) -> None:
        """Durably record uncertainty BEFORE entering the FINAM POST boundary."""
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind != "ENTRY":
            raise M15ExecutionError("M15_PROTECTIVE_REQUIRES_BROKER_POSITION_PREPOST")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(key)
            if (row is None or row["state"] != "PREPARED"
                    or row["kind"] != draft.kind
                    or row["payload_sha256"] != _digest(draft.payload)):
                raise M15ExecutionError("M15_OUTBOUND_NOT_PREPARED_OR_ALREADY_SENT")
            cur = self.db.execute(
                "UPDATE outbound SET state='UNCERTAIN' "
                "WHERE intent_key=? AND state='PREPARED'", (key,)
            )
            if cur.rowcount != 1:
                raise M15ExecutionError("M15_OUTBOUND_TRANSITION_FAILED")
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def record_broker_ack(self, *, key: str, draft: M15Draft,
                          broker_order_id: str) -> None:
        """A POST ACK confirms an order ID only; never an execution or stop coverage."""
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind != "ENTRY":
            raise M15ExecutionError("M15_PROTECTIVE_ACK_REQUIRES_ACTIVE_BROKER_GET")
        if not isinstance(broker_order_id, str) or not broker_order_id or len(broker_order_id) > 128:
            raise M15ExecutionError("M15_OUTBOUND_BROKER_ORDER_ID_MISSING")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(key)
            if (row is None or row["state"] != "UNCERTAIN"
                    or row["payload_sha256"] != _digest(draft.payload)):
                raise M15ExecutionError("M15_OUTBOUND_ACK_WITHOUT_UNCERTAIN")
            self.db.execute(
                "UPDATE outbound SET state='ACK',broker_order_sha256=? "
                "WHERE intent_key=? AND state='UNCERTAIN'",
                (hashlib.sha256(broker_order_id.encode()).hexdigest(), key),
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise







    def _owned_n4_risk_from_broker(self, *, positions: dict[str, int],
                                  orders: list,
                                  excluded_prepared_entry_key: str | None = None,
                                  ) -> tuple[Decimal, set[str]]:
        """H1-style portfolio gate: count ONLY exact owned protected N4 fills.

        Mismatches halt new entry preparation. Do not infer that a 100% SLTP
        was still covering a position that grew AFTER its first broker ACK.
        Previous/uncertain intents never become available capital on a guess.
        """
        all_rows = self.db.execute(
            "SELECT intent_key,kind,symbol,state,broker_order_sha256 "
            "FROM outbound").fetchall()
        if excluded_prepared_entry_key is not None:
            own = [x for x in all_rows if x[0] == excluded_prepared_entry_key]
            if len(own) != 1 or own[0][1] != "ENTRY" or own[0][3] != "PREPARED":
                raise M15ExecutionError("M15_ENTRY_PREPOST_NOT_PREPARED")
            all_rows = [x for x in all_rows if x[0] != excluded_prepared_entry_key]
        if not all_rows:
            if positions or any(o.active for o in orders):
                raise M15ExecutionError("M15_N4_UNOWNED_BROKER_POSITION_OR_ORDER")
            return Decimal("0"), set()
        # A broker-proven FLAT with no active SLTP releases original R15
        # reservation but does NOT erase audit evidence or permit LIVE.
        # Pending EXIT on an unclosed instrument still blocks every new entry.
        closed_pairs = self.db.execute(
            "SELECT entry_key,exit_key FROM broker_flat").fetchall()
        closed = {k: v for k, v in closed_pairs}
        if len(closed) != len(closed_pairs):
            raise M15ExecutionError("M15_N4_DUPLICATE_FLAT_EVIDENCE")
        allowed_exits = {v for v in closed.values() if v is not None}
        if any(r[1] == "EMERGENCY_EXIT" and r[0] not in allowed_exits
               for r in all_rows):
            raise M15ExecutionError("M15_N4_UNRESOLVED_PROTECTIVE_OR_EXIT_INTENT")
        if any(r[1] not in {"ENTRY", "EMERGENCY_EXIT",
                             "PROTECTIVE_STOP_INSTALL",
                             "PROTECTIVE_STOP_REPLACE"} for r in all_rows):
            raise M15ExecutionError("M15_N4_UNRECONCILED_EXIT_INTENT")
        if any(r[1] in {"PROTECTIVE_STOP_INSTALL","PROTECTIVE_STOP_REPLACE"}
               and r[3] != "ACK" for r in all_rows):
            raise M15ExecutionError("M15_N4_UNRESOLVED_PROTECTIVE_OR_EXIT_INTENT")
        entries = [r for r in all_rows
                   if r[1] == "ENTRY" and r[0] not in closed]
        if not entries:
            if positions or any(o.active for o in orders):
                raise M15ExecutionError("M15_N4_UNOWNED_BROKER_POSITION_OR_ORDER")
            return Decimal("0"), set()
        if (len(entries) > len(INSTRUMENTS)
                or any(r[3] != "ACK" or not r[4] for r in entries)
                or len({r[2] for r in entries}) != len(entries)):
            raise M15ExecutionError("M15_N4_UNRESOLVED_OR_DUPLICATE_ENTRY")
        symbols = {name + "@RTSX" for name in INSTRUMENTS}
        if (set(positions) - symbols
                or {s for s,q in positions.items() if q} != {r[2] for r in entries}
                or any(o.active and o.kind == "REGULAR" for o in orders)):
            raise M15ExecutionError("M15_N4_BROKER_POSITION_OR_ORDER_UNOWNED")
        planned = self.db.execute(
            "SELECT intent_key,symbol,direction,quantity,nominal_initial_risk,"
            "stop_price FROM entry_r15_basis "
            "WHERE intent_key NOT IN (SELECT entry_key FROM broker_flat) "
            "AND (? IS NULL OR intent_key<>?)",
            (excluded_prepared_entry_key, excluded_prepared_entry_key),
        ).fetchall()
        if len(planned) != len(entries):
            raise M15ExecutionError("M15_N4_ENTRY_RISK_BASIS_INCOMPLETE")
        risk_basis = {r[0]: r for r in planned}
        risk = Decimal("0")
        for key, _, symbol, _, order_hash in entries:
            base = risk_basis.get(key)
            if not base or base[1] != symbol:
                raise M15ExecutionError("M15_N4_ENTRY_RISK_BASIS_MISMATCH")
            _, _, direction, planned_qty, committed, initial = base
            signed = positions[symbol]
            if ((signed > 0) != (direction == "LONG")
                    or abs(signed) != planned_qty):
                raise M15ExecutionError("M15_N4_POSITION_NOT_FULLY_FILLED")
            order = unique_order_by_client_id(
                orders, "m15" + hashlib.sha256(key.encode()).hexdigest()[:17])
            if (order is None or order.kind != "REGULAR"
                    or order.symbol != symbol
                    or order.side != ("SIDE_BUY" if signed > 0 else "SIDE_SELL")
                    or order.status not in {"FILLED", "EXECUTED"}
                    or hashlib.sha256(order.order_id.encode()).hexdigest()
                    != order_hash
                    or not _rest_value_equals(order.request.get("quantity"),
                                              str(planned_qty))):
                raise M15ExecutionError("M15_N4_ORDER_ACK_IDENTITY_UNPROVEN")
            fills = self.db.execute(
                "SELECT quantity,price,broker_order_sha256 FROM broker_fills "
                "WHERE intent_key=?", (key,),
            ).fetchall()
            if (sum(q for q, _, _ in fills) != planned_qty
                    or any(h != order_hash for _, _, h in fills)):
                raise M15ExecutionError("M15_N4_DURABLE_BROKER_FILLS_INCOMPLETE")
            candidates = [
                x for x in orders if x.active and x.kind == "SLTP"
                and x.symbol == symbol
            ]
            if len(candidates) != 1:
                raise M15ExecutionError("M15_N4_ONE_ACTIVE_PROTECTIVE_STOP_REQUIRED")
            stop = candidates[0]
            if (stop.side != ("SIDE_SELL" if signed > 0 else "SIDE_BUY")
                    or not _rest_value_equals(stop.request.get("quantity_sl"), "100")
                    or stop.request.get("sl_qty_measure") !=
                    "SLTP_QTY_MEASURE_PERCENT"
                    or stop.request.get("valid_before") !=
                    "VALID_BEFORE_GOOD_TILL_CANCEL"):
                raise M15ExecutionError("M15_N4_ACTIVE_SLTP_SHAPE_INVALID")
            stop_rows = self.db.execute(
                "SELECT o.intent_key,c.broker_stop_sha256,"
                "c.covered_quantity_at_ack,c.stop_price "
                "FROM outbound o JOIN protective_coverage c "
                "ON c.intent_key=o.intent_key "
                "WHERE o.symbol=? AND o.state='ACK' "
                "AND o.kind IN ('PROTECTIVE_STOP_INSTALL',"
                "'PROTECTIVE_STOP_REPLACE')", (symbol,),
            ).fetchall()
            owned = [
                x for x in stop_rows if x[1] ==
                hashlib.sha256(stop.order_id.encode()).hexdigest()
                and stop.client_order_id ==
                "m15" + hashlib.sha256(x[0].encode()).hexdigest()[:17]
                and stop.comment == x[0]
            ]
            if (len(owned) != 1 or owned[0][2] != abs(signed)
                    or not _rest_value_equals(stop.request.get("sl_price"), owned[0][3])):
                raise M15ExecutionError("M15_N4_STOP_ACK_COVERAGE_OR_OWNER_UNPROVEN")
            spec = MOEX_N4_2026_10_18[symbol]
            vwap = sum(
                (Fraction(price) * quantity for quantity, price, _ in fills),
                Fraction(0),
            ) / planned_qty
            initial_price = Fraction(initial)
            if ((signed > 0 and vwap <= initial_price)
                    or (signed < 0 and vwap >= initial_price)):
                raise M15ExecutionError("M15_N4_INITIAL_RISK_WRONG_SIDE")
            real_risk = (abs(vwap-initial_price) / Fraction(spec.price_step)
                         * Fraction(spec.tick_rub) * planned_qty)
            fixed = Decimal(committed)
            if fixed <= 0 or not fixed.is_finite():
                raise M15ExecutionError("M15_N4_INITIAL_RISK_INVALID")
            # No rounding-down: maximum verified original vs. actual fill
            # risk is reserved; Fraction comparison retains exact precision.
            higher = max(Fraction(fixed), real_risk)
            if higher.denominator == 1:
                risk += Decimal(higher.numerator)
            else:
                # Terminating values are usual for decimal broker prices.
                # A fraction is converted with rounding UP to be conservative.
                from decimal import ROUND_CEILING, localcontext
                with localcontext() as ctx:
                    ctx.prec = 36
                    ctx.rounding = ROUND_CEILING
                    risk += Decimal(higher.numerator) / Decimal(higher.denominator)
        # No unowned active orders even on different symbols / same account.
        for order in orders:
            if order.active and (order.symbol not in {r[2] for r in entries}
                                 or order.kind != "SLTP"):
                raise M15ExecutionError("M15_N4_UNEXPECTED_ACTIVE_BROKER_ORDER")
        return risk, {r[2].split("@")[0] for r in entries}

    def prepare_verified_next_open_r15(
        self, *, api: Any, m15_account_id: str,
        drafts: M15OfflineTradeDrafts,
        instrument: str, authenticated_seed: Any,
        interval_start: str, interval_end: str,
        observed_at: datetime, now: datetime,
        verified_open_labels: bool = False,
    ) -> tuple[Any, M15Draft, SizedOrder] | None:
        """Closed M15 -> witnessed NEXT_OPEN -> exact M15 broker R15 -> PREPARED.

        Reuses the existing frozen T1 features, verified N4 GO/tick contract,
        lifetime cashflow gate and atomic SQLite R15 prepare. The only broker
        methods used here are GET. No entry order, SLTP or H1 access is possible.
        A lost/missing NEXT_OPEN or incomplete transactions never becomes a
        fallback signal-close fill or a guessed capital basis.
        """
        from .feature_adapter import latest_verified_finam_entry
        from .initial_capital import _timestamp
        if (not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None
                or not isinstance(observed_at, datetime)
                or observed_at.tzinfo is None or observed_at.utcoffset() is None):
            raise M15ExecutionError("M15_NEXT_OPEN_PREPARE_CLOCK_REQUIRED")
        age = (now.astimezone(timezone.utc)
               - observed_at.astimezone(timezone.utc)).total_seconds()
        if not 0 <= age <= 30:
            raise M15ExecutionError("M15_NEXT_OPEN_PREPARE_STALE")
        if (not isinstance(drafts, M15OfflineTradeDrafts)
                or drafts.execution_authorized
                or instrument not in INSTRUMENTS):
            raise M15ExecutionError("M15_NEXT_OPEN_PREPARE_DRAFT_INVALID")
        # The feature adapter strictly checks exact M15 FINAM client type and
        # closed-broker-bar provenance; the key is the deterministic signal ID.
        # Never write an outbound intent until every GET and R15 proof passes.
        # Exact M15 account supplied by the owning service: JWT-bound
        # broker methods reject all foreign-account GETs independently.
        # No API-private account attributes or H1 state are accessed.
        from .finam_readonly import M15FinamReadOnlyAPI
        from .finam_trading import M15FinamTradingAPI
        if (not isinstance(m15_account_id, str) or not m15_account_id
                or hashlib.sha256(m15_account_id.encode("utf-8")).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_NEXT_OPEN_ACCOUNT_MISMATCH")
        if type(api) is M15FinamReadOnlyAPI:
            if (api.readonly_bound is not True
                    or api.account_id != m15_account_id):
                raise M15ExecutionError("M15_NEXT_OPEN_READONLY_SESSION_UNBOUND")
        elif type(api) is not M15FinamTradingAPI:
            raise M15ExecutionError("M15_NEXT_OPEN_FINAM_CLIENT_INVALID")
        account_id = m15_account_id
        evidence = latest_verified_finam_entry(
            api=api, m15_account_id=account_id,
            instrument=instrument, authenticated_seed=authenticated_seed,
            interval_start=interval_start, interval_end=interval_end,
            observed_at=observed_at,
            verified_open_labels=verified_open_labels,
        )
        if evidence is None:
            return None
        if (not 0 <= (now.astimezone(timezone.utc)
                       - evidence.signal.completed_at.astimezone(timezone.utc)
                       ).total_seconds() <= 30):
            raise M15ExecutionError("M15_NEXT_OPEN_PREPARE_NOT_FRESH")
        account = api.account(account_id)
        orders = api.orders(account_id)
        symbol = instrument + "@RTSX"
        asset = api.asset_details(symbol)
        params = api.asset_params(symbol)
        contract = contract_from_moex_and_finam(
            check_instrument(asset, params, symbol, account_id))
        opened = _timestamp(account.get("open_account_date"))
        if opened > now.astimezone(timezone.utc):
            raise M15ExecutionError("M15_NEXT_OPEN_ACCOUNT_DATE_INVALID")
        start = opened - timedelta(seconds=1)
        end = now.astimezone(timezone.utc) + timedelta(minutes=1)
        limit = 1000
        transactions = api.transactions(
            account_id, start=start.isoformat(), end=end.isoformat(),
            limit=limit)
        windows = [CashflowWindow(start, end, transactions, limit)]
        proposal, sized = self.prepare_entry_from_broker_r15(
            key=evidence.signal.signal_id, drafts=drafts,
            instrument=instrument, direction=evidence.signal.direction,
            reference_entry=evidence.reference_open,
            signal_atr=Decimal(str(evidence.signal.signal_atr14)),
            contract=contract, asset=asset, asset_params=params,
            account=account, orders_response=orders,
            cashflow_windows=windows,
            observed_at=now, now=now,
        )
        return evidence, proposal, sized

    def prepare_entry_from_broker_r15(
        self, *, key: str, drafts: M15OfflineTradeDrafts,
        instrument: str, direction: str, reference_entry: Decimal,
        signal_atr: Decimal, contract: ContractAuthority,
        asset: dict, asset_params: dict,
        account: dict, orders_response: dict,
        cashflow_windows: list[CashflowWindow],
        observed_at: datetime, now: datetime,
    ) -> tuple[M15Draft, SizedOrder]:
        """Existing H1 clean-account R15/GO bootstrap -> ONE durable M15 ENTRY.

        Does not use H1 funds, estimated equity, hypothetical GO or position
        fills. Broker history, asset/account and freshness MUST be supplied
        from a separately authenticated M15-only read session.

        Supports the first FLAT-account entry and subsequent N4 instruments
        ONLY after all existing positions, entry fills, original risk basis and
        current broker SLTP coverage exactly reconcile. This path NEVER authorizes broker POST.
        """
        if not isinstance(drafts, M15OfflineTradeDrafts) or drafts.execution_authorized:
            raise M15ExecutionError("M15_ENTRY_R15_DRAFT_AUTHORITY_INVALID")
        if (instrument not in INSTRUMENTS or direction not in {"LONG", "SHORT"}
                or not isinstance(contract, ContractAuthority)):
            raise M15ExecutionError("M15_ENTRY_R15_INSTRUMENT_INVALID")
        if (not isinstance(observed_at, datetime) or observed_at.tzinfo is None
                or observed_at.utcoffset() is None
                or not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise M15ExecutionError("M15_ENTRY_R15_BROKER_CLOCK_INVALID")
        age = (now.astimezone(timezone.utc) -
               observed_at.astimezone(timezone.utc)).total_seconds()
        if not 0 <= age <= 30:
            raise M15ExecutionError("M15_ENTRY_R15_STALE_ACCOUNT_SNAPSHOT")
        if (not isinstance(account, dict) or
                not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_ENTRY_R15_WRONG_FINAM_ACCOUNT")
        try:
            broker = check_account(account, account["account_id"])
            capital = propose_realized_capital(
                account=account, expected_account_id=account["account_id"],
                windows=cashflow_windows, now=now,
            )
        except (ValueError, TypeError) as exc:
            raise M15ExecutionError("M15_ENTRY_R15_BROKER_CAPITAL_INVALID") from exc
        if (capital.proposed_realized_equity !=
                broker.broker_equity_minus_unrealized
                or capital.transaction_count < 1
                or capital.runtime_r15_authorized or capital.live_authorized
                or capital.source != "BOUNDED_FINAM_GET_OFFLINE_VERIFICATION"):
            raise M15ExecutionError("M15_ENTRY_R15_CAPITAL_AUTHORITY_INVALID")
        observed_positions = position_quantities(account)
        observed_orders = order_views(orders_response)
        # H1 N4: a second instrument is admissible only when every existing
        # broker position, durable fill, and protective STOP ACK reconciles.
        reserved_risk, occupied = self._owned_n4_risk_from_broker(
            positions=observed_positions, orders=observed_orders)
        if instrument in occupied:
            raise M15ExecutionError("M15_ENTRY_R15_INSTRUMENT_ALREADY_OCCUPIED")
        symbol = instrument + "@RTSX"
        verified = check_instrument(asset, asset_params, symbol, account["account_id"])
        contract.validate()
        # Reuse audited MOEX+FINAM contract authority; never accept arbitrary
        # caller tick-RUB numbers that could silently oversize live R15.
        approved = contract_from_moex_and_finam(verified)
        if contract != approved:
            raise M15ExecutionError("M15_ENTRY_R15_CONTRACT_OR_GO_MISMATCH")
        try:
            stop = initial_stop(
                direction, reference_entry, signal_atr, contract.price_step)
            budget = M15BatchRiskBudget(
                realized_equity=capital.proposed_realized_equity,
                available_margin_cash=broker.available_cash,
                committed_initial_risk=reserved_risk,
                occupied_instruments=tuple(sorted(occupied)),
            )
            sized = budget.size_and_reserve(
                instrument=instrument, direction=direction,
                entry=reference_entry, stop=stop, contract=contract,
            )
        except ValueError as exc:
            raise M15ExecutionError("M15_ENTRY_R15_PRICING_OR_MARGIN_INVALID") from exc
        if sized.reason != "OK" or sized.final_quantity <= 0:
            raise M15ExecutionError("M15_ENTRY_R15_ZERO_ORDER_CAPACITY")
        draft = drafts.entry(
            instrument=instrument, direction=direction,
            idempotency_key=key, sized=sized, observed_occupied=False,
        )
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        evidence = (
            key, self.account_hash, observed_at.astimezone(timezone.utc).isoformat(),
            capital.transaction_fingerprint_sha256,
            str(capital.proposed_realized_equity), str(broker.available_cash),
            symbol, direction, str(reference_entry), str(stop),
            sized.final_quantity, str(sized.initial_nominal_risk),
        )
        # H1 atomicity: the planned ENTRY and broker-capital/R15 basis are
        # ONE SQLite commit. No executor may observe a prepared entry that
        # lacks its original GO, risk, timestamp and account identity proof.
        self.db.execute("BEGIN IMMEDIATE")
        try:
            confirmed_risk, confirmed_occupied = self._owned_n4_risk_from_broker(
                positions=observed_positions, orders=observed_orders)
            if confirmed_risk != reserved_risk or confirmed_occupied != occupied:
                raise M15ExecutionError("M15_ENTRY_R15_PORTFOLIO_STATE_CHANGED")
            if instrument in confirmed_occupied or self.inspect(key) is not None:
                raise M15ExecutionError("M15_ENTRY_R15_DUPLICATE_INTENT")
            self.db.execute(
                "INSERT INTO outbound VALUES(?,?,?,?,?,NULL)",
                (key, draft.kind, draft.payload["symbol"],
                 _digest(draft.payload), "PREPARED"),
            )
            self.db.execute(
                "INSERT INTO entry_r15_basis VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                evidence,
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return draft, sized



    def begin_entry_post_uncertain_checked(
        self, *, key: str, draft: M15Draft,
        account: dict, orders_response: dict, asset: dict, asset_params: dict,
        schedule: dict, signal_atr: Decimal, signal_closed_at: datetime,
        now: datetime,
    ) -> None:
        """H1 pre-POST gate: session + latest NEXT_OPEN + broker N4/R15/GO.

        Caller must supply snapshots from the SAME authenticated M15 trading
        session; live transport re-GETs them instead of trusting a draft.
        The transition PREPARED→UNCERTAIN is ONE durable SQLite transaction;
        no FINAM order send or release of frozen LIVE authority happens here.
        """
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind != "ENTRY":
            raise M15ExecutionError("M15_ENTRY_PREPOST_KIND_INVALID")
        if any(not isinstance(v, datetime) or v.tzinfo is None
               or v.utcoffset() is None for v in (signal_closed_at, now)):
            raise M15ExecutionError("M15_ENTRY_PREPOST_CLOCK_INVALID")
        current = now.astimezone(timezone.utc)
        signal = signal_closed_at.astimezone(timezone.utc)
        delta = (current - signal).total_seconds()
        msk = signal_closed_at.astimezone(MOSCOW)
        minute = msk.hour * 60 + msk.minute
        if (not 0 <= delta <= 30
                or not SIGNAL_START_MSK_MINUTE <= minute < SIGNAL_END_MSK_MINUTE
                or msk.minute % 15 != 0 or msk.second or msk.microsecond):
            raise M15ExecutionError("M15_ENTRY_PREPOST_NOT_NEXT_OPEN")
        windows = trading_windows(schedule)
        if not any(start <= signal <= current < end
                   and (end - current).total_seconds() >= 30
                   for start, end in windows):
            raise M15ExecutionError("M15_ENTRY_PREPOST_SESSION_NOT_OPEN")
        row = self.inspect(key)
        proof = self.db.execute(
            "SELECT account_sha256,account_observed_utc,cashflow_sha256,"
            "realized_equity,available_cash,symbol,direction,reference_entry,"
            "stop_price,quantity,nominal_initial_risk "
            "FROM entry_r15_basis WHERE intent_key=?", (key,),
        ).fetchone()
        if (row is None or row["kind"] != "ENTRY"
                or row["state"] != "PREPARED"
                or row["payload_sha256"] != _digest(draft.payload)
                or not proof or proof[0] != self.account_hash
                or proof[5] != draft.payload["symbol"]
                or not isinstance(proof[2], str) or not _SHA64.fullmatch(proof[2])
                or proof[9] != int(draft.payload["quantity"]["value"])):
            raise M15ExecutionError("M15_ENTRY_PREPOST_DURABLE_R15_MISSING")
        try:
            prior = datetime.fromisoformat(proof[1])
            age = (current-prior.astimezone(timezone.utc)).total_seconds()
        except (TypeError, ValueError, AttributeError):
            raise M15ExecutionError("M15_ENTRY_PREPOST_R15_CLOCK_INVALID") from None
        if not 0 <= age <= 30:
            raise M15ExecutionError("M15_ENTRY_PREPOST_R15_STALE")
        if (not isinstance(account, dict)
                or not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_ENTRY_PREPOST_ACCOUNT_MISMATCH")
        funds = check_account(account, account["account_id"])
        if (funds.broker_equity_minus_unrealized != Decimal(proof[3])
                or funds.available_cash != Decimal(proof[4])):
            raise M15ExecutionError("M15_ENTRY_PREPOST_CAPITAL_OR_GO_CHANGED")
        symbol = proof[5]
        instrument = symbol.split("@")[0]
        direction = proof[6]
        if (direction not in {"LONG", "SHORT"}
                or draft.payload["side"] !=
                ("SIDE_BUY" if direction == "LONG" else "SIDE_SELL")):
            raise M15ExecutionError("M15_ENTRY_PREPOST_SIDE_MISMATCH")
        verified = check_instrument(asset, asset_params, symbol, account["account_id"])
        contract = contract_from_moex_and_finam(verified)
        reference = Decimal(proof[7])
        planned_stop = Decimal(proof[8])
        if (not isinstance(signal_atr, Decimal)
                or initial_stop(direction, reference, signal_atr,
                                contract.price_step) != planned_stop):
            raise M15ExecutionError("M15_ENTRY_PREPOST_2ATR_GRID_CHANGED")
        positions = position_quantities(account)
        orders = order_views(orders_response)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            state = self.inspect(key)
            if state is None or state["state"] != "PREPARED":
                raise M15ExecutionError("M15_ENTRY_PREPOST_ALREADY_SENT")
            risk, occupied = self._owned_n4_risk_from_broker(
                positions=positions, orders=orders,
                excluded_prepared_entry_key=key,
            )
            if instrument in occupied or any(
                o.client_order_id == draft.payload["client_order_id"]
                for o in orders
            ):
                raise M15ExecutionError("M15_ENTRY_PREPOST_ALREADY_AT_BROKER")
            budget = M15BatchRiskBudget(
                realized_equity=funds.broker_equity_minus_unrealized,
                available_margin_cash=funds.available_cash,
                committed_initial_risk=risk,
                occupied_instruments=tuple(sorted(occupied)),
            )
            sized = budget.size_and_reserve(
                instrument=instrument, direction=direction,
                entry=reference, stop=planned_stop, contract=contract,
            )
            if (sized.reason != "OK" or sized.final_quantity != proof[9]
                    or sized.initial_nominal_risk != Decimal(proof[10])):
                raise M15ExecutionError("M15_ENTRY_PREPOST_R15_GO_RECALC_MISMATCH")
            self.db.execute(
                "UPDATE outbound SET state='UNCERTAIN' "
                "WHERE intent_key=? AND state='PREPARED'", (key,),
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def _owned_exit_snapshot(
        self, *, entry_key: str, stop_key: str, account: dict,
        orders_response: dict, require_open: bool,
    ) -> tuple[str, int, str, list]:
        """Existing H1 broker ownership: exact M15 position and verified SLTP."""
        if (not isinstance(account, dict)
                or not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash
                or account.get("status") not in
                {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}):
            raise M15ExecutionError("M15_EXIT_EXACT_ACCOUNT_NOT_PROVEN")
        positions = position_quantities(account)
        orders = order_views(orders_response)
        entry = self.inspect(entry_key)
        stop = self.inspect(stop_key)
        if (entry is None or entry["kind"] != "ENTRY"
                or entry["state"] != "ACK" or not entry["broker_order_sha256"]
                or stop is None or stop["kind"] not in
                {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}
                or stop["state"] != "ACK" or not stop["broker_order_sha256"]
                or entry["symbol"] != stop["symbol"]):
            raise M15ExecutionError("M15_EXIT_DURABLE_OWNERSHIP_NOT_PROVEN")
        symbol = entry["symbol"]
        if set(positions) - {x + "@RTSX" for x in INSTRUMENTS}:
            raise M15ExecutionError("M15_EXIT_UNEXPECTED_BROKER_POSITION")
        broker_qty = positions.get(symbol, 0)
        fill_row = self.db.execute(
            "SELECT b.direction,b.quantity FROM entry_r15_basis b "
            "WHERE b.intent_key=? AND b.symbol=?", (entry_key, symbol),
        ).fetchone()
        fill_qty = self.db.execute(
            "SELECT COALESCE(SUM(quantity),0) FROM broker_fills "
            "WHERE intent_key=?", (entry_key,),
        ).fetchone()[0]
        if (fill_row is None or fill_row[1] != fill_qty
                or fill_qty <= 0):
            raise M15ExecutionError("M15_EXIT_MATCHED_ENTRY_FILLS_REQUIRED")
        original = unique_order_by_client_id(
            orders, "m15" + hashlib.sha256(entry_key.encode()).hexdigest()[:17])
        if (original is not None
                and (original.kind != "REGULAR"
                     or original.symbol != symbol
                     or original.side !=
                     ("SIDE_BUY" if fill_row[0] == "LONG" else "SIDE_SELL")
                     or hashlib.sha256(original.order_id.encode()).hexdigest()
                     != entry["broker_order_sha256"])):
            raise M15ExecutionError("M15_EXIT_ENTRY_ORDER_IDENTITY_MISMATCH")
        coverage = self.db.execute(
            "SELECT broker_stop_sha256,covered_quantity_at_ack,stop_price "
            "FROM protective_coverage WHERE intent_key=?", (stop_key,),
        ).fetchone()
        if (coverage is None or coverage[0] != stop["broker_order_sha256"]
                or coverage[1] != fill_qty):
            raise M15ExecutionError("M15_EXIT_PROTECTION_COVERAGE_UNPROVEN")
        matched_stop = [
            x for x in orders if x.kind == "SLTP" and x.symbol == symbol
            and hashlib.sha256(x.order_id.encode()).hexdigest() == coverage[0]
        ]
        if len(matched_stop) > 1:
            raise M15ExecutionError("M15_EXIT_DUPLICATE_OWNED_STOP")
        if matched_stop and (
                matched_stop[0].client_order_id !=
                "m15" + hashlib.sha256(stop_key.encode()).hexdigest()[:17]
                or matched_stop[0].comment != stop_key
                or matched_stop[0].side !=
                ("SIDE_SELL" if fill_row[0] == "LONG" else "SIDE_BUY")
                or not _rest_value_equals(matched_stop[0].request.get("quantity_sl"), "100")
                or matched_stop[0].request.get("sl_qty_measure") !=
                "SLTP_QTY_MEASURE_PERCENT"
                or not _rest_value_equals(matched_stop[0].request.get("sl_price"),
                                          coverage[2])):
            raise M15ExecutionError("M15_EXIT_STOP_OWNERSHIP_MISMATCH")
        if require_open:
            planned = fill_qty if fill_row[0] == "LONG" else -fill_qty
            if broker_qty != planned:
                raise M15ExecutionError("M15_EXIT_OPEN_POSITION_CHANGED")
            if (len(matched_stop) != 1 or not matched_stop[0].active):
                raise M15ExecutionError("M15_EXIT_PROTECTIVE_STOP_NOT_ACTIVE")
        elif broker_qty != 0:
            raise M15ExecutionError("M15_EXIT_BROKER_NOT_FLAT")
        return symbol, broker_qty, coverage[0], orders

    def prepare_emergency_exit_from_broker(
        self, *, entry_key: str, stop_key: str, exit_key: str,
        drafts: M15OfflineTradeDrafts, account: dict, orders_response: dict,
    ) -> M15Draft:
        """H1 exact-ownership, risk-reducing EXIT proposal: never POST."""
        if not isinstance(drafts, M15OfflineTradeDrafts) or drafts.execution_authorized:
            raise M15ExecutionError("M15_EXIT_DRAFT_AUTHORITY_INVALID")
        symbol, qty, _, orders = self._owned_exit_snapshot(
            entry_key=entry_key, stop_key=stop_key, account=account,
            orders_response=orders_response, require_open=True,
        )
        if (self.db.execute(
                "SELECT 1 FROM broker_flat WHERE entry_key=?", (entry_key,)
            ).fetchone()
                or any(o.active and o.symbol == symbol and o.kind == "REGULAR"
                       for o in orders)):
            raise M15ExecutionError("M15_EXIT_COMPETING_ORDER_OR_ALREADY_FLAT")
        direction = "LONG" if qty > 0 else "SHORT"
        draft = drafts.emergency_exit(
            instrument=symbol.split("@")[0], direction=direction,
            idempotency_key=exit_key, observed_position_quantity=qty,
        )
        if draft.account_fingerprint != self.account_hash:
            raise M15ExecutionError("M15_EXIT_WRONG_ACCOUNT_DRAFT")
        self.prepare(key=exit_key, draft=draft)
        return draft

    def begin_exit_post_uncertain(
        self, *, entry_key: str, stop_key: str, exit_key: str,
        draft: M15Draft, account: dict, orders_response: dict,
    ) -> None:
        """Durable UNKNOWN boundary before any future independently gated EXIT."""
        _valid_draft(draft, account_hash=self.account_hash, key=exit_key)
        if draft.kind != "EMERGENCY_EXIT":
            raise M15ExecutionError("M15_EXIT_WRONG_KIND")
        symbol, qty, stop_hash, orders = self._owned_exit_snapshot(
            entry_key=entry_key, stop_key=stop_key, account=account,
            orders_response=orders_response, require_open=True,
        )
        if (draft.payload["symbol"] != symbol
                or draft.payload["side"] !=
                ("SIDE_SELL" if qty > 0 else "SIDE_BUY")
                or not _rest_value_equals(draft.payload["quantity"], str(abs(qty)))
                or any(o.active and o.symbol == symbol and o.kind == "REGULAR"
                       for o in orders)):
            raise M15ExecutionError("M15_EXIT_PREPOST_POSITION_OR_ORDER_CHANGED")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(exit_key)
            if (row is None or row["kind"] != "EMERGENCY_EXIT"
                    or row["state"] != "PREPARED"
                    or row["payload_sha256"] != _digest(draft.payload)
                    or self.db.execute(
                        "SELECT 1 FROM exit_prepost WHERE intent_key=?",
                        (exit_key,),
                    ).fetchone()):
                raise M15ExecutionError("M15_EXIT_PREPOST_ALREADY_SENT_OR_CHANGED")
            self.db.execute(
                "INSERT INTO exit_prepost VALUES(?,?,?,?,?)",
                (exit_key, entry_key, stop_key, qty, stop_hash),
            )
            self.db.execute(
                "UPDATE outbound SET state='UNCERTAIN' "
                "WHERE intent_key=? AND state='PREPARED'",
                (exit_key,),
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise


    def begin_flat_stop_cancel_uncertain(
        self, *, entry_key: str, stop_key: str, broker_order_id: str,
        account: dict, orders_response: dict, observed_at: datetime,
    ) -> None:
        """H1: only broker-FLAT owned 100% SLTP, durable before future DELETE.

        A lost HTTP DELETE receipt is UNCERTAIN, never retried blindly.
        Caller separately uses observe_flat_broker_get on fresh FINAM GET;
        only broker-confirmed absence of the stop can reconcile cleanup.
        """
        if (not isinstance(broker_order_id, str) or not broker_order_id
                or len(broker_order_id) > 128
                or any(c in broker_order_id for c in "/?#")):
            raise M15ExecutionError("M15_FLAT_CANCEL_BROKER_STOP_ID_INVALID")
        status = self.observe_flat_broker_get(
            entry_key=entry_key, stop_key=stop_key, account=account,
            orders_response=orders_response, observed_at=observed_at,
        )
        expected_hash = hashlib.sha256(broker_order_id.encode()).hexdigest()
        if (status["active_sltp_cleanup_required"] is not True
                or status["broker_stop_sha256"] != expected_hash):
            raise M15ExecutionError("M15_FLAT_CANCEL_OWNED_ACTIVE_STOP_REQUIRED")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            if self.db.execute(
                "SELECT 1 FROM flat_stop_cleanup WHERE entry_key=?",
                (entry_key,),
            ).fetchone():
                raise M15ExecutionError("M15_FLAT_CANCEL_ALREADY_ATTEMPTED")
            if self.db.execute(
                "SELECT 1 FROM broker_flat WHERE entry_key=?",
                (entry_key,),
            ).fetchone():
                raise M15ExecutionError("M15_FLAT_CANCEL_ALREADY_CLOSED")
            self.db.execute(
                "INSERT INTO flat_stop_cleanup VALUES(?,?,?,'UNCERTAIN')",
                (entry_key, stop_key, expected_hash),
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def observe_flat_broker_get(
        self, *, entry_key: str, stop_key: str,
        account: dict, orders_response: dict, observed_at: datetime,
        exit_key: str | None = None,
    ) -> dict:
        """H1 flat→orphan SLTP cleanup→broker GET no-active→durable flat.

        No stop cancellation, market order, close-price or realized PnL is
        invented. An active STOP is surfaced for operator-approved cleanup
        and flat is NOT durably accepted until a subsequent clean GET.
        """
        if (not isinstance(observed_at, datetime)
                or observed_at.tzinfo is None or observed_at.utcoffset() is None):
            raise M15ExecutionError("M15_FLAT_OBSERVATION_TIME_INVALID")
        symbol, qty, stop_hash, orders = self._owned_exit_snapshot(
            entry_key=entry_key, stop_key=stop_key, account=account,
            orders_response=orders_response, require_open=False,
        )
        if qty != 0:
            raise M15ExecutionError("M15_FLAT_POSITION_STILL_OPEN")
        active = [o for o in orders if o.active and o.symbol == symbol]
        if any(o.kind != "SLTP" for o in active):
            raise M15ExecutionError("M15_FLAT_ACTIVE_ENTRY_OR_EXIT_UNRESOLVED")
        if active:
            if (len(active) != 1
                    or hashlib.sha256(active[0].order_id.encode()).hexdigest()
                    != stop_hash or active[0].kind != "SLTP"):
                raise M15ExecutionError("M15_FLAT_FOREIGN_ACTIVE_STOP")
            return {
                "flat_broker_observed": True,
                "active_sltp_cleanup_required": True,
                "broker_stop_sha256": stop_hash,
                "durable_closed": False,
                "new_entries_authorized": False,
                "live_authorized": False,
            }
        terminal_stop = [
            o for o in orders if o.kind == "SLTP" and o.symbol == symbol
            and hashlib.sha256(o.order_id.encode()).hexdigest() == stop_hash
        ]
        exit_row = self.inspect(exit_key) if exit_key is not None else None
        if exit_key is not None:
            prepost = self.db.execute(
                "SELECT entry_key,stop_key,signed_position_quantity,"
                "protected_stop_sha256 FROM exit_prepost WHERE intent_key=?",
                (exit_key,),
            ).fetchone()
            if (exit_row is None or exit_row["kind"] != "EMERGENCY_EXIT"
                    or exit_row["state"] not in {"UNCERTAIN", "ACK"}
                    or exit_row["symbol"] != symbol
                    or prepost is None or prepost[0] != entry_key
                    or prepost[1] != stop_key or prepost[3] != stop_hash):
                raise M15ExecutionError("M15_FLAT_EXIT_PREPOST_IDENTITY_UNPROVEN")
            exit_order = unique_order_by_client_id(
                orders, "m15" + hashlib.sha256(exit_key.encode()).hexdigest()[:17])
            if (exit_order is None or exit_order.kind != "REGULAR"
                    or exit_order.symbol != symbol
                    or exit_order.side !=
                    ("SIDE_SELL" if prepost[2] > 0 else "SIDE_BUY")
                    or not _rest_value_equals(
                        exit_order.request.get("quantity"), str(abs(prepost[2])))
                    or exit_order.status not in {"FILLED", "EXECUTED"}):
                raise M15ExecutionError("M15_FLAT_EXIT_FILL_ORDER_UNVERIFIED")
            reason = "EMERGENCY_EXIT"
        else:
            if len(terminal_stop) != 1 or terminal_stop[0].status not in {
                "SL_EXECUTED", "TP_EXECUTED", "FILLED", "EXECUTED"
            }:
                raise M15ExecutionError("M15_FLAT_PROTECTIVE_EXECUTION_UNVERIFIED")
            reason = "PROTECTIVE_EXECUTED"
        self.db.execute("BEGIN IMMEDIATE")
        try:
            existing = self.db.execute(
                "SELECT stop_key,exit_key,confirmed_stop_sha256,reason "
                "FROM broker_flat WHERE entry_key=?", (entry_key,),
            ).fetchone()
            expected = (stop_key, exit_key, stop_hash, reason)
            if existing is not None and existing != expected:
                raise M15ExecutionError("M15_FLAT_DURABLE_HISTORY_CONFLICT")
            if existing is None:
                self.db.execute(
                    "INSERT INTO broker_flat VALUES(?,?,?,?,?,?)",
                    (entry_key, stop_key, exit_key, stop_hash,
                     observed_at.astimezone(timezone.utc).isoformat(), reason),
                )
            cleanup = self.db.execute(
                "SELECT stop_key,broker_stop_sha256,state FROM flat_stop_cleanup "
                "WHERE entry_key=?", (entry_key,),
            ).fetchone()
            if cleanup is not None:
                if cleanup[0] != stop_key or cleanup[1] != stop_hash:
                    raise M15ExecutionError("M15_FLAT_CANCEL_IDENTITY_CHANGED")
                self.db.execute(
                    "UPDATE flat_stop_cleanup SET state='RECONCILED' "
                    "WHERE entry_key=? AND state='UNCERTAIN'",
                    (entry_key,),
                )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return {
            "flat_broker_observed": True,
            "active_sltp_cleanup_required": False,
            "durable_closed": True,
            "reason": reason,
            "new_entries_authorized": False,
            "live_authorized": False,
        }

    def begin_protective_post_uncertain(
        self, *, key: str, draft: M15Draft, account: dict,
        orders_response: dict, prior_active_broker_stop_id: str | None = None,
    ) -> None:
        """H1: durable signed quantity + UNKNOWN boundary BEFORE stop POST.

        This ONLY prepares for an externally authorized broker operation:
        it never sends, cancels or approves SLTP / orders.
        """
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise M15ExecutionError("M15_PROTECTIVE_PREPOST_KIND_INVALID")
        if (not isinstance(account, dict)
                or account.get("status") not in
                {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}
                or not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_PROTECTIVE_PREPOST_ACCOUNT_INVALID")
        positions = position_quantities(account)
        signed = positions.get(draft.payload["symbol"], 0)
        if (type(signed) is not int or signed == 0
                or draft.payload["side"] !=
                ("SIDE_SELL" if signed > 0 else "SIDE_BUY")):
            raise M15ExecutionError("M15_PROTECTIVE_PREPOST_POSITION_INVALID")
        orders = order_views(orders_response)
        active = [
            x for x in orders if x.active and x.kind == "SLTP"
            and x.symbol == draft.payload["symbol"]
        ]
        previous_hash = None
        if draft.kind == "PROTECTIVE_STOP_INSTALL":
            if active or prior_active_broker_stop_id is not None:
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_EXISTING_STOP")
        else:
            if (len(active) != 1
                    or not isinstance(prior_active_broker_stop_id, str)
                    or not prior_active_broker_stop_id
                    or active[0].order_id != prior_active_broker_stop_id):
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_BACKSTOP_UNPROVEN")
            old = active[0]
            if (old.side != draft.payload["side"]
                    or not _rest_value_equals(old.request.get("quantity_sl"), "100")
                    or old.request.get("sl_qty_measure") !=
                    "SLTP_QTY_MEASURE_PERCENT"
                    or not isinstance(old.request.get("sl_price"), dict)
                    or not _rest_value_equals(old.request["sl_price"],
                                              old.request["sl_price"].get("value", ""))):
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_BACKSTOP_INVALID")
            old_price = Decimal(old.request["sl_price"]["value"])
            new_price = Decimal(draft.payload["sl_price"]["value"])
            if (old_price <= 0
                    or (signed > 0 and new_price < old_price)
                    or (signed < 0 and new_price > old_price)):
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_STOP_WIDENING")
            previous_hash = hashlib.sha256(
                prior_active_broker_stop_id.encode("utf-8")).hexdigest()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(key)
            if (row is None or row["state"] != "PREPARED"
                    or row["kind"] != draft.kind
                    or row["payload_sha256"] != _digest(draft.payload)):
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_NOT_PREPARED")
            if self.db.execute(
                "SELECT 1 FROM protective_prepost WHERE intent_key=?", (key,)
            ).fetchone():
                raise M15ExecutionError("M15_PROTECTIVE_PREPOST_ALREADY_USED")
            self.db.execute(
                "INSERT INTO protective_prepost VALUES(?,?,?)",
                (key, signed, previous_hash),
            )
            self.db.execute(
                "UPDATE outbound SET state='UNCERTAIN' WHERE intent_key=? AND state='PREPARED'",
                (key,),
            )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise

    def reconcile_protective_broker_get(
        self, *, key: str, draft: M15Draft,
        account: dict, orders_response: dict,
    ) -> BrokerProtection:
        """H1 broker SLTP ACK: durable pre-POST quantity + matching ACTIVE GET.

        ACK is not a fill. A later partial fill makes this coverage stale and
        MUST hold new entries / trailing until another verified protection.
        """
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise M15ExecutionError("M15_PROTECTIVE_ACK_KIND_INVALID")
        if (not isinstance(account, dict)
                or account.get("status") not in
                {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}
                or not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_PROTECTIVE_ACK_ACCOUNT_INVALID")
        signed = position_quantities(account).get(draft.payload["symbol"], 0)
        if (type(signed) is not int or signed == 0
                or draft.payload["side"] !=
                ("SIDE_SELL" if signed > 0 else "SIDE_BUY")):
            raise M15ExecutionError("M15_PROTECTIVE_ACK_POSITION_INVALID")
        prepost = self.db.execute(
            "SELECT signed_position_quantity,prior_stop_sha256 "
            "FROM protective_prepost WHERE intent_key=?", (key,),
        ).fetchone()
        if prepost is None or signed != prepost[0]:
            raise M15ExecutionError("M15_PROTECTIVE_ACK_COVERAGE_UNPROVEN")
        orders = order_views(orders_response)
        candidates = [
            x for x in orders if x.active and x.kind == "SLTP"
            and x.symbol == draft.payload["symbol"]
        ]
        matching = [
            x for x in candidates if x.client_order_id ==
            draft.payload["client_order_id"] and x.comment == key
        ]
        if len(matching) != 1:
            raise M15ExecutionError("M15_PROTECTIVE_ACK_EXACT_STOP_NOT_ACTIVE")
        stop = matching[0]
        other = [x for x in candidates if x.order_id != stop.order_id]
        if draft.kind == "PROTECTIVE_STOP_INSTALL":
            if other or prepost[1] is not None:
                raise M15ExecutionError("M15_PROTECTIVE_ACK_DUPLICATE_ACTIVE_STOP")
        else:
            if (len(other) != 1 or prepost[1] is None
                    or hashlib.sha256(other[0].order_id.encode()).hexdigest()
                    != prepost[1]):
                raise M15ExecutionError("M15_PROTECTIVE_ACK_OLD_BACKSTOP_MISSING")
        if (stop.side != draft.payload["side"]
                or not _rest_value_equals(stop.request.get("quantity_sl"), "100")
                or stop.request.get("sl_qty_measure") != "SLTP_QTY_MEASURE_PERCENT"
                or stop.request.get("valid_before") !=
                "VALID_BEFORE_GOOD_TILL_CANCEL"
                or not _rest_value_equals(stop.request.get("sl_price"),
                                          draft.payload["sl_price"]["value"])):
            raise M15ExecutionError("M15_PROTECTIVE_ACK_PRICE_OR_100_PERCENT_MISMATCH")
        broker_hash = hashlib.sha256(stop.order_id.encode()).hexdigest()
        quantity = abs(signed)
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(key)
            if (row is None or row["kind"] != draft.kind
                    or row["state"] not in {"UNCERTAIN", "ACK"}
                    or row["payload_sha256"] != _digest(draft.payload)
                    or (row["state"] == "ACK"
                        and row["broker_order_sha256"] != broker_hash)):
                raise M15ExecutionError("M15_PROTECTIVE_ACK_INTENT_NOT_MATCHED")
            existing = self.db.execute(
                "SELECT broker_stop_sha256,covered_quantity_at_ack,stop_price "
                "FROM protective_coverage WHERE intent_key=?", (key,),
            ).fetchone()
            expected = (broker_hash, quantity, draft.payload["sl_price"]["value"])
            if existing is not None and existing != expected:
                raise M15ExecutionError("M15_PROTECTIVE_ACK_COVERAGE_CHANGED")
            if existing is None:
                self.db.execute(
                    "INSERT INTO protective_coverage VALUES(?,?,?,?)",
                    (key, *expected),
                )
            if row["state"] == "UNCERTAIN":
                self.db.execute(
                    "UPDATE outbound SET state='ACK',broker_order_sha256=? "
                    "WHERE intent_key=? AND state='UNCERTAIN'",
                    (broker_hash, key),
                )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return BrokerProtection(
            broker_order_id=stop.order_id,
            stop_price=Decimal(draft.payload["sl_price"]["value"]),
            percent=100, covered_quantity_at_ack=quantity, active=True,
        )

    def prepare_initial_sltp_from_broker_position(
        self, *, entry_key: str, entry_draft: M15Draft, stop_key: str,
        drafts: M15OfflineTradeDrafts, instrument: str, direction: str,
        reference_entry: Decimal, precommitted_stop: Decimal,
        atr_at_signal: Decimal, contract: ContractAuthority,
        sized: SizedOrder, account: dict, orders_response: dict,
    ) -> M15Draft:
        """H1 STOP-FIRST: broker position + PRECOMMITTED risk/stop, before trades.

        No AccountTrade/VWAP history is required to prepare the protective
        100%-position intent. This is still an unsent draft, NOT SLTP ACK.
        Real entry/stop POST remains forbidden under the separate LIVE gates.
        Subsequent authenticated trade history must validate exact fill VWAP
        and realized R15 risk without withdrawing this initial backstop.
        """
        _valid_draft(entry_draft, account_hash=self.account_hash, key=entry_key)
        row = self.inspect(entry_key)
        if (not row or row["kind"] != "ENTRY"
                or row["state"] not in {"UNCERTAIN", "ACK"}
                or row["payload_sha256"] != _digest(entry_draft.payload)):
            raise M15ExecutionError("M15_STOP_DURABLE_POST_BOUNDARY_REQUIRED")
        if (instrument not in INSTRUMENTS
                or entry_draft.payload["symbol"] != instrument + "@RTSX"
                or direction not in {"LONG", "SHORT"}
                or entry_draft.payload["side"] !=
                ("SIDE_BUY" if direction == "LONG" else "SIDE_SELL")
                or not isinstance(drafts, M15OfflineTradeDrafts)
                or drafts.execution_authorized):
            raise M15ExecutionError("M15_STOP_ACCOUNT_OR_ENTRY_IDENTITY_INVALID")
        if (not isinstance(contract, ContractAuthority)
                or not isinstance(sized, SizedOrder)):
            raise M15ExecutionError("M15_STOP_PRECOMMITTED_R15_GO_MISSING")
        contract.validate()
        if (not isinstance(atr_at_signal, Decimal) or
                not atr_at_signal.is_finite() or atr_at_signal <= 0 or
                not isinstance(reference_entry, Decimal) or
                not isinstance(precommitted_stop, Decimal)):
            raise M15ExecutionError("M15_STOP_PRECOMMITTED_PRICE_INVALID")
        try:
            computed = initial_stop(
                direction, reference_entry, atr_at_signal, contract.price_step)
        except ValueError:
            raise M15ExecutionError("M15_STOP_INITIAL_STOP_INVALID") from None
        if computed != precommitted_stop:
            raise M15ExecutionError("M15_STOP_PRECOMMITTED_2ATR_MISMATCH")
        planned = int(entry_draft.payload["quantity"]["value"])
        per_contract_risk = (
            abs(reference_entry - computed) / contract.price_step * contract.tick_value
        )
        if (sized.reason != "OK" or type(sized.final_quantity) is not int
                or sized.final_quantity != planned
                or sized.per_contract_loss != per_contract_risk
                or sized.initial_nominal_risk != per_contract_risk * planned
                or sized.risk_budget <= 0
                or sized.initial_nominal_risk > sized.risk_budget
                or planned % contract.trade_lot_size != 0
                or planned > sized.by_risk or planned > sized.by_margin):
            raise M15ExecutionError("M15_STOP_PRECOMMITTED_R15_GO_INVALID")
        if (not isinstance(account, dict)
                or account.get("status") not in
                {"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"}
                or not isinstance(account.get("account_id"), str)
                or hashlib.sha256(account["account_id"].encode()).hexdigest()
                != self.account_hash):
            raise M15ExecutionError("M15_STOP_BROKER_ACCOUNT_NOT_BOUND")
        positions = position_quantities(account)
        signed = positions.get(entry_draft.payload["symbol"], 0)
        if (type(signed) is not int or signed == 0
                or (signed > 0) != (direction == "LONG")
                or abs(signed) > planned):
            raise M15ExecutionError("M15_STOP_BROKER_POSITION_NOT_MATCHED")
        orders = order_views(orders_response)
        expected_client_id = entry_draft.payload["client_order_id"]
        order = unique_order_by_client_id(orders, expected_client_id)
        if (order is None or order.kind != "REGULAR"
                or order.symbol != entry_draft.payload["symbol"]
                or order.side != entry_draft.payload["side"]
                or order.request.get("quantity") != {"value": str(planned)}
                or order.status not in {"PARTIAL_FILL", "FILLED", "EXECUTED"}):
            raise M15ExecutionError("M15_STOP_BROKER_ENTRY_ORDER_NOT_MATCHED")
        for other in orders:
            if (other.active and other.symbol == order.symbol
                    and other.order_id != order.order_id):
                raise M15ExecutionError("M15_STOP_COMPETING_BROKER_ORDER_OR_STOP")
        if row["state"] == "ACK":
            expected_order_hash = hashlib.sha256(order.order_id.encode()).hexdigest()
            if row["broker_order_sha256"] != expected_order_hash:
                raise M15ExecutionError("M15_STOP_BROKER_ORDER_CHANGED")
        proposal = drafts.protective_stop(
            instrument=instrument, direction=direction, idempotency_key=stop_key,
            observed_position_quantity=signed, stop_price=computed,
            price_step=contract.price_step,
        )
        if (proposal.account_fingerprint != self.account_hash
                or proposal.submitted or proposal.live_authorized):
            raise M15ExecutionError("M15_STOP_PROPOSAL_ACCOUNT_OR_LIVE_INVALID")
        # First durable broker-order identity, then durable stop intent.
        # Crash between transactions is safe: restart can prepare same key.
        if row["state"] == "UNCERTAIN":
            self.record_broker_ack(
                key=entry_key, draft=entry_draft, broker_order_id=order.order_id)
        self.prepare(key=stop_key, draft=proposal)
        return proposal

    def prepare_initial_sltp_from_durable_fills(
        self, *, entry_key: str, entry_draft: M15Draft,
        broker_report: dict, stop_key: str, drafts: M15OfflineTradeDrafts,
        instrument: str, direction: str, atr_at_signal: Decimal,
        price_step: Decimal,
    ) -> M15Draft:
        """H1 STOP-first: exact broker GET fills -> persisted 100%-position SLTP.

        Does NOT transmit or ACK the stop. A new entry stays forbidden
        until a separately obtained broker-side 100% protection receipt.
        """
        _valid_draft(entry_draft, account_hash=self.account_hash, key=entry_key)
        row = self.inspect(entry_key)
        if (not row or row["state"] != "ACK" or row["kind"] != "ENTRY"
                or row["payload_sha256"] != _digest(entry_draft.payload)
                or not isinstance(broker_report, dict)
                or broker_report.get("broker_order_sha256") != row["broker_order_sha256"]
                or broker_report.get("protection_status") != "UNPROTECTED_BROKER_FILL"
                or broker_report.get("live_authorized") is not False):
            raise M15ExecutionError("M15_STOP_BROKER_FILL_OR_NO_STOP_PROOF_REQUIRED")
        if (instrument not in INSTRUMENTS
                or entry_draft.payload["symbol"] != instrument + "@RTSX"
                or direction not in {"LONG", "SHORT"}
                or entry_draft.payload["side"] !=
                ("SIDE_BUY" if direction == "LONG" else "SIDE_SELL")
                or not isinstance(drafts, M15OfflineTradeDrafts)
                or drafts.execution_authorized):
            raise M15ExecutionError("M15_STOP_DRAFT_IDENTITY_INVALID")
        if (not isinstance(atr_at_signal, Decimal) or not atr_at_signal.is_finite()
                or atr_at_signal <= 0 or not isinstance(price_step, Decimal)
                or not price_step.is_finite() or price_step <= 0):
            raise M15ExecutionError("M15_STOP_ATR_OR_GRID_INVALID")
        rows = self.db.execute(
            "SELECT quantity,price FROM broker_fills WHERE intent_key=?",
            (entry_key,),
        ).fetchall()
        filled = sum(q for q, _ in rows)
        signed = filled if direction == "LONG" else -filled
        if (filled <= 0
                or broker_report.get("matched_quantity") != filled
                or broker_report.get("broker_position_quantity") != signed):
            raise M15ExecutionError("M15_STOP_DURABLE_BROKER_QUANTITY_MISMATCH")
        weighted = sum((Fraction(price) * qty for qty, price in rows), Fraction(0))
        average = weighted / filled
        exact = broker_report.get("weighted_vwap_exact")
        if (not isinstance(exact, dict) or
                exact != {"numerator": str(average.numerator),
                          "denominator": str(average.denominator)}):
            raise M15ExecutionError("M15_STOP_VWAP_RECONCILIATION_FAILED")
        raw = (average - Fraction(INITIAL_STOP_ATR) * Fraction(atr_at_signal)
               if direction == "LONG"
               else average + Fraction(INITIAL_STOP_ATR) * Fraction(atr_at_signal))
        if (raw <= 0 or (direction == "LONG" and raw >= average)
                or (direction == "SHORT" and raw <= average)):
            raise M15ExecutionError("M15_STOP_WRONG_SIDE")
        stop = project_stop(direction, raw, price_step)
        proposal = drafts.protective_stop(
            instrument=instrument, direction=direction,
            idempotency_key=stop_key, observed_position_quantity=signed,
            stop_price=stop, price_step=price_step,
        )
        if (proposal.account_fingerprint != self.account_hash
                or proposal.submitted or proposal.live_authorized):
            raise M15ExecutionError("M15_STOP_ACCOUNT_OR_LIVE_PROPOSAL_INVALID")
        # Persist BEFORE any possible POST. A proposal is NEVER a broker ACK.
        self.prepare(key=stop_key, draft=proposal)
        return proposal


    def prepare_trailing_sltp_from_broker(
        self, *, drafts: M15OfflineTradeDrafts, stop_key: str,
        confirmed: TrailingState, broker_stop: BrokerProtection,
        broker_position_qty: int, completed_at: datetime,
        high: Decimal, low: Decimal, atr: Decimal, price_step: Decimal,
        survived_completed_bar: bool,
    ) -> tuple[PendingTrail, M15Draft | None]:
        """H1-style broker-protected STOP-before-TRAIL, no live state advance.

        A new stop is a durable, unsubmitted intent. Caller MUST separately
        obtain FINAM ACK and call existing trailing_gate.confirm_trail before
        committing the candidate stop/watermark. Never cancel the old stop.
        """
        if not isinstance(drafts, M15OfflineTradeDrafts) or drafts.execution_authorized:
            raise M15ExecutionError("M15_TRAIL_DRAFT_AUTHORITY_INVALID")
        pending = propose_trail(
            confirmed=confirmed, observed_stop=broker_stop,
            broker_position_qty=broker_position_qty,
            completed_at=completed_at, high=high, low=low, atr=atr,
            price_step=price_step, survived_completed_bar=survived_completed_bar,
        )
        if not pending.replace_required:
            return pending, None
        signed = (broker_position_qty if confirmed.direction == "LONG"
                  else -broker_position_qty)
        proposal = drafts.protective_stop(
            instrument=confirmed.instrument, direction=confirmed.direction,
            idempotency_key=stop_key, observed_position_quantity=signed,
            stop_price=pending.candidate.active_stop, price_step=price_step,
            kind="PROTECTIVE_STOP_REPLACE",
            previous_active_stop=confirmed.active_stop,
        )
        if (proposal.account_fingerprint != self.account_hash
                or proposal.submitted or proposal.live_authorized):
            raise M15ExecutionError("M15_TRAIL_DRAFT_ACCOUNT_OR_LIVE_INVALID")
        self.prepare(key=stop_key, draft=proposal)
        return pending, proposal

    def reconcile_entry_broker_get(
        self, *, key: str, draft: M15Draft, expected: ExpectedEntry,
        expected_client_order_id: str, stop_trade_tag: str,
        account: dict, orders_response: dict, trades_response: dict,
        start: str, end: str, limit: int = 1000,
    ) -> dict:
        """H1-style GET-only recovery of a real-shaped entry, incl. UNCERTAIN POST.

        The caller must separately prove a fresh authenticated M15 broker
        session. No token, FINAM API, order transport or live permission here.
        Atomic durable fills are facts, never an SLTP ACK or trading permit.
        """
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if not isinstance(expected, ExpectedEntry) or draft.kind != "ENTRY":
            raise M15ExecutionError("M15_FILL_EXPECTED_ENTRY_REQUIRED")
        if (hashlib.sha256(expected.account_id.encode("utf-8")).hexdigest() != self.account_hash
                or expected.symbol != draft.payload["symbol"]
                or expected.side != draft.payload["side"]
                or expected.quantity != int(draft.payload["quantity"]["value"])
                or expected_client_order_id != draft.payload["client_order_id"]):
            raise M15ExecutionError("M15_FILL_DURABLE_BROKER_IDENTITY_MISMATCH")
        # Both validators require matching account, order/client ID, position,
        # complete bounded FINAM AccountTrade history and compatible stop list.
        evidence = assess_entry_evidence(
            account=account, orders_response=orders_response,
            trades_response=trades_response, expected=expected,
            expected_client_order_id=expected_client_order_id,
            stop_trade_tag=stop_trade_tag, start=start, end=end, limit=limit,
        )
        report = analyze_account_trades(
            trades_response, expected, start=start, end=end, limit=limit,
        )
        if (evidence.matched_fill_quantity != report["matched_quantity"]
                or evidence.fill_set_sha256 != report["fill_set_sha256"]
                or evidence.sqlite_adoption_authorized or evidence.live_authorized
                or report["sqlite_reconciled"] or report["live_authorized"]):
            raise M15ExecutionError("M15_FILL_INDEPENDENT_GET_DIVERGENCE")
        broker_hash = hashlib.sha256(expected.order_id.encode("utf-8")).hexdigest()
        # Normalize exact validated trade facts. Duplicate identical GET rows
        # collapse by trade ID; different trade IDs never share SQL authority.
        observations = {}
        for raw in trades_response["trades"]:
            if raw["order_id"] != expected.order_id:
                continue
            trade_hash = hashlib.sha256(raw["trade_id"].encode("utf-8")).hexdigest()
            price = str(Decimal(raw["price"]["value"]))
            qty = int(Decimal(raw["size"]["value"]))
            fact = (key, broker_hash, qty, price, raw["timestamp"])
            if trade_hash in observations and observations[trade_hash] != fact:
                raise M15ExecutionError("M15_FILL_DUPLICATE_GET_CONFLICT")
            observations[trade_hash] = fact
        if sum(v[2] for v in observations.values()) != evidence.matched_fill_quantity:
            raise M15ExecutionError("M15_FILL_GET_QUANTITY_DIVERGENCE")
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.inspect(key)
            if (row is None or row["kind"] != "ENTRY"
                    or row["state"] not in {"UNCERTAIN", "ACK"}
                    or row["symbol"] != expected.symbol
                    or row["payload_sha256"] != _digest(draft.payload)
                    or (row["state"] == "ACK"
                        and row["broker_order_sha256"] != broker_hash)):
                raise M15ExecutionError("M15_FILL_UNCERTAIN_OR_ACK_INTENT_REQUIRED")
            old = self.db.execute(
                "SELECT trade_sha256,intent_key,broker_order_sha256,quantity,"
                "price,trade_timestamp FROM broker_fills WHERE intent_key=?",
                (key,),
            ).fetchall()
            for trade_hash, *previous in old:
                if observations.get(trade_hash) != tuple(previous):
                    raise M15ExecutionError("M15_FILL_DURABLE_HISTORY_MISSING_OR_CHANGED")
            new_count = 0
            old_hashes = {r[0] for r in old}
            for trade_hash, fact in observations.items():
                if trade_hash not in old_hashes:
                    self.db.execute(
                        "INSERT INTO broker_fills VALUES(?,?,?,?,?,?)",
                        (trade_hash, *fact),
                    )
                    new_count += 1
            if row["state"] == "UNCERTAIN":
                # Verified order/client-ID/account/trades GET proves the order
                # exists, even when its original POST ACK was lost.
                self.db.execute(
                    "UPDATE outbound SET state='ACK',broker_order_sha256=? "
                    "WHERE intent_key=? AND state='UNCERTAIN'",
                    (broker_hash, key),
                )
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return {
            "broker_order_sha256": broker_hash,
            "fill_set_sha256": report["fill_set_sha256"],
            "matched_quantity": report["matched_quantity"],
            "broker_position_quantity": evidence.broker_position_quantity,
            "quantity_status": evidence.quantity_status,
            "weighted_vwap_exact": report["weighted_price_exact"],
            "new_durable_fills": new_count,
            "protection_status": evidence.protection_status,
            "broker_stop_acknowledged": False,
            "new_entries_authorized": False,
            "order_submission_authorized": False,
            "live_authorized": False,
        }


def require_m15_production_entry_gate(*, runtime_root: Path, accepted_commit: str,
                                      account_hash: str, now: datetime) -> None:
    """H1-style M15 ARMED and healthy reconciliation: fail closed, no arming.

    Only a production M15 producer can furnish this evidence. The offline
    service heartbeat is explicitly insufficient to enable trading.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise M15PrePostRefused("M15_ENTRY_RUNTIME_CLOCK_INVALID")
    root = Path(runtime_root).resolve()
    paths = (
        (root / "safety" / "m15-trading-kill-switch.json", "m15_trading_kill_switch.v1"),
        (root / "diagnostics" / "m15-production-heartbeat.json", "m15_production_heartbeat.v1"),
    )
    values = []
    for path, schema in paths:
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise M15PrePostRefused("M15_ENTRY_RUNTIME_EVIDENCE_MISSING")
        try:
            if path.stat().st_size > 65536:
                raise ValueError("oversized")
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            raise M15PrePostRefused("M15_ENTRY_RUNTIME_EVIDENCE_INVALID") from None
        if not isinstance(value, dict) or value.get("schema_id") != schema:
            raise M15PrePostRefused("M15_ENTRY_RUNTIME_SCHEMA_MISMATCH")
        values.append(value)
    switch, heartbeat = values
    if (switch.get("robot_id") != ROBOT_ID or switch.get("state") != "ARMED"
            or type(switch.get("generation")) is not int or switch["generation"] < 1):
        raise M15PrePostRefused("M15_ENTRY_KILL_SWITCH_NOT_ARMED")
    if (heartbeat.get("robot_id") != ROBOT_ID
            or heartbeat.get("accepted_code_commit") != accepted_commit
            or heartbeat.get("account_hash") != account_hash
            or heartbeat.get("reconciliation_status") != "PASS"
            or heartbeat.get("health_status") != "HEALTHY"
            or type(heartbeat.get("cycle_count")) is not int
            or heartbeat["cycle_count"] < 1
            or type(heartbeat.get("unresolved_intent_count")) is not int
            or heartbeat["unresolved_intent_count"] != 0
            or heartbeat.get("kill_switch_generation") != switch["generation"]
            or heartbeat.get("position_protection_verified") is not True):
        raise M15PrePostRefused("M15_ENTRY_RUNTIME_NOT_RECONCILED")
    for kind, raw in (("switch", switch.get("updated_utc")),
                      ("heartbeat", heartbeat.get("timestamp")),
                      ("finam", heartbeat.get("last_successful_finam_api_contact"))):
        try:
            when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if when.tzinfo is None or when.utcoffset() is None:
                raise ValueError("timezone")
            age = (now.astimezone(timezone.utc) -
                   when.astimezone(timezone.utc)).total_seconds()
        except (TypeError, ValueError, AttributeError):
            raise M15PrePostRefused("M15_ENTRY_RUNTIME_TIMESTAMP_INVALID") from None
        # H1 behavior: ARMED persists; heartbeat and FINAM contact must be fresh.
        if age < -5 or (kind != "switch" and age > 60):
            raise M15PrePostRefused("M15_ENTRY_RUNTIME_EVIDENCE_STALE")


class M15AuthorizedExecutionTransport:
    """H1-style FINAM order interface; absolutely inert until independent LIVE approval.

    api supplies H1-compatible methods but MUST be M15-owned (never import or
    instantiate the H1 live object). Calls always require static LIVE gate,
    exact external M15 authorization, session account identity and separate
    M15 journal; new-entry heartbeat and broker reconciliation remain required
    release gates at later operator acceptance.
    """
    def __init__(self, *, api: Any, m15_account_id: str, h1_account_sha256: str,
                 runtime_root: Path, h1_runtime_root: Path,
                 repository_root: Path, accepted_commit: str):
        fingerprint = validate_independent_binding(
            m15_account_id=m15_account_id, h1_account_sha256=h1_account_sha256,
            m15_runtime_root=runtime_root, h1_runtime_root=h1_runtime_root,
            repository_root=repository_root,
        )
        self.api = api
        self.account_id = m15_account_id
        self.account_hash = fingerprint
        self.runtime_root = runtime_root
        self.accepted_commit = accepted_commit
        self.connected = False
        # H1 design: no FINAM session or POST unless durable permission exists.
        self._require_authorization()

    def _require_authorization(self) -> None:
        load_execution_authorization(
            runtime_root=self.runtime_root, expected_commit=self.accepted_commit,
            account_hash=self.account_hash,
        )

    def connect(self) -> None:
        self._require_authorization()
        self.api.create_session()
        details = self.api.session_details()
        if (not isinstance(details, dict) or details.get("readonly") is not False
                or details.get("account_ids") != [self.account_id]):
            raise M15ExecutionError("M15_TRADING_SESSION_NOT_EXACT_WRITE_ACCOUNT")
        account = self.api.account(self.account_id)
        if not isinstance(account, dict) or account.get("account_id") != self.account_id:
            raise M15ExecutionError("M15_TRADING_ACCOUNT_NOT_BOUND")
        from .finam_trading import M15FinamTradingAPI
        if not isinstance(self.api, M15FinamTradingAPI):
            raise M15ExecutionError("M15_TRADING_WRONG_API_CLIENT")
        self.api._bind_exact_session(details=details, account=account)
        self.connected = True

    def _require_connected(self) -> None:
        self._require_authorization()
        if self.connected is not True:
            raise M15ExecutionError("M15_TRADING_SESSION_NOT_CONNECTED")

    def _transmit(self, *, journal: M15OutboundJournal, key: str,
                  draft: M15Draft, send, protective_position_qty: int | None = None):
        self._require_connected()
        if not isinstance(journal, M15OutboundJournal) or journal.account_hash != self.account_hash:
            raise M15ExecutionError("M15_TRADING_JOURNAL_ACCOUNT_INVALID")
        if journal.path.parent.parent.resolve() != self.runtime_root.resolve():
            raise M15ExecutionError("M15_TRADING_JOURNAL_RUNTIME_MISMATCH")
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE",
                          "EMERGENCY_EXIT"}:
            if type(protective_position_qty) is not int or protective_position_qty == 0:
                raise M15ExecutionError("M15_TRADING_BROKER_POSITION_UNPROVEN")
            expected_side = "SIDE_SELL" if protective_position_qty > 0 else "SIDE_BUY"
            if draft.payload["side"] != expected_side:
                raise M15ExecutionError("M15_TRADING_CLOSING_SIDE_INVALID")
            if draft.kind == "EMERGENCY_EXIT" and draft.payload["quantity"] != {
                    "value": str(abs(protective_position_qty))}:
                raise M15ExecutionError("M15_TRADING_EXIT_SIZE_MISMATCH")
        if draft.kind == "ENTRY":
            # The production new-entry gate (broker reconciliation, fresh
            # heartbeat, ARMED switch, proven R15) is NOT YET connected.
            # Do not allow order submission merely from a valid market draft.
            raise M15PrePostRefused("M15_ENTRY_PRODUCTION_GATE_NOT_IMPLEMENTED")
        journal.begin_post_uncertain(key=key, draft=draft)
        # CRITICAL: every exception beyond this line is UNCERTAIN. NEVER retry.
        try:
            response = send(self.account_id, dict(draft.payload))
            if not isinstance(response, dict) or not isinstance(response.get("order_id"), str):
                raise M15SubmissionUncertain("M15_POST_ACK_MISSING_ORDER_ID")
            journal.record_broker_ack(
                key=key, draft=draft, broker_order_id=response["order_id"])
            return {"broker_order_sha256": hashlib.sha256(
                    response["order_id"].encode()).hexdigest(),
                    "order_post_ack": True, "fill_confirmed": False,
                    "stop_coverage_confirmed": False}
        except Exception as exc:
            raise M15SubmissionUncertain("M15_POST_UNCERTAIN_BROKER_GET_RECONCILE_REQUIRED") from exc

    def submit_entry(
        self, *, journal: M15OutboundJournal, key: str, draft: M15Draft,
        signal_atr: Decimal, signal_closed_at: datetime,
    ) -> dict:
        """H1 pre-POST: exact trading-session broker GET + durable R15/GO recheck.

        The M15 completed-bar/signal producer must separately establish the
        causal NEXT_OPEN event. No operator input can replace that upstream
        evidence. This method remains INERT under both frozen LIVE gates.
        """
        if draft.kind != "ENTRY":
            raise M15PrePostRefused("M15_ENTRY_DRAFT_KIND_INVALID")
        self._require_connected()
        from .finam_trading import M15FinamTradingAPI, M15_ORDER_POST_RELEASED
        if M15_ORDER_POST_RELEASED is not True:
            raise M15PrePostRefused("M15_ENTRY_POST_RELEASE_NOT_AUTHORIZED")
        if not isinstance(self.api, M15FinamTradingAPI):
            raise M15ExecutionError("M15_ENTRY_TRADING_CLIENT_INVALID")
        if (not isinstance(journal, M15OutboundJournal)
                or journal.account_hash != self.account_hash
                or journal.path.parent.parent.resolve()
                != self.runtime_root.resolve()):
            raise M15ExecutionError("M15_ENTRY_JOURNAL_IDENTITY_MISMATCH")
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        symbol = draft.payload["symbol"]
        require_m15_production_entry_gate(
            runtime_root=self.runtime_root, accepted_commit=self.accepted_commit,
            account_hash=self.account_hash, now=datetime.now(timezone.utc),
        )
        # These GETs use the SAME JWT-bound M15 trading session as POST.
        # No H1 import, account ID, token or runtime can be read from here.
        account = self.api.account(self.account_id)
        orders = self.api.orders(self.account_id)
        asset = self.api.asset_details(symbol)
        params = self.api.asset_params(symbol)
        schedule = self.api.schedule(symbol)
        journal.begin_entry_post_uncertain_checked(
            key=key, draft=draft, account=account, orders_response=orders,
            asset=asset, asset_params=params, schedule=schedule,
            signal_atr=signal_atr, signal_closed_at=signal_closed_at,
            now=datetime.now(timezone.utc),
        )
        try:
            receipt = self.api.place_order(self.account_id, dict(draft.payload))
        except Exception as exc:
            raise M15SubmissionUncertain(
                "M15_ENTRY_POST_UNCERTAIN_FINAM_GET_RECOVERY_REQUIRED") from exc
        if (not isinstance(receipt, dict)
                or not isinstance(receipt.get("order_id"), str)
                or not receipt["order_id"]):
            raise M15SubmissionUncertain("M15_ENTRY_POST_ACK_ORDER_ID_NOT_PROVED")
        # The order ID is not a fill and NEVER implies active protective SLTP.
        journal.record_broker_ack(
            key=key, draft=draft, broker_order_id=receipt["order_id"],
        )
        return {
            "broker_order_sha256": hashlib.sha256(
                receipt["order_id"].encode("utf-8")).hexdigest(),
            "post_ack_observed": True,
            "broker_fill_confirmed": False,
            "broker_stop_100_percent_confirmed": False,
            "new_entries_authorized": False,
            "live_reconciled": False,
        }

    def reconcile_entry_from_finam(
        self, *, journal: M15OutboundJournal, key: str, draft: M15Draft,
        expected: ExpectedEntry | None, stop_trade_tag: str,
        start: str, end: str, limit: int = 1000,
    ) -> dict:
        """Step 14: same authenticated M15 trading JWT -> durable FINAM fills.

        Mandatory on restart/unknown POST and after normal POST ACK. No order
        submission, no retry, and no inference of protective STOP from fills.
        """
        self._require_connected()
        from .finam_trading import M15FinamTradingAPI
        if (not isinstance(self.api, M15FinamTradingAPI)
                or not isinstance(journal, M15OutboundJournal)
                or journal.account_hash != self.account_hash
                or journal.path.parent.parent.resolve() != self.runtime_root.resolve()
                or (expected is not None
                    and (not isinstance(expected, ExpectedEntry)
                         or expected.account_id != self.account_id))):
            raise M15ExecutionError("M15_ENTRY_RECONCILE_SESSION_OR_ACCOUNT_INVALID")
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if draft.kind != "ENTRY":
            raise M15ExecutionError("M15_ENTRY_RECONCILE_WRONG_DRAFT")
        # Resolve lost-ACK ENTRY from the immutable deterministic client ID.
        # NEVER create or retry a FINAM order just because its HTTP ACK was lost.
        account = self.api.account(self.account_id)
        orders = self.api.orders(self.account_id)
        if expected is None:
            order = unique_order_by_client_id(
                order_views(orders), draft.payload["client_order_id"])
            if order is None:
                raise M15ExecutionError(
                    "M15_ENTRY_RECOVERY_CLIENT_ORDER_NOT_FOUND_NO_REPOST")
            if (order.kind != "REGULAR"
                    or order.symbol != draft.payload["symbol"]
                    or order.side != draft.payload["side"]
                    or not _rest_value_equals(
                        order.request.get("quantity"),
                        draft.payload["quantity"]["value"])):
                raise M15ExecutionError("M15_ENTRY_RECOVERY_ORDER_MISMATCH")
            # The executable tick grid comes only from the same M15 JWT,
            # checked against the pinned MOEX N4 reference, not from a guess.
            asset = self.api.asset_details(order.symbol)
            params = self.api.asset_params(order.symbol)
            contract = contract_from_moex_and_finam(
                check_instrument(asset, params, order.symbol, self.account_id))
            expected = ExpectedEntry(
                account_id=self.account_id, order_id=order.order_id,
                symbol=order.symbol, side=order.side,
                quantity=int(draft.payload["quantity"]["value"]),
                price_step=contract.price_step,
            )
        trades = self.api.trades(
            self.account_id, start=start, end=end, limit=limit)
        return journal.reconcile_entry_broker_get(
            key=key, draft=draft, expected=expected,
            expected_client_order_id=draft.payload["client_order_id"],
            stop_trade_tag=stop_trade_tag, account=account,
            orders_response=orders, trades_response=trades,
            start=start, end=end, limit=limit,
        )

    def submit_protective_stop(
        self, *, journal: M15OutboundJournal, key: str, draft: M15Draft,
        broker_position_qty: int, account: dict, orders_response: dict,
        prior_active_broker_stop_id: str | None = None,
    ) -> dict:
        """H1 STOP-first POST transition; never calls it in current no-LIVE mode.

        Durable signed broker position is committed BEFORE transmission.
        Successful POST ACK is ONLY a receipt; independent active SLTP
        broker GET and exact quantity must call reconcile_protective_broker_get.
        An error after the boundary is always UNCERTAIN, never retried.
        """
        if draft.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise M15PrePostRefused("M15_PROTECTIVE_DRAFT_KIND_INVALID")
        self._require_connected()
        from .finam_trading import M15FinamTradingAPI, M15_ORDER_POST_RELEASED
        if M15_ORDER_POST_RELEASED is not True:
            raise M15PrePostRefused("M15_PROTECTIVE_POST_RELEASE_NOT_AUTHORIZED")
        if not isinstance(self.api, M15FinamTradingAPI):
            raise M15ExecutionError("M15_PROTECTIVE_TRADING_CLIENT_INVALID")
        if (not isinstance(journal, M15OutboundJournal)
                or journal.account_hash != self.account_hash
                or journal.path.parent.parent.resolve()
                != self.runtime_root.resolve()):
            raise M15ExecutionError("M15_PROTECTIVE_JOURNAL_IDENTITY_MISMATCH")
        _valid_draft(draft, account_hash=self.account_hash, key=key)
        if (type(broker_position_qty) is not int or broker_position_qty == 0
                or not isinstance(account, dict)):
            raise M15ExecutionError("M15_PROTECTIVE_BROKER_POSITION_INVALID")
        observed = position_quantities(account).get(draft.payload["symbol"], 0)
        if broker_position_qty != observed:
            raise M15ExecutionError("M15_PROTECTIVE_BROKER_POSITION_MISMATCH")
        journal.begin_protective_post_uncertain(
            key=key, draft=draft, account=account,
            orders_response=orders_response,
            prior_active_broker_stop_id=prior_active_broker_stop_id,
        )
        try:
            response = self.api.place_sltp_order(
                self.account_id, dict(draft.payload))
        except Exception as exc:
            raise M15SubmissionUncertain(
                "M15_PROTECTIVE_POST_UNCERTAIN_GET_RECONCILIATION_REQUIRED"
            ) from exc
        if (not isinstance(response, dict)
                or not isinstance(response.get("order_id"), str)
                or not response["order_id"]):
            raise M15SubmissionUncertain(
                "M15_PROTECTIVE_POST_ACK_ORDER_ID_NOT_PROVED")
        return {
            "broker_order_sha256": hashlib.sha256(
                response["order_id"].encode("utf-8")).hexdigest(),
            "post_ack_observed": True,
            "broker_stop_active_confirmed": False,
            "broker_coverage_confirmed": False,
            "live_protection_reconciled": False,
        }

    def submit_emergency_exit(
        self, *, journal: M15OutboundJournal, key: str,
        entry_key: str, stop_key: str, draft: M15Draft,
        account: dict, orders_response: dict,
    ) -> dict:
        """H1 risk-reducing EXIT: durable unknown-before-POST, never resend.

        Dormant while static M15 NO-LIVE and separate POST release are OFF.
        The POST receipt never asserts the position is FLAT; caller must
        re-GET FINAM /account and /orders, then verify/cancel residual SLTP.
        """
        if draft.kind != "EMERGENCY_EXIT":
            raise M15PrePostRefused("M15_EXIT_DRAFT_KIND_INVALID")
        self._require_connected()
        from .finam_trading import M15FinamTradingAPI, M15_ORDER_POST_RELEASED
        if M15_ORDER_POST_RELEASED is not True:
            raise M15PrePostRefused("M15_EXIT_POST_RELEASE_NOT_AUTHORIZED")
        if not isinstance(self.api, M15FinamTradingAPI):
            raise M15ExecutionError("M15_EXIT_TRADING_CLIENT_INVALID")
        if (not isinstance(journal, M15OutboundJournal)
                or journal.account_hash != self.account_hash
                or journal.path.parent.parent.resolve()
                != self.runtime_root.resolve()):
            raise M15ExecutionError("M15_EXIT_JOURNAL_IDENTITY_MISMATCH")
        journal.begin_exit_post_uncertain(
            entry_key=entry_key, stop_key=stop_key, exit_key=key,
            draft=draft, account=account, orders_response=orders_response,
        )
        try:
            receipt = self.api.place_order(self.account_id, dict(draft.payload))
        except Exception as exc:
            raise M15SubmissionUncertain(
                "M15_EXIT_POST_UNCERTAIN_GET_RECONCILIATION_REQUIRED") from exc
        if (not isinstance(receipt, dict)
                or not isinstance(receipt.get("order_id"), str)
                or not receipt["order_id"]):
            raise M15SubmissionUncertain("M15_EXIT_POST_ACK_ORDER_ID_NOT_PROVEN")
        return {
            "broker_order_sha256": hashlib.sha256(
                receipt["order_id"].encode("utf-8")).hexdigest(),
            "post_ack_observed": True,
            "broker_flat_confirmed": False,
            "old_stop_cleanup_confirmed": False,
            "live_close_reconciled": False,
        }

    def cancel_protective_stop_after_flat(
        self, *, journal: M15OutboundJournal, entry_key: str, stop_key: str,
        broker_order_id: str, account: dict, orders_response: dict,
        observed_at: datetime,
    ) -> dict:
        """Riskless residual SLTP DELETE only after exact FINAM FLAT proof.

        Disabled by static M15 freeze and independent order-release switch.
        Successful HTTP DELETE is not a broker-confirmed disappearance; GET
        is mandatory before durable close, no second DELETE on uncertainty.
        """
        self._require_connected()
        from .finam_trading import M15FinamTradingAPI, M15_ORDER_POST_RELEASED
        if M15_ORDER_POST_RELEASED is not True:
            raise M15PrePostRefused("M15_FLAT_CANCEL_RELEASE_NOT_AUTHORIZED")
        if not isinstance(self.api, M15FinamTradingAPI):
            raise M15ExecutionError("M15_FLAT_CANCEL_TRADING_CLIENT_INVALID")
        if (not isinstance(journal, M15OutboundJournal)
                or journal.account_hash != self.account_hash
                or journal.path.parent.parent.resolve()
                != self.runtime_root.resolve()):
            raise M15ExecutionError("M15_FLAT_CANCEL_JOURNAL_IDENTITY_MISMATCH")
        journal.begin_flat_stop_cancel_uncertain(
            entry_key=entry_key, stop_key=stop_key,
            broker_order_id=broker_order_id, account=account,
            orders_response=orders_response, observed_at=observed_at,
        )
        try:
            self.api.cancel_order(self.account_id, broker_order_id)
        except Exception as exc:
            raise M15SubmissionUncertain(
                "M15_FLAT_CANCEL_UNCERTAIN_BROKER_GET_REQUIRED") from exc
        return {
            "cancel_http_receipt_observed": True,
            "broker_stop_inactive_confirmed": False,
            "durable_closed": False,
            "new_entries_authorized": False,
            "live_authorized": False,
        }
