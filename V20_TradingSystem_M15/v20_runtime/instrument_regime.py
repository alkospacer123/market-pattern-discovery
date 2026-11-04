"""V20 instrument-level READONLY regime OBSERVATION (not a forecast/filter).

Only finished frozen RAW_SIGNAL paths; combines duplicate robot signals for the
same market event. No FINAM, credentials, orders, SQLite or trade decisions.
"""
from __future__ import annotations

from datetime import datetime
from math import isclose, isfinite
from statistics import mean

SCHEMA = "v20.instrument_regime.readonly.v1"
WINDOW = 20
PERSISTENCE = 5
MAX_SPAN_DAYS = 365
MAX_AGE_DAYS = 90


def _dt(value):
    stamp = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(stamp, datetime) or stamp.tzinfo is not None:
        raise ValueError("MOSCOW_NAIVE_REQUIRED")
    return stamp


def unique_events(paths, *, instrument, as_of):
    """No future outcome is read, even when a caller passes future object sentinels."""
    at = _dt(as_of)
    events = {}
    for path in paths:
        if path["instrument"].upper() != instrument.upper():
            continue
        complete = _dt(path["available"])
        if complete > at:
            continue
        signal = _dt(path["signal"])
        contract = path["contract"]
        value = float(path["raw_R"])
        if (not isfinite(value) or complete <= signal or
                type(path["stop_touch"]) is not bool):
            raise ValueError("INVALID_COMPLETED_RAW_PATH")
        key = (path["instrument"].upper(), signal)
        existing = events.get(key)
        current = dict(instrument=instrument.upper(), contract=contract,
                       signal=signal, available=complete, raw_R=value,
                       stop_touch=path["stop_touch"])
        if existing is not None:
            if (existing["contract"] != contract or existing["available"] != complete or
                    existing["stop_touch"] != current["stop_touch"] or
                    not isclose(existing["raw_R"], value, rel_tol=1e-12, abs_tol=1e-9)):
                raise ValueError("CONFLICTING_DUPLICATE_FROZEN_SIGNALS")
        else:
            events[key] = current
    return sorted(events.values(), key=lambda v: (v["available"], v["signal"], v["contract"]))


def _summary(events):
    if not events:
        return dict(n=0, raw_R=None, stop_aware_reference_R=None,
                    stop_touch_pct=None, tail5_no_stop_pct=None,
                    first_signal=None, last_signal=None, last_horizon=None, span_days=None)
    return dict(n=len(events), raw_R=mean(x["raw_R"] for x in events),
                stop_aware_reference_R=mean(-1.0 if x["stop_touch"] else x["raw_R"] for x in events),
                stop_touch_pct=100 * mean(x["stop_touch"] for x in events),
                tail5_no_stop_pct=100 * mean((not x["stop_touch"]) and x["raw_R"] >= 5 for x in events),
                first_signal=min(x["signal"] for x in events).isoformat(),
                last_signal=max(x["signal"] for x in events).isoformat(),
                last_horizon=max(x["available"] for x in events).isoformat(),
                span_days=(max(x["available"] for x in events) -
                           min(x["signal"] for x in events)).days)


def _window(events, at):
    eligible = [x for x in events if x["available"] <= at]
    current = _summary(eligible[-WINDOW:])
    previous = _summary(eligible[-2 * WINDOW:-WINDOW])
    delta = (current["raw_R"] - previous["raw_R"]
             if current["n"] == previous["n"] == WINDOW else None)
    reasons = []
    if current["n"] < WINDOW:
        reasons.append("FEWER_THAN_20_EVENTS")
    if delta is None:
        reasons.append("FEWER_THAN_40_EVENTS_FOR_CHANGE")
    for label, w in (("CURRENT", current), ("PREVIOUS", previous)):
        if w["span_days"] is not None and w["span_days"] > MAX_SPAN_DAYS:
            reasons.append(label + "_WINDOW_TOO_LONG")
    age = (at - _dt(current["last_horizon"])).days if current["n"] else None
    if age is not None and age > MAX_AGE_DAYS:
        reasons.append("RAW_OUTCOME_STALE")
    return dict(current=current, previous=previous, delta_raw_R=delta,
                eligible=len(eligible), age_days=age, reasons=reasons,
                declining=delta is not None and delta < 0 and not reasons)


