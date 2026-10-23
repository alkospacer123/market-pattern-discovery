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
from TradingSystemLab.stage8_robot.margin import portfolio_authority, AVAILABLE_CASH_SEMANTICS

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
        self.revision = 0
        self.financials = None
        self.on_change = None

    def _checkpoint(self):
        if self.on_change is not None:
            self.on_change(self.export())

    def submit(self, wire, *, sltp=False, kind=None, trade_id=None):
        self.post_count += 1
        fault, self.next_fault = self.next_fault, None
        if fault == "rejected":
            self.revision += 1; self._checkpoint()
            raise FinamOrderRejected(400)
        if fault == "timeout_before_accept":
            self.revision += 1; self._checkpoint()
            raise FinamUncertainSubmission("SIMULATED_NO_ACK")
        oid = f"fake-{self.post_count}"
        self.orders.append(dict(order_id=oid, status="NEW",
                                fake_kind=kind or ("STOP" if sltp else "ENTRY"),
                                fake_trade_id=trade_id,
                                **{"sltp_order" if sltp else "order": deepcopy(wire)}))
        self.revision += 1
        self._checkpoint()  # broker book survives an ACK lost to the robot process
        if fault == "timeout_after_accept":
            raise FinamUncertainSubmission("SIMULATED_ACK_LOST")
        return {"order_id": oid}  # deliberately no fill authority

    def fill(self, order_id, trade_id, quantity, price, timestamp, fee="0"):
        row = next(x for x in self.orders if x["order_id"] == order_id)
        wire = row.get("order", row.get("sltp_order"))
        if row["status"] not in {"NEW", "PARTIAL_FILL"} or type(quantity) is not int or quantity <= 0:
            raise ExecutionBlocked("FAKE_TERMINAL_OR_INVALID_FILL")
        if "sltp_order" in row:
            current = position_quantities(self.snapshot()).get(wire["symbol"], 0)
            if not current or quantity > abs(current):
                raise ExecutionBlocked("FAKE_STOP_MUST_REDUCE_CURRENT_POSITION")
            target_remaining = abs(current)
        else:
            old_qty = sum(int(x["quantity"]) for x in self.fills if x["broker_order_id"] == order_id)
            target_remaining = int(wire["quantity"]["value"]) - old_qty
            if quantity > target_remaining:
                raise ExecutionBlocked("FAKE_OVERFILL")
        self.fills.append(dict(fill_id=f"fill-{len(self.fills)+1}",
                               broker_order_id=order_id, trade_id=trade_id,
                               quantity=str(quantity), price=str(price), fee=str(fee),
                               timestamp=timestamp))
        row["status"] = "FILLED" if quantity == target_remaining else "PARTIAL_FILL"
        self.revision += 1
        self._checkpoint()

    def cancel(self, order_id):
        next(x for x in self.orders if x["order_id"] == order_id)["status"] = "CANCELLED"
        self.revision += 1
        self._checkpoint()

    def configure_funds(self, *, realized_equity, available_cash, margins):
        """Explicit fake account baseline, never an estimate of real FINAM GO."""
        self.financials = dict(realized_equity=str(realized_equity),
                               available_cash=str(available_cash), margins=deepcopy(margins))
        self.revision += 1
        self._checkpoint()

    def financial_snapshot(self):
        if self.financials is None:
            raise ExecutionBlocked("FAKE_FINANCIAL_SOURCE_NOT_CONFIGURED")
        bindings = _load_registry()
        committed, pnl = Decimal(0), Decimal(0)
        covered = []
        for row in self.orders:
            if row.get("fake_kind") != "ENTRY":
                continue
            wire = row["order"]
            symbol = wire["symbol"].split("@")[0]
            side = 1 if wire["side"] == "SIDE_BUY" else -1
            entry_fills = [f for f in self.fills if f["broker_order_id"] == row["order_id"]]
            quantity = sum(int(f["quantity"]) for f in entry_fills)
            trade_ids = {f["trade_id"] for f in entry_fills}
            closed = [f for f in self.fills if f["trade_id"] in trade_ids
                      and f["broker_order_id"] != row["order_id"]]
            closed_qty = sum(int(f["quantity"]) for f in closed)
            pending = max(0, int(wire["quantity"]["value"]) - quantity) if row["status"] in {"NEW", "PARTIAL_FILL"} else 0
            margin = Decimal(self.financials["margins"][symbol]["LONG" if side == 1 else "SHORT"])
            committed += (quantity - closed_qty + pending)*margin
            covered.append(wire["client_order_id"])
            if closed and quantity:
                average = sum(Decimal(f["price"])*int(f["quantity"]) for f in entry_fills)/quantity
                multiplier = Decimal(bindings[symbol]["tick_value"])/Decimal(bindings[symbol]["price_step"])
                pnl += sum((Decimal(f["price"])-average)*side*int(f["quantity"])*multiplier for f in closed)
        fees = sum((Decimal(f.get("fee", "0")) for f in self.fills), Decimal(0))
        equity = Decimal(self.financials["realized_equity"]) + pnl - fees
        cash = Decimal(self.financials["available_cash"]) + pnl - fees - committed
        return dict(revision=self.revision, realized_equity=str(equity),
                    available_cash=str(cash), money_reserved=str(committed),
                    margin_reflected_client_ids=tuple(sorted(covered)))

    def authority(self, symbol, direction):
        evidence = self.financial_snapshot()
        binding = _load_registry()[symbol]
        # Same H1 parser/available_cash semantics, with explicit fake evidence.
        funds = portfolio_authority(dict(type="FORTS", portfolio_forts=dict(
            available_cash={"value": evidence["available_cash"]},
            money_reserved={"value": evidence["money_reserved"]})))
        return AccountAuthority(self.account_id, Decimal(evidence["realized_equity"]),
                                funds.available_cash, Decimal(binding["price_step"]),
                                Decimal(binding["tick_value"]),
                                Decimal(self.financials["margins"][symbol][direction]),
                                int(binding["quantity_granularity"]),
                                2*Decimal(binding["tick_value"]), evidence["revision"],
                                evidence["margin_reflected_client_ids"])

    def export(self):
        return deepcopy({k: getattr(self, k) for k in
                         ("account_id", "orders", "fills", "post_count", "next_fault", "revision", "financials")})

    @classmethod
    def restore(cls, book):
        broker = cls(book["account_id"])
        for key in ("orders", "fills", "post_count", "next_fault", "revision", "financials"):
            setattr(broker, key, deepcopy(book[key]))
        return broker

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

    M15OfflineRobot supplies frozen signals/plans and observed-session exits.
    Autonomous mode requires fresh account-bound monetary evidence; the older
    optional-authority interface is fake-only compatibility, never production.
    Actual fills are valued against installed protection. An unconfirmed stop
    amendment blocks new entries and retains the previous 100% backstop.
    """
    def __init__(self, root, robot_id, account_id, broker, *, require_money_authority=False):
        if type(broker) is not FakeBroker or broker.account_id != account_id:
            raise ExecutionBlocked("EXACT_OFFLINE_FAKE_ACCOUNT_REQUIRED")
        self.broker = broker
        self.journal = _ExecutionJournal(root, robot_id, account_id)
        self.store = self.journal._require_open()
        self.money_required = require_money_authority or self.store.get("money_required", False)
        if self.money_required:
            self.store.put("money_required", True)

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
            self.broker.submit(payload["wire"], sltp=payload["kind"] == "STOP",
                               kind=payload["kind"], trade_id=payload["entry_key"])
        except FinamOrderRejected:
            self.store.transition_intent(key, "REJECTED")
            if payload["kind"] != "ENTRY":
                self._halt("PROTECTION_OR_EXIT_REJECTED")
        except Exception:
            # Even an unfamiliar exception beyond this boundary cannot prove no POST.
            self.store.transition_intent(key, "UNCERTAIN")

    def submit_entry(self, signal, entry, *, price_step, account_authority=None):
        if self.money_required and account_authority is None:
            raise ExecutionBlocked("ACCOUNT_MONEY_AUTHORITY_REQUIRED")
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
            # A money cap may have reduced the original reference quantity.
            if entry.quantity < existing[key]["quantity"]:
                self._halt("CONFLICTING_ENTRY_REPLAY")
            row["quantity"] = existing[key]["quantity"]
            self.journal.record_reference(signal, replace(entry, quantity=row["quantity"]))
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
            raise ExecutionBlocked("ONE_OPEN_POSITION_PER_SYMBOL")
        # Required in autonomous mode; optional only for older fake-only tests.
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
            if account_authority.tick_value != Decimal(binding["tick_value"]):
                self._halt("ACCOUNT_MONEY_TICK_VALUE_MISMATCH")
            if self.money_required:
                if account_authority != self.broker.authority(entry.symbol, entry.direction):
                    raise ExecutionBlocked("STALE_OR_UNVERIFIED_ACCOUNT_SNAPSHOT")
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
                raise ExecutionBlocked("ACCOUNT_RISK_" + str(exc)) from exc
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
                authorities = self.store.get("risk_authorities", {})
                authorities[key] = dict(account_authority.record(),
                    available_cash_semantics=AVAILABLE_CASH_SEMANTICS,
                    mode="OFFLINE_FAKE_ONLY")
                self.store.put("risk_authorities", authorities)
            # Intent, session quota and account risk reservation commit together.
            payload = dict(kind="ENTRY", entry_key=key,
                           wire=self._market(self._action(row, "ENTRY", key)))
            self.store.persist_intent(key, payload)
        # _post_once deliberately refuses an already-persisted intent; first dispatch
        # marks it SUBMITTED before leaving SQLite. A restart never repeats it.
        self.store.transition_intent(key, "SUBMITTED")
        try:
            self.broker.submit(payload["wire"], kind="ENTRY", trade_id=key)
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
                    assessment = revalue_fill(reservation, actual_fills, other_reserved_risk=other,
                                               installed_stop=installed_stop)
                except (RiskBlocked, ValueError, KeyError) as exc:
                    # Positions/fills and active stop were already reconciled.
                    # Missing money evidence forbids entries, not risk reduction.
                    reason = "ACTUAL_FILL_MONEY_AUTHORITY_INVALID:" + str(exc)
                    self.store.put("execution_halt", reason)
                    self.store.put("actual_fill_risk:"+key,
                                   dict(status="HALT_NEW_ENTRIES", reason=reason))
                    continue
                self.store.put("actual_fill_risk:" + key, assessment)
                total_filled = sum(q for q, _, _ in actual_fills)
                entry_view = unique_order_by_client_id(orders, compact_client_order_id(key))
                pending = max(0, reservation.quantity - total_filled) if entry_view.active else 0
                planned_unit_risk = (abs(reservation.planned_entry - reservation.initial_stop)
                                     / reservation.price_step * reservation.tick_value
                                     + reservation.cost_per_contract)
                committed_risk = Decimal(assessment["actual_risk"])*qty/total_filled + pending*planned_unit_risk
                records = self.store.get("risk_reservations", {})
                known_entry_fees = sum(Decimal(fee) for _, _, fee in actual_fills)
                outstanding_cost = max(Decimal(0), reservation.cost_per_contract*(qty + pending)
                                        - known_entry_fees*qty/total_filled)
                records[key] = replace(reservation, reserved_risk=committed_risk,
                                       reserved_margin=(qty + pending)*reservation.initial_margin,
                                       reserved_cost=outstanding_cost).record()
                self.store.put("risk_reservations", records)
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
        if self.money_required:
            if self.broker.financials is None:
                self.store.put("execution_halt", "ACCOUNT_FINANCIAL_SOURCE_UNAVAILABLE")
            else:
                try:
                    financial = self.broker.financial_snapshot()
                    total_risk = sum((RiskReservation.restore(v).reserved_risk for v in
                                      self.store.get("risk_reservations", {}).values()), Decimal(0))
                    if total_risk > Decimal(financial["realized_equity"])*Decimal("0.06"):
                        self.store.put("execution_halt", "ACCOUNT_INITIAL_RISK_EXCEEDS_R6")
                    elif not any(quantities.values()) and self.store.get("execution_halt") in {
                            "ACTUAL_FILL_STOP_UPDATE_UNCONFIRMED", "ACTUAL_FILL_EXCEEDS_R15",
                            "ACCOUNT_INITIAL_RISK_EXCEEDS_R6", "ACCOUNT_FINANCIAL_SOURCE_UNAVAILABLE",
                            "M15_PATH_CENSORED_RECONCILE_REQUIRED"}:
                        self.store.put("execution_halt", None)
                except (RiskBlocked, ValueError, ArithmeticError, KeyError):
                    self.store.put("execution_halt", "ACCOUNT_FINANCIAL_SOURCE_UNAVAILABLE")
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
