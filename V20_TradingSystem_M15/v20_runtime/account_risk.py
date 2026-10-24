"""04.4 offline account risk authority using frozen H1 sizing/margin/grid.

No FINAM transport, trading, credentials, mutable H1 code or new trade logic.
Caller must supply explicit account-bound financial evidence and atomically persist
returned reservations alongside its intent. Unknown evidence always blocks.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from fractions import Fraction

from TradingSystemLab.stage8_robot.execution_grid import project_stop, require_on_grid
from TradingSystemLab.stage8_robot.margin import cap_r15_by_margin, floor_to_trade_lot
from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position
from TradingSystemLab.stage8_robot.broker import compact_client_order_id

RISK_PER_TRADE = Decimal("0.015")  # existing frozen H1 R15
MAX_ACCOUNT_RISK = Decimal("0.06")  # existing V20 roadmap


class RiskBlocked(ValueError):
    """Fail closed; never turn missing evidence into estimated risk capacity."""


def _positive(value, label):
    try:
        number = Decimal(str(value))
    except (ValueError, ArithmeticError, TypeError) as exc:
        raise RiskBlocked("INVALID_" + label) from exc
    if not number.is_finite() or number <= 0:
        raise RiskBlocked("INVALID_" + label)
    return number


def _nonnegative(value, label):
    try:
        number = Decimal(str(value))
    except (ValueError, ArithmeticError, TypeError) as exc:
        raise RiskBlocked("INVALID_" + label) from exc
    if not number.is_finite() or number < 0:
        raise RiskBlocked("INVALID_" + label)
    return number


@dataclass(frozen=True)
class AccountAuthority:
    account_id: str
    realized_equity: Decimal
    available_cash: Decimal
    price_step: Decimal
    tick_value: Decimal
    initial_margin: Decimal
    trade_lot_size: int
    roundtrip_cost_per_contract: Decimal
    snapshot_revision: int | None = None
    margin_reflected_client_ids: tuple[str, ...] = ()

    def record(self):
        return {name: str(getattr(self, name)) if isinstance(getattr(self, name), Decimal)
                else getattr(self, name) for name in self.__dataclass_fields__}

    def __post_init__(self):
        if not isinstance(self.account_id, str) or not self.account_id.strip():
            raise RiskBlocked("ACCOUNT_ID_UNKNOWN")
        for name in ("realized_equity", "price_step", "tick_value", "initial_margin"):
            object.__setattr__(self, name, _positive(getattr(self, name), name.upper()))
        for name in ("available_cash", "roundtrip_cost_per_contract"):
            object.__setattr__(self, name, _nonnegative(getattr(self, name), name.upper()))
        if type(self.trade_lot_size) is not int or self.trade_lot_size <= 0:
            raise RiskBlocked("TRADE_LOT_SIZE_INVALID")
        if self.snapshot_revision is not None and (type(self.snapshot_revision) is not int or self.snapshot_revision < 0):
            raise RiskBlocked("SNAPSHOT_REVISION_INVALID")
        ids = self.margin_reflected_client_ids
        if (not isinstance(ids, tuple) or len(set(ids)) != len(ids)
                or any(not isinstance(x, str) or not x for x in ids)):
            raise RiskBlocked("MARGIN_REFLECTION_EVIDENCE_INVALID")
        if ids and self.snapshot_revision is None:
            raise RiskBlocked("MARGIN_REFLECTION_WITHOUT_SNAPSHOT")


@dataclass(frozen=True)
class RiskReservation:
    account_id: str
    entry_key: str
    symbol: str
    direction: str
    quantity: int
    planned_entry: Decimal
    initial_stop: Decimal
    atr14: Decimal
    price_step: Decimal
    tick_value: Decimal
    initial_margin: Decimal
    cost_per_contract: Decimal
    reserved_risk: Decimal
    reserved_margin: Decimal
    realized_equity: Decimal
    reserved_cost: Decimal = Decimal("0")

    def __post_init__(self):
        if (any(not isinstance(v, str) or not v for v in (self.account_id, self.entry_key, self.symbol))
                or self.direction not in {"LONG", "SHORT"}
                or type(self.quantity) is not int or self.quantity <= 0):
            raise RiskBlocked("RESERVATION_IDENTITY_INVALID")
        for name in ("planned_entry", "initial_stop", "atr14", "price_step", "tick_value",
                     "initial_margin", "reserved_risk", "reserved_margin", "realized_equity"):
            object.__setattr__(self, name, _positive(getattr(self, name), name.upper()))
        object.__setattr__(self, "cost_per_contract", _nonnegative(self.cost_per_contract, "COST"))
        object.__setattr__(self, "reserved_cost", _nonnegative(self.reserved_cost, "RESERVED_COST"))

    def record(self) -> dict:
        return {name: str(getattr(self, name)) if isinstance(getattr(self, name), Decimal)
                else getattr(self, name) for name in self.__dataclass_fields__}

    @classmethod
    def restore(cls, raw: dict):
        # Earlier published fake-only journals predate the cash cost reserve.
        raw = dict(raw) if isinstance(raw, dict) else raw
        if isinstance(raw, dict) and "reserved_cost" not in raw:
            raw["reserved_cost"] = str(_nonnegative(raw.get("cost_per_contract"), "COST")
                                       * _positive(raw.get("quantity"), "QUANTITY"))
        if not isinstance(raw, dict) or set(raw) != set(cls.__dataclass_fields__):
            raise RiskBlocked("RESERVATION_SCHEMA_INVALID")
        decs = {"planned_entry", "initial_stop", "atr14", "price_step", "tick_value",
                "initial_margin", "cost_per_contract", "reserved_risk", "reserved_margin",
                "realized_equity", "reserved_cost"}
        try:
            return cls(**{k: Decimal(str(v)) if k in decs else v for k, v in raw.items()})
        except (ValueError, ArithmeticError, TypeError) as exc:
            raise RiskBlocked("RESERVATION_VALUE_INVALID") from exc


def _committed(authority, reservations, key):
    used_cash = Decimal("0")
    used_risk = Decimal("0")
    for old in reservations:
        if not isinstance(old, RiskReservation):
            raise RiskBlocked("RESERVATION_INVALID")
        if old.account_id != authority.account_id:
            raise RiskBlocked("CROSS_ACCOUNT_RESERVATION")
        if old.entry_key == key:
            raise RiskBlocked("ENTRY_KEY_ALREADY_RESERVED")
        if (old.quantity <= 0 or not old.reserved_risk.is_finite()
                or old.reserved_risk <= 0 or not old.reserved_margin.is_finite()
                or old.reserved_margin <= 0):
            raise RiskBlocked("RESERVATION_CORRUPT")
        if compact_client_order_id(old.entry_key) not in authority.margin_reflected_client_ids:
            used_cash += old.reserved_margin
        used_cash += old.reserved_cost  # only unpaid costs, not broker-accounted fees
        used_risk += old.reserved_risk
    return used_cash, used_risk


def reserve_entry(*, authority: AccountAuthority, entry_key: str, symbol: str,
                  direction: str, entry, atr14, planned_max_quantity: int,
                  current_reservations=()) -> RiskReservation:
    """Conservatively reserve local cash and worst-case frozen stop loss.

    available_cash is broker free capacity at snapshot time; local reservations
    account for concurrent intents not reflected in that snapshot. Do not
    subtract broker-reported already reserved funds a second time.
    """
    if not isinstance(entry_key, str) or not entry_key or not isinstance(symbol, str) or not symbol:
        raise RiskBlocked("ENTRY_IDENTITY_INVALID")
    if direction not in ("LONG", "SHORT") or type(planned_max_quantity) is not int:
        raise RiskBlocked("ENTRY_SIDE_OR_QUANTITY_INVALID")
    if planned_max_quantity <= 0:
        raise RiskBlocked("ZERO_REFERENCE_QUANTITY")
    price, atr = _positive(entry, "ENTRY_PRICE"), _positive(atr14, "ATR14")
    try:
        require_on_grid(price, authority.price_step)
        side = 1 if direction == "LONG" else -1
        stop = project_stop(direction, price - side * 2 * atr, authority.price_step)
        if (direction == "LONG" and stop >= price) or (direction == "SHORT" and stop <= price):
            raise RiskBlocked("FROZEN_STOP_WRONG_SIDE")
        h1 = size_position(authority.realized_equity, price, stop, ContractEconomics(
            authority.price_step, authority.tick_value, authority.trade_lot_size, True))
    except (ValueError, ArithmeticError) as exc:
        raise RiskBlocked("H1_SIZING_INVALID") from exc
    cost = authority.roundtrip_cost_per_contract
    per_contract = h1.loss_per_contract + cost
    if per_contract <= 0:
        raise RiskBlocked("INVALID_PER_CONTRACT_LOSS")
    cash_committed, risk_committed = _committed(authority, current_reservations, entry_key)
    cash_left = authority.available_cash - cash_committed
    risk_left = MAX_ACCOUNT_RISK * authority.realized_equity - risk_committed
    if cash_left <= 0 or risk_left <= 0:
        raise RiskBlocked("NO_ACCOUNT_RISK_OR_MARGIN_CAPACITY")
    per_entry_limit = min(RISK_PER_TRADE * authority.realized_equity, risk_left)
    lot = authority.trade_lot_size
    permitted = floor_to_trade_lot(
        int((per_entry_limit / per_contract).to_integral_value(rounding=ROUND_FLOOR)), lot)
    risk_limited = floor_to_trade_lot(min(permitted, h1.quantity, planned_max_quantity), lot)
    cash_qty = floor_to_trade_lot(int((cash_left / (authority.initial_margin + cost))
                                      .to_integral_value(rounding=ROUND_FLOOR)), lot)
    risk_limited = min(risk_limited, cash_qty)
    try:
        margin = cap_r15_by_margin(realized_equity=authority.realized_equity,
            entry=price, stop=stop, price_step=authority.price_step,
            tick_value=authority.tick_value, r15_quantity=risk_limited,
            available_cash=cash_left, direction=direction,
            initial_margin=authority.initial_margin, trade_lot_size=lot)
    except (ValueError, ArithmeticError) as exc:
        raise RiskBlocked("H1_MARGIN_INVALID") from exc
    qty = margin.final_quantity
    if qty <= 0:
        raise RiskBlocked("INSUFFICIENT_RISK_OR_MARGIN_FOR_ONE_LOT")
    risk, hold = per_contract * qty, authority.initial_margin * qty
    if (risk > per_entry_limit or risk_committed + risk > MAX_ACCOUNT_RISK * authority.realized_equity
            or cash_committed + hold + cost*qty > authority.available_cash):
        raise RiskBlocked("RISK_OR_MARGIN_CAP_EXCEEDED")
    return RiskReservation(authority.account_id, entry_key, symbol, direction,
                           qty, price, stop, atr, authority.price_step, authority.tick_value,
                           authority.initial_margin, cost, risk, hold,
                           authority.realized_equity, cost*qty)


def revalue_fill(reservation: RiskReservation, fills, *, other_reserved_risk=Decimal("0"),
                 installed_stop=None) -> dict:
    """Reconcile actual VWAP, stop and exposure without modifying an active SLTP.

    Caller must separately confirm 100% SLTP and any required stop amendment.
    FAIL result means HALT NEW ENTRIES, not release protection or liquidate.
    """
    if not fills:
        raise RiskBlocked("NO_FILL_AUTHORITY")
    quantity = 0
    total_price = Fraction(0)
    fees = Decimal("0")
    for item in fills:
        if not isinstance(item, (tuple, list)) or len(item) != 3:
            raise RiskBlocked("FILL_SCHEMA_INVALID")
        q, price, fee = item
        if type(q) is not int or q <= 0:
            raise RiskBlocked("FILL_QUANTITY_INVALID")
        p = _positive(price, "FILL_PRICE")
        fees += _nonnegative(fee, "FILL_FEE")
        quantity += q
        total_price += q * Fraction(p)
    if quantity > reservation.quantity:
        raise RiskBlocked("FILL_OVER_QUANTITY")
    average = total_price / quantity
    side = 1 if reservation.direction == "LONG" else -1
    stop = project_stop(reservation.direction, average - side * 2 * Fraction(reservation.atr14),
                        reservation.price_step)
    actual_stop = stop if installed_stop is None else _positive(installed_stop, "INSTALLED_STOP")
    require_on_grid(actual_stop, reservation.price_step)
    raw_ticks = abs(average - Fraction(actual_stop)) / Fraction(reservation.price_step)
    loss = Decimal(raw_ticks.numerator) / Decimal(raw_ticks.denominator) * reservation.tick_value
    # Known fees replace the already budgeted cost component, never add it twice.
    risk = loss * quantity + max(reservation.cost_per_contract * quantity, fees)
    other = _nonnegative(other_reserved_risk, "OTHER_RISK")
    per_trade_cap = RISK_PER_TRADE * reservation.realized_equity
    account_cap = MAX_ACCOUNT_RISK * reservation.realized_equity
    reason = None
    if risk > per_trade_cap:
        reason = "ACTUAL_FILL_EXCEEDS_R15"
    elif risk + other > account_cap:
        reason = "ACCOUNT_INITIAL_RISK_EXCEEDS_R6"
    return dict(status="PASS" if reason is None else "HALT_NEW_ENTRIES",
                reason=reason, filled_quantity=quantity, average_price=str(average),
                projected_stop=str(stop), actual_risk=str(risk), entry_risk_cap=str(per_trade_cap),
                installed_stop=str(actual_stop), stop_conforms=actual_stop == stop,
                account_risk_cap=str(account_cap), known_fees=str(fees),
                reserved_margin=str(reservation.initial_margin * quantity))
