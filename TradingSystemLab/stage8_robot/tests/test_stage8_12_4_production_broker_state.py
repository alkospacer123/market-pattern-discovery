from decimal import Decimal

import pytest

from TradingSystemLab.stage8_robot.production_broker_state import (
    ProductionBrokerStateError,
    active_protection_for_position,
    broker_positions,
    broker_realized_basis,
    parse_orders,
    require_no_external_cash_flows,
    require_no_unknown_active_orders,
)


def account(positions=None):
    return {
        "equity": {"value": "100500"},
        "unrealized_profit": {"value": "500"},
        "positions": positions or [],
    }


def normal_order(order_id="O1", status="ORDER_STATUS_NEW", client="s8abc"):
    return {
        "order_id": order_id,
        "status": status,
        "order": {
            "symbol": "USDRUBF@RTSX",
            "side": "SIDE_BUY",
            "client_order_id": client,
        },
    }


def sltp(order_id, comment, price="99.95", status="ORDER_STATUS_WATCHING"):
    return {
        "order_id": order_id,
        "status": status,
        "sltp_order": {
            "symbol": "USDRUBF@RTSX",
            "side": "SIDE_SELL",
            "client_order_id": "x",
            "comment": comment,
            "quantity_sl": {"value": "100"},
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "sl_price": {"value": price},
        },
    }


def test_signed_positions_and_realized_basis():
    positions = [
        {"symbol": "USDRUBF@RTSX", "quantity": {"value": "2"}},
        {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "-3"}},
        {"symbol": "GLDRUBF@RTSX", "quantity": {"value": "0"}},
    ]
    parsed = broker_positions(
        account(positions),
        finam_to_instrument={
            "USDRUBF@RTSX": "USDRUBF",
            "CNYRUBF@RTSX": "CNYRUBF",
            "GLDRUBF@RTSX": "GLDRUBF",
            "IMOEXF@RTSX": "IMOEXF",
        },
    )
    assert parsed["USDRUBF"] == 2
    assert parsed["CNYRUBF"] == -3
    assert broker_realized_basis(account(positions)) == Decimal("100000")


def test_unknown_nonzero_position_fails_closed():
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPECTED_NON_N4_BROKER_POSITION",
    ):
        broker_positions(
            account([{"symbol": "SBER@MISX", "quantity": {"value": "1"}}]),
            finam_to_instrument={},
        )


def test_external_cash_flows_block_realized_equity_authority():
    require_no_external_cash_flows({
        "transactions": [
            {"transaction_category": "COMMISSION"},
            {"transaction_category": "INCOME"},
        ]
    })
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPLAINED_EXTERNAL_CASH_FLOW",
    ):
        require_no_external_cash_flows({
            "transactions": [{"transaction_category": "DEPOSIT"}]
        })


def test_unknown_active_order_fails_closed():
    parsed = parse_orders({"orders": [normal_order()]})
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPECTED_ACTIVE_BROKER_ORDER",
    ):
        require_no_unknown_active_orders(parsed, [])


def test_position_protection_requires_current_stop_and_allows_looser_backstop():
    trade = "trade-1"
    current_comment = f"stage8.12:{trade}:stop:0001"
    old_comment = f"stage8.12:{trade}:stop:0000"
    rows = parse_orders({
        "orders": [
            sltp("S0", old_comment, price="99.90"),
            sltp("S1", current_comment, price="99.95"),
        ]
    })
    position = {
        "trade_id": trade,
        "finam_symbol": "USDRUBF@RTSX",
        "direction": "LONG",
        "protective_stop_price": "99.95",
        "protective_stop_broker_order_id": "S1",
    }
    assert active_protection_for_position(rows, position) == ["S0", "S1"]


def test_position_protection_rejects_tighter_unknown_stop():
    trade = "trade-1"
    rows = parse_orders({
        "orders": [
            sltp("S1", f"stage8.12:{trade}:stop:0001", price="99.95"),
            sltp("S2", f"stage8.12:{trade}:stop:9999", price="100.00"),
        ]
    })
    position = {
        "trade_id": trade,
        "finam_symbol": "USDRUBF@RTSX",
        "direction": "LONG",
        "protective_stop_price": "99.95",
        "protective_stop_broker_order_id": "S1",
    }
    with pytest.raises(
        ProductionBrokerStateError,
        match="BROKER_PROTECTIVE_STOP_UNEXPECTEDLY_TIGHTER",
    ):
        active_protection_for_position(rows, position)
