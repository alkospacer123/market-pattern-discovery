"""V20-08.2 one focused fake-only acceptance test: owner manual terminal exit.

No terminal interaction, no real FINAM/DPAPI, no automatic stop cancellation.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

import V20_TradingSystem_M15.v20_runtime.finam_execution as execution
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20TradeJournal, V20FinamReadAdapter, run_v20_single_trial_cycle,
)
import test_finam_trial_transport as fixture


class ManualFlatTests(unittest.TestCase):
    def test_broker_manual_flat_requires_protective_stop_cancel_before_acceptance(self):
        with TemporaryDirectory() as temp:
            root=Path(temp)/'v20lab'
            root.mkdir()
            api=fixture.FakeFinam()
            reader=V20FinamReadAdapter(
                api=api,robot_id=fixture.ROBOT,account_id=fixture.ACCOUNT,
                expected_account_hash=fixture.HASH,
            )
            reader.authenticate()
            self.root,self.api,self.reader=root,api,reader
            # Synthetic FINAM only: no real order or cancellation permitted.
            with patch.object(execution,'datetime',fixture.OfflineTestClock):
                with patch(
                    'TradingSystemLab.stage8_robot.trading_safety_gate.load_kill_switch',
                    return_value=({'state':'ARMED'},None)
                ):
                    with V20TradeJournal(root,fixture.ROBOT,fixture.ACCOUNT) as journal:
                        key,snap=fixture.TrialBoundaryTests.entry(self,journal)
                        permit=fixture.TrialBoundaryTests.approval(self,journal,key)
                        sender=fixture.TrialBoundaryTests.transport(self,journal,permit)
                        sender.submit_entry_once(
                            key=key,snapshot=snap,now=fixture.OPEN_UTC,
                        )
                        api.positions=[{
                            'symbol':fixture.SYMBOL,'quantity':fixture.value('1'),
                        }]
                        started=fixture.OPEN_UTC+timedelta(seconds=3)
                        placed=run_v20_single_trial_cycle(
                            sender,now=started,trial_symbol='USDRUBF',
                            from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                            cost_per_contract=Decimal('2'),
                        )
                        self.assertEqual(placed['state'],'STOP_ACK_NEEDS_BROKER_PROOF')
                        later=fixture.OPEN_UTC+timedelta(minutes=1,seconds=3)
                        run_v20_single_trial_cycle(
                            sender,now=later,trial_symbol='USDRUBF',
                            from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                            cost_per_contract=Decimal('2'),
                        )
                        self.assertIsNotNone(journal.store.get('protected_fill:'+key))
                        self.assertEqual(api.order_posts,1)
                        self.assertEqual(api.stop_posts,1)

                        # Owner closes the WHOLE position in FINAM terminal.
                        # Remaining active stop is a HOLD: NEVER erase it or
                        # claim this is a completed and accepted trial.
                        api.positions=[]
                        api.orders_book[0]['status']='FILLED'
                        active=run_v20_single_trial_cycle(
                            sender,now=later+timedelta(seconds=5),
                            trial_symbol='USDRUBF',
                            from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                            cost_per_contract=Decimal('2'),
                        )
                        self.assertEqual(
                            active['state'],
                            'MANUAL_EXIT_FLAT_ACTIVE_STOP_CANCEL_IN_TERMINAL'
                        )
                        self.assertIsNone(journal.store.get('manual_flat:'+key))
                        self.assertEqual(api.stop_posts,1)
                        self.assertEqual(api.order_posts,1)

                        # Operator separately CANCELS old SLTP IN TERMINAL
                        # after confirming broker flat. This reader only
                        # observes terminal state and never sends DELETE.
                        api.orders_book[1]['status']='CANCELED'
                        completed=run_v20_single_trial_cycle(
                            sender,now=later+timedelta(seconds=10),
                            trial_symbol='USDRUBF',
                            from_utc=fixture.OPEN_UTC-timedelta(hours=1),
                            cost_per_contract=Decimal('2'),
                        )
                        self.assertEqual(
                            completed['state'],
                            'MANUAL_EXIT_BROKER_FLAT_UNDER_ACCEPTANCE'
                        )
                        proof=journal.store.get('manual_flat:'+key)
                        self.assertEqual(
                            proof['status'],'FLAT_NO_ACTIVE_ORDERS_FEES_UNVERIFIED'
                        )
                        self.assertIsNotNone(journal.store.get('execution_halt'))
                        self.assertEqual(api.stop_posts,1)
                        self.assertEqual(api.order_posts,1)


if __name__=='__main__':
    unittest.main()
