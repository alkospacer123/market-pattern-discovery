"""Offline/READONLY operator rendering of a market suitability card.

Usage (repository root):
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input completed_sessions.json

Input is a previously VERIFIED snapshot, not a FINAM session discovery tool.
Default output to stdout, so the existing V20 logger/operator can capture JSON.
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


def _load_snapshot(path: Path) -> tuple[str, datetime, tuple[CompletedSession, ...], dict]:
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
            sessions, data.get("execution_readonly", {}))


def format_text(card: dict) -> str:
    quality = card["metrics"]["data_quality"]
    lines = [
        "V20 MARKET SUITABILITY — READONLY / НЕ ТОРГОВЫЙ ФИЛЬТР",
        f"Инструмент {card['symbol']} | данные до {card['as_of_msk']} МСК",
        f"Завершённых сессий {quality['observed_sessions']}/{quality['required_sessions']}; "
        f"пропусков M15 {quality['missing_bars']}",
    ]
    for name in STRATEGIES:
        diagnostics = card["strategies"][name]
        metrics = ", ".join(f"{k}={v if v is not None else 'НЕИЗВЕСТНО'}"
                            for k, v in diagnostics["diagnostics"].items())
        lines.append(f"{name}: {diagnostics['suitability']} | {metrics}")
    lines.append("Изменения значений не являются подтверждением улучшения пригодности; "
                 "сигналы, стопы и риск не изменяются.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V20 market card; readonly, no FINAM")
    parser.add_argument("--input", type=Path, required=True,
                        help="locally verified closed sessions JSON")
    parser.add_argument("--previous", type=Path, default=None,
                        help="previous output card JSON, for metric deltas")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)
    try:
        symbol, as_of, sessions, execution = _load_snapshot(args.input)
        previous = (json.loads(args.previous.read_text(encoding="utf-8"))
                    if args.previous is not None else None)
        card = evaluate_market_card(
            symbol, sessions, as_of=as_of, previous=previous,
            execution_readonly=execution)
        output = (json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False)
                  if args.format == "json" else format_text(card))
        print(output)
        return 0
    except (KeyError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"V20_MARKET_CARD_INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
