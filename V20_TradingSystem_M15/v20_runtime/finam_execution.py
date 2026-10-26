"""V20-08.1 broker-side adapter using existing, unchanged H1 FINAM readers.

The OFFLINE FakeBroker runner and three Disabled Windows Tasks are NOT replaced.
This module has no order/SLTP/cancel methods, credential store or authorization
writer. In particular it must never be treated as proof of executable LIVE.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlencode

import pandas as pd
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import re
from typing import Any

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, FinamOrderRejected, BARS_PATH_TEMPLATE
from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.execution_grid import require_on_grid, initial_projection, project_stop
from TradingSystemLab.stage8_robot.finam_fill_price_readonly import (
    Target, analyze_history,
)
from TradingSystemLab.stage8_robot.margin import (
    directional_initial_margin,
    parse_rest_decimal_value_object,
    portfolio_authority,
)
from TradingSystemLab.stage8_robot.production_broker_state import (
    BrokerOrderView, order_views, position_quantities, unique_order_by_client_id,
    _validate_production_sltp,
)
from TradingSystemLab.stage8_robot.production_runtime import _load_registry, RuntimeAction

from TradingSystemLab.stage8_robot.live_execution import AuthorizedFinamProductionTransport
from TradingSystemLab.stage8_robot.protective_stop_contract import percent_position_stop_payload
from .account_risk import AccountAuthority, RiskReservation, reserve_entry, revalue_fill
from .h1_state_journal import ROBOT_STRATEGIES, IsolatedReferenceJournal
from .offline_planner import N4, FrozenSignal, ProposedEntry, OfflinePlanner, STEP
from .frozen_adapter import validate_completed_history, completed_signal, _frozen_immutable_features


ACTIVE_STATUSES = frozenset({"ACCOUNT_ACTIVE", "ACCOUNT_STATUS_ACTIVE"})


class V20FinamBlocked(RuntimeError):
    """No implicit cross-account, estimated or unverified FINAM authority."""


@dataclass(frozen=True)
class LiveAccountSnapshot:
    robot_id: str
    account_hash: str
    observed_at: datetime
    realized_equity: Decimal
    available_cash: Decimal
    positions: dict[str, int]
    orders: tuple[BrokerOrderView, ...]

    @property
    def clean(self) -> bool:
        return not self.positions and not any(order.active for order in self.orders)


class V20FinamReadAdapter:
    """One instance per FINAM account; all network traffic uses H1 FinamAPI.

    Its only network operations are session auth, account GET, orders GET and
    four N4 account-scoped asset-params GETs. Before actual LIVE, V20 must
    separately implement durable order intents and user-scoped authorization.
    """

    def __init__(
        self, *, api: FinamAPI, robot_id: str, account_id: str,
        expected_account_hash: str,
    ):
        if robot_id not in ROBOT_STRATEGIES:
            raise V20FinamBlocked("UNKNOWN_V20_ROBOT")
        if (not isinstance(account_id, str)
                or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account_id)
                or not re.fullmatch(r"[0-9a-f]{64}", str(expected_account_hash))
                or hashlib.sha256(account_id.encode("utf-8")).hexdigest() != expected_account_hash):
            raise V20FinamBlocked("ACCOUNT_IDENTITY_MISMATCH")
        if not isinstance(api, FinamAPI):
            raise V20FinamBlocked("H1_FINAM_API_REQUIRED")
        self.api = api
        self.robot_id = robot_id
        self.account_id = account_id
        self.account_hash = expected_account_hash
        self._bound = False

    def authenticate(self) -> None:
        self._bound = False
        self.api.create_session()
        details = self.api.session_details()
        ids = details.get("account_ids") if isinstance(details, dict) else None
        if (not isinstance(ids, list) or ids.count(self.account_id) != 1
                or details.get("readonly") is not False):
            raise V20FinamBlocked("EXACT_TRADING_TOKEN_SCOPE_REQUIRED")
        self._bound = True

    def _require_bound(self) -> None:
        if not self._bound:
            raise V20FinamBlocked("TRADING_SESSION_NOT_BOUND")

    def snapshot(self, *, now: datetime) -> LiveAccountSnapshot:
        self._require_bound()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise V20FinamBlocked("UTC_OBSERVATION_REQUIRED")
        raw = self.api.account(self.account_id)
        if (not isinstance(raw, dict) or raw.get("account_id") != self.account_id
                or raw.get("status") not in ACTIVE_STATUSES):
            raise V20FinamBlocked("FINAM_ACCOUNT_RESPONSE_INVALID")
        positions = position_quantities(raw)
        orders = order_views(self.api.orders(self.account_id))
        known = {x["finam_symbol"] for x in _load_registry().values()}
        if any(symbol not in known for symbol in positions):
            raise V20FinamBlocked("FOREIGN_ACCOUNT_POSITION")
        if any(order.active and order.symbol not in known for order in orders):
            raise V20FinamBlocked("UNKNOWN_ACTIVE_ACCOUNT_ORDER")
        funds = portfolio_authority(raw)
        realized = (parse_rest_decimal_value_object(raw.get("equity"))
                    - parse_rest_decimal_value_object(raw.get("unrealized_profit")))
        if realized <= 0 or funds.available_cash < 0:
            raise V20FinamBlocked("BROKER_MONEY_NOT_VALID")
        return LiveAccountSnapshot(
            self.robot_id, self.account_hash, now.astimezone(timezone.utc),
            realized, funds.available_cash, positions, tuple(orders),
        )

    def authority(
        self, snapshot: LiveAccountSnapshot, *, symbol: str, direction: str,
        roundtrip_cost_per_contract: Decimal, now: datetime,
    ) -> AccountAuthority:
        """Refresh directional FINAM GO and use H1 R15/grid/lot semantics.

        Cost is an explicit broker-tariff input, never offline C1 or invented
        zero. The caller retains the responsibility to prove its source.
        """
        self._require_bound()
        if (symbol not in N4 or direction not in {"LONG", "SHORT"}
                or not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.robot_id != self.robot_id or snapshot.account_hash != self.account_hash
                or not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise V20FinamBlocked("ACCOUNT_AUTHORITY_SCOPE_INVALID")
        elapsed = now.astimezone(timezone.utc) - snapshot.observed_at
        if not timedelta(0) <= elapsed <= timedelta(seconds=60):
            raise V20FinamBlocked("STALE_FINAM_ACCOUNT_SNAPSHOT")
        try:
            cost = Decimal(str(roundtrip_cost_per_contract))
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise V20FinamBlocked("BROKER_TARIFF_INVALID") from exc
        if not cost.is_finite() or cost <= 0:
            raise V20FinamBlocked("BROKER_TARIFF_REQUIRED")
        registry = _load_registry()[symbol]
        params = self.api.asset_params(registry["finam_symbol"], self.account_id)
        go = directional_initial_margin(params, direction)
        return AccountAuthority(
            account_id=self.account_id,
            realized_equity=snapshot.realized_equity,
            available_cash=snapshot.available_cash,
            price_step=Decimal(registry["price_step"]),
            tick_value=Decimal(registry["tick_value"]),
            initial_margin=go,
            trade_lot_size=int(registry["quantity_granularity"]),
            roundtrip_cost_per_contract=cost,
        )

    def inspect_entry_fills(
        self, snapshot: LiveAccountSnapshot, *, entry_key: str, symbol: str,
        direction: str, requested_quantity: int, submitted_at: datetime,
        now: datetime,
    ) -> dict[str, Any]:
        """Reuse H1's exact order-linked FINAM fill parser (GET-only).

        Diagnostic evidence, NOT a production handoff or a POST permission.
        Complete-history proof requires the H1 response row count below limit.
        Broker order ACK alone is never fill/price proof.
        """
        self._fresh(snapshot, now)
        if (symbol not in N4 or direction not in {"LONG", "SHORT"}
                or not isinstance(entry_key, str) or not entry_key.startswith(
                    "v20:" + self.robot_id + ":" + self.account_hash[:16] + ":"
                )
                or type(requested_quantity) is not int or requested_quantity <= 0
                or not isinstance(submitted_at, datetime) or submitted_at.tzinfo is None):
            raise V20FinamBlocked("ENTRY_FILL_IDENTITY_INVALID")
        order = unique_order_by_client_id(
            list(snapshot.orders), compact_client_order_id(entry_key),
        )
        row = _load_registry()[symbol]
        side = "SIDE_BUY" if direction == "LONG" else "SIDE_SELL"
        if (order is None or order.kind != "REGULAR"
                or order.symbol != row["finam_symbol"] or order.side != side
                or order.request.get("quantity") != {"value": str(requested_quantity)}):
            raise V20FinamBlocked("ENTRY_ORDER_BROKER_PROOF_MISSING")
        start = submitted_at.astimezone(timezone.utc)
        end = now.astimezone(timezone.utc)
        if not timedelta(0) < end - start <= timedelta(days=7):
            raise V20FinamBlocked("ENTRY_FILL_INTERVAL_INVALID")
        limit = 1000
        begin_text, end_text = start.isoformat(), end.isoformat()
        response = self.api.trades(
            self.account_id, start=begin_text, end=end_text, limit=limit,
        )
        target = Target(
            self.account_id, entry_key, order.order_id, row["finam_symbol"],
            side, requested_quantity, Decimal(row["price_step"]),
        )
        return analyze_history(response, target, begin_text, end_text, limit)

    def inspect_protective_stop(
        self, snapshot: LiveAccountSnapshot, *, entry_key: str, symbol: str,
        direction: str, stop_price: Decimal, now: datetime,
    ) -> BrokerOrderView:
        """Match current active 100%-of-position SLTP against H1 contract."""
        self._fresh(snapshot, now)
        if (symbol not in N4 or direction not in {"LONG", "SHORT"}
                or not isinstance(entry_key, str) or not entry_key.startswith(
                    "v20:" + self.robot_id + ":" + self.account_hash[:16] + ":"
                )):
            raise V20FinamBlocked("STOP_TRADE_IDENTITY_INVALID")
        row = _load_registry()[symbol]
        price = Decimal(str(stop_price))
        require_on_grid(price, Decimal(row["price_step"]))
        finam_symbol = row["finam_symbol"]
        quantity = snapshot.positions.get(finam_symbol, 0)
        if type(quantity) is not int or quantity == 0 or (
            (quantity > 0) != (direction == "LONG")
        ):
            raise V20FinamBlocked("STOP_POSITION_BROKER_PROOF_MISSING")
        stop_key = entry_key + ":stop"
        candidate = unique_order_by_client_id(
            list(snapshot.orders), compact_client_order_id(stop_key),
        )
        active_stops = [
            order for order in snapshot.orders
            if order.active and order.kind == "SLTP" and order.symbol == finam_symbol
        ]
        if (candidate is None or not candidate.active
                or len(active_stops) != 1 or active_stops[0] != candidate
                or candidate.symbol != finam_symbol
                or candidate.side != ("SIDE_SELL" if direction == "LONG" else "SIDE_BUY")
                or candidate.comment != stop_key
                or Decimal(candidate.request.get("sl_price", {}).get("value", "0")) != price):
            raise V20FinamBlocked("STOP_NOT_EXACTLY_ACTIVE")
        _validate_production_sltp(candidate)
        return candidate

    def _fresh(self, snapshot: LiveAccountSnapshot, now: datetime) -> None:
        self._require_bound()
        if (not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.robot_id != self.robot_id
                or snapshot.account_hash != self.account_hash
                or not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None):
            raise V20FinamBlocked("BROKER_OBSERVATION_SCOPE_INVALID")
        age = now.astimezone(timezone.utc) - snapshot.observed_at
        if not timedelta(0) <= age <= timedelta(seconds=60):
            raise V20FinamBlocked("BROKER_OBSERVATION_STALE")


class V20TradeJournal(IsolatedReferenceJournal):
    """H1 StateStore/InstanceLock reused for isolated V20 real-order *intents*.

    The journal is not a sender.  Existing offline FakeBroker databases are
    neither read nor migrated.  A persisted entry can never, by itself,
    authorize an order or SLTP POST.
    """
    # Intel Stage07 owns C:\\V20Lab\\robots\\<slug> (config/state/secrets/logs).
    # Do not create a second real ledger at C:\\V20Lab\\<slug>.
    instance_parent = "robots"
    state_file = "v20-real-intents.sqlite3"
    schema = "v20.h1_state_store.real_intents.v1"
    mode = "V20_PRETRADE_UNAUTHORIZED"

    def record_reference(self, *args, **kwargs):
        raise V20FinamBlocked("OFFLINE_REFERENCE_FORBIDDEN_IN_REAL_JOURNAL")

    def preview_entry_key(self, entry: ProposedEntry) -> str:
        """Exactly the H1 idempotency key used by prepare_entry; no writes."""
        if (not isinstance(entry, ProposedEntry)
                or entry.symbol not in N4
                or entry.direction not in {"LONG", "SHORT"}
                or not hasattr(entry.entry_bar_open, "tzinfo")
                or entry.entry_bar_open.tzinfo is not None):
            raise V20FinamBlocked("TRIAL_PREVIEW_KEY_INVALID")
        return ("v20:" + self.robot_id + ":" + self.account_hash[:16] + ":" +
                compact_client_order_id(
                    f"{entry.symbol}:{entry.entry_bar_open.isoformat()}:{entry.direction}"
                )[2:])

    def prepare_entry(self, *, signal: FrozenSignal, entry: ProposedEntry,
                      authority: AccountAuthority, snapshot: LiveAccountSnapshot) -> str:
        """Atomic H1 risk reservation, once-per-session quota and immutable wire."""
        if (not isinstance(signal, FrozenSignal) or not isinstance(entry, ProposedEntry)
                or not isinstance(authority, AccountAuthority)
                or not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.robot_id != self.robot_id
                or snapshot.account_hash != self.account_hash
                or hashlib.sha256(authority.account_id.encode("utf-8")).hexdigest() != self.account_hash):
            raise V20FinamBlocked("PRETRADE_ACCOUNT_AUTHORITY_MISMATCH")
        if (authority.realized_equity != snapshot.realized_equity
                or authority.available_cash != snapshot.available_cash):
            raise V20FinamBlocked("BROKER_MONEY_SNAPSHOT_MISMATCH")
        if (snapshot.observed_at.tzinfo is None
                or not timedelta(0) <= datetime.now(timezone.utc) - snapshot.observed_at
                <= timedelta(seconds=60)):
            raise V20FinamBlocked("PRETRADE_BROKER_SNAPSHOT_STALE")
        if (signal.strategy != self.strategy or entry.strategy != self.strategy
                or signal.symbol not in N4 or entry.symbol != signal.symbol
                or signal.side not in (-1, 1)
                or entry.direction != ("LONG" if signal.side == 1 else "SHORT")
                or entry.entry_bar_open != signal.signal_bar_open + STEP
                or entry.mode != "OFFLINE_REFERENCE_NOT_ORDER"
                or type(entry.quantity) is not int or entry.quantity <= 0):
            raise V20FinamBlocked("FROZEN_NEXT_OPEN_ENTRY_INVALID")
        registry = _load_registry()[entry.symbol]
        step = authority.price_step
        if (authority.price_step != Decimal(registry["price_step"])
                or authority.tick_value != Decimal(registry["tick_value"])
                or authority.trade_lot_size != int(registry["quantity_granularity"])):
            raise V20FinamBlocked("FROZEN_N4_ECONOMICS_MISMATCH")
        stop, _ = initial_projection(
            entry.direction, entry.reference_entry,
            Decimal(entry.reference_entry) - Decimal(signal.side) * 2 * signal.atr14, step,
        )
        if entry.initial_stop != stop:
            raise V20FinamBlocked("FROZEN_2ATR_EXECUTABLE_STOP_MISMATCH")
        # Before durable ownership/recovery is connected, only a demonstrably
        # clean FINAM account may be seeded into this non-ordering ledger.
        if not snapshot.clean:
            raise V20FinamBlocked("NONFLAT_BROKER_BOOTSTRAP_FORBIDDEN")
        day = OfflinePlanner._session_key(entry.entry_bar_open).isoformat()
        key = self.preview_entry_key(entry)
        with self.store.transaction():
            if self.store.get("execution_halt"):
                raise V20FinamBlocked("JOURNAL_HALTED")
            previous = self.store.intent(key)
            if previous is not None:
                raise V20FinamBlocked("ENTRY_INTENT_ALREADY_PERSISTED_NO_RETRY")
            index = self.store.get("session_entries", {})
            rows = index.get(day, [])
            if len(rows) >= 2:
                raise V20FinamBlocked("TWO_ENTRIES_PER_SESSION")
            for old_key in rows:
                old = self.store.intent(old_key)
                if old is None or not isinstance(old["payload"], dict):
                    raise V20FinamBlocked("DURABLE_SESSION_INDEX_INVALID")
                if old["payload"].get("symbol") == entry.symbol:
                    raise V20FinamBlocked("ONE_ENTRY_PER_SYMBOL_PER_SESSION")
            risks = self.store.get("risk_reservations", {})
            reservations = [RiskReservation.restore(record) for record in risks.values()]
            reservation = reserve_entry(
                authority=authority, entry_key=key, symbol=entry.symbol,
                direction=entry.direction, entry=entry.reference_entry,
                atr14=signal.atr14, planned_max_quantity=entry.quantity,
                current_reservations=reservations,
            )
            if reservation.initial_stop != entry.initial_stop:
                raise V20FinamBlocked("RESERVED_EXECUTABLE_STOP_CHANGED")
            action = RuntimeAction(
                "ENTRY", key, entry.symbol, registry["finam_symbol"],
                entry.direction, reservation.quantity, key, None,
                entry.reference_entry, entry.initial_stop,
                reservation.quantity if entry.direction == "LONG" else -reservation.quantity,
            )
            wire = AuthorizedFinamProductionTransport._market_payload(
                action, exit_order=False,
            )
            payload = {
                "kind": "ENTRY", "mode": "PRETRADE_NOT_AUTHORIZED",
                "robot_id": self.robot_id, "account_sha256": self.account_hash,
                "symbol": entry.symbol, "direction": entry.direction,
                "entry_at": entry.entry_bar_open.isoformat(),
                "finam_symbol": registry["finam_symbol"],
                "quantity": reservation.quantity,
                "reference_entry": str(entry.reference_entry),
                "initial_stop": str(entry.initial_stop),
                "atr14": str(signal.atr14), "wire": wire,
            }
            if not self.store.persist_intent(key, payload):
                raise V20FinamBlocked("DUPLICATE_DURABLE_ENTRY_INTENT")
            risks[key] = reservation.record()
            self.store.put("risk_reservations", risks)
            index[day] = rows + [key]
            self.store.put("session_entries", index)
        return key

    def record_submission_boundary(self, key: str, *, at: datetime | None = None) -> None:
        """Pre-POST checkpoint with durable time for H1 order-linked history.

        This function does NOT submit. Future V20 order transport must call
        this before any network POST, after separate user authorization.
        """
        observed = at if at is not None else datetime.now(timezone.utc)
        if (not isinstance(observed, datetime) or observed.tzinfo is None
                or observed.utcoffset() is None):
            raise V20FinamBlocked("POST_TIME_AUTHORITY_INVALID")
        observed_utc = observed.astimezone(timezone.utc)
        if not timedelta(0) <= datetime.now(timezone.utc) - observed_utc <= timedelta(seconds=60):
            raise V20FinamBlocked("POST_TIME_STALE_OR_FUTURE")
        with self.store.transaction():
            intent = self.store.intent(key)
            if (intent is None or intent["payload"].get("mode") != "PRETRADE_NOT_AUTHORIZED"
                    or intent["status"] != "INTENT_PERSISTED"):
                raise V20FinamBlocked("POST_BOUNDARY_ALREADY_CONSUMED_OR_MISSING")
            self.store.put("entry_submission:" + key, {
                "account_sha256": self.account_hash,
                "submitted_at": observed_utc.isoformat(),
            })
            self.store.transition_intent(key, "UNCERTAIN")
            self.store.put("execution_halt", "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION")

    def reconcile_order(self, *, key: str, snapshot: LiveAccountSnapshot) -> str:
        """Read-side H1 order proof; never retransmit a missing/unknown POST."""
        if (not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.account_hash != self.account_hash
                or snapshot.robot_id != self.robot_id):
            raise V20FinamBlocked("RECONCILIATION_ACCOUNT_MISMATCH")
        intent = self.store.intent(key)
        if intent is None or intent["payload"].get("mode") != "PRETRADE_NOT_AUTHORIZED":
            raise V20FinamBlocked("RECONCILIATION_INTENT_UNKNOWN")
        orders = list(snapshot.orders)
        found = unique_order_by_client_id(orders, compact_client_order_id(key))
        if found is None:
            if intent["status"] == "INTENT_PERSISTED":
                return "PREPARED_ONLY_NO_POST"
            self.store.put("execution_halt", "UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION")
            raise V20FinamBlocked("UNKNOWN_POST_NO_RETRANSMIT")
        wire = intent["payload"]["wire"]
        if (found.kind != "REGULAR"
                or found.symbol != wire["symbol"] or found.side != wire["side"]
                or found.request.get("quantity") != wire["quantity"]
                or found.request.get("client_order_id") != wire["client_order_id"]):
            self.store.put("execution_halt", "BROKER_ORDER_MISMATCH")
            raise V20FinamBlocked("BROKER_ORDER_MISMATCH")
        if intent["status"] == "INTENT_PERSISTED":
            # An order that appeared without the local pre-POST checkpoint is
            # not silently adopted. Operator reconciliation is mandatory.
            self.store.put("execution_halt", "UNEXPECTED_ORDER_WITHOUT_POST_CHECKPOINT")
            raise V20FinamBlocked("UNEXPECTED_ORDER_WITHOUT_POST_CHECKPOINT")
        # Repeated H1 /orders observations cannot demote a partially filled
        # or already reconciled durable entry to the earlier ACK state.
        if intent["broker_order_id"] not in (None, found.order_id):
            self.store.put("execution_halt", "BROKER_ORDER_ID_CHANGED")
            raise V20FinamBlocked("BROKER_ORDER_ID_CHANGED")
        if intent["status"] in {"PARTIAL_FILL", "FILL", "RECONCILED"}:
            return "BROKER_ORDER_ALREADY_" + intent["status"] + "_NO_RETRANSMIT"
        if intent["status"] not in {"UNCERTAIN", "SUBMITTED", "ACK"}:
            self.store.put("execution_halt", "BROKER_INTENT_STATUS_INVALID")
            raise V20FinamBlocked("BROKER_INTENT_STATUS_INVALID")
        if intent["status"] != "ACK":
            self.store.transition_intent(key, "ACK", found.order_id)
        # Broker ACK does not prove fill price, quantity or stop protection.
        return "BROKER_ACK_NO_FILL_OR_SLTP_PROOF"

    def observe_protected_entry(
        self, *, key: str, reader: V20FinamReadAdapter,
        snapshot: LiveAccountSnapshot, now: datetime,
    ) -> dict[str, Any]:
        """Persist order-linked fill and active 100% stop *observations* only.

        FINAM must prove every observed contract via H1 trade-history parsing,
        and the current SLTP must match VWAP +/- frozen 2*ATR14 on the tick
        grid. No method transmits an order or changes the active stop. Fees
        remain a budget estimate until separate FINAM fee authority arrives.
        """
        if (not isinstance(reader, V20FinamReadAdapter)
                or reader.account_hash != self.account_hash
                or reader.robot_id != self.robot_id
                or not isinstance(snapshot, LiveAccountSnapshot)
                or snapshot.account_hash != self.account_hash
                or snapshot.robot_id != self.robot_id):
            raise V20FinamBlocked("PROTECTED_FILL_ACCOUNT_IDENTITY_MISMATCH")
        reader._fresh(snapshot, now)
        intent = self.store.intent(key)
        if (intent is None or intent["payload"].get("kind") != "ENTRY"
                or intent["payload"].get("mode") != "PRETRADE_NOT_AUTHORIZED"
                or intent["status"] not in {"ACK", "PARTIAL_FILL", "FILL", "RECONCILED"}
                or not intent["broker_order_id"]):
            raise V20FinamBlocked("BROKER_ACK_RECONCILIATION_REQUIRED")
        submission = self.store.get("entry_submission:" + key)
        if (not isinstance(submission, dict)
                or submission.get("account_sha256") != self.account_hash
                or not isinstance(submission.get("submitted_at"), str)):
            raise V20FinamBlocked("DURABLE_SUBMISSION_TIME_MISSING")
        payload = intent["payload"]
        reservation_data = self.store.get("risk_reservations", {}).get(key)
        reservation = RiskReservation.restore(reservation_data)
        symbol = payload["symbol"]
        direction = payload["direction"]
        observed_at = datetime.fromisoformat(submission["submitted_at"])
        try:
            history = reader.inspect_entry_fills(
                snapshot, entry_key=key, symbol=symbol,
                direction=direction, requested_quantity=reservation.quantity,
                submitted_at=observed_at, now=now,
            )
        except Exception:
            self.store.put("execution_halt", "ENTRY_FILL_HISTORY_UNVERIFIED")
            raise
        facts = history.get("matched_unique_fills", [])
        filled = history.get("matched_quantity")
        if (history.get("authority_scope") !=
                "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF"
                or type(filled) is not int or filled <= 0
                or not isinstance(facts, list) or not facts
                or filled != sum(row["quantity"] for row in facts)):
            self.store.put("execution_halt", "ENTRY_FILL_HISTORY_UNVERIFIED")
            raise V20FinamBlocked("ENTRY_FILL_HISTORY_INCOMPLETE")
        registry = _load_registry()[symbol]
        finam_symbol = registry["finam_symbol"]
        expected_position = filled if direction == "LONG" else -filled
        if snapshot.positions.get(finam_symbol, 0) != expected_position:
            self.store.put("execution_halt", "ENTRY_BROKER_POSITION_FILL_MISMATCH")
            raise V20FinamBlocked("ENTRY_BROKER_POSITION_FILL_MISMATCH")
        matched_order = unique_order_by_client_id(
            list(snapshot.orders), compact_client_order_id(key),
        )
        if (matched_order is None or matched_order.order_id != intent["broker_order_id"]
                or matched_order.kind != "REGULAR"
                or matched_order.symbol != finam_symbol):
            self.store.put("execution_halt", "ENTRY_ORDER_IDENTITY_CHANGED")
            raise V20FinamBlocked("ENTRY_ORDER_IDENTITY_CHANGED")
        exact_average = (sum(
            (int(fact["quantity"]) * Fraction(fact["price"]) for fact in facts),
            Fraction(0),
        ) / filled)
        side = 1 if direction == "LONG" else -1
        projected_stop = project_stop(
            direction, exact_average - side * 2 * Fraction(reservation.atr14),
            reservation.price_step,
        )
        try:
            stop = reader.inspect_protective_stop(
                snapshot, entry_key=key, symbol=symbol, direction=direction,
                stop_price=projected_stop, now=now,
            )
        except Exception:
            self.store.put("execution_halt", "OPEN_POSITION_PROTECTION_UNVERIFIED")
            raise
        # No actual broker fee in H1 /trades diagnostic; the *reserved* roundtrip
        # amount is the conservative provisional cost, not a verified fee.
        assessment = revalue_fill(
            reservation,
            [(int(f["quantity"]), f["price"], "0") for f in facts],
            installed_stop=projected_stop,
            other_reserved_risk=sum(
                (RiskReservation.restore(r).reserved_risk for k, r in
                 self.store.get("risk_reservations", {}).items() if k != key),
                Decimal(0),
            ),
        )
        with self.store.transaction():
            # H1's strict SQLite fill identity detects changed data on restart.
            durable = self.store.fills_for_order(matched_order.order_id)
            known = {f["fill_id"] for f in durable}
            newly_seen = set()
            for fact in facts:
                fid = ("finam:" + self.account_hash + ":" + fact["trade_id_sha256"])
                newly_seen.add(fid)
                entry_fill = {
                    "fill_id": fid, "broker_order_id": matched_order.order_id,
                    "trade_id": key, "entry_key": key,
                    "quantity": str(fact["quantity"]), "price": fact["price"],
                    "timestamp": str(fact["utc_seconds"]) + ":" + str(fact["nanoseconds"]),
                    "broker_trade_id_sha256": fact["trade_id_sha256"],
                    "account_sha256": self.account_hash,
                    "fees": "NOT_YET_CONFIRMED_BY_FINAM",
                }
                self.store.persist_fill(entry_fill, strict=True)
            if not known.issubset(newly_seen):
                raise V20FinamBlocked("HISTORICAL_FINAM_FILL_DISAPPEARED")
            observation = {
                "account_sha256": self.account_hash,
                "broker_order_id": matched_order.order_id,
                "broker_stop_id": stop.order_id,
                "fill_set_sha256": history["fill_set_sha256"],
                "filled_quantity": filled, "average_exact": str(exact_average),
                "installed_stop": str(projected_stop),
                "broker_stop_percent": "100",
                "risk_assessment": assessment,
                "fees_status": "BUDGETED_ONLY_NOT_ACTUAL",
                "observed_at_utc": now.astimezone(timezone.utc).isoformat(),
            }
            self.store.put("protected_fill:" + key, observation)
            if matched_order.status in {"FILLED", "EXECUTED"}:
                if filled != reservation.quantity:
                    raise V20FinamBlocked("TERMINAL_ENTRY_FILL_QUANTITY_MISMATCH")
                self.store.transition_intent(key, "RECONCILED", matched_order.order_id)
            else:
                self.store.transition_intent(key, "PARTIAL_FILL", matched_order.order_id)
            self.store.put(
                "execution_halt",
                assessment["reason"] if assessment["status"] != "PASS"
                else "ACTUAL_FINAM_FEE_AUTHORITY_PENDING",
            )
        return observation

class V20SingleTradeTransport:
    """08.1 only: reuse H1 FINAM POSTs, strictly gated to an individual trial.

    This is NOT wired to any Windows Task or installed LIVE runner. There is
    deliberately no permit creator or automatic permission escalation.
    Possession of an API token, a clean account or a prepared SQLite intent
    alone cannot enable any POST. 08.2 requires separate operator approval.
    """

    def __init__(self, *, journal: V20TradeJournal, reader: V20FinamReadAdapter,
                 accepted_commit: str, trial_permit_path: Path | None = None):
        if (not isinstance(journal, V20TradeJournal)
                or not isinstance(reader, V20FinamReadAdapter)
                or journal.robot_id != reader.robot_id
                or journal.account_hash != reader.account_hash
                or not re.fullmatch(r"[0-9a-f]{40}", str(accepted_commit))):
            raise V20FinamBlocked("TRIAL_TRANSPORT_ACCOUNT_OR_COMMIT_INVALID")
        self.journal = journal
        self.reader = reader
        self.accepted_commit = accepted_commit
        self.trial_permit_path = trial_permit_path

    def _permit(self, *, key: str, kind: str) -> dict:
        """Validate a separately supplied narrow trial approval, never create it."""
        path = self.trial_permit_path
        authorized = self.journal.instance_root / "safety" / "v20-single-trial-approval.json"
        if (path is None or Path(path).resolve(strict=False) != authorized.resolve(strict=False)
                or not authorized.is_file() or authorized.is_symlink()
                or authorized.parent.is_symlink()):
            raise V20FinamBlocked("SINGLE_TRIAL_EXPLICIT_AUTHORIZATION_MISSING")
        try:
            approval = json.loads(authorized.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            raise V20FinamBlocked("SINGLE_TRIAL_AUTHORIZATION_INVALID") from None
        expected = {
            "schema": "v20.08.2.single_trial.v1",
            "scope": "ONE_SPECIFIC_APPROVED_TRIAL",
            "source_commit": self.accepted_commit,
            "robot_id": self.journal.robot_id,
            "account_sha256": self.journal.account_hash,
            "entry_key": key,
        }
        if (not isinstance(approval, dict)
                or any(approval.get(k) != v for k, v in expected.items())
                or approval.get("authorized_operations") != ["ENTRY", "PROTECTIVE_STOP", "FROZEN_EXIT"]
                or approval.get("explicit_owner_approval") is not True
                or not isinstance(approval.get("instrument"), str)
                or approval["instrument"] not in N4
                or approval.get("direction") not in {"LONG", "SHORT"}
                or type(approval.get("max_quantity")) is not int
                or approval["max_quantity"] < 1):
            raise V20FinamBlocked("SINGLE_TRIAL_EXPLICIT_AUTHORIZATION_MISSING")
        if kind not in approval["authorized_operations"]:
            raise V20FinamBlocked("TRIAL_OPERATION_NOT_APPROVED")
        if (self.journal.store.get("trial_authority_consumed")
                not in (None, key)):
            raise V20FinamBlocked("TRIAL_AUTHORITY_ALREADY_USED")
        return approval

    def _entry(self, key: str, *, snapshot: LiveAccountSnapshot, now: datetime):
        self.reader._fresh(snapshot, now)
        current = self.reader.snapshot(now=now)
        if (not snapshot.clean or not current.clean
                or current.realized_equity != snapshot.realized_equity
                or current.available_cash != snapshot.available_cash):
            raise V20FinamBlocked("TRIAL_ACCOUNT_NOT_FLAT_OR_MONEY_CHANGED")
        if self.journal.store.get("execution_halt") is not None:
            raise V20FinamBlocked("TRIAL_JOURNAL_HALTED")
        approval = self._permit(key=key, kind="ENTRY")
        row = self.journal.store.intent(key)
        if (row is None or row["status"] != "INTENT_PERSISTED"
                or row["payload"].get("mode") != "PRETRADE_NOT_AUTHORIZED"):
            raise V20FinamBlocked("TRIAL_ENTRY_NOT_PREPARED")
        payload = row["payload"]
        if (payload["symbol"] != approval["instrument"]
                or payload["direction"] != approval["direction"]
                or payload["quantity"] > approval["max_quantity"]
                or len(self.journal.store.all_intents()) != 1):
            raise V20FinamBlocked("TRIAL_SCOPE_NOT_EXACT")
        entry_open = datetime.fromisoformat(payload["entry_at"])
        if entry_open.tzinfo is not None or now.tzinfo is None:
            raise V20FinamBlocked("TRIAL_NEXT_OPEN_TIME_INVALID")
        expected_utc = entry_open.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        elapsed = now.astimezone(timezone.utc) - expected_utc
        if not timedelta(0) <= elapsed <= timedelta(seconds=60):
            raise V20FinamBlocked("TRIAL_NEXT_OPEN_EXPIRED_OR_FUTURE")
        reservation = RiskReservation.restore(
            self.journal.store.get("risk_reservations", {}).get(key),
        )
        try:
            approved_risk = Decimal(str(approval.get("max_risk_rub")))
        except (ValueError, ArithmeticError, TypeError):
            raise V20FinamBlocked("TRIAL_APPROVED_RISK_INVALID") from None
        if (not approved_risk.is_finite() or approved_risk <= 0
                or reservation.reserved_risk > approved_risk):
            raise V20FinamBlocked("TRIAL_RISK_EXCEEDS_APPROVAL")
        return payload

    def submit_entry_once(self, *, key: str, snapshot: LiveAccountSnapshot,
                          now: datetime) -> str:
        """One H1 market POST, after durable UNCERTAIN checkpoint. Never retry."""
        payload = self._entry(key, snapshot=snapshot, now=now)
        # Preparation checked ARMED, but a separate operator may HALT between
        # durable intent creation and this final irreversible market POST.
        # Re-read the V20 instance's own H1 kill switch immediately before
        # marking the one-shot trial authority consumed. Fail closed on loss.
        from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch
        switch, switch_error = load_kill_switch(self.journal.instance_root)
        if (switch_error or not isinstance(switch, dict)
                or switch.get("state") != "ARMED"):
            raise V20FinamBlocked("TRIAL_ENTRY_V20_KILL_SWITCH_NOT_ARMED")
        # The caller's 'now' may be a few FINAM roundtrips old. Recheck the
        # ACTUAL wall clock directly before the irreversible one-shot POST.
        entry_open = datetime.fromisoformat(payload["entry_at"])
        actual_post_time = datetime.now(timezone.utc)
        due = entry_open.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        if not timedelta(0) <= actual_post_time-due <= timedelta(seconds=60):
            raise V20FinamBlocked("TRIAL_ENTRY_ACTUAL_NEXT_OPEN_EXPIRED")
        with self.journal.store.transaction():
            if self.journal.store.get("trial_authority_consumed") is not None:
                raise V20FinamBlocked("TRIAL_ALREADY_CONSUMED")
            self.journal.store.put("trial_authority_consumed", key)
            self.journal.record_submission_boundary(key, at=now)
        try:
            ack = self.reader.api.place_order(self.reader.account_id, payload["wire"])
        except FinamOrderRejected:
            self.journal.store.transition_intent(key, "REJECTED")
            # Even a terminal rejection requires an operator before rearming.
            raise
        except BaseException:
            # No retry; unknown post result remains UNCERTAIN/HALTED in SQLite.
            raise
        oid = ack.get("order_id") if isinstance(ack, dict) else None
        if not isinstance(oid, str) or not oid:
            raise V20FinamBlocked("TRIAL_ENTRY_ACK_UNVERIFIED")
        self.journal.store.transition_intent(key, "ACK", oid)
        return oid

    def submit_protection_once(self, *, key: str, snapshot: LiveAccountSnapshot,
                               stop_price: Decimal, now: datetime) -> str:
        """Use H1 100%-SLTP payload; persist intent BEFORE the only stop POST.

        This risk-reducing operation deliberately remains possible when the
        trial entry left the new-entry gate HALTED. An unknown stop result
        never creates an automatic second stop.
        """
        self.reader._fresh(snapshot, now)
        current = self.reader.snapshot(now=now)
        if current.positions != snapshot.positions:
            raise V20FinamBlocked("STOP_BROKER_POSITION_CHANGED")
        approval = self._permit(key=key, kind="PROTECTIVE_STOP")
        entry = self.journal.store.intent(key)
        if (entry is None or entry["status"] not in
                {"ACK", "PARTIAL_FILL", "FILL", "RECONCILED"}
                or not entry["broker_order_id"]):
            raise V20FinamBlocked("STOP_ENTRY_ORDER_UNVERIFIED")
        payload = entry["payload"]
        if (payload["symbol"] != approval["instrument"]
                or payload["direction"] != approval["direction"]):
            raise V20FinamBlocked("STOP_TRIAL_SCOPE_INVALID")
        position = snapshot.positions.get(payload["finam_symbol"], 0)
        if (type(position) is not int or position == 0
                or (position > 0) != (payload["direction"] == "LONG")
                or abs(position) > payload["quantity"]):
            raise V20FinamBlocked("STOP_POSITION_AUTHORITY_INVALID")
        registry = _load_registry()[payload["symbol"]]
        step = Decimal(registry["price_step"])
        price = Decimal(str(stop_price))
        require_on_grid(price, step)
        # Reuse the SAME strict H1 FINAM /trades order-linked fill proof that
        # our V20 SQLite protected-entry observer already trusts. A caller
        # cannot supply an arbitrary stop merely because it lies on the grid.
        submission = self.journal.store.get("entry_submission:" + key)
        if (not isinstance(submission, dict)
                or submission.get("account_sha256") != self.journal.account_hash
                or not isinstance(submission.get("submitted_at"), str)):
            raise V20FinamBlocked("STOP_ENTRY_SUBMISSION_EVIDENCE_MISSING")
        try:
            submitted_at = datetime.fromisoformat(submission["submitted_at"])
            history = self.reader.inspect_entry_fills(
                current, entry_key=key, symbol=payload["symbol"],
                direction=payload["direction"],
                requested_quantity=payload["quantity"],
                submitted_at=submitted_at, now=now,
            )
            facts = history["matched_unique_fills"]
            if (history["authority_scope"] !=
                    "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF"
                    or history["matched_quantity"] != abs(position)
                    or not facts):
                raise V20FinamBlocked("STOP_ENTRY_FILLS_NOT_PROVEN")
            order = unique_order_by_client_id(
                list(current.orders), compact_client_order_id(key),
            )
            if order is None or order.order_id != entry["broker_order_id"]:
                raise V20FinamBlocked("STOP_ENTRY_ORDER_ID_MISMATCH")
            reservation = RiskReservation.restore(
                self.journal.store.get("risk_reservations", {}).get(key),
            )
            fill_items = [(int(f["quantity"]), f["price"], "0") for f in facts]
            valuation = revalue_fill(
                reservation, fill_items, installed_stop=price,
                other_reserved_risk=sum(
                    (RiskReservation.restore(r).reserved_risk for k, r in
                     self.journal.store.get("risk_reservations", {}).items()
                     if k != key), Decimal(0),
                ),
            )
            if valuation["stop_conforms"] is not True:
                raise V20FinamBlocked("STOP_NOT_FROM_ACTUAL_FINAM_FILL_VWAP")
            actual_vwap = Fraction(valuation["average_price"])
            if ((payload["direction"] == "LONG" and Fraction(price) >= actual_vwap)
                    or (payload["direction"] == "SHORT" and Fraction(price) <= actual_vwap)):
                raise V20FinamBlocked("STOP_ON_WRONG_SIDE_OF_ACTUAL_FILL")
        except Exception:
            self.journal.store.put("execution_halt", "STOP_FILL_OR_PRICE_AUTHORITY_UNVERIFIED")
            raise
        stop_key = key + ":stop"
        action = RuntimeAction(
            "PROTECTIVE_STOP_INSTALL", stop_key, payload["symbol"],
            payload["finam_symbol"], payload["direction"],
            abs(position), key, None, Decimal(payload["reference_entry"]),
            price, position, price_step=step,
        )
        wire = percent_position_stop_payload(action)
        wire.pop("schema_id", None)
        wire["client_order_id"] = compact_client_order_id(stop_key)
        if len(stop_key) > 128:
            raise V20FinamBlocked("STOP_KEY_COMMENT_TOO_LONG")
        # Only the H1 documented 100%-of-position stop is accepted.
        if wire["sl_qty_measure"] != "SLTP_QTY_MEASURE_PERCENT" or wire["quantity_sl"] != {"value": "100"}:
            raise V20FinamBlocked("STOP_COVERAGE_INVALID")
        with self.journal.store.transaction():
            if self.journal.store.intent(stop_key) is not None:
                raise V20FinamBlocked("STOP_ALREADY_ATTEMPTED_NO_RETRANSMIT")
            if any(o.active and o.kind == "SLTP" and o.symbol == payload["finam_symbol"]
                   for o in current.orders):
                raise V20FinamBlocked("PREEXISTING_BROKER_STOP_REQUIRES_RECONCILIATION")
            self.journal.store.persist_intent(stop_key, {
                "kind": "STOP", "entry_key": key, "wire": wire,
                "account_sha256": self.journal.account_hash,
                "observed_position_quantity": position,
            })
            self.journal.store.transition_intent(stop_key, "UNCERTAIN")
        try:
            ack = self.reader.api.place_sltp_order(self.reader.account_id, wire)
        except FinamOrderRejected:
            self.journal.store.transition_intent(stop_key, "REJECTED")
            self.journal.store.put("execution_halt", "STOP_ORDER_REJECTED")
            raise
        except BaseException:
            self.journal.store.put("execution_halt", "STOP_POST_OUTCOME_UNVERIFIED")
            raise
        oid = ack.get("order_id") if isinstance(ack, dict) else None
        if not isinstance(oid, str) or not oid:
            self.journal.store.put("execution_halt", "STOP_ACK_UNVERIFIED")
            raise V20FinamBlocked("STOP_ACK_UNVERIFIED")
        self.journal.store.transition_intent(stop_key, "ACK", oid)
        # ACK alone is not protection: reader must see active 100% stop.
        return oid


    def submit_frozen_exit_once(
        self, *, key: str, boundary: "V20M15Boundary",
        snapshot: LiveAccountSnapshot, now: datetime,
    ) -> str:
        """H1 market exit on observed third session; durable one-shot only."""
        approval = self._permit(key=key, kind="FROZEN_EXIT")
        self.reader._fresh(snapshot, now)
        current = self.reader.snapshot(now=now)
        if (not isinstance(boundary, V20M15Boundary)
                or boundary.observed_at_utc != now.astimezone(timezone.utc)
                or current.positions != snapshot.positions
                or current.orders != snapshot.orders):
            raise V20FinamBlocked("EXIT_M15_OR_BROKER_SNAPSHOT_MISMATCH")
        entry = self.journal.store.intent(key)
        proof = self.journal.store.get("protected_fill:" + key)
        if (entry is None or entry["status"] not in {"RECONCILED", "PARTIAL_FILL", "FILL"}
                or not isinstance(proof, dict)
                or proof.get("account_sha256") != self.journal.account_hash):
            raise V20FinamBlocked("EXIT_PROTECTED_ENTRY_UNVERIFIED")
        payload = entry["payload"]
        if (payload["symbol"] != approval["instrument"]
                or payload["direction"] != approval["direction"]
                or boundary.symbol != payload["symbol"]):
            raise V20FinamBlocked("EXIT_TRIAL_SCOPE_MISMATCH")
        # Never trust a caller-supplied M15 boundary for a live close; GET
        # the actual FINAM completed bars and new Open through H1 first.
        entry_open = datetime.fromisoformat(payload["entry_at"])
        entry_utc = entry_open.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        witnessed = read_finam_m15_boundary(
            self.reader, symbol=payload["symbol"],
            from_utc=entry_utc - STEP, now=now,
            require_adjacent_completed=False,
        )
        if (witnessed.at_msk != boundary.at_msk
                or witnessed.witnessed_open != boundary.witnessed_open):
            raise V20FinamBlocked("EXIT_FINAM_M15_WITNESS_MISMATCH")
        if frozen_observed_session_exit(
            witnessed, entry_open_msk=entry_open,
        ) != "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN":
            raise V20FinamBlocked("EXIT_THIRD_SESSION_OPEN_NOT_DUE")
        due = boundary.at_msk.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
        if not timedelta(0) <= now.astimezone(timezone.utc) - due <= timedelta(seconds=60):
            raise V20FinamBlocked("EXIT_OPEN_STALE")
        position = current.positions.get(payload["finam_symbol"], 0)
        if (type(position) is not int or position == 0
                or (position > 0) != (payload["direction"] == "LONG")
                or abs(position) != proof.get("filled_quantity")
                or abs(position) > approval["max_quantity"]):
            raise V20FinamBlocked("EXIT_BROKER_QUANTITY_MISMATCH")
        stop = self.reader.inspect_protective_stop(
            current, entry_key=key, symbol=payload["symbol"],
            direction=payload["direction"],
            stop_price=Decimal(proof["installed_stop"]), now=now,
        )
        if stop.order_id != proof["broker_stop_id"]:
            raise V20FinamBlocked("EXIT_BROKER_STOP_ID_MISMATCH")
        exit_key = key + ":frozen-exit"
        action = RuntimeAction("EMERGENCY_EXIT_REQUIRED", exit_key,
                               payload["symbol"], payload["finam_symbol"],
                               payload["direction"], abs(position), key,
                               None, None, None, position)
        wire = AuthorizedFinamProductionTransport._market_payload(action, exit_order=True)
        with self.journal.store.transaction():
            if self.journal.store.intent(exit_key):
                raise V20FinamBlocked("EXIT_ALREADY_ATTEMPTED_NO_RETRANSMIT")
            self.journal.store.persist_intent(exit_key, {
                "kind": "FROZEN_EXIT", "entry_key": key,
                "account_sha256": self.journal.account_hash,
                "broker_stop_id": stop.order_id, "quantity": abs(position),
                "boundary_msk": boundary.at_msk.isoformat(), "wire": wire,
            })
            self.journal.store.transition_intent(exit_key, "UNCERTAIN")
        try:
            ack = self.reader.api.place_order(self.reader.account_id, wire)
        except FinamOrderRejected:
            self.journal.store.transition_intent(exit_key, "REJECTED")
            self.journal.store.put("execution_halt", "FROZEN_EXIT_REJECTED_KEEP_STOP")
            raise
        except BaseException:
            self.journal.store.put("execution_halt", "FROZEN_EXIT_UNCERTAIN_KEEP_STOP")
            raise
        oid = ack.get("order_id") if isinstance(ack, dict) else None
        if not isinstance(oid, str) or not oid:
            self.journal.store.put("execution_halt", "FROZEN_EXIT_ACK_UNVERIFIED")
            raise V20FinamBlocked("FROZEN_EXIT_ACK_UNVERIFIED")
        self.journal.store.transition_intent(exit_key, "ACK", oid)
        return oid

    def cancel_stop_after_flat_once(
        self, *, key: str, snapshot: LiveAccountSnapshot, now: datetime,
    ) -> str:
        """H1 cancel-after-flat: FINAM GET must prove zero position first."""
        self._permit(key=key, kind="FROZEN_EXIT")
        self.reader._fresh(snapshot, now)
        current = self.reader.snapshot(now=now)
        if current.positions != snapshot.positions:
            raise V20FinamBlocked("FLAT_CLEANUP_SNAPSHOT_CHANGED")
        entry = self.journal.store.intent(key)
        proof = self.journal.store.get("protected_fill:" + key)
        exit_intent = self.journal.store.intent(key + ":frozen-exit")
        if (entry is None or not isinstance(proof, dict)
                or exit_intent is None
                or exit_intent["status"] not in {"ACK", "UNCERTAIN", "RECONCILED"}
                or exit_intent["payload"].get("kind") != "FROZEN_EXIT"):
            raise V20FinamBlocked("FLAT_CLEANUP_ENTRY_EXIT_UNVERIFIED")
        symbol = entry["payload"]["finam_symbol"]
        if current.positions.get(symbol, 0) != 0:
            raise V20FinamBlocked("FLAT_CLEANUP_POSITION_OPEN")
        active = [o for o in current.orders if o.active and o.kind == "SLTP"
                  and o.symbol == symbol]
        if not active:
            self.journal.store.put("flat_cleanup:" + key, {
                "status": "BROKER_FLAT_NO_ACTIVE_STOP",
                "account_sha256": self.journal.account_hash,
            })
            return "BROKER_FLAT_NO_ACTIVE_STOP"
        stop_key = key + ":stop"
        if (len(active) != 1 or active[0].order_id != proof.get("broker_stop_id")
                or active[0].client_order_id != compact_client_order_id(stop_key)
                or active[0].comment != stop_key):
            raise V20FinamBlocked("FLAT_CLEANUP_STOP_ID_MISMATCH")
        cancel_key = key + ":cancel-after-flat"
        with self.journal.store.transaction():
            if self.journal.store.intent(cancel_key):
                raise V20FinamBlocked("FLAT_CANCEL_ALREADY_ATTEMPTED_NO_RETRANSMIT")
            self.journal.store.persist_intent(cancel_key, {
                "kind": "STOP_CANCEL", "entry_key": key,
                "account_sha256": self.journal.account_hash,
                "broker_order_id": active[0].order_id,
            })
            self.journal.store.transition_intent(cancel_key, "UNCERTAIN")
        try:
            self.reader.api.cancel_order(self.reader.account_id, active[0].order_id)
        except BaseException:
            self.journal.store.put("execution_halt", "STOP_CANCEL_UNKNOWN_RECONCILE")
            raise
        self.journal.store.transition_intent(cancel_key, "ACK", active[0].order_id)
        return "CANCEL_ACK_REQUIRE_BROKER_NO_STOP_CONFIRMATION"

@dataclass(frozen=True)
class V20M15Boundary:
    """Separate FINAM completed-candle facts and a new-bar Open witness."""
    symbol: str
    at_msk: datetime  # naive Moscow wall-clock exact M15 boundary
    completed: pd.DataFrame
    witnessed_open: Decimal
    observed_at_utc: datetime


def read_finam_m15_boundary(
    reader: V20FinamReadAdapter, *, symbol: str,
    from_utc: datetime, now: datetime,
    require_adjacent_completed: bool = True,
) -> V20M15Boundary:
    """GET-only H1 FINAM API + official TIME_FRAME_M15 query.

    Caller must still establish FINAM M15 timestamp *open-label* semantics
    against real broker samples before any LIVE decision. We never treat a
    partially formed bar's High/Low/Close/Volume as a completed signal.
    An absent current-bar Open, late observation or discontinuity refuses entry.
    """
    reader._require_bound()
    if (symbol not in N4 or not isinstance(from_utc, datetime)
            or not isinstance(now, datetime)
            or from_utc.tzinfo is None or now.tzinfo is None
            or from_utc.utcoffset() is None or now.utcoffset() is None):
        raise V20FinamBlocked("M15_READ_INPUT_INVALID")
    start = from_utc.astimezone(timezone.utc)
    observed = now.astimezone(timezone.utc)
    if not timedelta(minutes=15) <= observed + STEP - start <= timedelta(days=30):
        raise V20FinamBlocked("M15_FINAM_HISTORY_INTERVAL_INVALID")
    at_msk = observed.astimezone(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
    boundary = at_msk.replace(minute=at_msk.minute//15*15, second=0, microsecond=0)
    elapsed = at_msk - boundary
    if not timedelta(0) <= elapsed <= timedelta(seconds=60):
        raise V20FinamBlocked("M15_IMMEDIATE_NEXT_OPEN_MISSED")
    # The exclusive end includes the current M15 bar's Open if FINAM has
    # published it. This is a scalar reference only, not a filled price.
    exclusive_end = (observed + STEP).isoformat()
    query = urlencode({
        "timeframe": "TIME_FRAME_M15",
        "interval.start_time": start.isoformat(),
        "interval.end_time": exclusive_end,
    })
    finam_symbol = _load_registry()[symbol]["finam_symbol"]
    response = reader.api._request(
        "GET", BARS_PATH_TEMPLATE.format(symbol=finam_symbol) + "?" + query,
    ).body
    if (not isinstance(response, dict)
            or response.get("symbol") not in (None, finam_symbol)
            or not isinstance(response.get("bars"), list)):
        raise V20FinamBlocked("M15_FINAM_RESPONSE_SCHEMA_INVALID")
    rows = []
    for item in response["bars"]:
        if not isinstance(item, dict) or not isinstance(item.get("timestamp"), str):
            raise V20FinamBlocked("M15_FINAM_BAR_SCHEMA_INVALID")
        try:
            utc_open = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00"),
            ).astimezone(timezone.utc)
        except (ValueError, TypeError) as exc:
            raise V20FinamBlocked("M15_FINAM_TIMESTAMP_INVALID") from exc
        if utc_open < start or utc_open > observed or utc_open.second or utc_open.microsecond:
            raise V20FinamBlocked("M15_FINAM_TIMESTAMP_OUT_OF_RANGE")
        stamp = utc_open.astimezone(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
        if stamp.minute % 15:
            raise V20FinamBlocked("M15_FINAM_GRID_MISMATCH")
        if stamp == boundary:
            # FINAM may not yet have final High/Low/Close/Volume in the
            # still-forming opening candle. Never inspect or trust them.
            opened = parse_rest_decimal_value_object(item.get("open"), positive=True)
            rows.append((stamp, {"open": opened}))
            continue
        price = {}
        for field in ("open", "high", "low", "close", "volume"):
            price[field] = parse_rest_decimal_value_object(item.get(field))
            if not price[field].is_finite() or price[field] < 0 or (
                field != "volume" and price[field] <= 0
            ):
                raise V20FinamBlocked("M15_FINAM_OHLCV_INVALID")
        rows.append((stamp, price))
    dates = [r[0] for r in rows]
    if dates != sorted(set(dates)):
        raise V20FinamBlocked("M15_DUPLICATE_OR_UNSORTED_BARS")
    live = [(t, x) for t, x in rows if t == boundary]
    if len(live) != 1:
        raise V20FinamBlocked("M15_NEXT_OPEN_WITNESS_MISSING")
    witnessed_open = live[0][1]["open"]
    require_on_grid(witnessed_open, Decimal(_load_registry()[symbol]["price_step"]))
    completed = [(t, x) for t, x in rows if t + STEP <= boundary]
    if not completed or (require_adjacent_completed
                         and completed[-1][0] != boundary-STEP):
        raise V20FinamBlocked("M15_FINAL_COMPLETED_BAR_MISSING")
    if any(t > boundary for t in dates):
        raise V20FinamBlocked("M15_FUTURE_BAR_FORBIDDEN")
    frame = pd.DataFrame([
        {"Datetime": t, "Open": float(x["open"]), "High": float(x["high"]),
         "Low": float(x["low"]), "Close": float(x["close"]),
         "Volume": float(x["volume"])}
        for t, x in completed
    ])
    frame = validate_completed_history(symbol, frame, observed_at=boundary)
    return V20M15Boundary(symbol, boundary, frame, witnessed_open, observed)


def offline_m15_signal_diagnostic(
    reader: V20FinamReadAdapter, *, symbol: str, from_utc: datetime,
    now: datetime,
) -> dict[str, Any]:
    """Run *only* the frozen signal from observed FINAM bars, not a trade."""
    boundary = read_finam_m15_boundary(
        reader, symbol=symbol, from_utc=from_utc, now=now,
    )
    signal = completed_signal(
        symbol, ROBOT_STRATEGIES[reader.robot_id], boundary.completed,
        observed_at=boundary.at_msk,
    )
    return {
        "mode": "DIAGNOSTIC_ONLY_TIMESTAMP_SEMANTICS_NOT_YET_VERIFIED",
        "robot_id": reader.robot_id, "symbol": symbol,
        "at_msk": boundary.at_msk.isoformat(),
        "completed_bar_count": len(boundary.completed),
        "witnessed_open": str(boundary.witnessed_open),
        "signal": None if signal is None else {
            "direction": "LONG" if signal.side == 1 else "SHORT",
            "atr14": str(signal.atr14),
            "bar_open_msk": signal.signal_bar_open.isoformat(),
        },
        "orders": 0,
    }

def frozen_observed_session_exit(
    boundary: V20M15Boundary, *, entry_open_msk: datetime,
) -> str:
    """Frozen V20 holding deadline, evaluated on *observed* M15 opens only.

    The entry session counts as the first. On the first witnessed Open of
    the third session, return EXIT_AT_THIRD_OBSERVED_SESSION_OPEN. If that
    exact opening boundary was missed, HALT instead of pretending to have
    exited at a past price. This emits NO broker orders.
    """
    if (not isinstance(boundary, V20M15Boundary)
            or not isinstance(entry_open_msk, datetime)
            or entry_open_msk.tzinfo is not None
            or entry_open_msk.second or entry_open_msk.microsecond
            or entry_open_msk.minute % 15
            or boundary.at_msk < entry_open_msk):
        raise V20FinamBlocked("THIRD_SESSION_EXIT_INPUT_INVALID")
    entry_day = OfflinePlanner._session_key(entry_open_msk)
    rows = [
        pd.Timestamp(value).to_pydatetime()
        for value in boundary.completed["Datetime"]
    ]
    if entry_open_msk not in rows and entry_open_msk != boundary.at_msk:
        raise V20FinamBlocked("ENTRY_SESSION_OBSERVATION_MISSING")
    days = sorted({OfflinePlanner._session_key(t) for t in rows
                   if t >= entry_open_msk}
                  | {OfflinePlanner._session_key(boundary.at_msk), entry_day})
    if len(days) < 3:
        return "HOLD_UNTIL_THIRD_OBSERVED_SESSION"
    third = days[2]
    if (len(days) == 3
            and OfflinePlanner._session_key(boundary.at_msk) == third
            and not any(OfflinePlanner._session_key(t) == third for t in rows)):
        return "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN"
    return "MISSED_OR_PASSED_THIRD_SESSION_OPEN_HALT"


def propose_finam_m15_next_open(
    reader: V20FinamReadAdapter, *, symbol: str, from_utc: datetime,
    now: datetime, cost_per_contract: Decimal, technical_acceptance: bool = False,
) -> tuple[FrozenSignal, ProposedEntry, AccountAuthority, LiveAccountSnapshot] | None:
    """08.1: one common NO-POST path FINAM M15 -> frozen V20 -> reused H1 risk.

    Return None on a verified no-signal bar, otherwise an *unpersisted*
    candidate. Neither durable authority nor permission to place an order
    is granted here. Caller still needs its per-account journal/kill switch,
    approved trial, fresh broker reconciliation and H1 order transport.
    """
    if not isinstance(reader, V20FinamReadAdapter) or reader.robot_id not in ROBOT_STRATEGIES:
        raise V20FinamBlocked("NEXT_OPEN_ROBOT_IDENTITY_INVALID")
    boundary = read_finam_m15_boundary(
        reader, symbol=symbol, from_utc=from_utc, now=now,
    )
    if boundary.at_msk != (
        now.astimezone(ZoneInfo("Europe/Moscow"))
        .replace(tzinfo=None, minute=now.astimezone(ZoneInfo("Europe/Moscow")).minute//15*15,
                 second=0, microsecond=0)
    ):
        raise V20FinamBlocked("NEXT_OPEN_BOUNDARY_INVALID")
    if technical_acceptance:
        # Technical 08.2 acceptance is NOT a strategy signal. Only the
        # unchanged frozen feature calculator provides Wilder ATR14. Reuse
        # the existing H1 risk/stop planner on the observed next M15 Open.
        # This synthetic typed input is isolated and permanently labeled
        # TECHNICAL_ACCEPTANCE in its separate SQLite journal.
        last = boundary.completed["Datetime"].iloc[-1].to_pydatetime()
        if last + STEP != boundary.at_msk:
            raise V20FinamBlocked("TECHNICAL_TRIAL_ADJACENT_M15_MISSING")
        features = _frozen_immutable_features(boundary.completed)
        atr = Decimal(str(features["atr"].iloc[-1]))
        if not atr.is_finite() or atr <= 0:
            raise V20FinamBlocked("TECHNICAL_TRIAL_ATR_INVALID")
        signal = FrozenSignal(ROBOT_STRATEGIES[reader.robot_id], symbol, 1, last, atr)
    else:
        signal = completed_signal(
            symbol, ROBOT_STRATEGIES[reader.robot_id],
            boundary.completed, observed_at=boundary.at_msk,
        )
        if signal is None:
            return None
    if (signal.strategy != ROBOT_STRATEGIES[reader.robot_id]
            or signal.symbol != symbol
            or signal.signal_bar_open + STEP != boundary.at_msk):
        raise V20FinamBlocked("NEXT_OPEN_FROZEN_SIGNAL_MISMATCH")
    snapshot = reader.snapshot(now=now)
    if not snapshot.clean:
        raise V20FinamBlocked("NEXT_OPEN_NONFLAT_ACCOUNT_NO_BOOTSTRAP")
    direction = "LONG" if signal.side == 1 else "SHORT"
    authority = reader.authority(
        snapshot, symbol=symbol, direction=direction,
        roundtrip_cost_per_contract=cost_per_contract, now=now,
    )
    candidate = OfflinePlanner(ROBOT_STRATEGIES[reader.robot_id]).reference_next_open(
        signal, at=boundary.at_msk, entry_open=boundary.witnessed_open,
        realized_equity=authority.realized_equity, price_step=authority.price_step,
        tick_value=authority.tick_value, initial_margin=authority.initial_margin,
        available_cash=authority.available_cash,
        trade_lot_size=authority.trade_lot_size,
        cost_buffer_per_contract=authority.roundtrip_cost_per_contract,
    )
    if (candidate.strategy != signal.strategy or candidate.symbol != symbol
            or candidate.entry_bar_open != boundary.at_msk
            or candidate.reference_entry != boundary.witnessed_open):
        raise V20FinamBlocked("NEXT_OPEN_PLANNER_MISMATCH")
    return signal, candidate, authority, snapshot


def prepare_finam_single_trial(
    transport: V20SingleTradeTransport, *, symbol: str, from_utc: datetime,
    now: datetime, cost_per_contract: Decimal,
    permit_on_signal=None, technical_acceptance: bool = False,
) -> dict[str, Any]:
    """08.1/08.2 preflight: exact trial authority -> durable H1 intent.

    Does NOT send a FINAM order. Its returned key may only be submitted by
    V20SingleTradeTransport.submit_entry_once after the same broker guards.
    A no-signal boundary does not consume the single-trial permit.
    """
    if not isinstance(transport, V20SingleTradeTransport):
        raise V20FinamBlocked("TRIAL_PREPARER_TRANSPORT_INVALID")
    journal, reader = transport.journal, transport.reader
    if (journal.robot_id != reader.robot_id
            or journal.account_hash != reader.account_hash
            or journal.store.get("execution_halt") is not None
            or journal.store.all_intents()):
        raise V20FinamBlocked("TRIAL_PREPARER_EXISTING_INTENT_OR_HALT")
    from TradingSystemLab.stage8_robot.trading_safety_gate import load_kill_switch
    switch, switch_error = load_kill_switch(journal.instance_root)
    if switch_error or not switch or switch["state"] != "ARMED":
        raise V20FinamBlocked("TRIAL_PREPARER_V20_KILL_SWITCH_NOT_ARMED")
    draft = propose_finam_m15_next_open(
        reader, symbol=symbol, from_utc=from_utc,
        now=now, cost_per_contract=cost_per_contract,
        technical_acceptance=technical_acceptance,
    )
    if draft is None:
        return {"status": "NO_FROZEN_SIGNAL", "orders": 0}
    signal, candidate, authority, snapshot = draft
    if technical_acceptance:
        if authority.trade_lot_size != 1:
            raise V20FinamBlocked("TECHNICAL_ONE_CONTRACT_LOT_REQUIRED")
        candidate = replace(candidate, quantity=1)
    key = journal.preview_entry_key(candidate)
    # 08.2: owner may approve ONE frozen entry in advance by account/robot/
    # instrument/risk ceiling. Only after real FINAM bars + frozen signal
    # generate the exact pre-existing H1 one-trial permit for this entry key.
    # The callback cannot bypass the unchanged _permit() validator.
    if permit_on_signal is not None:
        permit_on_signal(key, signal, candidate, authority)
    approval = transport._permit(key=key, kind="ENTRY")
    if (approval["instrument"] != candidate.symbol
            or approval["direction"] != candidate.direction):
        raise V20FinamBlocked("TRIAL_PREPARER_SCOPE_NOT_APPROVED")
    candidate = replace(candidate, quantity=min(
        candidate.quantity, approval["max_quantity"],
    ))
    # Reuse exactly the current H1 risk authority to validate the owner's
    # monetary ceiling BEFORE writing an intent that could never be approved.
    risk = reserve_entry(
        authority=authority, entry_key=key, symbol=symbol,
        direction=candidate.direction, entry=candidate.reference_entry,
        atr14=signal.atr14, planned_max_quantity=candidate.quantity,
        current_reservations=(),
    )
    try:
        cap = Decimal(str(approval["max_risk_rub"]))
    except (ValueError, TypeError, ArithmeticError):
        raise V20FinamBlocked("TRIAL_PREPARER_APPROVED_RISK_INVALID") from None
    if not cap.is_finite() or cap <= 0 or risk.reserved_risk > cap:
        raise V20FinamBlocked("TRIAL_PREPARER_RISK_EXCEEDS_APPROVAL")
    with journal.store.transaction():
        persisted = journal.prepare_entry(
            signal=signal, entry=candidate, authority=authority, snapshot=snapshot,
        )
        if persisted != key:
            raise V20FinamBlocked("TRIAL_PREPARER_INTENT_KEY_CHANGED")
        if technical_acceptance:
            journal.store.put("technical_acceptance:" + key, {
                "kind": "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL",
                "robot_id": journal.robot_id, "account_sha256": journal.account_hash,
                "symbol": symbol, "direction": "LONG", "max_quantity": 1,
                "m15_observed_open": str(candidate.reference_entry),
                "atr14_wilder": str(signal.atr14),
                "reserved_risk_rub": str(risk.reserved_risk),
            })
    return {
        "status": "APPROVED_PREPARED_ONLY_NO_ORDER",
        "robot_id": journal.robot_id,
        "entry_key": persisted,
        "symbol": candidate.symbol,
        "direction": candidate.direction,
        "quantity": risk.quantity,
        "reserved_risk_rub": str(risk.reserved_risk),
        "orders": 0,
    }


def run_v20_single_trial_cycle(
    transport: V20SingleTradeTransport, *, now: datetime,
    trial_symbol: str, from_utc: datetime, cost_per_contract: Decimal,
    allow_new_entry: bool = False, permit_on_signal=None,
    technical_acceptance: bool = False,
) -> dict[str, Any]:
    """Existing H1 read/reconcile -> stop/exit -> optional one approved entry.

    Common V20 one-trial coordinator, NOT general LIVE enablement.
    No scheduler, token store or Task activation. In a restarted process, an
    existing entry/stop/exit intent is managed but NEVER retransmitted.
    """
    if (not isinstance(transport, V20SingleTradeTransport)
            or trial_symbol not in N4
            or not isinstance(now, datetime) or now.tzinfo is None):
        raise V20FinamBlocked("TRIAL_CYCLE_INPUT_INVALID")
    reader, journal = transport.reader, transport.journal
    if reader.robot_id != journal.robot_id or reader.account_hash != journal.account_hash:
        raise V20FinamBlocked("TRIAL_CYCLE_ACCOUNT_MISMATCH")
    current = reader.snapshot(now=now)
    entries = [r for r in journal.store.all_intents()
               if r["payload"].get("kind") == "ENTRY"]
    if len(entries) > 1:
        raise V20FinamBlocked("TRIAL_CYCLE_MORE_THAN_ONE_ENTRY")
    if not entries:
        if not current.clean:
            raise V20FinamBlocked("TRIAL_CYCLE_UNOWNED_BROKER_POSITION_OR_ORDER")
        if not allow_new_entry:
            return {"state": "BROKER_OBSERVED_NO_TRIAL_ENTRY", "orders": 0}
        prepared = prepare_finam_single_trial(
            transport, symbol=trial_symbol, from_utc=from_utc,
            now=now, cost_per_contract=cost_per_contract,
            permit_on_signal=permit_on_signal,
            technical_acceptance=technical_acceptance,
        )
        if prepared["status"] == "NO_FROZEN_SIGNAL":
            return {"state": "NO_FROZEN_SIGNAL", "orders": 0}
        key = prepared["entry_key"]
        # The H1 transport checks fresh account, EXACT permit and time again
        # before performing the only market-order POST.
        ack = transport.submit_entry_once(
            key=key, snapshot=reader.snapshot(now=now), now=now,
        )
        return {"state": "ENTRY_ACK_NEEDS_FILL_AND_STOP", "entry_key": key,
                "broker_entry_order_id": ack, "orders": 1}

    entry = entries[0]
    key = entry["idempotency_key"]
    payload = entry["payload"]
    if (payload.get("symbol") != trial_symbol
            or payload.get("robot_id") != journal.robot_id
            or payload.get("account_sha256") != journal.account_hash):
        raise V20FinamBlocked("TRIAL_CYCLE_FOREIGN_ENTRY")
    symbol = payload["finam_symbol"]
    if technical_acceptance:
        marker = journal.store.get("technical_acceptance:" + key)
        if (not isinstance(marker, dict)
                or marker.get("kind") != "TECHNICAL_ACCEPTANCE_NOT_FROZEN_SIGNAL"
                or marker.get("robot_id") != journal.robot_id
                or marker.get("account_sha256") != journal.account_hash
                or marker.get("symbol") != trial_symbol
                or marker.get("max_quantity") != 1
                or payload.get("quantity") != 1):
            raise V20FinamBlocked("TECHNICAL_TRIAL_DURABLE_SCOPE_INVALID")
    elif journal.store.get("technical_acceptance:" + key) is not None:
        raise V20FinamBlocked("TECHNICAL_TRIAL_CANNOT_RUN_AS_FROZEN")
    # The unchanged H1 service rejects unrelated broker positions/orders
    # before it reconciles owned orders or transmits a protective action.
    # Single-trial V20 uses the same ownership invariant, one account only.
    if set(current.positions) - {symbol}:
        raise V20FinamBlocked("TRIAL_CYCLE_FOREIGN_BROKER_POSITION")
    expected_orders = {
        compact_client_order_id(key): (key, "REGULAR"),
        compact_client_order_id(key + ":stop"): (key + ":stop", "SLTP"),
        compact_client_order_id(key + ":frozen-exit"): (
            key + ":frozen-exit", "REGULAR",
        ),
    }
    seen_active = set()
    for order in current.orders:
        if not order.active:
            continue
        owner = expected_orders.get(order.client_order_id)
        if (owner is None or order.client_order_id in seen_active
                or order.symbol != symbol or order.kind != owner[1]
                or journal.store.intent(owner[0]) is None):
            raise V20FinamBlocked("TRIAL_CYCLE_UNOWNED_OR_DUPLICATE_ACTIVE_ORDER")
        seen_active.add(order.client_order_id)
    position = current.positions.get(symbol, 0)
    proof = journal.store.get("protected_fill:" + key)
    if position == 0:
        exit_intent = journal.store.intent(key + ":frozen-exit")
        if exit_intent is not None:
            return {"state": transport.cancel_stop_after_flat_once(
                key=key, snapshot=current, now=now,
            ), "orders": 0}
        if isinstance(proof, dict):
            stop = next((o for o in current.orders if
                         o.order_id == proof.get("broker_stop_id")
                         and o.kind == "SLTP" and o.symbol == symbol), None)
            if (stop is not None and not stop.active
                    and stop.status in {"FILLED", "EXECUTED"}
                    and not any(o.active and o.kind == "SLTP" and o.symbol == symbol
                                for o in current.orders)):
                journal.store.put("flat_cleanup:" + key, {
                    "status": "STOP_TERMINAL_BROKER_FLAT",
                    "account_sha256": journal.account_hash,
                })
                journal.store.put("execution_halt", "STOP_EXIT_FEES_PENDING_ACCEPTANCE")
                return {"state": "STOP_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
                        "orders": 0}
        if isinstance(proof, dict):
            # Acceptance-only early MANUAL exit in FINAM terminal. The frozen
            # 3rd-session exit and SL/TP rules of autonomous LIVE are unchanged.
            # Never cancel an active stop implicitly, nor claim that flat
            # alone proves canceled stop, fills, fees or complete acceptance.
            if proof.get("account_sha256") != journal.account_hash:
                raise V20FinamBlocked("MANUAL_EXIT_PROTECTED_PROOF_ACCOUNT_INVALID")
            unexpected_active = [
                o for o in current.orders if o.active
                and (o.kind != "SLTP" or o.order_id != proof.get("broker_stop_id"))
            ]
            if unexpected_active:
                raise V20FinamBlocked("MANUAL_EXIT_OTHER_ACTIVE_ORDER_RECONCILE")
            if any(o.active for o in current.orders):
                return {"state": "MANUAL_EXIT_FLAT_ACTIVE_STOP_CANCEL_IN_TERMINAL",
                        "orders": 0}
            journal.store.put("manual_flat:" + key, {
                "status": "FLAT_NO_ACTIVE_ORDERS_FEES_UNVERIFIED",
                "account_sha256": journal.account_hash,
                "broker_stop_id": proof.get("broker_stop_id"),
            })
            journal.store.put("execution_halt", "MANUAL_EXIT_PENDING_BROKER_ACCEPTANCE")
            return {"state": "MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE",
                    "orders": 0}
        return {"state": "ENTRY_NO_POSITION_RECONCILIATION_REQUIRED",
                "orders": 0}

    if (position > 0) != (payload["direction"] == "LONG"):
        raise V20FinamBlocked("TRIAL_CYCLE_BROKER_POSITION_SIDE_INVALID")
    if abs(position) > payload["quantity"]:
        raise V20FinamBlocked("TRIAL_CYCLE_POSITION_EXCEEDS_ENTRY")
    journal.reconcile_order(key=key, snapshot=current)
    if journal.store.intent(key + ":frozen-exit") is not None:
        return {"state": "EXIT_ALREADY_ATTEMPTED_KEEP_PROTECTION",
                "orders": 0}

    stop_intent = journal.store.intent(key + ":stop")
    if stop_intent is None:
        # H1 links fills to exact order_id and computes the executable 2 ATR
        # initial stop from actual broker VWAP (not reference entry Open).
        submitted = journal.store.get("entry_submission:" + key)
        if not isinstance(submitted, dict):
            raise V20FinamBlocked("TRIAL_CYCLE_SUBMISSION_PROOF_MISSING")
        history = reader.inspect_entry_fills(
            current, entry_key=key, symbol=trial_symbol,
            direction=payload["direction"],
            requested_quantity=payload["quantity"],
            submitted_at=datetime.fromisoformat(submitted["submitted_at"]),
            now=now,
        )
        if (history.get("authority_scope") !=
                "READONLY_DIAGNOSTIC_ONLY_NO_RUNTIME_HANDOFF"
                or history.get("matched_quantity") != abs(position)
                or not history.get("matched_unique_fills")):
            raise V20FinamBlocked("TRIAL_CYCLE_FILL_AUTHORITY_MISSING")
        filled = history["matched_unique_fills"]
        vw = sum(
            (int(f["quantity"]) * Fraction(f["price"]) for f in filled),
            Fraction(0),
        ) / abs(position)
        step = Decimal(_load_registry()[trial_symbol]["price_step"])
        side = 1 if payload["direction"] == "LONG" else -1
        stop = project_stop(
            payload["direction"],
            vw - side * 2 * Fraction(payload["atr14"]), step,
        )
        oid = transport.submit_protection_once(
            key=key, snapshot=current, stop_price=stop, now=now,
        )
        return {"state": "STOP_ACK_NEEDS_BROKER_PROOF",
                "broker_stop_order_id": oid, "orders": 1}

    if stop_intent["status"] not in {"ACK", "RECONCILED"}:
        raise V20FinamBlocked("TRIAL_CYCLE_STOP_UNCERTAIN_NO_RETRY")
    # H1 strict fill and active-100%-SLTP broker proof, preserved after restart.
    observed = journal.observe_protected_entry(
        key=key, reader=reader, snapshot=current, now=now,
    )
    if (not isinstance(proof, dict)
            or proof.get("broker_stop_id") != observed["broker_stop_id"]):
        return {"state": "STOP_NOW_BROKER_PROVEN", "orders": 0}
    if technical_acceptance:
        # In the isolated H1-style acceptance trade the owner closes manually.
        # Never apply the third-session *strategy* exit to this technical test.
        return {"state": "TECHNICAL_SLTP_CONFIRMED_AWAIT_MANUAL_CLOSE", "orders": 0}
    utc = now.astimezone(timezone.utc)
    msk = utc.astimezone(ZoneInfo("Europe/Moscow"))
    if msk.minute % 15 != 0:
        return {"state": "PROTECTED_AWAIT_NEXT_OPEN", "orders": 0}
    if msk.second + msk.microsecond / 1_000_000 > 60:
        return {"state": "PROTECTED_AWAIT_NEXT_OPEN", "orders": 0}
    entry_at = datetime.fromisoformat(payload["entry_at"])
    since = entry_at.replace(tzinfo=ZoneInfo("Europe/Moscow")).astimezone(timezone.utc)
    boundary = read_finam_m15_boundary(
        reader, symbol=trial_symbol, from_utc=since - STEP, now=now,
        require_adjacent_completed=False,
    )
    decision = frozen_observed_session_exit(
        boundary, entry_open_msk=entry_at,
    )
    if decision == "HOLD_UNTIL_THIRD_OBSERVED_SESSION":
        return {"state": "PROTECTED_HOLD", "orders": 0}
    if decision != "EXIT_AT_THIRD_OBSERVED_SESSION_OPEN":
        journal.store.put("execution_halt", "FROZEN_THIRD_SESSION_OPEN_MISSED")
        raise V20FinamBlocked("TRIAL_CYCLE_DEADLINE_MISSED")
    oid = transport.submit_frozen_exit_once(
        key=key, boundary=boundary, snapshot=current, now=now,
    )
    return {"state": "EXIT_ACK_KEEP_STOP_UNTIL_FLAT",
            "broker_exit_order_id": oid, "orders": 1}
