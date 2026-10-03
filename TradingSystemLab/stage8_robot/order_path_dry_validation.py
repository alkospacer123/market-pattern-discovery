"""Stage 8.10.5 offline order-path validation.

This module uses only synthetic values and in-process transports.  Quantity one
is a serialization fixture, not an affordability, sizing, or Stage 8.11
authorization claim.  No FINAM endpoint is contacted.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from .broker import FinamDemoBroker, OrderRequest, compact_client_order_id
from .finam_api import FinamAPI, FinamUncertainSubmission

ACCOUNT = "SYNTHETIC-STAGE8-10-5"
EXPECTED_SYMBOLS = ("USDRUBF@RTSX", "CNYRUBF@RTSX", "GLDRUBF@RTSX", "IMOEXF@RTSX")
SPECIFICATION = "PROD_STAGE7_46DB784378797C7FB04636892350AFF21006D71A31F2CED9D4B974EDA2DC36B8"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_OUTPUT_FORBIDDEN = "STAGE8_10_5_REPORT_REPOSITORY_OUTPUT_FORBIDDEN"


class _Response:
    def __init__(self, body: dict):
        self.status = 200
        self.headers = {}
        self._stream = BytesIO(json.dumps(body).encode("ascii"))

    def read(self) -> bytes:
        return self._stream.read()


class SyntheticTransport:
    """A callable request recorder with deliberately no network primitive."""
    def __init__(self, *, fail_order: bool = False):
        self.captured = []
        self.fail_order = fail_order

    def __call__(self, request, *, timeout):
        self.captured.append(request)
        if urlsplit(request.full_url).path.endswith("/orders"):
            if self.fail_order:
                raise TimeoutError("synthetic timeout")
            return _Response({"order_id": "synthetic-ack"})
        return _Response({"token": "synthetic-jwt"})


class _CaptureAPI:
    def __init__(self):
        self.calls = []

    def place_order(self, account_id, payload):
        self.calls.append((account_id, payload))
        return {"order_id": "synthetic-ack"}


def load_frozen_symbols() -> tuple[str, ...]:
    path = Path(__file__).with_name("production_instrument_registry.csv")
    with path.open(newline="", encoding="utf-8") as stream:
        return tuple(row["finam_symbol"] for row in csv.DictReader(stream))


def _broker_cases() -> list[dict]:
    symbols = load_frozen_symbols()
    if symbols != EXPECTED_SYMBOLS:
        raise AssertionError("FROZEN_N4_SYMBOLS_MISMATCH")
    api = _CaptureAPI()
    broker = FinamDemoBroker(api, ACCOUNT, ACCOUNT, transmission_enabled=True)
    cases = []
    for symbol in symbols:
        for label, direction, exit_order, side in (
            ("entry_long", "LONG", False, "SIDE_BUY"),
            ("entry_short", "SHORT", False, "SIDE_SELL"),
            ("exit_long", "LONG", True, "SIDE_SELL"),
            ("exit_short", "SHORT", True, "SIDE_BUY"),
        ):
            key = f"stage8-10-5:{symbol}:{label}"
            broker.submit_order(OrderRequest(key, symbol, direction, 1, exit_order))
            account, payload = api.calls[-1]
            expected_id = compact_client_order_id(key)
            expected = {"symbol": symbol, "quantity": {"value": "1"}, "side": side,
                        "type": "ORDER_TYPE_MARKET", "client_order_id": expected_id}
            if account != ACCOUNT or payload != expected:
                raise AssertionError("BROKER_PAYLOAD_MISMATCH")
            if len(expected_id) != 20 or not expected_id.isascii():
                raise AssertionError("CLIENT_ORDER_ID_INVALID")
            cases.append(payload)
    ids = [case["client_order_id"] for case in cases]
    if len(set(ids)) != len(ids) or compact_client_order_id("same") != compact_client_order_id("same"):
        raise AssertionError("CLIENT_ORDER_ID_DETERMINISM_INVALID")
    return cases


def _transport_validation(*, fail_order: bool = False):
    transport = SyntheticTransport(fail_order=fail_order)
    api = FinamAPI("synthetic-secret", transport=transport)
    api.create_session()
    payload = {"symbol": "SYNTHETIC@RTSX", "quantity": {"value": "1"},
               "side": "SIDE_BUY", "type": "ORDER_TYPE_MARKET",
               "client_order_id": "s8syntheticfixture1"}
    if fail_order:
        try:
            api.place_order(ACCOUNT, payload)
        except FinamUncertainSubmission as exc:
            if str(exc) != "RECONCILIATION_REQUIRED":
                raise
        else:
            raise AssertionError("UNCERTAIN_SUBMISSION_NOT_RAISED")
    else:
        api.place_order(ACCOUNT, payload)
    posts = [r for r in transport.captured if urlsplit(r.full_url).path.endswith("/orders")]
    if len(posts) != 1:
        raise AssertionError("ORDER_POST_COUNT_INVALID")
    request = posts[0]
    if (request.get_method() != "POST"
            or urlsplit(request.full_url).path != f"/v1/accounts/{ACCOUNT}/orders"
            or json.loads(request.data) != payload
            or request.get_header("Authorization") != "Bearer synthetic-jwt"
            or request.get_header("Content-type") != "application/json"):
        raise AssertionError("TRANSPORT_SERIALIZATION_INVALID")
    return transport


def validate() -> dict:
    cases = _broker_cases()
    success = _transport_validation()
    uncertain = _transport_validation(fail_order=True)
    return {
        "schema_id": "stage8_10_5_order_path_dry_validation.v1",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "production_specification_id": SPECIFICATION,
        "mode": "OFFLINE_SYNTHETIC_NO_TRANSMISSION",
        "frozen_n4_symbol_count": 4, "broker_payload_case_count": len(cases),
        "broker_payload_validation": "PASS", "client_order_id_validation": "PASS",
        "market_order_type": "ORDER_TYPE_MARKET", "transport_serialization_validation": "PASS",
        "synthetic_order_post_constructed": True, "synthetic_order_post_count": 1,
        "uncertain_submission_validation": "PASS", "uncertain_submission_order_post_count": 1,
        "automatic_order_post_retry_count": 0, "external_network_calls": 0,
        "real_account_id_used": False, "readonly_token_used": False, "trading_token_used": False,
        "finam_authentication_performed": False, "real_order_endpoint_called": False,
        "real_order_count": 0, "order_path_dry_validation": "PASS",
        "live_trading_authorized": False, "real_order_transmission_authorized": False,
        "scheduled_task_required": False, "stage8_10_6_status": "NOT_STARTED",
        "stage8_11_status": "NOT_STARTED_NOT_AUTHORIZED",
        "stage8_12_status": "NOT_STARTED_NOT_AUTHORIZED",
    }


def write_report(destination: Path, report: dict) -> None:
    """Write external evidence, refusing every destination in the checkout."""
    destination = destination.resolve()
    if destination == REPOSITORY_ROOT or REPOSITORY_ROOT in destination.parents:
        raise ValueError(REPOSITORY_OUTPUT_FORBIDDEN)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    if destination == REPOSITORY_ROOT or REPOSITORY_ROOT in destination.parents:
        parser.error(REPOSITORY_OUTPUT_FORBIDDEN)
    report = validate()
    write_report(destination, report)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
