"""FINAM M15 REST read-only adapter: synthetic protocol tests, no network."""
import json
import unittest
from urllib.parse import urlparse, parse_qs

from IntradayLab.m15_robot.finam_readonly import (
    M15FinamReadOnlyAPI, M15FinamReadOnlyError, TIMEFRAME_M15,
)


class FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def read(self):
        return json.dumps(self.payload).encode()


class FakeTransport:
    def __init__(self, *, readonly=True, accounts=None, details=None):
        self.calls = []
        self.readonly = readonly
        self.accounts = ["M15-ACCOUNT"] if accounts is None else accounts
        self.details = details
    def __call__(self, request, timeout):
        parsed = urlparse(request.full_url)
        self.calls.append((request.get_method(), parsed.path, parsed.query, timeout))
        if parsed.path == "/v1/sessions":
            return FakeResponse({"token": "synthetic-jwt"})
        if parsed.path == "/v1/sessions/details":
            return FakeResponse(self.details if self.details is not None else
                                {"readonly": self.readonly, "account_ids": self.accounts})
        if parsed.path == "/v1/accounts/M15-ACCOUNT":
            return FakeResponse({
                "account_id": "M15-ACCOUNT", "status": "ACCOUNT_ACTIVE", "positions": [],
            })
        if parsed.path == "/v1/accounts/M15-ACCOUNT/orders":
            return FakeResponse({"orders": []})
        if parsed.path == "/v1/accounts/M15-ACCOUNT/trades":
            return FakeResponse({"trades": []})
        if parsed.path.startswith("/v1/instruments/"):
            symbol = parsed.path.split("/")[3]
            return FakeResponse({"symbol": symbol, "bars": []})
        if parsed.path.endswith("/params"):
            return FakeResponse({"sample_params": 1})
        if parsed.path.startswith("/v1/assets/") and not parsed.path.endswith("/schedule"):
            return FakeResponse({"ticker": "CNYRUBF", "mic": "RTSX", "min_step": "1", "decimals": 3})
        if parsed.path.endswith("/schedule"):
            return FakeResponse({"sample_schedule": 1})
        raise AssertionError("Unexpected method/path: " + parsed.path)


def adapter(transport):
    return M15FinamReadOnlyAPI(
        secret="synthetic-secret", account_id="M15-ACCOUNT", transport=transport,
        sleeper=lambda delay: None,
    )


