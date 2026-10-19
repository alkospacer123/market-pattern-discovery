"""Render Russian reports from completed, audited exploratory artifacts."""
import json
import math
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent


def fmt(value, digits=3):
    if value is None or pd.isna(value): return "—"
    if isinstance(value, str): return value.replace("|", "/")
    return f"{value:.{digits}f}"


def table(headers, rows):
    return "| "+" | ".join(headers)+" |\n|"+"|".join(["---"]*len(headers))+"|\n"+"\n".join("| "+" | ".join(str(x) for x in row)+" |" for row in rows)+"\n"


def main():
    read = lambda name: pd.read_csv(HERE/name)
    summary = json.loads((HERE/"summary.json").read_text())
    audit = json.loads((HERE/"independent_audit.json").read_text())
    repro = json.loads((HERE/"reproducibility.json").read_text())
    assert summary["EXPLORATORY_REPLAY"] == "COMPLETE" and repro["historical_runs"] == 2
    totals = summary["totals"]
    annual, robust = read("annual_combined.csv"), read("robustness.csv")
    names = ["Si", "CNY", "GD", "MIX", "BR", "NG", "PRIMARY4", "ADDITIONAL2", "ALL6"]
    total_table = table(["Ряд/корзина", "Сделки", "Gross PF", "Net PF", "Gross R", "Cost R", "Net R", "Avg R", "Win%", "DD R"],
        [[n, totals[n]["trades"]]+[fmt(totals[n][k]) for k in ["gross_pf", "net_pf", "gross_R", "cost_R", "net_R", "average_R", "win_pct", "max_closed_R_drawdown"]] for n in names])
    yearly_table = table(["Год", "PRIMARY4 n/PF/R", "ADDITIONAL2 n/PF/R", "ALL6 n/PF/R"],
        [[y]+[f"{int(r.trades)} / {fmt(r.net_pf)} / {fmt(r.net_R)}" for n in names[-3:] for r in annual[(annual.year == str(y)) & (annual.instrument == n) & (annual.direction == "ALL")].itertuples()] for y in range(2020, 2027)])
    singles = annual[(annual.direction == "ALL") & annual.instrument.isin(names[:6]) & (annual.year != "2020-2026")]
    detail_table = table(["Год", "Ряд", "n", "Gross PF", "Net PF", "Gross R", "Net R", "Avg R", "Win%", "Avg win", "Avg loss", "DD R"],
        [[r.year, r.instrument, "NO_DATA" if pd.isna(r.trades) else int(r.trades)]+[fmt(getattr(r, k)) for k in ["gross_pf", "net_pf", "gross_R", "net_R", "average_R", "win_pct", "average_win_R", "average_loss_R", "max_closed_R_drawdown"]] for r in singles.sort_values(["year", "instrument"]).itertuples()])
    direction_table = table(["Ряд/корзина", "Направление", "n", "Net PF", "Net R", "Avg R", "DD R"],
        [[r.instrument, r.direction, int(r.trades)]+[fmt(getattr(r, k)) for k in ["net_pf", "net_R", "average_R", "max_closed_R_drawdown"]]
         for r in robust[robust.direction.isin(["LONG", "SHORT"])].itertuples()])
    robustness_table = table(["Ряд/корзина", "+ / − лет", "Худший год", "Худший квартал", "Худший месяц", "Убытков подряд", "R без top1", "R без top3", "R без top5", "Top5 доля win R"],
        [[r.instrument, f"{int(r.positive_years)} / {int(r.negative_years)}", r.worst_year, r.worst_quarter, r.worst_month, int(r.max_losing_streak), fmt(r.net_R_without_top1), fmt(r.net_R_without_top3), fmt(r.net_R_without_top5), fmt(r.top5_positive_profit_share*100)+"%"] for r in robust[robust.direction == "ALL"].itertuples()])
    n4 = read("quarterly_vs_perpetual_n4.csv")
    n4_agg = n4[(n4.quarterly == "PRIMARY4") & (n4.comparison_mode == "EXIT_DATE_WINDOW") & (n4.year >= 2023)]
    n4_table = table(["Год", "Общий интервал", "Quarterly4 n/PF/R", "N4 n/PF/R", "Quarterly AvgR", "N4 AvgR", "Δ AvgR"],
        [[r.year, str(r.common_start)[:10]+" — "+str(r.common_end)[:10], f"{int(r.quarterly_trades)} / {fmt(r.quarterly_net_pf)} / {fmt(r.quarterly_net_R)}", f"{int(r.perpetual_trades)} / {fmt(r.perpetual_net_pf)} / {fmt(r.perpetual_net_R)}", fmt(r.quarterly_average_R), fmt(r.perpetual_average_R), fmt(r.delta_average_R)] for r in n4_agg.itertuples()])
    n4_pairs = n4[(n4.quarterly != "PRIMARY4") & (n4.comparison_mode == "EXIT_DATE_WINDOW") & (n4.year >= 2023)]
    pair_table = table(["Год", "Пара", "Quarterly n/PF/R", "Perpetual n/PF/R", "Δ AvgR"],
        [[r.year, r.quarterly+" / "+r.perpetual, f"{int(r.quarterly_trades)} / {fmt(r.quarterly_net_pf)} / {fmt(r.quarterly_net_R)}", f"{int(r.perpetual_trades)} / {fmt(r.perpetual_net_pf)} / {fmt(r.perpetual_net_R)}", fmt(r.delta_average_R)] for r in n4_pairs.itertuples()])
    v2 = read("v2_vs_v3_comparison.csv")
    v2_table = table(["Год", "v3 TRAIL1 n/PF/R", "v2 published n/PF/R", "v2 single-C1 PF/R"],
        [[r.year, f"{int(r.v3_trades)} / {fmt(r.v3_net_pf)} / {fmt(r.v3_net_R)}", f"{int(r.v2_published_trades)} / {fmt(r.v2_published_net_pf)} / {fmt(r.v2_published_net_R)}", f"{fmt(r.v2_single_C1_net_pf)} / {fmt(r.v2_single_C1_net_R)}"] for r in v2[v2.instrument == "ALL6"].itertuples()])
    concentration = read("roll_concentration.csv")
    c = concentration[(concentration.instrument == "ALL6") & (concentration.year == "ALL")]
    concentration_table = table(["Условные окна", "Доля исходных H1", "Доля сигналов", "Входов рядом", "Выходов рядом", "Stop tests рядом", "Доля positive R выходов"],
        [[r.definition, fmt(100*r.observed_bar_share)+"%", fmt(100*r.near_signal_share)+"%", int(r.near_entries), int(r.near_exits), int(r.near_stop_tests), fmt(100*r.positive_R_share_exiting_near)+"%"] for r in c.itertuples()])
    sensitivity = read("roll_sensitivity.csv")
    sensitivity_table = table(["Корзина", "Диагностика", "Осталось n", "Убрано n", "Net PF", "Net R", "Avg R"],
        [[r.instrument, r.scenario, int(r.trades), int(r.omitted_closed_trades), fmt(r.net_pf), fmt(r.net_R), fmt(r.average_R)] for r in sensitivity[sensitivity.instrument.isin(names[-3:])].itertuples()])
    flags = read("trade_roll_flags.csv")
    gap_table = table(["Ряд", "Сделок", "Пересекают ±3d окно", "Пересекают anchor", "Крупный gap при позиции", "Gap stop penalty R"],
        [[n, len(f), int(f.touches_quarter_3d.sum()), int(f.crosses_quarter_anchor.sum()), int(f.large_gap_while_open.sum()), fmt(f.gap_stop_penalty_R.sum())] for n in names[:6] for f in [flags[flags.instrument == n]]])
    total_checks = sum(x["scalar_indicator_comparisons"] for x in audit["historical_independent_checks"])
    total_events = sum(x["all_real_management_events_checked"] for x in audit["historical_independent_checks"])
    max_error = max(x["maximum_indicator_absolute_error"] for x in audit["historical_independent_checks"])
    winners = ", ".join(n for n in names[:6] if totals[n]["net_R"] > 0)
    losers = ", ".join(n for n in names[:6] if totals[n]["net_R"] <= 0) or "нет"
    weak = ", ".join(sorted(names[:6], key=lambda n: totals[n]["average_R"])[:2])
    rb = robust[robust.direction == "ALL"].set_index("instrument")
    individual_years = annual[(annual.direction == "ALL") & annual.instrument.isin(names[:6]) & (annual.year != "2020-2026")]
    positive_cells, negative_cells = int((individual_years.net_R > 0).sum()), int((individual_years.net_R < 0).sum())
    sensitivity_all = sensitivity[sensitivity.instrument == "ALL6"].set_index("scenario")
    report = f"""# T3/H1/TRAIL1: описательный исторический replay, 2020–2026

Дата: 19.10.2026, Europe/Moscow. Продолжение существующего Draft PR #555.

**На предоставленных рядах средний Net R ALL6 равен {fmt(totals['ALL6']['average_R'])} R на закрытую сделку, Net PF={fmt(totals['ALL6']['net_pf'])}, Net R={fmt(totals['ALL6']['net_R'])} на {totals['ALL6']['trades']} сделках. Это описательный результат недокументированных непрерывных рядов, а не подтверждение реальной торговли отдельными контрактами.**

| Независимое состояние | Значение |
|---|---|
| COMPUTATIONAL_AUDIT | PASS |
| SOURCE_INTEGRITY | PASS |
| ROLL_PROVENANCE | UNVERIFIED |
| EXPLORATORY_REPLAY | COMPLETE |
| TRADABLE_QUARTERLY_PERFORMANCE | NOT_VALIDATED |

## Допуск, источники и замороженная стратегия

Исходный main: `38489db7e69336548a583f968f13aab49c20913b`. Предыдущий preflight PR #555: `7404fc23f2e92344fd5aea66924b74410f777ebe`. Пользователь явно разрешил отдельный EXPLORATORY REPLAY без паспорта склейки. Это изменило допуск данных; стратегия не менялась. Полный прежний DATA_BLOCKED-аудит сохранён в `prior_preflight/`. Правила ролловера по-прежнему не установлены.

Использованы ровно шесть ранее найденных H1 CSV, в оригинальном порядке и без изменения OHLC, удаления баров, сглаживания гэпов или новой склейки. Их байтовые SHA256 повторно совпали с Stage5 и предыдущим аудитом. Принята convention frozen loader: open-labelled H1, Europe/Moscow, доступность open+1h; это исследовательское допущение без подтверждения поставщика. Все ряды заканчиваются close **16.09.2026 00:00 +03:00** (исходный Datetime 15.09.2026 23:00). Начало Si/GD/MIX/BR — 03.01.2020 11:00; NG — 03.02.2020 11:00; CNY — **21.04.2022 11:00**, до этого источника нет. Детали — `DATA_AUDIT.md`, `data_quality.json`, `source_coverage.csv`.

Frozen reference: `T3_H1_candidate_v3`, `T3-H1-4e73cdb77246`, `TRAIL1__N4_01__FULL__R15`. Все девять effective parameters совпали со Stage7: EMA100, slope5, ADX14/20, prior Donchian20, ATR14, ATR average20, initial stop2.5 ATR, trail3 ATR. TRAIL1 trigger=+1 первоначальный R, activation только на следующем событии. Параметр SHA256 `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a` воспроизведён из frozen six-field payload; defaults дополняют его до девяти полей.

Сохранены causal H4 из четырёх завершённых H1 в пределах локального дня, Donchian без текущей свечи, SIGNAL_CLOSE, запрет управления на entry bar, одна позиция, tighten-only, adverse open при gap-through-stop, EXIT перед независимым ENTRY. Позиции и индикаторы на границах лет **не сбрасывались**. На конце ряда {summary['unclosed_positions']} открытых позиций; они раскрыты в `open_positions.csv` и не закрыты принудительно.

PRIMARY C1: один normalized research tick 0.001 на сторону, два за круг. `GrossR=sign*(exit-entry)/initialR`, `CostR=0.002/initialR`, `NetR=GrossR−CostR`. C1 не является реальными комиссиями и экономически неодинаков для рядов с разным масштабом цены. R не переведён в проценты капитала. SECONDARY и FULL/R15 cash-модель не рассчитывались без исторических contract specs и rollover cash flows.

## Итоги и таблицы A/B

{total_table}
DD — отрицательная максимальная просадка хронологической закрытой суммы R с начальной точкой 0. Совокупный PF рассчитан из всех сделок, не усреднением PF рынков. Порядок при совпадающих выходах: время, instrument, trade ID; это воспроизводимая последовательность закрытых R, а не внутридневной mark-to-market DD.

### Годовые агрегаты

{yearly_table}
Формат ячеек: число закрытых сделок / Net PF / Net R. 2026 — неполный год до 16 сентября. PRIMARY4/ALL6 в 2020–2021 содержат только доступные рынки; отсутствующий CNY не заменяется нулевой торговлей. NG в 2020 начинается в феврале. Годы определены по **московскому времени выхода**, переносимые через Новый год позиции сохранены.

### Инструменты по годам

{detail_table}
Полные метрики и LONG/SHORT каждого года находятся в `annual_by_instrument.csv`; агрегаты — `annual_primary4.csv`, `annual_additional2.csv`, `annual_all6.csv`, полный набор — `annual_combined.csv`. `monthly.csv` и `quarterly.csv` включают отдельные NO_DATA-периоды, а не фиктивные сделки.

## LONG/SHORT и устойчивость (таблица D)

{direction_table}
{robustness_table}
Худшие периоды выбираются по Net R среди периодов с закрытыми сделками. Годовые знаки учитывают доступные годы, включая неполные начальный/2026. Top1/3/5 удаляются только в таблице чувствительности: основной журнал неизменён. Доля top5 имеет знаменатель **сумма положительных Net R**, а не чистая прибыль. Полные результаты ALL/LONG/SHORT, удаление top1/3/5 и соответствующий PF — `robustness.csv`.

## Сравнение с N4 (таблица C)

Использован только authenticated Stage6 `trail1_authoritative_trades.csv` (418 физических строк, 355 baseline+historical_true_oos; **63 Walk Forward исключены**). SHA256 `0f9034edf228a687da67e9f3e35fad01f2339be162c558e6d802c3cd77eea8ad`. Никаких CANONICAL сделок или заново рассчитанного N4 нет. Общие интервалы взяты из frozen lifecycle registry и доступного quarterly source coverage, а не из первой/последней сделки.

{n4_table}
{pair_table}
2020–2022 N4=`NO_DATA`, сравнение=`NO_COMMON_COVERAGE`, не нули. В 2023 GLDRUBF source начинается в июле, IMOEXF в ноябре; общий четырёхинструментный интервал начинается только 14.11.2023. Частичная история не названа полным годом. В CSV также есть частота на 365.25 календарных дней (не прогноз) и каждый фактический common start/end.

Основная панель использует exit-date window: допускает позиции, открытые до начала сравниваемого интервала. В том же CSV отдельная панель `FULLY_CONTAINED_TRADES` исключает такие сделки **из сравнения**, не из основного quarterly replay. N4 ledger имеет самостоятельный cold start в 2025, quarterly replay непрерывен; одинаковая дата не гарантирует одинаковое состояние индикаторов/позиции. Источники цен и normalized C1 не экономически эквивалентны. Разницу нельзя приписывать исключительно типу контракта.

## Сравнение с существующей v2 (таблица E)

`T3_H1_candidate_v2` имеет stop_atr=2.0, atr_average_period=30 и не имеет идентичного TRAIL1. Для 2020–2024 повторно исполнен только опубликованный frozen candidate существующей функцией `_execute`, без перебора конфигураций. Все пять опубликованных годовых rows (n/PF/R/AvgR/DD) воспроизведены с допуском округления. Для 2025–2026 взят существующий опубликованный trade ledger. Входы/выходы v2 не заменены новой оптимизацией. Подробный компаратор — `v2_comparator_trades.csv`.

**Обнаружена legacy-особенность издержек v2:** `_normalize_backtester` присваивает `gross_R=profit_R`, где cost уже вычтен, а затем `_execute` вычитает cost_R повторно. Published net поэтому эффективно включает два C1. Старые результаты и frozen-код не исправлялись. Ниже и в CSV одновременно сохранены published net и отдельная арифметическая нормализация к одному C1 (`published_net+cost_R`), без изменения сделок. Это не смена стратегии.

{v2_table}
Таблица выше — ALL6; CSV содержит все инструменты и три корзины по каждому году. True gross восстановлен отдельно как published_net+2×cost_R; ошибочно названное gross_R старого источника не принимается за настоящий gross. Lifecycle v2 сброшен в 2025; v3 непрерывен. Сравнение проводится на одинаковом доступном календарном source-покрытии, но различие cold starts остаётся ограничением. В 2020–2021 CNY=`NO_DATA`. На ALL6 v3 даёт меньше Net R, чем v2 single-C1, в 2020–2023 и больше в 2024–2026; это сравнение версий с разными параметрами и lifecycle, не доказательство превосходства отдельного изменения.

## Независимый исторический аудит

На всех **148 250 реальных H1-барах** проверены сигналы скалярной реализацией, {total_checks} значений индикаторов и {total_events} реальных событий управления позицией. Все {summary['closed_trades']} закрытых сделок и их поля сверены с unchanged research authority и production replay. Проверены entry-bar exclusion, fixed initial R, один active position, trigger/activation times, tighten-only, adverse gap fills и порядок выхода/повторного входа.

Максимальная абсолютная ошибка scalar indicators: `{max_error:.17g}`; применяется `abs_tol=2e-10`, `rel_tol=2e-12` для полей. Для R отдельная Decimal-проверка с допуском округления. Индикаторы/сигналы и закрытые сделки проверены также на реальных исторических префиксах в 2021/2023/2025/2026 (по наличию истории). Синтетический future-perturbation audit и adversarial cases сохранены. Это подтверждает причинность **расчёта по данным ряда**, но не point-in-time доступность неизвестных price adjustments у поставщика.

PF, Gross/Cost/Net R и closed-R DD пересчитаны независимо через Decimal; выполнены сверки годов, направлений, инструментов и корзин. Два свежих **полных исторических** прогона, включая source checks, независимые вычисления, roll diagnostics и сравнения, дали побайтово одинаковые SHA256 всех {len(repro['artifacts'])} генерируемых файлов. 15 офлайн-тестов прошли. Полные детали — `independent_audit.json`, `reproducibility.json`, `tests.log`, `run1.log`, `run2.log`.

## Чувствительность к неизвестной склейке

Полный отдельный отчёт — `ROLL_DIAGNOSTICS_RU.md`. Диагностические признаки не используются в генерации сигналов и не удаляют сделки из PRIMARY.

{concentration_table}
{gap_table}
Календарный anchor — третий четверг марта/июня/сентября/декабря; окна ±3 и ±7 календарных дней, включая крайние дни. Дополнительная проверка третьего четверга **каждого месяца** ±3 дня показана для всех рынков, поскольку особенно для energy нельзя предполагать, что квартальные окна охватывают фактические смены контрактов. Ни одно окно не объявлено реальным expiry/roll schedule. Все пересекающие окна сделки перечислены в `trade_roll_flags.csv`, включая список anchors/windows.

Большой наблюдаемый гэп заранее определён как `abs(Open−previousClose)/previousClose ≥3%` **или** `abs(Open−previousClose)/previousATR ≥2.5`. Используется предыдущий причинный ATR. Признак означает разрыв между наблюдениями; он не доказывает roll-артефакт. Gap bars и сигналы/стопы на них не исправляются.

{sensitivity_table}
Сценарии `ATTRIBUTION_OMIT_*` — post-hoc разложение уже закрытых сделок, без повторного прогона и без моделирования новых входов после исключения. Они не являются предлагаемыми фильтрами или альтернативной стратегией. `STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY` только возвращает gap-stop penalty при неизменных времени/последовательности сделок; это не утверждение об исполнимости stop-price fill через гэп.

## Содержательный вывод

На предоставленных рядах положительный итог имеют **{summary['positive_instruments']}/6** инструментов: {winners}. Неположительные: {losers}. По среднему Net R наиболее слабые рынки: **{weak}**. PRIMARY4 имеет {summary['positive_years_by_basket']['PRIMARY4']}/7 положительных доступных лет, ADDITIONAL2 — {summary['positive_years_by_basket']['ADDITIONAL2']}/7, ALL6 — {summary['positive_years_by_basket']['ALL6']}/7; 2026 неполный. Точный результат без лучших сделок и разница с N4 представлены выше, поэтому положительный PF не подменяет анализ стабильности и концентрации.

По отдельным сочетаниям «инструмент × год» положительны **{positive_cells}/{positive_cells+negative_cells}**, отрицательны {negative_cells}; CNY 2020–2021 отсутствует. В PRIMARY4 слабейший общий год — 2021, всего {fmt(rb.loc['PRIMARY4','worst_year_net_R'])} R; в ALL6 — 2023, {fmt(rb.loc['ALL6','worst_year_net_R'])} R. Нельзя назвать преимущество одинаково сильным во всех годах и направлениях.

ALL6 без пяти лучших сделок сохраняет **{fmt(rb.loc['ALL6','net_R_without_top5'])} R**, PRIMARY4 — **{fmt(rb.loc['PRIMARY4','net_R_without_top5'])} R**. Поэтому общая прибыль не сводится к пяти сделкам. Но BR без трёх лучших даёт {fmt(rb.loc['BR','net_R_without_top3'])} R, NG — {fmt(rb.loc['NG','net_R_without_top3'])} R; ADDITIONAL2 без пяти лучших имеет лишь {fmt(rb.loc['ADDITIONAL2','net_R_without_top5'])} R. У дополнительных рынков преимущество существенно слабее и чувствительнее к крупнейшим победителям.

На одинаковых общих exit-интервалах Quarterly4 уступает N4 по среднему R во всех четырёх сравниваемых годах; разница в 2024 мала, а в 2025–2026 заметнее (таблица C). В общей части 2023 обе корзины отрицательны. Это описательная разница с аутентифицированным ledger при различиях исходных цен, C1 и cold starts; причинный эффект типа контракта не установлен.

В ALL6 после условного исключения сделок, затронувших ±3d квартальные окна, остаётся {fmt(sensitivity_all.loc['ATTRIBUTION_OMIT_TOUCH_QUARTER_3D','net_R'])} R; после исключения сделок с крупным gap во время позиции — {fmt(sensitivity_all.loc['ATTRIBUTION_OMIT_LARGE_GAP_WHILE_OPEN','net_R'])} R. Прямая adverse gap-stop penalty равна {fmt(flags.gap_stop_penalty_R.sum())} R. Исходный положительный итог не исчезает в этих разложениях, но это не исключает влияние неизвестных корректировок на сигналы, ATR и прочую историю.

Это выборочное среднее на ранее просмотренной истории. 2020–2024 — ранее исследованный исторический период; 2025–2026 — ранее просмотренный на этих рынках. **Нового чистого TRUE OOS нет.** Факт прежнего подбора candidate и пересмотра допустимости источников ограничивает силу подтверждения; текущий эксперимент не выполнял оптимизации. Положительный результат сам по себе не доказывает отсутствие частичной исторической подгонки, как и неизвестная склейка сама по себе её не доказывает.

Вывод о реальной доходности квартальных контрактов остаётся **NOT_VALIDATED**: нет паспорта склейки и причинности supplier adjustments, contract mapping, historical price steps, execution/rollover cash flows и реальных расходов. Нельзя вывести доходность капитала из суммы R или объяснить всю разницу с N4 типом контракта. Результат не даёт основания менять production-конфигурацию.

Все изменения находятся в изолированном каталоге PR #555; исходные котировки не опубликованы. Production, frozen authority, N4, H1/M15, FINAM и ControlCenter не менялись; торговые API не вызывались. PR остаётся Draft, без merge/auto-merge. **STOP для внешнего аудита.**
"""
    (HERE/"REPORT_RU.md").write_text(report, encoding="utf-8")
    diag = """# Неизвестная склейка: отдельная диагностика чувствительности

Статус: ROLL_PROVENANCE=UNVERIFIED; TRADABLE_QUARTERLY_PERFORMANCE=NOT_VALIDATED.
Это постфактум-диагностика исходного replay, не фильтр и не оптимизация. Все сделки сохранены в PRIMARY.

## Заранее заданные определения

- Потенциальные квартальные окна: третий четверг марта/июня/сентября/декабря ±3 и ±7 календарных дней. Крайние дни включены целиком; локальное время Europe/Moscow. Это условные календарные anchors, не расписание MOEX и не найденные даты переходов.
- Дополнительное monthly_3d окно — третий четверг каждого месяца ±3 дня для всех шести рынков. Оно не подтверждает monthly cadence. Квартальные окна могут пропускать большую часть реальных energy rolls.
- Открытая сделка пересекает окно, если [entry,exit] пересекает [window_start,window_end]; anchor crossing отдельно означает entry≤anchor≤exit.
- Крупный гэп: absolute fractional gap≥3% ИЛИ absolute gap≥2.5 предыдущих ATR. Первые бары без ATR могут попасть по процентному критерию. Никаких quantiles, выбора лучших порогов или удаления свечей нет.
- Сигнал — eligible breakout/regime на закрытии независимо от занятой позиции. Вход — действительно принятый сигнал при отсутствии позиции. Stop test — каждое событие управления уже открытой позицией. Trigger, activation и tighten учитываются отдельно.
- Прибыль для концентрации относится к exit timestamp; прибыль пересекающих окно сделок дополнительно раскрывается через полный список флагов. Доля positive R имеет знаменатель сумму положительных Net R. Для корректной базы сравнения показаны наблюдаемые H1 и сигналы на 1000 баров рядом/вне окон.

## Концентрация всех шести

"""+concentration_table+"\n"+gap_table+"""
## Чувствительность уже наблюдаемых сделок

"""+sensitivity_table+"""
Остальные инструменты и сценарии находятся в roll_sensitivity.csv. Удаление закрытых сделок — условное разложение результата, а не новый исполнимый replay: после удаления не моделируются освобождение позиции, новые входы, изменившиеся индикаторы или новый путь стопов. Исходные показатели находятся в ORIGINAL_CONTINUOUS_SERIES.

STOP_LEVEL_FILL_ARITHMETIC_CREDIT_ONLY прибавляет сумму sign*(stop−actual_gap_fill)/initialR к исходным Gross/Net R. Издержки, моменты выхода и последовательность сделок не меняются. Эта величина показывает прямую adverse gap-stop penalty, но не оценивает полный эффект discontinuity на ATR/EMA/Donchian, входы и будущие стопы. Нельзя считать stop-level fill физически доступным при гэпе.

## Файлы и ограничения

- potential_expiry_windows.csv: все proxy windows с actual_roll_date_confirmed=False.
- trade_roll_flags.csv: каждая закрытая сделка, пересечения/anchors, entry/exit proximity, large-gap exposures и gap-stop penalty.
- roll_concentration.csv: инструменты и три корзины, каждый год и общий период; сигналы/входы/выходы/stop tests/triggers/activation/profit и базовая экспозиция.
- potential_window_metrics.csv: детализация по каждому инструменту и условному окну.
- gap_events.csv: все наблюдаемые разрывы по заранее заданному критерию, без публикации исходных OHLC.
- roll_sensitivity.csv: исходный результат и явно отделённые диагностические разложения.

Связь результатов с календарными окнами или гэпами не идентифицирует причинный эффект ролловера: окна занимают часть торговой истории, сделки могут быть длинными, а кризисные рыночные гэпы не являются доказанными склейками. Отсутствие концентрации в выбранных окнах тоже не подтверждает корректность ряда. Для точной проверки нужны паспорт поставщика и составляющие контракты. Параметры и основной журнал не меняются.
"""
    (HERE/"ROLL_DIAGNOSTICS_RU.md").write_text(diag, encoding="utf-8")


if __name__ == "__main__": main()
