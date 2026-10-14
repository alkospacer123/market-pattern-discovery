"""Readable tables for every fixed replay; descriptive interpretation only."""
import json
from pathlib import Path
import pandas as pd


def table(f,cols):
    def cell(x):
        if pd.isna(x):return '—'
        if isinstance(x,float):return f'{x:.4f}'
        return str(x)
    return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']+[
        '| '+' | '.join(cell(r[c]) for c in cols)+' |' for r in f.to_dict('records')])


def render(output):
    def read(name):return pd.read_csv(output/name)
    overall=read('overall_report.csv');years=read('yearly_report.csv');monthly=read('monthly_report.csv')
    risk=read('risk_distribution.csv');change=read('winner_occupancy_changes.csv');valid=read('entry_validity.csv')
    objective=json.loads((output/'OBJECTIVE_ASSESSMENT.json').read_text())
    manifest=json.loads((output/'SOURCE_MANIFEST.json').read_text())
    hits=[r for r in objective['rows'] if r['rule']!='CONTROL' and r['numerical_goal_actual_PF_ge_2']]
    lines=['# T3/M15 Initial Stop v1 — полный 2023–2024',
        '', '**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**. Все 2023–2024 development-exposed.', '',
        '## Вывод по заданной цели', '',
        f'Численно достигли pooled Gross PF ≥2,0: {len(hits)} из 6 самостоятельных вариантов I1/I2/I3 на двух trailing. '+
        ('Цель достигнута только как валовая исследовательская метрика.' if hits else 'Цель полного периода не достигнута ни одним вариантом.'), '',
        'Экономическое преимущество и исполнимость не доказаны; автоматического PASS и выбора победителя нет. '+
        'Узкие Stop порядка одного–двух тиков нельзя считать доказательством экономического преимущества. '+
        'Снижение знаменателя R влияет на вес сделок в PF: ниже отдельно приведена нормализация на исходные 2×ATR.', '',
        '## Полный период, четыре инструмента', '']
    for norm,description in [('ACTUAL_INITIAL_RISK','Основная Gross R: прибыль в цене / фактический фиксированный первоначальный риск.'),
        ('REFERENCE_2ATR','Диагностика: та же прибыль в цене / (2×ATR при входе). Это отдельная метрика, не подмена основной Gross R.')]:
        f=overall.loc[overall.scope.eq('ALL_FOUR')&overall.normalization.eq(norm)]
        lines.extend([f'### {norm}', '',description,'',table(f,['version','rule','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R',
            'max_drawdown_closed_R','max_consecutive_losses','positive_months','negative_months','zero_months','worst_month','worst_month_R']), ''])
    lines.extend(['## По годам, четыре инструмента', '',
        'CLOSED отнесены к году исторической метки exit-bar Close в МСК. OPEN — фактические позиции на последней доступной свече перед границей года, без ликвидации. '+
        'Количество OPEN в 2023 не означает терминальную позицию в полном replay.', '',
        table(years.loc[years.scope.eq('ALL_FOUR')],['version','rule','normalization','year','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R',
            'max_drawdown_closed_R','positive_months','negative_months','zero_months','worst_month','worst_month_R']), '',
        '## Концентрация и ноябрь 2024', '',table(overall.loc[overall.scope.eq('ALL_FOUR')],['version','rule','normalization','top5_share_positive_R','top10_share_positive_R','gross_PF_without_top5','gross_PF_without_top10','gross_R_without_top10']), '',
        table(read('november_dependence.csv').loc[lambda f:f.scope.eq('ALL_FOUR')],['version','rule','normalization','year','november_closed','november_R','full_PF','ex_november_PF','ex_november_R','ex_november_drawdown_R']), '',
        'Удаление ноября и top5/top10 — только описательная чувствительность; сделки не исключаются из основной оценки. '+
        'Drawdown — сумма CLOSED R в порядке exit_time/instrument/trade_id; это не денежная или mark-to-market просадка.', '',
        '## Первоначальный риск и пропуски', '',
        'Распределения включают все принятые входы, включая терминальные OPEN. Тики биржевые: USD 0,01; CNY 0,01 до 27.09.2023 19:00 МСК и 0,001 после; GLD 0,1; IMOEX 0,5. '+
        'Источники — сохранённая спецификация IntradayLab, раздел 2 и датированные ссылки MOEX. Полные исторические редакции не аттестованы. '+
        'Исходные искусственные единицы C1 0,001 USD/CNY не используются как биржевые тики. '+
        'Уровни Stop не округлены; геометрия тиков — диагностика, не гарантия допустимости заявки.', '',
        table(risk.loc[risk.entry_year.eq('ALL')&risk.direction.eq('ALL')],['version','rule','instrument','accepted_entries_including_terminal_open',
            'risk_price_min','risk_price_median','risk_ATR_median','risk_exchange_ticks_min','risk_exchange_ticks_median','risk_le_1_tick','risk_le_2_ticks','risk_le_2_ticks_share']), '',
        table(valid,['version','rule','instrument','signal_opportunities','accepted','busy','invalid_candidate_count','invalid_unoccupied_skipped','nonpositive_risk','nonfinite_risk','fallbacks']), '',
        f'Всего записей чрезвычайно узких принятых Stop ≤2 тиков: {len(read("narrow_stop_entries.csv"))}; гэпов с потерей >1R: {len(read("gap_losses_gt_1R.csv"))}. '+
        'Полные строки сохранены в отдельных журналах; никакого нового фильтра по ним нет.', '',
        '## Исходные крупные победители и занятость', '',
        table(change.loc[change.scope.eq('ALL_FOUR')&change.control_exit_year.eq('ALL')],['version','rule','control_large_winners_ge_2R',
            'large_winner_entry_busy','large_winner_entry_invalid','large_winner_price_pnl_preserved','large_winner_reference_R_preserved','large_winner_actual_R_preserved',
            'large_winners_turned_losses','missed_busy_entries','new_closed_entries','new_closed_losses']), '',
        'Сохранение победителя показано в цене, R на исходных 2×ATR и R на новом риске отдельно. Рост actual R при сокращении цены выигрыша не считается сохранением экономического результата. '+
        'trade_lineage.csv содержит каждый исходный CLOSED, причину пропуска и идентификатор занятой позиции; new_entries.csv содержит новые CLOSED.', '',
        '## Данные и сопоставимость', '',
        f'Удалённый main проверен: `{manifest["base_main"]}` (#497); данные `{manifest["data_commit"]}`. Freeze commit `{manifest["freeze_commit"]}`.', '',
        table(pd.DataFrame(manifest['sources']),['instrument','used_candles','first_open','last_open','first_close','last_close']), '',
        'Использованы все исходные доступные M15 2023–2024 с реальными поздними стартами. OHLC 2025+ не парсятся: оба timestamp-first парсера останавливаются перед ними; '+
        'полнофайловый SHA — только непрозрачная проверка байтов. Raw OHLC не копируются в research-репозиторий.', '',
        'Исторический вход по Close завершённой сигнальной свечи — **непроверенное предположение об исполнении**, сохранённое для сопоставимости. '+
        'H1 использует исходные дневные порядковые блоки по четыре последовательных M15, только завершённые. EMA/ATR/ADX/Donchian пересекают дни, как в замороженном T3. '+
        'Stop проверяется первым; неблагоприятный gap исполняется по Open; trailing после пережитой свечи действует со следующей. '+
        'Одинаковая хронология LONG/SHORT, фиксированный первоначальный риск, повторные входы после выхода и перенос через день/год сохранены.', '',
        'CONTROL проходит совпадение всех общих полей #490/#495: 1 442 CLOSED + 2 терминальных OPEN, численный допуск 1e−8. '+
        'Исторические C1/net и искусственные C1 tick units исключены из сопоставления и расчётов.', '',
        '## Все календарные месяцы', '',
        'Для каждого инструмента показаны все 24 месяца. До старта — NO_COVERAGE, нулевой CLOSED R; такие месяцы не являются положительными. '+
        'В overall_report.csv дополнительно указан знаменатель и положительная доля только среди месяцев покрытия. '+
        'Закрытая месячная сумма может не отражать накопленный PnL удерживаемой позиции.', ''])
    for norm in ('ACTUAL_INITIAL_RISK','REFERENCE_2ATR'):
        for scope in ('ALL_FOUR','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
            lines.extend([f'### {scope} / {norm}', '',table(monthly.loc[monthly.scope.eq(scope)&monthly.normalization.eq(norm)],
                ['version','rule','month','coverage','closed_trades','gross_PF','gross_R']), ''])
    lines.extend(['## Каждый инструмент и LONG/SHORT', '',table(overall.loc[overall.scope.ne('ALL_FOUR')],
        ['version','rule','scope','normalization','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','max_drawdown_closed_R','positive_months','negative_months','zero_months']), '',
        table(read('direction_report.csv'),['version','rule','scope','normalization','year','direction','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R']), '',
        '## Проверки и остановка', '',
        'Полные trade/entry/Stop журналы, риск, крупные победители, годовые OPEN и отрицательные результаты сохранены. '+
        'AUDIT_RESULTS.json содержит отдельный stdlib replay и проверку всех полей журналов и диагностики; независимость алгоритмическая, автор тот же. '+
        'Внешний аудит остаётся PENDING. REPEATABILITY.json подтверждает два полных побайтных повтора, ARTIFACT_SHA256.json — состав и SHA артефактов. '+
        'Optimization, Robustness, Walk Forward, TRUE OOS и LIVE не выполнялись. Один Draft PR, без Merge и Auto-Merge; STOP для внешнего аудита и решения пользователя.', ''])
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    render(Path(__file__).resolve().parent/'results')
