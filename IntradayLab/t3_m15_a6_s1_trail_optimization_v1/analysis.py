"""Preregistered descriptive tables; no feedback into replay or grid."""
import numpy as np
from collections import defaultdict
import common as C
from primary_metrics import metrics

ECON_TRADE=('entry_time','entry_price','initial_stop','initial_risk','exit_time','exit_price','gross_R','activation_time','MFE_R','MAE_R','active_stop','last_close','last_close_price','threshold_activated')
ECON_STOP=('bar_open_time','bar_close_time','active_stop','active_stop_next_bar','phase','exit_price','activated_before','activated_after','activation_time_after','extreme_before','extreme_after','stop_hit')

def equal(a,b):
    if isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)) and not isinstance(b,bool):return abs(a-b)<=1e-8
    return a==b

def equivalent(a,b,da,db):
    if set(k for k in ECON_TRADE if k in a)!=set(k for k in ECON_TRADE if k in b):return False
    if any(not equal(a.get(k),b.get(k)) for k in ECON_TRADE):return False
    return len(da)==len(db) and all(all(equal(x.get(k),y.get(k)) for k in ECON_STOP) for x,y in zip(da,db))

def entry_id(r):return '|'.join((r['instrument'],r['direction'],r['signal_time'].isoformat()))

def build(out,frames):
    tables={k:[] for k in ('summary','monthly','funnel_occupancy','lineage','winner_retention','new_entries','november','closed_equity','negative_results','top_winners','comparison','neighbor_comparison','historical_references')}
    pools={v:{k:[r for r in out[k] if r['version']==v] for k in out} for v in C.VERSIONS}
    for v,trail in C.VERSIONS.items():
        p=pools[v];t=p['trades'];op=p['OPEN_POSITIONS'];sn=p['PERIOD_END_OPEN_POSITIONS'];e=p['entry_opportunities'];d=p['stop_decisions'];ident={'variant':v,'trail_atr':trail}
        for scope in ('ALL_FOUR',*C.SYMBOLS):
            symbols=C.SYMBOLS if scope=='ALL_FOUR' else (scope,)
            first=min(frames[s].index[0] for s in symbols).strftime('%Y-%m')
            for direction in ('ALL','LONG','SHORT'):
                base=[r for r in t if r['instrument'] in symbols and (direction=='ALL' or r['direction']==direction)]
                for year in ('ALL',2023,2024):
                    rows=[r for r in base if year=='ALL' or r['exit_time'].year==year];calendar=[m for m in C.CALENDAR if year=='ALL' or m.startswith(str(year))]
                    o=op if year=='ALL' else [r for r in sn if r['month']==f'{year}-12']
                    opened=sum(r['instrument'] in symbols and (direction=='ALL' or r['direction']==direction) for r in o)
                    row=ident|{'scope':scope,'direction':direction,'year':year,'period_end_OPEN':opened}|metrics(rows,calendar);tables['summary'].append(row)
                    if scope=='ALL_FOUR' and direction=='ALL' and year!='ALL' and (row['gross_PF'] is None or row['gross_PF']<1.7):tables['negative_results'].append(ident|{'year':year,'finding':'ANNUAL_PF_MINIMUM_NOT_MET','value':row['gross_PF']})
                for month in C.CALENDAR:
                    rows=[r for r in base if r['exit_time'].strftime('%Y-%m')==month]
                    row=ident|{'scope':scope,'direction':direction,'month':month,'coverage':'NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if month==first and scope in ('GLDRUBF','IMOEXF') else 'AVAILABLE'}|metrics(rows,[month]);tables['monthly'].append(row)
                    if scope=='ALL_FOUR' and direction=='ALL' and row['gross_R']<0:tables['negative_results'].append(ident|{'year':int(month[:4]),'month':month,'finding':'NEGATIVE_MONTH','value':row['gross_R']})
            for year in ('ALL',2023,2024):
                ee=[r for r in e if r['instrument'] in symbols and (year=='ALL' or r['signal_time'].year==year)];dd=[r for r in d if r['instrument'] in symbols and (year=='ALL' or r['bar_close_time'].year==year)]
                denom=sum(sum(year=='ALL' or at.year==year for at in frames[s].index[1:]) for s in symbols)
                executed=sum(r['entry_accepted'] for r in ee);filtered=sum(not r['rule_pass'] for r in ee);busy=sum(r['rule_pass'] and r['position_occupied'] for r in ee);skips=sum(r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN' for r in ee);pending=sum(r['decision_reason']=='UNRESOLVED_END_OF_DATA' for r in ee)
                tables['funnel_occupancy'].append(ident|{'scope':scope,'year':year,'signals':len(ee),'executed_entries':executed,'filtered':filtered,'occupied_allowed_signals':busy,'missing_adjacent_open':skips,'unresolved_pending':pending,'occupied_observed_bars':len(dd),'observed_bar_denominator':denom,'occupancy_share':len(dd)/denom if denom else None,'partition_PASS':len(ee)==executed+filtered+busy+skips+pending})
            year=[r for r in t if r['instrument'] in symbols and r['exit_time'].year==2024];nov=[r for r in year if r['exit_time'].month==11];ex=[r for r in year if r['exit_time'].month!=11];a=metrics(year,C.CALENDAR[12:]);b=metrics(ex,[m for m in C.CALENDAR[12:] if m!='2024-11']);nr=sum(r['gross_R'] for r in nov)
            tables['november'].append(ident|{'scope':scope,'november_CLOSED':len(nov),'november_PF':metrics(nov,['2024-11'])['gross_PF'],'november_R':nr,'november_share_2024_R':nr/a['gross_R'] if a['gross_R']>0 else None,'ex_november_PF':b['gross_PF'],'ex_november_R':b['gross_R'],'ex_november_DD':b['closed_R_drawdown'],'november_best_month':a['top1_months']=='2024-11'})
        total=peak=0.
        for r in sorted(t,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id'])):
            total+=r['gross_R'];peak=max(peak,total);tables['closed_equity'].append(ident|{k:r[k] for k in ('instrument','trade_id','exit_time','gross_R')}|{'entry_id':entry_id(r),'cumulative_R':total,'drawdown_R':peak-total})
        for year in ('ALL',2023,2024):
            ranked=sorted([r for r in t if r['gross_R']>0 and (year=='ALL' or r['exit_time'].year==year)],key=lambda r:(-r['gross_R'],r['exit_time'],r['instrument'],r['trade_id']))[:10]
            for rank,r in enumerate(ranked,1):tables['top_winners'].append(ident|{'year':year,'rank':rank,'in_top5':rank<=5,'entry_id':entry_id(r)}|{k:r[k] for k in ('instrument','direction','signal_time','entry_time','exit_time','entry_price','exit_price','gross_R','bars_held')})
    for ref in ('TRAIL_300','TRAIL_350'):
        originals=pools[ref]['trades']+pools[ref]['OPEN_POSITIONS'];original_map={entry_id(r):r for r in originals}
        rpaths=defaultdict(list)
        for r in pools[ref]['stop_decisions']:rpaths[(r['instrument'],r['trade_id'])].append(r)
        for v in C.VERSIONS:
            target={entry_id(r):r for r in pools[v]['trades']+pools[v]['OPEN_POSITIONS']};decisions={(r['instrument'],r['signal_time']):r for r in pools[v]['entry_opportunities']};paths=defaultdict(list)
            for r in pools[v]['stop_decisions']:paths[(r['instrument'],r['trade_id'])].append(r)
            for id,r in original_map.items():
                n=target.get(id);closed='gross_R' in r;nc=n is not None and 'gross_R' in n
                status='ORIGINAL_OPEN' if not closed else 'LOST_ENTRY' if n is None else 'TERMINAL_OPEN' if not nc else 'PRESERVED_OR_IMPROVED_R' if n['gross_R']>=r['gross_R']-1e-8 else 'TURNED_LOSS' if n['gross_R']<0 else 'PARTIALLY_REDUCED'
                reason=decisions[(r['instrument'],r['signal_time'])]['decision_reason'];equiv=bool(n and equivalent(r,n,rpaths[(r['instrument'],r['trade_id'])],paths[(n['instrument'],n['trade_id'])]))
                tables['lineage'].append({'reference':ref,'variant':v,'entry_id':id,'instrument':r['instrument'],'direction':r['direction'],'signal_time':r['signal_time'],'reference_trade_id':r['trade_id'],'candidate_trade_id':n['trade_id'] if n else None,'original_status':'CLOSED' if closed else 'OPEN','original_exit_year':r['exit_time'].year if closed else None,'original_R':r.get('gross_R'),'candidate_R':n.get('gross_R') if n else None,'status':status,'entry_id_matched':n is not None,'economic_trajectory_equivalent':equiv,'decision_reason':reason,'lost_due_occupancy':n is None and reason=='POSITION_OCCUPIED','candidate_status':'CLOSED' if nc else 'OPEN' if n else 'NOT_ENTERED','original_exit_time':r.get('exit_time'),'candidate_exit_time':n.get('exit_time') if n else None,'R_change':n['gross_R']-r['gross_R'] if closed and nc else None})
            for year in ('ALL',2023,2024):
                for threshold in (2.,5.):
                    selected=[r for r in tables['lineage'] if r['reference']==ref and r['variant']==v and r['original_status']=='CLOSED' and r['original_R']>=threshold and (year=='ALL' or r['original_exit_year']==year)]
                    tables['winner_retention'].append({'reference':ref,'variant':v,'year':year,'threshold_R':threshold,'original_winners':len(selected),'preserved_or_improved_R':sum(r['status']=='PRESERVED_OR_IMPROVED_R' for r in selected),'partially_reduced':sum(r['status']=='PARTIALLY_REDUCED' for r in selected),'turned_loss':sum(r['status']=='TURNED_LOSS' for r in selected),'lost_entry':sum(r['status']=='LOST_ENTRY' for r in selected),'lost_due_occupancy':sum(r['lost_due_occupancy'] for r in selected),'terminal_OPEN':sum(r['status']=='TERMINAL_OPEN' for r in selected),'entry_id_matched':sum(r['entry_id_matched'] for r in selected),'economic_trajectory_equivalent':sum(r['economic_trajectory_equivalent'] for r in selected),'still_at_threshold':sum(r['candidate_R'] is not None and r['candidate_R']>=threshold for r in selected),'original_R_sum':sum(r['original_R'] for r in selected),'candidate_matched_closed_R_sum':sum(r['candidate_R'] for r in selected if r['candidate_R'] is not None)})
            for id,n in target.items():
                if id not in original_map:tables['new_entries'].append({'reference':ref,'variant':v,'entry_id':id,'status':'CLOSED' if 'gross_R' in n else 'OPEN'}|{k:n.get(k) for k in ('instrument','direction','signal_time','entry_time','exit_time','gross_R')})
    get=lambda v,y:next(r for r in tables['summary'] if r['variant']==v and r['year']==y and r['scope']=='ALL_FOUR' and r['direction']=='ALL')
    for v,trail in C.VERSIONS.items():
        a=get(v,2023);b=get(v,2024);m=get(v,'ALL');n=next(r for r in tables['november'] if r['variant']==v and r['scope']=='ALL_FOUR');gate=a['gross_PF'] is not None and b['gross_PF'] is not None and min(a['gross_PF'],b['gross_PF'])>=1.7
        tables['comparison'].append({'variant':v,'trail_atr':trail,'PF2023':a['gross_PF'],'PF2024':b['gross_PF'],'PF_ALL':m['gross_PF'],'R2023':a['gross_R'],'R2024':b['gross_R'],'R_ALL':m['gross_R'],'CLOSED':m['closed'],'OPEN':m['period_end_OPEN'],'positive2023':a['positive_months'],'positive2024':b['positive_months'],'positive_ALL':m['positive_months'],'DD_ALL':m['closed_R_drawdown'],'worst_month':m['worst_month'],'worst_month_R':m['worst_month_R'],'max_negative_month_run':m['max_negative_month_run'],'november_share_2024_R':n['november_share_2024_R'],'ex_november_PF':n['ex_november_PF'],'ex_november_R':n['ex_november_R'],'ANNUAL_PF_MINIMUM_MET':gate,'annual_category':'ANNUAL_PF_GATE_MET' if gate else 'NOT MET','PREFERRED_PF_TARGET_MET':a['gross_PF'] is not None and b['gross_PF'] is not None and min(a['gross_PF'],b['gross_PF'])>2.})
    for left,right in zip(tables['comparison'],tables['comparison'][1:]):tables['neighbor_comparison'].append({'left':left['variant'],'right':right['variant']}|{'delta_'+k:right[k]-left[k] for k in ('PF2023','PF2024','PF_ALL','R_ALL','positive_ALL','DD_ALL','november_share_2024_R','worst_month_R')})
    for pr,folder in [(497,'t3_m15_combined_v1/results'),(504,'t3_m15_execution_sensitivity_v1/results/next_open')]:
        raw=C.reference('IntradayLab/'+folder+'/trades.csv')
        for version in ('BASELINE','OPTIMIZED'):
            rows=[r for r in raw if r['version']==version and r['rule']=='C1']
            from datetime import datetime
            rows=[r|{'exit_time':datetime.fromisoformat(r['exit_time']),'gross_R':float(r['gross_R'])} for r in rows]
            for year in ('ALL',2023,2024):tables['historical_references'].append({'PR':pr,'execution':'SIGNAL_CLOSE' if pr==497 else 'NEXT_OPEN','version':version,'year':year}|metrics([r for r in rows if year=='ALL' or r['exit_time'].year==year],[m for m in C.CALENDAR if year=='ALL' or m.startswith(str(year))]))
    assert all(r['partition_PASS'] for r in tables['funnel_occupancy'])
    return tables

def fmt(v):
    if v is None:return 'NA'
    if isinstance(v,float):return f'{v:.6f}'
    return str(v).replace('|',' / ')

def table(rows,fields):
    return '\n'.join(['| '+' | '.join(fields)+' |','| '+' | '.join('---' for _ in fields)+' |']+['| '+' | '.join(fmt(r.get(k)) for k in fields)+' |' for r in rows])

def render(t,path):
    full=[r for r in t['summary'] if r['scope']=='ALL_FOUR' and r['direction']=='ALL']
    status='ANNUAL_PF_TARGET_NOT_MET' if not any(r['ANNUAL_PF_MINIMUM_MET'] for r in t['comparison']) else 'ANNUAL_PF_GATE_MET: требует отдельной оценки месячной стабильности'
    lines=['# A6+S1 — Bounded Trailing Optimization v1','',f'**{status}**','',f'**{C.LABEL}. 2023–2024 DEVELOPMENT_EXPOSED.**','',
        'Полный самостоятельный causal replay ровно пяти заранее замороженных коэффициентов; только A6+S1 / NEXT_OPEN, LONG и SHORT, четыре вечных фьючерса. Новых параметров после результата нет. Ежегодный PF ≥1,70 проверяется отдельно; общий PF не компенсирует слабый год. Optimization не является независимым подтверждением.','',
        '## Все пять вариантов','',table(t['comparison'],list(t['comparison'][0])),'',
        '## Экономика по годам и за весь период','',table(full,['variant','year','closed','period_end_OPEN','gross_PF','gross_R','expectancy_R','win_fraction','wins','losses','mean_WIN_R','mean_LOSS_R','positive_months','negative_months','zero_months','closed_R_drawdown','max_losing_trade_run','worst_month','worst_month_R','max_negative_month_run']),'',
        '## Концентрация и исключение лучших месяцев: только sensitivity','',table([r for r in full if r['year']!='ALL'],['variant','year','top1_months','top1_months_R','top1_share_annual_R','ex_top1_PF','ex_top1_R','top3_months','top3_months_R','top3_share_annual_R','ex_top3_PF','ex_top3_R']),'',
        'Доли — от годовой суммы всех CLOSED Gross R; при R≤0 доля NA. Исключение месяцев — арифметика существующих CLOSED, без нового replay и без изменения первичной оценки.','',
        '## Ноябрь 2024','',table([r for r in t['november'] if r['scope']=='ALL_FOUR'],list(t['november'][0])),'',
        '## Все 24 месяца','']
    for v in C.VERSIONS:
        rows=[]
        for m in C.CALENDAR:
            get=lambda s,d='ALL':next(r for r in t['monthly'] if r['variant']==v and r['month']==m and r['scope']==s and r['direction']==d)
            r=get('ALL_FOUR');rows.append({k:r[k] for k in ('month','gross_PF','gross_R','closed','closed_R_drawdown')}|{side+'_CLOSED':get('ALL_FOUR',side)['closed'] for side in ('LONG','SHORT')}|{side+'_R':get('ALL_FOUR',side)['gross_R'] for side in ('LONG','SHORT')}|{s+'_R':get(s)['gross_R'] for s in C.SYMBOLS})
        lines+=['### '+v,'',table(rows,list(rows[0])),'']
    lines+=['## Соседние значения','',table(t['neighbor_comparison'],list(t['neighbor_comparison'][0])),'',
        'Сравнение использует только пять разрешённых точек. Граничный максимум не разрешает расширять диапазон. Нет составного score или подобранных весов.','',
        '## Сохранение ≥2R и ≥5R исходных победителей','',table([r for r in t['winner_retention'] if r['year']=='ALL'],list(t['winner_retention'][0])),'',
        'Стабильный entry ID = instrument|direction|signal_time. Последовательный trade_id меняется при иной занятости и показан отдельно. PRESERVED_OR_IMPROVED_R означает сохранённую или увеличенную прибыль, PARTIALLY_REDUCED — меньший неотрицательный R, TURNED_LOSS — отрицательный R. Потерянный вход и terminal OPEN выделены отдельно. Экономическая эквивалентность требует одинаковых entry/risk, exit/OPEN, S1, MFE/MAE и всей последовательности эффективных Stops/экстремумов с допуском 1e−8. Совпадение entry ID или R не доказывает эквивалентность траектории.','',
        'Подробная lineage всех входов относительно обоих контролей — lineage.csv; каждый новый вход и его итог — new_entries.csv; ежегодное удержание — winner_retention.csv. Параметр меняет Stop, момент выхода и последующую занятость совместно; отдельный P&L-вклад этих механизмов не приписывается.','',
        '## Top-5/Top-10 победителей','',table([r for r in t['top_winners'] if r['year']=='ALL'],list(t['top_winners'][0])),'',table(full,['variant','year','top5_winners_R','top5_share_positive_R','ex_top5_winners_PF','ex_top5_winners_R','top10_winners_R','top10_share_positive_R','ex_top10_winners_PF','ex_top10_winners_R']),'',
        '## Занятость и пропущенные сигналы','',table([r for r in t['funnel_occupancy'] if r['scope']=='ALL_FOUR'],list(t['funnel_occupancy'][0])),'',
        'Занятость = stop-checked observed bars / observed bars excluding first per instrument. Gaps не достраиваются; pending без смежного Open отменяется. Terminal OPEN не закрывается принудительно и не входит в CLOSED-экономику. На годовых границах позиции и индикаторы продолжаются.','',
        '## Инструменты и направления по годам','',table([r for r in t['summary'] if r['year']!='ALL' and ((r['scope']!='ALL_FOUR' and r['direction']=='ALL') or (r['scope']=='ALL_FOUR' and r['direction']!='ALL'))],['variant','scope','direction','year','closed','period_end_OPEN','gross_PF','gross_R','expectancy_R','win_fraction','mean_WIN_R','mean_LOSS_R','closed_R_drawdown']),'',
        'GLDRUBF доступен с 11 июля 2023, IMOEXF — с 14 ноября 2023. История сохраняет late starts; denominator — все 24 месяца. До старта NO_COVERAGE отличается от нулевого торгового месяца. Все instrument × LONG/SHORT месяцы с PF/R/CLOSED/DD опубликованы в monthly.csv и MONTHLY_DETAIL.md.','',
        '## Исторические референсы #497/#504','',table(t['historical_references'],['PR','execution','version','year','closed','gross_PF','gross_R','positive_months','closed_R_drawdown']),'',
        '## Воспроизводимость и ограничения','',
        'Два контроля проверены первичным и отдельным scalar replay до новых значений: все доступные trade/Stop/signal/occupancy/gap/terminal OPEN/period OPEN поля #504 и обязательные агрегаты. engine.py и scalar.py побайтно совпадают с #504. Исходные исследования и ROADMAP read-only. Source/spec/tests/report/audit/repeat заморожены в Git до первого результата. Подробности в FREEZE.json, control*/CONTROL_GATE.json, SOURCE_MANIFEST.json и audit/AUDIT_RESULT.json.','',
        'H1 публикуется только после четырёх смежных закрытых M15 дневного ordinal-блока; gaps/неполные блоки пропускаются без перепаковки. EMA/ATR/ADX/Donchian пересекают дни по исходной спецификации. Сигнал Close, вход только непосредственный Next Open; initial Stop = entry ±2 signal ATR. Stop-first; extrema выходной свечи не активируют S1. Пережитая свеча может активировать S1 на Close, Stop действует со следующей свечи. T1 отсутствует.','',
        'Год/месяц CLOSED — историческая Close-метка выходной свечи. CLOSED-R DD не является процентной просадкой капитала или MTM. Timestamp-first парсеры не читают OHLC 2025+; полный SHA — opaque bytes. Официальная календарная полнота сессий не заявлена. Расходы, funding, sizing/tick-grid и фактический брокерский fill отложены.','',
        'Аудит вычислительно независим: stdlib streaming features, dict state machine и scalar aggregates, без импорта primary engine/analysis/metrics; автор один, внешнее человеческое ревью PENDING. Два свежих повтора проверяют прямое равенство байтов и SHA256 всех generated CSV/JSON/MD. Отрицательные результаты сохранены.','',
        'При ANNUAL_PF_TARGET_NOT_MET следующий исследовательский шаг — возврат к архитектуре входа/режима по установленным недостаткам, после отдельного решения пользователя. Диапазон trailing не расширяется. Robustness/WF/TRUE OOS/LIVE не запускались. Один Draft PR, NO MERGE / NO AUTO-MERGE, STOP.','']
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n')
    detail=['# Все 24 месяца × инструменты × LONG/SHORT','',C.LABEL+'; 2023–2024 DEVELOPMENT_EXPOSED','']
    for v in C.VERSIONS:
        detail+=['## '+v,'',table([r for r in t['monthly'] if r['variant']==v],['month','scope','direction','coverage','closed','gross_PF','gross_R','expectancy_R','win_fraction','mean_WIN_R','mean_LOSS_R','closed_R_drawdown','max_losing_trade_run']),'']
    (path/'MONTHLY_DETAIL.md').write_text('\n'.join(detail)+'\n')
