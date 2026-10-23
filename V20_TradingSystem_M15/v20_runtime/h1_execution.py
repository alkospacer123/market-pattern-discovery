"""V20-04.3 OFFLINE H1 order-contract integration; in-memory broker only.

Reuse H1 wire builders, strict broker readers, SQLite intents/fills and locks.
Never construct H1 ProductionRuntime/Service or authorized LIVE transport.
No authentication, credential reading, HTTP, TP or trailing. An unresolved POST
is never retried, including after restart. This is not a LIVE executor.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

from TradingSystemLab.stage8_robot.broker import compact_client_order_id
from TradingSystemLab.stage8_robot.execution_grid import initial_projection, project_stop, require_on_grid
from TradingSystemLab.stage8_robot.finam_api import FinamUncertainSubmission, FinamOrderRejected
from TradingSystemLab.stage8_robot.live_execution import AuthorizedFinamProductionTransport
from TradingSystemLab.stage8_robot.production_runtime import RuntimeAction, _load_registry
from TradingSystemLab.stage8_robot.production_broker_state import (
    order_views, position_quantities, unique_order_by_client_id,
)
from TradingSystemLab.stage8_robot.protective_stop_contract import percent_position_stop_payload
from TradingSystemLab.stage8_robot.reconciliation import reconcile, Reconciliation

from .h1_state_journal import IsolatedReferenceJournal, V20StateBoundaryError
from .offline_planner import N4
from .account_risk import AccountAuthority, RiskBlocked, RiskReservation, reserve_entry, revalue_fill

LIVE_ENABLED = False


class ExecutionBlocked(RuntimeError):
    pass


class FakeBroker:
    """Explicit simulator, no network-capable object or API accepted by executor.

    Fills are injected by tests/caller, never inferred from OHLC or an ACK.
    Timeout injection can model both accepted and unaccepted uncertain POSTs.
    """
    def __init__(self, account_id):
        self.account_id = account_id
        self.orders = []
        self.fills = []
        self.post_count = 0
        self.next_fault = None

    def submit(self, wire, *, sltp=False):
        self.post_count += 1
        fault, self.next_fault = self.next_fault, None
        if fault == "rejected":
            raise FinamOrderRejected(400)
        if fault == "timeout_before_accept":
            raise FinamUncertainSubmission("SIMULATED_NO_ACK")
        oid = f"fake-{self.post_count}"
        self.orders.append(dict(order_id=oid, status="NEW",
                                **{"sltp_order" if sltp else "order": deepcopy(wire)}))
        if fault == "timeout_after_accept":
            raise FinamUncertainSubmission("SIMULATED_ACK_LOST")
        return {"order_id": oid}  # deliberately no fill authority

    def fill(self, order_id, trade_id, quantity, price, timestamp):
        row = next(x for x in self.orders if x["order_id"] == order_id)
        wire = row.get("order", row.get("sltp_order"))
        self.fills.append(dict(fill_id=f"fill-{len(self.fills)+1}",
                               broker_order_id=order_id, trade_id=trade_id,
                               quantity=str(quantity), price=str(price), fee="0",
                               timestamp=timestamp))
        filled = sum(int(x["quantity"]) for x in self.fills
                     if x["broker_order_id"] == order_id)
        target = int(wire["quantity"]["value"]) if "order" in row else filled
        row["status"] = "FILLED" if filled >= target else "PARTIAL_FILL"

    def cancel(self, order_id):
        next(x for x in self.orders if x["order_id"] == order_id)["status"] = "CANCELLED"

    def snapshot(self):
        positions = {}
        for fill in self.fills:
            row = next(x for x in self.orders if x["order_id"] == fill["broker_order_id"])
            wire = row.get("order", row.get("sltp_order"))
            sign = 1 if wire["side"] == "SIDE_BUY" else -1
            positions[wire["symbol"]] = positions.get(wire["symbol"], 0) + sign*int(fill["quantity"])
        return deepcopy(dict(account_id=self.account_id,
                             positions=[dict(symbol=s, quantity={"value": str(q)})
                                        for s, q in sorted(positions.items())],
                             orders=self.orders, fills=self.fills))


class _ExecutionJournal(IsolatedReferenceJournal):
    state_file = "v20-offline-execution.sqlite3"
    schema = "v20.h1_execution.fake_broker.v1"


class OfflineH1Executor:
    """One identical executor per robot and account; separate durable state.

    Caller supplies frozen signal/plan and frozen exit decision. Full event-loop,
    account-wide actual-fill risk/GO and physical broker validation remain later
    roadmap acceptance. Slipped fills are protected but block further entries
    pending V20-04.4 risk reconciliation.
    """
    def __init__(self, root, robot_id, account_id, broker):
        if type(broker) is not FakeBroker or broker.account_id != account_id:
            raise ExecutionBlocked("EXACT_OFFLINE_FAKE_ACCOUNT_REQUIRED")
        self.broker = broker
        self.journal = _ExecutionJournal(root, robot_id, account_id)
        self.store = self.journal._require_open()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.journal.close()

    def _halt(self, reason):
        self.store.put("execution_halt", reason)
        raise ExecutionBlocked(reason)

    @staticmethod
    def _action(row, kind, key, quantity=None, stop=None):
        qty = row["quantity"] if quantity is None else quantity
        return RuntimeAction(kind, key, row["symbol"], row["finam_symbol"], row["direction"],
                             qty, row["entry_key"], None,
                             Decimal(row["reference_entry"]), stop,
                             qty if row["direction"] == "LONG" else -qty)

    @staticmethod
    def _market(action, *, exit_order=False):
        # Pure H1 serializer only. Never instantiate/call its authorized sender.
        return AuthorizedFinamProductionTransport._market_payload(action, exit_order=exit_order)

    def _post_once(self, key, payload):
        old = self.store.intent(key)
        if old is not None:
            if old["payload"] != payload:
                self._halt("CONFLICTING_INTENT_REPLAY")
            return  # includes INTENT_PERSISTED/UNCERTAIN: no automatic retransmit
        with self.store.transaction():
            self.store.persist_intent(key, payload)
            self.store.transition_intent(key, "SUBMITTED")
        try:
            self.broker.submit(payload["wire"], sltp=payload["kind"] == "STOP")
        except FinamOrderRejected:
            self.store.transition_intent(key, "REJECTED")
            if payload["kind"] != "ENTRY":
                self._halt("PROTECTION_OR_EXIT_REJECTED")
        except Exception:
            # Even an unfamiliar exception beyond this boundary cannot prove no POST.
            self.store.transition_intent(key, "UNCERTAIN")

    def submit_entry(self, signal, entry, *, price_step, account_authority=None):
        if entry.symbol not in N4:
            raise V20StateBoundaryError("UNKNOWN_V20_SYMBOL")
        binding = _load_registry()[entry.symbol]
        if Decimal(str(price_step)) != Decimal(binding["price_step"]):
            raise ExecutionBlocked("FROZEN_N4_PRICE_STEP_MISMATCH")
        require_on_grid(entry.reference_entry, Decimal(str(price_step)))
        require_on_grid(entry.initial_stop, Decimal(str(price_step)))
        atr = Decimal(str(signal.atr14))
        if not atr.is_finite() or atr <= 0:
            raise ExecutionBlocked("INVALID_SIGNAL_ATR")
        expected, _ = initial_projection(entry.direction, entry.reference_entry,
                                         entry.reference_entry - signal.side*2*atr,
                                         Decimal(str(price_step)))
        if entry.initial_stop != expected:
            raise ExecutionBlocked("FROZEN_2_ATR_STOP_MISMATCH")
        # Existing reference validation/caps run atomically alongside durable intent.
        key = "v20:" + self.journal.robot_id + ":" + self.journal.account_hash[:16] + ":"
        material = f"{entry.symbol}:{entry.entry_bar_open.isoformat()}:{entry.direction}"
        key += compact_client_order_id(material)[2:]
        row = dict(entry_key=key, symbol=entry.symbol, direction=entry.direction,
                   finam_symbol=binding["finam_symbol"],
                   quantity=entry.quantity, reference_entry=str(entry.reference_entry),
                   planned_stop=str(entry.initial_stop), atr=str(signal.atr14),
                   price_step=str(price_step), entry_at=entry.entry_bar_open.isoformat())
        existing = self.store.get("execution_entries", {})
        if key in existing:
            self.journal.record_reference(signal, entry)
            if existing[key] != row:
                self._halt("CONFLICTING_ENTRY_REPLAY")
            self.recover()
            return key
        self.recover()
        if self.store.get("execution_halt"):
            raise ExecutionBlocked(self.store.get("execution_halt"))
        if any(x["symbol"] == entry.symbol and
               (self.store.get("remaining:" + k, 0) or self.store.intent(k)["status"] in
                {"INTENT_PERSISTED", "SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL"})
               for k, x in existing.items()):
            self._halt("ONE_OPEN_POSITION_PER_SYMBOL")
        # Optional explicit offline money-authority path. Legacy FakeBroker-only
        # tests without risk records remain untouched; real transport is disabled.
        saved_risk = self.store.get("risk_reservations", {})
        reservation = None
        if account_authority is None:
            if saved_risk:
                self._halt("ACCOUNT_MONEY_AUTHORITY_REQUIRED")
        else:
            if type(account_authority) is not AccountAuthority or account_authority.account_id != self.broker.account_id:
                self._halt("ACCOUNT_MONEY_AUTHORITY_MISMATCH")
            if account_authority.price_step != Decimal(str(price_step)):
                self._halt("ACCOUNT_MONEY_PRICE_STEP_MISMATCH")
            # Do not silently exclude positions entered by the older fake-only
            # path from the account-wide R6/margin budget.
            for old_key in existing:
                if old_key not in saved_risk and (
                        self.store.get("remaining:" + old_key, 0) or
                        (self.store.intent(old_key) and self.store.intent(old_key)["status"] in
                         {"INTENT_PERSISTED", "SUBMITTED", "UNCERTAIN", "ACK", "PARTIAL_FILL"})):
                    self._halt("UNACCOUNTED_EXISTING_POSITION_RISK")
            try:
                reservation = reserve_entry(
                    authority=account_authority, entry_key=key,
                    symbol=entry.symbol, direction=entry.direction,
                    entry=entry.reference_entry, atr14=signal.atr14,
                    planned_max_quantity=entry.quantity,
                    current_reservations=[RiskReservation.restore(x) for x in saved_risk.values()])
            except RiskBlocked as exc:
                self._halt("ACCOUNT_RISK_" + str(exc))
            if reservation.initial_stop != entry.initial_stop:
                self._halt("ACCOUNT_RISK_FROZEN_STOP_MISMATCH")
            row["quantity"] = reservation.quantity
            entry = replace(entry, quantity=reservation.quantity,
                            margin_required=reservation.reserved_margin)
        with self.store.transaction():
            self.journal.record_reference(signal, entry)
            existing[key] = row
            self.store.put("execution_entries", existing)
            if reservation is not None:
                saved_risk[key] = reservation.record()
                self.store.put("risk_reservations", saved_risk)
            # Intent, session quota and account risk reservation commit together.
            payload = dict(kind="ENTRY", entry_key=key,
                           wire=self._market(self._action(row, "ENTRY", key)))
            self.store.persist_intent(key, payload)
        # _post_once deliberately refuses an already-persisted intent; first dispatch
        # marks it SUBMITTED before leaving SQLite. A restart never repeats it.
        self.store.transition_intent(key, "SUBMITTED")
        try:
            self.broker.submit(payload["wire"])
        except FinamOrderRejected:
            self.store.transition_intent(key, "REJECTED")
        except Exception:
            self.store.transition_intent(key, "UNCERTAIN")
        self.recover()
        return key

    def recover(self):
        # Persist a fail-closed reason AFTER any failed transaction has unwound.
        try:
            return self._recover()
        except Exception as exc:
            self.store.put("execution_halt", str(exc))
            raise

    def _recover(self):
        """Reconcile exact broker orders/fills; then protect observed partial fills."""
        snap = self.broker.snapshot()
        if snap.get("account_id") != self.broker.account_id:
            self._halt("BROKER_ACCOUNT_MISMATCH")
        positions = position_quantities(snap)
        orders = order_views(snap)
        intents = {x["idempotency_key"]: x for x in self.store.all_intents()}
        entries = self.store.get("execution_entries", {})
        by_id = {}
        uncertain = False
        for key, intent in intents.items():
            view = unique_order_by_client_id(orders, compact_client_order_id(key))
            if view is None:
                if intent["status"] not in {"REJECTED", "CANCELLED", "CLOSED"}:
                    self.store.transition_intent(key, "UNCERTAIN")
                    uncertain = True
                continue
            if (view.request != intent["payload"]["wire"]
                    or view.kind != ("SLTP" if intent["payload"]["kind"] == "STOP" else "REGULAR")):
                self._halt("BROKER_INTENT_WIRE_MISMATCH")
            by_id[view.order_id] = (intent, view)
            status = ("ACK" if view.active else "FILL" if view.status in
                      {"FILLED", "SL_EXECUTED", "EXECUTED"} else "CANCELLED")
            self.store.transition_intent(key, status, view.order_id)
        if any(x.active and x.order_id not in by_id for x in orders):
            self._halt("UNKNOWN_BROKER_ORDER")

        quantities = {k: 0 for k in entries}
        entry_fills = {k: [] for k in entries}
        observed_fills = set()
        with self.store.transaction():
            for fill in snap["fills"]:
                oid = fill.get("broker_order_id")
                if oid not in by_id or fill.get("fill_id") in observed_fills:
                    self._halt("UNKNOWN_OR_DUPLICATE_FILL")
                observed_fills.add(fill["fill_id"])
                intent, view = by_id[oid]
                key = intent["payload"]["entry_key"]
                if key not in entries or fill.get("trade_id") != key:
                    self._halt("FILL_TRADE_IDENTITY_MISMATCH")
                try:
                    qty, price = Decimal(fill["quantity"]), Decimal(fill["price"])
                    datetime.fromisoformat(fill["timestamp"])
                    if (not qty.is_finite() or qty <= 0 or qty != qty.to_integral_value()
                            or not price.is_finite() or price <= 0):
                        raise ValueError()
                except (ValueError, ArithmeticError, KeyError):
                    self._halt("FILL_VALUES_INVALID")
                require_on_grid(price, Decimal(entries[key]["price_step"]))
                kind = intent["payload"]["kind"]
                quantities[key] += int(qty) * (1 if kind == "ENTRY" else -1)
                if kind == "ENTRY":
                    entry_fills[key].append((int(qty), price))
                self.store.persist_fill(fill, strict=True)
            if observed_fills != {x["fill_id"] for x in self.store.all_fills()}:
                self._halt("FILL_HISTORY_INCOMPLETE")
            for oid, (intent, view) in by_id.items():
                if intent["payload"]["kind"] == "STOP":
                    continue
                filled = sum(int(f["quantity"]) for f in snap["fills"]
                             if f["broker_order_id"] == oid)
                target = int(view.request["quantity"]["value"])
                if (filled > target or (view.status == "FILLED" and filled != target)
                        or (view.status == "PARTIAL_FILL" and not 0 < filled < target)):
                    self._halt("ORDER_FILL_HISTORY_INCONSISTENT")
            local = []
            for key, row in entries.items():
                qty = quantities[key]
                total = sum(q for q, _ in entry_fills[key])
                if qty < 0 or qty > total or total > row["quantity"]:
                    self._halt("FILLED_POSITION_OUTSIDE_INTENT")
                self.store.put("remaining:" + key, qty)
                if qty:
                    local.append(dict(contract_id=row["finam_symbol"],
                                      quantity=qty if row["direction"] == "LONG" else -qty))
            local_orders = [dict(order_id=oid) for oid, (_, v) in by_id.items() if v.active]
            result = reconcile(local, [dict(contract_id=s, quantity=q) for s, q in positions.items()],
                               local_orders, [dict(order_id=v.order_id) for v in orders if v.active])
            if result != Reconciliation.RECONCILED:
                self._halt("RECONCILIATION_" + result.value)

        for key, row in entries.items():
            qty = quantities[key]
            if not qty:
                if entry_fills[key]:
                    # Only after verified flat: cancel residual entry and stop.
                    for oid, (intent, view) in by_id.items():
                        if intent["payload"]["entry_key"] == key and view.active:
                            self.broker.cancel(oid)
                            self.store.transition_intent(intent["idempotency_key"], "CANCELLED", oid)
                    self.store.transition_intent(key, "CLOSED")
                    # Broker confirmed flat; release durable local risk reserve.
                    risks = self.store.get("risk_reservations", {})
                    if key in risks:
                        del risks[key]
                        self.store.put("risk_reservations", risks)
                elif self.store.intent(key) and self.store.intent(key)["status"] in {"REJECTED", "CANCELLED", "CLOSED"}:
                    risks = self.store.get("risk_reservations", {})
                    if key in risks:
                        del risks[key]
                        self.store.put("risk_reservations", risks)
                continue
            stop_key = key + ":stop"
            stop = self.store.intent(stop_key)
            fills = entry_fills[key]
            average = sum(q*Fraction(p) for q, p in fills)/sum(q for q, _ in fills)
            raw = average - (1 if row["direction"] == "LONG" else -1)*2*Fraction(row["atr"])
            # H1 grid projection requires an on-grid entry; VWAP can be fractional.
            # Use pure outward stop projection for actual VWAP, never round the fill.
            stop_price = project_stop(row["direction"], raw, Decimal(row["price_step"]))
            if stop is None:
                action = self._action(row, "PROTECTIVE_STOP_INSTALL", stop_key, qty, stop_price)
                wire = percent_position_stop_payload(action)
                wire.pop("schema_id")
                wire["client_order_id"] = compact_client_order_id(stop_key)
                self._post_once(stop_key, dict(kind="STOP", entry_key=key, wire=wire))
                return self.recover()  # at most one new stop per entry
            stop_view = unique_order_by_client_id(orders, compact_client_order_id(stop_key))
            if stop_view is None or not stop_view.active:
                self._halt("PROTECTION_UNCONFIRMED_NO_RETRANSMIT")
            installed_stop = Decimal(stop["payload"]["wire"]["sl_price"]["value"])
            risk_record = self.store.get("risk_reservations", {}).get(key)
            if risk_record is not None:
                try:
                    reservation = RiskReservation.restore(risk_record)
                    actual_fills = [
                        (int(x["quantity"]), x["price"], x.get("fee"))
                        for x in snap["fills"]
                        if x["trade_id"] == key and by_id[x["broker_order_id"]][0]["payload"]["kind"] == "ENTRY"
                    ]
                    other = sum(
                        Decimal(str(v["reserved_risk"]))
                        for k, v in self.store.get("risk_reservations", {}).items() if k != key
                    )
                    assessment = revalue_fill(reservation, actual_fills, other_reserved_risk=other)
                except (RiskBlocked, ValueError, KeyError) as exc:
                    self._halt("ACTUAL_FILL_MONEY_AUTHORITY_INVALID:" + str(exc))
                self.store.put("actual_fill_risk:" + key, assessment)
                if assessment["status"] != "PASS":
                    self.store.put("execution_halt", assessment["reason"])
                if installed_stop != Decimal(assessment["projected_stop"]):
                    # Existing 100% protection remains in force. Never cancel/re-post
                    # a broker stop blindly after another partial fill changes VWAP.
                    self.store.put("execution_halt", "ACTUAL_FILL_STOP_UPDATE_UNCONFIRMED")
            elif average != Decimal(row["reference_entry"]) or installed_stop != stop_price:
                self.store.put("execution_halt", "ACTUAL_FILL_RISK_REQUIRES_V20_04_4")
        if uncertain:
            self._halt("UNCERTAIN_POST_NO_RETRANSMIT")
        return {"mode": "OFFLINE_FAKE_ONLY", "reconciliation": "RECONCILED",
                "positions": positions, "halt": self.store.get("execution_halt")}

    def request_frozen_exit(self, entry_key):
        """Execute caller's frozen time-exit decision; retain stop until flat."""
        self.recover()
        row = self.store.get("execution_entries", {})[entry_key]
        qty = self.store.get("remaining:" + entry_key, 0)
        if not qty:
            return
        views = order_views(self.broker.snapshot())
        view = unique_order_by_client_id(views, compact_client_order_id(entry_key))
        if view is not None and view.active:
            self.broker.cancel(view.order_id)  # residual entry cannot refill after exit
        key = entry_key + ":exit"
        action = self._action(row, "EMERGENCY_EXIT_REQUIRED", key, qty)
        self._post_once(key, dict(kind="EXIT", entry_key=entry_key,
                                 wire=self._market(action, exit_order=True)))
        self.recover()
