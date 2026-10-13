"""Stage 8 #493: offline-only funding / frozen FULL-R15 behavior tests.

Every number below is synthetic.  No broker, runtime SQLite, credentials,
Scheduled Task, production authorization, or REAL order endpoints.
These tests demonstrate current code behavior, not a funding-policy decision.
"""
from decimal import Decimal as D

import pytest

from TradingSystemLab.stage8_robot.margin import cap_r15_by_margin
from TradingSystemLab.stage8_robot.production_service import (
    ProductionService,
    ProductionServiceError,
)
from TradingSystemLab.stage8_robot.risk import ContractEconomics, size_position


class MemoryState:
    def __init__(self, external="0", starting="10000", persisted="10000"):
        self.values = {
            "explained_external_cash_flows": external,
            "starting_realized_equity": starting,
            "realized_equity": persisted,
        }

    def get(self, key, default=None):
        return self.values.get(key, default)

    def put(self, key, value):
        self.values[key] = value

    def unresolved_intent_count(self):
        return 0


class FakeRuntime:
    def __init__(self, store):
        self.store = store

    def current_realized_equity(self):
        value = self.store.get("realized_equity")
        return None if value is None else D(str(value))

    def set_realized_equity(self, value):
        assert value > 0
        self.store.put("realized_equity", str(value))


def read_frozen_basis(broker_equity, unrealized="0", external="0", starting="10000"):
    """Exercise actual candidate ProductionService method without __init__."""
    service = object.__new__(ProductionService)
    state = MemoryState(external=external, starting=starting)
    service.runtime = FakeRuntime(state)
    account = {
        "equity": {"value": str(broker_equity)},
        "unrealized_profit": {"value": str(unrealized)},
    }
    basis = ProductionService._realized_basis(service, account, {}, [])
    assert D(str(state.get("realized_equity"))) == basis
    return basis


def size_new_position(basis, available_cash):
    """Real frozen risk.py and margin.py, deliberately synthetic instrument."""
    tick = ContractEconomics(D("0.01"), D("1"), 1, True)
    pre = size_position(basis, D("12.75"), D("12.25"), tick)
    result = cap_r15_by_margin(
        realized_equity=basis, entry=D("12.75"), stop=D("12.25"),
        price_step=D("0.01"), tick_value=D("1"),
        r15_quantity=pre.quantity, available_cash=D(str(available_cash)),
        direction="LONG", initial_margin=D("1000"), trade_lot_size=1,
    )
    return pre, result


def test_funding_increases_new_entry_r15_and_margin_capacity():
    before = read_frozen_basis("10000")
    after = read_frozen_basis("50000")
    next_deposit = read_frozen_basis("55000")
    assert [before, after, next_deposit] == [D("10000"), D("50000"), D("55000")]
    before_r, before_qty = size_new_position(before, "10000")
    after_r, after_qty = size_new_position(after, "50000")
    next_r, next_qty = size_new_position(next_deposit, "55000")
    assert [x.risk_cash for x in (before_r, after_r, next_r)] == [
        D("150"), D("750"), D("825")]
    assert [x.quantity for x in (before_r, after_r, next_r)] == [3, 15, 16]
    assert [x.final_quantity for x in (before_qty, after_qty, next_qty)] == [
        3, 15, 16]
    assert all(x.final_quantity <= x.r15_quantity for x in
               (before_qty, after_qty, next_qty))


def test_unrealized_price_gain_is_not_new_realized_risk():
    assert read_frozen_basis("51000", unrealized="1000") == D("50000")
    assert read_frozen_basis("49500", unrealized="-500") == D("50000")


def test_recording_deposit_as_explained_flow_excludes_it_from_risk():
    # Documents EXISTING service math, not a recommendation to set this key.
    assert read_frozen_basis("50000", external="40000") == D("10000")
    r15, sized = size_new_position(D("10000"), "50000")
    assert r15.risk_cash == D("150")
    assert sized.final_quantity == 3


def test_frozen_sizing_stays_zero_for_narrow_risk_budget():
    r15, sized = size_new_position(D("1000"), "50000")
    assert r15.risk_cash == D("15")
    assert r15.quantity == sized.final_quantity == 0


@pytest.mark.parametrize("value", ["10000", "10001", "NaN", "Infinity"])
def test_invalid_or_excessive_external_flow_fails_closed(value):
    with pytest.raises(ProductionServiceError, match="STAGE8_12_4_REALIZED_EQUITY"):
        read_frozen_basis("10000", external=value)


def test_existing_position_budget_not_retroactively_resized():
    # Historical position evidence is immutable: only a new-entry sizing
    # calculation changes after the simulated funding event.
    saved_position = {"quantity": 3, "risk_cash": "150"}
    assert read_frozen_basis("55000") == D("55000")
    future, next_size = size_new_position(D("55000"), "55000")
    assert saved_position == {"quantity": 3, "risk_cash": "150"}
    assert future.risk_cash == D("825")
    assert next_size.final_quantity == 16
