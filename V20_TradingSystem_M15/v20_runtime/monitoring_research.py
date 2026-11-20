"""Reproducible descriptive tables and archive cards; no parameter search."""
from __future__ import annotations
from collections import Counter,defaultdict
from datetime import datetime,timedelta
import argparse
import json
from pathlib import Path
import subprocess
import sys
import unittest
from statistics import mean,median

from .market_monitoring import (load_data,monitoring_card,assess,P,DIAG,INSUF,NORMAL)
from .calendar_review import statistics,shift_month,completion_period,quarter
from .calendar_tail_diagnostics import tail_stats
from .regime_monthly_comparison import ROOT,FOLDER,dt,digest,read_csv
from .regime_research import dump_csv
from .suitability_research import MODES


def epoch(t):
    return '2012-2017' if t.year<2018 else '2018' if t.year==2018 else '2019-2022' if t.year<=2022 else '2023-2026'


def describe(rows):
    q=statistics(rows);wins=sorted((r['net'] for r in rows if r['net']>0),reverse=True)
    losses=[r['net'] for r in rows if r['net']<0];s=sum(wins)
    monthly=defaultdict(float)
    for r in rows:monthly[completion_period(r['available']).strftime('%Y-%m')]+=r['net']
    return dict(**q,win_rate=len(wins)/len(rows) if rows else None,
        mean_win_R=mean(wins) if wins else None,mean_loss_R=mean(losses) if losses else None,
        initial_stop_share=mean(r['stop'] for r in rows) if rows else None,
        time_exit_share=mean(r['reason']==3 for r in rows) if rows else None,
        net_ge4_n=sum(r['net']>=4 for r in rows),net_ge5_n=sum(r['net']>=5 for r in rows),
        net_ge4_share_positive_R=sum(v for v in wins if v>=4)/s if s else None,
        net_ge5_share_positive_R=sum(v for v in wins if v>=5)/s if s else None,
        top1_winner_share=sum(wins[:1])/s if s else None,top3_winner_share=sum(wins[:3])/s if s else None,
        top10_winner_share=sum(wins[:10])/s if s else None,
        positive_months=sum(v>0 for v in monthly.values()),negative_months=sum(v<0 for v in monthly.values()),
        gap_stop_n=sum(r["reason"]==2 for r in rows),gap_stop_net_R=sum(r["net"] for r in rows if r["reason"]==2),
        worst_net_R=min((r["net"] for r in rows),default=None))


def partial_replay(censored,start,end):
    return any(r.get('unknown_after',datetime.max)<end and r.get('scope_end',datetime.min)>start for r in censored)


def flat_snapshot(card):
    return dict(status=card['status'],economic_status=card['economic_status'],last_closed_result=card['last_closed_result'],
        **{f'{label}_{k}':w[k] for label,w in (('w3',card['w3']),('w6',card['w6']))
            for k in ('n','net_R','PF_C1','mean_R','sufficient')})


def forward(rows,raw,censored,t,end):
    stop=shift_month(t,3)
    q=[r for r in rows if t<r['available']<=stop]
    bad=[r for r in censored if t<=r['entry']<stop or t<r['available']<=stop]
    complete=end>=stop
    label=('FALSE_ALERT' if sum(r['net'] for r in q)>0 else 'CONTINUED_WEAK' if sum(r['net'] for r in q)<0 else 'UNRESOLVED') if complete and len(q)>=10 and not bad else 'UNRESOLVED'
    new=[r for r in rows if t<=r['entry']<stop]
    paths=[r for r in raw if t<=r['decision']<stop]
    return dict(evaluation_only=True,from_at=t,to_at=stop,complete=complete,censored=len(bad),label=label,
        completed=describe(q),structure=tail_stats(paths,new),
        hypothetical_exclusion_basis='BASELINE_NEW_ENTRY_COHORT; NOT_EXECUTABLE_FILTER_REPLAY',
        lost_positive_R=sum(max(0,r['net']) for r in new),avoided_negative_R=-sum(min(0,r['net']) for r in new),
        lost_winners=sum(r['net']>0 for r in new),avoided_losers=sum(r['net']<0 for r in new))


