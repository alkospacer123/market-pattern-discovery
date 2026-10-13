"""Fixed descriptive analysis. No filtering or parameter selection in replay."""
import numpy as np
import common as C

MODELS={'C1':'A6+S1','T1':'T1','COMBINED':'T1+S1'}

def metrics(rows,calendar):
    ordered=sorted(rows,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    x=np.asarray([r['gross_R'] for r in ordered],dtype=float)
    positive=float(x[x>0].sum());negative=float(-x[x<0].sum());total=float(x.sum())
    monthly={m:sum(r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m')==m) for m in calendar}
    equity=np.r_[0.,np.cumsum(x)];longest=streak=0
    for v in monthly.values():streak=streak+1 if v<0 else 0;longest=max(streak,longest)
    worst=min(monthly,key=monthly.get) if monthly else None
    losing=seq=0
    for v in x:seq=seq+1 if v<0 else 0;losing=max(losing,seq)
    result={'closed':len(x),'gross_PF':positive/negative if negative else None,'gross_R':total,
        'expectancy_R':float(x.mean()) if len(x) else None,'positive_R':positive,'negative_R':negative,
        'positive_months':sum(v>0 for v in monthly.values()),'negative_months':sum(v<0 for v in monthly.values()),
        'zero_months':sum(v==0 for v in monthly.values()),'months':len(calendar),
        'worst_month':worst,'worst_month_R':monthly.get(worst),'max_negative_month_run':longest,
        'closed_R_drawdown':float((np.maximum.accumulate(equity)-equity).max()),'max_losing_trade_run':losing}
    ranking=sorted(monthly,key=lambda m:(-monthly[m],m))
    for n in (1,3):
        top=ranking[:n];contrib=sum(monthly[m] for m in top)
        remaining=[r['gross_R'] for r in rows if r['exit_time'].strftime('%Y-%m') not in top]
        p=sum(r for r in remaining if r>0);l=-sum(r for r in remaining if r<0)
        result.update({f'top{n}_months':','.join(top),f'top{n}_months_R':contrib,
            f'top{n}_share_annual_R':contrib/total if total>0 else None,
            f'ex_top{n}_PF':p/l if l else None,f'ex_top{n}_R':sum(remaining)})
    for n in (5,10):
        wins=sorted((v for v in x if v>0),reverse=True)[:n];p=sum(wins)
        result.update({f'top{n}_winners_R':p,f'top{n}_share_positive_R':p/positive if positive else None,
            f'ex_top{n}_winners_PF':(positive-p)/negative if negative else None,f'ex_top{n}_winners_R':total-p})
    return result

def build(out,frames):
    tables={k:[] for k in ('summary','monthly','funnel_occupancy','lineage','winner_retention','new_entries','november','entry_price_sensitivity','closed_equity','negative_results')}
    for version in C.VERSIONS:
        for rule,model in MODELS.items():
            for mode in ('SIGNAL_CLOSE','NEXT_OPEN'):
                ident={'model':model,'rule':rule,'version':version,'mode':mode}
                subset=lambda name:[r for r in out[name] if r['version']==version and r['rule']==rule and r['mode']==mode]
                t=subset('trades');e=subset('entry_opportunities');d=subset('stop_decisions');op=subset('OPEN_POSITIONS');sn=subset('PERIOD_END_OPEN_POSITIONS')
                for scope in ('ALL_FOUR',*C.SYMBOLS):
                    symbols=C.SYMBOLS if scope=='ALL_FOUR' else (scope,)
                    first=min(frames[s].index[0] for s in symbols).strftime('%Y-%m')
                    for direction in ('ALL','LONG','SHORT'):
                        base=[r for r in t if r['instrument'] in symbols and (direction=='ALL' or r['direction']==direction)]
                        for year in ('ALL',2023,2024):
                            rows=[r for r in base if year=='ALL' or r['exit_time'].year==year]
                            months=[m for m in C.CALENDAR if year=='ALL' or m.startswith(str(year))]
                            o=op if year=='ALL' else [r for r in sn if r['month']==f'{year}-12']
                            opened=sum(r['instrument'] in symbols and (direction=='ALL' or r['direction']==direction) for r in o)
                            row=ident|{'scope':scope,'direction':direction,'year':year,'period_end_OPEN':opened}|metrics(rows,months)
                            tables['summary'].append(row)
                            if scope=='ALL_FOUR' and direction=='ALL':
                                if year!='ALL' and (row['gross_PF'] is None or row['gross_PF']<1.7):tables['negative_results'].append(ident|{'year':year,'finding':'ANNUAL_PF_MINIMUM_NOT_MET','value':row['gross_PF']})
                                if year=='ALL' and row['positive_months']<20:tables['negative_results'].append(ident|{'year':year,'finding':'BELOW_20_POSITIVE_MONTHS_ORIENTATION','value':row['positive_months']})
                        for month in C.CALENDAR:
                            rows=[r for r in base if r['exit_time'].strftime('%Y-%m')==month]
                            tables['monthly'].append(ident|{'scope':scope,'direction':direction,'month':month,
                                'coverage':'NO_COVERAGE' if month<first else 'AVAILABLE_PARTIAL_START' if month==first and scope in ('GLDRUBF','IMOEXF') else 'AVAILABLE'}|metrics(rows,[month]))
                            if scope=='ALL_FOUR' and direction=='ALL' and sum(r['gross_R'] for r in rows)<0:tables['negative_results'].append(ident|{'year':int(month[:4]),'month':month,'finding':'NEGATIVE_MONTH','value':sum(r['gross_R'] for r in rows)})
                    for year in ('ALL',2023,2024):
                        ee=[r for r in e if r['instrument'] in symbols and (year=='ALL' or r['signal_time'].year==year)]
                        dd=[r for r in d if r['instrument'] in symbols and (year=='ALL' or r['bar_close_time'].year==year)]
                        denom=sum(sum(year=='ALL' or at.year==year for at in frames[s].index[1:]) for s in symbols)
                        executed=sum(r['entry_accepted'] for r in ee)
                        tables['funnel_occupancy'].append(ident|{'scope':scope,'year':year,'signals':len(ee),'executed_entries':executed,
                            'filtered':sum(not r['rule_pass'] for r in ee),'occupied_allowed_signals':sum(r['rule_pass'] and r['position_occupied'] for r in ee),
                            'missing_adjacent_open':sum(r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN' for r in ee),
                            'unresolved_pending':sum(r['decision_reason']=='UNRESOLVED_END_OF_DATA' for r in ee),
                            'occupied_observed_bars':len(dd),'observed_bar_denominator':denom,'occupancy_share':len(dd)/denom if denom else None,
                            'partition_PASS':len(ee)==executed+sum(not r['rule_pass'] or r['rule_pass'] and r['position_occupied'] or r['decision_reason'] in ('SKIPPED_MISSING_ADJACENT_OPEN','UNRESOLVED_END_OF_DATA') for r in ee)})
                    yy=[r for r in t if r['instrument'] in symbols and r['exit_time'].year==2024]
                    nov=[r for r in yy if r['exit_time'].month==11];ex=[r for r in yy if r['exit_time'].month!=11]
                    full=metrics(yy,C.CALENDAR[12:]);remaining=metrics(ex,[m for m in C.CALENDAR[12:] if m!='2024-11'])
                    nr=sum(r['gross_R'] for r in nov)
                    tables['november'].append(ident|{'scope':scope,'november_closed':len(nov),'november_R':nr,'november_share_2024_R':nr/full['gross_R'] if full['gross_R']>0 else None,
                        'ex_november_PF':remaining['gross_PF'],'ex_november_R':remaining['gross_R'],'ex_november_DD':remaining['closed_R_drawdown'],
                        'november_best_month':full['top1_months']=='2024-11'})
                total=peak=0.
                for r in sorted(t,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id'])):
                    total+=r['gross_R'];peak=max(peak,total)
                    tables['closed_equity'].append(ident|{k:r[k] for k in ('instrument','trade_id','exit_time','gross_R')}|{'cumulative_R':total,'drawdown_R':peak-total})
            key=lambda r:(r['instrument'],r['direction'],r['signal_time'])
            filt=lambda name,mode:[r for r in out[name] if r['rule']==rule and r['version']==version and r['mode']==mode]
            ct=filt('trades','SIGNAL_CLOSE');co=filt('OPEN_POSITIONS','SIGNAL_CLOSE');nt=filt('trades','NEXT_OPEN');no=filt('OPEN_POSITIONS','NEXT_OPEN')
            target={key(r):r for r in nt};opened={key(r):r for r in no}
            decisions={(r['instrument'],r['signal_time']):r for r in filt('entry_opportunities','NEXT_OPEN')}
            refs={key(r):r for r in ct+co}
            ident={'model':model,'rule':rule,'version':version}
            for r in ct+co:
                k=key(r);n=target.get(k);o=opened.get(k);decision=decisions.get((r['instrument'],r['signal_time']))
                status='PRESERVED_R' if n and 'gross_R' in r and n['gross_R']>=r['gross_R']-1e-8 else 'CHANGED_R' if n else 'TERMINAL_OPEN' if o else 'LOST_ENTRY'
                tables['lineage'].append(ident|{'instrument':r['instrument'],'direction':r['direction'],'signal_time':r['signal_time'],
                    'original_status':'CLOSED' if 'gross_R' in r else 'OPEN','original_exit_year':r['exit_time'].year if 'exit_time' in r else None,
                    'original_R':r.get('gross_R'),'next_R':n.get('gross_R') if n else None,'status':status,
                    'decision_reason':decision['decision_reason'] if decision else 'NO_SIGNAL_DECISION',
                    'R_change':n['gross_R']-r['gross_R'] if n and 'gross_R' in r else None,
                    'next_entry_price':(n or o or {}).get('entry_price'),'original_entry_price':r['entry_price'],
                    'exit_time_changed':n['exit_time']!=r.get('exit_time') if n else None})
            lineage=[r for r in tables['lineage'] if r['rule']==rule and r['version']==version and r['original_status']=='CLOSED']
            for threshold in (2.,5.):
                for year in ('ALL',2023,2024):
                    rows=[r for r in lineage if r['original_R']>=threshold and (year=='ALL' or r['original_exit_year']==year)]
                    tables['winner_retention'].append(ident|{'threshold_R':threshold,'year':year,'original_winners':len(rows),
                        'preserved_or_improved_R':sum(r['status']=='PRESERVED_R' for r in rows),'changed_R':sum(r['status']=='CHANGED_R' for r in rows),
                        'lost_entry':sum(r['status']=='LOST_ENTRY' for r in rows),'terminal_OPEN':sum(r['status']=='TERMINAL_OPEN' for r in rows),
                        'still_at_threshold':sum(r['next_R'] is not None and r['next_R']>=threshold for r in rows),
                        'matched_below_threshold':sum(r['next_R'] is not None and r['next_R']<threshold for r in rows),
                        'matched_nonpositive':sum(r['next_R'] is not None and r['next_R']<=0 for r in rows)})
            for n in nt+no:
                if key(n) not in refs:tables['new_entries'].append(ident|{k:n.get(k) for k in ('instrument','direction','signal_time','entry_price','exit_time','gross_R')}|{'status':'CLOSED' if 'gross_R' in n else 'OPEN'})
            for year in ('ALL',2023,2024):
                rows=[r for r in nt+no if year=='ALL' or r['signal_time'].year==year]
                dev=[(1 if r['direction']=='LONG' else -1)*(r['entry_price']-r['signal_close'])/r['initial_risk'] for r in rows]
                tables['entry_price_sensitivity'].append(ident|{'year':year,'executed_entries':len(rows),'mean_signed_entry_deviation_R':float(np.mean(dev)) if dev else None,
                    'median_signed_entry_deviation_R':float(np.median(dev)) if dev else None,'mean_absolute_entry_deviation_R':float(np.mean(np.abs(dev))) if dev else None,
                    'worse_price_count':sum(v>0 for v in dev),'better_price_count':sum(v<0 for v in dev),'same_price_count':sum(v==0 for v in dev),
                    'not_a_PnL_attribution':True})
    assert all(r['partition_PASS'] for r in tables['funnel_occupancy'])
    return tables

def fmt(v):
    if v is None:return 'NA'
    if isinstance(v,bool):return str(v)
    if isinstance(v,float):return f'{v:.4f}'
    return str(v)

def table(rows,columns):
    return '\n'.join(['| '+' | '.join(label for key,label in columns)+' |','| '+' | '.join('---' for c in columns)+' |']+
        ['| '+' | '.join(fmt(r.get(key)) for key,label in columns)+' |' for r in rows])

def render(tables,path):
    full=[r for r in tables['summary'] if r['scope']=='ALL_FOUR' and r['direction']=='ALL']
    comparison=[]
    for v in C.VERSIONS:
        for rule,model in MODELS.items():
            get=lambda y,m:next(r for r in full if r['rule']==rule and r['version']==v and r['year']==y and r['mode']==m)
            c=get('ALL','SIGNAL_CLOSE');n=get('ALL','NEXT_OPEN');a=get(2023,'NEXT_OPEN');b=get(2024,'NEXT_OPEN')
            comparison.append({'model':model,'version':v,'Close_PF':c['gross_PF'],'Next_PF':n['gross_PF'],'Close_R':c['gross_R'],'Next_R':n['gross_R'],
                'delta_R':n['gross_R']-c['gross_R'],'PF2023':a['gross_PF'],'PF2024':b['gross_PF'],'positive_Close':c['positive_months'],'positive_Next':n['positive_months'],
                'closed_Close':c['closed'],'closed_Next':n['closed'],'DD_Close':c['closed_R_drawdown'],'DD_Next':n['closed_R_drawdown'],
                'annual_minimum':'MET' if a['gross_PF'] is not None and b['gross_PF'] is not None and min(a['gross_PF'],b['gross_PF'])>=1.7 else 'NOT MET'})
    C.write_csv(path/'comparison.csv',comparison);C.write_json(path/'TABLES.json',tables)
    lines=['# T3/M15 Execution Sensitivity v1','',
        '**GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY. 2023–2024 DEVELOPMENT_EXPOSED.**','',
        'Ровно шесть фиксированных конфигураций, два исполнения. OPTIMIZED — унаследованное имя trailing 3.5 ATR; новой Optimization нет. Полный доступный период четырёх инструментов.','',
        '## Сравнение всех конфигураций','',table(comparison,[(k,k) for k in comparison[0]]),'',
        'Ежегодный минимум roadmap: PF ≥1.70 отдельно в каждом году; предпочтительно >2.0 ежегодно. Месячная регулярность — равноправный приоритет, ориентир 20–24/24. Полный двухлетний PF не компенсирует провал года.','',
        '## Годы и полный период','',table(full,[(k,k) for k in ('model','version','mode','year','closed','period_end_OPEN','gross_PF','gross_R','expectancy_R','positive_months','negative_months','zero_months','closed_R_drawdown','worst_month','worst_month_R','max_negative_month_run','max_losing_trade_run')]),'',
        '## Концентрация месяцев и исключения — только sensitivity','',
        table([r for r in full if r['year']!='ALL'],[(k,k) for k in ('model','version','mode','year','top1_months','top1_months_R','top1_share_annual_R','ex_top1_PF','ex_top1_R','top3_months','top3_months_R','top3_share_annual_R','ex_top3_PF','ex_top3_R')]),'',
        'Доли вычислены от годового net sum Gross R (суммы закрытых gross_R), а не от суммы положительных R. При неположительном годовом R доля NA. Исключение месяцев не перезапускает торговый путь.','',
        '## Все 24 месяца','']
    for v in C.VERSIONS:
        for rule,model in MODELS.items():
            rows=[]
            for m in C.CALENDAR:
                get=lambda mode:next(r for r in tables['monthly'] if r['version']==v and r['rule']==rule and r['mode']==mode and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['month']==m)
                c=get('SIGNAL_CLOSE');n=get('NEXT_OPEN');rows.append({'month':m,'Close_R':c['gross_R'],'Next_R':n['gross_R'],'delta_R':n['gross_R']-c['gross_R'],
                    'Close_PF':c['gross_PF'],'Next_PF':n['gross_PF'],'Close_CLOSED':c['closed'],'Next_CLOSED':n['closed'],'Next_expectancy_R':n['expectancy_R']})
            lines+=['### '+model+' '+v,'',table(rows,[(k,k) for k in rows[0]]),'']
    lines+=['## Занятость, пропуски и новая цена','',
        table([r for r in tables['funnel_occupancy'] if r['scope']=='ALL_FOUR'],[(k,k) for k in ('model','version','mode','year','signals','executed_entries','filtered','occupied_allowed_signals','missing_adjacent_open','unresolved_pending','occupied_observed_bars','observed_bar_denominator','occupancy_share')]),'',
        table(tables['entry_price_sensitivity'],[(k,k) for k in ('model','version','year','executed_entries','mean_signed_entry_deviation_R','mean_absolute_entry_deviation_R','worse_price_count','better_price_count','same_price_count')]),'',
        'Положительное signed entry deviation означает худшую цену для направления сделки; это расстояние цены в новом первоначальном R, **не вклад в изменение P&L**. Общая ΔR отражает совместное действие цены, пропусков и изменившейся занятости/Stops/повторных входов. Строго разделить эти эффекты без дополнительных counterfactual replay нельзя; выдуманных численных вкладов нет.','',
        'Занятость — число реально наблюдаемых свечей, на Open которых была позиция (включая новый вход), делённое на наблюдаемые свечи кроме первой по инструменту. Календарные gaps не заполняются. Фильтр, занятость, skip, unresolved и исполнение образуют проверенную полную partition сигналов.','',
        '## Сохранение исходных крупных победителей','',table(tables['winner_retention'],[(k,k) for k in tables['winner_retention'][0]]),'',
        'Сопоставление по instrument/direction/исходному signal_time в той же архитектуре и версии. PRESERVED_R = новый CLOSED R ≥ исходный R−1e−8; CHANGED_R — меньший R; LOST_ENTRY — исходный сигнал не исполнен; terminal OPEN не превращается в убыток. Это диагностическая связь, не изолированный причинный контрфакт. Полный перечень — lineage.csv, дополнительные сделки — new_entries.csv.','',
        '## Ноябрь 2024','',table([r for r in tables['november'] if r['scope']=='ALL_FOUR'],[(k,k) for k in tables['november'][0]]),'',
        '## Все инструменты и LONG/SHORT','',
        'GLDRUBF начинается 2023-07-11 10:00 МСК, IMOEXF — 2023-11-14 10:00 МСК. История не достраивается. NO_COVERAGE до старта хранится отдельно от нулевых торговых результатов; denominator всё равно 24 месяца. Полные ежегодные и месячные instrument × direction таблицы: summary.csv, monthly.csv.','',
        table([r for r in tables['summary'] if r['year']!='ALL' and r['mode']=='NEXT_OPEN' and r['scope']!='ALL_FOUR' and r['direction']=='ALL'],[(k,k) for k in ('model','version','scope','year','closed','gross_PF','gross_R','expectancy_R','positive_months','closed_R_drawdown')]),'',
        table([r for r in tables['summary'] if r['year']!='ALL' and r['scope']=='ALL_FOUR' and r['direction']!='ALL'],[(k,k) for k in ('model','version','mode','direction','year','closed','gross_PF','gross_R','expectancy_R')]),'',
        '## Методология и пределы','',
        'Все признаки доступны только после signal Close. H1 — исходные дневные ordinal-блоки четырёх смежных M15; неполные/gapped блоки исключаются без перепаковки. EMA/ATR/ADX и Donchian пересекают дни. T1 [10:00,18:00) проверяет сигнал. A6 требует строгого роста H1 ATR/ATRMean к предыдущему завершённому H1.','',
        'Next Open исполняет только непосредственно следующую смежную M15. ATR и направление берутся с завершённого сигнала; начальный Stop = entry − side×2×signal ATR; первоначальный R неизменен. Stop-first с adverse Open gap; экстремумы Stop-свечи не улучшают вход/Stop и не активируют S1. Пережитая свеча исполнения может активировать S1 на Close, Stop изменится не ранее следующей наблюдаемой свечи.','',
        'Нет принудительного закрытия на сессии/годе. Год и месяц результата — историческая Close-метка свечи выхода, точный intrabar момент неизвестен. OPEN не ликвидирован и исключён из CLOSED метрик; unresolved pending отдельно в entry_opportunities. Граница 2025 соблюдена timestamp-first парсерами; full source SHA считается как непрозрачные байты.','',
        'CLOSED-R drawdown — drawdown накопленной суммы R в порядке exit_time/instrument/trade_id с начальным 0; это не реальная портфельная equity/MTM или просадка капитала. Next Open тоже исследовательское допущение: не гарантирует fill, очередь заявки или задержку брокера. Издержки, sizing и tick/grid исполнение отложены.','',
        'Полный перечень отрицательных годовых и месячных результатов: negative_results.csv. Ни один отрицательный результат не удалён. Никаких численных Optimization, Robustness, Walk Forward, TRUE OOS, LIVE или брокерских endpoint. Независимость аудита вычислительная (отдельные scalar признаки/state machine/арифметика), автор один; внешняя независимая проверка PENDING.','']
    (path/'REPORT.md').write_text('\n'.join(lines)+'\n')
