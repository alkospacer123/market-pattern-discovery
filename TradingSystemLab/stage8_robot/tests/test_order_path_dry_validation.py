import json
import urllib.request

import pytest

from TradingSystemLab.stage8_robot import order_path_dry_validation as dry
from TradingSystemLab.stage8_robot import finam_api
from TradingSystemLab.stage8_robot.broker import FinamRealReadOnlyBroker, OrderRequest
from TradingSystemLab.stage8_robot.config import RuntimeConfig


def test_complete_offline_gate_blocks_default_network(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("REAL_NETWORK_CALLED")
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(finam_api, "urlopen", forbidden)
    report = dry.validate()
    assert dry.load_frozen_symbols() == dry.EXPECTED_SYMBOLS
    assert report["broker_payload_case_count"] == 16
    assert report["synthetic_order_post_count"] == 1
    assert report["uncertain_submission_order_post_count"] == 1
    assert report["automatic_order_post_retry_count"] == 0
    assert report["external_network_calls"] == report["real_order_count"] == 0
    assert report["real_order_endpoint_called"] is False
    assert report["trading_token_used"] is report["readonly_token_used"] is False
    assert report["finam_authentication_performed"] is False
    assert report["stage8_10_6_status"] == "NOT_STARTED"
    assert report["stage8_11_status"] == report["stage8_12_status"] == "NOT_STARTED_NOT_AUTHORIZED"
    encoded = json.dumps(report).lower()
    for forbidden_text in ("synthetic-secret", "synthetic-jwt", "authorization", dry.ACCOUNT.lower()):
        assert forbidden_text not in encoded


def test_broker_matrix_exact_payloads_and_ids():
    cases = dry._broker_cases()
    assert len(cases) == 16
    assert [case["side"] for case in cases[:4]] == ["SIDE_BUY", "SIDE_SELL", "SIDE_SELL", "SIDE_BUY"]
    assert all(case["quantity"] == {"value": "1"} for case in cases)
    assert all(case["type"] == "ORDER_TYPE_MARKET" for case in cases)
    ids = [case["client_order_id"] for case in cases]
    assert all(len(value) == 20 and len(value) <= 20 and value.isascii() for value in ids)
    assert len(ids) == len(set(ids))


def test_transport_request_serialization_and_uncertainty():
    success = dry._transport_validation()
    uncertain = dry._transport_validation(fail_order=True)
    assert len(success.captured) == 2
    assert len(uncertain.captured) == 2


def test_real_readonly_submit_is_air_gapped():
    class API:
        def place_order(self, *args):
            raise AssertionError("PLACE_ORDER_CALLED")
    broker = FinamRealReadOnlyBroker(API(), "synthetic-readonly")
    with pytest.raises(RuntimeError, match="REAL_ORDER_TRANSMISSION_NOT_AUTHORIZED"):
        broker.submit_order(OrderRequest("key", "SYNTHETIC@RTSX", "LONG", 1))


def test_live_runtime_remains_forbidden(monkeypatch):
    monkeypatch.setenv("FINAM_MODE", "LIVE")
    with pytest.raises(RuntimeError, match="LIVE_TRADING_NOT_AUTHORIZED"):
        RuntimeConfig.from_environment()
