"""New 08.2 H1 kill-switch lifecycle acceptance; fake token, no FINAM I/O."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from TradingSystemLab.stage8_robot.trading_safety_gate import (
    emergency_halt, load_kill_switch,
)
from V20_TradingSystem_M15.v20_runtime.finam_execution import (
    V20TradeJournal, V20FinamBlocked,
)
from V20_TradingSystem_M15.v20_runtime import finam_trial_operator as operator


ACCOUNT = 'isolated-intel-no-network-synthetic'
HASH = hashlib.sha256(ACCOUNT.encode()).hexdigest()
SHA = 'e9de4acd8582009c93d67dcac299cabf51eae08e'


class TrialArmingTests(unittest.TestCase):
    def setup_env(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / 'v20lab'
        root.mkdir()
        with V20TradeJournal(root, 'v20-shallow', ACCOUNT) as journal:
            safety = journal.instance_root / 'safety'
            safety.mkdir(exist_ok=True)
            grant = {
                'schema': 'v20.08.2.first_signal_approval.v1',
                'scope': 'ONE_FIRST_REAL_FROZEN_TRIAL_ONLY',
                'robot_id': 'v20-shallow',
                'account_sha256': HASH,
                'source_commit': SHA,
                'instrument': 'CNYRUBF',
                'max_risk_fraction': '0.015',
                'explicit_owner_approval': True,
            }
            (safety / 'v20-first-signal-approval.json').write_text(
                json.dumps(grant), encoding='utf-8',
            )
            emergency_halt(journal.instance_root)
        return root

    def test_trial_without_explicit_arm_flag_never_contacts_finam(self):
        root = self.setup_env()
        env = {
            'V20_FINAM_ACCOUNT': ACCOUNT,
            'V20_FINAM_TOKEN': 'fake-opaque',
            'V20_FINAM_ACCOUNT_SHA256': HASH,
        }
        with patch.dict(os.environ, env), patch.object(
            operator.V20FinamReadAdapter, 'authenticate',
            side_effect=AssertionError('no network expected')
        ):
            with self.assertRaisesRegex(
                V20FinamBlocked, 'TRIAL_OPERATOR_EXPLICIT_ARM_FLAG_REQUIRED'
            ):
                operator.run(
                    root=root, robot='v20-shallow', symbol='CNYRUBF',
                    fee='2.02', source_sha=SHA, mode='trial',
                    arm_for_trial=False,
                )
        switch, err = load_kill_switch(root / 'robots' / 'shallow')
        self.assertIsNone(err)
        self.assertEqual(switch['state'], 'HALTED')

    def test_arm_then_broker_error_restores_own_halted_switch(self):
        root = self.setup_env()
        env = {
            'V20_FINAM_ACCOUNT': ACCOUNT,
            'V20_FINAM_TOKEN': 'fake-opaque',
            'V20_FINAM_ACCOUNT_SHA256': HASH,
        }
        observed = []
        def synthetic_network_denial(_self):
            switch,err = load_kill_switch(root / 'robots' / 'shallow')
            self.assertIsNone(err)
            observed.append(switch['state'])
            raise V20FinamBlocked('FAKE_BROKER_UNAVAILABLE_AFTER_ARM')
        with patch.dict(os.environ, env), patch.object(
            operator.V20FinamReadAdapter, 'authenticate',
            synthetic_network_denial
        ):
            with self.assertRaisesRegex(
                V20FinamBlocked, 'FAKE_BROKER_UNAVAILABLE_AFTER_ARM'
            ):
                operator.run(
                    root=root, robot='v20-shallow', symbol='CNYRUBF',
                    fee='2.02', source_sha=SHA, mode='trial',
                    arm_for_trial=True,
                )
        self.assertEqual(observed, ['ARMED'])
        switch, err = load_kill_switch(root / 'robots' / 'shallow')
        self.assertIsNone(err)
        self.assertEqual(switch['state'], 'HALTED')


if __name__ == '__main__':
    unittest.main()
