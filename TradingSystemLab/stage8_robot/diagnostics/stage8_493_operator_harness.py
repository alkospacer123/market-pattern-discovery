"""Stage 8 #493: isolated operator-only two-lot execution boundary, NOT LIVE wired.

No FinamAPI import, no credential store, no cli execute path, no scheduled task,
no production database. A caller must separately provide an independently
reviewed, broker-authenticated port AND specifically authorized operator input.
This module deliberately never certifies a 100%-SLTP GET echo as actual trigger
coverage, and never reissues an uncertain POST. Physical bridge is NOT READY.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class Hold(RuntimeError):
    """Sticky operator intervention required; never silently authorize re-entry."""


@dataclass(frozen=True)
class Plan:
    account_hash: str
    instrument: str
    symbol: str
    direction: str
    entry_key: str
    stop_key: str
    stop_price: str
    quantity: int = 2

    def check(self) -> None:
        if (len(self.account_hash) != 64 or any(c not in '0123456789abcdef' for c in self.account_hash)
                or self.instrument not in {'USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF'}
                or self.symbol != self.instrument + '@RTSX'
                or self.direction not in {'LONG', 'SHORT'} or type(self.quantity) is not int
                or self.quantity != 2 or not self.entry_key or not self.stop_key
                or self.entry_key == self.stop_key or not self.stop_price):
            raise Hold('PLAN_IDENTITY_INVALID')


class Port(Protocol):
    def observe(self) -> dict: ...
    def entry(self, *, key: str, symbol: str, side: str, quantity: int) -> str: ...
    def install_stop(self, *, key: str, symbol: str, side: str, price: str, percent: int) -> str: ...
    def fills(self, order_id: str) -> list[dict]: ...
    def cancel(self, order_id: str) -> str: ...
    def exit(self, *, key: str, symbol: str, side: str, quantity: int) -> str: ...


class Journal:
    """Immutable numbered standalone evidence files with fsync, outside LIVE state.

    Any interrupted/ambiguous attempt must be reconciled manually before a new
    attempt. Never automatically resume or replay broker writes.
    """
    def __init__(self, root: Path, *, fresh: bool):
        self.root = root
        if not root.is_absolute() or root.is_symlink() or any(
                part.lower() in {'runtime', 'state', 'production'} for part in root.parts):
            raise Hold('UNSAFE_JOURNAL_DIRECTORY')
        if fresh:
            root.mkdir(mode=0o700, parents=False, exist_ok=False)
        elif not root.is_dir():
            raise Hold('JOURNAL_MISSING')
        self.records = []
        files = sorted(root.glob('*.json'))
        if files != [root / f'{i:04d}.json' for i in range(1, len(files) + 1)]:
            raise Hold('JOURNAL_SEQUENCE_INVALID')
        for file in files:
            try:
                self.records.append(json.loads(file.read_text('utf-8')))
            except (OSError, ValueError):
                raise Hold('JOURNAL_INVALID') from None
        if fresh and files:
            raise Hold('JOURNAL_NOT_EMPTY')

    def add(self, event: str, **fields) -> None:
        row = {'event': event, **fields}
        file = self.root / f'{len(self.records) + 1:04d}.json'
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        descriptor = os.open(file, flags, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(row, stream, sort_keys=True, separators=(',', ':'))
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        self.records.append(row)

    def count(self, event: str) -> int:
        return sum(r['event'] == event for r in self.records)

    def value(self, event: str, key: str):
        matches = [r for r in self.records if r['event'] == event]
        if len(matches) != 1 or key not in matches[0]:
            raise Hold('JOURNAL_EVENT_IDENTITY_MISSING')
        return matches[0][key]


class OperatorHarness:
    """Auditable API-side core, not connected to any real transport by this PR.

    Observations must be supplied by a later independently validated adapter;
    raw operator assertions are insufficient for physical authorization.
    """
    def __init__(self, plan: Plan, port: Port, journal: Journal):
        plan.check()
        self.plan, self.port, self.journal = plan, port, journal

    def observe(self) -> dict:
        row = self.port.observe()
        if (type(row) is not dict or row.get('account_hash') != self.plan.account_hash
                or row.get('symbol') != self.plan.symbol
                or type(row.get('position')) is not int
                or type(row.get('other_positions')) is not int
                or row['other_positions'] != 0
                or type(row.get('orders')) is not list
                or any(type(o) is not dict for o in row['orders'])):
            raise Hold('BROKER_OBSERVATION_INVALID')
        return row

    def _entry_fills(self, order_id: str, expected_qty: int) -> None:
        rows = self.port.fills(order_id)
        if type(rows) is not list or not rows:
            raise Hold('ORDER_LINKED_FILL_HISTORY_MISSING')
        seen, total = set(), 0
        side = 'SIDE_BUY' if self.plan.direction == 'LONG' else 'SIDE_SELL'
        for row in rows:
            if (type(row) is not dict or row.get('order_id') != order_id
                    or row.get('account_hash') != self.plan.account_hash
                    or row.get('symbol') != self.plan.symbol or row.get('side') != side
                    or type(row.get('quantity')) is not int
                    or row['quantity'] not in (1, 2)
                    or not isinstance(row.get('trade_id'), str) or not row['trade_id']
                    or row['trade_id'] in seen):
                raise Hold('ORDER_LINKED_FILL_IDENTITY_INVALID')
            seen.add(row['trade_id'])
            total += row['quantity']
        if total != expected_qty:
            raise Hold('ORDER_LINKED_FILL_QUANTITY_INVALID')

    def _stop(self, snapshot: dict, stop_id: str) -> None:
        stop_side = 'SIDE_SELL' if self.plan.direction == 'LONG' else 'SIDE_BUY'
        matches = [o for o in snapshot['orders'] if o.get('id') == stop_id]
        if (len(matches) != 1 or matches[0].get('kind') != 'sltp'
                or matches[0].get('active') is not True
                or matches[0].get('side') != stop_side
                or matches[0].get('percent') != 100
                or matches[0].get('price') != self.plan.stop_price
                or matches[0].get('symbol') != self.plan.symbol):
            raise Hold('ACTIVE_SAME_SLTP_100_PERCENT_NOT_OBSERVED')

    def _hold(self, reason: str) -> None:
        self.journal.add('operator_hold', reason=reason)
        raise Hold(reason)

    def entry_and_growth(self) -> str:
        """One entry and one stop at most. No direct exit or automatic reentry.

        0->2 direct fill is deliberately inconclusive. GET echo after 1->2 is
        *also* inconclusive as physical stop trigger coverage, regardless of ACK.
        """
        if self.journal.records:
            raise Hold('JOURNAL_ALREADY_USED_NO_REPLAY')
        snapshot = self.observe()
        if (snapshot['position'] != 0 or snapshot['other_positions'] != 0
                or any(order.get('active') is not False for order in snapshot['orders'])):
            raise Hold('INITIAL_ACCOUNT_NOT_FLAT')
        self.journal.add('precheck', account_hash=self.plan.account_hash, symbol=self.plan.symbol)
        self.journal.add('entry_intent', key=self.plan.entry_key, quantity=2)
        try:
            order_id = self.port.entry(key=self.plan.entry_key, symbol=self.plan.symbol,
                                       side='SIDE_BUY' if self.plan.direction == 'LONG' else 'SIDE_SELL',
                                       quantity=2)
        except Exception:
            self._hold('ENTRY_ACK_OR_TRANSPORT_UNKNOWN')
        if not isinstance(order_id, str) or not order_id:
            self._hold('ENTRY_ACK_UNKNOWN')
        self.journal.add('entry_ack', order_id=order_id)
        snapshot = self.observe()
        signed = snapshot['position'] * (1 if self.plan.direction == 'LONG' else -1)
        if signed not in (1, 2):
            self._hold('ENTRY_PARTIAL_OBSERVATION_UNKNOWN')
        try:
            self._entry_fills(order_id, signed)
        except Hold as exc:
            self._hold(str(exc))
        self.journal.add('entry_fills', quantity=signed, order_id=order_id)
        # Even direct 0->2 must be covered before classifying the physical
        # partial-growth experiment INCONCLUSIVE; never strand two lots naked.
        self.journal.add('stop_intent', key=self.plan.stop_key, after_quantity=signed, percent=100)
        try:
            stop_id = self.port.install_stop(key=self.plan.stop_key, symbol=self.plan.symbol,
                       side='SIDE_SELL' if self.plan.direction == 'LONG' else 'SIDE_BUY',
                       price=self.plan.stop_price, percent=100)
        except Exception:
            self._hold('STOP_ACK_OR_TRANSPORT_UNKNOWN')
        if not isinstance(stop_id, str) or not stop_id:
            self._hold('STOP_ACK_UNKNOWN')
        self.journal.add('stop_ack', order_id=stop_id)
        snapshot = self.observe()
        try:
            self._stop(snapshot, stop_id)
        except Hold as exc:
            self._hold(str(exc))
        if snapshot['position'] != (signed if self.plan.direction == 'LONG' else -signed):
            self._hold('POSITION_CHANGED_DURING_STOP_INSTALL')
        if signed == 2:
            self._hold('DIRECT_0_TO_2_INCONCLUSIVE_MANUAL_RECOVERY')
        self.journal.add('stop_at_one_observed', order_id=stop_id)
        # No sleep/unbounded polling here; a later independent operator
        # observation must be explicitly requested, not an automatic POST.
        return 'STOP_AT_ONE_OBSERVED_GROWTH_PENDING'

    def observe_growth(self) -> str:
        """Read-only transition; never interprets 100%-SLTP echo as trigger proof."""
        if self.journal.count('stop_at_one_observed') != 1 or self.journal.count('operator_hold'):
            raise Hold('GROWTH_NOT_AUTHORIZED')
        if self.journal.count('growth_observed'):
            raise Hold('GROWTH_ALREADY_OBSERVED')
        snap = self.observe()
        signed = snap['position'] * (1 if self.plan.direction == 'LONG' else -1)
        if signed != 2:
            self._hold('SAME_ENTRY_GROWTH_NOT_OBSERVED')
        oid = self.journal.value('entry_ack', 'order_id')
        sid = self.journal.value('stop_ack', 'order_id')
        try:
            self._entry_fills(oid, 2)
            self._stop(snap, sid)
        except Hold as exc:
            self._hold(str(exc))
        self.journal.add('growth_observed', quantity=2, entry_order_id=oid, stop_order_id=sid)
        return 'INCONCLUSIVE_REAL_STOP_TRIGGER_NOT_PROVEN'

    def recovery_precheck(self) -> dict:
        """A manual recovery *plan*, not permission to send cancel/exit.

        No action can be generated from an unknown or contradictory broker state;
        the operator must use broker terminal intervention if needed.
        """
        snap = self.observe()
        oid = self.journal.value('entry_ack', 'order_id')
        entry_orders = [o for o in snap['orders'] if o.get('id') == oid]
        if len(entry_orders) != 1 or entry_orders[0].get('remaining') != 0:
            self._hold('ENTRY_REMAINDER_MUST_BE_CLOSED_BEFORE_RECOVERY')
        pos = snap['position']
        signed = pos * (1 if self.plan.direction == 'LONG' else -1)
        if signed not in (0, 1, 2):
            self._hold('UNEXPECTED_RECOVERY_EXPOSURE')
        if signed and self.journal.count('stop_ack'):
            self._stop(snap, self.journal.value('stop_ack', 'order_id'))
        # Not executable: do not automatically cancel an existing backstop
        # while holding exposure or race exit against a possibly firing stop.
        return {'status': 'MANUAL_BROKER_TERMINAL_RECOVERY_REQUIRED',
                'observed_position': signed, 'no_automatic_cancel_or_exit': True,
                'broker_stop_trigger_proven': False}

    def final_flat(self) -> str:
        """Fail closed if known entry/stop are not terminal in TWO full reads.

        Flat positions by themselves cannot exclude a delayed ACK/entry fill,
        an outstanding resting entry, or an active broker protective stop.
        This is evidence only, never a broker stop-trigger PASS.
        """
        if (self.journal.count('entry_intent') != 1 or
                self.journal.count('entry_ack') != 1 or
                self.journal.count('double_flat')):
            self._hold('FINAL_FLAT_KNOWN_ENTRY_ACK_REQUIRED')
        entry_id = self.journal.value('entry_ack', 'order_id')
        stop_count = self.journal.count('stop_ack')
        if stop_count > 1:
            self._hold('FINAL_FLAT_STOP_LEDGER_AMBIGUOUS')
        stop_id = self.journal.value('stop_ack', 'order_id') if stop_count else None
        for _ in range(2):
            snap = self.observe()
            if snap['position'] != 0:
                self._hold('FINAL_FLAT_OR_ORDERS_NOT_PROVEN')
            by_id = {}
            for order in snap['orders']:
                order_id = order.get('id')
                if (not isinstance(order_id, str) or not order_id
                        or type(order.get('active')) is not bool
                        or order_id in by_id):
                    self._hold('FINAL_ORDER_OBSERVATION_INVALID')
                by_id[order_id] = order
                if order['active']:
                    self._hold('FINAL_FLAT_OR_ORDERS_NOT_PROVEN')
            entry = by_id.get(entry_id)
            if (entry is None or entry.get('kind') != 'regular'
                    or type(entry.get('remaining')) is not int
                    or entry['remaining'] != 0):
                self._hold('FINAL_ENTRY_TERMINAL_NOT_PROVEN')
            if stop_id is not None:
                stop = by_id.get(stop_id)
                if stop is None or stop.get('kind') != 'sltp':
                    self._hold('FINAL_STOP_TERMINAL_NOT_PROVEN')
        self.journal.add('double_flat', confirmed=True)
        return 'FLAT_AFTER_MANUAL_RECOVERY_NOT_PHYSICAL_SLTP_ACCEPTANCE'
