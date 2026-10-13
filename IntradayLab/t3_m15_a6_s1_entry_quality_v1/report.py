"""Russian presentation of already audited slices; no trade or signal changes."""
import argparse,json,math
from pathlib import Path
import pandas as pd
import common as C


def supplement(t):
    f=pd.DataFrame(t['trade_features']);rows=[]
    for y in (2023,2024):
        for d in ('LONG','SHORT'):
            group=f.loc[(f.exit_year==y)&(f.direction==d)]
            for label,lo,hi in [('LT_0_5',0,.5),('0_5_TO_1',.5,1),('1_TO_2',1,2),('GE2_MFE',2,math.inf)]:
                part=group.loc[(group.MFE_R>=lo)&(group.MFE_R<hi)]
                rows.append({'year':y,'direction':d,'MFE_band':label,'closed':len(part),'fraction':len(part)/len(group),'gross_R':float(part.gross_R.sum()),'initial_no_s1':int(part.initial_no_s1.sum()),'losses':int((part.gross_R<0).sum())})
    focus=[]
    for m in ('2024-05','2024-10'):
        for d in ('ALL','LONG','SHORT'):
            part=f.loc[(f.signal_month==m)&((f.direction==d) if d!='ALL' else True)]
            focus.append({'signal_month':m,'direction':d,'closed':len(part),'gross_R':float(part.gross_R.sum()),'initial_no_s1':int(part.initial_no_s1.sum()),'failed_lower_MFE':int(part.failed_lower_MFE.sum()),'GE2':int(part.GE2.sum()),'GE5':int(part.GE5.sum()),'exit_other_month':int((part.exit_month!=m).sum())})
    extreme=[]
    for y in (2023,2024):
        part=f.loc[(f.signal_year==y)&(f.direction=='SHORT')&(f.H1ATRRatio>=1.25)]
        extreme.append({'year':y,'closed':len(part),'gross_R':float(part.gross_R.sum()),'days':part.signal_date.nunique(),'months':part.signal_month.nunique(),'initial_no_s1':int(part.initial_no_s1.sum()),'S1_activated':int(part.threshold_activated.sum()),'MFE_GE2':int((part.MFE_R>=2).sum()),'GE2':int(part.GE2.sum()),'GE5':int(part.GE5.sum()),'may_2024_entries':int((part.signal_month=='2024-05').sum()),'oct_2024_entries':int((part.signal_month=='2024-10').sum())})
    return {'MFE_bands':rows,'focus_signal_cohorts':focus,'extreme_ratio_SHORT':extreme}


def fmt(v):
    if v is None:return '—'
    if isinstance(v,float):return f'{v:.6f}'
    return str(v)


