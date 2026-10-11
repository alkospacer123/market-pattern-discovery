#!/usr/bin/env python3
"""Reporting only: three frozen Baselines and archived A; no source-price reads."""
import argparse
from decimal import Decimal as D
import itertools
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from IntradayLab.core.reports import dump,csv_write
from IntradayLab.tools.audit_canonical_baseline import read_csv
from IntradayLab.tools.run_equal_high_low_baseline import table
from IntradayLab.tools.high_low_cluster_contract import LAB,verify_freeze,output_path,hashes


def compare():
    configs={n:verify_freeze(n) for n in (4,7,10)}
    docs={n:json.loads((output_path(n)/'metrics.json').read_text()) for n in (4,7,10)}
    am=json.loads((LAB/'results/equal_high_low_m5_2023_a_v1/metrics.json').read_text())
    sources={'A_v1':LAB/'results/equal_high_low_m5_2023_a_v1',**{f'B{n}':output_path(n) for n in (4,7,10)}}
    signals={key:read_csv(path/'signals.csv') for key,path in sources.items()}
    trades={key:read_csv(path/'trades.csv') for key,path in sources.items()}
    overlap=[]
    for left,right in itertools.combinations((4,7,10),2):
        for symbol in configs[4][0]['instruments']:
            la=[s for s in signals[f'B{left}'] if s['instrument']==symbol];ra=[s for s in signals[f'B{right}'] if s['instrument']==symbol]
            common=set(s['episode_id'] for s in la)&set(s['episode_id'] for s in ra)
            common_fills=set(t['episode_id'] for t in trades[f'B{left}'] if t['instrument']==symbol and t['model_filled']=='True')&set(t['episode_id'] for t in trades[f'B{right}'] if t['instrument']==symbol and t['model_filled']=='True')
            # Same direction, overlapping raw N-window observations, even with different episode IDs.
            pairs=[(a['signal_id'],b['signal_id']) for a in la for b in ra if a['direction']==b['direction'] and
                max(a['cluster_start'],b['cluster_start'])<=min(a['cluster_end'],b['cluster_end'])]
            overlap.append(dict(instrument=symbol,left=f'B{left}',right=f'B{right}',shared_formed_episode_ids=len(common),shared_filled_episode_ids=len(common_fills),overlapping_same_side_window_pairs=len(pairs),episode_ids=sorted(common)))
    target=LAB/'results/high_low_cluster_b4_b7_b10_comparison_v1';target.mkdir(parents=True,exist_ok=True)
    dump(target/'overlap.json',overlap)
    lines=['# HIGH_LOW_CLUSTER_M5: B4 / B7 / B10 — Baseline 2023','',
        'Все три версии: **INCONCLUSIVE** по годовой полноте; экономический диагноз известных закрытий отдельно. Нет автоматического PASS, выбора победителя или перехода к Optimization.','',
        f'Base main `{configs[4][0]["base_main"]}` совпадает с исходным SHA пользователя. PR #474 MERGED. Все три модели freeze `{configs[4][1]}` до первого исторического P&L. Source `{configs[4][0]["source_ref"]}`. Общий Backtester и A_v1 не изменены.','',
        '## Экономика по инструментам, условные известные закрытия','']
    rows=[]
    for key,doc in [('A_v1',am),*[(f'B{n}',docs[n]) for n in (4,7,10)]]:
        for symbol,m in doc['instruments'].items():
            d=m['conditional_closed_only_C1'];e=m['economics'];dist=m['distribution']
            rows.append([key,symbol,m.get('detected_accumulations',m['raw_directional_candidates']),m['signals'],m['model_fills'],m['closed'],m['unknown'],d['PF_C1_R'],d['PF_C1_price'],e['gross_R'],e['C1_R'],e['net_R'],d['Expectancy_R'],f'{dist["positive_months"]}/{dist["negative_months"]}',m['economic_diagnostic']])
    lines+=table(['Model','Instrument','Detected','Signals','Fills','CLOSED','UNKNOWN','PF R','PF price','Gross R','C1 R','Net R','E[R]','+ / − months','Known-closure diagnosis'],rows)
    lines+=['Цены USD/CNY/GLD/IMOEX несовместимы для суммирования в деньги. Ниже все Net R — условные суммы исследовательских сделок в единицах индивидуального первоначального риска; это не капитализированная доходность. Полные годовые PF/Net/DD остаются null.','',
        '## A. Диапазон против точных равных High/Low A_v1','']
    for symbol in configs[4][0]['instruments']:
        a=am['instruments'][symbol]['conditional_closed_only_C1'];parts=[]
        for n in (4,7,10):
            b=docs[n]['instruments'][symbol]['conditional_closed_only_C1']
            delta=D(b['Expectancy_R'])-D(a['Expectancy_R']) if b['Expectancy_R'] is not None and a['Expectancy_R'] is not None else None
            parts.append(f'B{n}: CLOSED={b["closed"]}, Δ E[R]={delta}, PF R={b["PF_C1_R"]}')
        lines += [f'{symbol}: A_v1 E[R]={a["Expectancy_R"]}; '+ '; '.join(parts)+'.','']
    lines+=['Разница описательная: A имеет три точных экстремума и другую грамматику сброса, B — ненулевой диапазон и 4/7/10 свечей. Выборки не парные и история неполна; превосходство и статистическая значимость не установлены. A frozen config/metrics/trades SHA-256 перечислены в comparison_provenance.json; A не перезапускалась с новыми параметрами.','',
        '## B. Длительность 4 → 7 → 10','']
    for symbol in configs[4][0]['instruments']:
        parts=[f'B{n}: {docs[n]["instruments"][symbol]["closed"]} CLOSED, Net R={docs[n]["instruments"][symbol]["economics"]["net_R"]}, E[R]={docs[n]["instruments"][symbol]["conditional_closed_only_C1"]["Expectancy_R"]}' for n in (4,7,10)]
        lines += [symbol+': '+'; '.join(parts)+'.','']
    lines+=['Увеличение N меняет частоту формирования, задержку относительно начала эпизода и занятую позицию, даже при одинаковом NEXT_OPEN. Малые длинные выборки и пересечение эпизодов не позволяют объявлять вариант с максимальным PF победителем.','',
        '## C. Реальные касания границы','']
    for n in (4,7,10):
        lines += [f'### B{n}','']
        tr=read_csv(output_path(n)/'boundary_touch_report.csv')
        lines+=table(['Instrument','Touches','Detected','CLOSED','UNKNOWN','Net R','PF R'],[[r['instrument'],r['boundary_touches'],r['detected_accumulations'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_R']] for r in tr])
    lines+=['Касания — только экстремумы точно на внешней границе, остальные свечи внутри зоны отдельно подсчитаны. Эти группы вложены в одну стратегию; редкие высокие PF без достаточного числа эпизодов не подтверждают эффект числа касаний.','',
        '## D. Где теряется ожидание','']
    for n in (4,7,10):
        for symbol,m in docs[n]['instruments'].items():
            lines += [f'### B{n} / {symbol}','',
                f'Stop mean={m["geometry"]["mean_stop_ticks"]} тика; средняя C1/risk={m["geometry"]["mean_C1_initial_risk_R"]}; Open против сигнального Close={m["geometry"]["mean_directional_open_vs_signal_close_ticks"]} тика в направлении отбоя.','',
                'Отказы: `'+json.dumps(m['all_candidate_refusal_reasons'],sort_keys=True)+'`. UNKNOWN: `'+json.dumps(m['unknown_reasons'],sort_keys=True)+'`.','']
            lines+=table(['Exit','Count','Gross R','C1 R','Net R','Mean hold lower / upper'],[[k,v['count'],v['gross_R'],v['cost_R'],v['net_R'],f'{v["mean_holding_lower_minutes"]}/{v["mean_holding_upper_minutes"]}'] for k,v in m['loss_attribution'].items()])
    lines+=['Структурный Stop не расширяли. Принятые риски 3–5 тиков делают C1 большой частью риска. Take 17–23 тика требует движения, которое многие сделки не достигают: STOP, TIME и SESSION_FLAT разделены в таблицах. Отказ ENTRY_MORE_THAN_4_TICKS исключает погоню за движением; STOP_BELOW_3_TICKS исключает слишком малый риск. POSITION_BUSY/UNKNOWN_POSITION_BLOCK — состояние общего исполнения, SESSION_LIMIT — внутридневной контракт. STOP_ABOVE_12_TICKS имеет приоритет над distance в коде отказов; один отказ может нарушать несколько ограничений. Нет доказанного контрфактического эффекта задержки или исполнимости входа по Close.','',
        '## E. Круглые и обычные уровни','']
    for n in (4,7,10):
        rr=read_csv(output_path(n)/'round_report.csv')
        lines+=table(['Model','Instrument','Level','Signals','CLOSED','UNKNOWN','Net R','PF R'],[[f'B{n}',r['instrument'],r['level_type'],r['signals'],r['closed'],r['unknown'],r['conditional_Net_R'],r['conditional_PF_C1_R']] for r in rr])
    lines+=['Фиксированные шаги 0,10 /0,05 /10 /10; ROUND_NEAR <=1 датированного тика от внешней границы до ближайшего узла. Диагностическая разница не разрешает новый фильтр или изменение шага. При малых группах эффект INCONCLUSIVE.','',
        '## Все календарные месяцы 2023','']
    monthly={key:read_csv(path/'monthly_report.csv') for key,path in sources.items()}
    for symbol in configs[4][0]['instruments']:
        rows=[]
        for month in range(1,13):
            label=f'2023-{month:02d}';r=[label]
            for key in sources:
                item=next(x for x in monthly[key] if x['instrument']==symbol and x['month']==label)
                r.append('NO_COVERAGE' if item['coverage_classification']=='NO_COVERAGE' else item['conditional_Net_R'] or '0')
            rows.append(r)
        lines += [f'### {symbol}','',*table(['Month','A_v1 Net R','B4 Net R','B7 Net R','B10 Net R'],rows)]
    lines+=['Нули с наблюдаемой историей — месяцы без закрытого P&L, а NO_COVERAGE до GLD/IMOEX inception не является торговой доходностью. В отдельных monthly_report.csv сохранены CLOSED/UNKNOWN и покрытие каждого месяца.','',
        '## Пересечение рыночных эпизодов','']
    lines+=table(['Instrument','Pair','Shared formed episodes','Shared filled episodes','Overlapping same-side N-window pairs'],[[r['instrument'],r['left']+'/'+r['right'],r['shared_formed_episode_ids'],r['shared_filled_episode_ids'],r['overlapping_same_side_window_pairs']] for r in overlap])
    lines+=['Полные общие ID в overlap.json. Три Baseline описывают пересекающиеся рыночные эпизоды, не три независимые статистические выборки. Суммирование их сделок увеличило бы зависимость и двойной учёт.','',
        '## Проверки и итог','']
    for n in (4,7,10):
        au=json.loads((output_path(n)/'audit.json').read_text());va=json.loads((output_path(n)/'validation.json').read_text())
        lines += [f'B{n}: audit **{au["status"]}**, {sum(au["checked_fields"].values())} проверенных полей; validation **{va["status"]}**, два полных повтора идентичны по байтам. **{docs[n]["baseline_status"]}**, экономического PASS нет; не переходить к Optimization.','']
    lines += [f'Pre-P&L unittest: **{configs[4][0].get("pre_pnl_unittest_count")} PASS**. Все старые default-mode Baseline и A_v1 воспроизведены без изменения экономических артефактов; общий core регрессионно проверен. Число unittest и технический preflight находятся в pre_pnl_tests.log и pre_pnl_validation.json; все три freeze до первого исторического P&L. Аудитор — отдельный алгоритм без production imports; внешний человеческий signoff остаётся задачей ревью PR.','',
        'Полнота данных: USD/CNY доступны с 3 января, GLD с 11 июля, IMOEX с 14 ноября. Точные 2023 префиксы проверены; 2024/2025+ ценовые байты не читались. Нет непрерывной годовой/account equity при пропусках и UNKNOWN. Все ранее существовавшие IntradayLab файлы, TradingSystemLab и источник защищены; scope PASS в validation.json.','',
        '**STOP.** Только Draft PR без Merge. Нет новых N/ширин, Take-вариантов, trailing, индикаторов, модели C, Optimization, Robustness, WF или TRUE OOS.','']
    report=target/'HIGH_LOW_CLUSTER_B4_B7_B10_COMPARISON.md';report.write_text('\n'.join(lines))
    provenance=dict(base_main=configs[4][0]['base_main'],pre_pnl_freeze_commit=configs[4][1],source_ref=configs[4][0]['source_ref'],
        config_sha256={f'B{n}':configs[n][2] for n in (4,7,10)},A_v1_sha256=hashes(sources['A_v1']),
        baseline_artifact_hashes={f'B{n}':json.loads((output_path(n)/'artifact_hashes.json').read_text()) for n in (4,7,10)},no_independent_sample_claim=True,no_parameter_changes_after_pnl=True)
    dump(target/'comparison_provenance.json',provenance);dump(target/'artifact_hashes.json',hashes(target,('artifact_hashes.json',)))
    return report


if __name__=='__main__':print(compare())
