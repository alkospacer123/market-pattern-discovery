"""Read-only Intel physical runner refuses foreign state; mock FINAM only."""
import unittest
from unittest.mock import patch

from IntradayLab.m15_robot.finam_readonly import M15FinamReadOnlyAPI
from IntradayLab.m15_robot.operator_readonly_recovery import (
    M15PhysicalSmokeError, run_physical_readonly_smoke,
)

PARAMS = {
    "m15_account_id": "M15-SYNTH",
    "h1_account_id": "H1-SYNTH",
    "readonly_secret": "synthetic-unusable-token",
}
ACCOUNT = {
    "account_id": "M15-SYNTH", "status": "ACCOUNT_ACTIVE", "positions": [],
}


class M15PhysicalReadOnlySmokeTests(unittest.TestCase):
    def test_two_real_shape_get_polls_and_sqlite_restart(self):
        with (
            patch.object(M15FinamReadOnlyAPI, "connect_readonly") as connect,
            patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
            patch.object(M15FinamReadOnlyAPI, "account", return_value=ACCOUNT) as account,
            patch.object(M15FinamReadOnlyAPI, "orders", return_value={"orders": []}) as orders,
        ):
            result = run_physical_readonly_smoke(**PARAMS)
        self.assertEqual(result["status"], "PASS_EMPTY_ACCOUNT_READONLY_RESTART")
        self.assertFalse(result["order_post_permitted"])
        self.assertEqual(result["broker_get_cycles"], 2)
        connect.assert_called_once_with()
        self.assertEqual(account.call_count, 2)
        self.assertEqual(orders.call_count, 2)

    def test_foreign_broker_position_fails_closed(self):
        occupied = {
            **ACCOUNT, "positions": [{
                "symbol": "CNYRUBF@RTSX", "quantity": {"value": "1"},
            }],
        }
        with (
            patch.object(M15FinamReadOnlyAPI, "connect_readonly"),
            patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
            patch.object(M15FinamReadOnlyAPI, "account", return_value=occupied),
            patch.object(M15FinamReadOnlyAPI, "orders", return_value={"orders": []}),
        ):
            with self.assertRaises(Exception):
                run_physical_readonly_smoke(**PARAMS)

    def test_active_broker_order_fails_closed(self):
        active = {
            "orders": [{
                "order_id": "foreign-active", "status": "ORDER_STATUS_NEW",
                "order": {
                    "symbol": "CNYRUBF@RTSX", "side": "SIDE_BUY",
                    "quantity": {"value": "1"},
                    "client_order_id": "foreign1",
                },
            }],
        }
        with (
            patch.object(M15FinamReadOnlyAPI, "connect_readonly"),
            patch.object(M15FinamReadOnlyAPI, "readonly_bound", True),
            patch.object(M15FinamReadOnlyAPI, "account", return_value=ACCOUNT),
            patch.object(M15FinamReadOnlyAPI, "orders", return_value=active),
        ):
            with self.assertRaises(Exception):
                run_physical_readonly_smoke(**PARAMS)

    def test_same_account_rejected_before_network(self):
        with patch.object(M15FinamReadOnlyAPI, "connect_readonly") as connect:
            with self.assertRaisesRegex(M15PhysicalSmokeError, "DISTINCT_ACCOUNT"):
                run_physical_readonly_smoke(
                    **{**PARAMS, "h1_account_id": "M15-SYNTH"})
            connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