def run(results,audit):
    t=json.loads((results/'TABLES.json').read_text());s=supplement(t);C.write_json(results/'REPORT_SUPPLEMENT.json',s)
    sources=t|s;manifest=[];table_counter=0
    def table(source,predicate,columns):
        nonlocal table_counter
        table_counter+=1;indices=[i for i,r in enumerate(sources[source]) if predicate(r)];rows=[sources[source][i] for i in indices]
        ident=f'T{table_counter:03d}';manifest.append({'id':ident,'source':source,'indices':indices,'columns':columns})
        lines=[f'<!-- table:{ident} -->','| '+' | '.join(columns)+' |','| '+' | '.join('---' for _ in columns)+' |']
        lines+=['| '+' | '.join(fmt(r.get(k)) for k in columns)+' |' for r in rows]
        return '\n'.join(lines)+'\n'
    main=[]
    def add(x):main.append(x.strip()+'\n')
    add('# A6+S1 / TRAIL_375 — качество входов T3/M15 за 2023–2024')
    add('**Конкретная слабость SHORT 2024 — меньшая доля выигрышных входов и частый возврат после промежуточного движения 0,5–1 первоначального R до активации S1. Однако проверенные доступные признаки не дают убедительного общего различителя, сохраняющего крупные тренды и объясняющего май/октябрь. Итог: `NO_SUPPORTED_ENTRY_CHANGE`. Следующий изменённый causal replay не рекомендуется в рамках имеющихся свидетельств.**')
    add('**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.** Только исходная стратегия; фильтры и параметры не менялись. Торговые операции, Optimization, Robustness, Walk Forward и TRUE OOS не выполнялись.')
    add('## CONTROL, источники и календарь')
    add('Actual GitHub main при начале — `57599b39ed1d7a93a84b97747388408291f30276`, Merge #506. #505 и #506 уже MERGED; прежний SHA задания `0546e10…` соответствует Merge #505. Данные read-only — `market-pattern-data/forever/`, commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. ROADMAP и предыдущая диагностика T1+S1 прочитаны; её результаты не переносятся на эту архитектуру.')
    add('Engine/scalar и обе реализации метрик побайтно совпадают с #506/#505. CONTROL прошёл полную сверку 480 CLOSED, 1 terminal OPEN, 12 478 Stop и 2 017 signal decisions с обоими PR; feature-control проверил все 98 305 M15. Полные журналы, включая gaps, первоначальные и изменённые Stops, period OPEN, terminal OPEN — [control/](control/). Все checkpoint PF/R и май/октябрь совпали; диагностический код недоступен до успешных двух CONTROL gates.')
    add(table('summary',lambda r:r['scope']=='ALL_FOUR' and r['direction']=='ALL',['year','closed','terminal_OPEN','gross_PF','gross_R','positive_months','months','closed_R_drawdown']))
    add('Заморожены EMA75/slope5, H1 ADX14>20, H1 ATR14/mean20>1 и A6 `ATRRatio > PreviousATRRatio`, Donchian20 prior-only, первоначальный Stop=2 ATR сигнала, S1 activation=1 initial R, trailing=3,75 ATR. T1 отсутствует. H1 — дневной ordinal-блок четырёх последовательных M15, публикация на четвёртом Close; рекурсии и Donchian пересекают дни. Pending вход исполняется на строго соседнем Open; при пропуске — skip. Stop-first, пережитый Close, затем обновление для следующего наблюдаемого бара; same-close reentry/occupancy сохранены.')
    add('Год/месяц экономики — exit Close MSK; дата/время доступного сигнала — signal Close MSK. Историческая Close-метка выхода не определяет точное intrabar время fill. OPEN не ликвидирован и не входит в PF/R. DD — сумма CLOSED R с нулевого начального уровня, exit_time/instrument/trade_id; это не просадка капитала/MTM. GLD доступен с июля 2023, IMOEX с ноября; полный denominator 24 месяца и NO_COVERAGE сохранены в [monthly.csv](monthly.csv).')
    add('## Что именно ухудшает SHORT 2024')
    add(table('summary',lambda r:r['scope']=='ALL_FOUR' and r['direction']!='ALL' and r['year']!='ALL',['year','direction','closed','gross_PF','gross_R','win_fraction','mean_WIN_R','mean_LOSS_R','initial_no_s1','failed_lower_MFE','MFE_GE2','GE2','GE5']))
    add('SHORT 2024 выигрывает 55/148 (37,1622%), LONG 83/167 (49,7006%). При этом средний SHORT выигрыш **выше**, 2,168251R против 1,940396R, а средний убыток по модулю **меньше**, 0,870242R против 0,919550R. Разрыв возникает в частоте успешных входов, а не от худшей величины каждого убытка или малого среднего выигрыша. SHORT 2023 PF2,174044 почти равен LONG2,231690; постоянной непригодности SHORT нет.')
    add('Первоначальный Stop без S1: SHORT69/148=46,6216%, LONG67/167=40,1198%. Он даёт SHORT −69,532773R, 85,9145% всех отрицательных SHORT R. Но мгновенно слабые LOSS с нижней MFE<0,5R **реже** у SHORT: 37/148=25%, LONG51/167=30,5389%. Поэтому тезис «SHORT хуже только из-за немедленно ложных пробоев» неверен.')
    add(table('MFE_bands',lambda r:True,['year','direction','MFE_band','closed','fraction','gross_R','initial_no_s1','losses']))
    add('Ключевая разница — промежуточное продолжение: 32 SHORT2024 показали наблюдаемые 0,5≤MFE<1R, затем потеряли ровно −32R на первоначальном Stop; LONG имеет16 таких сделок. Доли 21,6216% против9,5808%; SHORT2023 —7/68=10,2941%. CNY имеет9/36, IMOEX13/53, GLD4/25 таких SHORT2024. Сохранённый причинный механизм исполнения объясняет результат: до завершённой пережитой свечи с +1 initial R S1 не активируется, Stop остаётся исходным. Уменьшать этот порог или Stop здесь не разрешено и этим диагнозом не обосновано.')
    add('MFE — **нижняя наблюдаемая оценка**, extrema Stop-свечи исключены. Эти категории не доказывают отсутствия более высокого intrabar движения и не доступны при входе. S1 также не гарантирует сразу сдвинутый Stop: 2024 имеет 2 LONG и1 SHORT INITIAL_STOP уже после активации, отдельно в [outcome_anatomy.csv](outcome_anatomy.csv).')
    add(table('summary',lambda r:r['scope'] in C.SYMBOLS and r['direction']!='ALL' and r['year']!='ALL',['scope','year','direction','closed','gross_PF','gross_R','win_fraction','initial_no_s1','GE2','GE5']))
    add('CNY SHORT2024: PF1,357551, WIN13/36, первоначальный Stop18/36; IMOEX: PF1,240522, WIN18/53, Stop25/53. GLD: PF2,262983, WIN11/25, Stop8/25 и менее тяжёлый mean loss −0,712385R. Успешный GLD не объясняется только большим средним победителем: mean win2,051783R близок IMOEX2,035956R. USD SHORT тоже ухудшается с PF2,648390 до1,539364. SHORT FX полного покрытия падает с2,757549 до1,449561: расширение доли IMOEX не объясняет весь эффект. Инструментальные исключения не предлагаются.')
    add(table('matched_cohorts',lambda r:r['direction']=='SHORT',['scope','year','matched_days','closed','gross_PF','gross_R','initial_no_s1_fraction']))
    add('Matched MM-DD использует даты с хотя бы одной M15 с готовым H1/ATR в обоих годах; точные639 instrument/date pairs — [matched_dates.csv](matched_dates.csv). Это не одинаковое intraday покрытие или независимая выборка; только проверка календарного смешения полного пути. USD/CNY остаются хуже в2024, GLD лучше. IMOEX2023 всего6 SHORT, matched2024 всего4: универсальная межгодовая закономерность по IMOEX не доказана.')
    add('## Какие известные признаки это объясняют — и где объяснение не работает')
    add('Все available fields построены из завершённого signal M15 и опубликованного H1. dADX/slope/dATRRatio сравнивают предыдущий опубликованный H1; directed slope нормирован на **M15 ATR сигнала**, что явно отражено в имени. Отдельно есть ATR/Close %, prior Donchian превышение/ATR, час и возраст H1. NEXT_OPEN High/Low/Close, MFE/MAE и финальный R не участвуют ни в одном available field. Bins заранее описаны в SPEC/PROTOCOL; ни один новый фильтр не replayed.')
    add(table('cuts',lambda r:r['scope']=='ALL_FOUR' and r['direction']=='SHORT' and r['year']!='ALL' and r['feature'] in ['H1ADX','H1ATRRatio','dATRRatio','ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING'],['year','feature','bin','closed','gross_PF','gross_R','initial_no_s1_fraction','GE2','GE5']))
    add('ADX B0=20–30, B1=30–40, B2≥40. SHORT ADX30–40 в2024:37 сделок, −18,000426R, PF0,298178; CNY9/−5,827682R и IMOEX15/−8,933334R. Это конкретная слабая входная среда, но в2023 эта же группа18/+8,148227R, PF1,998998 и3≥2R/1≥5R. Низкий ADX20–30 в2024, наоборот, содержит14≥2R и4≥5R SHORT, включая сильный IMOEX SHORT сADX20,643011. Ужесточение ADX уничтожает часть работающих ранних трендов; «больше ADX — лучше» не подтверждено.')
    add('ATRRatio B0=1–1,10, B1=1,10–1,25, B2≥1,25. Умеренное расширение B1 хорошо в2024, но B0 лучше в2023; B0 в2024 всё ещё содержит11≥2R/2≥5R SHORT. dATRRatio B0<.025 в2024 отрицателен, но в2023 +12,849760R и2≥5R. Все исполненные входы уже проходят A6: факт роста отношения не объясняет, какой пробой сохранит тренд. У GLD WIN/LOSS ratio median1,099409/1,049927; у IMOEX1,064336/1,084594: даже знак этой связи зависит от рынка.')
    add('Slope strengthening=False SHORT лучше по PF в обоих годах (3,965747/2,223018), но малая выборка10/20; это не поддерживает требование усиливающейся slope. Вся False-группа обоих направлений содержит13≥2R/6≥5R. ADX rising SHORT в2024 PF1,457847 против1,524369 non-rising, а M15 ATR rising1,426571 против1,702911. Требовать эти признаки ради улучшения входов оснований нет. Распределения WIN/LOSS пересекаются — [feature_distributions.csv](feature_distributions.csv).')
    add(table('cuts',lambda r:r['scope']=='ALL_FOUR' and r['direction']=='SHORT' and r['year']!='ALL' and r['feature'] in ['breakout_ATR','signed_slope_M15ATR','ATR_pct','HOUR'],['year','feature','bin','closed','gross_PF','gross_R','initial_no_s1_fraction','GE2','GE5']))
    add('Breakout B0<.25, B1=.25–.5, B2=.5–1, B3≥1 ATR. Малые пробои B0 в2023 имеют61,5% первоначальных Stop, но в2024 группа прибыльна и содержит9≥2R; большие B3 в2024 почти без net R, но всё ещё3≥2R/1≥5R SHORT. Исходный сильный тренд не определяется одним размером breakout. Slope B0<.5/B1=.5–1/B2≥1 M15 ATR; ATR_pct B0<.1/B1=.1–.2/B2=.2–.4/B3≥.4%. Эти связи меняются годом и инструментом. Часы10–12 SHORT дают +34,148802R в2023 и −7,896381R в2024, после18 −6,181920R и +11,035919R. Запрет часов по2024 — подгонка.')
    add('На следующих4 соседних M15 у SHORT2024 Close-возврат за Donchian встречается84/148=56,7568% против43,4783% всех входов2023 (и44,7761% SHORT2023). Однако SHORT2024 без благоприятного1ATR за час —42,5676%, SHORT2023 —49,2537%. Быстрый импульс может быть, а устойчивого продолжения нет; полное исчезновение трендов не установлено. Future окна не являются торговой MFE: Stop переживать не обязаны, окна через gap/дату CENSORED. По всем годам7 из480 CLOSED окон цензурированы; каждый raw signal и его причина/окно доступны в [signal_features.csv](signal_features.csv).')
    add('## Май и октябрь 2024')
    add(table('monthly',lambda r:r['scope']=='ALL_FOUR' and r['month'] in ['2024-05','2024-10'],['month','direction','closed','gross_PF','gross_R','initial_no_s1','failed_lower_MFE','GE2','GE5']))
    add(table('monthly',lambda r:r['scope'] in C.SYMBOLS and r['direction']=='ALL' and r['month'] in ['2024-05','2024-10'],['month','scope','closed','gross_R','initial_no_s1','failed_lower_MFE','GE2','GE5']))
    add('Май:25/27 CLOSED —SHORT (92,5926%); SHORT −2,985895R, LONG +0,113054R. CNY −3,233359R, USD −1,069253R, GLD −0,348821R; IMOEX +1,778592R частично компенсирует. Только5 LOSS с нижнейMFE<.5R, поэтому месяц не сводится к немедленно неудачным пробоям:10 SHORT первоначальных Stop безS1,5 SHORT ratcheted losses,10 SHORT выигрышей, всего2≥2R и0≥5R. Наблюдаемые импульсы часто не стали крупными реализованными трендами.')
    add('Октябрь:9/26 SHORT (34,6154%), −7,955777R против LONG +8,165675R; 8/9 SHORT —первоначальный Stop безS1. IMOEX5/5 SHORT=−5R, USD2/2=−2R, CNY2=−0,955777R, GLD SHORT нет. Из8 первоначальных SHORT Stop четыре имеют нижнююMFE .5–1R, четыре<.5R. Месяц около нуля благодаря3≥2R LONG, включая1≥5R. Это концентрированный провалSHORT с компенсацией LONG, а не отсутствие трендов на всех рынках.')
    add(table('focus_signal_cohorts',lambda r:True,['signal_month','direction','closed','gross_R','initial_no_s1','failed_lower_MFE','GE2','GE5','exit_other_month']))
    add('Майская когорта сигналов даёт +0,591181R по последующим полным исходам, тогда как cash exit-месяц −2,872841R. Разницу образуют GLD вход30апреля/выход2мая −0,355777R и IMOEX вход30мая/выход3июня +3,108244R. Октябрьские26 signal/exit cohort совпадают. Не смешивать календарь входа и календарь результата. Все27+26 exit-месячных сделок сохранены, никакие плохие исходы не исключены.')
    add('## Сильные тренды и единственный итог исследования')
    add('Исходная стратегия содержит83 CLOSED≥2R и21≥5R. Каждому известному разрезу сопоставлены **все** оригинальные winner IDs и доли: [winner_entries.csv](winner_entries.csv), [cuts.csv](cuts.csv). Это экспозиция исходных входов, а не доказательство их сохранения после изменения занятости. Нового replay/«PF после удаления» нет.')
    add(table('cuts',lambda r:r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['year']=='ALL' and r['feature'] in ['H1ADX','H1ATRRatio','breakout_ATR','ADX_RISING','SLOPE_STRENGTHENING','M15_ATR_RISING','HOUR'],['feature','bin','closed','GE2','base_GE2','GE2_share','GE5','base_GE5','GE5_share','OPEN_in_bin']))
    add('Самый последовательный отрицательный описательный эпизод — SHORT ATRRatio≥1,25. Его следует показать полностью, чтобы отсутствие рекомендации не скрывало найденную закономерность:')
    add(table('extreme_ratio_SHORT',lambda r:True,['year','closed','gross_R','days','months','initial_no_s1','S1_activated','MFE_GE2','GE2','GE5','may_2024_entries','oct_2024_entries']))
    add('В нём6 SHORT2023 и11 SHORT2024, суммы −3,843889R/−5,174529R,0 исходных≥2R/≥5R. Но всего17 наблюдений на16 датах/10 месяцах; USD/CNY 13июня2024 разделяют один рыночный shock, не независимые подтверждения. IMOEX2023 вообще не представлен, GLD2024 всего1 сделка с небольшим плюсом. **12/17 уже активировалиS1, 3 достигли нижнейMFE≥2R**: это не механизм массовых первоначальных Stop без продолжения. В октябре нет ни одного такого входа, в мае оба дают суммарно лишь −0,268872R. Общий запрет B2 обоим направлениям затронул бы4≥2R LONG. Данные допускают описание неустойчивого продолжения при сильном расширении, но не устанавливают причинный эффект отсечения и не поддерживают его как следующее улучшение слабыхSHORT/месяцев. Порог1,25 — заранее заданная граница описательного интервала, не выбранный торговый cutoff.')
    add('**Решение `NO_SUPPORTED_ENTRY_CHANGE`; число предлагаемых механизмов для следующего causal replay —0.** Ухудшение SHORT2024 установлено; устойчивого доступного при входе объяснителя по обоим годам, рынкам и слабым месяцам с убедительным сохранением хвоста не найдено. Не заменять его запретомSHORT, инструментов, ADX/часов или новым порогом. TRAIL_375 остаётся неизменным исследовательским CONTROL; измененияS1/Stop/trailing не исследовались.')
    add('Полная2024 прибыль концентрирована: ноябрь53,744915R —44,0056% годовогоR. Без ноября PF1,452043/+68,387068R — sensitivity полного CLOSED журнала, не другой replay. Диагностика не исправляет концентрацию. Occupancy тоже меняет потенциальные альтернативы:711 A6-pass сигналов за оба года заняты позицией,481 исполняются,1 пропущен по adjacency. Неисполненным сигналам не присваивается выдуманный торговыйR.')
    add(table('funnel',lambda r:r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['period'] in ['2023','2024'],['period','decision_reason','signals','all_signals']))
    add('## Верификация и границы вывода')
    af=json.loads((audit/'AUDIT_RESULT.json').read_text());ff=json.loads((results/'FEATURE_CONTROL.json').read_text())
    add(f'Независимая вычислительная сверка: **{af["fields_compared"]} полей, {af["differences"]} расхождений**, max delta `{af["max_numeric_delta"]:.3g}`, tolerance1e−8. All-bars feature-control: **{ff["fields_compared"]} полей**,0 расхождений. 26 execution и9 diagnostic causal fixtures PASS. Primary использует pandas/object, independent verifier —stdlib/scalar рекурсии, другую position machine и отдельно написанные features/windows/quantiles/aggregates; не импортирует primary diagnostics/engine/metrics. Shared только metadata/constants/serialization/comparison. Автор один; внешнее человеческое ревью PENDING.')
    add('Заморозка computational protocol/code/spec/test/audit перед первыми новыми разрезами — `40f938734aff22d3b71ec829b9aba7fad4e624d6`, опубликована в ветке; [FREEZE.json](../FREEZE.json). Первые38 computational и10 audit artifacts записаны в FIRST_*_SHA256, проверяются при повторах. Отчётные представления/простые outcome-cohort дополнения написаны после просмотра результатов; исходный frozen diagnostic код не менялся. Два дополнительных свежих процесса повторяют полный CONTROL, features, diagnostics, independent audit, report и presentation audit; direct bytes+SHA256 — [REPEATABILITY.json](../REPEATABILITY.json).')
    add('Все числовые Markdown-таблицы сверяются с независимо проверенными CSV/JSON; дополнительные outcome-bands/focus signal cohorts/17-entry cohort отдельно сверяются из scalar raw replay. [AUDIT_RESULT](../audit/AUDIT_RESULT.json), [PRESENTATION_AUDIT](../audit/PRESENTATION_AUDIT.json). Полные24 месяца — [MONTHLY_DETAIL](MONTHLY_DETAIL.md), все фиксированные разрезы — [CUTS_DETAIL](CUTS_DETAIL.md), полные feature/outcome distributions и отрицательные значения — CSV/TABLES.json.')
    add('2023/2024 уже DEVELOPMENT_EXPOSED, не независимый OOS. Размеры отдельных групп малы, эффекты перемешаны рынками/месяцами, множество описательных разрезов не даёт подтверждения улучшения. Future outcomes никогда не используются для сигнала. 2025+ numeric OHLC не читается/не парсится; full-file hashes —opaque bytes. Данные не копируются в исследовательский репозиторий. Реальные costs/slippage/spread/funding, tick-grid, sizing/capital и live fills отложены. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.')
    add('Все новые repo-файлы только `IntradayLab/t3_m15_a6_s1_entry_quality_v1/`. TradingSystemLab, робот, ROADMAP, прежние исследования, data pin и оригинальный checkout неизменны. Один Draft PR безMerge/Auto-Merge; **STOP после создания Draft PR**.')
    (results/'REPORT.md').write_text('\n'.join(main))
    details=['# Все 24 exit-месяца, инструменты и стороны\n','GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. NO_COVERAGE не является нулевой торговой историей.\n']
    for scope in ('ALL_FOUR','FX',*C.SYMBOLS):
        details.append(f'## {scope}\n')
        details.append(table('monthly',lambda r:r['scope']==scope,['month','direction','coverage','closed','gross_PF','gross_R','initial_no_s1','failed_lower_MFE','GE2','GE5']))
    (results/'MONTHLY_DETAIL.md').write_text('\n'.join(details))
    details=['# Все фиксированные входные разрезы\n','Отдельные описательные группы signal cohorts; это не тест фильтров и не causal replay новой стратегии. Границы — SPEC.json; B0 включает значения ниже первой границы, далее левые границы включены. Gross R относится к полным исходам исходных CLOSED. Годовые когорты не independent OOS.\n']
    for scope in ('ALL_FOUR','FX',*C.SYMBOLS):
        details.append(f'## {scope}, оба года\n');details.append(table('cuts',lambda r:r['scope']==scope and r['year']!='ALL',['year','direction','feature','bin','closed','gross_PF','gross_R','initial_no_s1_fraction','failed_lower_MFE_fraction','GE2','GE5','base_GE2','base_GE5']))
    (results/'CUTS_DETAIL.md').write_text('\n'.join(details))
    C.write_json(results/'REPORT_TABLES.json',manifest)
    C.write_json(results/'DECISION.json',{'decision':'NO_SUPPORTED_ENTRY_CHANGE','proposed_mechanisms':0,'new_strategies':0,'filter_replays':0,'frozen_control_unchanged':True,'reason':'SHORT intermediate continuation failures are observable outcomes; available features lack stable cross-year/cross-market weak-month discrimination with strong-winner preservation; extreme ATRRatio short slice is small and does not explain October','labels':C.LABEL,'years':'2023-2024 DEVELOPMENT_EXPOSED'})
    print(json.dumps({'report_tables':len(manifest),'decision':'NO_SUPPORTED_ENTRY_CHANGE'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=C.HERE/'results');p.add_argument('--audit',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.results,a.audit)
