"""Targeted loop stitches and three actual subprocesses; never FINAM/network."""
from contextlib import ExitStack
from datetime import datetime, timedelta
from decimal import Decimal
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase, SkipTest
from unittest.mock import patch

from V20_TradingSystem_M15.v20_runtime import m15_runner as runner
from V20_TradingSystem_M15.v20_runtime.offline_planner import FrozenSignal, N4
from V20_TradingSystem_M15.v20_runtime.h1_state_journal import ROBOT_STRATEGIES
from V20_TradingSystem_M15.v20_runtime.market_reference_descriptive import SOURCE_SHA256

T = datetime(2024, 1, 9, 10)
PRICES = dict(CNYRUBF="10", USDRUBF="100", GLDRUBF="1000", IMOEXF="3000")
ATRS = dict(CNYRUBF="3.5", USDRUBF="3", GLDRUBF="300", IMOEXF="250")


def candle(at=T, symbol="CNYRUBF", **changes):
    p = Decimal(PRICES[symbol]); tick = Decimal(runner._load_registry()[symbol]["price_step"])
    return dict(Datetime=at.isoformat(), Open=str(p), High=str(p+tick), Low=str(p-tick),
                Close=str(p), Volume="100", **changes)


def signal(symbol, strategy, bars, *, observed_at):
    return FrozenSignal(strategy, symbol, 1, observed_at-timedelta(minutes=15), Decimal(ATRS[symbol]))


