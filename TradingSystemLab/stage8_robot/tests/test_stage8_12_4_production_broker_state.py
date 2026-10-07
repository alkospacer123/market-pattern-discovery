from __future__ import annotations

import pytest

from TradingSystemLab.stage8_robot.production_broker_state import (
    ProductionBrokerStateError,
    active_sltp_for_trade,
    broker_realized_basis,
    order_for_intent,
    protected_stop_ids_for_position,
    require_no_external_cash_flows,
    require_no_unknown_active_orders,
    order_views,
    position_quantities,
    unique_order_by_client_id,
)


def sltp(order_id, *, client="s8stop", comment="stage8.12:trade-1:stop:0000",
         status="ORDER_STATUS_NEW", symbol="USDRUBF@RTSX"):
    return {
        "order_id": order_id,
        "status": status,
        "sltp_order": {
            "symbol": symbol,
            "side": "SIDE_SELL",
            "quantity_sl": {"value": "100"},
            "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
            "sl_price": {"value": "99.5"},
            "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
            "client_order_id": client,
            "comment": comment,
        },
    }


def regular(order_id, *, client="s8entry", status="ORDER_STATUS_NEW"):
    return {
        "order_id": order_id,
        "status": status,
        "order": {
            "symbol": "USDRUBF@RTSX",
            "quantity": {"value": "2"},
            "side": "SIDE_BUY",
            "type": "ORDER_TYPE_MARKET",
            "time_in_force": "TIME_IN_FORCE_DAY",
            "client_order_id": client,
        },
    }


def test_position_quantities_are_signed_and_zero_rows_are_flat():
    account = {
        "positions": [
            {"symbol": "USDRUBF@RTSX", "quantity": {"value": "2"}},
            {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "-3"}},
            {"symbol": "GLDRUBF@RTSX", "quantity": {"value": "0"}},
        ]
    }
    assert position_quantities(account) == {
        "USDRUBF@RTSX": 2,
        "CNYRUBF@RTSX": -3,
    }

    duplicate = {
        "positions": [
            {"symbol": "USDRUBF@RTSX", "quantity": {"value": "1"}},
            {"symbol": "USDRUBF@RTSX", "quantity": {"value": "1"}},
        ]
    }
    with pytest.raises(ProductionBrokerStateError, match="POSITIONS_SCHEMA_INVALID"):
        position_quantities(duplicate)


def test_order_views_distinguish_regular_and_sltp_without_owning_manual_history():
    manual_terminal = sltp(
        "MANUAL",
        client="manual",
        comment="manual-order",
        status="ORDER_STATUS_EXECUTED",
    )
    manual_terminal["sltp_order"]["quantity_sl"] = {"value": "2"}
    manual_terminal["sltp_order"].pop("sl_qty_measure")
    views = order_views({"orders": [regular("R1"), manual_terminal]})
    assert [view.kind for view in views] == ["REGULAR", "SLTP"]
    assert views[0].active is True
    assert views[1].active is False


def test_production_owned_active_sltp_must_preserve_close_only_contract():
    malformed = sltp("BAD")
    malformed["sltp_order"]["quantity_sl"] = {"value": "2"}
    views = order_views({"orders": [malformed]})
    with pytest.raises(
        ProductionBrokerStateError,
        match="SLTP_CLOSE_ONLY_CONTRACT_INVALID",
    ):
        active_sltp_for_trade(
            views, trade_id="trade-1", symbol="USDRUBF@RTSX"
        )


def test_terminal_sltp_is_not_active_and_trade_filter_is_identity_specific():
    views = order_views({
        "orders": [
            sltp("OLD", client="old", status="ORDER_STATUS_REPLACED"),
            sltp("A", client="a", comment="stage8.12:trade-1:stop:0001"),
            sltp("B", client="b", comment="stage8.12:trade-1:stop:0002"),
            sltp(
                "C",
                client="c",
                comment="stage8.12:trade-2:stop:0000",
                symbol="CNYRUBF@RTSX",
            ),
        ]
    })
    trade1 = active_sltp_for_trade(
        views, trade_id="trade-1", symbol="USDRUBF@RTSX"
    )
    assert [view.order_id for view in trade1] == ["A", "B"]
    assert active_sltp_for_trade(
        views, trade_id="trade-2", symbol="CNYRUBF@RTSX"
    )[0].order_id == "C"


