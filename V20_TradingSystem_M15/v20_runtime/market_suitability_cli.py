"""Offline/READONLY operator rendering of a market suitability card.

Usage (repository root):
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --symbol USDRUBF
python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --input completed_sessions.json

Published SHA-pinned raw paths are primary; optional verified M15 snapshots give
reference ATR. --legacy-diagnostics retains the archived five-group interface.
No write to SQLite, tasks, tokens, orders, H1 or IntradayLab.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from .market_suitability import (
    CompletedSession, M15Bar, evaluate_market_card,
)
from .market_verdict import apply_market_reference
from .market_ranges import DEFAULT_RANGES, annotate_card
from .market_epochs import DEFAULT_EPOCHS, annotate_epochs, annotate_instrument
from .market_rolling_raw import (
    SCHEMA as RAW_SCHEMA, DEFAULT_PROFILE, NAMES, load_paths, instrument_card, atr_reference, stamp,
)
from .instrument_regime import (
    instrument_regime_card, format_card as format_instrument_regime,
)
from .confirmed_market_regime import (
    load_published as load_confirmed_events,
    confirmed_card, format_text as format_confirmed_regime,
)


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
    if card.get('schema')==RAW_SCHEMA or 'rolling_raw' in card:
        return format_raw_text(card.get('rolling_raw',card),details=details)
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


def format_raw_text(card: dict, *, details: bool = False) -> str:
    def number(value):
        return f'{value:+.3f}' if value is not None else 'Н/Д'
    def day(value):
        return value[:10] if value else 'Н/Д'
    lines=['V20 — ОЦЕНКА ИНСТРУМЕНТА (READONLY)',
        f"Инструмент {card['symbol']} | полные raw горизонты до {card['raw_data_through'] or 'Н/Д'} | M15",
        f"As-of {card['as_of_msk']} МСК",
        'Робот | Последние 20 raw R | Предыдущие 20 | ΔR | Мин.* | Реком.* | N/период/горизонт | Оценка']
    outliers=[]
    stops=[]
    conclusions={}
    for row in card['rows']:
        c,p=row['current'],row['previous']
        name=NAMES[row['strategy']]
        value=c['mean'] if c['n']>=10 else None
        period=f"{c['n']}+{p['n']}; {day(c['first_signal'])}–{day(c['last_signal'])}; H {day(c['completed_at'])}"
        period+=f"; {c['span_days']}д / давность {row['age_days']}д" if c['n'] else ''
        trend=row['trend']
        if row['delta_raw_R'] is not None and c['without_2'] is not None and p['without_2'] is not None:
            if (c['without_2']-p['without_2']<0)!=(row['delta_raw_R']<0):
                trend+='; ЧУВСТВИТЕЛЬНО К ВЫБРОСАМ'
        lines.append(f"{name} | {number(value)} | {number(p['mean'])} | {number(row['delta_raw_R'])} | "
            f"{number(row['minimum_reference_R'])} | {number(row['recommended_reference_R'])} | {period} | {trend}")
        stops.append(f"{name} {100*c['stop_touch_share']:.1f}%" if c['n'] else f'{name} Н/Д')
        outliers.append(f"{name} {number(c['without_1'])}/{number(c['without_2'])}")
        conclusions.setdefault(row['trend'],[]).append(name)
    atr=card.get('atr_reference',{})
    value=atr.get('atr14_pct_close')
    lines += [f"Справочно: ATR14/Close {100*value:.4f}% (до {atr.get('data_through')})" if value is not None
              else 'Справочно: ATR14/Close Н/Д — нет проверенного завершённого снимка.',
        '2ATR stop-touch: '+', '.join(stops)+' — справочно, полный путь, не доля SL-сделок.',
        'Среднее без 1/2 крупнейших |raw R|: '+', '.join(outliers)+'.',
        '* Исторические средние слабой/поздней эпохи; надёжные минимумы/рекомендации НЕ УСТАНОВЛЕНЫ.',
        'Ориентиры доступны только после даты их исследования; для раннего as-of — Н/Д.',
        'ИТОГ: '+'; '.join(f"{trend}: {', '.join(names)}" for trend,names in conclusions.items()),
        '10–19 путей — предварительное среднее; для Δ нужны 40. Окно >365д или давность >90д — недостаточно данных.',
        'raw R — движение к третьей сессии, НЕ PnL; может включать цену после стопа.',
        'Не торговый фильтр. Не меняет сигнал, стоп, риск, N4 или FINAM. LIVE не разрешён.']
    if details:
        lines.append('Причины ограничений: '+json.dumps({NAMES[r['strategy']]:r['reasons'] for r in card['rows']},ensure_ascii=False))
    return '\n'.join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="V20 market card; readonly, no FINAM")
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path,
                        help="locally verified closed sessions JSON")
    source.add_argument('--symbol',help='instrument with published frozen raw paths; no FINAM calls')
    parser.add_argument('--as-of',help='Moscow naive ISO time; defaults to current Moscow time')
    parser.add_argument('--monitoring',action='store_true',help='archive-only completed C1 monitoring; --symbol ALL or a single instrument')
    parser.add_argument('--data-dir',type=Path,help='optional SHA-verified N4 quotes for reference ATR only')
    parser.add_argument('--raw-profile',type=Path,default=DEFAULT_PROFILE)
    parser.add_argument('--legacy-diagnostics',action='store_true',help='archived five-group interface')
    parser.add_argument('--raw-diagnostics',action='store_true',
                        help='legacy pooled mean raw 20/20 instead of confirmed observational card')
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
        if args.monitoring:
            from .market_monitoring import load_data,monitoring_card,format_text as render_monitor
            if not args.symbol:raise ValueError('MONITORING_REQUIRES_SYMBOL_OR_ALL')
            as_of=stamp(args.as_of) if args.as_of else datetime.now(ZoneInfo('Europe/Moscow')).replace(tzinfo=None)
            groups,bounds,raw,censored,_=load_data()
            card=monitoring_card(groups,bounds,raw,censored,as_of,args.symbol)
            print(json.dumps(card,ensure_ascii=False,indent=2,default=str,allow_nan=False) if args.format=='json' else render_monitor(card))
            return 0
        raw_profile=(json.loads(args.raw_profile.read_text(encoding='utf-8')) if args.raw_profile.exists() else None)
        if args.symbol:
            if args.legacy_diagnostics:
                raise ValueError('LEGACY_DIAGNOSTICS_REQUIRES_SNAPSHOT')
            as_of=stamp(args.as_of) if args.as_of else datetime.now(ZoneInfo('Europe/Moscow')).replace(tzinfo=None,second=0,microsecond=0)
            if args.raw_diagnostics:
                paths,_=load_paths(as_of=as_of)
                card=instrument_regime_card(paths,args.symbol,as_of)
                card['atr_reference']=atr_reference(args.data_dir,args.symbol.upper(),as_of)
                render=format_instrument_regime
            else:
                # The published path-quality CSV is pinned. Latest verified M15
                # source is informational, NOT a FINAM LIVE connection.
                events=load_confirmed_events(instrument=args.symbol,as_of=as_of)
                atr=atr_reference(args.data_dir,args.symbol.upper(),as_of)
                card=confirmed_card(events,args.symbol,as_of=as_of,
                    latest_completed_m15=atr.get('data_through'),feed_connected=False)
                card['atr_reference']=atr
                render=format_confirmed_regime
            print(json.dumps(card,ensure_ascii=False,indent=2,allow_nan=False) if args.format=='json'
                  else render(card))
            return 0
        symbol, as_of, sessions, execution, calendar = _load_snapshot(args.input)
        if args.as_of is not None and stamp(args.as_of)!=as_of:
            raise ValueError('SNAPSHOT_AS_OF_MISMATCH')
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
        if not args.legacy_diagnostics:
            paths,_=load_paths(as_of=as_of)
            atr=dict(atr14_pct_close=card['metrics']['volatility']['atr14_pct_close'],
                     data_through=card.get('last_completed_session'))
            card['rolling_raw']=instrument_card(paths,symbol,as_of,profile=raw_profile,atr=atr)
        output = (json.dumps(card, ensure_ascii=False, indent=2, allow_nan=False)
                  if args.format == "json" else format_text(card, details=args.details))
        print(output)
        return 0
    except (KeyError, ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"V20_MARKET_CARD_INPUT_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
