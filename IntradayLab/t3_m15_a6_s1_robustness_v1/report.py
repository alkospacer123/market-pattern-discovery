"""Deterministic Russian presentation. All numeric table cells audited independently."""
import common as C

KEYS={
    'summary':['scope','direction','year'],
    'scenario_summary':['scenario','scope','direction','year'],
    'monthly':['scope','direction','year','month'],
    'top_winners':['year','direction','rank'],
    'november2024':['scope','direction']}

def display(value):
    if value is None:return 'N/A'
    if isinstance(value,bool):return str(value)
    if isinstance(value,float):return f'{value:.6f}'
    return str(value)

def table(name,rows,fields):
    lines=['<!-- table:'+name+' -->','| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']
    lines+=['| '+' | '.join(display(r.get(k)) for k in fields)+' |' for r in rows]
    return '\n'.join(lines)+'\n'

def render(tables,path):
    text='# TRAIL_375 — фиксированная Robustness v1\n\n'
    text+='2023–2024 DEVELOPMENT_EXPOSED. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.\n\n'
    text+='Все расчёты основаны на неизменных траекториях A6+S1 / T3 M15 / NEXT_OPEN / TRAIL_375. Исходный состав — четыре инструмента. Диагностическое вычитание сделок/месяцев/инструмента не меняет торговые решения и не предлагает новый портфель. Единственный торговый replay здесь — CONTROL.\n\n'
    text+='Результат Robustness и ответы на четыре вопроса находятся в ../CONCLUSIONS.md и ../DECISION.json. Таблицы ниже не являются автоматическим критерием допуска.\n\n'
    text+='## Инструменты и LONG/SHORT по годам\n\n'
    text+=table('summary',tables['summary'],KEYS['summary']+['closed','period_end_OPEN','gross_PF','gross_R','expectancy_R','positive_months','months','no_coverage_months','worst_month_R','closed_R_drawdown','max_losing_trade_run','max_negative_month_run','share_portfolio_net_R'])
    text+='\nGLDRUBF: partial start июль2023; IMOEXF: ноябрь2023. Denominator всегда календарные12/24; NO_COVERAGE не равен AVAILABLE_NO_CLOSED. Period-end OPEN — фактический исходный снимок, не число диагностически исключённых позиций. OPEN не включён в PF/R.\n\n'
    text+='## Фиксированные sensitivity\n\n'
    text+=table('scenario_summary',tables['scenario_summary'],KEYS['scenario_summary']+['closed','gross_PF','gross_R','positive_months','months','retained_calendar_months','closed_R_drawdown','worst_month_R','removed_or_stressed_R','excluded_months'])
    text+='\nLEAVE_OUT допустим для эталонной суммы R: состояние позиции/ожидающего входа локально одному symbol; межинструментальных лимитов нет. Для реального общего капитала это условная диагностика, без sizing/equity. Состав не меняется.\n\n'
    text+='EX_BEST1/3 и EX_TOP1/3/5/10 ранжируются отдельно внутри assessment year/ALL и direction. ALL exclusions и годовые exclusions поэтому могут содержать разные IDs/месяцы и не должны складываться. В EX_BEST исходный denominator сохраняется; исключённые месяцы нулевые, retained denominator отдельный.\n\n'
    text+='R_STRESS_005/010 вычитает0.05/0.10 initial R каждой CLOSED-сделки, переклассифицирует wins/losses и считает PF по новым положительным/отрицательным R. Это абстрактное снижение результата, не комиссия, C1 или реальный FINAM slippage. Исходные entry/exit/Stop/R и OPEN неизменны.\n\n'
    text+='## Крупнейшие победители\n\n'
    text+=table('top_winners',tables['top_winners'],KEYS['top_winners']+['instrument','trade_id','exit_month','gross_R'])
    text+='\n## Ноябрь2024\n\n'
    text+=table('november2024',tables['november2024'],KEYS['november2024']+['closed','gross_PF','gross_R','share_2024_net_R'])
    text+='\nДоли net R определены только при положительной сумме соответствующего периода. Ноябрьский результат и top winners перекрываются: вклады нельзя складывать как независимые объяснения.\n\n'
    text+='Все summary поля (best1/best3 shares, ex-month PF/R, wins/losses, expectancy, серии), полные scenario_monthly, каждое исключение/снижение CLOSED в scenario_ledger, все negative runs и ноябрьские разрезы сохранены в CSV и TABLES.json. CLOSED-R DD — накопленный реализованный R с deterministic tie order, не MTM или доходность капитала.\n\n'
    text+='Никакого Walk Forward, TRUE OOS, OHLC2025+ или LIVE. Вычислительная независимость — отдельные indicators/dict replay/accounting; автор один, внешнее человеческое ревью PENDING. Один Draft PR, NO MERGE / NO AUTO-MERGE; STOP для проверки.\n'
    (path/'REPORT.md').write_text(text)
    detail='# Все24 календарных месяца — исходный кандидат\n\n'+C.LABEL+'. DEVELOPMENT_EXPOSED.\n\n'
    detail+=table('monthly',tables['monthly'],KEYS['monthly']+['coverage','status','closed','gross_PF','gross_R','positive_R','negative_R'])
    (path/'MONTHLY_DETAIL.md').write_text(detail)
