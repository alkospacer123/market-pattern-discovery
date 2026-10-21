"""Offline tests for ONE immutable H1-style context in the live M15 journal."""
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from IntradayLab.m15_robot.grid_risk import ContractAuthority
from IntradayLab.m15_robot.live_execution import M15OutboundJournal
from IntradayLab.m15_robot.production_one_shot import (
    M15OneShotCycleError, persist_original_signal_context,
    restore_original_signal_context, stop_key_for, trade_tag,
)
from IntradayLab.m15_robot.tests.test_live_execution import TestLiveExecution


class TestProductionOneShotContext(TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory(prefix="m15-one-shot-")
        root=Path(self.temp.name)
        self.args={
            "runtime_root": root/"m15",
            "h1_runtime_root": root/"other-never-open",
            "repository_root": root,
            "m15_account_id":"M15-SYNTH",
            "h1_account_sha256":hashlib.sha256(b"H1-SEPARATE").hexdigest(),
        }
        self.j=M15OutboundJournal(**self.args)

    def tearDown(self):
        self.j.close()
        self.temp.cleanup()

    def test_deterministic_stop_key_no_secrets(self):
        key="m15:entry:abc"
        self.assertEqual(stop_key_for(key),stop_key_for(key))
        self.assertIn(trade_tag(key), stop_key_for(key))
        self.assertNotIn("M15-SYNTH",stop_key_for(key))

    def test_cannot_persist_context_without_durable_r15(self):
        contract=ContractAuthority(
            Decimal("0.001"),Decimal("1"),1,
            Decimal("100"),Decimal("100"))
        from IntradayLab.m15_robot.grid_risk import SizedOrder
        sized=SizedOrder(Decimal("750"),Decimal("200"),3,5,3,
                         Decimal("600"),"OK")
        with self.assertRaisesRegex(
                M15OneShotCycleError,"CONTEXT_R15_PROOF_INVALID"):
            persist_original_signal_context(
                journal=self.j,entry_key="m15:missing",
                signal_closed_at=datetime.now(timezone.utc),
                signal_atr=Decimal("0.100"),
                contract=contract,sized=sized)
        with self.assertRaisesRegex(
                M15OneShotCycleError,"ORIGINAL_CONTEXT_MISSING"):
            restore_original_signal_context(
                journal=self.j,entry_key="m15:missing")
