"""Deterministic presentation only; no strategy or outcome-based selection."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent;ROOT=HERE/'results'
RULES=('CONTROL','A6','A7','S1','C1','C2');VERSIONS=('BASELINE','OPTIMIZED')
matplotlib.rcParams['svg.hashsalt']='t3_m15_combined_v1'
matplotlib.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})


def load(name):return pd.read_csv(ROOT/(name+'.csv'))
def fmt(x):
    if x is None or pd.isna(x):return '—'
    if isinstance(x,(float,np.floating)):return f'{x:.3f}'
    return str(x)
def table(f,cols):
    rows=['| '+' | '.join(label for field,label in cols)+' |','|'+'|'.join('---' for _ in cols)+'|']
    rows+=['| '+' | '.join(fmt(t[field]) for field,label in cols)+' |' for t in f.to_dict('records')]
    return '\n'.join(rows)+'\n'
def js(p,value):p.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')
def write(name,sections):(HERE/name).write_text('\n\n'.join(sections)+'\n')


def charts(overall,yearly,monthly,trades):
    fig,axes=plt.subplots(1,2,figsize=(12,4),sharey=True,layout='constrained')
    for ax,v in zip(axes,VERSIONS):
        for offset,period,color in [(-.23,'2023','#4578ad'),(0,'2024','#dd9149'),(.23,'ALL','#368d7c')]:
            f=overall if period=='ALL' else yearly.loc[yearly.year.eq(int(period))]
            values=[float(f.loc[f.version.eq(v)&f.rule.eq(r),'gross_PF'].iloc[0]) for r in RULES]
            ax.bar(np.arange(len(RULES))+offset,values,width=.22,label=period,color=color)
        ax.axhline(2,color='#333',linestyle='--',linewidth=1);ax.set_xticks(range(len(RULES)),RULES);ax.set_title(v);ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Gross PF / ALL_FOUR');axes[1].legend();fig.savefig(HERE/'gross_pf.svg',metadata={'Date':None});plt.close(fig)
    months=sorted(monthly.month.unique());labels=[v+' / '+r for v in VERSIONS for r in ('CONTROL','C1','C2')]
    values=np.array([[float(monthly.loc[monthly.version.eq(v)&monthly.rule.eq(r)&monthly.month.eq(m),'gross_R'].iloc[0]) for m in months] for v in VERSIONS for r in ('CONTROL','C1','C2')])
    fig,ax=plt.subplots(figsize=(15,4),layout='constrained');scale=float(abs(values).max())
    im=ax.imshow(values,cmap='RdBu',vmin=-scale,vmax=scale,aspect='auto');ax.set_xticks(range(len(months)),months,rotation=55,ha='right',fontsize=8);ax.set_yticks(range(len(labels)),labels)
    for y in range(len(labels)):
        for x in range(len(months)):ax.text(x,y,f'{values[y,x]:.1f}',ha='center',va='center',fontsize=7,color='white' if abs(values[y,x])>scale*.55 else '#222')
    ax.set_title('Monthly CLOSED Gross R / ALL_FOUR / 2023–2024');fig.colorbar(im,ax=ax,label='Gross R');fig.savefig(HERE/'monthly_gross_R.svg',metadata={'Date':None});plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(12,4),layout='constrained')
    for ax,v in zip(axes,VERSIONS):
        for r,color in [('CONTROL','#738090'),('S1','#bb8945'),('C1','#33816a'),('C2','#436bb7')]:
            f=trades.loc[trades.version.eq(v)&trades.rule.eq(r)].sort_values(['exit_time','instrument','trade_id'],kind='mergesort')
            ax.plot(pd.to_datetime(f.exit_time,utc=True),f.gross_R.cumsum(),label=r,color=color,linewidth=1.2)
        ax.set_title(v);ax.set_ylabel('Cumulative CLOSED Gross R');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Closed-trade bookkeeping; no portfolio capital / MTM model');fig.savefig(HERE/'closed_gross_R.svg',metadata={'Date':None});plt.close(fig)


def main():
    all_overall=load('overall_report');overall=all_overall.loc[all_overall.scope.eq('ALL_FOUR')]
    all_yearly=load('yearly_report');yearly=all_yearly.loc[all_yearly.scope.eq('ALL_FOUR')]
    monthly=load('monthly_report');directions=load('direction_report');nov=load('november_dependence')
    frequency=load('frequency_occupancy');retention=load('component_winner_retention');comparison=load('component_comparisons')
    source=json.loads((ROOT/'SOURCE_MANIFEST.json').read_text());audit=json.loads((HERE/'AUDIT_RESULTS.json').read_text());repeat=json.loads((HERE/'REPEATABILITY.json').read_text())
    charts(overall,yearly,monthly.loc[monthly.scope.eq('ALL_FOUR')],load('trades'))
    variants=overall.loc[overall.rule.isin(('C1','C2'))];achieved=bool((variants.gross_PF>=2).any())
    goal='Цель полного Gross PF ≥2 достигнута хотя бы одной комбинацией.' if achieved else 'Цель полного Gross PF ≥2 не достигнута ни одной из четырёх конфигураций C1/C2. Дополнительной подгонки нет.'
    core=[('version','Версия'),('rule','Вариант'),('gross_PF','Gross PF'),('gross_R','Gross R'),('closed_trades','CLOSED'),('open_terminal_positions','terminal OPEN')]
    report=['# IntradayLab — T3/M15 Combined v1',
        '**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 development-exposed. Draft PR; STOP для внешней проверки, без Merge и Auto-Merge.**',goal,
        'PR #496 слит до начала: фактический GitHub main `'+source['base_main']+'`. Источники #490/#495/#496 неизменны. Данные `market-pattern-data` @ `'+source['data_commit']+'`. Спецификация и весь исполняемый код заморожены до результатов в `'+source['spec_freeze_commit']+'`. Подробности: [PREREGISTRATION](PREREGISTRATION.json), [START_GATE](START_GATE.json), [SPEC](EXPERIMENT_SPECS.json).',
        table(pd.DataFrame(source['sources']),[('instrument','Инструмент'),('first_close','Первый M15 Close MSK'),('last_close','Последний M15 Close MSK'),('used_candles','Свечей')]),
        '## Механика и определения',
        'C1 = A6 H1_ATR_EXPANSION + S1 TRAIL_AFTER_1R. C2 = A7 M15_ATR_RISING + S1. BASELINE trailing 3.0, OPTIMIZED trailing 3.5; initial Stop 2 ATR. A6 требует строго растущий H1 ATR/ATRMean по двум завершённым H1; A7 — строго растущий M15 ATR. Missing predecessor / равенство не проходят. EMA75, slope5, ADX14>20, ATR14, H1 ATRMean20 и Donchian20 сохранены.',
        'Каждый вариант выполняет полный причинный replay. Сначала действует прежний Stop: неблагоприятный Open gap, затем adverse intrabar extreme. Exit candle не даёт новый favorable extreme, активацию или MFE. После пережитой завершённой свечи с ≥1 initial R S1 разрешает оригинальный trailing по накопленному post-entry extreme; новый Stop действует только на следующей наблюдаемой свече. SHORT зеркален, риск неизменен, Stop монотонен. Signal-candle extremes исключены. Состояние переносится через сессии, выходные и годы.',
        'Сохранена историческая модель Close-входов и same-Close re-entry после выхода. Protective exit имеет метку Close свечи, фактический intrabar момент неизвестен; adverse Open заполняет gap. Terminal OPEN не ликвидируются и исключены из CLOSED PF/R; в годовых/месячных OPEN-графах указано время входа терминальных позиций, это не исторические снимки.',
        'Gross PF = сумма положительных R / модуль суммы отрицательных R. Год и месяц CLOSED определяются по метке выхода MSK. Нулевые доступные месяцы включены, до поздних стартов искусственных месяцев нет. DD — последовательность CLOSED R с нулевым начальным equity, сортировка exit_time/instrument/trade_id; сумма R не является портфельной доходностью или MTM. Top5/top10 делятся на все положительные R. Удаление top/ноября — фиксированная отчётная чувствительность, не повторный replay или отбор.',
        'Занятость = число M15-свечей с позицией при Open / число фактически наблюдавшихся eligible свечей (первая свеча каждого инструмента исключена). Частота = принятые входы на 1000 observed bars. Отдельно сохранены raw signals, filter rejects и passes blocked by occupancy. Holding minutes используют исторические Close-метки и включают календарные разрывы.',
        '## Полный период и каждый год',table(overall,core),table(yearly,core[:2]+[('year','Год')]+core[2:]),'![Gross PF](gross_pf.svg)',
        '## Сравнение с CONTROL и отдельными компонентами',
        'Каждая комбинация сравнивается с CONTROL, соответствующим A6/A7 и S1. Полный набор по годам, месяцам, инструментам и направлениям: [component_comparisons.csv](results/component_comparisons.csv).',
        table(comparison.loc[comparison.scope.eq('ALL_FOUR')&comparison.report.isin(('overall_report.csv','yearly_report.csv'))&comparison.metric.isin(('gross_PF','gross_R','closed_trades','max_drawdown_R','positive_months'))],[('version','Версия'),('variant','Комбинация'),('reference','Основа'),('report','Период таблицы'),('year','Год'),('metric','Метрика'),('variant_value','Комбинация'),('reference_value','Основа'),('delta','Δ')]),
        '## Календарь, риск, концентрация',
        table(overall,core[:2]+[('positive_months','+месяцев'),('available_months','Всего'),('worst_month','Худший месяц'),('worst_month_R','R худшего'),('max_drawdown_R','DD R'),('top5_share_positive_R','Top5/+R'),('top10_share_positive_R','Top10/+R'),('gross_PF_without_top10','PF без top10')]),
        '![Месяцы](monthly_gross_R.svg)','![Накопленный Gross R](closed_gross_R.svg)',
        '## Победители ≥2R',
        'Когорты фиксированы по исходной CLOSED сделке каждой основы; совпадение по version/instrument/direction/exact entry_time. Fully preserved означает variant R ≥ reference R −1e−8. Reduced / lost-entry / terminal OPEN раздельны; ниже 2R и неположительные исходы дополнительно. Совпадение входов — диагностическая связь, не рыночный контрфактуал.',
        table(retention.loc[retention.scope.eq('ALL_FOUR')&retention.year.eq('ALL')],[('version','Версия'),('variant','Комбинация'),('reference','Основа'),('reference_ge2R_winners','Исходных ≥2R'),('fully_preserved','Полностью сохранены'),('reduced','Сокращены'),('lost_entry','Нет входа'),('terminal_open','OPEN'),('matched_below_2R','Ниже 2R'),('matched_nonpositive','R≤0')]),
        'Полная связь каждой исходной сделки: [component_trade_lineage](results/component_trade_lineage.csv). Когорты по каждому году и инструменту: [component_winner_retention](results/component_winner_retention.csv). Все исходные победители/убытки CONTROL, top5/top10 и точная декомпозиция ΔR: [winner_loss_changes](results/winner_loss_changes.csv), [large_winners](results/large_winners.csv), [gross_R_attribution](results/gross_R_attribution.csv).',
        '## Ноябрь 2024',table(nov.loc[nov.scope.eq('ALL_FOUR')],core[:2]+[('gross_R_2024','R 2024'),('november_R','R ноября'),('november_share_positive_R','Ноябрь/+R'),('ex_november_R','R без ноября'),('ex_november_PF','PF без ноября'),('ex_november_max_drawdown_R','DD без ноября')]),
        '## Частота и занятость',table(frequency.loc[frequency.scope.eq('ALL_FOUR')&frequency.year.eq('ALL')],core[:2]+[('accepted_entries','Входы'),('closed_trades','CLOSED'),('accepted_entries_per_1000_observed_bars','Входов/1000'),('observed_bar_occupancy','Занятость'),('mean_closed_bars_held','Средн. M15 held'),('filter_failed','Не прошли фильтр'),('filter_pass_but_occupied','Pass/занято')]),
        'Полные изменения по годам и инструментам: [frequency_comparison](results/frequency_comparison.csv).',
        '## Проверки и ограничение независимости аудита',
        f"20 причинных tests PASS до market replay. CONTROL, A6, A7, S1 воспроизведены: [REFERENCE_REPRODUCTION](results/REFERENCE_REPRODUCTION.json), [REFERENCE_PATH_REPRODUCTION](results/REFERENCE_PATH_REPRODUCTION.json); CONTROL также проверен относительно #490. Отдельный standard-library auditor независимо пересчитал признаки и все пути: {audit['closed_records_verified']} CLOSED, {audit['terminal_positions_verified']} terminal OPEN, {audit['stop_decisions_verified']} Stop-решений, {audit['entry_opportunities_verified']} entry decisions; статус {audit['status']}. Два свежих детерминированных повтора: {repeat['status']}, прямое bytes/SHA сравнение каждого generated файла.",
        'Аудит использует отдельный код без импорта primary engine/research/pandas, но написан тем же автором. Это независимая реализация, не независимый человеческий reviewer. Внешний аудит остаётся PENDING; [INDEPENDENT_AUDIT](INDEPENDENT_AUDIT.md) описывает проверенный объём и ограничения.',
        '## Полный пакет и границы',
        'Все шесть полных журналов сделок: [trades](results/trades.csv), отдельные trades_CONTROL/A6/A7/S1/C1/C2. Все входы/occupancy: [entry_opportunities](results/entry_opportunities.csv). Все Stop/активации: [stop_decisions](results/stop_decisions.csv). Terminal OPEN: [OPEN_POSITIONS](results/OPEN_POSITIONS.json). Таблицы overall/yearly/monthly/instrument/direction/monthly_direction_report сохраняют полный набор метрик. Все отрицательные исходы сохранены.',
        'Источник read-only; OHLC 2025+ не парсятся. Полный SHA — непрозрачные байты для проверки целостности. Нет Optimization, Robustness, Walk Forward, TRUE OOS, LIVE, дополнительных сочетаний, порогов или изменения механики. TradingSystemLab, прежние исследования, ROADMAP, market data и робот неизменны. Стоимость, slippage/spread/funding не вычитались по явно заданному gross-only scope; исполнимость Close-входов, tick-safe Stops и net economics не доказаны. 2023–2024 development-exposed, не независимый тест. **STOP на Draft PR для внешней проверки.**']
    write('EXPERIMENT_REPORT.md',report)
    details=['# Инструменты и направления','GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. CLOSED по выходу; terminal OPEN по входу.',table(all_overall,core[:2]+[('scope','Scope')]+core[2:]),table(all_yearly,core[:2]+[('scope','Scope'),('year','Год')]+core[2:]),table(directions,core[:2]+[('scope','Scope'),('year','Год'),('direction','Направление')]+core[2:])]
    write('INSTRUMENT_DIRECTION_DETAIL.md',details)
    write('MONTHLY_DETAIL.md',['# Все доступные календарные месяцы','MSK. Поздние старты сохранены; доступные zero месяцы включены. Полные direction-month данные в monthly_direction_report.csv.',table(monthly,core[:2]+[('scope','Scope'),('month','Месяц')]+core[2:])])
    js(HERE/'OBJECTIVE_ASSESSMENT.json',{'status':'OBJECTIVE_REACHED_GROSS_ONLY' if achieved else 'OBJECTIVE_NOT_REACHED',
        'target_gross_PF':2.,'scope':'ALL_FOUR_FULL_PERIOD','combinations':[{'version':r.version,'rule':r.rule,'gross_PF':r.gross_PF,'gross_R':r.gross_R,'closed':int(r.closed_trades),'open':int(r.open_terminal_positions)} for r in variants.itertuples()],
        'retrospective_adjustment':False,'external_independent_reviewer':'PENDING','2023_2024':'DEVELOPMENT_EXPOSED',
        'labels':['GROSS_ONLY','COSTS_DEFERRED','NOT_LIVE_READY'],'next_action':'STOP_EXTERNAL_REVIEW','merge':False,'auto_merge':False})
    for p in HERE.iterdir():
        if p.suffix in ('.md','.svg'):p.write_text('\n'.join(t.rstrip() for t in p.read_text().splitlines()).rstrip()+'\n')
    js(HERE/'PRESENTATION_SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.iterdir()) if p.suffix in ('.md','.svg') or p.name=='OBJECTIVE_ASSESSMENT.json'})
    print(json.dumps({'presentation':'COMPLETE','objective_reached':achieved}))


if __name__=='__main__':main()
