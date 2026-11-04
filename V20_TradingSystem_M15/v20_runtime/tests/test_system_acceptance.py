"""V20-05 new acceptance boundaries, not another historical replay."""
from contextlib import closing
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import queue
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
from unittest import TestCase
from unittest.mock import patch

from .test_m15_runner import T, candle, signal
from .. import m15_runner as runner

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = {}


class SystemAcceptanceTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(prefix="v20-acceptance-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"V20Lab"

    def child(self, robot="v20-shallow", phase=None):
        command = [sys.executable, "-m", "V20_TradingSystem_M15.v20_runtime.tests.acceptance_child",
                   "--root", str(self.root), "--robot", robot]
        if phase:
            command += ["--phase", phase]
        proc = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        def cleanup():
            if proc.poll() is None:
                proc.kill()
            proc.communicate(timeout=10)
        self.addCleanup(cleanup)
        return proc

    def read(self, proc):
        result = queue.Queue()
        threading.Thread(target=lambda: result.put(proc.stdout.readline()), daemon=True).start()
        line = result.get(timeout=20)
        self.assertTrue(line, "Child ended before publishing evidence")
        return json.loads(line)

    def open_bot(self, bot):
        bot.on_event(dict(at="2024-01-09T10:15:00", history={"CNYRUBF": [candle(T)]}))
        bot.on_event(dict(at="2024-01-09T10:15:00", updates={"CNYRUBF": dict(open="10", bars=[])}))
        return next(iter(bot.store.get("execution_entries")))

    def test_os_kill_at_six_durable_boundaries_no_duplicate_post(self):
        records = []
        for phase, expected in [("signal", 0), ("intent", 0), ("post", 1),
                                ("ack", 1), ("fill", 2), ("stop", 2)]:
            with self.subTest(phase=phase), TemporaryDirectory(prefix="v20-kill-") as tmp:
                self.root = Path(tmp)/"V20Lab"
                first = self.child(phase=phase); before = self.read(first)
                self.assertEqual(before["phase"], phase)
                first.kill(); first.communicate(timeout=10)
                restarted = self.child(); after = self.read(restarted)
                restarted.stdin.close(); restarted.stdin = None
                restarted.communicate(timeout=10)
                book = json.loads((self.root/"shallow/state/fake-broker.json").read_text())
                self.assertEqual(book["post_count"], expected)
                self.assertEqual(len({r.get("order", r.get("sltp_order"))["client_order_id"]
                                      for r in book["orders"]}), expected)
                if phase == "intent":
                    self.assertEqual(after["phase"], "blocked")
                    self.assertIn("UNCERTAIN_POST", after["error"])
                    self.assertEqual(len(before["reservations"]), 1)
                else:
                    self.assertEqual(after["phase"], "recovered")
                if phase in {"fill", "stop"}:
                    self.assertEqual(book["orders"][1]["sltp_order"]["quantity_sl"], {"value": "100"})
                with closing(sqlite3.connect(self.root/"shallow/state/v20-offline-execution.sqlite3")) as db:
                    self.assertEqual(db.execute("pragma integrity_check").fetchone(), ("ok",))
                records.append(dict(phase=phase, killed=before, restarted=after,
                                    posts_after_restart=book["post_count"], exit_code=first.returncode))
        EVIDENCE["os_kill"] = records

    def test_three_concurrent_accounts_one_killed_others_exit_independently(self):
        processes = {r: self.child(r, "protected") for r in runner.ROBOT_STRATEGIES}
        first = {r: self.read(p) for r, p in processes.items()}
        self.assertEqual(len({r["pid"] for r in first.values()}), 3)
        self.assertEqual(len({r["account"] for r in first.values()}), 3)
        self.assertTrue(all(r["post_count"] == 2 for r in first.values()))
        duplicate = self.child("v20-obv"); refused = self.read(duplicate)
        self.assertIn("SECOND_ROBOT_INSTANCE", refused["error"])
        duplicate.communicate(timeout=10)
        protected = [self.root/r/"state/fake-broker.json" for r in ("obv", "inside")]
        hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in protected]
        failed = processes["v20-shallow"]; failed.kill(); failed.communicate(timeout=10)
        self.assertEqual([hashlib.sha256(p.read_bytes()).hexdigest() for p in protected], hashes)
        processes["v20-shallow"] = self.child("v20-shallow")
        restart = self.read(processes["v20-shallow"])
        self.assertEqual(restart["post_count"], 2)
        final = {}
        for robot, proc in processes.items():
            for day in (10, 11):
                proc.stdin.write(json.dumps(dict(at=f"2024-01-{day}T09:00:00",
                    updates={"CNYRUBF": dict(open="10", bars=[])}))+"\n")
                proc.stdin.flush(); result = self.read(proc)
            proc.stdin.close(); proc.stdin = None; proc.communicate(timeout=10)
            self.assertEqual(proc.returncode, 0)
            self.assertTrue(all(int(p["quantity"]["value"]) == 0 for p in result["positions"]))
            self.assertEqual(result["post_count"], 3)
            self.assertEqual(result["reservations"], {})
            instance = self.root/robot.removeprefix("v20-")
            self.assertTrue((instance/"logs/m15.jsonl").is_file())
            self.assertFalse(json.loads((instance/"status.json").read_text())["live_enabled"])
            final[robot] = result
        EVIDENCE["three_process_isolation"] = dict(initial=first, duplicate=refused,
                                                   shallow_restart=restart, final=final)

    def test_missing_stop_confirmation_does_not_disable_verified_position_exit(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, \
             patch.object(runner, "completed_signal", side_effect=signal):
            key = self.open_bot(bot)
            bot.broker.cancel(bot.broker.orders[1]["order_id"])
            bot.on_event(dict(at="2024-01-09T10:30:00", updates={"GLDRUBF": dict(
                bars=[candle(datetime(2024, 1, 9, 10, 15), "GLDRUBF")], open="1000")}))
            self.assertEqual(bot.broker.post_count, 2)
            self.assertIn("PROTECTION_UNCONFIRMED", json.dumps(bot.store.get("last_refusal")))
            # Existing position/fills are verified; new entries must be blocked,
            # but an operator/frozen exit must remain possible without stop retry.
            bot.executor.request_frozen_exit(key)
            exit_order = bot.broker.orders[-1]
            self.assertEqual(exit_order["fake_kind"], "EXIT")
            bot._fill(exit_order, key, bot.store.get("remaining:"+key), Decimal("10"), datetime(2024, 1, 9, 11))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
            self.assertEqual(len([r for r in bot.broker.orders if r["fake_kind"] == "STOP"]), 1)

    def test_unconfirmed_stop_restart_blocks_entries_but_keeps_frozen_time_exit(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, \
             patch.object(runner, "completed_signal", side_effect=signal):
            key = self.open_bot(bot)
            bot.broker.cancel(bot.broker.orders[1]["order_id"])
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot:
            self.assertEqual(bot.store.get("execution_halt"), "PROTECTION_UNCONFIRMED_NO_RETRANSMIT")
            for day in (10, 11):
                result = bot.on_event(dict(at=f"2024-01-{day}T09:00:00",
                    updates={"CNYRUBF": dict(open="10", bars=[])}))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
            self.assertEqual(bot.broker.post_count, 3)  # one entry, one old stop, one exit
            self.assertNotEqual(result["reason"], "EVENT_BLOCKED")

    def test_h1_kill_switch_is_namespaced_blocks_entries_only_and_survives_restart(self):
        from TradingSystemLab.stage8_robot.trading_safety_gate import emergency_halt, kill_switch_path
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, \
             patch.object(runner, "completed_signal", side_effect=signal):
            key = self.open_bot(bot)
            emergency_halt(bot.instance)
            event = dict(at="2024-01-09T10:30:00", updates={"GLDRUBF": dict(
                bars=[candle(datetime(2024, 1, 9, 10, 15), "GLDRUBF")], open="1000")})
            bot.on_event(event)
            self.assertIn("KILL_SWITCH_HALTED", json.dumps(bot.store.get("last_refusal")))
            self.assertEqual(bot.broker.post_count, 2)
            self.assertEqual(bot.broker.orders[1]["status"], "NEW")
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot:
            self.assertEqual(runner.load_kill_switch(bot.instance)[0]["state"], "HALTED")
            for day in (10, 11):
                bot.on_event(dict(at=f"2024-01-{day}T09:00:00",
                    updates={"CNYRUBF": dict(open="10", bars=[])}))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
        with runner.M15OfflineRobot(self.root, "v20-obv") as other:
            self.assertEqual(runner.load_kill_switch(other.instance)[0]["state"], "ARMED")
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, \
             patch.object(runner, "completed_signal") as frozen:
            kill_switch_path(bot.instance).unlink()
            bot.on_event(dict(at="2024-01-12T10:15:00", updates={"IMOEXF": dict(
                bars=[candle(datetime(2024, 1, 12, 10), "IMOEXF")], open="3000")}))
            frozen.assert_not_called()
            self.assertIn("KILL_SWITCH_MISSING", json.dumps(bot.store.get("last_refusal")))
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot:
            self.assertIsNone(runner.load_kill_switch(bot.instance)[0])

    def test_offline_diagnostic_cli_and_halt_never_contact_network(self):
        command = [sys.executable, "-m", runner.__name__, "--offline", "--root", str(self.root),
                   "--robot", "v20-inside"]
        records = []
        with runner.M15OfflineRobot(self.root, "v20-inside") as bot:
            before = bot.broker.export()
            for option in ("--status", "--halt-entries", "--status"):
                result = subprocess.run(command+[option], cwd=ROOT, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                records.append(json.loads(result.stdout))
            self.assertEqual(bot.broker.export(), before)
        self.assertEqual([r["kill_switch"] for r in records], ["ARMED", "HALTED", "HALTED"])
        self.assertTrue(all(r["live_enabled"] is False for r in records))
        EVIDENCE["diagnostic_cli"] = records

    def test_readonly_card_failure_cannot_change_orders_or_signals(self):
        from .. import market_suitability
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, \
             patch.object(runner, "completed_signal", side_effect=signal), \
             patch.object(market_suitability, "evaluate_market_card", side_effect=AssertionError("card called")):
            key = self.open_bot(bot)
            self.assertGreater(bot.store.get("remaining:"+key), 0)
            self.assertEqual(bot.broker.post_count, 2)
            # Trading import closure must not acquire a dependency on a card.
            import ast
            for module in (runner, sys.modules[runner.OfflineH1Executor.__module__]):
                imports = [n.module or "" for n in ast.walk(ast.parse(Path(module.__file__).read_text()))
                           if isinstance(n, ast.ImportFrom)]
                self.assertFalse(any("market_" in n or "regime" in n for n in imports))