class M15LoopTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"V20Lab"

    def warm(self, bot, symbols=("CNYRUBF",), at=T):
        return bot.on_event(dict(at=(at+timedelta(minutes=15)).isoformat(),
                                history={s: [candle(at, s)] for s in symbols}))

    def boundary(self, symbols=("CNYRUBF",), at=T+timedelta(minutes=15)):
        return dict(at=at.isoformat(), updates={s: dict(bars=[], open=PRICES[s]) for s in symbols})

    def test_full_n4_deterministic_order_caps_and_duplicate_batch(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot, sorted(N4))
            event = self.boundary(sorted(N4, reverse=True))
            bot.on_event(event)
            opened = [r["symbol"] for r in bot.store.get("execution_entries").values()]
            self.assertEqual(opened, ["CNYRUBF", "GLDRUBF"])
            self.assertEqual(bot.broker.post_count, 4)
            bot.on_event(event)
            self.assertEqual(bot.broker.post_count, 4)
            self.assertIn("TWO_NEW_ENTRIES", json.dumps(bot.store.get("last_refusal")))

    def test_unfinished_future_bar_and_foreign_symbol_rejected_before_signal(self):
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot, patch.object(runner, "completed_signal") as frozen:
            bad = dict(at=T.isoformat(), history={"CNYRUBF": [candle(T)]})
            self.assertEqual(bot.on_event(bad)["reason"], "EVENT_BLOCKED")
            bad = dict(at=T.isoformat(), updates={"Si-3.24": dict(open="10")})
            self.assertEqual(bot.on_event(bad)["reason"], "EVENT_BLOCKED")
            frozen.assert_not_called(); self.assertEqual(bot.broker.post_count, 0)

    def test_revision_and_out_of_order_event_never_rewrite_history(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot:
            self.warm(bot)
            bad = self.boundary(); bad["updates"]["CNYRUBF"]["bars"] = [dict(candle(), Volume="999")]
            self.assertEqual(bot.on_event(bad)["reason"], "EVENT_BLOCKED")
            self.assertIn("IMMUTABLE_M15", json.dumps(bot.store.get("last_refusal")))
            self.assertEqual(bot.store.get("m15:CNYRUBF")[0]["Volume"], 100.)
            self.assertEqual(bot.on_event(dict(at=T.isoformat(), updates={ }))["reason"], "STALE_EVENT_IGNORED")

    def test_no_delayed_next_open_or_current_candle_fields(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal") as frozen:
            self.warm(bot)
            bot.on_event(self.boundary(at=T+timedelta(minutes=30)))
            self.assertIn("MISSING_IMMEDIATE", json.dumps(bot.store.get("last_refusal")))
            bad = self.boundary(at=T+timedelta(minutes=30)); bad["updates"]["CNYRUBF"]["High"] = "999"
            self.assertEqual(bot.on_event(bad)["reason"], "EVENT_BLOCKED")
            frozen.assert_not_called()

    def test_stop_on_entry_bar_is_observed_only_when_bar_finishes(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            key = next(iter(bot.store.get("execution_entries")))
            self.assertGreater(bot.store.get("remaining:"+key), 0)
            row = dict(candle(T+timedelta(minutes=15)), Low="2")
            bot.on_event(dict(at=(T+timedelta(minutes=30)).isoformat(),
                               updates={"CNYRUBF": dict(bars=[row], open="10")}))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
            self.assertEqual(bot.store.intent(key)["status"], "CLOSED")
            self.assertEqual(bot.broker.post_count, 2)  # same-session re-entry prohibited
            self.assertEqual(bot.store.get("risk_reservations"), {})

    def test_third_observed_session_survives_restart_and_calendar_holes(self):
        with runner.M15OfflineRobot(self.root, "v20-inside") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            key = next(iter(bot.store.get("execution_entries")))
            bot.on_event(self.boundary(at=datetime(2024, 1, 12, 9)))
            self.assertGreater(bot.store.get("remaining:"+key), 0)
        with runner.M15OfflineRobot(self.root, "v20-inside") as bot:
            bot.on_event(self.boundary(at=datetime(2024, 1, 19, 9)))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
            self.assertEqual(bot.broker.post_count, 3)
            self.assertEqual(bot.broker.orders[1]["status"], "CANCELLED")
            log = (self.root/"inside/logs/m15.jsonl").read_text()
            self.assertIn("THIRD_OBSERVED_SESSION_EXIT", log)

    def test_broker_book_history_cursors_and_budget_survive_restart(self):
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            before = bot.broker.export()
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot:
            bot.on_event(self.boundary())
            self.assertEqual(bot.broker.export(), before)
            self.assertTrue(bot.store.get("money_required"))
            self.assertEqual(len(bot.store.get("risk_reservations")), 1)

    def test_missing_broker_book_or_financial_evidence_is_never_recreated(self):
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
        path = self.root/"obv/state/fake-broker.json"
        original = path.read_text(); raw = json.loads(original); raw["financials"] = None
        path.write_text(json.dumps(raw))
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot:
            self.assertEqual(bot.store.get("execution_halt"), "ACCOUNT_FINANCIAL_SOURCE_UNAVAILABLE")
            self.assertEqual(bot.broker.orders[1]["status"], "NEW")
        self.assertIsNone(json.loads(path.read_text())["financials"])
        path.unlink()
        with self.assertRaisesRegex(runner.ExecutionBlocked, "BROKER_BOOK_MISSING"):
            runner.M15OfflineRobot(self.root, "v20-obv")
        self.assertFalse(path.exists())
        path.write_text(original)
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot:
            self.assertEqual(bot.broker.post_count, 2)

    def test_missing_financials_blocks_new_entries_but_autonomous_time_exit_survives(self):
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            key = next(iter(bot.store.get("execution_entries")))
        path = self.root/"obv/state/fake-broker.json"
        book = json.loads(path.read_text()); book["financials"] = None; path.write_text(json.dumps(book))
        with runner.M15OfflineRobot(self.root, "v20-obv") as bot:
            bot.on_event(self.boundary(at=datetime(2024, 1, 10, 9)))
            bot.on_event(self.boundary(at=datetime(2024, 1, 11, 9)))
            self.assertEqual(bot.store.get("remaining:"+key), 0)
            self.assertEqual(bot.broker.orders[1]["status"], "CANCELLED")
            self.assertIsNone(bot.broker.financials)

    def test_three_accounts_same_symbol_independent_and_instance_lock(self):
        with ExitStack() as stack, patch.object(runner, "completed_signal", side_effect=signal):
            bots = [stack.enter_context(runner.M15OfflineRobot(self.root, r)) for r in ROBOT_STRATEGIES]
            for bot in bots:
                self.warm(bot, sorted(N4)); bot.on_event(self.boundary(sorted(N4)))
                day2 = datetime(2024, 1, 10, 10)
                event = self.boundary(sorted(N4), at=day2)
                for symbol in N4:
                    event["updates"][symbol]["bars"] = [candle(day2-timedelta(minutes=15), symbol)]
                bot.on_event(event)
                self.assertEqual({r["symbol"] for r in bot.store.get("execution_entries").values()}, N4)
                self.assertEqual(bot.broker.post_count, 8)
                self.assertLessEqual(sum(Decimal(r["reserved_risk"]) for r in
                    bot.store.get("risk_reservations").values()), Decimal("30000"))
                proof = bot.store.get("risk_authorities")
                self.assertEqual(len(proof), 4)
                self.assertTrue(all(p["snapshot_revision"] is not None for p in proof.values()))
            self.assertEqual(len({b.broker.account_id for b in bots}), 3)
            with self.assertRaisesRegex(RuntimeError, "SECOND_ROBOT_INSTANCE"):
                runner.M15OfflineRobot(self.root, "v20-obv")

    def test_crash_after_durable_fill_recovers_protection_without_entry_retry(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot)
            original = bot.broker.fill
            def crash(*args, **kwargs):
                original(*args, **kwargs)
                raise KeyboardInterrupt()
            with patch.object(bot.broker, "fill", side_effect=crash):
                with self.assertRaises(KeyboardInterrupt):
                    bot.on_event(self.boundary())
            self.assertEqual(bot.broker.post_count, 1)
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot:
            self.assertEqual(bot.broker.post_count, 2)
            self.assertEqual(bot.broker.orders[1]["sltp_order"]["quantity_sl"], {"value": "100"})
            bot.on_event(self.boundary())
            self.assertEqual(bot.broker.post_count, 2)

    def test_observed_intraday_gap_marks_open_path_censored_keeps_stop(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            key = next(iter(bot.store.get("execution_entries")))
            row = candle(datetime(2024, 1, 9, 11))
            result = bot.on_event(dict(at="2024-01-09T11:15:00",
                updates={"CNYRUBF": dict(bars=[row], open="10")}))
            self.assertEqual(result["halt"], "M15_PATH_CENSORED_RECONCILE_REQUIRED")
            self.assertIsNotNone(bot.store.get("path_censored:"+key))
            self.assertEqual(bot.broker.orders[1]["status"], "NEW")

    def test_no_capacity_refuses_entry_without_dropping_protection(self):
        with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
            self.warm(bot); bot.on_event(self.boundary())
            bot.broker.configure_funds(realized_equity="500000", available_cash="10001",
                                      margins=bot.broker.financials["margins"])
            at = T+timedelta(minutes=30)
            bot.on_event(dict(at=at.isoformat(), updates={"GLDRUBF": dict(
                bars=[candle(at-timedelta(minutes=15), "GLDRUBF")], open="1000")}))
            self.assertEqual(bot.broker.post_count, 2)
            self.assertEqual(bot.broker.orders[1]["status"], "NEW")
            self.assertIn("MARGIN_CAPACITY", json.dumps(bot.store.get("last_refusal")))

    def test_no_network_and_no_live_or_unbound_config_path(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            with runner.M15OfflineRobot(self.root, "v20-shallow") as bot, patch.object(runner, "completed_signal", side_effect=signal):
                self.warm(bot); bot.on_event(self.boundary())
                self.assertFalse(json.loads((self.root/"shallow/status.json").read_text())["live_enabled"])
        config = json.loads(runner.CONFIG.read_text()); config["execution_mode"] = "LIVE"
        path = Path(self.tmp.name)/"bad-config.json"; path.write_text(json.dumps(config))
        with self.assertRaisesRegex(runner.ExecutionBlocked, "FROZEN_OFFLINE"):
            runner.M15OfflineRobot(self.root, "v20-shallow", config_path=path)

    def test_cli_requires_explicit_offline_and_has_no_live_switch(self):
        command = [sys.executable, "-m", runner.__name__, "--root", str(self.root),
                   "--robot", "v20-shallow", "--events", "-"]
        for tail in ([], ["--live"]):
            result = subprocess.run(command+tail, input="", text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 2)
        self.assertFalse(self.root.exists())


class ThreeProcessFrozenAcceptance(TestCase):
    def test_three_real_frozen_signals_then_offline_stop_and_process_restart(self):
        """Real published CNY prefixes, synthetic adverse next-bar fixtures.

        This proves process plumbing, not historical profitability or full replay.
        Six previously checked USDRUBF signals are not recalculated.
        """
        root = Path(runner.__file__).resolve().parents[1]
        ledger = root/"V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv"
        quotes = Path(os.environ.get("V20_N4_QUOTES_ROOT", "/workspace/work/v20-n4-parity-f8486b4"))/"CNYRUBF/CNYRUBF_M15.csv"
        if not quotes.exists():
            raise SkipTest("Pinned external CNY quotes unavailable: process acceptance NOT PASS")
        self.assertEqual(hashlib.sha256(quotes.read_bytes()).hexdigest(), SOURCE_SHA256["CNYRUBF"])
        self.assertEqual(hashlib.sha256(ledger.read_bytes()).hexdigest(),
                         "1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f")
        cases = {}
        with ledger.open() as stream:
            for r in csv.DictReader(stream):
                if r["record_type"] == "RAW_SIGNAL" and r["instrument"] == "CNYRUBF" and r["signal_bar_dt"].startswith("2024-"):
                    cases.setdefault(r["strategy"], r)
        with TemporaryDirectory(prefix="v20-three-processes-") as tmp:
            runtime = Path(tmp)/"V20Lab"; events = {}
            for robot, strategy in ROBOT_STRATEGIES.items():
                selected = cases[strategy]; cutoff = datetime.fromisoformat(selected["signal_bar_dt"])
                at = cutoff+timedelta(minutes=15); rows = []
                with quotes.open() as stream:
                    for r in csv.DictReader(stream, delimiter=";"):
                        if datetime.fromisoformat(r["Datetime"]) > cutoff:
                            break
                        rows.append({k: r[k] for k in ("Datetime", "Open", "High", "Low", "Close", "Volume")})
                path = Path(tmp)/(robot+"-open.jsonl")
                payloads = [dict(at=at.isoformat(), history={"CNYRUBF": rows}),
                            dict(at=at.isoformat(), updates={"CNYRUBF": dict(open=selected["entry"], bars=[])})]
                path.write_text("\n".join(json.dumps(x) for x in payloads)+"\n")
                events[robot] = path

            def run_all(paths):
                processes = {robot: subprocess.Popen([sys.executable, "-m", runner.__name__,
                    "--offline", "--root", str(runtime), "--robot", robot, "--events", str(path)],
                    cwd=root.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    for robot, path in paths.items()}
                results = []
                for robot, proc in processes.items():
                    out, err = proc.communicate(timeout=55)
                    self.assertEqual(proc.returncode, 0, robot+": "+err+out)
                    results.append(json.loads(out))
                self.assertEqual(len({r["pid"] for r in results}), 3)
                return results

            first = run_all(events)
            for robot, strategy in ROBOT_STRATEGIES.items():
                instance = runtime/robot.removeprefix("v20-")
                book = json.loads((instance/"state/fake-broker.json").read_text())
                self.assertEqual(book["post_count"], 2)
                self.assertEqual(len(book["fills"]), 1)
                opened = Decimal(book["orders"][0]["order"]["quantity"]["value"])
                self.assertGreater(opened, 0)
                stop = Decimal(book["orders"][1]["sltp_order"]["sl_price"]["value"])
                at = datetime.fromisoformat(book["fills"][0]["timestamp"])
                price = Decimal(book["fills"][0]["price"]); long = int(cases[strategy]["side"]) == 1
                row = dict(Datetime=at.isoformat(), Open=str(price), Close=str(price), Volume="100",
                           High=str(price+Decimal("0.001") if long else stop+Decimal("0.001")),
                           Low=str(stop-Decimal("0.001") if long else price-Decimal("0.001")))
                path = Path(tmp)/(robot+"-stop.jsonl")
                path.write_text(json.dumps(dict(at=(at+timedelta(minutes=15)).isoformat(),
                    updates={"CNYRUBF": dict(bars=[row], open=str(price))}))+"\n")
                events[robot] = path
            second = run_all(events)
            repeated = run_all(events)
            for r in second+repeated:
                self.assertEqual(r["post_count"], 2)
                self.assertEqual(r["positions"], {})
            self.assertEqual(len(list(runtime.glob("*/state/v20-offline-execution.sqlite3"))), 3)
            for instance in runtime.iterdir():
                status = json.loads((instance/"status.json").read_text())
                self.assertFalse(status["live_enabled"])
                self.assertEqual(status["symbols"], sorted(N4))
                self.assertTrue((instance/"logs/m15.jsonl").is_file())
            self.__class__.process_evidence = dict(first=first, after_stop=second,
                                                  after_duplicate_restart=repeated,
                                                  quote_sha256=hashlib.sha256(quotes.read_bytes()).hexdigest(),
                                                  fixture="real CNY frozen prefix / synthetic adverse completed entry bar")
