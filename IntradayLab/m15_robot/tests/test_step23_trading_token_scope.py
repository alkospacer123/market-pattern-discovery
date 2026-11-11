"""Step 23 trading token auth-only preflight: fake FINAM, no orders."""
import unittest
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI, M15FinamReadOnlyError
from IntradayLab.m15_robot.step23_trading_token_scope import (
    M15TradingScopeError, verify_m15_trading_token_scope, safe_failure_code,
)

M15 = "M15-SYNTH"
TOKEN = "synthetic-token-never-valid"


class TestM15Step23TradingScope(unittest.TestCase):
    def invoke(self, details):
        with patch.object(M15FinamReadOnlyAPI, "_request", side_effect=[
                {"token": "synthetic-jwt"}, details,
        ]) as request:
            output = verify_m15_trading_token_scope(
                m15_account_id=M15, secret=TOKEN)
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[0].args,
                         ("POST", "/v1/sessions", {"secret": TOKEN}))
        self.assertEqual(request.call_args_list[1].args,
                         ("POST", "/v1/sessions/details", {"token": "synthetic-jwt"}))
        return output

    def test_exact_one_account_trading_token_auth_only(self):
        result = self.invoke({"readonly": False, "account_ids": [M15]})
        self.assertTrue(result["trading_token_exact_single_m15_account"])
        self.assertEqual(result["broker_order_post_count"], 0)
        self.assertEqual(result["broker_order_cancel_count"], 0)
        self.assertFalse(result["live_authorized"])

    def test_readonly_token_rejected(self):
        with self.assertRaisesRegex(M15TradingScopeError, "NOT_TRADING_TOKEN"):
            self.invoke({"readonly": True, "account_ids": [M15]})

    def test_other_or_multi_account_rejected(self):
        for ids in (["OTHER"], [M15, "OTHER"], []):
            with self.subTest(ids=ids), self.assertRaisesRegex(
                    M15TradingScopeError, "ACCOUNT_NOT_EXACT_SINGLE"):
                self.invoke({"readonly": False, "account_ids": ids})

    def test_bad_session_schema_and_unauthorized_401(self):
        with patch.object(M15FinamReadOnlyAPI, "_request",
                          return_value={"foo": "bar"}):
            with self.assertRaisesRegex(M15TradingScopeError,
                                        "SESSION_TOKEN_INVALID"):
                verify_m15_trading_token_scope(
                    m15_account_id=M15, secret=TOKEN)
        with patch.object(M15FinamReadOnlyAPI, "_request",
                          side_effect=M15FinamReadOnlyError(
                              "M15_FINAM_HTTP_SESSION_CREATE_STATUS_401")):
            with self.assertRaisesRegex(M15FinamReadOnlyError, "STATUS_401"):
                verify_m15_trading_token_scope(
                    m15_account_id=M15, secret=TOKEN)

    def test_no_order_transport_or_authorization_from_reader(self):
        self.assertFalse(hasattr(M15FinamReadOnlyAPI, "place_order"))
        self.assertFalse(hasattr(M15FinamReadOnlyAPI, "cancel_order"))
        self.assertFalse(hasattr(M15FinamReadOnlyAPI, "place_sltp_order"))

    def test_safe_error_codes_cannot_leak_secrets(self):
        self.assertEqual(safe_failure_code(
            M15FinamReadOnlyError("account=1234 token=abcd")),
            "M15_STEP23_TRADE_SCOPE_UNCLASSIFIED_ERROR")
        self.assertEqual(safe_failure_code(
            M15FinamReadOnlyError("M15_FINAM_HTTP_SESSION_CREATE_STATUS_401")),
            "M15_FINAM_HTTP_SESSION_CREATE_STATUS_401")
        self.assertEqual(safe_failure_code(ValueError("secret")),
                         "M15_STEP23_TRADE_SCOPE_UNEXPECTED_ERROR")


if __name__ == "__main__":
    unittest.main()