class ReadOnlyTransport(unittest.TestCase):
    def test_constructing_client_makes_no_network_calls(self):
        fake = FakeTransport()
        api = adapter(fake)
        self.assertEqual(fake.calls, [])
        self.assertFalse(api.readonly_bound)
        self.assertNotIn("synthetic-secret", repr(api))
        self.assertNotIn("synthetic-jwt", repr(api))

    def test_readonly_exact_second_account_sequence(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        self.assertTrue(api.readonly_bound)
        self.assertEqual(api.account("M15-ACCOUNT")["account_id"], "M15-ACCOUNT")
        self.assertEqual(api.orders("M15-ACCOUNT")["orders"], [])
        self.assertEqual(api.asset_params("CNYRUBF@RTSX")["sample_params"], 1)
        self.assertEqual(api.schedule("CNYRUBF@RTSX")["sample_schedule"], 1)
        self.assertEqual(api.bars_m15("CNYRUBF@RTSX", "2026-10-15T10:00:00Z",
                                      "2026-10-15T12:00:00Z")["bars"], [])
        methods = [(method, path) for method, path, _, _ in fake.calls]
        self.assertEqual(methods[:2], [("POST", "/v1/sessions"),
                                      ("POST", "/v1/sessions/details")])
        self.assertTrue(all(method == "GET" for method, _ in methods[2:]))
        bars_query = next(query for method, path, query, _ in fake.calls if path.endswith("/bars"))
        self.assertEqual(parse_qs(bars_query)["timeframe"], [TIMEFRAME_M15])
        self.assertNotIn("H1", bars_query)

    def test_prohibit_all_order_posts_and_deletes(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        for method, path in [
            ("POST", "/v1/accounts/M15-ACCOUNT/orders"),
            ("POST", "/v1/accounts/M15-ACCOUNT/sltp-orders"),
            ("DELETE", "/v1/accounts/M15-ACCOUNT/orders/order-id"),
            ("PUT", "/v1/accounts/M15-ACCOUNT/orders/order-id"),
        ]:
            with self.subTest(method=method, path=path):
                with self.assertRaisesRegex(M15FinamReadOnlyError, "FORBIDDEN"):
                    api._request(method, path, {"secret": "none"})
        self.assertEqual(len(fake.calls), 2)

    def test_read_before_session_proof_rejected(self):
        fake = FakeTransport()
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "BINDING_REQUIRED"):
            api.account("M15-ACCOUNT")
        self.assertEqual(fake.calls, [])

    def test_reject_trading_capable_token(self):
        fake = FakeTransport(readonly=False)
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_reject_shared_token_with_h1_account(self):
        fake = FakeTransport(accounts=["M15-ACCOUNT", "H1-ACCOUNT"])
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)

    def test_reject_session_details_without_readonly_proof(self):
        fake = FakeTransport(details={"account_ids": ["M15-ACCOUNT"]})
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED_SESSION_SCHEMA"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_reject_false_readonly_with_specific_safe_code(self):
        fake = FakeTransport(readonly=False)
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED_TOKEN_NOT_READONLY"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_reject_multiple_accounts_with_specific_safe_code(self):
        fake = FakeTransport(accounts=["M15-ACCOUNT", "H1-ACCOUNT"])
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED_ACCOUNT_LIST_NOT_SINGLE"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_reject_nonlist_accounts_with_specific_safe_code(self):
        fake = FakeTransport(details={"readonly": True, "account_ids": "M15-ACCOUNT"})
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED_ACCOUNT_LIST_SCHEMA"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_reject_other_only_account_with_specific_safe_code(self):
        fake = FakeTransport(accounts=["H1-ACCOUNT"])
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "NOT_PROVED_ACCOUNT_ID_MISMATCH"):
            api.connect_readonly()
        self.assertFalse(api.readonly_bound)
        self.assertEqual(len(fake.calls), 2)

    def test_cross_account_read_never_calls_transport(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "CROSS_ACCOUNT"):
            api.account("H1-ACCOUNT")
        with self.assertRaisesRegex(M15FinamReadOnlyError, "CROSS_ACCOUNT"):
            api.orders("H1-ACCOUNT")
        self.assertEqual(len(fake.calls), 2)

    def test_reject_symbol_with_url_path_injection(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "SYMBOL_INVALID"):
            api.bars_m15("IMOEXF@RTSX/../../orders", "2026-10-15T10:00:00Z",
                         "2026-10-15T12:00:00Z")
        self.assertEqual(len(fake.calls), 2)

    def test_bars_reply_with_foreign_symbol_fails(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        orig = fake.__call__
        def swapped(request, timeout):
            if urlparse(request.full_url).path.endswith("/bars"):
                return FakeResponse({"symbol": "H1_FORTS@RTSX", "bars": []})
            return orig(request, timeout)
        api._transport = swapped
        with self.assertRaisesRegex(M15FinamReadOnlyError, "SYMBOL_OR_SCHEMA"):
            api.bars_m15("USDRUBF@RTSX", "2026-10-15T10:00:00Z",
                         "2026-10-15T12:00:00Z")

    def test_reject_get_payload_even_with_bound_session(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "GET_WITH_BODY"):
            api._request("GET", "/v1/accounts/M15-ACCOUNT", {"bad": "payload"})
        self.assertEqual(len(fake.calls), 2)

    def test_bad_time_interval_fails_before_get(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "INTERVAL_INVALID"):
            api.bars_m15("USDRUBF@RTSX", "2026-10-15T12:00:00Z",
                         "2026-10-15T10:00:00Z")
        self.assertEqual(len(fake.calls), 2)

    def test_asset_metadata_read_is_exact_account_get(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        result = api.asset_details("CNYRUBF@RTSX")
        self.assertEqual(result["min_step"], "1")
        method, path, query, timeout = fake.calls[-1]
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/v1/assets/CNYRUBF@RTSX")
        self.assertEqual(parse_qs(query), {"account_id": ["M15-ACCOUNT"]})
        self.assertEqual(len(fake.calls), 3)

    def test_trade_history_uses_only_exact_account_bounded_get(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        reply = api.trades("M15-ACCOUNT", start="2026-10-16T07:00:00Z",
                           end="2026-10-16T08:00:00Z", limit=1000)
        self.assertEqual(reply, {"trades": []})
        method, path, query, timeout = fake.calls[-1]
        self.assertEqual(method, "GET")
        self.assertEqual(path, "/v1/accounts/M15-ACCOUNT/trades")
        self.assertEqual(parse_qs(query), {
            "limit": ["1000"],
            "interval.start_time": ["2026-10-16T07:00:00Z"],
            "interval.end_time": ["2026-10-16T08:00:00Z"],
        })
        self.assertTrue(all(method == "GET" for method, _, _, _ in fake.calls[2:]))

    def test_trade_history_forbidden_for_h1_account(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "CROSS_ACCOUNT"):
            api.trades("H1-ACCOUNT", start="2026-10-16T07:00:00Z",
                       end="2026-10-16T08:00:00Z")
        self.assertEqual(len(fake.calls), 2)

    def test_trade_history_needs_valid_explicit_interval_and_limit(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        for start, end, limit in [
            ("2026-10-16T08:00:00Z", "2026-10-16T07:00:00Z", 1000),
            ("2026-10-16T07:00:00Z", "2026-10-16T07:00:00Z", 1000),
            ("2026-10-16T07:00:00Z", "2026-10-16T08:00:00Z", 1001),
            ("2026-10-16T07:00:00Z", "2026-10-16T08:00:00Z", 0),
            ("2026-10-16T07:00:00Z", "2026-10-16T08:00:00Z", True),
        ]:
            with self.subTest(start=start, end=end, limit=limit):
                with self.assertRaisesRegex(M15FinamReadOnlyError, "TRADES_INTERVAL_OR_LIMIT"):
                    api.trades("M15-ACCOUNT", start=start, end=end, limit=limit)
        self.assertEqual(len(fake.calls), 2)

    def test_trade_history_not_authorized_before_binding(self):
        fake = FakeTransport()
        api = adapter(fake)
        with self.assertRaisesRegex(M15FinamReadOnlyError, "BINDING_REQUIRED"):
            api.trades("M15-ACCOUNT", start="2026-10-16T07:00:00Z",
                       end="2026-10-16T08:00:00Z")
        self.assertEqual(fake.calls, [])

    def test_trade_history_refuses_broken_response_schema(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        original = fake.__call__
        def wrong(request, timeout):
            if urlparse(request.full_url).path.endswith("/trades"):
                return FakeResponse({"other": []})
            return original(request, timeout)
        api._transport = wrong
        with self.assertRaisesRegex(M15FinamReadOnlyError, "TRADES_SCHEMA"):
            api.trades("M15-ACCOUNT", start="2026-10-16T07:00:00Z",
                       end="2026-10-16T08:00:00Z")

    def test_double_session_rebind_rejected(self):
        fake = FakeTransport()
        api = adapter(fake)
        api.connect_readonly()
        with self.assertRaisesRegex(M15FinamReadOnlyError, "ALREADY_BOUND"):
            api.connect_readonly()
        self.assertEqual(len(fake.calls), 2)

    def test_malformed_account_id_refused_before_transport(self):
        with self.assertRaisesRegex(M15FinamReadOnlyError, "ACCOUNT_FORMAT"):
            M15FinamReadOnlyAPI(
                secret="synthetic", account_id="../H1-ACCOUNT", transport=FakeTransport(),
            )


if __name__ == "__main__":
    unittest.main()
