"""Offline regression for R070 Protect3 diagnostic JSONL; never contact FINAM."""
from __future__ import annotations

from contextlib import ExitStack, nullcontext
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import hashlib
import json
import os
import unittest

from V20_TradingSystem_M15.v20_runtime.finam_live import (
    V20FinamBlocked, run,
)
from V20_TradingSystem_M15.v20_runtime.tp6_protect3 import TP6Protect3Unsafe


@unittest.skipUnless(
    os.environ.get("R070_PROTECT3_DIAGNOSTIC_PATCH_ACTIVE") == "1",
    "ephemeral Protect3 diagnostic logging patch required")
class R070Protect3DiagnosticLoggingTests(unittest.TestCase):
    def test_jsonl_preserves_only_safe_internal_reason(self):
        cases = (
            ("R070_RESTART_DURABLE_FILLS_MISSING",
             "R070_RESTART_DURABLE_FILLS_MISSING"),
            ("TP6_FILL_PRICE_INVALID", "TP6_FILL_PRICE_INVALID"),
            ("PROTECT3_CURRENT_STOP_INVALID", "PROTECT3_CURRENT_STOP_INVALID"),
            ("R070_RESTART_FILL_account-secret", None),
        )
        for reason, expected in cases:
            with self.subTest(reason=reason), TemporaryDirectory() as tmp:
                root = Path(tmp) / "V20Lab"
                instance = root / "robots" / "shallow"
                (instance / "logs").mkdir(parents=True)
                account = "v20-test-account"
                journal = SimpleNamespace(
                    instance_root=instance,
                    robot_id="v20-shallow",
                    account_hash=hashlib.sha256(account.encode()).hexdigest(),
                )
                reader = SimpleNamespace(authenticate=lambda: None)

                def cycle(*_args):
                    try:
                        raise TP6Protect3Unsafe(reason)
                    except TP6Protect3Unsafe as exc:
                        raise V20FinamBlocked(
                            "R070_PROTECT3_M15_OR_FILL_UNVERIFIED") from exc

                env = {
                    "V20_FINAM_ACCOUNT": account,
                    "V20_FINAM_TOKEN": "synthetic-token",
                    "V20_FINAM_ACCOUNT_SHA256": hashlib.sha256(
                        account.encode()).hexdigest(),
                }
                with ExitStack() as stack:
                    stack.enter_context(patch.dict("os.environ", env))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveJournal",
                        return_value=nullcontext(journal)))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.V20FinamAPI"))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.V20FinamReadAdapter",
                        return_value=reader))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.V20LiveTransport"))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.run_cycle",
                        side_effect=cycle))
                    stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.load_kill_switch",
                        return_value=({"state": "ARMED"}, None)))
                    halted = stack.enter_context(patch(
                        "V20_TradingSystem_M15.v20_runtime.finam_live.emergency_halt"))
                    self.assertEqual(run(
                        root=root, robot="v20-shallow", source="0" * 40,
                        once=True), 1)
                    halted.assert_called_once_with(instance)

                rows = [json.loads(line) for line in
                        (instance / "logs" / "live-m15.jsonl").read_text(
                            encoding="utf-8").splitlines()]
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["state"],
                                 "HALT_R070_PROTECT3_M15_OR_FILL_UNVERIFIED")
                self.assertEqual(rows[0].get("protect3_reason"), expected)
                serialized = json.dumps(rows[0])
                self.assertNotIn(account, serialized)
                self.assertNotIn("synthetic-token", serialized)
                self.assertNotIn("account-secret", serialized)


if __name__ == "__main__":
    unittest.main()
