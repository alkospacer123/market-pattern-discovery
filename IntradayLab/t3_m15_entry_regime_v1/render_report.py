"""Readable presentation of every fixed experiment; no strategy selection run."""
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE/'results'


def read(name):
    with (ROOT/name).open() as f:return list(csv.DictReader(f))


def fmt(v,digits=3):
    if v in ('',None):return '—'
    try:
        n = float(v)
        return str(int(n)) if n.is_integer() else f'{n:.{digits}f}'
    except (ValueError,TypeError):return str(v)


def table(rows,cols):
    return '\n'.join(['| '+' | '.join(label for label,col in cols)+' |',
        '|'+'|'.join('---' for x in cols)+'|']+
        ['| '+' | '.join(fmt(r.get(col)) for label,col in cols)+' |' for r in rows])


def main():
    yearly,overall,changes,winners,november,directions = map(read,('yearly_report.csv','overall_report.csv','winner_loss_changes.csv','large_winners.csv','november_dependence.csv','direction_report.csv'))
    pooled = lambda rows:[r for r in rows if r['scope'] == 'ALL_FOUR']
    annual = pooled(yearly)
    y24 = [r for r in annual if r['year'] == '2024']
    complete = pooled(overall)
    find = lambda rows,v,rule,**kwargs:next(r for r in rows if r['version'] == v and r['rule'] == rule and all(r[k] == str(val) for k,val in kwargs.items()))
    spec = json.loads((HERE/'EXPERIMENT_SPECS.json').read_text())
    manifest = json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
    combined = []
    for r in y24:
        v,rule = r['version'],r['rule']
        c = find(y24,v,'CONTROL')
        a23 = find(annual,v,rule,year=2023)
        combined.append(r | {'PF_2023':a23['gross_PF'],'R_2023':a23['gross_R'],
            'delta_PF_2024':float(r['gross_PF'])-float(c['gross_PF']),
            'positive_months_display':f"{r['positive_months']}/{r['available_months']}"})
    instrument_rows = []
    for r in y24:
        instrument_rows.append({k:r[k] for k in ('version','rule')} |
            {s:find(yearly,r['version'],r['rule'],scope=s,year=2024)['gross_PF'] for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')})
    direction_rows = []
    for r in y24:
        v,rule = r['version'],r['rule']
        lr,sr = find(directions,v,rule,scope='ALL_FOUR',year=2024,direction='LONG'),find(directions,v,rule,scope='ALL_FOUR',year=2024,direction='SHORT')
        direction_rows.append({'version':v,'rule':rule,'LONG_PF':lr['gross_PF'],'LONG_R':lr['gross_R'],'LONG_n':lr['closed_trades'],
            'SHORT_PF':sr['gross_PF'],'SHORT_R':sr['gross_R'],'SHORT_n':sr['closed_trades']})
    preserved = []
    for r in pooled(changes):
        if r['year'] != '2024':continue
        n = find(november,r['version'],r['rule'],scope='ALL_FOUR')
        t = find(winners,r['version'],r['rule'],scope='ALL_FOUR',year=2024,top_n=10)
        preserved.append(r | {'top10_preserved':t['fully_preserved'],'top10_lost':t['entries_lost'],
            'ex_nov_PF':n['ex_november_PF'],'nov_share_positive_R':n['november_share_positive_R']})
    # Static scientific visual, exported as a standalone artifact. Fixed SVG
    # IDs and no timestamp make rendering byte reproducible.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams['svg.hashsalt'] = 'intraday-t3-m15-entry-regime-v1'
    fig,axes = plt.subplots(1,2,figsize=(12,5),gridspec_kw={'width_ratios':[1,1.4]})
    rules = ['CONTROL','A1','A2','A3','A4','A5','A6','A7']
    x = np.arange(8)
    for offset,v,color in [(-.18,'BASELINE','#356b9a'),(.18,'OPTIMIZED','#cf8735')]:
        axes[0].bar(x+offset,[float(find(y24,v,r)['gross_PF']) for r in rules],.36,label=v,color=color)
    axes[0].axhline(2,color='#777777',ls='--',lw=1,label='Research target 2.0')
    axes[0].set_xticks(x,rules,rotation=30);axes[0].set_ylim(0,2.15)
    axes[0].set_ylabel('Gross PF');axes[0].set_title('All four instruments / 2024');axes[0].legend(fontsize=8)
    m = read('monthly_report.csv')
    labels = [(v,r) for v in ('BASELINE','OPTIMIZED') for r in rules]
    month_labels = [f'2024-{i:02d}' for i in range(1,13)]
    matrix = np.array([[float(find(m,v,r,scope='ALL_FOUR',month=month)['gross_R']) for month in month_labels] for v,r in labels])
    limit = max(abs(matrix.min()),abs(matrix.max()))
    im = axes[1].imshow(matrix,cmap='RdBu',vmin=-limit,vmax=limit,aspect='auto')
    axes[1].set_xticks(range(12),range(1,13));axes[1].set_xlabel('Calendar month / Moscow exit labels')
    axes[1].set_yticks(range(16),[('B ' if v == 'BASELINE' else 'O ')+r for v,r in labels],fontsize=8)
    axes[1].set_title('Gross R by month / 2024');axes[1].axvline(9.5,color='#555555',lw=.7);axes[1].axvline(10.5,color='#555555',lw=.7)
    fig.colorbar(im,ax=axes[1],label='Bookkeeping R sum')
    fig.suptitle('GROSS ONLY / COSTS DEFERRED / NOT LIVE READY',fontsize=11)
    fig.tight_layout();fig.savefig(HERE/'gross_summary.svg',metadata={'Date':None});plt.close(fig)
    text = ['# EXPERIMENT REPORT — T3/M15 Entry & Regime v1',
        '**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. Внешний аудит и решение пользователя: PENDING.**',
        'Выполнены семь фиксированных одиночных механизмов на BASELINE trailing 3.0 и OPTIMIZED trailing 3.5. Оптимизацию, комбинации и дополнительный подбор не выполняли. PF ≥2 — исследовательская цель, не критерий PASS. Полная таблица сохраняет отрицательные результаты.',
        '## Контроль и источники',
        f"GitHub main перед началом `{manifest['base_main']}` содержит объединённый PR #494. Заморозка спецификаций: `{manifest['spec_freeze_commit']}`. Данные `{manifest['data_commit']}`. Только M15 2023–2024; реальные даты начала приведены ниже.",
        '**Контроль механики PASS: 1 442 закрытые сделки (741 BASELINE, 701 OPTIMIZED) и две незакрытые позиции IMOEXF.** Цены, время, направление, Stop, Gross R, последовательность и сопутствующие поля сверены с неизменным PR #490; результаты Gross-only сохранены отдельно от его C1-результатов.',
        table(manifest['sources'],[('Инструмент','instrument'),('Первый Close','first_close'),('Последний Close','last_close'),('M15','used_candles')]),
        '## Итог всех механизмов и обоих контролей',
        'PF, R и просадка ниже относятся к Gross. Суммы R четырёх инструментов — учётная сумма разных нормированных сделок, **не доходность реального портфеля**. Открытые позиции не ликвидируются и не входят в closed-trade PF/R.',
        table(combined,[('Контроль','version'),('Правило','rule'),('PF 2023','PF_2023'),('R 2023','R_2023'),('PF 2024','gross_PF'),('Δ PF 2024','delta_PF_2024'),('R 2024','gross_R'),('Сделок 2024','closed_trades'),('Плюс месяцев','positive_months_display')]),
        '![Gross PF and monthly Gross R, all fixed variants](gross_summary.svg)',
        '## Полный 2023–2024 Gross-результат',
        table(complete,[('Контроль','version'),('Правило','rule'),('PF','gross_PF'),('R','gross_R'),('Expectancy','gross_expectancy_R'),('Закрыто','closed_trades'),('Открыто','open_terminal_positions'),('Win rate','win_rate'),('Средний выигрыш','mean_win_R'),('Средний убыток','mean_loss_R'),('Max DD R','max_drawdown_R')]),
        '## Календарь и концентрация в слабом 2024',
        table(y24,[('Контроль','version'),('Правило','rule'),('+','positive_months'),('−','negative_months'),('0','zero_months'),('Худший месяц','worst_month'),('R худшего','worst_month_R'),('Серия − месяцев','max_losing_month_streak'),('Max DD R','max_drawdown_R'),('Top5 / +R','top5_share_positive_R'),('Top10 / +R','top10_share_positive_R')]),
        'Все календарные месяцы, включая нулевые, сохранены в `results/monthly_report.csv`; показатели по 2023 и полному периоду в `yearly_report.csv` / `overall_report.csv`. У инструментов до фактического старта месяцы не добавляются. Год и месяц определяются по метке выхода.',
        '## Каждый инструмент: Gross PF 2024',
        table(instrument_rows,[('Контроль','version'),('Правило','rule'),('USDRUBF','USDRUBF'),('CNYRUBF','CNYRUBF'),('GLDRUBF','GLDRUBF'),('IMOEXF','IMOEXF')]),
        'Полные R, expectancy, частота, форма выигрыша/убытка, DD, месяцы и концентрация для каждого инструмента — в `instrument_report.csv`, `yearly_report.csv` и `monthly_report.csv`; ни один инструмент не исключён.',
        '## Направления: Gross 2024',
        table(direction_rows,[('Контроль','version'),('Правило','rule'),('LONG PF','LONG_PF'),('LONG R','LONG_R'),('LONG n','LONG_n'),('SHORT PF','SHORT_PF'),('SHORT R','SHORT_R'),('SHORT n','SHORT_n')]),
        'Каждое направление каждого инструмента по каждому году и полному периоду сохранено в `direction_report.csv`.',
        '## Сохранённые тренды и устранённые убытки 2024',
        'Диагностическое определение крупного исходного трендового победителя заморожено: исходный Gross R ≥2. Сопоставление — точные инструмент/направление/время входа внутри соответствующей исходной конфигурации. «Полностью сохранён» означает совпадающий вход и итог не хуже исходного. Эти знания используются только после replay. Потерянный исходный вход не доказывает, что весь рыночный тренд отсутствовал в новых входах.',
        table(preserved,[('Контроль','version'),('Правило','rule'),('Исходных ≥2R','original_trend_winners'),('Полностью сохранено','trend_fully_preserved'),('Входов потеряно','trend_entries_lost'),('Итог уменьшен','trend_outcomes_reduced'),('Top10 сохранено','top10_preserved'),('Top10 входов потеряно','top10_lost')]),
        table(preserved,[('Контроль','version'),('Правило','rule'),('Убыточных входов устранено','loss_entries_eliminated'),('Убытков сокращено/обращено','losses_reduced_or_reversed'),('−R устранено','negative_R_eliminated_entries'),('−R сокращено','negative_R_reduced_matched'),('Новых входов','new_entries'),('−R новых входов','new_entry_negative_R')]),
        'Это сопоставление исходных входов, а не аддитивный эффект правила на весь рынок. `trade_lineage.csv` содержит каждую исходную сделку, включая открытые/несопоставленные; `winner_loss_changes.csv` — все положительные сделки, потерянные и уменьшенные R, оба года и каждый инструмент; `large_winners.csv` — отдельные исходные top5/top10 когорты. Новые отрицательные R показаны отдельно, поэтому удаление старых убытков не выдаётся за чистое улучшение.',
        'Исходные убыточные сделки с recorded MFE <0.5R выделены только для постфактум диагностики слабого продолжения (как в #491). Будущий MFE не участвует в правилах.',
        table(preserved,[('Контроль','version'),('Правило','rule'),('Исходных слабых убытков','original_weak_losses'),('Их −R','original_weak_negative_R'),('Входов устранено','weak_loss_entries_eliminated'),('Убытков сокращено','weak_losses_reduced_or_reversed'),('−R устранено','weak_negative_R_eliminated'),('−R сокращено','weak_negative_R_reduced')]),
        '## Зависимость от ноября 2024',
        table(pooled(november),[('Контроль','version'),('Правило','rule'),('R 2024','gross_R_2024'),('R ноября','november_R'),('Ноябрь / +R','november_share_positive_R'),('PF без ноября','ex_november_PF'),('R без ноября','ex_november_R'),('Плюс месяцев без ноября','ex_november_positive_months')]),
        'Удаление ноября — только постфактум чувствительность этого же полного replay; период эксперимента не сокращался. Полная инструментальная чувствительность также сохранена.',
        '## Замороженные механизмы',
        '\n'.join(f"- **{k} — {v['name']}**: {v['rule']}" for k,v in spec['experiments'].items()),
        'A2: пользователь заранее уточнил окно **первых четырёх** завершённых M15; окно не перебирали. A1 и A2 никогда не применяются одновременно.',
        '## Summary: исследовательский вывод',
        (HERE/'CONCLUSIONS.md').read_text() if (HERE/'CONCLUSIONS.md').exists() else 'Содержательная интерпретация будет заполнена после независимой сверки. Варианты не выбираются только по максимальному PF.',
        '## Причинность, ограничения и проверки',
        'Индикаторы доступны после завершения свечи; H1 предшественники определены на H1, Donchian сдвинут. Проверка Stop предшествует trailing; новые exit-решения исполняются только на следующем фактическом Open. Adverse Stop gap имеет приоритет на Open; будущий intrabar экстремум не меняет уже исполненный выход. Все дальнейшие входы и занятость пересчитаны. Нет искусственных цен и терминальной ликвидации. См. `CAUSALITY_REPORT.md`.',
        '**Вход по Close сигнальной свечи — исторический oracle, ещё не подтверждение физической исполнимости заявки по этому Close.** Stop остаётся непрерывным, без исправления сетки; соответствующая инженерная работа H1 отделена. Protective exits сохраняют исходную Close-метку свечи, точный intrabar timestamp неизвестен. Новый exit использует известный Open timestamp.',
        '2023–2024 уже изучались; это development-exposed исследовательская выборка, не новый независимый Walk Forward. 2025+ OHLC не читались. Не запускались Robustness, Walk Forward, TRUE OOS, Optimization или следующий пакет. PF не является гарантией. Отложены любые расходы и экономическая проверка перед реальным исполнением.',
        'Independent Audit: отдельный standard-library replay и арифметика тем же автором; внешний независимый аудит **PENDING**. `AUDIT_RESULTS.json` сверяет записи, решения, сигналы, отчёты и SHA-256. `TEST_RESULTS.txt` фиксирует смысловые тесты; `REPEATABILITY.json` — два свежих детерминированных повтора; `SCOPE_CHECK.json` — только новый каталог; `ARTIFACT_SHA256.json` — исходный код и финальные артефакты. Никаких изменений production, TradingSystemLab, прежних исследований, данных, брокерских endpoint, Merge или Auto-Merge.',
        '**STOP: отдельный Draft PR для внешнего аудита и решения пользователя. Следующий пакет автоматически не запускается.**']
    (HERE/'EXPERIMENT_REPORT.md').write_text('\n\n'.join(text)+'\n')
    print('EXPERIMENT_REPORT.md rendered')


if __name__ == '__main__':main()
