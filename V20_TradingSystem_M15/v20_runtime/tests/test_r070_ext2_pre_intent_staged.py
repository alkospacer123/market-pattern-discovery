"""R070 offline only: test the original V20 run_cycle with a temporary EXT2 patch.

The Windows workflow applies r070-ext2-pre-intent-candidate.patch to a
temporary checkout and restores the immutable production file afterward.
No FINAM token, API, real order, or LIVE installation is involved.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import Mock, patch

from V20_TradingSystem_M15.v20_runtime.ext2_history_bridge import m15_history_sha256
from V20_TradingSystem_M15.v20_runtime.finam_execution import V20FinamBlocked
from V20_TradingSystem_M15.v20_runtime.finam_live import run_cycle, SYMBOLS
from V20_TradingSystem_M15.v20_runtime.tests.test_finam_live import StubStore
from V20_TradingSystem_M15.v20_runtime.tests.test_r070_candidate_entry import fixtures


class R070Ext2PreIntentWindowsTests(TestCase):
    def scenario(self, *, robot="v20-shallow", symbol="GLDRUBF",
                 contra=False, provider=True, witness_drift=False):
        _, full, recent, draft = fixtures(
            robot=robot, symbol=symbol, contra=contra)
        store = StubStore()
        journal = SimpleNamespace(
            robot_id=robot, store=store, instance_root=Path("."),
            prepare_entry=Mock(return_value="staged-key"),
        )
        broker = SimpleNamespace(positions={}, orders=[])
        reader = SimpleNamespace(
            robot_id=robot, snapshot=Mock(return_value=broker))
        sender = SimpleNamespace(
            reader=reader, journal=journal, source="0"*40,
            auth_path=Path("synthetic-authorization.json"),
            auth={"roundtrip_cost_rub": {s: "2.02" for s in SYMBOLS}},
            submit_entry_once=Mock(return_value="broker-ack"),
        )
        if provider:
            sender.r070_verified_history_provider = Mock(
                return_value=(full, m15_history_sha256(full)))
        boundary = SimpleNamespace(
            symbol=symbol, at_msk=draft[1].entry_bar_open,
            witnessed_open=draft[1].reference_entry + (
                Decimal("0.1") if witness_drift else Decimal("0")),
            completed=recent,
        )
        return SimpleNamespace(
            sender=sender, journal=journal, reader=reader,
            draft=draft, boundary=boundary, store=store, symbol=symbol,
        )

    def cycle(self, case):
        path="V20_TradingSystem_M15.v20_runtime."
        with patch(path+"finam_live._safe_auth",return_value=case.sender.auth), \
             patch(path+"finam_live._follow_existing",
                   return_value="BROKER_RECONCILED_PROTECTION_PASS"), \
             patch(path+"finam_live.load_kill_switch",
                   return_value=({"state":"ARMED"},None)), \
             patch(path+"finam_live._entries",return_value=[]), \
             patch(path+"finam_live._ownership",return_value=[]), \
             patch(path+"finam_live.propose_finam_m15_next_open",
                   side_effect=lambda *args, **kw:
                       case.draft if kw["symbol"]==case.symbol else None) as proposal, \
             patch(path+"r070_candidate_entry.read_finam_m15_boundary",
                   return_value=case.boundary) as m15:
            result=run_cycle(
                case.sender,
                datetime(2026,11,16,10,15,10,tzinfo=timezone.utc))
        return result,proposal,m15

    def test_late_signal_blocked_before_prepare_entry_or_post(self):
        case=self.scenario()
        outcome,proposal,m15=self.cycle(case)
        self.assertEqual(outcome,"NO_FROZEN_SIGNAL")
        case.journal.prepare_entry.assert_not_called()
        case.sender.submit_entry_once.assert_not_called()
        self.assertEqual(m15.call_count,1)
        key="r070_ext2_decision:"+case.symbol+":"+case.draft[1].entry_bar_open.isoformat()
        self.assertEqual(case.store.get(key)["reason"],
                         "EXT2_LATE_NO_OPPOSING_M15")
        self.assertFalse(case.store.get(key)["permit"])

    def test_qualifying_signal_keeps_exact_frozen_entry_and_risk(self):
        case=self.scenario(contra=True)
        outcome,proposal,m15=self.cycle(case)
        self.assertEqual(outcome,"ENTRY_ACK_NEEDS_FILL_AND_STOP")
        self.assertEqual(m15.call_count,1)
        case.journal.prepare_entry.assert_called_once()
        kw=case.journal.prepare_entry.call_args.kwargs
        self.assertIs(kw["signal"],case.draft[0])
        self.assertIs(kw["entry"],case.draft[1])
        self.assertIs(kw["authority"],case.draft[2])
        case.sender.submit_entry_once.assert_called_once()
        key="r070_ext2_decision:"+case.symbol+":"+case.draft[1].entry_bar_open.isoformat()
        self.assertEqual(case.store.get(key)["reason"],"EXT2_PASS")
        self.assertTrue(case.store.get(key)["permit"])

    def test_missing_verified_history_blocks_without_extra_m15_request(self):
        case=self.scenario(provider=False)
        outcome,proposal,m15=self.cycle(case)
        self.assertEqual(outcome,"NO_FROZEN_SIGNAL")
        m15.assert_not_called()
        case.journal.prepare_entry.assert_not_called()
        case.sender.submit_entry_once.assert_not_called()
        key="r070_ext2_decision:"+case.symbol+":"+case.draft[1].entry_bar_open.isoformat()
        self.assertEqual(case.store.get(key)["reason"],
                         "EXT2_VERIFIED_HISTORY_PROVIDER_MISSING")

    def test_second_witness_drift_rejects_before_intent(self):
        case=self.scenario(contra=True,witness_drift=True)
        with self.assertRaisesRegex(
                V20FinamBlocked,"R070_EXT2_SECOND_WITNESS_DIVERGED"):
            self.cycle(case)
        case.journal.prepare_entry.assert_not_called()
        case.sender.submit_entry_once.assert_not_called()

    def test_inside_and_imoex_keep_frozen_flow_without_extra_get(self):
        for robot,symbol in (("v20-inside","GLDRUBF"),
                             ("v20-shallow","IMOEXF")):
            with self.subTest(robot=robot,symbol=symbol):
                case=self.scenario(robot=robot,symbol=symbol,provider=False)
                outcome,proposal,m15=self.cycle(case)
                self.assertEqual(outcome,"ENTRY_ACK_NEEDS_FILL_AND_STOP")
                m15.assert_not_called()
                case.journal.prepare_entry.assert_called_once()
                case.sender.submit_entry_once.assert_called_once()


if __name__=="__main__":
    main()