def test_duplicate_client_order_id_fails_closed():
    views = order_views({
        "orders": [
            regular("R1", client="same"),
            sltp("S1", client="same"),
        ]
    })
    with pytest.raises(
        ProductionBrokerStateError,
        match="DUPLICATE_CLIENT_ORDER_ID",
    ):
        unique_order_by_client_id(views, "same")


def test_unknown_order_status_and_ambiguous_order_kind_fail_closed():
    bad = regular("R1")
    bad["status"] = "ORDER_STATUS_UNSPECIFIED"
    with pytest.raises(ProductionBrokerStateError, match="ORDER_STATUS_INVALID"):
        order_views({"orders": [bad]})

    ambiguous = regular("R2")
    ambiguous["sltp_order"] = sltp("S2")["sltp_order"]
    with pytest.raises(ProductionBrokerStateError, match="ORDER_KIND_INVALID"):
        order_views({"orders": [ambiguous]})


def test_realized_basis_excludes_unrealized_profit():
    account = {
        "equity": {"value": "100500.25"},
        "unrealized_profit": {"value": "500.25"},
    }
    assert broker_realized_basis(account) == Decimal("100000.00")


def test_external_cash_flow_categories_fail_closed():
    assert require_no_external_cash_flows({
        "transactions": [
            {"transaction_category": "TRANSACTION_CATEGORY_COMMISSION"},
            {"transaction_category": "INCOME"},
        ]
    }) == 2
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPLAINED_EXTERNAL_CASH_FLOW",
    ):
        require_no_external_cash_flows({
            "transactions": [{"transaction_category": "DEPOSIT"}]
        })


def test_unknown_active_order_is_not_production_authority():
    orders = order_views({
        "orders": [{
            "order_id": "manual-1",
            "status": "ORDER_STATUS_NEW",
            "order": {
                "symbol": "USDRUBF@RTSX",
                "quantity": {"value": "1"},
                "side": "SIDE_BUY",
                "type": "ORDER_TYPE_MARKET",
                "time_in_force": "TIME_IN_FORCE_DAY",
                "client_order_id": "manual1",
            },
        }]
    })
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPECTED_ACTIVE_ORDER",
    ):
        require_no_unknown_active_orders(orders, [])


def test_intent_order_matching_and_exact_current_stop_authority():
    trade_id = "trade-1"
    stop0 = f"stage8.12:{trade_id}:stop:0000"
    stop1 = f"stage8.12:{trade_id}:stop:0001"
    orders = order_views({
        "orders": [
            {
                "order_id": "S0",
                "status": "ORDER_STATUS_WATCHING",
                "sltp_order": {
                    "symbol": "USDRUBF@RTSX",
                    "side": "SIDE_SELL",
                    "quantity_sl": {"value": "100"},
                    "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                    "sl_price": {"value": "99.90"},
                    "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
                    "client_order_id": "s8old",
                    "comment": stop0,
                },
            },
            {
                "order_id": "S1",
                "status": "ORDER_STATUS_WATCHING",
                "sltp_order": {
                    "symbol": "USDRUBF@RTSX",
                    "side": "SIDE_SELL",
                    "quantity_sl": {"value": "100"},
                    "sl_qty_measure": "SLTP_QTY_MEASURE_PERCENT",
                    "sl_price": {"value": "99.95"},
                    "valid_before": "VALID_BEFORE_GOOD_TILL_CANCEL",
                    "client_order_id": "s8new",
                    "comment": stop1,
                },
            },
        ]
    })
    matched = order_for_intent(orders, idempotency_key=stop1)
    assert matched is not None and matched.order_id == "S1"
    position = {
        "trade_id": trade_id,
        "finam_symbol": "USDRUBF@RTSX",
        "direction": "LONG",
        "protective_stop_broker_order_id": "S1",
        "protective_stop_price": "99.95",
    }
    assert protected_stop_ids_for_position(
        orders, position=position
    ) == ["S0", "S1"]

    position["protective_stop_price"] = "99.94"
    with pytest.raises(
        ProductionBrokerStateError,
        match="UNEXPECTED_TIGHTER_STOP",
    ):
        protected_stop_ids_for_position(orders, position=position)
