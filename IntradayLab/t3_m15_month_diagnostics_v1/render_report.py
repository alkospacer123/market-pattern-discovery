"""Russian report and deterministic standalone figures from audited tables."""
import argparse,csv,json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
TABLES=[]
def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def pick(rows,**kw):return [r for r in rows if all(str(r[k])==str(v) for k,v in kw.items())]
def fmt(v,mode='f'):
    if v in ['',None]:return '—'
    if mode=='s':return str(v)
    x=float(v)
    if not math.isfinite(x):return '—'
    if mode=='i':return str(int(x))
    if mode=='p':return f'{x*100:.1f}%'
    return f'{x:.4f}'
def table(source,rows,cols):
    # Human table fields are also recorded for separate presentation verification.
    text='| '+' | '.join(c[1] for c in cols)+' |\n| '+' | '.join('---' for c in cols)+' |\n'
    text+='\n'.join('| '+' | '.join(fmt(r[c[0]],c[2]) for c in cols)+' |' for r in rows)+'\n'
    TABLES.append({'source':source,'columns':cols,'rows':[{k:r[k] for k,_,_ in cols} for r in rows],'markdown':text})
    return text

def run(source,audit,output):
    assert output.resolve().is_relative_to(HERE);output.mkdir(parents=True,exist_ok=True)
    TABLES.clear()
    year=read(source/'yearly.csv');month=read(source/'monthly.csv');market=read(source/'market_regime.csv');quality=read(source/'entry_quality.csv');cuts=read(source/'causal_cuts.csv');funnel=read(source/'signal_funnel.csv');matched=read(source/'matched_coverage_trades.csv');trades=read(source/'trade_diagnostics.csv');historical=read(source/'historical_A6.csv');dist=read(source/'entry_feature_distributions.csv');directions=read(source/'breakout_direction.csv')
    a=json.loads((audit/'AUDIT_RESULT.json').read_text());assert a['status']=='PASS'
    yy=pick(year,scope='ALL',direction='ALL')
    y23=pick(yy,period='2023')[0];y24=pick(yy,period='2024')[0]
    text='''# T3/M15 OPTIMIZED T1+S1 — диагноз календарных месяцев и входов

**2024 снизил PF прежде всего из-за ухудшения доли успешных принятых входов и частоты крупных выигрышей, при значительно большем объёме убыточных сделок. Средний убыток не вырос. Свечные данные не подтверждают общее отсутствие трендов. Убедительного одного изменения, одновременно улучшающего слабые месяцы и сохраняющего ключевые тренды, не найдено.**

**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024: DEVELOPMENT_EXPOSED.** Исследуется только прежний OPTIMIZED T1+S1; торговых изменений, новых вариантов или численной Optimization нет. Исторический вход по signal Close остаётся непроверенным предположением.

## Воспроизведение и определения

Фактический discovery `main`: `8c40950726446ebccb1ad80b8f129558470d9c11`, Merge #500. Pinned read-only данные `market-pattern-data/forever/`: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Предыдущие #490, #491, #495–#500 и ROADMAP изучены; [PR_CONTEXT](../PR_CONTEXT.json) и [SHA прочитанных материалов](../READ_REFERENCES_SHA256.json) сохранены. Основной источник — неизменный `t3_m15_t1_s1_v1`.

EMA75, slope5, H1 ADX14>20, Donchian20 shift(1), Stop 2 M15 ATR, trail 3.5 ATR, T1 [10:00,18:00) MSK по завершённому signal Close; S1 — активация на завершённой пережитой свече после +1 первоначального R. Исходный код также требует H1 ATR14/ATRMean20>1. Это сохранённое условие, не новый фильтр; A6 отдельно требует роста этого отношения относительно предыдущего опубликованного H1.

H1 состоит из исходных дневных ordinal-блоков четырёх последовательных наблюдаемых M15, публикуется только на четвёртом Close. Рекурсивные индикаторы и Donchian пересекают дни. Сначала действует прежний Stop, неблагоприятный gap исполняется по Open; новые extrema/активация/Stop доступны только после пережитого Close, Stop применяется на следующем наблюдаемом баре. Занятость, same-Close повторный вход, переносы и OPEN сохранены.

Полный causal replay воспроизвёл **545 CLOSED и 1 terminal OPEN**. Сверены **547 878 полей** исходных trade/Stop/entry/gap/period OPEN журналов, расхождений нет. Это воспроизведение прежней стратегии, а не удаление сделок из CSV. [Результат](REPRODUCTION.json), [контрольные точки](CHECKPOINTS.json), [полные журналы](trades.csv).

Месяц/год экономики — историческая Close-метка выхода MSK. Качество входа и рыночные признаки — дата signal Close. DD — просадка суммы CLOSED R с нулевого начального уровня, порядок exit_time/instrument/trade_id; это не портфельная доходность и не внутрипозиционная MTM-просадка. OPEN не ликвидируется и не входит в PF. MFE/MAE, длительность и будущий исход — только диагностика. MFE — нижняя наблюдаемая оценка по пережитым свечам; extrema Stop-свечи исключены, неизвестный intrabar порядок не выдумывается.

'''
    text+=table('yearly.csv',pick(yy,period='2023')+pick(yy,period='2024'),[('period','Год','s'),('closed','CLOSED','i'),('gross_PF','Gross PF','f'),('gross_R','Gross R','f'),('expectancy_R','Exp R','f'),('positive_months','+месяцев /12','i'),('DD_closed_R','DD R','f')])
    text+='''
Контрольные апрель −0.8685R, май −2.8096R, июнь −1.1554R, октябрь −0.3681R и ноябрь +44.0619R совпали. **2024 без ноября: +50.3610R, PF 1.2958**; это ретроспективная чувствительность CLOSED-журнала, не новый causal replay.

## 1. Почему снизился Profit Factor

PF = (число выигрышей / число убытков) × (средний выигрыш / абсолютный средний убыток). В 2023 есть одна нулевая CLOSED-сделка; она не входит в выигрыши/убытки.

'''
    text+=table('yearly.csv',pick(yy,period='2023')+pick(yy,period='2024'),[('period','Год','s'),('wins','WIN','i'),('losses','LOSS','i'),('win_share','WIN доля','p'),('mean_win_R','Средний WIN R','f'),('mean_loss_R','Средний LOSS R','f'),('positive_R','Положительные R','f'),('negative_R','Отрицательные R','f')])
    text+='''
Положительная сумма выросла примерно на 49%, отрицательная — на 110%; почти одинаковый итоговый Gross R теперь получен значительно большим оборотом риска. Expectancy упала примерно вдвое. Главный арифметический механизм — меньшая вероятность выигрышного входа; уменьшение среднего выигрыша вторично, средний убыток даже немного меньше.

'''
    text+=table('yearly.csv',pick(yy,period='2023')+pick(yy,period='2024'),[('period','Год','s'),('MFE_ge_0.5_share','MFE≥0.5R','p'),('MFE_ge_1_share','MFE≥1R','p'),('MFE_ge_2_share','MFE≥2R','p'),('initial_without_S1_share','Initial Stop без S1','p'),('holding_mean_minutes','Удержание среднее, мин','f'),('holding_median_minutes','Медиана, мин','f'),('GE2_count','WIN≥2R','i'),('GE5_count','WIN≥5R','i')])
    text+='''
Доля ≥5R CLOSED снизилась с 14/190 (7.4%) до 10/355 (2.8%). Нижняя MFE и средняя длительность подтверждают более слабый реализованный хвост принятой последовательности. Это не означает, что любой позднее успешный сигнал можно было отличить при входе.

Состав инструментов изменился: в 2023 GLD доступен с 11 июля, IMOEX — с 14 ноября. Число CLOSED IMOEX выросло с 8 до 103, и менее эффективный инструмент занял большую долю. Но состав не объясняет всё: на USD/CNY с полными годами PF упал с 2.5420 до 1.4926. Основной провал — USD: +64.9775R → +13.2431R. CNY вырос +27.2127R → +30.9933R, GLD и IMOEX улучшились относительно короткой истории 2023.

'''
    rows=[r for r in year if r['period'] in ['2023','2024'] and r['scope'] in ['FX']+['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'] and r['direction']=='ALL']
    text+=table('yearly.csv',rows,[('period','Год','s'),('scope','Инструмент','s'),('closed','CLOSED','i'),('gross_PF','PF','f'),('gross_R','R','f'),('win_share','WIN доля','p')])
    text+='''
Дополнительно сопоставлены **одинаковые фактически доступные MM-DD даты с готовыми H1** для каждого инструмента, а не условные полные годы GLD/IMOEX. [Точный перечень](matched_dates.csv): USD 156 пар дат, CNY 156, GLD 72, IMOEX 16. Выборка по дате входа берётся из полного неизменного пути; выходы не перезапускаются. Календарные будни и число свечей могут различаться. Это диагностическая когорта, не результат укороченного replay; IMOEX особенно мал.

'''
    text+=table('matched_coverage_trades.csv',matched,[('period','Год входа','s'),('scope','Охват','s'),('closed','CLOSED','i'),('gross_PF','PF','f'),('gross_R','R','f'),('win_share','WIN доля','p')])
    text+='''
На matched FX PF также падает 2.8304→1.5011. У matched USD R становится немного отрицательным, CNY и GLD положительны. Единой деградации всех четырёх рынков нет.

## 2. Все 24 календарных месяца

![Месячный Gross R](monthly_gross_R.svg)

«Неудачные» ниже — CLOSED с Gross R<0 и нижней MFE<0.5R. Это исход после входа, не доступный тогда фильтр. «Stop» — первоначальный Stop без активации S1. «Top3» — доля трёх крупнейших победителей в положительных R месяца. Более подробный разрез всех инструментов и LONG/SHORT — [MONTHLY_DETAIL](MONTHLY_DETAIL.md); NO_COVERAGE до реальных запусков показан отдельно.

'''
    mm=pick(month,scope='ALL',direction='ALL')
    text+=table('monthly.csv',mm,[('period','Месяц','s'),('closed','CLOSED','i'),('gross_PF','PF','f'),('gross_R','R','f'),('expectancy_R','Exp','f'),('DD_closed_R','DD R','f'),('R_LONG','LONG R','f'),('R_SHORT','SHORT R','f'),('failed_entries','Неудачные','i'),('initial_without_S1_share','Stop','p'),('S1_count_share','S1','p'),('top3_share_positive_R','Top3','p')])
    text+='\nВклад каждого инструмента:\n\n'
    text+=table('monthly.csv',mm,[('period','Месяц','s'),('R_USDRUBF','USD R','f'),('R_CNYRUBF','CNY R','f'),('R_GLDRUBF','GLD R','f'),('R_IMOEXF','IMOEX R','f')])
    text+='''
### Апрель–июнь: три разные проблемы, а не три месяца без тренда

Итого −4.8334R при 99 CLOSED: 35 выигрышей и 64 убытка; средний выигрыш +1.5143R, убыток −0.9037R. Без S1 закрылись 49/99, неудачных с MFE<0.5R — 34. LONG дал −4.7624R, SHORT около −0.0710R: слабый квартал нельзя целиком приписать SHORT.

- **Апрель:** 15/37 выигрышей, средний +1.3228R; USD −4.2914R и IMOEX −4.1853R перекрыли CNY +5.9883R и GLD +1.6198R. При доле пригодного H1-режима 45.1% и среднем ADX 34.24 не было дефицита формально направленного режима; 53.8% полных пригодных Donchian-пробоев не получили +0.5 исходного R в следующие четыре M15. Для LONG это 65.0%, SHORT 45.1%.
- **Май:** 13/33 выигрышей со средним +1.1802R, ни одного ≥5R. CNY −4.8523R — главный отрицательный вклад; IMOEX +2.6040R его не компенсировал. Пригодные LONG-сигналы редки (8 полных окон), 75% без часового продолжения; у SHORT 65 окон и 43.1% без продолжения. Небольшие выигрыши при обычных Stop-убытках — другая форма слабости, чем апрель.
- **Июнь:** лишь 7/29 выигрышей; их средний +2.5454R почти целиком поддерживает CNY SHORT +13.1105R, entry 18.06 16:00, exit 19.06 11:00 MSK. Другие 28 CLOSED дали −14.2659R. CNY +9.0708R перекрывался GLD −6.6435R и остальными. Месячная CLOSED-DD 14.6037R при итоговом −1.1554R показывает, почему маленький месячный минус не означает контролируемую внутримесячную просадку. Пригодных часовых пробоев без продолжения лишь 40.7%; у FX 21.7%. Тренд существовал, но слишком мало прибыльных принятых сделок и очень высокая зависимость от одного хвоста.

### Октябрь

−0.3681R, 33 CLOSED, WIN 11/33, средний выигрыш +1.6457R; 18 Initial Stop без S1, 16 неудачных MFE<0.5R. LONG +4.5681R против SHORT −4.9362R. Средний рыночный ADX 26.81 — ниже апрельского/ноябрьского; 60.3% полных пригодных часовых пробоев без продолжения. Здесь свидетельство шумных входов сильнее, чем в июне. Однако одна CNY LONG сделка +5.7690R сохранила полезный тренд.

### Ноябрь

+44.0619R — **46.7% годового Gross R**, но около 20.1% годовых положительных R. Поэтому речь о концентрации итогового результата, а не о половине всех выигрышных R. 16/31 WIN, средний выигрыш +3.4627R, средний убыток −0.7561R; S1 активирован у 21/31, Initial Stop без S1 только 10/31.

Все четыре инструмента положительны: GLD +22.2268R, CNY +10.8069R, USD +7.2430R, IMOEX +3.7851R. LONG +34.6187R даёт 78.6% результата месяца. Пригодный H1-режим занимает 50.4% core bars, средний ADX 34.03, normalized slope 0.4771 H1 ATR. Лишь 26.4% пригодных полных пробоев не получили часового продолжения, против 60.3% в октябре.

Две крупнейшие сделки GLD LONG +11.4352R и CNY LONG +8.0961R дают +19.5313R: 44.3% итогового R месяца и 35.3% его положительных R. Они удерживались 6750 и 4680 календарных минут с переносами. S1 и свободное удержание позволили сохранить тренды; принудительное закрытие сессии либо раннее отсечение не проверено как улучшение.

'''
    nov=sorted([r for r in trades if r['exit_time'].startswith('2024-11')],key=lambda r:float(r['gross_R']),reverse=True)[:6]
    text+=table('trade_diagnostics.csv',nov,[('instrument','Инструмент','s'),('direction','Сторона','s'),('entry_time','Entry MSK','s'),('gross_R','R','f'),('holding_minutes','Минут','i'),('H1ADX','ADX входа','f'),('dADX','dADX','f'),('dATRRatio','dATRRatio','f')])
    text+='''
### Концентрация месяцев и победителей

Доля лучшего/трёх лучших месяцев ниже делится на итоговый Gross R; отдельно дана доля лучшего в сумме только положительных месяцев. Эти знаменатели различаются. У отдельных инструментов доля может быть >100%, если остальные месяцы убыточны.

'''
    text+=table('yearly.csv',pick(yy,period='2023')+pick(yy,period='2024'),[('period','Год','s'),('best_month_share_GrossR','Лучший / Gross R','p'),('top3_months_share_GrossR','Три лучших / Gross R','p'),('best_month_share_positive_month_R','Лучший / +месяцы R','p'),('top3_months_share_positive_month_R','Три лучших / +месяцы R','p'),('top5_share_positive_R','Top5 WIN / +R','p'),('top10_share_positive_R','Top10 WIN / +R','p')])
    text+='''
Top10-доля положительных торговых R не выросла, а снизилась 33.6%→28.8%: нельзя утверждать, что ухудшились все виды концентрации. Но лучший месяц теперь даёт 46.7% годового итога, три лучших — 76.6%. Без десяти крупнейших выигрышей 2024 остаётся +15.0006R / PF 1.0826. Это диагностическая чувствительность прежнего списка, не новый replay.

## 3. Были ли тренды: H1 против H2

Рыночная таблица построена по всем доступным завершённым M15/H1, независимо от наличия позиции. Знаменатель долей — core M15 bars с готовыми причинными H1-признаками. Directional до ATR-gate требует ADX>20, согласованные EMA/slope; пригодный режим дополнительно ATRRatio>1. Efficiency5 — абсолютное изменение H1 Close за пять H1, делённое на сумму абсолютных соседних изменений; это причинная оценка направленности, не торговый фильтр.

'''
    mk=[r for r in market if r['period'] in ['2023','2024'] and r['scope'] in ['ALL','FX']]
    text+=table('market_regime.csv',mk,[('period','Год','s'),('scope','Охват','s'),('coverage_mode','Покрытие','s'),('base_directional_share','Directional','p'),('tradable_regime_share','Пригодный','p'),('mean_ADX','ADX','f'),('mean_ATRRatio','ATRRatio','f'),('mean_efficiency5','Efficiency5','f'),('eligible_no_continuation_share','Пробои без +0.5R','p')])
    text+='''
**H1 — «устойчивых направленных движений было меньше»: не подтверждена как общий диагноз.** На FULL и MATCHED FX направленные/пригодные режимы, средний ADX и efficiency5 не слабее; аналогичный pooled вывод сохраняется на matched календаре. При этом короткая 5-H1 направленность не доказывает неизменную частоту многодневных движений относительно начального риска. Ухудшение частоты ≥5R принятой последовательности реально, но его нельзя автоматически приписать исчезновению всех рыночных трендов.

**H2 — «движения присутствовали, но текущая логика часто принимала неудачные пробои»: частично поддержана на принятой последовательности.** Доля сделок с нижней MFE<0.5R выросла 27.9%→32.4%, Initial Stop без S1 40.0%→45.9%, WIN-доля упала. Но все пригодные часовые сигналы в целом не стали явно хуже: доля без продолжения 46.9%→47.1%, а FX даже лучше 44.1%→41.9%. Значит, ключевое различие — качество реально принятой очереди/более длинного продолжения и изменившийся состав, а не установленная массовая деградация каждого Donchian-сигнала. Причинный вклад занятости без альтернативного replay не идентифицирован.

Четыре будущие M15 должны быть строго последовательны, в той же дате Close; неполные окна CENSORED. Эта диагностика включает движение после возможного Stop и не равна MFE сделки. Перекрывающиеся сигналы не являются независимыми наблюдениями. В качестве «нет продолжения» взят только фиксированный +1 ATR сигнала (=0.5 исходного R), не выбранный лучший порог.

'''
    periods=['2024-04','2024-05','2024-06','2024-10','2024-11']
    focus=[r for r in market if r['scope']=='ALL' and r['coverage_mode']=='FULL' and r['period'] in periods]
    text+=table('market_regime.csv',focus,[('period','Месяц','s'),('tradable_regime_share','Пригодный','p'),('mean_ADX','ADX','f'),('mean_dADX','dADX','f'),('mean_ATRRatio','ATRRatio','f'),('mean_dATRRatio','dATRRatio','f'),('mean_abs_slope_ATR','Slope / ATR','f'),('eligible_no_continuation_share','Без +0.5R','p'),('no_tradable_share','Без режима','p')])
    text+='''
Периоды без пригодного режима занимают 64.7% core bars 2023 и 61.5% 2024. Число наблюдаемых эпизодов на 1000 core bars почти одинаково: 35.0 и 35.6. Эпизод начинается при входе в отсутствие режима; день/core/gap прерывает эпизод. Это не реконструкция отсутствующих биржевых свечей.

Повторные пробои после часовой неудачи: 192/969 полных follow-up окон в 2023, 408/1862 в 2024; противоположные — 40/969 и 102/1862. Частоты выросли умеренно, а абсолютные количества также отражают расширенное покрытие. [Полные признаки](h1_features.csv), [каждый пробой и цензурирование](breakout_diagnostics.csv), [рыночные/инструментальные месяцы](market_regime.csv), [стороны](breakout_direction.csv). Эти результаты не доказывают преимущество запрета повторного входа.

## 4. Почему SHORT уступал LONG

'''
    side=[r for r in year if r['scope']=='ALL' and r['period'] in ['2023','2024'] and r['direction'] in ['LONG','SHORT']]
    text+=table('yearly.csv',side,[('period','Год','s'),('direction','Сторона','s'),('closed','CLOSED','i'),('gross_PF','PF','f'),('gross_R','R','f'),('win_share','WIN доля','p'),('mean_win_R','Средний WIN','f'),('mean_loss_R','Средний LOSS','f'),('initial_without_S1_share','Stop без S1','p'),('MFE_ge_2_share','MFE≥2R','p')])
    text+='''
В 2024 средние выигрыши/убытки почти одинаковы у обеих сторон; разрыв возникает в WIN-доле 46.1% против 35.0%. SHORT чаще закрывается первоначальным Stop без S1 (49.7% против 42.1%) и реже достигает ≥2R. SHORT удерживается в среднем 458.7 мин, LONG 828.5; это будущая характеристика, а не критерий входа.

Свечной часовой анализ не подтверждает «SHORT всегда хуже продолжает»: без +0.5R у пригодных SHORT 44.1%, у LONG 49.8%. Но Close-возврат за исходный уровень чаще SHORT — 55.9% против 51.1%. Быстрый отскок в направлении SHORT не гарантирует устойчивого движения до выхода. В 2023 SHORT имел **более высокий** PF, чем LONG; исключать SHORT по известному 2024 было бы подгонкой. И слабость апрель–июнь в основном LONG, поэтому запрет SHORT её не решает.

## 5. Признаки, известные на входе, и A6

Сравниваются только завершённые H1/M15: ADX/dADX, ATRRatio/dATRRatio, slope/H1 ATR со знаком позиции, M15 ATR/Close, превышение исходного Donchian в ATR, положение Close внутри range в направлении позиции, час MSK. Все характеристики outcome/MFE/MAE/holding остаются отдельно. Средние по pooled данным могут быть смешаны инструментами; соответствующие instrument/direction группы и квартили сохранены.

'''
    q=[r for r in quality if r['scope']=='ALL' and r['direction']=='ALL' and r['period'] in ['2023','2024'] and r['outcome'] in ['WIN','LOSS','GE5']]
    text+=table('entry_quality.csv',q,[('period','Год входа','s'),('outcome','Исход','s'),('closed','N','i'),('mean_H1ADX','ADX','f'),('mean_dADX','dADX','f'),('mean_H1ATRRatio','ATRRatio','f'),('mean_dATRRatio','dATRRatio','f'),('mean_signed_slope_ATR','Slope/ATR','f'),('mean_volatility_pct','ATR/Close %','f'),('mean_breakout_ATR','Breakout/ATR','f'),('mean_close_location','Close range','f'),('mean_hour','Час MSK','f')])
    text+='''
В 2024 убытки в среднем имели **выше ADX и dADX**, чем выигрыши. Превышение Donchian у убыточных входов немного больше, но распределения перекрываются. У всех крупных победителей есть исходное согласование режима, поскольку это условие стратегии, — оно также есть у всех убытков. Вывести из него дополнительный разделяющий фильтр нельзя.

'''
    dq=[r for r in dist if r['period']=='2024' and r['direction']=='ALL' and r['outcome'] in ['LOSS','GE5'] and r['feature'] in ['H1ADX','dATRRatio','signed_slope_ATR','breakout_ATR']]
    text+=table('entry_feature_distributions.csv',dq,[('outcome','Исход','s'),('feature','Признак','s'),('count','N','i'),('min','Min','f'),('p25','Q25','f'),('median','Медиана','f'),('p75','Q75','f'),('max','Max','f')])
    text+='''
Часовые эффекты также меняются местами: [10,12) даёт +84.7541R в 2023 и −8.3907R в 2024, [15,18) −4.3725R и +69.6759R. Это отрицательное свидетельство против выбора нового часового порога по одному году. М15 ATR rising в 2024 почти не разделяет PF (1.5202 против 1.5182). ADX rising хуже non-rising (1.4059 против 1.8247). Не подбирались новые пороги или комбинации.

### Что действительно известно про A6

В предыдущем полном standalone replay #495 A6 на OPTIMIZED улучшал 2024 PF 1.3631→1.5573 и R +80.1020→+86.1245R, давал 9 вместо 8 положительных месяцев. Но терял около 20.2% R 2023, 15 из 56 исходных победителей ≥2R 2024, увеличивал концентрацию. #497 A6+S1 также не дал одновременного улучшения календаря/DD. Это другие пути исполнения; добавления A6 к T1+S1 здесь нет.

'''
    hr=[r for r in historical if r['period'] in periods]
    text+=table('historical_A6.csv',hr,[('rule','Старый replay #495','s'),('period','Месяц выхода','s'),('closed','N','i'),('gross_PF','PF','f'),('gross_R','R','f')])
    text+='''
A6 раньше улучшал апрель и июнь, но ухудшал май; октябрь оставался убыточным. Это совместимо с отсевом части неустойчивых расширений/затухающих движений, но не доказывает такой причинный механизм.

На **замороженном** списке входов T1+S1 группы A6 pass/fail имеют следующую картину. Ничего не удалено из основной оценки. Это **диагностические группы, не результаты нового causal replay**:

'''
    a6=[r for r in cuts if r['direction']=='ALL' and r['cut']=='A6' and r['period'] in ['2023','2024','2024Q2','2024-10','2024-11']]
    text+=table('causal_cuts.csv',a6,[('period','Период входа','s'),('value','A6 pass','s'),('closed','N','i'),('gross_PF','Групповой PF','f'),('gross_R','Групповой R','f'),('failed_entries','Неудачные','i'),('GE2_count','≥2R','i'),('GE5_count','≥5R','i')])
    text+='''
Годовая pass-группа лучше, однако в апреле–июне она даёт −8.5248R, fail +3.6913R; единственный крупнейший июньский CNY SHORT +13.1105R имеет **падающий ATRRatio** (dATRRatio −0.0446). В 2024 fail-группа содержит четыре из десяти ≥5R с суммой +35.9919R. Такой фильтр отсеял бы эти исходные входы; возможность позже войти в те же тренды требует полного replay. Эта арифметика не равна эффекту фильтра: отсутствие входа освобождает позицию, допускает другие сигналы и меняет всю последующую очередь.

## 6. Главная проблема: вход, режим, Stop или сопровождение

**Наблюдаемый центр проблемы — слабое продолжение значительной части принятых пробоев, особенно в отдельных инструментальных/направленных эпизодах. Это взаимодействие входа и локального режима, а не доказанная ошибка только одного компонента.**

В 2024 115 неудачных MFE<0.5R закрытий дают −115.0333R — 63.3% отрицательных R. После уже наблюдённого MFE≥1R потеряно лишь 18.5874R (10.2% отрицательных R), а MFE≥2R → LOSS случился один раз. Поэтому массовое превращение больших выигрышей в убыток не является главным источником падения PF. Первоначальный Stop без S1 встречается в 163/355 CLOSED и даёт почти обычный −1R; средний убыток не вырос.

Большой giveback существует: ноябрьский GLD дошёл до нижней MFE 19.6343R и завершился +11.4352R. Но эта будущая разница не доказывает, что иной trail мог удержать весь экстремум. Ранее проверенные ранние выходы #495 ухудшали 2024; изменения Initial Stop #498 снижали полный PF и губили тренды. Основания вновь сужать Stop, добавлять BE или forced flat из этих данных нет.

**Занятость существенна:**

'''
    ff=[r for r in funnel if r['scope']=='ALL' and r['direction']=='ALL' and r['period'] in ['2023','2024']]
    text+=table('signal_funnel.csv',ff,[('period','Год signal','s'),('signals_all_hours','Все исходные сигналы','i'),('signals_T1','В T1','i'),('T1_busy','Занятые T1','i'),('accepted_including_OPEN','Принятые с OPEN','i'),('same_close_reentry','Same Close повтор','i')])
    text+='''
Сигнал считается на каждом завершённом Close; последовательные пробои не дедуплицируются в одну «идею». В 2024 544 из 900 T1-сигналов заблокированы позицией. Ни PF групп A6, ни доля будущих неудач не заменяют новый полный replay. По #500 изменение занятости уже теряло один ≥2R победитель относительно T1; этот риск явно сохраняется.

## 7. Как уменьшить зависимость от сильных месяцев

Регулярность требует улучшения распределения **всех** слабых месяцев при сохранении положительного хвоста, а не искусственного удаления ноября или выигрышей. В рамках неизменной стратегии зависимость констатируется, но не исправляется. Основные слабые месяцы близки к нулю по итоговому R, однако июньская DD и редкие большие выигрыши делают равномерную прибыльность ненадёжной.

Для любого отдельно разрешённого будущего изменения нужны полный причинный путь, все 24 месяца, худшие месяцы/DD, сохранение ≥2/≥5R и последствия новой занятости; оба года уже DEVELOPMENT_EXPOSED. Сокращение SHORT, утренних часов, расширений ATR или длительных позиций не обосновано как универсальное решение. Риск/капитал/корреляции и расходы не моделировались, поэтому уменьшение CLOSED-R DD не обещает такой же эффект на счёте.

## 8. Одно следующее изменение

**Убедительного причинного кандидата, отвечающего приоритету календарной регулярности и сохранения крупных трендов, нет. Новое изменение не рекомендуется.** Ближайший ранее подтверждённый standalone кандидат — фиксированный A6, но он не получает поддержки на слабом апреле–июне T1+S1 и отсеял бы исходный вход крупнейшего июньского победителя. Возможность другого входа в тот же тренд без полного replay неизвестна. Объявлять его решением этой задачи было бы сильнее имеющихся данных.

Это отрицательный исследовательский вывод, а не повод придумать новый порог/комбинацию. Если A6 отдельно всё же будет разрешён, единственная проверяемая гипотеза — его уже зафиксированное условие `H1 ATRRatio > Previous H1 ATRRatio` поверх неизменного T1+S1, с полным replay и сохранением отрицательных результатов; преимущество не заявляется. Здесь такой вариант **не запускался**, разрешение на него не запрашивается.

## Контроль качества и ограничения

'''
    text+=f'''Независимая вычислительная сверка — **{a['fields_compared']:,} полей, 0 расхождений**, max delta `{a['maximum_numeric_delta']:.3g}` при абсолютном допуске 1e−8. Primary — dataframe features/object replay; проверка — ранее независимые scalar features/replay #500 плюс отдельно написанные stdlib агрегаты и диагностические окна. Проверены все H1/пробои, исходные и обогащённые trade-поля, Stop/entry/gap/OPEN, покрытия, matched dates и все числовые строки CSV, включая отрицательные результаты. Автор один; независимое человеческое ревью PENDING. [AUDIT_RESULT](../audit/AUDIT_RESULT.json).

'''
    text+='''Отдельные causal fixtures проверяют prefix invariance диагностических признаков, запрет чтения будущего numeric suffix и цензурирование gap-окна; исходные 40 причинных fixtures #500 выполняются без изменения их файлов. Два свежих полных повтора primary+scalar audit+presentation сверяются direct bytes и SHA256; [REPEATABILITY](../REPEATABILITY.json). Все исходные SHA, число/границы свечей и реально наблюдаемые gaps проверены: [coverage](coverage.csv), [SOURCE_MANIFEST](SOURCE_MANIFEST.json). Наличие биржевых свечей в отсутствующие интервалы не выдумывается; полнота относительно официального исторического session calendar не установлена.

Полные файлы хешируются как непрозрачные байты, но timestamp-first парсеры прекращают чтение до OHLC 2025+. Издержки, funding, tick-grid, реальные fills, sizing и капитал отложены. Историческая метка Stop Close не является точным intrabar временем исполнения. Никаких изменений прежних исследований, ROADMAP, TradingSystemLab или источников нет. Ни новых стадий, Robustness, Walk Forward, TRUE OOS, LIVE, ни нового торгового варианта.

**Один Draft PR; Auto-Merge выключен; Merge не выполняется. STOP после создания и проверки PR.**
'''
    (output/'REPORT.md').write_text(text)
    detail='# Все 24 месяца: инструменты и направления\n\nGROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. DEVELOPMENT_EXPOSED. EXIT month MSK. DD CLOSED R; MFE нижняя наблюдаемая оценка. NO_COVERAGE означает отсутствие исходных свечей, не торговый ноль.\n'
    for m in sorted({r['period'] for r in month}):
        detail+='\n## '+m+'\n\n'
        rows=[r for r in month if r['period']==m and r['scope'] in ['ALL','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF']]
        detail+=table('monthly.csv',rows,[('scope','Инструмент','s'),('direction','Сторона','s'),('coverage','Покрытие','s'),('closed','N','i'),('gross_PF','PF','f'),('gross_R','R','f'),('expectancy_R','Exp','f'),('DD_closed_R','DD','f'),('failed_entries','Неудачные','i'),('initial_without_S1_share','Stop','p'),('S1_count_share','S1','p'),('top3_share_positive_R','Top3','p')])
    (output/'MONTHLY_DETAIL.md').write_text(detail)
    (output/'REPORT_TABLES.json').write_text(json.dumps(TABLES,ensure_ascii=False,indent=2)+'\n')
    matplotlib.rcParams['svg.hashsalt']='t3-m15-month-diagnostics-v1'
    fig,ax=plt.subplots(figsize=(13,5));x=list(range(24));v=[float(r['gross_R']) for r in mm]
    ax.bar(x,v,color=['#187e60' if z>=0 else '#b74545' for z in v]);ax.axhline(0,color='#222222',linewidth=.7)
    ax.set_xticks(x,[r['period'] for r in mm],rotation=70);ax.set_ylabel('Gross R (closed trades)');ax.set_title('OPTIMIZED T1+S1: 24 calendar months / DEVELOPMENT_EXPOSED')
    fig.tight_layout();fig.savefig(output/'monthly_gross_R.svg',metadata={'Date':None});plt.close(fig)
    svg=output/'monthly_gross_R.svg';svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    print(json.dumps({'report_tables':len(TABLES),'human_report':'REPORT.md','status':'PASS'}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=HERE/'results');p.add_argument('--audit',type=Path,default=HERE/'audit');p.add_argument('--output',type=Path,default=HERE/'results');a=p.parse_args();run(a.source,a.audit,a.output)