def instrument_regime_card(paths, symbol, as_of):
    """Past-only market pulse. Observed persistence is NOT future-regime accuracy."""
    at = _dt(as_of)
    if not isinstance(symbol, str) or not symbol or not symbol.replace("_", "").isalnum():
        raise ValueError("INVALID_INSTRUMENT")
    events = unique_events(paths, instrument=symbol, as_of=at)
    state = _window(events, at)
    completed_times = sorted({x["available"] for x in events})
    last_five = [_window(events, time) for time in completed_times[-PERSISTENCE:]]
    sustained = (len(last_five) == PERSISTENCE and
                 all(x["declining"] for x in last_five))
    if state["reasons"]:
        status = "НЕДОСТАТОЧНО ДАННЫХ"
    elif sustained:
        status = "УСТОЙЧИВОЕ НАБЛЮДАЕМОЕ СНИЖЕНИЕ"
    elif state["declining"]:
        status = "РАННЕЕ НАБЛЮДАЕМОЕ СНИЖЕНИЕ"
    else:
        status = "СНИЖЕНИЕ НЕ ПОДТВЕРЖДЕНО"
    eligible_paths = sum(1 for p in paths if p["instrument"].upper() == symbol.upper()
                         and _dt(p["available"]) <= at)
    return dict(schema=SCHEMA, symbol=symbol.upper(), as_of_msk=at.isoformat(),
                observed_raw_paths=eligible_paths, unique_completed_events=len(events),
                duplicate_paths_removed=eligible_paths - len(events),
                current=state["current"], previous=state["previous"],
                delta_raw_R=state["delta_raw_R"], age_days=state["age_days"],
                warning_persistence=PERSISTENCE if sustained else sum(x["declining"] for x in last_five),
                status=status, reasons=state["reasons"],
                prediction_validated=False, next20_reliable=False,
                finam_live_feed="NOT_CONNECTED", affects_orders_or_risk=False,
                independent_out_of_sample=False,
                limitation="Historical observation only; stop-aware -1R assumes ideal fill, no fees/gaps.")


def format_card(card):
    current, previous = card["current"], card["previous"]
    def num(x, suffix="R"):
        return f"{x:+.3f}{suffix}" if x is not None else "Н/Д"
    return "\n".join((
        f"V20 — ИНСТРУМЕНТ {card['symbol']} / READONLY",
        f"На дату {card['as_of_msk']} МСК | LIVE FINAM: НЕ ПОДКЛЮЧЁН",
        f"Raw R завершённые 20: {num(current['raw_R'])} | предыдущие 20: {num(previous['raw_R'])} | Δ: {num(card['delta_raw_R'])}",
        f"Условно с 2ATR стопом (НЕ PnL): {num(current['stop_aware_reference_R'])}",
        f"Касания стопа: {num(current['stop_touch_pct'], '%')} | движение 5R без стопа: {num(current['tail5_no_stop_pct'], '%')}",
        f"ATR14/Close (справочно): {num(card.get('atr_reference', {}).get('atr14_pct_close') * 100 if card.get('atr_reference', {}).get('atr14_pct_close') is not None else None, '%')}",
        f"Наблюдений: {card['unique_completed_events']} уникальных / {card['observed_raw_paths']} raw; повторов {card['duplicate_paths_removed']}",
        f"Последний полный горизонт: {current['last_horizon'] or 'Н/Д'}, давность {card['age_days']} д.",
        f"Статус: {card['status']} | подтверждений за последние 5 завершений: {card['warning_persistence']}",
        f"Ограничения: {', '.join(card['reasons']) or 'нет ограничений истории'}",
        "Статус говорит о прошлом, НЕ о достоверном прогнозе будущего. Не влияет на заявки/N4."
    ))


def main(argv=None):
    import argparse
    import json
    from zoneinfo import ZoneInfo
    from .market_rolling_raw import load_paths
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    as_of = _dt(args.as_of) if args.as_of else datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None, second=0, microsecond=0)
    paths, _ = load_paths(as_of=as_of)  # SHA verified; excludes unknown and future numerics
    card = instrument_regime_card(paths, args.symbol, as_of)
    print(json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False) if args.format == "json"
          else format_card(card))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
