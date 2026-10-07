from __future__ import annotations

import pytest

from TradingSystemLab.stage8_robot.production_broker_state import (
    ProductionBrokerStateError,
    by_broker_id,
    by_client_id,
    client_order_id,
    is_active,
    is_filled,
    is_rejected,
    is_terminal,
    normalized_status,
    order_comment,
    order_rows,
    position_quantity_map,
)


def test_signed_position_map_and_duplicates_fail_closed():
    account = {
        "positions": [
            {"symbol": "USDRUBF@RTSX", "quantity": {"value": "2"}},
            {"symbol": "CNYRUBF@RTSX", "quantity": {"value": "-3"}},
            {"symbol": "GLDRUBF@RTSX", "quantity": {"value": "0"}},
        ]
    }
    assert position_quantity_map(account) == {
        "USDRUBF@RTSX": 2,
        "CNYRUBF@RTSX": -3,
    }
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_BROKER_POSITIONS_INVALID",
    ):
        position_quantity_map({
            "positions": [
                {"symbol": "USDRUBF@RTSX", "quantity": {"value": "1"}},
                {"symbol": "USDRUBF@RTSX", "quantity": {"value": "2"}},
            ]
        })
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_BROKER_QUANTITY_INVALID",
    ):
        position_quantity_map({
            "positions": [
                {"symbol": "USDRUBF@RTSX", "quantity": {"value": "1.5"}}
            ]
        })


def test_order_state_parses_nested_market_and_sltp_identities():
    market = {
        "order_id": "ENTRY-1",
        "status": "ORDER_STATUS_FILLED",
        "order": {
            "client_order_id": "s8abc",
            "symbol": "USDRUBF@RTSX",
        },
    }
    stop = {
        "order_id": "STOP-1",
        "status": "ORDER_STATUS_WATCHING",
        "sltp_order": {
            "client_order_id": "s8def",
            "comment": "stage8.12:trade:stop:0000",
            "symbol": "USDRUBF@RTSX",
        },
    }
    rows = order_rows({"orders": [market, stop]})
    assert client_order_id(market) == "s8abc"
    assert client_order_id(stop) == "s8def"
    assert order_comment(stop) == "stage8.12:trade:stop:0000"
    assert order_comment(market) is None
    assert by_broker_id(rows) == {"ENTRY-1": market, "STOP-1": stop}
    assert by_client_id(rows) == {"s8abc": market, "s8def": stop}
    assert normalized_status(market) == "FILLED"
    assert is_filled(market) is True
    assert is_terminal(market) is True
    assert is_active(market) is False
    assert is_active(stop) is True
    assert is_terminal(stop) is False


def test_rejected_and_unknown_statuses_are_fail_closed():
    rejected = {
        "order_id": "R-1",
        "status": "ORDER_STATUS_REJECTED_BY_EXCHANGE",
        "order": {"client_order_id": "s8x"},
    }
    assert is_rejected(rejected) is True
    assert is_terminal(rejected) is True
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_BROKER_ORDER_STATUS_INVALID",
    ):
        order_rows([{
            "order_id": "X",
            "status": "ORDER_STATUS_FUTURE_UNKNOWN",
            "order": {"client_order_id": "s8x"},
        }])


def test_duplicate_broker_or_client_order_identity_fails_closed():
    a = {
        "order_id": "A",
        "status": "ORDER_STATUS_NEW",
        "order": {"client_order_id": "same"},
    }
    b = {
        "order_id": "B",
        "status": "ORDER_STATUS_NEW",
        "order": {"client_order_id": "same"},
    }
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_DUPLICATE_CLIENT_ORDER_ID",
    ):
        by_client_id(order_rows([a, b]))
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_DUPLICATE_BROKER_ORDER_ID",
    ):
        by_broker_id(order_rows([a, {**b, "order_id": "A", "order": {"client_order_id": "other"}}]))


def test_ambiguous_market_and_sltp_payload_fails_closed():
    row = {
        "order_id": "A",
        "status": "ORDER_STATUS_NEW",
        "order": {"client_order_id": "a"},
        "sltp_order": {"client_order_id": "b"},
    }
    with pytest.raises(
        ProductionBrokerStateError,
        match="STAGE8_12_4_BROKER_ORDER_PAYLOAD_AMBIGUOUS",
    ):
        client_order_id(row)
