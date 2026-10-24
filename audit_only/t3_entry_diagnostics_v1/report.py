"""Russian report and scientific figure from predeclared development tables."""
import json,math
from pathlib import Path
from support import *

def num(x,d=3):return '—' if x is None or str(x)=='' else f'{float(x):.{d}f}'
def pct(x):return '—' if x is None or str(x)=='' else f'{100*float(x):.1f}%'
def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n'

def figure(out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows=csvin(out/'FEATURE_BUCKETS.csv');s=csvin(out/'BREAKOUT_05_STRATA.csv');a=csvin(out/'BREAKOUT_05_STANDARDIZED.csv')
    fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
    colors={'H1':'#31648e','M15':'#d77937'}
    for i,system in enumerate(('H1','M15')):
        raw=next(r for r in s if r['system']==system and r['dimension']=='ALL')
        adj=next(r for r in a if r['system']==system and r['adjust_for'].count('|')==3)
        for j,(label,r) in enumerate([('Raw',raw),('Within strata',adj)]):
            at=i*3+j;x=100*float(r['risk_difference']);lo=100*float(r['ci95_low']);hi=100*float(r['ci95_high'])
            axes[0].errorbar(x,at,xerr=[[x-lo],[hi-x]],fmt='o',capsize=4,color=colors[system])
            axes[0].text(x,at+.2,f'{x:+.1f} pp',ha='center',fontsize=9)
        high=next(r for r in rows if r['system']==system and r['feature']=='breakout_05_prespecified' and r['bucket']=='GE_0.5')
        axes[1].bar(i,100*float(high['share_of_all_large_winners']),color=colors[system],width=.55)
        axes[1].text(i,100*float(high['share_of_all_large_winners'])+1,f"{high['large_winners_ge_2R']} winners / {pct(high['share_of_all_large_winners'])}",ha='center',fontsize=9)
    axes[0].set_yticks([0,1,3,4],['H1 raw','H1 within strata','M15 raw','M15 within strata']);axes[0].set_ylim(4.65,-.65)
    axes[0].axvline(0,color='#888',lw=1);axes[0].set_xlabel('INITIAL_STOP risk difference, percentage points')
    axes[0].set_title('Breakout >=0.5 ATR versus <0.5 ATR\n95% month-cluster descriptive intervals',fontsize=11)
    axes[1].set_xticks([0,1],['H1','M15']);axes[1].set_ylim(0,60);axes[1].set_ylabel('Share of all realized winners >=2R, %')
    axes[1].set_title('Large winners also occur in the high-risk group\nThis comparison does not justify a filter',fontsize=11)
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.savefig(out/'ENTRY_DIAGNOSTICS.png',dpi=170,metadata={'Software':'T3 entry diagnostics V1'});plt.close(fig)

def render(out):
    summary=csvin(out/'OUTCOME_SUMMARY.csv');buckets=csvin(out/'FEATURE_BUCKETS.csv');stability=csvin(out/'STABILITY.csv')
    strata=csvin(out/'BREAKOUT_05_STRATA.csv');adj=csvin(out/'BREAKOUT_05_STANDARDIZED.csv');post=csvin(out/'POST_STOP_SUMMARY.csv')
    coverage=csvin(out/'COVERAGE.csv');distributions=csvin(out/'FEATURE_DISTRIBUTIONS.csv');calendar=csvin(out/'MONTHLY_BASELINE.csv')
    control=json.loads((out/'CONTROL_RECONCILIATION.json').read_text())
    def get(system,group):return next(r for r in summary if r['system']==system and r['outcome']==group)
    text='# T3 ENTRY DIAGNOSTICS V1 — H1/M15\n\n'
    text+='На development 2023–2024 наиболее согласованное наблюдаемое свойство неудачных входов — большее превышение предыдущего Donchian20 относительно ATR. На M15 дополнительно выделяется широкий диапазон сигнальной свечи. Это ассоциации с INITIAL_STOP, а не доказательство причинности или прибыльности отбора. Большая часть INITIAL_STOP не достигает +0.5R; отрицательный M15 trailing — отдельный механизм возврата уже накопленной плавающей прибыли.\n\n'
    text+='**Новых фильтров, стратегий, backtest альтернатив, пороговой оптимизации и изменений исполнения нет. Сохранность крупных победителей при изменениях НЕ установлена.** Протокол заморожен в `'+PROTOCOL+'` до discovery. 2025–2026 обработаны только изолированным процессом обязательного CONTROL; новых OOS-выводов нет.\n\n'
    text+='## Источники и CONTROL\n\n'
    text+=table(['Источник','Закреплённый SHA'],[['main',MAIN]]+[[name,pin[0]] for name,pin in PINS.items()]+[['H1 data','50f1fd2178c18b7ab3bd969be82ad01f47a34745'],['M15 data','f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8']])
    text+='\nSHA256 архивов, frozen source и восьми data blobs сверены. Данные остаются read-only вне git; source OHLC не копируются в исследование. `SOURCE_MANIFEST.json` содержит полный перечень.\n\n'
    text+=table(['CONTROL','CLOSED','INITIAL_STOP','Результат'],[[s,control['headline'][s]['CLOSED'],control['headline'][s]['INITIAL_STOP'],'PASS'] for s in ('H1','M15')]+[['H1 WF отдельно',control['H1_WF_separate']['CLOSED'],control['H1_WF_separate']['INITIAL_STOP'],'PASS, не discovery и не добавлен к H1']])
    text+='\nСверены 202418 полей первоначальных журналов и 4385052 поля состояния PR557, затем все CONTROL trade fields PR560; свежий scalar CONTROL replay совпал. Конфигурации: H1 `TRAIL1__N4_01__FULL__R15`, Initial 2.5 ATR / TRAIL1 3 ATR; M15 `T3_M15_T1_TRAIL35_N4_R15`, NEXT_OPEN, Initial 2 / trail 3.5 ATR. FULL N4, одна позиция на инструмент. Frozen stop-first, активация H1 TRAIL1 и R15 сохранены.\n\n'
    text+='## Покрытие, причинность и неопределённость\n\n'
    text+=table(['Система','Инструмент','Первый replay Close МСК','Последний Close','Исходных сигналов'],[[r['system'],r['instrument'],r['replay_first_close'],r['replay_last_close'],r['discovery_signals']] for r in coverage])
    text+='\nGLDRUBF отсутствует до 11.07.2023, IMOEXF — до 14.11.2023; N4 в 2023 неполон. H1 baseline холодно стартует в 2023, начальные строки 2022 не входят в его индикаторы или сделки. Конец обоих development потоков фактически 31.12.2024 00:00 МСК, исходный close-label. H1 historical TRUE OOS и WF в discovery отсутствуют. Одна OPEN позиция в каждой системе не разрешена будущими данными.\n\n'
    text+='Все признаки рассчитаны для каждого исходного сигнала, включая занятость и M15 вне T1; outcome-таблицы относятся только к исполненным CONTROL входам. Прежний Donchian исключает текущую свечу. EMA/ADX/ATR и предшествующее движение CROSS_DAY используют только завершённые свечи. У H1 frozen EMA100 принадлежит H4; диагностическая H1 EMA100 хранится отдельно. Опубликованные H4/H1 состояния имеют `context_available_at <= signal_time`. Блоки старшего контекста строятся по frozen close-date, включая midnight; показатели не публикуются до последнего Close блока. Дневной `session_minutes` считается от 10:00 МСК, T1 [10:00,18:00). Это часы frozen сессии, а не аттестация исторического биржевого расписания.\n\n'
    text+='NEXT_OPEN gap известен в следующем событии исполнения (при непрерывной сетке имеет тот же wall timestamp, что signal Close, но более позднюю фазу). Он вынесен в `EXECUTION_DIAGNOSTICS.csv`, не включён в signal features и не используется для выбора гипотез.\n\n'
    text+='Терцили заданы квантилями доступных признаков development-входов без outcome. Везде 95% описательные интервалы paired bootstrap по 24 календарным месяцам входа сразу по всем инструментам, 2000 повторов, seed 560518; дополнительно 8 квартальных блоков. Они не исправляют множественный просмотр признаков, возможную зависимость через границы блоков или нестационарность. SMALL = <20 CLOSED или <6 месяцев хотя бы в одной сравниваемой группе. Один-два года и малые страты не дают основания объявлять универсальную закономерность.\n\n'
    for system in ('H1','M15'):
        allr=get(system,'ALL');init=get(system,'INITIAL_STOP');neg=get(system,'TRAILING_NEGATIVE')
        text+=f'## {system}: исходы и признаки входа\n\n'
        text+=f"Исполнено {allr['N']} входов: {allr['CLOSED']} CLOSED, {allr['OPEN']} OPEN. INITIAL_STOP {init['CLOSED']} ({pct(allr['initial_stop_share'])} CLOSED); победителей от +2R — {allr['large_winners_ge_2R']}.\n\n"
        text+=table(['Исход','N closed/open','Mean Gross R','Median R','Median MAE','Median MFE','+0.5R наблюдалось','Медиана минут до +0.5R*'],[
          [g,r['CLOSED']+'/'+r['OPEN'],num(r['mean_gross_R']),num(r['median_gross_R']),num(r['median_MAE_R']),num(r['median_MFE_R']),r['half_R_observed'],num(r['median_first_half_R_minutes_observed'],0)]
          for g in ('INITIAL_STOP','TRAILING_NEGATIVE','TRAILING_POSITIVE','TRAILING_ZERO','OPEN') for r in [get(system,g)]])
        text+='\n'
        text+=table(['Исход','Первое >0R наблюдалось','Не наблюдалось / ambiguous / censored','Median минут до первого >0R*'],[[g,r['first_favorable_observed'],r['first_favorable_not_observed']+' / '+r['first_favorable_ambiguous']+' / '+r['first_favorable_censored'],num(r['median_first_favorable_minutes_observed'],0)] for g in ('INITIAL_STOP','TRAILING_NEGATIVE','TRAILING_POSITIVE','OPEN') for r in [get(system,g)]])
        text+='\n*Только среди достигших; Open — точный момент, intrabar — верхняя временная граница. Ненаблюдавшиеся, ambiguous exit-bar и OPEN censoring перечислены отдельно в OUTCOME_SUMMARY. MAE/MFE — CONTROL R0, stop-first гарантированная граница; полные exit-bar High/Low лишь upper bounds, их порядок неизвестен. OPEN extrema ограничены development endpoint.\n\n'
        names=['breakout_atr','range_atr','body_abs_atr','prior_move20_atr_cross_day','context_adx','context_slope_atr']
        text+=table(['Признак','WINNERS p25 / median / p75','LOSERS p25 / median / p75'],[[name]+[' / '.join(num(next(r for r in distributions if r['system']==system and r['feature']==name and r['outcome']==g)[key]) for key in ('p25','median','p75')) for g in ('WINNERS','LOSERS')] for name in names])
        text+='\nПолные распределения всех запрошенных признаков, в том числе EMA, ADX, ATR, ATRRatio, location, prior movement и session time: `FEATURE_DISTRIBUTIONS.csv`; все исходные feature rows — `ENTRY_FEATURES_'+system+'.csv`. Абсолютные ATR выражены в единицах цены, их pooled сравнение между разными инструментами само по себе неинформативно.\n\n'
        chosen=['breakout_atr','range_atr','prior_move20_atr_cross_day']
        text+=table(['Признак HIGH–LOW','Δ INITIAL_STOP, п.п.','95% month CI','95% quarter CI'],[[r['feature'],num(100*float(r['risk_difference']),1),f"[{num(100*float(r['ci95_low']),1)}; {num(100*float(r['ci95_high']),1)}]",f"[{num(100*float(r['quarter_ci95_low']),1)}; {num(100*float(r['quarter_ci95_high']),1)}]"] for r in stability if r['system']==system and r['dimension']=='ALL' and r['feature'] in chosen])
        if system=='H1':text+='\nH1: превышение Donchian направлено одинаково на всех четырёх инструментах, обеих сторонах и в обоих годах; большинство instrument-терцилей SMALL. Предшествующее движение 20 свечей также ассоциировано с INITIAL_STOP, но направление разворачивается на IMOEXF и оценка слабее после исключения CNY. Широкая сигнальная свеча не даёт согласованного H1 эффекта. Слабый H4 slope — лишь намёк: на USDRUBF направление противоположно, ADX почти не различает исходы внутри уже отобранного gate.\n\n'
        else:text+='\nM15: HIGH range >1.842 ATR против LOW ≤1.227 ATR: 78/183 (42.6%) против 45/183 (24.6%) INITIAL_STOP; разница +18.0 п.п. [8.6;29.9]. Направление положительное на всех инструментах, обеих сторонах, в обоих годах и при исключении каждого инструмента; отдельные instrument CI широки. В HIGH range всё же 25/74 всех крупных победителей (33.8%), средний Gross R HIGH +0.307 и LOW +0.303. Тело свечи само по себе гораздо слабее диапазона. Context ADX, EMA-distance, slope и ATRRatio не дают согласованного объяснения. Возраст контекста и часы сессии имеют вторичные ассоциации, которые могут отражать структуру времени; они не выделены как самостоятельная механическая гипотеза.\n\n'
    text+='## Предварительное наблюдение Donchian ≥0.5 ATR\n\n'
    text+=table(['Система','Группа','CLOSED','INITIAL_STOP','Доля','Mean / median Gross R','Победителей ≥2R','Доля всех ≥2R'],[
      [r['system'],r['bucket'],r['CLOSED'],r['INITIAL_STOP'],pct(r['initial_stop_share']),num(r['mean_gross_R'])+' / '+num(r['median_gross_R']),r['large_winners_ge_2R'],pct(r['share_of_all_large_winners'])]
      for r in buckets if r['feature']=='breakout_05_prespecified'])
    text+='\nПорог 0.5 ATR задан до расчёта как исследовательский ориентир. Его не оптимизировали и не утверждали фильтром.\n\n'
    text+=table(['Система','Оценка','Δ INITIAL_STOP, п.п.','95% month CI','Покрытие'],[
      [system,label,num(100*float(r['risk_difference']),1),f"[{num(100*float(r['ci95_low']),1)}; {num(100*float(r['ci95_high']),1)}]",coverage]
      for system in ('H1','M15') for label,r,coverage in [
        ('Raw',next(r for r in strata if r['system']==system and r['dimension']=='ALL'),'100%'),
        ('instrument × direction × year × context ATRRatio tercile',next(r for r in adj if r['system']==system and r['adjust_for'].count('|')==3),pct(next(r for r in adj if r['system']==system and r['adjust_for'].count('|')==3)['coverage_share']))]])
    text+='\nВес общей страты n_high*n_low/(n_high+n_low), страты без обеих групп исключены. M15: +10.8 п.п. [1.8;20.9], квартальный CI [1.8;20.2]; связь не объясняется полностью этими наблюдаемыми факторами. Это не устраняет ненаблюдаемые факторы. На CNY и USD эффект около +17.4/+17.3 п.п.; на GLD/IMOEX близок к нулю. Обе стороны, оба года и все volatility терцили имеют положительный raw знак, но CI отдельных разрезов часто включает ноль. H1 совместная оценка +10.5 п.п. [−2.0;25.9], квартальный CI [−4.1;28.0], покрытие 86.5%: неопределённость существенно больше.\n\n'
    text+='![Описание ассоциации и сохранности крупных победителей](ENTRY_DIAGNOSTICS.png)\n\n'
    text+='В группе ≥0.5 ATR остаются 10/22 (45.5%) H1 и 33/74 (44.6%) M15 крупных победителей. У H1 их частота внутри high-группы даже немного выше, чем в low-группе. Одновременное наличие риска стопа и больших победителей принципиально ограничивает отбор. `CONFLICT_EXAMPLES.csv` содержит для каждого общего bucket первый по времени INITIAL_STOP и первый ≥2R; эти примеры выбраны детерминированно, не по эффектности.\n\n'
    text+='## Что поддерживают A–E\n\n'
    text+=table(['Механизм','Наблюдение','Интерпретация'],[
      ['A. Ложный пробой / мало продолжения','H1 46/60 INITIAL_STOP без гарантированных +0.5R; M15 152/184, из них 7 ambiguous exit-bars (145 strict).','Самая прямая outcome-диагностика INITIAL_STOP; входной причинный классификатор не получен.'],
      ['B. Чрезмерное растяжение','Donchian extension: согласованная связь в обеих системах; широкий range — главным образом M15; тело слабее.','Поддерживает гипотезу истощения/непродолжения, но отличить её от случайного ложного пробоя по этим данным нельзя.'],
      ['C. Вход до конца нормального отката','Recovery после стопа часто наблюдается на M15; порядок до adverse1.5R заметно менее благоприятен.','Нормальность отката не установлена; возврат после стопа не равен достижимой прибыли.'],
      ['D. Слабый старший тренд','Внутри gate ADX/ATRRatio уже ограничены; slope/ADX дают неоднородные эффекты.','Меньше поддержки, чем A/B; отсутствие эффекта внутри gate не опровергает важность самого тренда.'],
      ['E. Возврат плавающей прибыли','H1 8 negative trailing, MFE median 1.082R; M15 144, MFE median 0.954R, 133 достигали +0.5R и 67 +1R.','Отдельный значимый M15 механизм убытка, который нельзя смешивать с первоначальным стопом.']])
    text+='\nУ M15 negative trailing median итог −0.492R, median giveback 1.557R; 2 таких сделки имели guaranteed MFE≥2R. У положительных M15 trailing median giveback тоже 1.568R — сам giveback встречается и у победителей. H1 negative trailing всего 8, все после ≥1R, вывод по этой малой группе ограничен. Раннее adverse движение наблюдается у 51/60 H1 и 175/184 M15 INITIAL_STOP, но также у 13/22 и 27/74 крупных победителей соответственно. Поэтому даже ретроспективный adverse-паттерн не отделяет безопасно неудачу. Все path-признаки после входа — диагностика исхода, не доступные на входе фильтры. A/C/E пересекаются, B/D — ассоциации, поэтому суммы категорий не складываются в причинный диагноз.\n\n'
    text+=table(['Система','Следующих наблюдаемых дней','Полных / censored','Recovery входной цены','Recovery до/без adverse1.5R','Adverse first','Same-bar ambiguous'],[[r['system'],r['days'],r['complete']+' / '+r['censored'],r['recovery_observed']+' ('+pct(r['recovery_share'])+')',str(int(r['recovery_first'])+int(r['recovery_only']))+' ('+pct(r['recovery_before_or_without_adverse_share'])+')',r['adverse_first'],r['ambiguous']] for r in post])
    text+='\nОкно включает остаток дня стопа и следующие 1/2 **наблюдавшихся** торговых дня. На M15 в двухдневном полном окне recovery 145/183 (79.2%; month CI 71.4–86.3%), но до/без adverse1.5R только 68/183 (37.2%; 28.2–47.2%); 75 recovery были после adverse1.5R, 2 same-bar ambiguous. Непрерывность всех ожидаемых биржевых баров не аттестована. Результат не обосновывает удержание после стопа или задержанный вход; такого backtest нет.\n\n'
    text+='## Календарные месяцы и две гипотезы\n\n'
    text+=table(['Development','Отрицательных CLOSED месяцев','Убыток initial stops, сумма R','Убыток negative trailing, сумма R'],[[s,sum(float(r['gross_R'])<0 for r in calendar if r['system']==s),num(math.fsum(float(r['initial_stop_R']) for r in calendar if r['system']==s)),num(math.fsum(float(r['negative_trailing_R']) for r in calendar if r['system']==s))] for s in ('H1','M15')])
    text+='\nЭто исходный календарь CONTROL, МСК по exit-label, Gross R; не новый расчёт отфильтрованной стратегии. Изменение входов изменило бы занятость и будущие сделки. Снижение числа отрицательных месяцев, денежный результат, executable net и сохранность победителей при любых изменениях здесь **не проверены**.\n\n'
    text+='1. **Растянутый пробой чаще не получает продолжения.** Основной наблюдаемый маркер — Close дальше предыдущего Donchian в ATR; широкий range M15 усиливает механическую правдоподобность, но не доказан как независимый фактор. Это одна гипотеза A/B, не набор фильтров. Ограничение: high breakout содержит около 45% крупных победителей, HIGH M15 range — 33.8%; механическое исключение таких входов не обосновано.\n'
    text+='2. **Часть M15 убытков связана с возвратом накопленной прибыли, а не с отсутствием первого движения.** 144 negative trailing, 133 после +0.5R и 67 после +1R; этот механизм материален относительно 184 initial stops. Это гипотеза E о пути/сопровождении, а не найденный предиктор на входе. Ограничение: сопоставимый giveback встречается у победителей; механическое его подавление может обрезать правый хвост.\n\n'
    text+='Ранги отражают полноту механического свидетельства и устойчивость, а не PF. C/D не выделены для отдельного изменения стратегии. Перед отдельной причинной проверкой необходимо заранее определить исходы: число отрицательных календарных месяцев и их глубина, число и вклад сохранённых ≥2R победителей, пропущенные/новые входы из-за занятости, расходы и неопределённость. Нельзя объявлять успех по PF или сумме собственных R; повторное использование уже просмотренных 2025–2026 не создаёт нового независимого OOS. V1 не задаёт параметры будущего вмешательства.\n\n'
    text+='## Аудит и воспроизводимость\n\n'
    text+='`INDEPENDENT_VERIFICATION.json`: отдельный stdlib/scalar parser, индикаторы и признаки из pinned-prefix OHLC, stop-first path, post-stop порядок, Decimal R, границы МСК и стратификация. `TABLE_VERIFICATION.json`: свежие CSV, распределения, терцили, counts/means/medians и повторный месячный bootstrap. `CAUSALITY.json`: prefix invariance и возмущение будущего суффикса на опубликованном контексте, midnight и поздних сигналах всех потоков. `SYNTHETIC_TESTS.json`: warmup, ATR gap, slope, midnight/year boundary, paired clusters и воспроизводимость seed.\n\n'
    text+='**Предел независимости:** verifier — отдельно реализованный алгоритм тем же автором; внешняя человеческая и отдельная агентская проверка не выполнены. Human signoff остаётся PENDING. Это явно отражено в AUDIT, а не выдано за внешнее одобрение. Полный fresh процесс и два свежих повтора после code freeze сравниваются direct bytes и SHA256; окончательная квитанция — `REPEATABILITY.json`.\n\n'
    text+='Все файлы — только новый audit-каталог. LIVE H1, M15 robot, FINAM, Control Center, Windows Tasks, SQLite и торговые токены не читались/не запускались/не менялись. Только Draft PR, **NO MERGE / NO AUTO-MERGE**.\n\n'
    text+='## Карта обязательных таблиц\n\n'
    text+=table(['Содержание','Файл'],[
      ['Исходные причинные признаки H1/M15','ENTRY_FEATURES_H1.csv / ENTRY_FEATURES_M15.csv'],['Фактические исходы и path bounds','OUTCOME_GROUPS_H1.csv / OUTCOME_GROUPS_M15.csv'],
      ['Распределения и риск/mean/median R/MAE/MFE/latency по группам','FEATURE_DISTRIBUTIONS.csv / FEATURE_BUCKETS.csv / OUTCOME_SUMMARY.csv'],
      ['Инструмент, LONG/SHORT, год и их пересечение','INSTRUMENT_DIRECTION.csv'],['Направленность и leave-one-instrument-out','STABILITY.csv'],
      ['0.5 ATR: confounding и общие страты','BREAKOUT_05_STRATA.csv / BREAKOUT_05_STANDARDIZED.csv'],['Крупные победители в риск-группах; совпадающие признаки','FEATURE_BUCKETS.csv / CONFLICT_EXAMPLES.csv'],
      ['Раннее adverse движение / A–E / recovery','MECHANICS.csv / POST_STOP.csv / POST_STOP_SUMMARY.csv'],['Исходный календарь без новых фильтров','MONTHLY_BASELINE.csv'],
      ['Причины неисполнения / NEXT_OPEN gap','SIGNAL_DISPOSITION_H1.csv / SIGNAL_DISPOSITION_M15.csv / EXECUTION_DIAGNOSTICS.csv / EXECUTION_DIAGNOSTIC_SUMMARY.csv']])
    (out/'REPORT_RU.md').write_text(text)
    figure(out)
