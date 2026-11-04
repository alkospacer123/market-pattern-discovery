"""READONLY, archive-only monitoring of completed frozen V20 C1 results.

No broker, database, gate, instrument rotation or trading lifecycle imports.
Economic statuses are descriptive and explicitly NOT validated loss warnings.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime, timedelta
import json
from statistics import mean

from .calendar_review import statistics, shift_month, completed_window
from .calendar_tail_diagnostics import known_raw, tail_stats
from .suitability_research import load_sources, trade_row, MODES, NEW
from .regime_monthly_comparison import ROOT, FOLDER, read_csv, digest, dt

P='V20_2012_2026_'
NORMAL='НОРМА'
WATCH='НАБЛЮДАТЬ'
DIAG='ТРЕБУЕТСЯ ДИАГНОСТИКА'
INSUF='НЕДОСТАТОЧНО ДАННЫХ'
STALE='НЕТ АКТУАЛЬНЫХ ДАННЫХ'


def load_data(*, verify=True):
    if verify:
        receipt=json.loads((FOLDER/(P+'MANIFEST.json')).read_text())
        for name,h in receipt['card_inputs'].items():
            if digest(ROOT/name)!=h:raise ValueError('MONITOR_INPUT_SHA_MISMATCH '+name)
    groups,bounds,raw,hashes=load_sources()
    early=list(read_csv(FOLDER/'V20_2012_2022_REPLAY_TRADES.csv'))
    for r in early:groups[r['account'],r['family']].append(trade_row(r))
    spans={}
    for name,modern in (('V20-03/results/CLOSED_TRADES.csv',False),('V20-03/comparison/DIAGNOSTIC_REPLAY_TRADES.csv',True),
                        ('V20-04/V20_2012_2022_REPLAY_TRADES.csv',False)):
        for r in read_csv(ROOT/name):
            spans[r['account'],r['symbol'] if modern else r['family'],dt(r['entry_dt'])]=int(r['session_span'])
    for key,rows in groups.items():
        rows.sort(key=lambda r:(r['available'],r['signal'],r['contract']))
        for r in rows:r['session_span']=spans[key[0],key[1],r['entry']]
    for r in read_csv(FOLDER/(P+'NEW_RAW_PATHS.csv')):
        raw.append(dict(strategy=r['strategy'],instrument=r['instrument'],contract=r['contract'],signal=dt(r['signal']),decision=dt(r['decision']),
            horizon_status=r['horizon_status'],outcome=json.loads(r['outcome'])))
    for s in ('Si','MIX'):bounds[s]=(datetime(2012,1,1),bounds[s][1])
    censored=[]
    for r in read_csv(ROOT/'V20-03/results/CENSORED_CLOSED.csv'):
        censored.append(trade_row(r))
    for r in read_csv(FOLDER/(P+'CENSORED_TRADES.csv')):censored.append(trade_row(r))
    audit=json.loads((FOLDER/'V20_2012_2022_SOURCE_AUDIT.json').read_text())
    for r in audit['early_open_positions']:
        censored.append(dict(strategy=r['account'],instrument=r['family'],entry=dt(r['entry_dt']),available=datetime.max,
            unknown_after=dt(r['unknown_after']) if r['unknown_after'] else datetime.max,scope_end=dt(r['scope_end']),
            reason='MISSING_CONTRACT_THIRD_SESSION_EXIT'))
    meta=json.loads((ROOT/'V20-02_AUDIT/ACCEPTANCE_V20_02.json').read_text())
    for strategy,m in meta['meta'].items():
        for r in m['terminal_positions']:
            censored.append(dict(strategy=strategy,instrument=r['symbol'],entry=dt(r['entry_dt']),available=datetime.max))
    return groups,bounds,raw,censored,hashes


def economic_status(w3,w6):
    if not(w3['sufficient'] and w6['sufficient']):return INSUF
    if w3['net_R']<0 and w6['net_R']<0:return DIAG
    if w3['net_R']>0 and w6['net_R']>0:return NORMAL
    return WATCH


def window(rows, raw, t, months, start):
    w=completed_window(rows,t,months,start)
    a=w['window_start']
    trades=[r for r in rows if a<r['available']<=t]
    paths=known_raw([r for r in raw if a<=r['decision']<t],t)
    w['structure']=tail_stats(paths,trades)
    w['structure']['gap_stop_n']=sum(r['reason']==2 for r in trades)
    w['structure']['gap_stop_net_R']=sum(r['net'] for r in trades if r['reason']==2)
    w['structure']['worst_closed_net_R']=min((r['net'] for r in trades),default=None)
    w['mean_win_R']=w['structure']['mean_win_R'];w['mean_loss_R']=w['structure']['mean_loss_R']
    return w


def assess(rows,raw,start,end,as_of,censored=()):
    cut=datetime(as_of.year,as_of.month,1)
    if start.month==1 and start.day<=3:history=datetime(start.year,1,1)
    else:history=shift_month(datetime(start.year,start.month,1),1)
    w3,w6=[window(rows,raw,cut,m,history) for m in (3,6)]
    # An unobservable model result cannot become favourable by being dropped.
    uncertain=[r for r in censored if shift_month(cut,-6)<=r['entry']<cut]
    unresolved=[r for r in censored if r.get('unknown_after',datetime.max)<=as_of<r.get('scope_end',datetime.max)]
    economic=economic_status(w3,w6)
    if uncertain or unresolved:economic=INSUF
    known=[r for r in rows if r['available']<=as_of]
    last=max((r['available'] for r in known),default=None)
    status=STALE if as_of>end+timedelta(days=90) else economic
    return dict(status=status,economic_status=economic,as_of=as_of,assessment_at=cut,
        w3=w3,w6=w6,current_month=statistics([r for r in known if cut<r['available']<=as_of]),
        unresolved_model_positions=len(unresolved),
        last_closed_result=last,known_closed=len(known),uncertain_results_6m=len(uncertain),
        source_through=min(as_of,end),source_state='ARCHIVE_ENDED' if as_of>end else 'HISTORICAL_ARCHIVE',
        explanation={NORMAL:'Оба полных окна положительны; будущая прибыль не гарантирована.',
            WATCH:'Окна расходятся либо нулевые: наблюдать структуру, без исключения инструмента.',
            DIAG:'Оба полных окна отрицательны: проверить размер выигрыша, хвост прибыли и исполнение.',
            INSUF:('Frozen replay заблокирован неизвестным выходом старого контракта; полная экономика NOT AVAILABLE.' if unresolved else 'Нужны полные 3/6 месяцев, 10/20 сделок и наблюдаемые исходы.'),
            STALE:'Архив устарел, текущий источник не подключён.'}[status])


def monitoring_card(groups,bounds,raw,censored,as_of,symbol='ALL'):
    if as_of.tzinfo is not None:raise ValueError('EXPECTED_NAIVE_MSK_AS_OF')
    universe=('Si','MIX','CNY') if as_of.year<=2022 else NEW
    if symbol!='ALL':
        if symbol not in bounds:raise ValueError('UNKNOWN_SYMBOL '+symbol)
        universe=(symbol,)
    selected=[s for s in universe if s in bounds and bounds[s][0]<=as_of]
    cards=[];accounts=[]
    for strategy in MODES:
        account_rows=[];account_raw=[];account_bad=[]
        for s in selected:
            rows=groups.get((strategy,s),[]);paths=[r for r in raw if r['strategy']==strategy and r['instrument']==s]
            bad=[r for r in censored if r['strategy']==strategy and r['instrument']==s and r['entry']<=as_of]
            card=assess(rows,paths,*bounds[s],as_of,bad)
            card.update(strategy=strategy,instrument=s)
            card['source_quality']='CONDITIONAL_LOCKED_V1_UNVERIFIED_HISTORICAL_SPECIFICATIONS' if s in ('Si','MIX') else 'SHA_PINNED_N4_MODEL_REPRODUCTION'
            cards.append(card);account_rows+=rows;account_raw+=paths;account_bad+=bad
        if selected:
            # Per-account sum is descriptive of currently available instruments;
            # do not classify the account using pooled N to conceal sparse rows.
            t=datetime(as_of.year,as_of.month,1)
            accounts.append(dict(strategy=strategy,w3=statistics([r for r in account_rows if shift_month(t,-3)<r['available']<=t]),
                w6=statistics([r for r in account_rows if shift_month(t,-6)<r['available']<=t]),
                instrument_status_counts={state:sum(r['economic_status']==state for r in cards if r['strategy']==strategy) for state in (NORMAL,WATCH,DIAG,INSUF)},
                majority_observed_weak=sum(r['economic_status']==DIAG for r in cards if r['strategy']==strategy)>len(selected)/2,
                scope='INDEPENDENT_ACCOUNT; inspect instrument sufficiency separately'))
    end=max((bounds[s][1] for s in selected),default=datetime.min)
    return dict(schema='v20.monitoring.readonly.v1',as_of_msk=as_of,feed_connected=False,
        status=STALE if not selected or as_of>end else 'АРХИВНЫЙ СНИМОК',
        history_start=min((bounds[s][0] for s in selected),default=None),history_through=min(as_of,end) if selected else None,
        accounts=accounts,rows=cards,validated_indicator=False,automatic_actions=False,
        source_health='ARCHIVE_ONLY_NOT_LIVE_EXECUTION_CERTIFICATION',
        warning='Диагностическая статистика, не прогноз и не валидированный сигнал исключения. FINAM LIVE не подключён.',
        source_limitations='LOCKED_V1 условный квартальный replay; MSK/OPEN и экспирации не заверены поставщиком. Ранний MIX tick=25 не подтверждён. Два дефекта OHLC Si2012 карантинированы. Shallow/Si заблокирован неизвестным выходом Si-12.14 в2014; 2018 reference начинается независимо, без синтетического закрытия.')


def format_text(card):
    def num(v):return f'{v:.3f}' if v is not None else 'Н/Д'
    lines=['V20 — МОНИТОРИНГ РАБОТОСПОСОБНОСТИ (READONLY)',
        f"На {card['as_of_msk']} МСК | {card['status']} | FINAM LIVE: не подключён",
        f"Доступная история: {card['history_start']} — {card['history_through']}",
        'Робот / инструмент | 3м: N, net R, PF | 6м: N, net R, PF | Статус']
    for r in card['rows']:
        a,b=r['w3'],r['w6']
        lines.append(f"{r['strategy']} / {r['instrument']} | {a['n']}, {num(a['net_R'])}, {num(a['PF_C1'])} | "
            f"{b['n']}, {num(b['net_R'])}, {num(b['PF_C1'])} | {r['status']}")
        ta,tb=a['structure'],b['structure']
        lines.append(f"  Выигрыш R {num(ta['mean_win_R'])}/{num(tb['mean_win_R'])}; win rate {num(ta['win_rate'])}/{num(tb['win_rate'])}; "
            f"FP4 {num(ta['FP4'])}/{num(tb['FP4'])}; FP5 {num(ta['FP5'])}/{num(tb['FP5'])}; "
            f"стопы сделок {num(ta['trade_stop_share'])}/{num(tb['trade_stop_share'])}; gap-стопы {ta['gap_stop_n']}/{tb['gap_stop_n']}. Последний результат {r['last_closed_result']}.")
        lines.append('  '+r['explanation'])
        if r['instrument'] in ('Si','MIX'):lines.append('  Источник: условные исторические спецификации/исполнимость OPEN; экономический статус не заверяет качество источника.')
    lines.append('Сводка по отдельным счетам (R между счетами не денежный портфель):')
    for r in card['accounts']:
        a,b=r['w3'],r['w6'];lines.append(f"  {r['strategy']}: 3м {num(a['net_R'])}R PF {num(a['PF_C1'])}; 6м {num(b['net_R'])}R PF {num(b['PF_C1'])}; "
            f"инструментов с диагностикой {r['instrument_status_counts'][DIAG]}, с недостатком данных {r['instrument_status_counts'][INSUF]}; большинство слабых: {r['majority_observed_weak']}")
    lines.extend([card['warning'],card['source_limitations']])
    return '\n'.join(lines)
