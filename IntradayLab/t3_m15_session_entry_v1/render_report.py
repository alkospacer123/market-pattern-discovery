"""Readable complete economics; no parameter selection or extra experiments."""
import json
from pathlib import Path
import pandas as pd

def table(f,cols):
    def cell(x):
        if pd.isna(x):return '—'
        if isinstance(x,float):return f'{x:.4f}'
        return str(x)
    return '\n'.join(['| '+' | '.join(cols)+' |','| '+' | '.join(['---']*len(cols))+' |']+['| '+' | '.join(cell(r[c]) for c in cols)+' |' for r in f.to_dict('records')])

def render(output):
    read=lambda name:pd.read_csv(output/name)
    overall=read('overall_report.csv');years=read('yearly_report.csv');monthly=read('monthly_report.csv')
    change=read('winner_comparison.csv');holding=read('holding_frequency.csv');funnel=read('signal_funnel.csv')
    manifest=json.loads((output/'SOURCE_MANIFEST.json').read_text())
    all4=overall.loc[overall.scope.eq('ALL_FOUR')];variants=all4.loc[all4.rule.ne('CONTROL')]
    hits=int(variants.gross_PF.ge(2).sum());improved=[]
    for r in variants.to_dict('records'):
        c=all4.loc[all4.version.eq(r['version'])&all4.rule.eq('CONTROL')].iloc[0]
        if r['positive_months']>c.positive_months:improved.append(f"{r['version']}/{r['rule']}")
    lines=['# T3/M15 Session Entry v1 — 2023–2024','',
        '**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY**. 2023–2024 development-exposed; это не новый независимый Walk Forward.','',
        f'Цель полного pooled Gross PF ≥2,0: {"достигнута" if hits else "не достигнута"} ({hits}/4 вариантов T1/T2).',
        f'Число положительных календарных месяцев увеличилось: {", ".join(improved) if improved else "ни у одного варианта"}.','',
        '## Все шесть полных replay','',table(all4,['version','rule','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R',
        'max_drawdown_closed_R','max_consecutive_losses','positive_months','negative_months','zero_months','positive_month_share','worst_month','worst_month_R','max_losing_month_streak']),'',
        '## По годам','',
        'CLOSED относятся к году московского exit-bar Close, как в исходной модели. OPEN — снимок на последнем наблюдаемом закрытии перед годовой границей; позиция продолжает жить в полном replay. На конце периода terminal OPEN исключены из CLOSED PF/R.',
        '',table(years.loc[years.scope.eq('ALL_FOUR')],['version','rule','year','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','positive_months','negative_months','max_drawdown_closed_R']),'',
        '## Концентрация и 2024 без ноября — только диагностика','',
        table(all4,['version','rule','top5_positive_R','top5_share_positive_R','top10_positive_R','top10_share_positive_R','gross_R_without_top5','gross_R_without_top10','gross_PF_without_top5','gross_PF_without_top10']),'',
        table(read('november_dependence.csv').loc[lambda f:f.scope.eq('ALL_FOUR')],['version','rule','november_closed','november_R','full_PF','ex_november_closed','ex_november_PF','ex_november_R','ex_november_drawdown_R']),'',
        'Drawdown — сумма CLOSED R в порядке exit_time/instrument/trade_id с начальным нулём. Это не денежная и не mark-to-market просадка. Ни ноябрь, ни крупные победители не удаляются из основной экономики. top_winners.csv сохраняет идентификаторы top5/top10. losing_month_runs.csv содержит все серии отрицательных месяцев.','',
        '## Исходные сигналы, запреты и занятость','',
        'original_signals = accepted_entries + rule_forbidden_signals + allowed_skipped_position_busy. Запрет правила и занятость могут пересекаться: forbidden_and_busy показан отдельно. Каждый вариант заново обрабатывает все исходные сигналы, включая сигналы, занятые в CONTROL.',
        '',table(funnel.loc[funnel.scope.eq('ALL_FOUR')],['version','rule','year','original_signals','rule_forbidden_signals','rule_forbidden_when_flat','rule_forbidden_and_busy','accepted_entries','allowed_skipped_position_busy']),'',
        '## Длительность, частота и наблюдаемые ночные разрывы','',
        'Годовая длительность — CLOSED exit-year cohort; частота — entry-year cohort, включая terminal OPEN. Знаменатели частоты — реально наблюдаемые московские даты Close, отдельно общий календарь портфеля и сумма инструмент-дней. Ночной gap для диагностики: >15 минут между закрытиями, даты соответствующих исходных Open различаются. Никаких искусственных свечей и официальной классификации перерыва.',
        '',table(holding.loc[holding.scope.eq('ALL_FOUR')],['version','rule','year','holding_minutes_mean','holding_minutes_median','holding_minutes_p90','accepted_entries','entries_per_observed_portfolio_day','closed_with_observed_overnight_gap','closed_with_observed_overnight_gap_share','total_observed_overnight_gap_exposures']),'',
        '## Победители ≥2R и изменение последующих входов','',
        'Сопоставление — инструмент/направление/время исходного входа, а не последовательный trade_id. При совпавшем входе весь исходный Stop/выход/P&L обязан совпадать. trade_lineage.csv объясняет каждый пропавший вход; chronology_changes.csv показывает каждое изменение допуска/занятости; new_entries.csv содержит новые CLOSED и их убытки.',
        '',table(change.loc[change.scope.eq('ALL_FOUR')],['version','rule','control_exit_year','control_large_winners_ge_2R','large_winners_preserved','large_winners_lost','lost_large_winner_R','lost_positive_R','removed_negative_R_volume','lost_entry_rule_blocked','lost_entry_busy_only','new_closed_entries','new_closed_losses','new_closed_gross_R','new_losses_R_volume']),'',
        'Сохранение победителей и ночные переносы — только ретроспективная диагностика. Прибыльный будущий перенос через полночь нельзя распознать при входе; он не используется как фильтр. Сравнивается полная экономика replay с новыми и потерянными сделками.','',
        '## T1: запрещённые сигналы по московским часам','',
        'Фиксированное окно 10:00 ≤ signal Close <18:00. Это исследовательское окно, а не официальная сессия MOEX.',
        '',table(read('t1_blocked_hours.csv').loc[lambda f:f.scope.eq('ALL_FOUR')],['version','moscow_hour','original_signals','forbidden','forbidden_flat','forbidden_busy']),'',
        '## T2: первая завершённая свеча после наблюдаемого gap','',
        'Только текущий и предыдущий фактически наблюдаемые завершённые Close. При отсутствии предыдущего — отдельная причина NO_PREVIOUS_OBSERVED_CLOSE. Следующая непрерывная свеча снова разрешена. observed_gaps.csv фиксирует все gaps, даже без исходного сигнала.',
        '',table(read('t2_gap_summary.csv').loc[lambda f:f.scope.eq('ALL_FOUR')&f.rule.eq('T2')],['version','year','observed_gaps_gt_15min','no_previous_bars','signals_on_first_bar_after_gap','signals_without_previous','blocked_gap_signals','blocked_no_previous_signals']),'',
        '## Данные и воспроизведение','',
        f'База удалённого main `{manifest["base_main"]}` совпала с ожидаемым Merge #498. Данные `{manifest["data_commit"]}`; freeze commit `{manifest["freeze_commit"]}`.',
        '',table(pd.DataFrame(manifest['sources']),['instrument','used_candles','first_open','last_open','first_close','last_close']),'',
        'CONTROL: 1 442 CLOSED +2 terminal OPEN, все общие торговые поля #490/#495 и OPEN сверены; допуск чисел 1e−8, даты/строки/флаги точно. Исторические C1/net и искусственные C1-единицы исключены. Исходные OHLC не копируются.',
        'Парсеры останавливаются по timestamp перед OHLC 2025+. Полнофайловые SHA используют будущий суффикс только как непрозрачные байты целостности. H1 — исходные дневные порядковые блоки четырёх последовательных M15; только закрытые H1 доступны текущему Close. Индикаторы пересекают дни, как в исходной модели.',
        'Stop-first, неблагоприятный Open gap, trailing после завершённой пережитой свечи, same-Close re-entry при разрешении нового входа, занятость, перенос через дни/выходные/годы сохранены. Вход по Close — историческое предположение; исполнимость реального Close-fill не заявляется.','',
        '## Каждый инструмент','',table(overall.loc[overall.scope.ne('ALL_FOUR')],['version','rule','scope','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R','positive_months','negative_months','zero_months','positive_share_covered_months','max_drawdown_closed_R']),'',
        '## LONG/SHORT, полный период и оба года','',table(read('direction_report.csv'),['version','rule','scope','year','direction','closed_trades','open_positions_at_period_end','gross_PF','gross_R','expectancy_R']),'',
        '## Все календарные месяцы','',
        'Полный календарный знаменатель — 24 месяца, включая NO_COVERAGE до старта инструмента. Доля среди покрытых месяцев отдельно в overall_report.csv. Нулевые и NO_COVERAGE не считаются положительными. OPEN на каждом месячном конце сохранены отдельно; месячная CLOSED сумма не отражает текущий P&L открытых позиций.','']
    for scope in ('ALL_FOUR','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
        lines.extend([f'### {scope}','',table(monthly.loc[monthly.scope.eq(scope)],['version','rule','month','coverage','closed_trades','open_positions_at_period_end','gross_PF','gross_R']),''])
    lines.extend(['## Аудит и STOP','',
        'AUDIT_RESULTS.json — отдельная stdlib реализация парсера, рекурсивных индикаторов, допуска входов, replay и отчётных расчётов. Алгоритмическая независимость; автор тот же, внешний аудит PENDING. Два свежих полных повтора проверяют каждый сгенерированный файл побайтно; SHA артефактов проверяется отдельно.',
        'Один Draft PR, без Merge/Auto-Merge. STOP для внешнего аудита и решения пользователя. Numerical Optimization, Robustness, Walk Forward, TRUE OOS, LIVE и новые комбинации не выполнялись.',''])
    (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
