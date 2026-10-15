"""Receiving side only: a single packaged OFFLINE_FIXTURE, never Intel telemetry."""
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from ..models import (
    BarObservation, Candle, DataProvenance, ExecutionState, FieldObservation,
    H1ReadonlyDetails, InstrumentStatus, OrderEvent, PortfolioSnapshot,
    PositionSnapshot, RiskSnapshot, RobotId, RobotSnapshot, RobotStatus,
    SignalEvent, SourceKind, State, StopObservation, SystemAlert, aware,
)
from .h1_contract import (
    ACCEPTED_COMMIT, ACTIVE, FINANCIAL_TTL, HEARTBEAT_TTL, MAX_BYTES, MAX_SKEW,
    N4, RECONCILIATION_TTL, SNAPSHOT_TTL, SPEC, timestamp, validate,
)
from .readonly_file import read_snapshot

# Trusted package configuration. No environment, query parameter, uploader,
# session-state path or constructor option can select a production location.
FIXTURE_ROOT = Path(__file__).absolute().parents[2] / "fixtures" / "h1"
SAFE_ERROR = "H1_SNAPSHOT_INVALID_OR_UNAVAILABLE"


def canonical_digest(value):
    payload = {key: item for key, item in value.items() if key != "payload_sha256"}
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")).hexdigest()


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("DUPLICATE_KEY")
        value[key] = item
    return value


def _reject_constant(value):
    raise ValueError("NONFINITE_JSON")


def _quality(at, now, ttl):
    if at is None or ttl is None:
        return State.UNKNOWN
    age = (now - at).total_seconds()
    if age < -MAX_SKEW:
        return State.UNKNOWN
    return State.STALE if age > ttl else State.HEALTHY


def _provenance(now, observed=None):
    return DataProvenance(RobotId.H1, "FIXTURE-H1", "OFFLINE_FIXTURE/H1", observed, now,
                          source_kind=SourceKind.OFFLINE_FIXTURE,
                          snapshot_ttl_seconds=SNAPSHOT_TTL, heartbeat_ttl_seconds=HEARTBEAT_TTL)


def unavailable(now):
    p = _provenance(now)
    return RobotSnapshot(
        RobotStatus(p, State.UNKNOWN, "TradingSystemLab", "T3/H1/TRAIL1", ACTIVE,
                    None, None, None, False, None, None, None), (), (), (), (), None,
        RiskSnapshot(p, None, None, None, None, SAFE_ERROR),
        PortfolioSnapshot(p, None, None, None, None, None, None), None,
        (SystemAlert(p, None, now, "ERROR", "WARNING", SAFE_ERROR),))


