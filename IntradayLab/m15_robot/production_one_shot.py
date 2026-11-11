"""H1-style M15 one-shot production coordinator, staged under frozen LIVE.

One coordinator consumes the real installed M15 intent journal and one bound
M15 trading JWT: first account/order reconciliation, then either ONE real
NEXT_OPEN order or first-priority stop handling for its existing position.
The original H1 rule holds: protect broker exposure BEFORE GET fills or bar
management; ACK != FILL and UNCERTAIN is NEVER reposted.

A frozen deployment cannot construct the trading transport at all. There
is no operator CLI, authorization writer, Task activation or H1 IO here.
Trailing replacement and final operator release are separate existing
M15 #17/#23 duties; this coordinator does NOT pretend they are complete.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from .broker_snapshot import order_views, position_quantities
from .exchange_contract import contract_from_moex_and_finam
from .broker_risk_readonly import check_instrument
from .grid_risk import ContractAuthority, SizedOrder, initial_stop
from .live_execution import (
    M15AuthorizedExecutionTransport, M15OutboundJournal, M15ExecutionError,
)
from .service_clock import M15SingleInstance
from .spec import INSTRUMENTS
from .trade_draft_contract import M15OfflineTradeDrafts

_CONTEXT_PREFIX = "one-shot-entry-v1:"
_LOCK = "m15-production-one-shot.lock"


class M15OneShotCycleError(RuntimeError):
    pass


def trade_tag(entry_key: str) -> str:
    if not isinstance(entry_key, str) or not entry_key:
        raise M15OneShotCycleError("M15_ONESHOT_ENTRY_KEY_INVALID")
    return hashlib.sha256(entry_key.encode("utf-8")).hexdigest()[:20]


def stop_key_for(entry_key: str) -> str:
    return "m15:" + trade_tag(entry_key) + ":stop:0000"


def _decimal(value: str) -> Decimal:
    if not isinstance(value, str):
        raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_INVALID")
    try:
        x = Decimal(value)
    except ArithmeticError:
        raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_INVALID") from None
    if not x.is_finite():
        raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_INVALID")
    return x


def persist_original_signal_context(
    *, journal: M15OutboundJournal, entry_key: str,
    signal_closed_at: datetime, signal_atr: Decimal,
    contract: ContractAuthority, sized: SizedOrder,
) -> None:
    """Reboot-safe immutable NEXT_OPEN and R15 inputs, before first ENTRY POST.

    Reuses existing M15 SQLite metadata table; NO schema migration of the
    physical journal. Missing data after a crash is a PREPARED hold, not a
    license to repeat or estimate the broker entry.
    """
    if (not isinstance(journal, M15OutboundJournal)
            or not isinstance(signal_closed_at, datetime)
            or signal_closed_at.tzinfo is None
            or signal_closed_at.utcoffset() is None
            or not isinstance(signal_atr, Decimal)
            or not signal_atr.is_finite() or signal_atr <= 0
            or not isinstance(contract, ContractAuthority)
            or not isinstance(sized, SizedOrder)):
        raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_TYPE_INVALID")
    contract.validate()
    row = journal.inspect(entry_key)
    proof = journal.db.execute(
        "SELECT symbol,direction,reference_entry,stop_price,quantity,"
        "nominal_initial_risk FROM entry_r15_basis WHERE intent_key=?",
        (entry_key,),
    ).fetchone()
    if (row is None or row["state"] != "PREPARED"
            or row["kind"] != "ENTRY" or proof is None
            or proof[4] != sized.final_quantity
            or _decimal(proof[5]) != sized.initial_nominal_risk
            or initial_stop(
                proof[1], _decimal(proof[2]), signal_atr,
                contract.price_step) != _decimal(proof[3])
            or sized.initial_nominal_risk > sized.risk_budget
            or sized.reason != "OK"):
        raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_R15_PROOF_INVALID")
    data = {
        "signal_closed_at": signal_closed_at.astimezone(timezone.utc).isoformat(),
        "signal_atr": str(signal_atr),
        "contract": {key: str(getattr(contract, key))
                     for key in ("price_step", "tick_value",
                                 "trade_lot_size", "long_initial_margin",
                                 "short_initial_margin")},
        "sized": {key: str(getattr(sized, key))
                  for key in ("risk_budget", "per_contract_loss", "by_risk",
                              "by_margin", "final_quantity",
                              "initial_nominal_risk", "reason")},
    }
    value = json.dumps(data, sort_keys=True, separators=(",", ":"))
    key = _CONTEXT_PREFIX + entry_key
    journal.db.execute("BEGIN IMMEDIATE")
    try:
        old = journal.db.execute(
            "SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        if old is not None and old[0] != value:
            raise M15OneShotCycleError("M15_ONESHOT_CONTEXT_CONFLICT")
        if old is None:
            journal.db.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?)", (key, value))
        journal.db.execute("COMMIT")
    except Exception:
        if journal.db.in_transaction:
            journal.db.execute("ROLLBACK")
        raise


def restore_original_signal_context(
    *, journal: M15OutboundJournal, entry_key: str,
) -> tuple[datetime, Decimal, ContractAuthority, SizedOrder]:
    row = journal.db.execute(
        "SELECT value FROM metadata WHERE key=?",
        (_CONTEXT_PREFIX + entry_key,),
    ).fetchone()
    if row is None:
        raise M15OneShotCycleError("M15_ONESHOT_ORIGINAL_CONTEXT_MISSING")
    try:
        value = json.loads(row[0])
        stamp = datetime.fromisoformat(value["signal_closed_at"])
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError("timezone")
        a = value["contract"]
        b = value["sized"]
        contract = ContractAuthority(
            _decimal(a["price_step"]), _decimal(a["tick_value"]),
            int(a["trade_lot_size"]), _decimal(a["long_initial_margin"]),
            _decimal(a["short_initial_margin"]))
        sized = SizedOrder(
            _decimal(b["risk_budget"]), _decimal(b["per_contract_loss"]),
            int(b["by_risk"]), int(b["by_margin"]),
            int(b["final_quantity"]), _decimal(b["initial_nominal_risk"]),
            b["reason"])
        signal_atr = _decimal(value["signal_atr"])
        contract.validate()
        proof = journal.db.execute(
            "SELECT symbol,direction,reference_entry,stop_price,quantity,"
            "nominal_initial_risk FROM entry_r15_basis WHERE intent_key=?",
            (entry_key,),
        ).fetchone()
        if (proof is None or sized.reason != "OK"
                or proof[4] != sized.final_quantity
                or _decimal(proof[5]) != sized.initial_nominal_risk
                or sized.initial_nominal_risk > sized.risk_budget
                or sized.per_contract_loss * sized.final_quantity
                != sized.initial_nominal_risk
                or initial_stop(
                    proof[1], _decimal(proof[2]), signal_atr,
                    contract.price_step) != _decimal(proof[3])):
            raise ValueError("original_r15_mismatch")
        return stamp, signal_atr, contract, sized
    except (TypeError, ValueError, KeyError, ArithmeticError, AttributeError):
        raise M15OneShotCycleError(
            "M15_ONESHOT_ORIGINAL_CONTEXT_INVALID") from None


class M15OneShotProductionCycle:
    """H1 cycle order: broker GET -> STOP FIRST -> fills -> broker FLAT.

    A caller must supply independently authenticated original N4 source
    histories and open-labelled FINAM interval. This class never loads a
    research file by guessed path, nor does it connect to FINAM by itself.
    """

    def __init__(
        self, *, journal: M15OutboundJournal,
        transport: M15AuthorizedExecutionTransport,
        drafts: M15OfflineTradeDrafts,
        authenticated_seeds: dict,
        interval_start: str, interval_end: str,
        verified_open_labels: bool,
    ):
        if (not isinstance(journal, M15OutboundJournal)
                or not isinstance(transport, M15AuthorizedExecutionTransport)
                or not isinstance(drafts, M15OfflineTradeDrafts)
                or journal.account_hash != transport.account_hash
                or journal.path.parent.parent.resolve()
                != transport.runtime_root.resolve()
                or not isinstance(authenticated_seeds, dict)
                or set(authenticated_seeds) != set(INSTRUMENTS)
                or not isinstance(interval_start, str)
                or not isinstance(interval_end, str)
                or verified_open_labels is not True):
            raise M15OneShotCycleError("M15_ONESHOT_SERVICE_IDENTITY_INVALID")
        self.journal = journal
        self.transport = transport
        self.drafts = drafts
        self.seeds = authenticated_seeds
        self.interval_start = interval_start
        self.interval_end = interval_end
        self.verified_open_labels = verified_open_labels

    def _manage_existing(self, entry_key: str, now: datetime) -> dict:
        entry = self.journal.inspect(entry_key)
        if entry is None or entry["kind"] != "ENTRY":
            raise M15OneShotCycleError("M15_ONESHOT_ENTRY_MISSING")
        if entry["state"] == "PREPARED":
            return {"status": "ENTRY_PREPARED_NEVER_POSTED_OPERATOR_REVIEW",
                    "new_entries_authorized": False}
        signal_time, atr, contract, sized = restore_original_signal_context(
            journal=self.journal, entry_key=entry_key)
        proof = self.journal.db.execute(
            "SELECT symbol,direction,reference_entry,stop_price FROM "
            "entry_r15_basis WHERE intent_key=?", (entry_key,),
        ).fetchone()
        symbol, direction, ref, stop = proof
        account = self.transport.api.account(self.transport.account_id)
        orders = self.transport.api.orders(self.transport.account_id)
        positions = position_quantities(account)
        if set(positions) - {symbol}:
            raise M15OneShotCycleError("M15_ONESHOT_FOREIGN_POSITION_HALTED")
        owned_ids = {
            self.journal.recover_draft(key).payload["client_order_id"]
            for (key,) in self.journal.db.execute(
                "SELECT intent_key FROM outbound")}
        if any(x.active and x.client_order_id not in owned_ids
               for x in order_views(orders)):
            raise M15OneShotCycleError("M15_ONESHOT_FOREIGN_ORDER_HALTED")
        stop_key = stop_key_for(entry_key)
        if positions.get(symbol, 0):
            # H1: install/recover the real broker backstop BEFORE reading
            # fills or considering any later candle/trailing signal.
            stop_report = self.transport.drive_one_shot_initial_stop_once(
                journal=self.journal, entry_key=entry_key,
                entry_draft=self.journal.recover_draft(entry_key),
                stop_key=stop_key, drafts=self.drafts,
                instrument=symbol.split("@")[0], direction=direction,
                reference_entry=Decimal(ref),
                precommitted_stop=Decimal(stop), atr_at_signal=atr,
                contract=contract, sized=sized,
            )
            if stop_report.get("position_protected") is not True:
                return stop_report
            # These GETs can be delayed: the STOP remains active meanwhile.
            after_stop = self.transport.reconcile_entry_from_finam(
                journal=self.journal, key=entry_key,
                draft=self.journal.recover_draft(entry_key),
                expected=None, stop_trade_tag=trade_tag(entry_key),
                start=(signal_time - timedelta(seconds=1)).isoformat(),
                end=(now + timedelta(seconds=1)).isoformat(),
            )
            if after_stop["matched_quantity"] <= 0:
                raise M15OneShotCycleError("M15_ONESHOT_BROKER_FILL_MISSING")
            state = self.transport.observe_one_shot_coverage_or_flat_once(
                journal=self.journal, entry_key=entry_key,
                stop_key=stop_key, observed_at=now,
            )
            # Real 3.5ATR trailing is not marked active by this bootstrap
            # coordinator. Full H1-style bar/trailing management is still
            # required before the production Task and LIVE are released.
            return state | {"trailing_live_complete": False}
        # No position is NOT proof that an uncertain ENTRY never executed.
        if self.journal.inspect(stop_key) is None:
            return {"status": "ENTRY_UNCERTAIN_OR_UNFILLED_GET_RECOVERY_REQUIRED",
                    "new_entries_authorized": False}
        flat = self.transport.observe_one_shot_coverage_or_flat_once(
            journal=self.journal, entry_key=entry_key,
            stop_key=stop_key, observed_at=now,
        )
        return flat | {"trailing_live_complete": False}

    def once(self, *, now: datetime, new_entry_permitted: bool = False) -> dict:
        if (not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None
                or type(new_entry_permitted) is not bool):
            raise M15OneShotCycleError("M15_ONESHOT_TIME_OR_MODE_INVALID")
        with M15SingleInstance(
                self.transport.runtime_root / "state" / _LOCK):
            self.transport._require_connected()
            entries = self.journal.db.execute(
                "SELECT intent_key FROM outbound WHERE kind='ENTRY' "
                "ORDER BY rowid").fetchall()
            if len(entries) > 1:
                raise M15OneShotCycleError(
                    "M15_ONESHOT_MULTIPLE_ENTRIES_NOT_ACCEPTED")
            if entries:
                return self._manage_existing(entries[0][0], now)
            if not new_entry_permitted:
                return {"status": "HALTED_NO_ENTRY", "new_entries_authorized": False}
            # No more than one real acceptance ENTRY, and only a broker-FLAT
            # M15 account may prepare it. The transport rechecks EVERYTHING
            # after signal preparation and before sending a market order.
            account = self.transport.api.account(self.transport.account_id)
            orders = self.transport.api.orders(self.transport.account_id)
            if (position_quantities(account)
                    or any(x.active for x in order_views(orders))):
                raise M15OneShotCycleError(
                    "M15_ONESHOT_ACCOUNT_NOT_FLAT_FOR_ENTRY")
            for instrument in INSTRUMENTS:
                prepared = self.journal.prepare_verified_next_open_r15(
                    api=self.transport.api,
                    m15_account_id=self.transport.account_id,
                    drafts=self.drafts, instrument=instrument,
                    authenticated_seed=self.seeds[instrument],
                    interval_start=self.interval_start,
                    interval_end=self.interval_end,
                    observed_at=now, now=now,
                    verified_open_labels=self.verified_open_labels,
                )
                if prepared is None:
                    continue
                witness, draft, sized = prepared
                asset = self.transport.api.asset_details(
                    instrument + "@RTSX")
                params = self.transport.api.asset_params(
                    instrument + "@RTSX")
                contract = contract_from_moex_and_finam(
                    check_instrument(
                        asset, params, instrument + "@RTSX",
                        self.transport.account_id))
                persist_original_signal_context(
                    journal=self.journal,
                    entry_key=witness.signal.signal_id,
                    signal_closed_at=witness.signal.completed_at,
                    signal_atr=Decimal(str(witness.signal.signal_atr14)),
                    contract=contract, sized=sized)
                receipt = self.transport.submit_entry(
                    journal=self.journal, key=witness.signal.signal_id,
                    draft=draft,
                    signal_atr=Decimal(str(witness.signal.signal_atr14)),
                    signal_closed_at=witness.signal.completed_at,
                    authenticated_seed=self.seeds[instrument],
                    interval_start=self.interval_start,
                    interval_end=self.interval_end,
                    verified_open_labels=self.verified_open_labels,
                )
                return {"status": "ENTRY_SENT_BROKER_FILL_AND_STOP_UNPROVEN",
                        "post_ack_observed": receipt["post_ack_observed"],
                        "new_entries_authorized": False}
            return {"status": "NO_VERIFIED_NEXT_OPEN_SIGNAL",
                    "new_entries_authorized": False}
