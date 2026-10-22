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
    CompletedSession, M15Bar, STRATEGIES, evaluate_market_card,
)
from .market_verdict import apply_market_reference
from .market_ranges import DEFAULT_RANGES, annotate_card


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
    lines = [
        "V20 MARKET SUITABILITY — READONLY / НЕ ТОРГОВЫЙ ФИЛЬТР",
        f"Инструмент {card['symbol']} | данные до {card['as_of_msk']} МСК",
        f"Завершённых сессий {quality['observed_sessions']}/{quality['required_sessions']}; "
        f"пропусков M15 {quality['missing_bars']}; сессий {quality['missing_sessions']}",
    ]
    ranges = card.get('typical_ranges', {})
    typical = ranges.get('values', {})
    def range_line(spec):
        if spec['p25'] is None or spec['p75'] is None:
            return spec['label']+': типичный диапазон НЕ ПРОВЕРЕНО'
        scale = 100 if spec['metric']=='atr14_pct_close' else 1
        unit = '%' if scale==100 else ''
        value = f"{spec['value']*scale:.4g}{unit}" if spec['value'] is not None else 'НЕИЗВЕСТНО'
        return (f"{spec['label']}: {value} / типично {spec['p25']*scale:.4g}–"
                f"{spec['p75']*scale:.4g}{unit} / {spec['position']}")
    if typical:
        lines.append('Типичные диапазоны N4, 2023–2024; календарь эталона FINAM не подтверждён.')
        lines.append(range_line(typical['COMMON_ATR']))
        if not ranges['symbol_in_reference']:
            lines.append('Перенос диапазонов на этот инструмент не проверен.')
    for name in STRATEGIES:
        diagnostics = card["strategies"][name]
        lines.append(f"{name}: {diagnostics['suitability']}")
        reasons = diagnostics.get("explanation", [])[:2]
        readable = {"REFERENCE_NOT_PROVIDED": "Нет проверенного профиля классификации.",
                    "INCOMPLETE_OR_UNVERIFIED_M15": "Недостаточно подтверждённых завершённых сессий."}
        if reasons:
            lines.append("  Причины: " + "; ".join(readable.get(r,r) for r in reasons))
        if name in typical:
            lines.append('  '+range_line(typical[name]))
    if ranges.get('interval_check'):
        lines.append('Пригодность по диапазонам не доказана; независимой проверки нет.')
    if details:
        for name in ("volatility", "directionality", "breakouts", "volume_pressure", "compression", "liquidity"):
            lines.append(name + ": " + ", ".join(
                f"{k}={v if v is not None else 'НЕИЗВЕСТНО'}"
                for k, v in card["metrics"][name].items()))
    lines.append("Изменения значений не являются подтверждением улучшения пригодности; "
                 "сигналы, стопы и риск не изменяются.")
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
        output = (json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False)
                  if args.format == "json" else format_text(card, details=args.details))
        print(output)
        return 0
    except (KeyError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"V20_MARKET_CARD_INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
