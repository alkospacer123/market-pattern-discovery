"""Offline/READONLY operator rendering of a market suitability card.

Usage (repository root):
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input completed_sessions.json

Input is a previously VERIFIED snapshot, not a FINAM session discovery tool.
Compact text by default; --details or --format json expose the five groups.
No write to SQLite, tasks, tokens, orders, H1 or IntradayLab.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

from .market_suitability import (
    CompletedSession, M15Bar, evaluate_market_card,
)
from .market_verdict import apply_market_reference
from .market_ranges import DEFAULT_RANGES, annotate_card
from .market_epochs import DEFAULT_EPOCHS, annotate_epochs, annotate_instrument


def _load_snapshot(path: Path) -> tuple:
    data = json.loads(path.read_text(encoding="utf-8"))
    sessions = tuple(CompletedSession(
        day=date.fromisoformat(s["day"]),
        expected_opens=tuple(datetime.fromisoformat(t) for t in s["expected_opens"]),
        bars=tuple(M15Bar(
            datetime.fromisoformat(b["open_time"]),
            b["open"], b["high"], b["low"], b["close"], b["volume"])
            for b in s["bars"]),
        closed_at=datetime.fromisoformat(s["closed_at"]),
    ) for s in data["completed_sessions"])
    return (data["symbol"], datetime.fromisoformat(data["as_of_msk"]),
            sessions, data.get("execution_readonly", {}),
            tuple(date.fromisoformat(d) for d in data["expected_session_days"])
            if "expected_session_days" in data else None)


def format_text(card: dict, *, details: bool = False) -> str:
    quality = card["metrics"]["data_quality"]
    assessment = card.get('instrument_assessment') or annotate_instrument(card)['instrument_assessment']
    def number(value):
        return f"{value:.4f}" if value is not None else 'Н/Д'
    def interval(item):
        if not item or item['p25'] is None or item['p75'] is None:
            return 'Н/Д'
        return f"{number(item['p25'])}–{number(item['p75'])} (N={item['n']})"
    lines = [
        "V20 — АНАЛИТИЧЕСКАЯ КАРТОЧКА ИНСТРУМЕНТА",
        f"ИНСТРУМЕНТ {card['symbol']} | M15 | ДАННЫЕ ДО {card.get('last_completed_session', card['as_of_msk'])}",
        f"Сопоставление с эталонами на {card['as_of_msk']} МСК; исторический снимок, не LIVE.",
        f"ОБЩИЙ ИСТОРИЧЕСКИЙ РЕЖИМ: {assessment['status']}",
        f"Причина: {assessment['reason']} Историческая диагностика, не прогноз PF.",
        "Параметр | Сейчас | 2018–2022: от–до | 2023–2024: от–до | Оценка",
    ]
    for row in assessment['rows']:
        events=f" (N={row['current_events']})" if row['current_events'] is not None else ''
        lines.append(f"{row['label']} | {number(row['value'])}{events} | {interval(row['old'])} | "
                     f"{interval(row['new'])} | {row['assessment']}")
    atr = assessment['atr14_pct_close']
    lines += [f"Справочно ATR14/Close: {number(100*atr) if atr is not None else 'Н/Д'}%",
        "Диапазоны — семейные p25–p75 рынка, не границы пригодности.",
        f"Данные: {quality['observed_sessions']}/{quality['required_sessions']} завершённых сессий; "
        f"пропусков M15 {quality['missing_bars']}; сессий {quality['missing_sessions']}.",
        f"Календарь: {quality.get('session_calendar','ОПРЕДЕЛЁН ИСТОЧНИКОМ')}; полнота требует внешней проверки.",
        assessment['limitation'],
        "2023–2024 — рабочее сравнение; полный опубликованный эталон 2023–2026: 1589 сделок.",
        "Не влияет на заявки, сигнал, стоп и риск. Независимая торговая пригодность не доказана.",
    ]
    if details:
        for name in ("volatility", "directionality", "breakouts", "volume_pressure", "compression", "liquidity"):
            lines.append(name + ": " + ", ".join(
                f"{k}={v if v is not None else 'НЕИЗВЕСТНО'}"
                for k, v in card["metrics"][name].items()))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V20 market card; readonly, no FINAM")
    parser.add_argument("--input", type=Path, required=True,
                        help="locally verified closed sessions JSON")
    parser.add_argument("--previous", type=Path, default=None,
                        help="previous output card JSON, for metric deltas")
    parser.add_argument("--reference-profile", type=Path, default=None,
                        help="explicitly reviewed holdout-validated diagnostic profile; never a trading gate")
    parser.add_argument("--typical-ranges", type=Path, default=DEFAULT_RANGES,
                        help="descriptive p25/p75 artifact; never a validated suitability profile")
    parser.add_argument("--epoch-profile",type=Path,default=DEFAULT_EPOCHS,
                        help="descriptive historical similarity only; no trading authority")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--details", action="store_true", help="show numeric details in text output")
    args = parser.parse_args(argv)
    try:
        symbol, as_of, sessions, execution, calendar = _load_snapshot(args.input)
        previous = (json.loads(args.previous.read_text(encoding="utf-8"))
                    if args.previous is not None else None)
        card = evaluate_market_card(
            symbol, sessions, as_of=as_of, previous=previous,
            execution_readonly=execution, expected_session_days=calendar)
        reference = (json.loads(args.reference_profile.read_text(encoding="utf-8"))
                     if args.reference_profile is not None else None)
        card = apply_market_reference(card, reference)
        if args.typical_ranges.exists():
            card = annotate_card(card,json.loads(args.typical_ranges.read_text(encoding='utf-8')))
        epoch_profile = (json.loads(args.epoch_profile.read_text(encoding='utf-8'))
                         if args.epoch_profile.exists() else None)
        if epoch_profile is not None:
            card = annotate_epochs(card,epoch_profile)
        card = annotate_instrument(card,epoch_profile)
        output = (json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False)
                  if args.format == "json" else format_text(card, details=args.details))
        print(output)
        return 0
    except (KeyError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"V20_MARKET_CARD_INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