def _check_times(value, upper):
    """Validate every observation/event time, not just the transport envelope."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("_at") and child is not None:
                if timestamp(child) > upper:
                    raise ValueError("TIME_ORDER_INVALID")
            else:
                _check_times(child, upper)
    elif isinstance(value, list):
        for child in value:
            _check_times(child, upper)


def _evidence(value, kind, now, observed, ttl):
    return (value is not None and value["kind"] == kind and value["complete"]
            and observed is not None and timestamp(value["observed_at"]) <= observed
            and _quality(timestamp(value["observed_at"]), now, ttl) == State.HEALTHY)


def _unique(rows, key):
    values = [row[key] for row in rows]
    if len(values) != len(set(values)):
        raise ValueError("DUPLICATE_ROW")


class H1ReadonlyProvider:
    def snapshot(self, robot_id: RobotId, scenario: str, now: datetime) -> RobotSnapshot:
        # No last-good cache. Every failure produces a new, empty UNKNOWN.
        try:
            aware(now)
            if now is None or robot_id != RobotId.H1 or not isinstance(robot_id, RobotId):
                raise ValueError("H1_ONLY")
            raw = read_snapshot(FIXTURE_ROOT, "h1.snapshot.json", MAX_BYTES)
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_reject_constant)
            validate(value)
            if value["payload_sha256"] != canonical_digest(value):
                raise ValueError("INTEGRITY_INVALID")
            generated, observed = timestamp(value["generated_at"]), timestamp(value["observed_at"])
            if generated > now + timedelta(seconds=MAX_SKEW) or observed > generated:
                raise ValueError("TIME_ORDER_INVALID")
            _check_times({k: v for k, v in value.items() if k != "generated_at"}, observed)
            return self._convert(value, now, generated, observed)
        except Exception:
            # Do not log exception strings: paths and upstream errors may contain secrets.
            return unavailable(now)

    def _convert(self, value, now, generated, observed):
        p = _provenance(now, observed)
        observations = []
        snapshot_quality = _quality(observed, now, SNAPSHOT_TTL)
        if snapshot_quality == State.HEALTHY and value["runtime"]["source_status"] != "AVAILABLE":
            snapshot_quality = State.UNKNOWN

        def observe(name, group, ttl):
            at = timestamp(group["observed_at"])
            quality = _quality(at, now, ttl)
            if snapshot_quality != State.HEALTHY:
                quality = snapshot_quality
            observations.append(FieldObservation(name, at, quality))
            return at, quality

        runtime = value["runtime"]
        runtime_at, runtime_quality = observe("runtime", runtime, SNAPSHOT_TTL)
        heartbeat = timestamp(runtime["heartbeat_at"])
        cycle = timestamp(runtime["last_successful_cycle_at"])
        if any(at is not None and at > runtime_at for at in (heartbeat, cycle)):
            raise ValueError("RUNTIME_TIME_INVALID")
        heartbeat_quality = _quality(heartbeat, now, HEARTBEAT_TTL)
        observations.append(FieldObservation("heartbeat", heartbeat, heartbeat_quality))
        observations.append(FieldObservation("last_successful_cycle", cycle, _quality(cycle, now, HEARTBEAT_TTL)))
        rec = value["reconciliation"]
        rec_at, rec_quality = observe("reconciliation", rec, RECONCILIATION_TTL)
        rec_success = timestamp(rec["last_success_at"])
        if rec_success is not None and (rec_at is None or rec_success > rec_at):
            raise ValueError("RECONCILIATION_TIME_INVALID")
        reconciled = (rec["status"] == "PASS" and rec_quality == State.HEALTHY
                      and _quality(rec_success, now, RECONCILIATION_TTL) == State.HEALTHY)
        state = State(runtime["state"])
        if runtime_quality != State.HEALTHY:
            state = runtime_quality
        elif runtime["source_status"] != "AVAILABLE":
            state = State.UNKNOWN
        elif state == State.HEALTHY:
            if heartbeat_quality != State.HEALTHY:
                state = heartbeat_quality
            elif _quality(cycle, now, HEARTBEAT_TTL) != State.HEALTHY:
                state = _quality(cycle, now, HEARTBEAT_TTL)
            elif rec["status"] == "FAULT":
                state = State.UNHEALTHY
            elif not reconciled or rec["unresolved_intents"] is None:
                state = State.UNKNOWN
            elif rec["unresolved_intents"] > 0:
                state = State.UNRESOLVED
        # HALTED intentionally does not require heartbeat/cycle/reconciliation PASS.
        # Source freshness is still required; a dated document is not a source observation.
        bars, instruments, candles, close_by_symbol = [], [], [], {}
        _unique(value["bars"], "instrument")
        if set(row["instrument"] for row in value["bars"]) != set(N4):
            raise ValueError("N4_INCOMPLETE")
        for row in value["bars"]:
            at, quality = observe("bar/" + row["instrument"], row, None)
            close, open_at = timestamp(row["close_at"]), timestamp(row["open_at"])
            if close is not None:
                if (not row["completed"] or open_at is None or close - open_at != timedelta(hours=1)
                        or close > at or row["time_source"] != "RUNTIME_HISTORY_OPEN_PLUS_1H"):
                    raise ValueError("BAR_NOT_COMPLETED")
            elif row["completed"] or open_at is not None or row["ohlc"] is not None:
                raise ValueError("BAR_INCOMPLETE")
            if row["quality"] == "CONFIRMED" and close is None:
                raise ValueError("BAR_INCOMPLETE")
            close_by_symbol[row["instrument"]] = close
            bar_quality = State.DATA_GAP if row["gaps"] is True or row["quality"] == "GAP" else quality
            bars.append(BarObservation(p, row["instrument"], close, row["time_source"],
                                       row["gaps"], row["quality"], bar_quality))
            instruments.append(InstrumentStatus(p, row["instrument"], bar_quality, close,
                                                 "UNKNOWN / Причина не опубликована", None, None))
            if row["ohlc"] is not None:
                candle = Candle(p, row["instrument"], close, **row["ohlc"])
                if row["quality"] == "CONFIRMED" and snapshot_quality == State.HEALTHY:
                    candles.append(candle)

        signal_group = value["signals"]
        signal_at, signal_quality = observe("signals", signal_group, None)
        signals = []
        _unique(signal_group["items"], "instrument")
        for row in signal_group["items"]:
            close = timestamp(row["bar_close_at"])
            if (signal_at is None or close > signal_at or close_by_symbol[row["instrument"]] != close):
                raise ValueError("SIGNAL_BAR_MISMATCH")
            # Emitted historical event, never inferred from an absent row.
            if snapshot_quality == State.HEALTHY:
                reason = row["rejection_reason"] or "UNKNOWN / Причина не опубликована"
                signals.append(SignalEvent(p, row["instrument"], close, row["direction"],
                                           f"{reason}; risk={row['risk_result']}", None))

        orders_group = value["orders"]
        order_at, order_quality = observe("orders", orders_group, RECONCILIATION_TTL)
        orders = []
        _unique(orders_group["items"], "reference")
        for row in orders_group["items"]:
            occurred = timestamp(row["occurred_at"])
            if order_at is None or occurred > order_at:
                raise ValueError("ORDER_TIME_INVALID")
            execution = ExecutionState(row["state"])
            filled, price, proof = row["filled_quantity"], row["fill_price"], row["evidence"]
            if execution != ExecutionState.FILL_CONFIRMED and any(item is not None for item in (filled, price, proof)):
                raise ValueError("ACK_IS_NOT_FILL")
            if execution == ExecutionState.FILL_CONFIRMED:
                if not _evidence(proof, "FIXTURE_TRADE_HISTORY", now, order_at, RECONCILIATION_TTL) or not reconciled:
                    execution, filled, price, proof = ExecutionState.UNRESOLVED, None, None, None
            if snapshot_quality == State.HEALTHY and order_quality == State.HEALTHY:
                orders.append(OrderEvent(p, row["instrument"], occurred, "fixture-" + row["reference"][:12],
                                         execution, row["quantity"], filled, price,
                                         "OFFLINE_FIXTURE/TRADE_HISTORY" if proof else None))

        position_group = value["positions"]
        position_at, position_quality = observe("positions", position_group, RECONCILIATION_TTL)
        position_rows = position_group["items"]
        _unique(position_rows, "instrument")
        known_positions = (reconciled and position_group["complete"] and position_quality == State.HEALTHY)
        positions = [] if known_positions else None
        for row in position_rows:
            if row["quantity"] <= 0:
                raise ValueError("POSITION_QUANTITY_INVALID")
            if positions is not None:
                price = row["entry_price"] if _evidence(row["price_evidence"], "FIXTURE_TRADE_HISTORY", now,
                                                       position_at, RECONCILIATION_TTL) else None
                positions.append(PositionSnapshot(p, row["instrument"], row["quantity"], price, None, None, None, side=row["side"]))

        stop_group = value["stops"]
        stop_at, stop_quality = observe("stops", stop_group, RECONCILIATION_TTL)
        stops = []
        _unique(stop_group["items"], "instrument")
        for row in stop_group["items"]:
            checked = timestamp(row["checked_at"])
            if checked is not None and (stop_at is None or checked > stop_at):
                raise ValueError("STOP_TIME_INVALID")
            matching = any((pos["instrument"], pos["side"], pos["quantity"]) ==
                           (row["instrument"], row["side"], row["quantity"]) for pos in position_rows)
            proof = (known_positions and stop_group["complete"] and stop_quality == State.HEALTHY and matching
                     and _quality(checked, now, RECONCILIATION_TTL) == State.HEALTHY
                     and _evidence(row["evidence"], "FIXTURE_BROKER_SLTP", now, stop_at, RECONCILIATION_TTL))
            protected = bool(proof and row["broker_status"] == "ACTIVE" and row["quantity"] > 0
                             and row["expected_quantity"] == row["quantity"] == row["observed_quantity"])
            stops.append(StopObservation(p, row["instrument"], row["side"], row["quantity"], row["expected_quantity"],
                                         row["observed_quantity"] if proof else None,
                                         row["broker_status"] if proof else "UNKNOWN", checked,
                                         "OFFLINE_FIXTURE/BROKER_SLTP" if proof else None, protected))

        finance = value["finances"]
        finance_at, finance_quality = observe("finances", finance, FINANCIAL_TTL)
        numeric = ("equity", "realized_pnl", "unrealized_pnl", "commissions", "deposits", "withdrawals",
                   "available_margin", "used_risk_pct", "contracts")
        financial_authority = (reconciled and finance["complete"] and finance_quality == State.HEALTHY
                               and all(finance[key] is not None for key in numeric)
                               and _evidence(finance["evidence"], "FIXTURE_ACCOUNT", now, finance_at, FINANCIAL_TTL))
        numbers = {key: finance[key] if financial_authority else None for key in numeric}
        details = H1ReadonlyDetails(
            p, SPEC, ACCEPTED_COMMIT, "FIXTURE-H1", generated, cycle,
            rec["status"] if rec_quality == State.HEALTHY else "UNKNOWN",
            rec["unresolved_intents"] if rec_quality == State.HEALTHY else None,
            runtime["source_status"], bool(reconciled and orders_group["complete"] and order_quality == State.HEALTHY),
            bool(known_positions), tuple(observations), tuple(bars), tuple(stops),
            numbers["deposits"], numbers["withdrawals"], numbers["available_margin"])
        # Aggregate candle timestamp only when all N4 closes agree; otherwise see per-symbol details.
        closes = set(close_by_symbol.values())
        last_bar = next(iter(closes)) if len(closes) == 1 else None
        status = RobotStatus(p, state, "TradingSystemLab", "T3/H1/TRAIL1", ACTIVE, heartbeat, last_bar,
                             len(positions) if positions is not None else None,
                             runtime["trading_permission"] if runtime_quality == State.HEALTHY else None, None, None, None)
        return RobotSnapshot(status, tuple(instruments), tuple(candles), tuple(signals), tuple(orders),
                             tuple(positions) if positions is not None else None,
                             RiskSnapshot(p, 1.5, 6.0, numbers["used_risk_pct"], numbers["contracts"],
                                          "Frozen R15 1.5% / 6%; OFFLINE_FIXTURE, не торговая авторизация"),
                             PortfolioSnapshot(p, numbers["equity"], numbers["realized_pnl"],
                                               numbers["unrealized_pnl"], numbers["commissions"], None, None),
                             None, (), details)
