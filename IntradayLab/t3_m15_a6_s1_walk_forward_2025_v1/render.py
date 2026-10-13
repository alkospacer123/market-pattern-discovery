"""Russian report and complete Markdown metric tables from frozen CSV/JSON data."""
import common as C
import accounting as A

def fmt(v):
    if v is None:return 'N/A'
    if isinstance(v,float):return f'{v:.6f}'
    if hasattr(v,'isoformat'):return v.isoformat()
    return str(v).replace('|',' / ').replace('\n',' ')

def table(name,rows,fields):
    result=[f'<!-- dataset {name} -->','| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']
    result += ['| '+' | '.join(fmt(r.get(k)) for k in fields)+' |' for r in rows]
    return '\n'.join(result)+'\n'

def views(t):
    return {
      'calendar':[r for r in t['summary'] if r['period'] in ['FULL_WF','W1','W2','W3','W4']+A.MONTHS and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['cohort']=='CALENDAR_CLOSED'],
      'cohorts':[r for r in t['summary'] if r['period']=='FULL_WF' and r['scope']=='ALL_FOUR' and r['direction']=='ALL'],
      'instruments':t['instrument_contributions'], 'directions':t['direction_contributions'],
      'stress':[r for r in t['scenario_summary'] if r['period']=='FULL_WF' and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT') and (r['scenario'].startswith(('R_STRESS_','LEAVE_OUT_','EX_BEST','EX_TOP')))],
      'marked':[r for r in t['marked_monthly'] if r['scope']=='ALL_FOUR' and r['direction']=='ALL']}

METRICS=['closed','period_end_OPEN','gross_PF','gross_R','expectancy_R','win_fraction','mean_WIN_R','mean_LOSS_R','positive_months','negative_months','zero_months','worst_month_R','closed_R_drawdown','max_losing_trade_run']

def report(t,out,origin,d,label):
    v=views(t);C.write_json(d/'REPORT_TABLES.json',v)
    text=['# TRAIL_375 — Walk Forward 2025',f'\nБлок **{label}**. '+C.LABEL,
      '\nТолько условная сумма первоначальных R; без общего sizing/capital и реальных издержек. Gross PF и R не являются доходностью капитала.',
      '\nПолный причинный replay от исходного начала 2023 года. Кандидат, четыре инструмента, LONG/SHORT, H1 ordinal aggregation, NEXT_OPEN, Stop-first, gaps, A6/S1, trailing 3,75 ATR неизменны. На квартальных границах FLAT-reset отсутствует. Каждый блок запечатан до чтения следующего.',
      '\nCONTROL полностью сверяется с #510, включая журналы, индикаторы и опубликованные таблицы; две реализации и фиксированные арифметические сценарии проверяются отдельно.',
      '\n## Календарные CLOSED: год, кварталы, месяцы\n',table('view_calendar',v['calendar'],['period']+METRICS),
      '\n## Новые и унаследованные сделки\n',
      'Календарный CLOSED учитывается один раз по каноническому exit Close. NEW_WF_COHORT: signal и фактический entry оба в 2025; на квартальных таблицах эта годовая cohort распределена по выходу. INHERITED_DEVELOPMENT раскрывается отдельно. OPEN не входит в CLOSED PF/R.',
      table('view_cohorts',v['cohorts'],['cohort']+METRICS),
      '\n## Инструменты\n',table('view_instruments',v['instruments'],['scope']+METRICS+['share_portfolio_R']),
      '\n## LONG / SHORT\n',table('view_directions',v['directions'],['direction']+METRICS+['share_portfolio_R']),
      '\n## Фиксированные диагностические сценарии\n',
      '−0,05R и −0,10R на каждый CLOSED — абстрактные потери R, без изменения траекторий, не комиссия FINAM/C1. Leave-one-out и исключения победителей/месяцев — диагностика; первичные результаты сохраняют все сделки.',
      table('view_stress',v['stress'],['cohort','scenario','closed','gross_PF','gross_R','expectancy_R','closed_R_drawdown','positive_months','negative_months','zero_months']),
      '\n## Marked-R отдельно от CLOSED\n',
      'Marked-R = CLOSED R + U_end − U_start. Снимок — последний разрешённый завершённый Close перед границей; время и цена отметки в open_monthly/ CHECKPOINT, без оценок 2026.',
      table('view_marked',v['marked'],['month','CLOSED_R','U_start_R','U_end_R','marked_R','OPEN_start','OPEN_end','carried_in_IDs','carried_out_IDs']),
      '\n## Аудит и ограничения\n',
      'Внешнее человеческое ревью PENDING. Независимость вычислительная: два канонических алгоритма, один автор. Покрытие проверяется только в разрешённом prefix: все 48 instrument-month, фактические наблюдаемые бары/дни/gaps; независимого биржевого календаря и доказательства отсутствия всех vendor-пропусков нет. Будущая часть не исследуется. Нет оптимизации, TRUE OOS, LIVE, брокерских действий, допуска к реальной торговле.',
      '\nПолные показатели, top-1/3/5/10 ID, recovery episodes, серии убытков, состояния OPEN, coverage и сценарии: DETAILS.md, CSV и TABLES.json. Полные журналы: primary/ и scalar/.']
    (d/'REPORT_RU.md').write_text('\n'.join(text)+'\n')
    columns={
      'summary':['period','cohort','scope','direction']+METRICS+['top1_months','top1_months_R','top1_share_annual_R','top3_months','top3_months_R','top3_share_annual_R','max_DD_recovered','max_DD_peak_time','max_DD_trough_time','max_DD_recovery_time','max_DD_days_to_recovery','terminal_underwater_R'],
      'scenario_summary':['period','cohort','scope','direction','scenario','closed','gross_PF','gross_R','expectancy_R','positive_months','negative_months','zero_months','closed_R_drawdown','excluded_months','R_stress_per_CLOSED'],
      'top_winners':['period','cohort','scope','direction','rank','instrument','trade_id','signal_time','entry_time','exit_time','gross_R'],
      'loss_runs':['period','scope','direction','type','start','end','length','gross_R'],
      'drawdown_episodes':['period','scope','direction','peak_time','underwater_start','max_depth_R','trough_time','recovery_time','recovered','days_to_recovery'],
      'coverage':['instrument','month','status','bars','indicator_ready_bars','first_close','last_close','observed_days'],
      'open_monthly':['month','instrument','trade_id','direction','signal_time','entry_time','entry_price','initial_risk','active_stop','threshold_activated','activation_time','favorable_extreme','last_close','last_close_price','unrealized_gross_R_at_last_close']}
    (d/'DETAILS.md').write_text('# Полные диагностические таблицы\n\nВсе первичные ячейки, включая отрицательные и N/A. Gross-only, без доходности капитала.\n\n'+'\n'.join(table(n,t[n],fs) for n,fs in columns.items()))

def final(t,decision,d):
    v=views(t);full=v['calendar'][0];cohort=next(r for r in v['cohorts'] if r['cohort']=='NEW_WF_COHORT')
    inherited=next(r for r in v['cohorts'] if r['cohort']=='INHERITED_DEVELOPMENT')
    marked=sum(r['marked_R'] for r in v['marked']);u0=v['marked'][0]['U_start_R'];u1=v['marked'][-1]['U_end_R']
    top=sorted([r for r in t['top_winners'] if r['period']=='FULL_WF' and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['cohort']=='CALENDAR_CLOSED'],key=lambda r:r['rank'])
    txt=f'''# Итог Walk Forward 2025 — {decision['status']}

**{decision['status']}**. Полный календарный 2025: Gross PF **{fmt(full['gross_PF'])}**, Gross R **{full['gross_R']:+.6f}R**, **{full['closed']} CLOSED / {full['period_end_OPEN']} terminal OPEN**, expectancy **{fmt(full['expectancy_R'])}R**, положительные месяцы **{full['positive_months']}/12**, отрицательные **{full['negative_months']}**, нулевые **{full['zero_months']}**. CLOSED-R DD **{full['closed_R_drawdown']:.6f}R**.

Новые входы WF: **{cohort['closed']} CLOSED / {cohort['period_end_OPEN']} OPEN**, PF **{fmt(cohort['gross_PF'])}**, Gross R **{cohort['gross_R']:+.6f}R**, expectancy **{fmt(cohort['expectancy_R'])}R**. Унаследованные из DEVELOPMENT: **{inherited['closed']} CLOSED**, **{inherited['gross_R']:+.6f}R**, новые сделки WF из них не создаются. Полная судьба IMOEXF T3-M15-IMOEXF-000090 в cohort_ledger и журналах.

Marked-R отдельно: **{marked:+.6f}R = {full['gross_R']:+.6f}R + {u1:.6f}R − {u0:.6f}R**. Это условный учёт индивидуальных initial R, без реального капитала, sizing, комиссий, spread/slippage и funding. Незакрытые сделки не ликвидированы и не разрешены через 2026.

Кварталы, стороны, инструменты и все отрицательные ячейки сохранены. Критерии #511 применяются в исходном порядке: validity → evidence → знак всего года и новых входов → неоднородность → review. Нет автоматического WF PASS. Высокий PF сам по себе не даёт допуска к TRUE OOS; не подбирались фильтры, параметры, инструменты или пороги.

Worst month **{full['worst_month']} ({full['worst_month_R']:+.6f}R)**; максимальная серия проигрышей **{full['max_losing_trade_run']}**; серия убыточных месяцев **{full['max_negative_month_run']}**. Recovery крупнейшего DD: **{full['max_DD_recovered']}**, время **{fmt(full['max_DD_recovery_time'])}**, дней от начала просадки **{fmt(full['max_DD_days_to_recovery'])}**. Лучший месяц **{full['top1_months']}**, доля годового R **{fmt(full['top1_share_annual_R'])}**; лучшие три **{full['top3_months']}**, доля **{fmt(full['top3_share_annual_R'])}**. Если Gross R неположительный, доли N/A; абсолютные R сохранены.

Top-1/3/5/10 суммарные победители: {', '.join(str(n)+'='+fmt(sum(r['gross_R'] for r in top[:n]))+'R' for n in (1,3,5,10))}. ID и исходные сделки раскрыты; stress и leave-one-out — в REPORT_RU/DETAILS/CSV, без изменения стратегии.

Независимость — вычислительная: dataframe/position и stdlib/scalar state machine, отдельная арифметика и свежий auditor. Один автор; внешнее человеческое ревью **PENDING**. CONTROL и все границы проверяются полными журналами, indicator prefix и переносом Stop/S1/extreme/initial R; два свежих полных повтора сверяются direct bytes и SHA256. Детальные receipts публикуются отдельно, утверждение об идентичности действительно только при REPEATABILITY.json PASS.

2026 не открыт: reader использует unbuffered FileIO, допускает suffix только после проверки завершения свечи < cutoff, для будущего года останавливается после четырёх ASCII-байтов года, без декодирования timestamp, OHLCV, coverage и результатов. SHA256 только разрешённого prefix. Git data pin взят из метаданных; запрещённый suffix не хешировался. Полный будущий порядок строк не проверяется. Покрытие WF подтверждено в пределах источника по месяцам/наблюдаемым дням, независимый exchange-calendar completeness не доказан.

**STOP после одного Draft PR для независимого аудита и решения пользователя. NO MERGE / NO AUTO-MERGE. TRUE OOS 2026 и LIVE не выполнялись.**

DEVELOPMENT_2023_2024_EXPOSED / WF_2025_AUTHORIZED / TRUE_OOS_2026_LOCKED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.
'''
    (d/'CONCLUSIONS_RU.md').write_text(txt)
