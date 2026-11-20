"""R070 incident 2026-11-17: offline GET-only IncompleteRead regression.

Run ONLY against the ephemeral candidate-patched finam_live.py. No network or
account credentials; production PIN restored by the Windows CI step.
"""
from __future__ import annotations

from http.client import IncompleteRead
from unittest import TestCase
from unittest.mock import patch

from TradingSystemLab.stage8_robot.finam_api import FinamAPI, FinamError
from V20_TradingSystem_M15.v20_runtime.finam_live import (
    V20FinamAPI, V20FinamSnapshotReadRetry,
)


class R070FinamIncompleteGetTests(TestCase):
    def test_incomplete_get_returns_explicit_transient_without_resending(self):
        api = V20FinamAPI("SYNTHETIC_DO_NOT_SEND")
        with patch.object(FinamAPI, "_request", side_effect=IncompleteRead(b"abc", 12)) as raw:
            with self.assertRaisesRegex(
                    V20FinamSnapshotReadRetry, "FINAM_GET_INCOMPLETE_READ"):
                api._request("GET", "/v1/accounts/synthetic/orders")
            raw.assert_called_once()

    def test_incomplete_post_or_delete_remains_fatal_without_resending(self):
        api = V20FinamAPI("SYNTHETIC_DO_NOT_SEND")
        for method, path in (
            ("POST", "/v1/accounts/synthetic/orders"),
            ("POST", "/v1/accounts/synthetic/sltp-orders"),
            ("DELETE", "/v1/accounts/synthetic/orders/unknown"),
            ("POST", "/v1/sessions"),
        ):
            with self.subTest(method=method, path=path):
                with patch.object(FinamAPI, "_request",
                                  side_effect=IncompleteRead(b"abc", 12)) as raw:
                    with self.assertRaises(IncompleteRead):
                        api._request(method, path)
                    raw.assert_called_once()

    def test_persistent_401_scope_is_unchanged(self):
        api = V20FinamAPI("SYNTHETIC_DO_NOT_SEND")
        with patch.object(FinamAPI, "_request", side_effect=FinamError(
                "HTTP_401:/v1/accounts/synthetic")) as raw:
            with self.assertRaisesRegex(
                    V20FinamSnapshotReadRetry,
                    "FINAM_READ_AUTH_HTTP_401_UNVERIFIED"):
                api._request("GET", "/v1/accounts/synthetic")
            raw.assert_called_once()
        with patch.object(FinamAPI, "_request", side_effect=FinamError(
                "HTTP_401:/v1/accounts/synthetic/orders")) as raw:
            with self.assertRaises(FinamError):
                api._request("POST", "/v1/accounts/synthetic/orders")
            raw.assert_called_once()
