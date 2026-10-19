"""M15-only H1-style execution adapter, staged behind an absolute LIVE gate.

Ported concepts from Stage8 H1 live_execution.py (read-only reference):
exact account-bound authorization, session identity, no retry of uncertain
POST, durable intent BEFORE POST, broker-confirmed risk-reducing requests.

NOT a runnable robot: frozen M15 EXECUTION_STATUS is NOT_LIVE_AUTHORIZED.
Constructing, connecting or calling this adapter cannot submit anything now.
No H1 module/runtime/token/Task is imported or mutated here.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from decimal import Decimal
from fractions import Fraction
from typing import Any

from .broker_fill_readonly import ExpectedEntry, analyze_account_trades
from .broker_snapshot import order_views, position_quantities, unique_order_by_client_id
from .broker_reconcile_gate import assess_entry_evidence
from .grid_risk import ContractAuthority, SizedOrder, TrailingState, initial_stop, project_stop
from .protective_gate import BrokerProtection
from .trailing_gate import PendingTrail, propose_trail
from .spec import INITIAL_STOP_ATR
from .trade_draft_contract import M15OfflineTradeDrafts

from .account_boundary import validate_independent_binding
from .spec import EXECUTION_STATUS, INSTRUMENTS, ROBOT_ID
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
            """)
            tables = {r[0] for r in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if tables != {"metadata", "outbound", "broker_fills"}:
                raise M15ExecutionError("M15_OUTBOUND_SCHEMA_TABLES_INVALID")
            expected = {
                "metadata": ("key", "value"),
                "outbound": ("intent_key", "kind", "symbol", "payload_sha256",
                             "state", "broker_order_sha256"),
                "broker_fills": ("trade_sha256", "intent_key", "broker_order_sha256",
                                 "quantity", "price", "trade_timestamp"),
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
                    "SELECT 1 FROM outbound WHERE symbol=? AND kind='ENTRY' "
                    "AND state IN ('PREPARED','UNCERTAIN','ACK') LIMIT 1",
                    (draft.payload["symbol"],),
                ).fetchone()
                if occupied:
                    raise M15ExecutionError("M15_OUTBOUND_INSTRUMENT_OCCUPIED")
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

    def submit_entry(self, *, journal: M15OutboundJournal, key: str,
                     draft: M15Draft):
        if draft.kind != "ENTRY":
            raise M15PrePostRefused("M15_ENTRY_DRAFT_KIND_INVALID")
        return self._transmit(journal=journal, key=key, draft=draft,
                              send=self.api.place_order)

    def submit_protective_stop(self, *, journal: M15OutboundJournal, key: str,
                               draft: M15Draft, broker_position_qty: int):
        if draft.kind not in {"PROTECTIVE_STOP_INSTALL", "PROTECTIVE_STOP_REPLACE"}:
            raise M15ExecutionError("M15_PROTECTIVE_DRAFT_KIND_INVALID")
        # Real replacement requires an independently observed current active
        # STOP, ACK sequence and tightening-first. The draft alone is NOT proof.
        raise M15PrePostRefused("M15_PROTECTION_BROKER_ACK_GATE_NOT_IMPLEMENTED")

    def submit_emergency_exit(self, *, journal: M15OutboundJournal, key: str,
                              draft: M15Draft, broker_position_qty: int):
        if draft.kind != "EMERGENCY_EXIT":
            raise M15ExecutionError("M15_EXIT_DRAFT_KIND_INVALID")
        # Production emergency exit must be risk-reducing after exact broker
        # reconciliation; cannot be inferred from untrusted supplied quantity.
        raise M15PrePostRefused("M15_EXIT_BROKER_POSITION_GATE_NOT_IMPLEMENTED")

    def cancel_protective_stop_after_flat(self, *, broker_order_id: str,
                                           observed_broker_position_qty: int):
        self._require_connected()
        if type(observed_broker_position_qty) is not int or observed_broker_position_qty != 0:
            raise M15ExecutionError("M15_CANCEL_REQUIRES_BROKER_FLAT")
        # Actual cancelled protection must have a fully reconciled broker
        # exit; current no-live stage has no independent proof of that fact.
        raise M15PrePostRefused("M15_CANCEL_REAL_FLAT_PROOF_NOT_IMPLEMENTED")