def early_controls(groups,bounds,raw,censored):
    """Only added years, unchanged OLD rules; no quotes or late replay."""
    from .regime_research import causal_states
    from .confirmed_market_regime import confirmed_card
    from .suitability_research import Evidence
    from .calendar_review import completed_window,rule
    from .regime_monthly_comparison import Track,GOOD,BAD,UNKNOWN
    evidence=Evidence(groups,bounds);controls=[];unique={}
    for r in raw:
        if r['signal'].year>=2018 or r['outcome'] is None:continue
        p=dict(r['outcome'],instrument=r['instrument'],contract=r.get('contract',''))
        for field in ('signal','available','entry_time'):p[field]=dt(p[field])
        p['stop_aware']=-1. if p['stop_touch']=='True' else float(p['raw_R'])
        unique[r['instrument'],r['signal']]=p
    for instrument in ('Si','MIX'):
        events=[r for (s,t),r in unique.items() if s==instrument]
        clocks=[];t=datetime(2012,1,1)
        while t<datetime(2018,1,1):clocks.append(t);t=shift_month(t,1)
        timeline,_=causal_states(events,[],clocks)
        track=Track([(r['as_of'],{'UNKNOWN':UNKNOWN,'NORMAL':GOOD,'WARNING':BAD}[r['RAW20_CONFIRM5']]) for r in timeline],*bounds[instrument])
        for strategy in MODES:
            rows=groups[strategy,instrument];paths=[r for r in raw if r['strategy']==strategy and r['instrument']==instrument]
            bad=[r for r in censored if r['strategy']==strategy and r['instrument']==instrument]
            states={m:('INSUFFICIENT',False) for m in ('QUARTER_3M','HALF_YEAR_6M','QUARTER_3M_6M')}
            for t in clocks:
                edge=evidence.at(strategy,instrument,t)
                two=confirmed_card(events,instrument,as_of=t)['historical_observation']
                status=dict(RAW20_CONFIRM5=track.at(t),
                    TWO_BLOCK_20=BAD if two=='CONFIRMED_OBSERVED_WEAK' else GOOD if two=='CONFIRMED_OBSERVED_FAVORABLE' else UNKNOWN,
                    EDGE_20_60=BAD if edge['state']=='NO_EDGE_CONFIRMED' else GOOD if edge['state']=='EDGE_CONFIRMED' else UNKNOWN)
                w3,w6=[completed_window(rows,t,m,datetime(2012,1,1)) for m in (3,6)]
                for method in states:
                    if t.month in ((1,7) if method=='HALF_YEAR_6M' else (1,4,7,10)):
                        states[method]=rule(method,w3,w6,states[method][1])
                    state,excluded=states[method]
                    status[method]=BAD if excluded else UNKNOWN if state=='INSUFFICIENT' else GOOD
                for method,state in status.items():
                    f=forward(rows,paths,bad,t,bounds[instrument][1]) if t.month in (1,4,7,10) and state==BAD else None
                    controls.append(dict(method=method,strategy=strategy,instrument=instrument,as_of=t,state=state,
                        quarterly_warning=bool(f),next_label=f['label'] if f else None,
                        next_net_R=f['completed']['net_R'] if f else None,
                        lost_positive_R=f['lost_positive_R'] if f else None,avoided_negative_R=f['avoided_negative_R'] if f else None))
    dump_csv(FOLDER/(P+'EARLY_FIXED_CONTROLS.csv'),controls)
    return [dict(method=m,unit='PER_ROBOT_INSTRUMENT_QUARTER_REVIEWS; NOT_UNIQUE_RAW_ALERT_EPISODES',
        warning_reviews=len(v),false=sum(r['next_label']=='FALSE_ALERT' for r in v),
        continued=sum(r['next_label']=='CONTINUED_WEAK' for r in v),unresolved=sum(r['next_label']=='UNRESOLVED' for r in v),
        monthly_coverage=sum(r['state']!='INSUFFICIENT' for r in controls if r['method']==m)/sum(r['method']==m for r in controls))
        for m in sorted({r['method'] for r in controls}) for v in [[r for r in controls if r['method']==m and r['quarterly_warning']]]]


