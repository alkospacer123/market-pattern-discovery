from __future__ import annotations

import pytest

from TradingSystemLab.stage8_robot.production_broker_state import (
    ProductionBrokerStateError,
    active_sltp_for_trade,
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


@pytest.mark.parametrize(
    "status",
    [
        "ORDER_STATUS_FILLED",
        "ORDER_STATUS_CANCELLED",
        "ORDER_STATUS_EXECUTED",
        "ORDER_STATUS_REPLACED",
        "ORDER_STATUS_SL_EXECUTED",
        "ORDER_STATUS_TP_EXECUTED",
    ],
)
@pytest.mark.parametrize("kind", ["REGULAR", "SLTP"])
def test_terminal_empty_client_id_is_history_only(status, kind):
    """FINAM terminal manual history may have a genuinely empty client ID."""
    entry = regular("OLD", client="", status=status) if kind == "REGULAR" else sltp(
        "OLD", client="", status=status, comment="manual-order"
    )
    result = order_views({"orders": [entry]})
    assert len(result) == 1
    assert result[0].kind == kind
    assert result[0].client_order_id == ""
    assert result[0].active is False


@pytest.mark.parametrize(
    "status",
    [
        "ORDER_STATUS_NEW",
        "ORDER_STATUS_WATCHING",
        "ORDER_STATUS_PENDING_CANCEL",
        "ORDER_STATUS_PARTIAL_FILL",
        "ORDER_STATUS_WAIT",
        "ORDER_STATUS_SL_GUARD_TIME",
    ],
)
@pytest.mark.parametrize("kind", ["REGULAR", "SLTP"])
def test_active_empty_client_id_still_fails_closed(status, kind):
    entry = regular("ACTIVE", client="", status=status) if kind == "REGULAR" else sltp(
        "ACTIVE", client="", status=status
    )
    with pytest.raises(ProductionBrokerStateError, match="ORDER_REQUEST_INVALID"):
        order_views({"orders": [entry]})


@pytest.mark.parametrize("client", [None, 123, [], "X" * 21])
@pytest.mark.parametrize("kind", ["REGULAR", "SLTP"])
def test_terminal_missing_or_nonstring_or_oversized_client_id_remains_invalid(client, kind):
    entry = regular("OLD", client=client, status="ORDER_STATUS_EXECUTED") if kind == "REGULAR" else sltp(
        "OLD", client=client, status="ORDER_STATUS_EXECUTED"
    )
    with pytest.raises(ProductionBrokerStateError, match="ORDER_REQUEST_INVALID"):
        order_views({"orders": [entry]})


@pytest.mark.parametrize("status", ["ORDER_STATUS_UNSPECIFIED", "ORDER_STATUS_NOT_REAL", None])
def test_empty_client_id_never_legalizes_ambiguous_status(status):
    with pytest.raises(ProductionBrokerStateError, match="ORDER_STATUS_INVALID"):
        order_views({"orders": [regular("OLD", client="", status=status)]})


def test_terminal_empty_history_does_not_hide_active_order():
    entries = [
        regular("MANUAL", client="", status="ORDER_STATUS_FILLED"),
        sltp("MANUAL_SL", client="", status="ORDER_STATUS_EXECUTED"),
        regular("LIVE", client="live_order", status="ORDER_STATUS_NEW"),
    ]
    result = order_views({"orders": entries})
    assert len(result) == 3
    assert [o.order_id for o in result if o.active] == ["LIVE"]
    assert unique_order_by_client_id(result, "live_order").order_id == "LIVE"
    assert unique_order_by_client_id(result, "absent") is None


@pytest.mark.parametrize("field,value", [
    ("symbol", ""),
    ("side", "SIDE_UNKNOWN"),
    ("comment", "x" * 129),
    ("quantity", {"value": "1.5"}),
])
def test_terminal_empty_client_id_cannot_override_other_order_contracts(field, value):
    entry = regular("OLD", client="", status="ORDER_STATUS_FILLED")
    entry["order"][field] = value
    with pytest.raises(ProductionBrokerStateError, match="ORDER_REQUEST_INVALID|ORDER_QUANTITY_INVALID"):
        order_views({"orders": [entry]})


def test_terminal_empty_client_id_cannot_hide_duplicate_broker_order_id():
    with pytest.raises(ProductionBrokerStateError, match="ORDER_ID_INVALID"):
        order_views({"orders": [
            regular("SAME", client="", status="ORDER_STATUS_FILLED"),
            sltp("SAME", client="", status="ORDER_STATUS_EXECUTED"),
        ]})


def test_realistic_three_orders_with_terminal_empty_client_id_keep_flat_gate_strict():
    """One historical manual order is tolerated; the other two remain fully parsed."""
    entries = [
        regular("R1", client="production", status="ORDER_STATUS_FILLED"),
        sltp("S1", client="", comment="manual-stop", status="ORDER_STATUS_EXECUTED"),
        regular("R2", client="production_two", status="ORDER_STATUS_CANCELLED"),
    ]
    result = order_views({"orders": entries})
    assert len(result) == 3 and all(o.active is False for o in result)
    entries[2]["status"] = "ORDER_STATUS_NEW"
    entries[2]["order"]["client_order_id"] = ""
    with pytest.raises(ProductionBrokerStateError, match="ORDER_REQUEST_INVALID"):
        order_views({"orders": entries})
