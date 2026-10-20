"""The H1 local-check parser never contacts either trading runtime."""
from datetime import datetime, timedelta, timezone
import unittest
from cc.providers.h1_operator_report import parse_operator_report, age_operator_report, REQUIRED_PASS, EXPECTED_COMMIT


NOW = datetime(2026, 10, 20, 18, 0, tzinfo=timezone.utc)


def report():
    rows = [
        "expected_production_commit=" + EXPECTED_COMMIT,
        "production_task=Running",
        "kill_switch_state=ARMED",
        "kill_switch_generation=62",
        "cycle_count=12000",
        "health_status=HEALTHY",
        "reconciliation_status=PASS",
        "reported_open_positions=0",
        "reported_active_stops=0",
        "reported_unresolved_intents=0",
        "heartbeat_utc=2026-10-20T17:59:40+00:00",
        "last_finam_api_contact_utc=2026-10-20T17:59:30+00:00",
        "last_cycle_attempts_found=10",
        "TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK=PASS",
        "NO_CHANGES_MADE_BY_THIS_SCRIPT=YES",
    ]
    rows += [x + "=PASS" for x in REQUIRED_PASS]
    rows += [f"cycle_{i:02}=status=PASS cycle={12000-10+i} code=NONE" for i in range(1, 11)]
    return "\n".join(rows) + "\n"


class TestOperatorReport(unittest.TestCase):
    def test_real_fields_and_10_cycles(self):
        x = parse_operator_report(report(), NOW)
        self.assertEqual(x["status"], "CURRENT")
        self.assertEqual(x["cycle_count"], 12000)
        self.assertEqual(len(x["cycles"]), 10)
        self.assertEqual(x["health"], "HEALTHY")

    def test_bad_authority_rejected(self):
        with self.assertRaises(ValueError):
            parse_operator_report(report().replace("HEARTBEAT_EXACT_FROZEN_IDENTITY=PASS", "HEARTBEAT_EXACT_FROZEN_IDENTITY=FAIL"), NOW)

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):
            parse_operator_report(report() + "cycle_count=1\n", NOW)

    def test_broker_claim_not_inferred(self):
        x = parse_operator_report(report(), NOW)
        self.assertNotIn("broker_flat", x)
        self.assertNotIn("fill_confirmed", x)
        self.assertNotIn("stop_protected", x)

    def test_stale_latches_without_source_reads(self):
        x = parse_operator_report(report(), NOW)
        y = age_operator_report(x, NOW + timedelta(minutes=16))
        self.assertEqual(y["status"], "STALE")
        self.assertEqual(age_operator_report(y, NOW)["status"], "STALE")

    def test_failed_final_check(self):
        with self.assertRaises(ValueError):
            parse_operator_report(report().replace("TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK=PASS", "TRADINGSYSTEMLAB_LIVE_LOCAL_READONLY_CHECK=FAIL"), NOW)

    def test_missing_cycle_rejected(self):
        with self.assertRaises(ValueError):
            parse_operator_report(report().replace("cycle_10=status=PASS cycle=12000 code=NONE", ""), NOW)


if __name__ == "__main__":
    unittest.main()