def build():
    groups,bounds,raw,censored,hashes=load_data(verify=False)
    rawgroups=defaultdict(list)
    for r in raw:rawgroups[r['strategy'],r['instrument']].append(r)
    monthly=[];annual=[];quarterly=[];large=[];alerts=[];episodes=[]
    alltr=[r for v in groups.values() for r in v]
    for strategy in MODES:
        instruments=sorted(s for m,s in groups if m==strategy)
        for instrument in [*instruments,'ALL']:
            rows=[r for r in alltr if r['strategy']==strategy and (instrument=='ALL' or r['instrument']==instrument)]
            start,end=bounds[instrument] if instrument!='ALL' else (datetime(2012,1,1),max(b for a,b in bounds.values()))
            paths=rawgroups[strategy,instrument] if instrument!='ALL' else [r for r in raw if r['strategy']==strategy]
            bad=[r for r in censored if r['strategy']==strategy and (instrument=='ALL' or r['instrument']==instrument)]
            # Include all calendar months in an instrument's observed era, not
            # fabricated pre-launch observations on a future N4 instrument.
            t=datetime(start.year,1,1);qs=[]
            while t<=end:
                stop=shift_month(t,1)
                q=[r for r in rows if t<r['available']<=stop]
                rec=dict(strategy=strategy,instrument=instrument,period=t.strftime('%Y-%m'),start=t,end=stop,
                    partial=t<start or stop>end,partial_replay=partial_replay(bad,t,stop),**describe(q))
                if instrument!='ALL':
                    a=assess(rows,paths,start,end,t,bad);b=assess(rows,paths,start,end,min(stop,end),bad)
                    rec.update({f'start_{k}':v for k,v in flat_snapshot(a).items()})
                    rec.update({f'end_{k}':v for k,v in flat_snapshot(b).items()})
                    rec['known_at_start_only']=True
                    if t.month in (1,4,7,10) and start<=t<=end and a['economic_status']==DIAG:
                        f=forward(rows,paths,bad,t,end)
                        alerts.append(dict(strategy=strategy,instrument=instrument,epoch=epoch(t),decision_at=t,
                            **flat_snapshot(a),evaluation=json.dumps(f,default=str,sort_keys=True),
                            label=f['label'],next_quarter_n=f['completed']['n'],next_quarter_net=f['completed']['net_R'],
                            lost_positive_R=f['lost_positive_R'],avoided_negative_R=f['avoided_negative_R'],
                            lost_winners=f['lost_winners'],avoided_losers=f['avoided_losers']))
                else:rec['start_status']=rec['end_status']='SEE_SEPARATE_INSTRUMENTS'
                monthly.append(rec)
                if t.month in (1,4,7,10):
                    qe=shift_month(t,3);tr=[r for r in rows if t<r['available']<=qe]
                    qr=dict(strategy=strategy,instrument=instrument,period=f'{t.year}Q{(t.month-1)//3+1}',start=t,end=qe,
                        partial=t<start or qe>end,partial_replay=partial_replay(bad,t,qe),**describe(tr));quarterly.append(qr);qs.append(qr)
                    # Tails are SIGNAL/ENTRY cohorts, not completed-PnL quarters.
                    rawq=[r for r in paths if t<=r['decision']<qe]
                    tradq=[r for r in rows if t<=r['entry']<qe]
                    large.append(dict(strategy=strategy,instrument=instrument,period=qr['period'],start=t,end=qe,
                        partial=qr['partial'],raw_axis='SIGNAL_DECISION',trade_axis='ENTRY',**tail_stats(rawq,tradq)))
                t=stop
            for y in range(start.year,end.year+1):
                a,b=datetime(y,1,1),datetime(y+1,1,1)
                annual.append(dict(strategy=strategy,instrument=instrument,year=y,partial=a<start or b>end,
                    partial_replay=partial_replay(bad,a,b),**describe([r for r in rows if a<r['available']<=b])))
            if instrument!='ALL':
                j=0
                while j<len(qs):
                    if qs[j]['partial'] or qs[j]['n']<10 or qs[j]['net_R']>=0:j+=1;continue
                    k=j+1
                    while k<len(qs) and not qs[k]['partial'] and qs[k]['n']>=10 and qs[k]['net_R']<0:k+=1
                    first,last=qs[j],qs[k-1];f=forward(rows,paths,bad,last['end'],end)
                    episodes.append(dict(strategy=strategy,instrument=instrument,epoch=epoch(first['start']),
                        onset=first['start'],first_known=first['end'],sustained_known=qs[j+1]['end'] if k-j>=2 else None,
                        last_weak_end=last['end'],negative_quarters=k-j,net_R=sum(r['net_R'] for r in qs[j:k]),
                        calendar_days=(last['end']-first['start']).days,
                        first_mean_win=first['mean_win_R'],last_mean_win=last['mean_win_R'],
                        first_stop_share=first['initial_stop_share'],last_stop_share=last['initial_stop_share'],
                        next_quarter_net=f['completed']['net_R'],next_quarter_n=f['completed']['n'],
                        next_complete=f['complete'],next_label=f['label'],
                        diagnostic_json=json.dumps(qs[j:k],default=str,sort_keys=True)))
                    j=k
    for r in episodes:
        points=[x for x in monthly if x['strategy']==r['strategy'] and x['instrument']==r['instrument']]
        warnings=[x['start'] for x in points if r['onset']<=x['start']<r['last_weak_end'] and x['start_economic_status']==DIAG]
        detected=min(warnings,default=None)
        normal=min((x['start'] for x in points if x['start']>=r['last_weak_end'] and x['start_economic_status']==NORMAL),default=None)
        r.update(first_monitor_diagnostic_during_weak=detected,diagnostic_delay_days=(detected-r['onset']).days if detected else None,
            missed_during_weak=detected is None,first_later_observed_normal=normal,
            warning='Normal date is observed statistics, not proven future restoration.')
    for name,data in [('MONTHLY',monthly),('ANNUAL',annual),('QUARTERLY',quarterly),('LARGE_MOVES',large),('REGIME_EPISODES',episodes),('FALSE_ALERTS',alerts)]:
        dump_csv(FOLDER/(P+name+'.csv'),data)
    snapshots=[]
    dates=['2013-07-01','2015-07-01','2017-07-01','2018-07-01','2019-07-01','2020-07-01',
        '2021-07-01','2022-07-01','2024-07-01','2025-07-01',str(max(b for a,b in bounds.values()))]
    for s in dates:
        t=dt(s);card=monitoring_card(groups,bounds,raw,censored,t)
        evaluations=[]
        for r in card['rows']:
            key=r['strategy'],r['instrument']
            evaluation_start=t if t==quarter(t) else shift_month(quarter(t),3)
            evaluations.append(dict(strategy=key[0],instrument=key[1],
                future=forward(groups[key],rawgroups[key],[x for x in censored if (x['strategy'],x['instrument'])==key],evaluation_start,bounds[key[1]][1])))
        snapshots.append(dict(card=card,retrospective_evaluation_only=evaluations))
    (FOLDER/(P+'CARD_SNAPSHOTS.json')).write_text(json.dumps(snapshots,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
    epochstats=[]
    for label,years in [('2012-2017',range(2012,2018)),('2018',[2018]),('2019-2022',range(2019,2023)),('2023-2026',range(2023,2027))]:
        for m in MODES:
            q=[r for r in alltr if r['strategy']==m and completion_period(r['available']).year in years]
            pr=[r for r in raw if r['strategy']==m and r['decision'].year in years]
            epochstats.append(dict(epoch=label,strategy=m,**describe(q),tails=tail_stats(pr,[r for r in q if r['entry'].year in years])))
    controls=early_controls(groups,bounds,raw,censored)
    summary=dict(calculation='PENDING_TESTS',monitoring='DIAGNOSTIC_ONLY',reliable_exclusion='FAIL_NOT_ESTABLISHED',early_fixed_controls=controls,
        input_head='089e6b5d12b773e09029f0db94df8857014015fa',source_hashes=hashes,epochs=epochstats,
        alerts=[dict(epoch=e,n=len(v),false=sum(x['label']=='FALSE_ALERT' for x in v),continued=sum(x['label']=='CONTINUED_WEAK' for x in v),
            unresolved=sum(x['label']=='UNRESOLVED' for x in v),lost_positive_R=sum(x['lost_positive_R'] for x in v),
            avoided_negative_R=sum(x['avoided_negative_R'] for x in v),lost_winners=sum(x['lost_winners'] for x in v),avoided_losers=sum(x['avoided_losers'] for x in v))
            for e in ('2012-2017','2018','2019-2022','2023-2026') for v in [[x for x in alerts if x['epoch']==e]]],
        notes=['New-year MIX fixed tick25 uncertified; not a real exchange-cost claim.',
            'Independent accounts, no pooled cash DD. Source composition differs across eras.',
            'False-alert prices are disjoint next-quarter entry cohorts per robot/instrument, not conditional portfolio replay.',
            'Old RAW5/TWO_BLOCK/EDGE controls unchanged; no retuning or repeated late replay.'],
        rows=dict(monthly=len(monthly),annual=len(annual),quarterly=len(quarterly),large_moves=len(large),episodes=len(episodes),alerts=len(alerts)))
    long=[r for r in episodes if r['negative_quarters']>=2]
    delays=[r['diagnostic_delay_days'] for r in long if r['diagnostic_delay_days'] is not None]
    summary['long_weak_episodes']=dict(n=len(long),missed_during_weak=sum(r['missed_during_weak'] for r in long),
        detected=len(delays),median_delay_days=median(delays) if delays else None,
        min_delay_days=min(delays,default=None),max_delay_days=max(delays,default=None),
        note='Retrospective sufficient-quarter labels; not independent OOS; includes conditional early source.')
    summary['full_early_replay']='FAIL_PARTIAL: Shallow Si-12.14 missing third-session exit blocks Si from2014. Published2018 reference restarts independently.'
    (FOLDER/(P+'RESULTS.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
    write_report(summary,annual,monthly,episodes,alerts,snapshots,groups)
    cardnames=['V20_2012_2022_REPLAY_TRADES.csv',P+'NEW_RAW_PATHS.csv',P+'CENSORED_TRADES.csv','V20_2012_2022_SOURCE_AUDIT.json']
    manifest=dict(card_inputs={str((FOLDER/n).relative_to(ROOT)):digest(FOLDER/n) for n in cardnames},
        artifacts={p.name:digest(p) for p in FOLDER.glob(P+'*') if p.suffix in ('.csv','.json') and p.name!=P+'MANIFEST.json'},
        code={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'v20_runtime').glob('*monitor*.py')},
        protocol_sha256=digest(FOLDER/'V20_2012_MONITORING_PROTOCOL_RU.md'))
    (FOLDER/(P+'MANIFEST.json')).write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(rows=summary['rows'],alerts=summary['alerts']),indent=2))


def write_report(summary,annual,monthly,episodes,alerts,snapshots,groups):
    audit=json.loads((FOLDER/'V20_2012_2022_SOURCE_AUDIT.json').read_text())
    def n(x):return f'{x:.3f}' if isinstance(x,(float,int)) else 'Н/Д' if x is None else str(x)
    names=dict(zip(MODES,('Shallow','OBV','Inside')))
    lines=['# V20-04.2 — история 2012–2026 и READONLY-мониторинг',
        '', '**Итог: диагностическая карточка работает; полный early replay — FAIL/PARTIAL из-за неизвестного выхода. Надёжность исключения — FAIL, не доказана.**',
        'Исходный main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`, PR head до работы `089e6b5d12b773e09029f0db94df8857014015fa`. PR #567 остаётся Draft.',
        '', '## Источники и сопоставимость', '',
        f"ZIP SHA256 `{audit['zip_sha256']}`: {audit['contracts']} квартальных файлов, {audit['bars']} M15-строк (Si 150813, MIX 149185), в том числе 1013 свечей прогрева 2011. После карантина двух OHLC: {audit['validated_bars']} строк.",
        f"5758 наблюдаемых контрактных сессий, 249 не удовлетворяют прежнему критерию полноты дневной сессии; {audit['unknown_holes']} неизвестных внутрисессионных разрывов плюс два принудительных reset после карантина. Это наблюдаемая полнота, не заверенный календарь биржи.",
        'Все 40 общих файлов 2018–2022 побайтово совпадают с прежним ZIP; OHLCV, timestamps, серии и пропуски тождественны. 48 новых файлов расширяют историю. Название ZIP 2012–2018 не описывает фактическое содержимое: оно до декабря 2022.',
        'Исходники не опубликованы. Полная инвентаризация, SHA каждого файла, размеры, временные границы и сетки цен — V20_2012_2022_SOURCE_AUDIT.json. Временная зона MSK и OPEN-разметка условны по прежней методологии; подтверждения поставщика нет.',
        'LOCKED_V1 не переписан: те же функции сигналов, отдельных сегментов/прогрева, причинного roll, NEXT_OPEN, ATR/stop, third-session exit, дневных лимитов и C1. AST адаптирует только календарный допуск replay 2018→2012 и проверки состава входного архива. Frozen-файлы не меняются.',
        'Две недопустимые OHLC Si-12.12 (03.10/03.12.2012 19:00) карантинированы без исправления цен; следующий наблюдаемый бар начинает новый сегмент. Открытый исход, пересекающий разрыв, не становится известным.',
        '**FAIL сертификации раннего MIX:** 88906 OHLC-значений в 11 контрактах 2012–2014 вне frozen tick=25. Tick/округление стопа не менялись. Показанные ранние C1 — условный результат прежнего адаптера, точные исторические биржевые расходы MIX NOT AVAILABLE.',
        '**Существенное ограничение раннего Si:** источник печатает экстремальные OPEN в 14:00/18:45. Сделка Shallow Si-6.12 03.05.2012 12:30→14:00: вход29669, риск40, выход27000, net−66.775R. Предыдущий Close29694, следующий OPEN29695. Значения не исправлены и не выброшены по величине PnL; исполнимость таких цен не подтверждена. Нельзя объявлять огромный убыток 2012 чистым циклом рыночного преимущества.',
        'Старые результаты: 1004 допустимые сделки (включая CNY только с 2022), 12 цензурированных закрытий. Поздние неизменённые 1589 воспроизведённых сделок N4, одна открытая Inside/USDRUBF без синтетического выхода. Оригинальный поздний ledger ранее отсутствовал: его полная построчная сверка остаётся SKIP, а не новый PASS.',
        '**FAIL/PARTIAL полноты early replay:** есть ещё одна незавершённая Shallow/Si позиция от12.12.2014 10:15 на Si-12.14. Файл заканчивается15.12, третья наблюдаемая сессия16.12.2014 10:00 не имеет старого контракта. Frozen one-position rule блокирует Si до конца прогона. Цена выхода не придумана; стратегия/roll не переписаны. Поэтому Shallow2015–2017 отражает доступные закрытия MIX, а не полный результат Si+MIX. В CSV это partial_replay=True, карточка Si показывает неизвестный модельный выход. Публикуемый reference2018 начинается отдельно с исходным состоянием; это не непрерывный капитал с2012.',
        'Новые 2012–2017: 731 допустимое закрытие, 18 цензурированных, одна неизвестная открытая позиция; raw1588, полностью наблюдаемых1511, gap69, нет третьей сессии8. Старые4431 исход не сканировались по OHLC повторно. Все749 новых закрытий проверены существующим quote/ATR/NEXT_OPEN/first-exit checker. Это PASS арифметики наблюдаемых закрытий, не PASS полноты всей торговой истории.',
        '', '## Перекрытие на одинаковой вселенной Si+MIX', '',
        '| Робот | Сделок | Net C1 R | Сверка |','|---|---:|---:|---|']
    for r in audit['overlap_replay']:lines.append(f"| {names[r['strategy']]} | {r['trades']} | {n(r['net_C1_R'])} | exact records PASS |")
    lines+=['', '**Отдельно фактическое продолжение состояния из2012 (не сброшенное на2018):**', '',
        '| Робот | Закрытий2018–2022 | Net C1 R |','|---|---:|---:|']
    for r in audit['continuous_replay_overlap']:lines.append(f"| {names[r['strategy']]} | {r['trades']} | {n(r['net_C1_R'])} |")
    lines+=['', 'Это два прогона прежней функции на одинаковых Si+MIX с прежним и расширенным roll-plan. CNY отсутствует и в кандидатах, и в дневном лимите. Вычеркнуть сделки CNY из трёхсимвольного ledger — другая операция; исходные 1004 результата сохраняются.',
        '', '## Новые годы: полная первичная статистика', '',
        '| Год | Робот | N | PF C1* | Net R* | DD closed R* | Win rate | Средний выигрыш | Стопы |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in sorted((r for r in annual if r['instrument']=='ALL' and r['year']<2018),key=lambda r:(r['year'],r['strategy'])):
        lines.append(f"| {r['year']} | {names[r['strategy']]} | {r['n']} | {n(r['PF_C1'])} | {n(r['net_R'])} | {n(r['DD_closed_R'])} | {n(r['win_rate'])} | {n(r['mean_win_R'])} | {n(r['initial_stop_share'])} |")
    lines+=['', '*Условный LOCKED_V1 replay с указанными проблемами данных. DD каждого независимого счета, не общий денежный портфель. В частности Shallow2012–2017: 13 gap-stop закрытий дают −168.144R при общем −139.291R; OBV9 дают −67.812R, Inside3 дают −15.356R. Структуру убытков нельзя свести к частоте −1R стопов.',
        '', '## Наблюдаемые закрытия 2012–2022 из отдельно стартовавших журналов (не непрерывный капитал)', '',
        '| Робот | Инструмент | N | PF C1* | Net R* | DD closed R* |', '|---|---|---:|---:|---:|---:|']
    for m in MODES:
        for s in ('Si','MIX','CNY','ALL'):
            r=describe([r for (mode,instr),rows in groups.items() if mode==m and instr in ('Si','MIX','CNY') and (s=='ALL' or s==instr) for r in rows])
            lines.append(f"| {names[m]} | {s} | {r['n']} | {n(r['PF_C1'])} | {n(r['net_R'])} | {n(r['DD_closed_R'])} |")
    lines+=['', 'ALL — три доступных инструмента соответствующих лет внутри одного счета; CNY не существовал в ранней вселенной. 2012–2017 впервые исследованы, 2018–2026 многократно использовались; вся история не независимый OOS.',
        '', '## Сравнение эпох и механизма прибыли', '',
        '| Эпоха | Робот | N | PF | Net R | DD R | Win rate | Средний выигрыш | Стопы | FP4 | FP5 | Доля положительных R от net≥5 |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in summary['epochs']:
        tail=r['tails'];lines.append(f"| {r['epoch']} | {names[r['strategy']]} | {r['n']} | {n(r['PF_C1'])} | {n(r['net_R'])} | {n(r['DD_closed_R'])} | {n(r['win_rate'])} | {n(r['mean_win_R'])} | {n(r['initial_stop_share'])} | {n(tail['FP4'])} | {n(tail['FP5'])} | {n(r['net_ge5_share_positive_R'])} |")
    lines+=['', '2018 был прибыльным при высокой доле стопов и очень редких, но больших выигрышах. Слабость OBV2019–2022 (PF1.008) не означает такую же слабость Inside (PF1.498). Поздний N4 отличается составом контрактов и большей частотой выигрышей; нельзя приписать всю разницу единому индикатору.',
        'Среднее net = win_rate × mean_win + loss_rate × mean_loss (нулевые исходы отдельно), PF = positive_R/negative_R. Это тождество, а не несколько независимых подтверждений. Снижение среднего выигрыша/хвоста и gap-убытки объясняют изменения результата; частота стопов отдельно недостаточна.',
        'FP2/3/4/5, >5, MFE нижняя/верхняя граница, неоднозначность и цензурирование — в LARGE_MOVES. Raw-квартал относится к решению по сигналу, модельные крупные выигрыши там — по входу; экономические ANNUAL/MONTHLY/QUARTERLY — по доступности закрытия. Поэтому числа 2018 могут отличаться от 193 входов старого отчета: здесь191 завершение. Траектория до стопа не прибыль сделки.',
        '', '## Длительные циклы и наблюдаемая задержка', '',
        '| Робот / инструмент | Начало слабости | Первый квартал известен | Два квартала известны | Конец слабой серии | Net R | Диагностика внутри серии | Следующий квартал net (N) |',
        '|---|---|---|---|---|---:|---|---|']
    for r in episodes:
        if r['negative_quarters']>=2:
            lines.append(f"| {names[r['strategy']]} / {r['instrument']} | {str(r['onset'])[:10]} | {str(r['first_known'])[:10]} | {str(r['sustained_known'])[:10]} | {str(r['last_weak_end'])[:10]} | {n(r['net_R'])} | {str(r['first_monitor_diagnostic_during_weak'])[:10]} | {n(r['next_quarter_net'])} ({r['next_quarter_n']}) |")
    lg=summary['long_weak_episodes']
    lines+=['', f"Длительных эпизодов {lg['n']}; диагностика не появилась внутри слабой серии в {lg['missed_during_weak']}. Среди {lg['detected']} обнаруженных медиана задержки {lg['median_delay_days']} дней, диапазон {lg['min_delay_days']}–{lg['max_delay_days']}. Условность ранних источников остаётся. Это оценка запаздывающего мониторинга, не обещание предотвращения убытков.",
        'Si/Shallow: отрицательная серия 01.10.2019–01.04.2020, первый завершённый квартал известен 01.01.2020, подтверждение двух — 01.04.2020. Внутри серии ДИАГНОСТИКА по 3/6 не появилась: нельзя объявлять, что карточка защитила от главного ухудшения 2019–2022. Период 2019–2022 не целиком отрицателен для всех стратегий.',
        'Эпизод здесь: последовательные полные отрицательные кварталы с N≥10, только внешний ретроспективный ярлык. Малый N прерывает доказуемую последовательность, а не доказывает восстановление. Все одиночные эпизоды и первая поздняя НОРМА — REGIME_EPISODES.csv. Диагностика может не появиться внутри слабой серии из-за малой выборки/цензурирования; отсутствие тревоги не успех.',
        '', '## Ложные предупреждения и цена гипотетического исключения', '',
        '| Эпоха | Квартальных предупреждений | FALSE | Дальше слабость | UNRESOLVED | Потеря положительных R | Предотвращённые отрицательные R | Потеря выигрышей / предотвращённые убытки |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for r in summary['alerts']:lines.append(f"| {r['epoch']} | {r['n']} | {r['false']} | {r['continued']} | {r['unresolved']} | {n(r['lost_positive_R'])} | {n(r['avoided_negative_R'])} | {r['lost_winners']} / {r['avoided_losers']} |")
    lines+=['', 'Это проверки на квартальных границах с обоими достаточными отрицательными окнами; повторные соседние проверки не называются независимыми эпизодами. Стоимость — новые входы следующего квартала, не повторный торговый replay с освобождением дневного лимита. Одна и та же сделка не попадает в две соседние квартальные цены одного робота/инструмента.',
        'FALSE требует полный следующий квартал, ≥10 закрытий и отсутствие цензурирования. Положительный квартал с N<10 остаётся UNRESOLVED, его фактический net не скрывается. Никакого определения ложности самим правилом двух плохих окон.',
        '', '| Дата | Робот / инструмент | Следующий квартал net | Потеря выигрышей R | Избежали убытков R |', '|---|---|---:|---:|---:|']
    for r in alerts:
        if r['label']=='FALSE_ALERT':lines.append(f"| {str(r['decision_at'])[:10]} | {names[r['strategy']]} / {r['instrument']} | {n(r['next_quarter_net'])} | {n(r['lost_positive_R'])} | {n(r['avoided_negative_R'])} |")
    lines+=['', '**GLDRUBF/Shallow 01.07.2025 повторно демонстрирует проблему:** отрицательное полугодие −12.681R, затем следующий квартал +21.567R. Это повод наблюдать причины и качество данных, а не доказательство необходимости исключения. Следующий положительный квартал возможен и после нескольких отрицательных.',
        '', '## Контроль старых правил только на добавленном блоке 2012–2017', '',
        '| Правило | Квартальных BAD-проверок по счету/инструменту | FALSE | Продолжение | UNRESOLVED | Покрытие месячных точек |',
        '|---|---:|---:|---:|---:|---:|']
    for r in summary['early_fixed_controls']:lines.append(f"| {r['method']} | {r['warning_reviews']} | {r['false']} | {r['continued']} | {r['unresolved']} | {n(100*r['monthly_coverage'])}% |")
    lines+=['', 'Параметры и реализации не изменены, оценки на том же внешнем следующем квартале C1. Raw/TWO имеют единый поток уникальных событий инструмента; строка оценки по роботу проверяет его собственные исполнимые исходы, поэтому это не старый счетчик raw-эпизодов. EDGE использует C120/60; 3/6 повторяют прежние правила, включая удержание исключения. Это диагностический контроль новых лет, не поиск победителя. Малые выборки оставляют много UNRESOLVED. Старые 2018–2026 результаты/кэши/FAIL сохранены без нового replay: V20_CALENDAR_REVIEW_RESULTS.json, V20_SUITABILITY_COMPARISON.json, REGIME_FINAL_COMPARISON.json.',
        '', '## Реальная карточка и архивные снимки', '',
        'Запуск из корня репозитория:', '', '```bash',
        'python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --monitoring --symbol ALL --as-of 2015-07-01',
        'python -m V20_TradingSystem_M15.v20_runtime.market_suitability_cli --monitoring --symbol GLDRUBF --as-of 2025-07-01 --format json',
        '```', '',
        'Верх: источник/границы архива, счетные net/PF отдельно, затем роботы/инструменты, 3м/6м N/net/PF, выигрыш/FP4/FP5/стопы, последнее закрытие, статус и причина. Текущий неполный месяц информационный, основной статус только по полным месяцам. Нет вкладок, сервиса, брокера, автоматической ротации. Без `--monitoring` прежний CLI сохранён.',
        'НОРМА означает только наблюдаемую положительную экономику двух достаточных окон. НАБЛЮДАТЬ — расхождение; ДИАГНОСТИКА — оба отрицательны. Недостаточность/цензурирование и устаревший источник отдельны. Достаточность не превращает результат в прогноз. Исторические статусы условны относительно верифицируемости источника.',
        '', '| As-of | Робот / пример инструмента | 3м N / net / PF | 6м N / net / PF | Статус | Следующий полный квартал net (N), только оценка |',
        '|---|---|---|---|---|---|']
    for snap in snapshots:
        card=snap['card'];t=dt(card['as_of_msk']);symbol='Si' if t.year<=2022 else 'GLDRUBF'
        for r in card['rows']:
            if r['instrument']!=symbol:continue
            ev=next(v['future'] for v in snap['retrospective_evaluation_only'] if v['strategy']==r['strategy'] and v['instrument']==symbol)
            a,b=r['w3'],r['w6'];q=ev['completed']
            lines.append(f"| {str(t)[:10]} | {names[r['strategy']]} / {symbol} | {a['n']} / {n(a['net_R'])} / {n(a['PF_C1'])} | {b['n']} / {n(b['net_R'])} / {n(b['PF_C1'])} | {r['status']} | {n(q['net_R'])} ({q['n']}), {'полный' if ev['complete'] else 'НЕПОЛНЫЙ'} |")
    lines+=['', 'CARD_SNAPSHOTS.json содержит все инструменты каждой эпохи, а не только примеры таблицы. Future лежит вне объекта card и никогда не передаётся функции статуса. Inside часто недостаточен — рост его прибыли не даёт права игнорировать маленький N. На текущую дату после архива карточка сообщает НЕТ АКТУАЛЬНЫХ ДАННЫХ / архив закончился; FINAM LIVE не подключён.',
        '', '## Что мониторить и чего не делать', '',
        'Минимум: N/актуальность/цензурирование, средний net C1 и PF как две формы экономики, win rate и средний выигрыш для разложения результата, частота FP4/FP5 и фактически закрытых net≥4/5 для хвоста, стопы и gap-стопы как диагностика исполнения/убытков. Mean loss/DD/комиссии/концентрация остаются в подробных файлах. Не считать коррелирующие признаки независимыми голосами.',
        'Крупные победители редки, пропуск одного способен развернуть квартал. Низкий FP5 и отрицательный квартал не доказывают длительную потерю преимущества. В раннем архиве добавляется сильная неопределённость исполнимости/спецификаций. Надёжной вероятности будущего восстановления не получено: частоты FALSE/UNRESOLVED описывают конкретную выборку, не универсальную вероятность.',
        '**Ответ на главный вопрос:** мониторинг своевременно показывает уже реализованные изменения и их структуру, но не доказал способность безопасно исключать инструменты перед длительным ухудшением и возвращать их без потери восстановления. Использовать как READONLY статистическую диагностику можно; как валидированный индикатор потери преимущества — нельзя (FAIL). Никаких параметров/инструментов/риска автоматически не менять.',
        '', '## Воспроизводимость, тесты и завершение', '',
        'Протокол: V20_2012_MONITORING_PROTOCOL_RU.md; расчёт: history_extension.py → monitoring_research.py. Первый требует два внешних ZIP и внешний --work; второй только опубликованные производные источники. Проверены749 новых закрытий без повторного полного аудита старой диагностики. Машинные значения без округления отчета: CSV/RESULTS/MANIFEST, результаты проверок — VERIFICATION.json.',
        'Адресные проверки: новые749 выходов по котировкам, frozen SHA, изменение только календарного guard, причинный roll, ATR/NEXT_OPEN/C1/лимиты, prefix-invariance карточек, яд/непарсинг будущего исхода, месячное распределение, малый N, восстановление, архивность. Неизменённые старые полные аудиты переиспользованы и отмечаются SKIP. Точный PASS/FAIL/SKIP записан в V20_2012_2026_VERIFICATION.json после фактического запуска.',
        'Исследование закрывается без подбора новых порогов. 04.2 frozen parity → 04.3 H1 execution остаются следующим основным направлением. Никакого заявления о завершении этих отдельных этапов здесь нет. Roadmap ровно8 этапов/24 подэтапа; H1/IntradayLab/FINAM/N4/риски/счета/Tasks не затронуты.']
    (FOLDER/(P+'FINAL_RU.md')).write_text('\n'.join(lines)+'\n')


def verify(market=None):
    """One bounded repeat of derivative aggregation, targeted tests and CLI."""
    before={p.name:digest(p) for p in FOLDER.glob(P+'*.csv')}
    before[P+'CARD_SNAPSHOTS.json']=digest(FOLDER/(P+'CARD_SNAPSHOTS.json'))
    build()
    assert all(digest(FOLDER/n)==h for n,h in before.items()),'NONDETERMINISTIC_DERIVATIVES'
    suite=unittest.defaultTestLoader.loadTestsFromNames([
        'V20_TradingSystem_M15.v20_runtime.tests.test_market_monitoring',
        'V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability',
        'V20_TradingSystem_M15.v20_runtime.tests.test_confirmed_market_regime'])
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful(),'TARGET_TEST_FAILURE'
    smoke=[]
    for args in (['--monitoring','--symbol','ALL','--as-of','2013-07-01'],
                 ['--monitoring','--symbol','ALL','--as-of','2026-10-23'],
                 ['--symbol','USDRUBF','--as-of','2026-07-01']):
        cmd=[sys.executable,'-m','V20_TradingSystem_M15.v20_runtime.market_suitability_cli',*args,'--format','json']
        run=subprocess.run(cmd,cwd=ROOT.parent,capture_output=True,text=True,check=True)
        card=json.loads(run.stdout)
        if '--monitoring' in args:
            assert not card['feed_connected'] and not card['automatic_actions'] and not card['validated_indicator']
        smoke.append(dict(args=args,status='PASS',schema=card['schema']))
    quotes={}
    if market:
        expected=json.loads((FOLDER/'REGIME_RESULTS.json').read_text())['provenance']['source_sha256']
        for s in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
            h=digest(market/s/(s+'_M15.csv'));assert h==expected[s],s
            quotes[s]=h
    audit=json.loads((FOLDER/'V20_2012_2022_SOURCE_AUDIT.json').read_text())
    receipt=dict(calculation='PASS_OBSERVED_RESULTS_ONLY',full_early_replay='FAIL_PARTIAL_MISSING_SOURCE_EXIT_LOCKS_SHALLOW_SI',reliable_exclusion='FAIL_NOT_PROVEN',
        source_certification='FAIL_EARLY_MIX_GRID; EARLY_OPEN_EXECUTABILITY_UNVERIFIED',
        unit_tests=dict(PASS=result.testsRun-len(result.skipped),FAIL=len(result.failures)+len(result.errors),SKIP=len(result.skipped)),
        deterministic_derivative_artifacts=dict(status='PASS',count=len(before)),
        new_quote_trade_checks=audit['new_trade_quote_ATR_NEXT_OPEN_first_exit_checks'],
        overlap=audit['overlap_replay'],cli_smoke=smoke,
        late_quote_source_hashes=quotes,late_quote_hash_check='PASS' if quotes else 'SKIP_NOT_PROVIDED',
        skipped=dict(old_4431_quote_outcomes='SKIP unchanged source/code SHA receipts reused',
            original_late_ledger='SKIP original absent; published reproduction1589 reused',
            late_replay='SKIP unchanged1589 frozen reproduction, no needless replay',
            live='SKIP no connected FINAM feed; no authorization or need for trading operations'),
        counts=dict(new_closed=731,new_censored=18,new_unknown_open=1,new_observed_raw=1511,old_closed=1004,late_closed=1589,
            total_observable_closed=3324,source_bars=299998,contracts=88,overlap_source_files=40),
        commands=['python -m V20_TradingSystem_M15.v20_runtime.monitoring_research --verify --market /path/to/forever',
            'python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_market_monitoring V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability V20_TradingSystem_M15.v20_runtime.tests.test_confirmed_market_regime -v'])
    (FOLDER/(P+'VERIFICATION.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    summary=json.loads((FOLDER/(P+'RESULTS.json')).read_text());summary['calculation']='PASS_OBSERVED_RESULTS_ONLY';summary['verification']=P+'VERIFICATION.json'
    (FOLDER/(P+'RESULTS.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    manifest=json.loads((FOLDER/(P+'MANIFEST.json')).read_text())
    for p in FOLDER.glob(P+'*'):
        if p.suffix in ('.csv','.json') and p.name!=P+'MANIFEST.json':manifest['artifacts'][p.name]=digest(p)
    (FOLDER/(P+'MANIFEST.json')).write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('VERIFIED',receipt['unit_tests'],len(before),'deterministic data artifacts')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');parser.add_argument('--market',type=Path)
    args=parser.parse_args()
    verify(args.market) if args.verify else build()
