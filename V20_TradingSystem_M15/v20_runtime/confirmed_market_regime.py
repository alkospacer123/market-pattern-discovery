"""Confirmed *current observed* V20 instrument regime. Offline/READONLY.

No forecast. No automatic instrument admission, orders, FINAM, H1 or M15
mutation. Two successive, non-overlapping cohorts of finished raw outcomes
must agree. A single unfavorable cohort is not a change of regime.

Definitions match the predeclared V20-04 REGIME_RESEARCH_PROTOCOL_RU.md,
without any fitted parameter: cohort 20; WEAK iff stop-aware mean<0 AND
FP2<1/3, STRONG iff stop-aware mean>=0 AND FP2>=1/3.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path
from statistics import mean
import csv
import json

COHORT_N = 20
CONFIRM_N = 2
MAX_SPAN = timedelta(days=365)
MAX_GAP = timedelta(days=90)
MAX_OUTCOME_STALE = timedelta(days=90)
MAX_M15_STALE = timedelta(days=4)  # fallback; trading-session freshness is authoritative at feed integration
SOURCE_SHA256 = "35cf524fda42d025feec35a39c9605669fc532d6d1107b23b698ecff3d348a5b"
SOURCE_PATH = Path(__file__).resolve().parents[1] / "V20-04/REGIME_EVENTS.csv"


def _dt(value):
    t = datetime.fromisoformat(value) if isinstance(value, str) else value
    if not isinstance(t, datetime) or t.tzinfo is not None:
        raise ValueError("MSK_NAIVE_REQUIRED")
    return t


def load_published(source=SOURCE_PATH, expected_sha=SOURCE_SHA256, *,
                   instrument=None, as_of=None):
    """Read trusted published events; never parse future *numeric* outcomes."""
    if expected_sha and sha256(Path(source).read_bytes()).hexdigest() != expected_sha:
        raise ValueError("REGIME_EVENTS_SHA_MISMATCH")
    cutoff = _dt(as_of) if as_of is not None else None
    rows = []
    with Path(source).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if instrument and row["instrument"].upper() != instrument.upper():
                continue
            if cutoff is not None and _dt(row["available"]) > cutoff:
                continue
            rows.append(row)
    return rows


def _event(row):
    signal, ready = _dt(row["signal"]), _dt(row["available"])
    if ready <= signal or row["fp2"] not in ("0", "1", 0, 1, False, True):
        raise ValueError("INVALID_FINISHED_V20_EVENT")
    fp2 = int(row["fp2"])
    stop_aware = float(row["stop_aware"])
    if not (-1e7 < stop_aware < 1e7):
        raise ValueError("NONFINITE_V20_OUTCOME")
    return dict(instrument=row["instrument"].upper(), signal=signal,
                available=ready, contract=row["contract"],
                fp2=fp2, stop_aware=stop_aware)


def cohorts(rows, instrument, *, as_of):
    """As-of, completed 20-event cohorts; identical timestamps become atomic."""
    at = _dt(as_of)
    events = []
    keys = set()
    for row in rows:
        if row["instrument"].upper() != instrument.upper():
            continue
        if _dt(row["available"]) > at:
            continue  # strictly no future numeric reads
        e = _event(row)
        key = (e["instrument"], e["signal"])
        if key in keys:
            raise ValueError("DUPLICATE_UNIQUE_MARKET_EVENT")
        keys.add(key)
        events.append(e)
    events.sort(key=lambda e: (e["available"], e["signal"], e["contract"]))
    blocks = []
    for i in range(0, len(events) - COHORT_N + 1, COHORT_N):
        q = events[i:i + COHORT_N]
        valid = (max(e["available"] for e in q) -
                 min(e["signal"] for e in q) <= MAX_SPAN and
                 all(b["available"] - a["available"] <= MAX_GAP
                     for a, b in zip(q, q[1:])))
        fp2 = mean(e["fp2"] for e in q)
        sa = mean(e["stop_aware"] for e in q)
        kind = ("WEAK" if sa < 0 and fp2 < 1/3 else
                "FAVORABLE" if sa >= 0 and fp2 >= 1/3 else "MIXED") if valid else "INVALID"
        blocks.append(dict(index=len(blocks), kind=kind, n=len(q),
                           first_signal=min(e["signal"] for e in q).isoformat(),
                           horizon_available=max(e["available"] for e in q).isoformat(),
                           stop_aware_R=sa, fp2=fp2, valid=valid))
    pending = events[len(blocks) * COHORT_N:]
    return blocks, pending, events


def confirmed_card(rows, instrument, *, as_of,
                   latest_completed_m15=None, feed_connected=False):
    """The status never denotes likely future profits or prediction accuracy."""
    at = _dt(as_of)
    if not isinstance(instrument, str) or not instrument or not instrument.replace("_", "").isalnum():
        raise ValueError("INVALID_INSTRUMENT")
    blocks, pending, events = cohorts(rows, instrument, as_of=at)
    last = blocks[-1] if blocks else None
    previous = blocks[-2] if len(blocks) >= 2 else None
    evidence = "INSUFFICIENT_HISTORY"
    if last and previous:
        if last["valid"] and previous["valid"]:
            if last["kind"] == previous["kind"] == "WEAK":
                evidence = "CONFIRMED_OBSERVED_WEAK"
            elif last["kind"] == previous["kind"] == "FAVORABLE":
                evidence = "CONFIRMED_OBSERVED_FAVORABLE"
            else:
                evidence = "UNCONFIRMED_OR_TRANSITION"
        else:
            evidence = "INSUFFICIENT_COHERENT_HISTORY"

    last_horizon = max((x["available"] for x in events), default=None)
    if last_horizon is None or at - last_horizon > MAX_OUTCOME_STALE:
        evidence = "STALE_OR_MISSING_COMPLETED_OUTCOMES"

    m15 = _dt(latest_completed_m15) if latest_completed_m15 is not None else None
    if m15 is not None and m15 > at:
        raise ValueError("M15_FUTURE_CLOSE")
    feed_fresh = m15 is not None and at - m15 <= MAX_M15_STALE
    # Even a fresh historical CSV is not proof of a connected live FINAM feed.
    live_status = (evidence if feed_connected and feed_fresh
                   else "LIVE_FEED_STALE" if feed_connected else "LIVE_FEED_NOT_CONNECTED")

    recent = blocks[-2:]
    return dict(schema="v20.confirmed_current_regime.readonly.v1",
                instrument=instrument.upper(), as_of_msk=at.isoformat(),
                unique_completed_events=len(events), complete_blocks=len(blocks),
                pending_block_n=len(pending),
                most_recent_outcome=last_horizon.isoformat() if last_horizon else None,
                last_completed_m15=m15.isoformat() if m15 else None,
                blocks=recent, historical_observation=evidence,
                live_current_status=live_status,
                source_is_live_connected=bool(feed_connected),
                basis="TWO_CONSECUTIVE_NONOVERLAPPING_20_EVENT_COHORTS",
                threshold_provenance="PREDECLARED_V20_REGIME_RESEARCH_PROTOCOL",
                prediction_validated=False, trading_gate=False,
                no_auto_symbol_rotation=True,
                warning="No future forecast. Consecutive cohorts can still be statistically dependent.")


def format_text(card):
    def number(v):
        return f"{v:+.3f}" if v is not None else "Н/Д"
    out = [f"V20 | {card['instrument']} | ТОЛЬКО ЗАВЕРШЁННЫЕ M15 / READONLY",
           f"As-of МСК: {card['as_of_msk']} | FINAM LIVE: " +
           ("ПОДКЛЮЧЁН (заявлено источником)" if card["source_is_live_connected"] else "НЕ ПОДКЛЮЧЁН"),
           f"Статус по завершённым исходам: {card['historical_observation']}",
           f"Текущий онлайн-статус: {card['live_current_status']}",
           f"Полных блоков: {card['complete_blocks']} по 20, незавершённый блок: {card['pending_block_n']}/20",
           f"Последний завершённый горизонт: {card['most_recent_outcome'] or 'Н/Д'}",
           f"Последняя закрытая M15: {card['last_completed_m15'] or 'Н/Д'}"]
    for b in card["blocks"]:
        out.append(f"Блок {b['index']}: {b['kind']} | FP2={100*b['fp2']:.1f}% | "
                   f"условно со стопом {number(b['stop_aware_R'])}R | до {b['horizon_available']}")
    out.append("Нет автоматического исключения инструмента. Одиночный слабый блок — НЕ подтверждение.")
    return "\n".join(out)


def main(argv=None):
    import argparse
    from zoneinfo import ZoneInfo
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--as-of", default=None)
    parser.add_argument("--events", type=Path, default=SOURCE_PATH)
    parser.add_argument("--last-completed-m15", default=None,
                        help="Archive reference only; does not connect FINAM.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    now = (_dt(args.as_of) if args.as_of else
           datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None, second=0, microsecond=0))
    rows = load_published(args.events, instrument=args.symbol, as_of=now)
    card = confirmed_card(rows, args.symbol, as_of=now,
                          latest_completed_m15=args.last_completed_m15,
                          feed_connected=False)
    print(json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False)
          if args.format == "json" else format_text(card))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
