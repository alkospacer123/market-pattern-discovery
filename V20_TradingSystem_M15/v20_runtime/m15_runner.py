"""One common OFFLINE M15 event loop; three isolated processes, no LIVE path.

JSONL boundary events contain completed bars and a separately witnessed Open.
History/warmup is explicit and causal. Broker operations, money control, state,
locks, frozen signals and stop execution reuse the existing H1/M15 adapters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd

from IntradayLab.core.execution import at_open, in_bar
from IntradayLab.core.models import Bar
from TradingSystemLab.stage8_robot.production_runtime import _load_registry
from TradingSystemLab.stage8_robot.production_broker_state import order_views

from .account_risk import RiskBlocked
from .frozen_adapter import completed_signal, validate_completed_history, known_m15_gap
from .h1_execution import FakeBroker, OfflineH1Executor, ExecutionBlocked
from .h1_state_journal import ROBOT_STRATEGIES, V20StateBoundaryError, _require_v20_root
from .offline_planner import N4, OfflinePlanner

CONFIG = Path(__file__).with_name("robots.json")
STEP = timedelta(minutes=15)


def atomic_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                          prefix=".v20-", delete=False) as f:
            name = f.name
            json.dump(payload, f, sort_keys=True, allow_nan=False)
            f.flush(); os.fsync(f.fileno())
        os.replace(name, path)
        name = None
    finally:
        if name is not None:
            Path(name).unlink(missing_ok=True)


def robot_config(path, robot_id):
    config = json.loads(Path(path).read_text())
    robots = config["robots"]
    if (config.get("execution_mode") != "OFFLINE_ONLY" or set(config["symbols"]) != N4
            or Decimal(str(config["provisional_risk_fraction"])) != Decimal("0.015")
            or len(config["symbols"]) != 4 or len(robots) != 3
            or {r["robot_id"] for r in robots} != set(ROBOT_STRATEGIES)
            or len({r["account_id"] for r in robots}) != 3):
        raise ExecutionBlocked("FROZEN_OFFLINE_CONFIG_REQUIRED")
    for r in robots:
        if (r["strategy"] != ROBOT_STRATEGIES[r["robot_id"]]
                or not r["account_id"].startswith("OFFLINE-")
                or r.get("token_binding") != "UNCONFIGURED"):
            raise ExecutionBlocked("OFFLINE_ACCOUNT_STRATEGY_BINDING_REQUIRED")
    return config, next(r for r in robots if r["robot_id"] == robot_id)


class M15OfflineRobot:
    def __init__(self, root, robot_id, *, config_path=CONFIG):
        config, robot = robot_config(config_path, robot_id)
        root = _require_v20_root(Path(root))
        checkout = CONFIG.resolve().parents[2]
        if root == checkout or checkout in root.parents:
            raise ExecutionBlocked("RUNTIME_MUST_BE_OUTSIDE_CHECKOUT")
        instance = root/robot_id.removeprefix("v20-")
        book_path = instance/"state"/"fake-broker.json"
        if book_path.is_symlink():
            raise ExecutionBlocked("BROKER_BOOK_SYMLINK_FORBIDDEN")
        broker = FakeBroker.restore(json.loads(book_path.read_text())) if book_path.exists() else FakeBroker(robot["account_id"])
        self.executor = OfflineH1Executor(root, robot_id, robot["account_id"], broker,
                                          require_money_authority=True)
        self.broker, self.store = broker, self.executor.store
        self.robot_id, self.strategy = robot_id, robot["strategy"]
        self.bindings = _load_registry()
        try:
            if not book_path.exists() and self.store.all_intents():
                raise ExecutionBlocked("BROKER_BOOK_MISSING_FOR_EXISTING_INTENTS")
            fingerprint = hashlib.sha256(json.dumps(dict(robot=robot, symbols=sorted(N4),
                mode=config["execution_mode"], model=config["offline_model"]), sort_keys=True).encode()).hexdigest()
            if self.store.get("runner_config", fingerprint) != fingerprint:
                raise ExecutionBlocked("RUNNER_CONFIG_CHANGED")
            self.store.put("runner_config", fingerprint)
            self.logs = instance/"logs"
            if self.logs.is_symlink() or (self.logs/"m15.jsonl").is_symlink():
                raise ExecutionBlocked("LOG_SYMLINK_FORBIDDEN")
            self.logs.mkdir(parents=True, exist_ok=True)
            self.status_path = instance/"status.json"
            broker.on_change = lambda book: atomic_json(book_path, book)
            if broker.financials is None and not book_path.exists():
                model = config["offline_model"]
                broker.configure_funds(realized_equity=model["realized_equity"],
                    available_cash=model["available_cash"],
                    margins={s: model["initial_margin"] for s in N4})
            self.executor.recover()
            interrupted = self.store.get("in_progress")
            self._status("RECOVERED_WITH_SKIPPED_DECISION" if interrupted else "RECOVERED", None)
            if interrupted:
                self.store.put("in_progress", None)  # at-most-once, never a late NEXT_OPEN
        except BaseException as exc:
            if hasattr(self, "logs"):
                self._status("STARTUP_BLOCKED", None, detail=str(exc))
            self.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        self.executor.journal.close()

    def _status(self, reason, at, **details):
        if reason in {"ENTRY_REFUSED", "EVENT_BLOCKED"}:
            self.store.put("last_refusal", dict(at=at, reason=reason, **details))
        record = dict(mode="OFFLINE_FAKE_ONLY", robot_id=self.robot_id,
                      account_hash=self.executor.journal.account_hash, pid=os.getpid(),
                      observed_at=at, last_clock=self.store.get("last_clock"),
                      reason=reason, halt=self.store.get("execution_halt"),
                      last_refusal=self.store.get("last_refusal"),
                      symbols=sorted(N4), live_enabled=False, **details)
        with (self.logs/"m15.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, sort_keys=True)+"\n")
        atomic_json(self.status_path, record)
        return record

    def _merge(self, symbol, rows, at):
        old = self.store.get("m15:"+symbol, [])
        known = {r["Datetime"]: r for r in old}
        if rows:
            frame = validate_completed_history(symbol, pd.DataFrame(rows), observed_at=at)
            for record in frame.to_dict("records"):
                record["Datetime"] = record["Datetime"].isoformat()
                stamp = record["Datetime"]
                if stamp in known and known[stamp] != record:
                    raise ExecutionBlocked("IMMUTABLE_M15_HISTORY_REVISED")
                if stamp not in known:
                    if old and stamp <= old[-1]["Datetime"]:
                        raise ExecutionBlocked("M15_BACKFILL_REQUIRES_DIAGNOSIS")
                    old.append(record)
        if not old:
            raise ExecutionBlocked("NO_COMPLETED_M15_HISTORY")
        frame = validate_completed_history(symbol, pd.DataFrame(old), observed_at=at)
        return old, frame

    def _fill(self, order, key, qty, price, at):
        symbol = order.get("order", order.get("sltp_order"))["symbol"].split("@")[0]
        self.broker.fill(order["order_id"], key, qty, str(price), at.isoformat(),
                          fee=Decimal(self.bindings[symbol]["tick_value"])*qty)  # C1 one tick/side
        self.executor.recover()

    def _stops(self, symbol, frame, at, witnessed_open):
        for key, entry in self.store.get("execution_entries", {}).items():
            if entry["symbol"] != symbol or not self.store.get("remaining:"+key, 0):
                continue
            stop = next((x for x in self.broker.orders if x.get("sltp_order", {}).get("comment") == key+":stop"
                         and x["status"] in {"NEW", "PARTIAL_FILL"}), None)
            if stop is None:
                raise ExecutionBlocked("PROTECTION_UNCONFIRMED_NO_RETRANSMIT")
            stop_price = Decimal(stop["sltp_order"]["sl_price"]["value"])
            side = 1 if entry["direction"] == "LONG" else -1
            entry_at = datetime.fromisoformat(entry["entry_at"])
            previous_rows = frame[frame.Datetime >= entry_at-STEP]
            for prev, current in zip(previous_rows.Datetime, previous_rows.Datetime.iloc[1:]):
                if known_m15_gap(prev, current):
                    if self.store.get("path_censored:"+key) is None:
                        self.store.put("path_censored:"+key, dict(known_at=at.isoformat(),
                            previous_open=prev.isoformat(), next_open=current.isoformat()))
                    self.store.put("execution_halt", "M15_PATH_CENSORED_RECONCILE_REQUIRED")
            # Only bars completed since the last boundary, never a future entry path.
            previous = self.store.get("path_cursor:"+symbol, entry_at.isoformat())
            candidates = frame[(frame.Datetime >= entry_at) & (frame.Datetime >= datetime.fromisoformat(previous))]
            for r in candidates.to_dict("records"):
                opened = at_open(Decimal(str(r["Open"])), side, stop_price, False)
                bar = Bar(r["Datetime"].to_pydatetime(), STEP,
                          *(Decimal(str(r[f])) for f in ("Open", "High", "Low", "Close", "Volume")))
                hit = opened or in_bar(bar, side, stop_price,
                                       Decimal("Infinity") if side == 1 else Decimal("-Infinity"), False)
                if hit:
                    self._fill(stop, key, self.store.get("remaining:"+key), hit[0], bar.available_at)
                    break
            if not self.store.get("remaining:"+key, 0) or witnessed_open is None:
                continue
            days = {datetime.fromisoformat(d).date() for d in self.store.get("sessions:"+symbol, [])}
            entered = OfflinePlanner._session_key(entry_at)
            deadline = len([d for d in days if d >= entered]) >= 3
            if deadline:
                self.executor.request_frozen_exit(key)
                exit_order = next(x for x in self.broker.orders
                                  if x.get("fake_trade_id") == key and x.get("fake_kind") == "EXIT")
                self._fill(exit_order, key, self.store.get("remaining:"+key), witnessed_open, at)
                self._status("THIRD_OBSERVED_SESSION_EXIT", at.isoformat(), symbol=symbol)
            else:
                hit = at_open(witnessed_open, side, stop_price, False)
                if hit:
                    self._fill(stop, key, self.store.get("remaining:"+key), hit[0], at)
        self.store.put("path_cursor:"+symbol, (frame.Datetime.iloc[-1].to_pydatetime()+STEP).isoformat())

    def on_event(self, event):
        """One deterministic boundary batch, sorted frozen symbol tie order."""
        try:
            if set(event) - {"at", "history", "updates"} or not isinstance(event.get("at"), str):
                raise ExecutionBlocked("BOUNDARY_EVENT_SCHEMA_INVALID")
            at = datetime.fromisoformat(event["at"])
            if pd.Timestamp(event["at"]).nanosecond:
                raise ValueError("M15_GRID_INVALID")
            OfflinePlanner._session_key(at)
            last = self.store.get("last_clock")
            if last and at < datetime.fromisoformat(last):
                return self._status("STALE_EVENT_IGNORED", at.isoformat())
            self.executor.recover()
            history, updates = event.get("history", {}), event.get("updates", {})
            if set(history) - N4 or set(updates) - N4 or (history and updates):
                raise ExecutionBlocked("ISOLATED_N4_BATCH_REQUIRED")
            prepared = {}
            for symbol in sorted(history or updates):
                item = dict(bars=history[symbol]) if history else updates[symbol]
                if set(item) - {"bars", "open"}:
                    raise ExecutionBlocked("ONLY_COMPLETED_BARS_AND_SCALAR_OPEN")
                rows, frame = self._merge(symbol, item.get("bars", []), at)
                opened = Decimal(str(item["open"])) if item.get("open") is not None else None
                if opened is not None:
                    from TradingSystemLab.stage8_robot.execution_grid import require_on_grid
                    require_on_grid(opened, Decimal(self.bindings[symbol]["price_step"]))
                prepared[symbol] = rows, frame, opened
            if history and any(self.store.get("remaining:"+k, 0) for k in self.store.get("execution_entries", {})):
                raise ExecutionBlocked("WARMUP_CANNOT_SKIP_OPEN_POSITION_PATH")
            with self.store.transaction():
                for symbol, (rows, _, _) in prepared.items():
                    self.store.put("m15:"+symbol, rows)
                    days = set(self.store.get("sessions:"+symbol, []))
                    days.update(OfflinePlanner._session_key(datetime.fromisoformat(r["Datetime"])).isoformat()
                                for r in rows)
                    if prepared[symbol][2] is not None:
                        days.add(OfflinePlanner._session_key(at).isoformat())
                    self.store.put("sessions:"+symbol, sorted(days))
                self.store.put("last_clock", at.isoformat())
            if history:
                return self._status("CAUSAL_WARMUP", at.isoformat())
            for symbol, (_, frame, opened) in prepared.items():
                self._stops(symbol, frame, at, opened)
            for symbol, (_, frame, opened) in prepared.items():
                stamp = frame.Datetime.iloc[-1].to_pydatetime()
                if self.store.get("decision_cursor:"+symbol) == stamp.isoformat():
                    self._status("DUPLICATE_COMPLETED_M15", at.isoformat(), symbol=symbol)
                    continue
                # Claim BEFORE decision/POST. A crash may skip a trade, never replay
                # the historical Open later. Executor intents/book recover separately.
                with self.store.transaction():
                    self.store.put("decision_cursor:"+symbol, stamp.isoformat())
                    self.store.put("in_progress", dict(symbol=symbol, at=at.isoformat()))
                try:
                    if opened is None or stamp+STEP != at:
                        raise ExecutionBlocked("MISSING_IMMEDIATE_NEXT_OPEN")
                    signal = completed_signal(symbol, self.strategy, frame, observed_at=at)
                    if signal is None:
                        self._status("NO_FROZEN_SIGNAL", at.isoformat(), symbol=symbol)
                        continue
                    authority = self.broker.authority(symbol, "LONG" if signal.side == 1 else "SHORT")
                    entry = OfflinePlanner(self.strategy).reference_next_open(signal, at=at,
                        entry_open=opened, realized_equity=authority.realized_equity,
                        price_step=authority.price_step, tick_value=authority.tick_value,
                        initial_margin=authority.initial_margin, available_cash=authority.available_cash,
                        trade_lot_size=authority.trade_lot_size,
                        cost_buffer_per_contract=authority.roundtrip_cost_per_contract)
                    key = self.executor.submit_entry(signal, entry, price_step=authority.price_step,
                                                       account_authority=authority)
                    order = next((x for x in self.broker.orders if x.get("fake_trade_id") == key
                                  and x.get("fake_kind") == "ENTRY"), None)
                    if order is None:
                        raise ExecutionBlocked("ENTRY_REJECTED_OR_UNCONFIRMED")
                    self._fill(order, key, self.store.get("execution_entries")[key]["quantity"], opened, at)
                    self._status("ENTRY_FILLED_AND_PROTECTED", at.isoformat(), symbol=symbol)
                except (ExecutionBlocked, RiskBlocked, V20StateBoundaryError, ValueError) as exc:
                    self._status("ENTRY_REFUSED", at.isoformat(), symbol=symbol, detail=str(exc))
                finally:
                    self.store.put("in_progress", None)
            return self._status("BOUNDARY_PROCESSED", at.isoformat(),
                                 positions=self.executor.recover()["positions"])
        except (ExecutionBlocked, RiskBlocked, V20StateBoundaryError, ValueError) as exc:
            return self._status("EVENT_BLOCKED", event.get("at"), detail=str(exc))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", choices=tuple(ROBOT_STRATEGIES), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--events", required=True, help="external JSONL path or - for stdin")
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--offline", action="store_true", required=True)
    args = parser.parse_args()
    failed = False
    with M15OfflineRobot(args.root, args.robot, config_path=args.config) as robot:
        stream = sys.stdin if args.events == "-" else Path(args.events).open()
        try:
            for line in stream:
                if line.strip():
                    status = robot.on_event(json.loads(line))
                    failed |= status["reason"] == "EVENT_BLOCKED"
            print(json.dumps(dict(robot_id=args.robot, pid=os.getpid(), mode="OFFLINE_FAKE_ONLY",
                                   post_count=robot.broker.post_count,
                                   positions=robot.executor.recover()["positions"]), sort_keys=True))
        finally:
            if stream is not sys.stdin:
                stream.close()
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
