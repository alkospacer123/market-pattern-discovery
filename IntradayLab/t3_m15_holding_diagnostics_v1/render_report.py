"""Deterministic presentation of existing diagnostics; no market-data reads."""
import argparse
import hashlib
import json
from pathlib import Path
import os

HERE=Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR',str(HERE/'work'/'matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def table(f,cols):
    lines=['| '+' | '.join(cols)+' |','|'+'|'.join(['---']*len(cols))+'|']
    for row in f[cols].to_dict('records'):
        def fmt(v):
            if pd.isna(v):return '—'
            if isinstance(v,(float,np.floating)):return f'{v:.3f}'
            return str(v)
        lines.append('| '+' | '.join(fmt(row[c]) for c in cols)+' |')
    return '\n'.join(lines)

def main(root):
    assert root.resolve().is_relative_to(HERE.resolve())
    f=pd.read_csv(root/'trade_diagnostics.csv');pooled=pd.read_csv(root/'pooled_year.csv')
    carry=pd.read_csv(root/'pooled_bookkeeping.csv');iy=pd.read_csv(root/'instrument_year.csv')
    first=pd.read_csv(root/'first_candles_summary.csv');first=first[(first.grouping=='version|year|horizon_bar|outcome') & first.outcome.isin(['WIN','LOSS'])]
    loss_rows=[];hold_rows=[];kind_rows=[];stop_rows=[];early_rows=[]
    for (v,y),g in f.groupby(['version','year'],sort=True):
        losses=g[g.net_R<0];volume=-losses.net_R.sum()
        low=losses[losses.MFE_R<.5];medium=losses[(losses.MFE_R>=.5)&(losses.MFE_R<1)];high=losses[losses.MFE_R>=1]
        loss_rows.append({'version':v,'year':y,'losses':len(losses),'loss_volume_R':volume,
            'MFE_lt_0_5_count':len(low),'MFE_lt_0_5_loss_share_pct':-low.net_R.sum()/volume*100,
            'MFE_0_5_to_1_loss_share_pct':-medium.net_R.sum()/volume*100,
            'MFE_ge_1_count':len(high),'MFE_ge_1_loss_share_pct':-high.net_R.sum()/volume*100,
            'MFE_ge_2_count':len(losses[losses.MFE_R>=2])})
        locked=losses[losses.first_positive_stop_bar.notna()]
        stop_rows.append({'version':v,'year':y,'initial_stop_exits':len(g[g.exit_type=='INITIAL_STOP']),
            'ratcheted_stop_losses':len(losses[losses.exit_type=='RATCHETED_STOP']),
            'positive_stop_then_net_loss':len(locked),'of_these_gap_exit':int(locked.gap_exit.sum()),
            'of_these_C1_flip':int(locked.C1_flipped_gross_profit.sum()),
            'updates':int(g.trailing_updates.sum()),'without_new_extreme':int(g.tightenings_without_new_extreme.sum()),
            'close_through_new_stop_bars':int(g.close_through_new_stop_bars.sum()),
            'mean_giveback_R':g.giveback_recorded_R.mean()})
        for k,h in g.groupby('holding_bucket',sort=True):
            pos=h.loc[h.net_R>0,'net_R'].sum();neg=-h.loc[h.net_R<0,'net_R'].sum()
            hold_rows.append({'version':v,'year':y,'holding_bucket':k,'trades':len(h),'PF_net_C1':pos/neg if neg else np.nan,
                'gross_R':h.gross_R.sum(),'net_R':h.net_R.sum(),'mean_net_R':h.net_R.mean(),'mean_MFE_R':h.MFE_R.mean()})
        for k,h in g.groupby('carry_kind',sort=True):kind_rows.append({'version':v,'year':y,'carry_kind':k,'trades':len(h),'net_R':h.net_R.sum()})
    for r in first.to_dict('records'):
        early_rows.append({'version':r['version'],'year':r['year'],'bar':r['horizon_bar'],'outcome':r['outcome'],
            'trades':r['trades'],'alive_before_close':r['completed_before_exit'],
            'all_close_R':r['all_fixed_horizon_mean_close_move_R'],
            'all_cum_favorable_R':r['all_fixed_horizon_mean_cumulative_favorable_R'],
            'all_cum_adverse_R':r['all_fixed_horizon_mean_cumulative_adverse_R'],
            'all_return_pct':r['all_fixed_horizon_mean_any_close_back_by_horizon']*100,
            'alive_return_pct':r['completed_in_position_mean_any_close_back_by_horizon']*100})
    # Descriptive comparison of only the two already frozen executions.
    pair=f[f.version=='BASELINE'].merge(f[f.version=='OPTIMIZED'],on=['instrument','entry_time','direction'],suffixes=('_B','_O'),validate='one_to_one')
    pairs=pair[['instrument','entry_time','direction','trade_id_B','trade_id_O','exit_time_B','exit_time_O','net_R_B','net_R_O','MFE_R_B','MFE_R_O']].copy()
    pairs['net_R_O_minus_B']=pairs.net_R_O-pairs.net_R_B
    pairs.to_csv(root/'fixed_version_entry_pairs.csv',index=False,float_format='%.15g',lineterminator='\n')
    giveback_rows=[]
    for (v,y,outcome),g in f.groupby(['version','year','outcome'],sort=True):
        giveback_rows.append({'version':v,'year':y,'outcome':outcome,'trades':len(g),'net_R':g.net_R.sum(),'mean_MFE_R':g.MFE_R.mean(),'mean_giveback_R':g.giveback_recorded_R.mean(),'median_giveback_R':g.giveback_recorded_R.median(),'mean_bars_after_peak':g.bars_after_peak_MFE.mean(),'mean_exit_stop_R':g.exit_stop_R.mean()})
    fx_decomposition=[]
    for (v,y),g in f[f.instrument.isin(['USDRUBF','CNYRUBF'])].groupby(['version','year'],sort=True):
        fx_decomposition.append({'version':v,'year':y,'trades':len(g),'mean_recorded_MFE_R':g.MFE_R.mean(),'mean_recorded_giveback_R':g.giveback_recorded_R.mean(),'mean_gross_R':g.gross_R.mean(),'mean_C1_R':g.C1_R.mean(),'mean_net_R':g.net_R.mean()})
    worst=pd.read_csv(root/'monthly.csv').sort_values('net_R').groupby(['version','instrument']).head(2).sort_values(['version','instrument','month'])
    bounds=pooled[['version','year','loss_recorded_MFE_zero','loss_no_favorable_confirmed','loss_no_favorable_unresolved',
        'loss_confirmed_MFE_ge_1','loss_possible_MFE_ge_1','loss_confirmed_MFE_ge_2','loss_possible_MFE_ge_2',
        'gross_loss_recorded_MFE_ge_1','gross_loss_recorded_MFE_ge_2']]
    lines=["""# T3/M15 Holding & Entry Diagnostics v1

## Summary для внешнего аудита

**Основная наблюдаемая слабость — недостаточное продолжение после значительной части входов. Управление выходами дополнительно отдаёт часть достигнутого движения, но массовое превращение +2R в убыток не подтверждается. Положительный C1-результат особенно в 2024 полностью зависит от сделок, фактически переживших календарную полночь. Полная исполнимая экономика переноса остаётся неизвестной.**

Это причинно-корректная реконструкция оригинального исполнения, а не идентификация причинного эффекта нового правила. Нельзя установить процент падения результата, который исправит изменение входа или выхода, без отдельного заранее заданного эксперимента. Приведённые доли относятся к объёму отрицательных R уже закрытых сделок, а не к потенциально возвратимой прибыли.

Фактический GitHub discovery/main на проверке: `d963b783b9de31fc0f2c965f6dfb11ab9cd90f5b`, merge PR #490. Данные: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Две фиксированные версии (trail ATR 3.0 / 3.5), четыре инструмента, только 2023–2024. 1 442 исходные закрытые сделки и две открытые терминальные позиции IMOEXF восстановлены; альтернативные сигналы или выходы не моделировались.

## Что считается и когда информация доступна

- R каждой сделки нормализован на её собственный первоначальный риск, Stop = entry ± 2 ATR M15. PF относится к C1 Net R; Gross PF дан отдельно в CSV. C1 = 2 × research unit / initial risk; units USDRUBF/CNYRUBF 0.001, GLDRUBF 0.1, IMOEXF 0.5 сохранены из PR #490.
- Свеча M15 становится доступна после закрытия; вход принят по закрытию сигнальной свечи. H1 использует исходные дневные ordinal-блоки из четырёх последовательных M15, лишь после их завершения. Последний доступный H1 имеет timestamp ≤ entry; Donchian использует предыдущие 20 свечей через shift(1). EMA, ATR, ADX и Donchian явно пересекают календарные дни, как в исходном исполнении; блоки H1 сбрасываются по московской дате закрытия.
- EMA75, slope5, ADX14>20 и H1 ATR14>ATRMean20 — исходные состояния, не новые фильтры. Все entry-признаки доступны при закрытии сигнальной свечи. Из этих OHLC нельзя доказать исполнимый fill по тому же закрытию после вычисления сигнала.
- SAME_DAY / CROSS_MIDNIGHT определяются московскими календарными датами entry/exit. Год и месяц — дата выхода; entry_year сохранён. Группы времени: ≤60, (60,240], (240,480], (480,1440], >1440 минут. Также показаны фактические бары. Это фиксированные описательные интервалы, не подобранные торговые параметры.
- Stop действует со следующей свечи: carried Stop проверяется первым; при гэпе используется неблагоприятный Open. Только пережитая свеча обновляет favorable extreme и Stop. На закрытии той же свечи разрешён исходный повторный вход. Stop только ужесточается; не округляется к тиковой сетке, как в исходном исследовании.
- Длительность, перенос, MAE/MFE, исход WIN/LOSS и первые свечи — **ретроспективные характеристики**. Они не используются для отбора входов. OHLC после Stop в фиксированных горизонтах помечены как движение цены после завершённой сделки. Условие «ещё открыта» тоже создаёт survivor selection и не является правилом.
- 2023 не полон для GLD (старт 11.07) и IMOEX (14.11; всего девять сделок на версию). Разница состава между годами не означает единый рыночный режим. 2025–2026 OHLC не читались исследовательским парсером; полные файлы хешировались как непрозрачные байты для проверки pin.
- Суммы R четырёх инструментов ниже — только бухгалтерия одинаковых условных единиц риска. Это **не портфельная доходность**, CAGR, RUB P&L или моделирование капитала. DD — просадка последовательности закрытых сделок в R с нулевым начальным уровнем, без внутрипозиционной переоценки/маржи; ties сортируются exit_time, instrument, trade_id.

## A. Продолжительность и перенос: подтверждённые результаты

Общая предпосылка «внутри дня всегда убыток» слишком сильна: Baseline в 2023 даёт +5.43R внутри дня; USDRUBF в 2023 даёт +14.90R / +5.45R внутри дня у двух версий. **В 2024 каждый инструмент обеих версий отрицателен внутри дня и положителен через полночь**. Ни одна из этих групп не была доступна для выбора при входе.
""",
        table(carry,['version','year','carry','trades','PF_net_C1','gross_R','C1_R','net_R','mean_MAE_R','mean_MFE_R','max_closed_trade_drawdown_R','top5_share_positive_R']),
        '\nРазрез инструмент × год × перенос:\n',
        table(pd.read_csv(root/'carry_by_year.csv'),['version','instrument','year','carry','trades','PF_net_C1','gross_R','net_R']),
        '\nФактическая длительность (условная pooled-бухгалтерия):\n',
        table(pd.DataFrame(hold_rows),['version','year','holding_bucket','trades','PF_net_C1','gross_R','net_R','mean_net_R','mean_MFE_R']),
        """
Обе версии убыточны среди сделок ≤4 часов, а более длинные группы положительны в двухлетней pooled-бухгалтерии. Это естественно совместимо с устройством исполнения: неудачные входы достигают Stop быстро; устойчивые движения дольше сохраняют позицию. Это не доказывает преимущество обязательного минимального удержания или запрета закрытия в день входа. Вход поздно вечером может пересечь полночь быстрее раннего входа; entry_hour.csv позволяет проверить состав по времени входа, без создания SESSION-правила.

Календарная полночь не равна фактическому ночному переносу. Закрытие последней свечи в 00:00 уже относится к следующей дате; вход в 00:00 перед утренним открытием может иметь ночной перерыв, оставаясь на той же календарной дате. Поэтому дополнительно показан наблюдаемый нерабочий ночной gap: разница соседних доступных M15 >15 минут, дата следующего открытия отличается от даты последней торговавшей минуты предыдущей свечи. Это диагностика gaps в источнике, не биржевой funding-календарь и не доказательство реального исполнения через клиринг.
""",
        table(pd.DataFrame(kind_rows),['version','year','carry_kind','trades','net_R']),
        """
В 2024 pooled SAME_DAY даёт -119.84R / -130.96R, CROSS_MIDNIGHT +148.97R / +190.84R; итог +29.14R / +59.88R. Оба направления внутри дня в 2024 отрицательны в pooled-бухгалтерии. Разрезы direction × instrument × year × carry/holding доступны в CSV. Удаление overnight-группы задним числом не является допустимым бэктестом.

## B. Первые 1/2/4 завершённые свечи: подтверждённые результаты

Номер свечи — следующий доступный M15 после entry, а не обязательно 15/30/60 минут календарного времени: пропуски/выходные увеличивают elapsed_minutes. Для каждого исходного входа показаны signed close R, благоприятный/неблагоприятный экстремум данной свечи и накопленный экстремум до горизонта, close за исходным breakout level, wick-возврат и хотя бы одно закрытие обратно за уровнем. Исходный breakout level не пересчитывается по будущим свечам.

`all_*` ниже включает цену и после выхода; `alive_*` включает только свечи, завершившиеся строго раньше Stop-выхода. Свеча Stop исключена из `alive_*`, даже если запись exit_time соответствует её закрытию. Эти две оценки нельзя смешивать или выдавать движение уже закрытой позиции за удержанную прибыль.
""",
        table(pd.DataFrame(early_rows),['version','year','bar','outcome','trades','alive_before_close','all_close_R','all_cum_favorable_R','all_cum_adverse_R','all_return_pct','alive_return_pct']),
        """
В 2024 убыточные входы уже на первой свече имеют среднее закрытие -0.112R / -0.110R против +0.168R / +0.156R у победителей. К четвёртой свече 65.6% / 65.2% будущих проигравших имели хотя бы одно закрытие обратно за breakout level, против 32.4% / 35.9% победителей. Среди ещё открытых до четвёртого закрытия: 55.2% / 54.6% против 32.2% / 35.8%. Различие сохраняется, но survivor-подвыборка сама зависит от Stop. Эти числа подтверждают связь слабого продолжения/возврата с итоговым убытком; не доказывают пригодность ONE_BAR и не являются готовым причинным фильтром.

Предвходовые признаки в entry_features_by_outcome.csv: средние и медианы breakout penetration, тела/диапазона сигнальной свечи, исходных ATR M15/H1, ATR ratio, ADX, расстояния H1 Close от EMA, signed slope и возраста H1. Полные EMA/ADX/ATR/H1-trend доступны по каждой сделке. EMA в исходном T3 находится на H1; новой M15 EMA не добавлено.

Нет универсального монотонного разделения по силе пробоя или ADX. Например, Baseline CNY 2024: median penetration у проигравших 0.231R против 0.150R у победителей; USDRUBF почти одинаков 0.216R против 0.215R. ADX Baseline GLD 2023 у проигравших выше (33.09 против 31.39), а в 2024 ниже (29.46 против 32.33). В OPTIMIZED эти различия также не дают единого направления для всех инструментов. Подбор порогов/индикаторов не проводился. Объяснение через ложные пробои/диапазон — рабочая гипотеза; формальное наблюдение здесь лишь возврат цены через исходный уровень и слабое последующее движение.

## C. Первоначальный Stop, trailing и потеря движения

stop_trajectory.csv содержит entry, каждую пережитую свечу и исходный exit, stop_before/after в цене и R, proposed Stop, отношение текущего ATR к entry ATR, trailing distance R, накопленные исходные MAE/MFE, ужесточение без нового extreme и close через новый Stop. Две терминальные позиции включены в траектории с OPEN_TERMINAL, исключены из закрытой экономики. Новых закрытий им не назначено.

Исходный recorded MFE исключает всю Stop-свечу. Это консервативная **модельная** оценка, не доказательство отсутствия любой favourable tick. `observed_MFE_lower_R` добавляет известный Open перед внутрисвечным Stop и сам fill. `possible_MFE_upper_R` допускает благоприятный экстремум Stop-свечи до касания Stop. Если Stop срабатывает уже на Open (включая Open ровно на Stop), все последующие wick исключены и upper=lower. Порядок High/Low внутри M15 не выдумывается. На пережитых свечах OHLC целиком относится к открытой позиции.

Для утверждения «не было благоприятного движения вообще»: confirmed означает upper≤1e-12; unresolved означает lower≤1e-12<upper. Оставшаяся разница между recorded zero и этими категориями — благоприятный Open, который исходный MFE не учёл. Числа +1/+2 в bounds относятся к net-loss; gross-loss отдельно показан по исходному MFE.
""",
        table(bounds,list(bounds.columns)),
        '\nРазложение объёма отрицательных C1 R по записанному MFE (описательная бухгалтерия):\n',
        table(pd.DataFrame(loss_rows),list(loss_rows[0])),
        """
В 2024 MFE<0.5R: 164/311 убыточных сделок Baseline (156.40R убытков, 67.5% отрицательного объёма) и 153/290 OPTIMIZED (151.34R, 65.0%). MFE≥1R с net-loss: 59 / 58 сделок, соответственно 20.22R / 23.98R (8.7% / 10.3% объёма убытков); из них 53 / 50 закрылись внутри дня. MFE≥2R с net-loss — только 3 / 2; с gross-loss — 2 / 1. Поэтому массовый механизм «+2R затем полный убыток» не подтверждён. Это не говорит, что всю потерю после MFE можно было бы реализовать на пике.

Формула текущего candidate Stop в R: `running_extreme_R − (trail_atr / 2) × ATR_current / ATR_entry`; активный Stop — максимум достигнутого signed Stop. При неизменном ATR trail-distance равна 1.5R / 1.75R. Достижение +1R не обязано ни включать безубыток, ни блокировать прибыль: такого механизма в исходной стратегии нет. Сжатие ATR может ужесточать Stop без нового favorable extreme; расширение ATR снижает candidate, но ранее достигнутый Stop не ослабляет. Реальный эффект считается по исходным траекториям, без моделирования альтернативы.
""",
        table(pd.DataFrame(stop_rows),list(stop_rows[0])),
        '\nОтдача движения и время после пика по фактическому исходу:\n',
        table(pd.DataFrame(giveback_rows),list(giveback_rows[0])),
        """
В 2024 Stop ужесточался без нового extreme 3 128 / 3 273 раза; такие изменения происходят за счёт ATR, а не нового ценового пика. 18 / 16 пережитых свечей закрылись уже через новый рассчитанный Stop: историческая модель активирует его лишь на следующей свече. Это конкретное ограничение close-only stop updates, не доказанный дефект LIVE. Положительный Stop затем net-loss встречается 13 / 6 раз, при этом гэпы и C1-flips могут пересекаться. Стоп выше entry сам по себе не гарантирует положительный net-fill при гэпе/затратах.

`giveback_recorded_R = recorded MFE − gross_R` — отданное движение в ценовой траектории, не исполнимая прибыль на известном пике. bars_after_peak_MFE показывает, где во времени оно теряется; пик — первое достижение максимума. В среднем recorded giveback в 2024 составляет 1.316R / 1.451R; в 2023 он больше, 1.481R / 1.628R. Поэтому сама средняя отдача не объясняет ухудшение 2024: уменьшился и запас favorable движения, особенно в USDRUBF.

## Концентрация, календарные месяцы и сравнение годов

Top5 — пять крупнейших **положительных** net-сделок в данной instrument/year группе. Их удаление — стресс-описание концентрации, не торговый отбор и не новое Robustness-испытание. На выборках с ≤5 победителями удаляются все победители; отрицательные сделки не удаляются.
""",
        '\nБухгалтерское разложение среднего Gross R для Si/CNY: `mean Gross = mean recorded MFE − mean recorded giveback`:\n',
        table(pd.DataFrame(fx_decomposition),list(fx_decomposition[0])),
        '\nУ Si/CNY в 2024 уменьшились и MFE, и средняя отдача движения. Снижение отдачи частично компенсировало снижение MFE; это не подтверждает объяснение валютного провала только чрезмерно поздним выходом. Это тождество на наблюдаемых сделках, а не причинная доля качества входа.\n',
        table(iy,['version','instrument','year','trades','PF_net_C1','gross_R','C1_R','net_R','mean_MFE_R','top5_share_positive_R','net_R_without_top5_winners']),
        """
Во всех восьми instrument/version результатах 2024 удаление пяти лучших победителей оставляет отрицательный net. Top5 дают 30.6–47.5% положительных R; положительный итог зависит от хвоста победителей, хотя большинство отдельных overnight-подгрупп сохраняют плюс и без своих top5. Внутридневные группы USDRUBF 2023 положительны только с крупными победителями.

Главное падение 2023→2024 в FX: Si/CNY Gross 94.03→19.76R Baseline и 98.20→35.72R OPTIMIZED, до C1. USDRUBF Net 64.02→2.97R / 69.87→4.26R. Его mean MFE 2.195→1.263R / 2.467→1.374R. CNY второй фиксированной версии не ухудшается по Net (23.49→23.87R). GLD и IMOEX улучшаются относительно короткого 2023. Единого подтверждённого режима ухудшения всех четырёх инструментов нет.

Два худших наблюдаемых месяца каждого instrument/version приведены ниже; monthly.csv содержит все месяцы с закрытыми сделками, monthly_carry.csv — month × direction × carry. Месяцы без закрытий имеют 0R, до старта инструмента — отсутствующую историю, не отрицательные/нулевые торговые месяцы. Неполные стартовые месяцы не превращались в полные годы.
""",
        table(worst,['version','instrument','month','trades','PF_net_C1','gross_R','C1_R','net_R']),
        f"\nОбе фиксированные версии имеют {len(pair)} общих instrument/entry_time/direction; OPTIMIZED содержит {len(f[f.version=='OPTIMIZED'])} закрытых сделок, Baseline {len(f[f.version=='BASELINE'])}. Сопоставление оригинальных выходов дано в fixed_version_entry_pairs.csv. Более длинный trailing меняет продолжительность и доступность повторных входов; агрегатное сравнение версий не изолирует один эффект выхода и не выбирает победителя.\n",
        """
## D. C1 и полная экономика переноса

Нормализованная C1-модель — один исходный исследовательский unit на сторону, уже вычтенный из Gross. Это не подтверждение реального тарифа брокера/биржи и не полный spread/slippage. Дополнительные комиссии, spread, slippage, funding/вариационные корректировки и дивидендные поправки **UNRESOLVED, а не 0**. Номинал, количество контрактов, маржа, обеспечение и real fills не моделировались. Ночная календарная группа не соответствует автоматически конкретному расчётному событию funding.

Для каждого instrument/year показан оставшийся запас C1. Отрицательный break-even означает, что дополнительных расходов система уже не выдерживает; это не отрицательный реальный тариф. Формулы:

- Постоянный дополнительный расход `c R / trade`: `c* = sum(net_R) / N`.
- Постоянные совокупные round-trip `b bps` от **entry price-equivalent notional** каждой сделки: дополнительный R = `b × entry_price / (10 000 × initial_risk)`; `b* = sum(net_R) / sum(entry_price / risk / 10 000)`. Это не тариф на сторону и не RUB-прибыль портфеля.
- Постоянный drag в bps на 24 часа по фиксированному entry notional: `d* = 240 000 × sum(net_R) / sum(entry_price / risk × elapsed_hours)`. Это единица чувствительности, **не оценка реального funding**, который может иметь иной базис, событие расчёта, знак и зависимость от стороны. Ночные/выходные часы учтены, но это не знание расписания списаний.

Три предела — отдельные one-at-a-time математические бюджеты; их нельзя одновременно потратить целиком. Реальный полный результат равен исходному net минус сумма документально восстановленных дополнительных расходов в R, включая кредитовые/дебетовые корректировки со знаком. Величины не имитируют реальные тарифы.
""",
        table(iy,['version','instrument','year','net_R','extra_cost_break_even_R_per_trade','extra_cost_break_even_bps_entry_notional','extra_drag_break_even_bps_per_24h']),
        """
В 2024 USDRUBF выдерживает лишь 0.0258R / 0.0387R дополнительного постоянного расхода на сделку; эквивалентный совокупный round-trip бюджет 0.689 / 1.027 bps. Baseline CNY/IMOEX — около 1.964 / 1.902 bps. Это узкий исследовательский запас. Overnight-результат превышает общий итог, потому что покрывает внутридневные убытки; к нему добавляется экспозиция к неизвестной полной экономике переноса. Без исторического учёта этих корректировок прибыльность вечных фьючерсов не доказана.

## Следующие эксперименты: приоритеты, не выполнены

1. **ONE_BAR**: заранее фиксированный отдельный эксперимент раннего продолжения/возврата через исходный breakout level после первого завершённого M15. Основание — слабость уже первой свечи и большой отрицательный объём low-MFE. Проверять полный исходный поток без выбора будущих победителей, цену исполнения только после появления признака, потери крупных победителей и C1. Конкретное правило следует определить до запуска; здесь оно не конструируется и не исполняется.
2. **TRAIL1**: отдельно проверить заранее определённую причинную механику исходного ATR trailing — активацию на следующей свече, зависимость от ATR-сжатия и отдачу favorable движения. Основание — тысячи ужесточений без нового пика и отсутствие защиты после +1R. Сначала формализовать одно изменение и полную цену исполнения; нельзя превращать исходный MFE-пик в доступный exit. Измерять повреждение длинных победителей вместе с уменьшением убытков.
3. **SESSION**: после восстановления исторической полной экономики переноса проверить один заранее заданный session/holding протокол на всём потоке. Основание — зависимость результата 2024 от overnight-позиций и узкий cost slack USDRUBF. Не отбирать сделки по будущему exit_day; определить события сессии/клиринга по известному календарю, а реальные funding/adjustments — по архивным данным.

**LOCK1 пока ниже приоритета**: достигавших +2R и завершившихся net-loss в 2024 лишь 3 / 2; убытки после +1R дают 8.7% / 10.3% отрицательного объёма. Это не отсутствие giveback у победителей и не доказательство бесполезности lock; отдельный lock может также уничтожать главный прибыльный хвост. Четвёртый эксперимент не предлагается.

## Независимая проверка и границы вывода

verify.py использует отдельные стандартные рекурсивные формулы и уже независимый oracle PR #490; не импортирует diagnose.py/pandas/numpy. Повторно считает все оригинальные сделки, H1/entry-признаки, каждую строку Stop, первые свечи и центральные метрики всех групп. Точность и объём сверки — AUDIT_RESULTS.json. Hand-calculated tests покрывают stop-first, гэп, Open ровно на Stop, ATR-сжатие, зеркальный SHORT, полночь и неизменность предвходовых признаков при замене будущего OHLC.

Два свежих процесса сравниваются по SHA-256 всех сгенерированных CSV/JSON, отчёта и SVG (REPEATABILITY.json); исходный каталог и data pin проверяются на неизменность (SCOPE_CHECK.json). Независимость здесь **реализационная, тот же автор**. Внешний аудитор ещё не проверил результат. Никакие изменения LIVE/TradingSystemLab, исходных результатов, закреплённых данных или Optimization Level Rejection не выполнялись; новых Optimization/Robustness/WF/TRUE OOS нет. После создания отдельного Draft PR — остановка для внешнего аудита, без merge/auto-merge.

![Descriptive holding and calendar contributions](holding_summary.svg)
"""]
    (root/'REPORT.md').write_text('\n\n'.join(lines).rstrip()+'\n')
    matplotlib.rcParams.update({'svg.hashsalt':'t3-m15-holding-v1','font.family':'DejaVu Sans','font.size':10})
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    labels=['<=60m','60–240m','240–480m','480–1440m','>1440m']
    for (v,y),g in pd.DataFrame(hold_rows).groupby(['version','year'],sort=True):
        g=g.sort_values('holding_bucket');axes[0].plot(range(5),g.mean_net_R,marker='o',label=f'{v} {y}')
    axes[0].set_xticks(range(5),labels);axes[0].set_ylabel('Mean closed-trade C1 Net R');axes[0].set_title('Actual holding duration (retrospective)');axes[0].legend(fontsize=8);axes[0].axhline(0,color='black',lw=.8)
    for n,(v,y) in enumerate(sorted(set(zip(carry.version,carry.year)))):
        sub=carry[(carry.version==v)&(carry.year==y)]
        axes[1].bar(n-.18,float(sub[sub.carry=='SAME_DAY'].net_R.iloc[0]),width=.36,color='#bf5656',label='Same date' if n==0 else None)
        axes[1].bar(n+.18,float(sub[sub.carry=='CROSS_MIDNIGHT'].net_R.iloc[0]),width=.36,color='#287d74',label='Cross midnight' if n==0 else None)
    axes[1].set_xticks(range(4),['B 2023','B 2024','O 2023','O 2024']);axes[1].set_ylabel('Sum of normalized trade R');axes[1].set_title('Calendar group contributions (retrospective)');axes[1].legend();axes[1].axhline(0,color='black',lw=.8)
    for ax in axes:ax.grid(axis='y',alpha=.2)
    fig.suptitle('Fixed T3/M15 • four instruments • risk-unit bookkeeping, not portfolio return',fontsize=12)
    fig.tight_layout();fig.savefig(root/'holding_summary.svg',metadata={'Date':None});plt.close(fig)
    svg=root/'holding_summary.svg'
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    manifest=json.loads((root/'MANIFEST.json').read_text())
    manifest['deterministic_artifacts']=sorted(set(manifest['deterministic_artifacts']+['REPORT.md','holding_summary.svg','fixed_version_entry_pairs.csv']))
    manifest['runtime']['matplotlib']=matplotlib.__version__
    (root/'MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    hashes=json.loads((root/'ARTIFACT_SHA256.json').read_text())
    hashes['MANIFEST.json']=hashlib.sha256((root/'MANIFEST.json').read_bytes()).hexdigest()
    for name in ['REPORT.md','holding_summary.svg','fixed_version_entry_pairs.csv']:hashes[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
    (root/'ARTIFACT_SHA256.json').write_text(json.dumps(hashes,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'report':'REPORT.md','hashes':len(hashes),'common_entries':len(pair)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE);a=p.parse_args();main(a.output)
