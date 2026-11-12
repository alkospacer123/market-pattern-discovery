"""One fixed offline phase probe. No strategy replay or trading integration.

Definitions below are fixed before reading phase/outcome results. OHLC source
adapters reuse market_epochs; all three metrics reuse market_suitability.
"""
from __future__ import annotations
import argparse
from bisect import bisect_left
from collections import Counter,defaultdict
from datetime import date,datetime,timedelta
import hashlib
import io
import json
from pathlib import Path
from statistics import mean,median
import zipfile

from .market_epochs import ROOT,FAMILY,series,unknown_gap,card_values
from .market_suitability import STEP,evaluate_market_card,_efficiency,_breakout_stats
from .regime_research import read_quotes,dump_csv
from .regime_monthly_comparison import digest,read_csv,dt
from .market_monitoring import load_data
from .suitability_research import MODES
from .calendar_review import statistics

OUT=ROOT/'V20-04'
STATES=('TREND','CHOP','TRANSITION','UNKNOWN')
PERIODS=('2012-2017','2018-2022','2023-2024','2025-2026_YTD')
PROTOCOL=dict(input_head='64c03e4583fe355e4ceddd10da181801c51f9d6a',window_sessions=20,
    calibration='40 PREVIOUS admissible snapshots; current excluded; no age tuning',
    ER='existing session_efficiency_ratio on20 session closes, not M15 ER20',
    breakout='existing20-prior-M15 close breakout; next M15 same session continuation/return',
    phase='ER and continuation strictly above prior medians TREND; both below CHOP; equality/mixed TRANSITION',
    sufficient_breakouts='existing nonzero completed_breakouts; denominators retained, no fitted new minimum',
    ATR='reference only; never used for state',
    roll='LOCKED_V1 choices; reset OHLC20 on roll/no selection, retain only normalized finished snapshots within SAME family',
    calibration_transfer='Si never pools with USDRUBF; MIX never pools with IMOEXF; no cross-N4 pooling',
    schedule='same conditional MSK daytime10:00..17:45, close18:00;32 bars; full-calendar authority unverified',
    quality='same full20 sessions, no unknown gap, source warmup200; quarantine2 Si bars with forced reset',
    evaluation='future5/10 observed sessions; same contract; full bars and uninterrupted source segment; no imputation',
    persistence='all next5/10 observed sessions including UNKNOWN, if archive horizon exists; do not select by future quote quality',
    external_ER='same efficiency formula, known closeT plus10 future session closes; no shared future returns',
    external_breakout='same helper on context session+future minus context; future events only',
    nonoverlap='fixed anchors i%10==0 in observed calendar from first research session; never selected by phase/outcome',
    independence='nonoverlapping TARGET sessions only; calibration/history/time dependence remain; no iid p-value claim',
    economics='existing closed ledgers only; last daily phase strictly BEFORE entry; same contract and unchanged known segment',
    verdict='A descriptive support needs both future metrics to retain TREND>CHOP in all sufficiently populated instrument-period cells (N>=10 each, descriptive inherited floor); otherwise NOT PROVEN. B/C/D numeric limitations disclosed; no parameter search',
    latency='no independent true phase-onset label: exact detection latency NOT AVAILABLE; compare past10 vs future10 progress descriptively',
    fixed_variants=1,replay_batches=0,parameter_searches=0,independent_OOS=False)


def epoch(day):
    return PERIODS[0] if day.year<2018 else PERIODS[1] if day.year<=2022 else PERIODS[2] if day.year<=2024 else PERIODS[3]


def phase(values,previous):
    # Filter current validity before touching numeric fields; prior prefix only.
    if values is None:return dict(phase='UNKNOWN',reason='INVALID_SNAPSHOT',baseline_n=min(len(previous),40))
    if len(previous)<40:return dict(phase='UNKNOWN',reason='FEWER_THAN40_PRIOR_VALID',baseline_n=len(previous))
    past=previous[-40:]
    er=median(r['er'] for r in past);bc=median(r['continuation'] for r in past)
    a,b=values['er']-er,values['continuation']-bc
    return dict(phase='TREND' if a>0 and b>0 else 'CHOP' if a<0 and b<0 else 'TRANSITION',reason='CLASSIFIED',
        baseline_n=40,baseline_er=er,baseline_continuation=bc,baseline_first=past[0]['available'],
        baseline_last=past[-1]['available'],baseline_span_days=(past[-1]['available']-past[0]['available']).days)


def prepare_series(bars,quarantined=()):
    source=series(bars)
    # Preserve forced reset even when quarantine coincides with a clearing gap
    # which LOCKED_V1 otherwise recognizes as a normal break.
    extra=0;previous=None;warm=0;old_segment=None
    for b in bars:
        seg,_=source['positions'][b.open_time]
        forced=previous is not None and any(previous<t<b.open_time for t in quarantined)
        if forced:extra+=1
        warm=1 if forced or seg!=old_segment else warm+1
        source['positions'][b.open_time]=(seg+extra,warm)
        old_segment=seg;previous=b.open_time
    return source


def load_sources(archive,old_archive,market):
    audit=json.loads((OUT/'V20_2012_2022_SOURCE_AUDIT.json').read_text())
    hashes={};sources={};plans=defaultdict(list);blocked=[]
    if archive and archive.exists():
        assert digest(archive)==audit['zip_sha256'],'NEW_ZIP_SHA_CHANGED'
        hashes['Si+MIX.zip']=digest(archive)
        with zipfile.ZipFile(archive) as z:
            for member in audit['members']:
                name=member['file'];data=z.read(name);assert hashlib.sha256(data).hexdigest()==member['sha256'],name
                quarantine=[dt(r['Datetime']) for r in audit['quarantined'] if r['file']==name]
                text=data.decode('utf-8-sig');skip={str(t) for t in quarantine}
                stream=io.StringIO('\n'.join(line for line in text.splitlines() if line.split(';')[0] not in skip))
                sources[Path(name).stem.removesuffix('_M15')]=prepare_series(read_quotes(stream),quarantine)
        for r in read_csv(OUT/'V20_2012_2026_ROLL_DECISIONS.csv'):
            plans[r['family']].append((dt(r['day']).date(),r['chosen_contract']))
    else:blocked+=['Si','MIX']
    if old_archive and old_archive.exists():
        assert digest(old_archive)==audit['old_zip_sha256'],'OLD_ZIP_SHA_CHANGED'
        hashes['2018-2022.zip']=digest(old_archive)
        with zipfile.ZipFile(old_archive) as z:
            maps=[r for r in read_csv(ROOT/'V20-03/results/CONTRACT_MAP.csv') if r['family']=='CNY']
            for r in maps:
                b=z.read(r['file']);assert hashlib.sha256(b).hexdigest()==r['sha256']
                sources[r['contract']]=prepare_series(read_quotes(io.StringIO(b.decode('utf-8-sig'))))
        for r in read_csv(ROOT/'V20-03/results/ROLL_DECISIONS.csv'):
            if r['family']=='CNY':plans['CNY'].append((dt(r['day']).date(),r['chosen_contract']))
    else:blocked+=['CNY']
    expected=json.loads((OUT/'V20_2012_2026_VERIFICATION.json').read_text())['late_quote_source_hashes']
    for s,h in expected.items():
        p=market/s/(s+'_M15.csv')
        if not p.exists():blocked.append(s);continue
        assert digest(p)==h,'N4_SOURCE_SHA_CHANGED '+s
        hashes[s]=h
        with p.open() as stream:sources[s]=prepare_series(read_quotes(stream))
        plans[s]=[(d,s) for d in sorted(sources[s]['sessions'])]
    names=('V20_2012_2026_FINAL_RU.md','V20_2012_2026_VERIFICATION.json','V20_2012_2022_SOURCE_AUDIT.json',
        'MARKET_EPOCH_COMPARISON_RU.md','MARKET_EPOCH_PROFILES.json','MARKET_CARD_RANGES_FINAL_RU.md','FROZEN_PARITY_PROGRESS_RU.md',
        'V20_2012_2026_ROLL_DECISIONS.csv')
    hashes.update({n:digest(OUT/n) for n in names})
    hashes.update({str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),Path(__file__).with_name('market_suitability.py'),Path(__file__).with_name('market_epochs.py')]})
    return sources,plans,hashes,blocked


def snapshot(source,history):
    if len(history)<20:return None,'ROLL_OR_INITIAL20_WARMUP'
    window=history[-20:]
    if any(s is None or tuple(b.open_time for b in s.bars)!=s.expected_opens for s in window):return None,'INCOMPLETE20_WINDOW'
    first=source['positions'][window[0].bars[0].open_time];last=source['positions'][window[-1].bars[-1].open_time]
    if first[0]!=last[0]:return None,'GAP20_WINDOW'
    if last[1]<200:return None,'SOURCE_WARMUP200'
    card=evaluate_market_card('PROBE',window,as_of=window[-1].closed_at,expected_session_days=[s.day for s in window])
    if not card['metrics']['breakouts']['completed_breakouts']:return None,'NO_COMPLETED_BREAKOUTS'
    v=card_values(card)
    closes=[s.bars[-1].close for s in window]
    return dict(er=v['directional_efficiency'],continuation=v['continuation_rate'],return_inside=v['return_inside_rate'],
        atr=v['atr14_pct_close'],breakouts=card['metrics']['breakouts']['completed_breakouts'],window_start=window[0].day,
        available=window[-1].closed_at,segment=last[0],past10_er=_efficiency(closes[-11:]),
        past10_abs_pct=abs(closes[-1]/closes[-11]-1),past_direction=1 if closes[-1]>closes[-11] else -1 if closes[-1]<closes[-11] else 0), 'VALID'


def timeline(instrument,plan,sources,cache=None):
    cachefile=cache/(instrument+'.json') if cache else None
    # Receipt pins full inputs and this adapter; cache stores CAUSAL features,
    # never future outcomes or states calibrated from the whole history.
    signature=hashlib.sha256(json.dumps(dict(plan=[(str(d),c) for d,c in plan],
        code=[digest(Path(__file__)),digest(Path(__file__).with_name('market_epochs.py')),digest(Path(__file__).with_name('market_suitability.py'))],
        sources={c:(len(sources[c]['bars']),str(sources[c]['bars'][0]),str(sources[c]['bars'][-1])) for c in {c for d,c in plan if c}}),sort_keys=True).encode()).hexdigest()
    receipt=cachefile.with_suffix('.receipt.json') if cachefile else None
    if cachefile and cachefile.exists() and receipt.exists() and json.loads(receipt.read_text())==dict(signature=signature,sha256=digest(cachefile)):
        rows=json.loads(cachefile.read_text())
        for r in rows:
            r['available']=dt(r['available']);r['day']=date.fromisoformat(r['day'])
            for k in ('baseline_first','baseline_last'):
                if k in r:r[k]=dt(r[k])
        return rows
    rows=[];history=[];prior=[];last=None
    for day,c in plan:
        if c!=last:history=[]
        last=c
        if not c:
            if day.year>=2012:rows.append(dict(instrument=instrument,contract='',day=day,available=datetime.combine(day,datetime.min.time()).replace(hour=18),phase='UNKNOWN',reason='NO_LOCKED_SELECTION',valid=False))
            continue
        source=sources[c];s=source['sessions'].get(day);history.append(s)
        if day.year<2012:continue
        values,reason=snapshot(source,history)
        current=phase(values,prior)
        r=dict(instrument=instrument,contract=c,day=day,available=s.closed_at if s else datetime.combine(day,datetime.min.time()).replace(hour=18),
            valid=values is not None,**current)
        if values is None:r['reason']=reason
        else:
            r.update(values)
            assert not prior or prior[-1]['available']<r['available']
            prior.append(dict(values))  # own snapshot becomes available ONLY for later days
        rows.append(r)
    if cachefile:
        cachefile.parent.mkdir(parents=True,exist_ok=True);cachefile.write_text(json.dumps(rows,default=str))
        receipt.write_text(json.dumps(dict(signature=signature,sha256=digest(cachefile))))
    return rows


def future(rows,index,sources,n=10):
    r=rows[index];q=rows[index+1:index+n+1]
    result=dict(future_status='CENSORED_END_OF_ARCHIVE',eval_anchor=index%10==0)
    if len(q)<n:return result
    result.update(future_available=q[-1]['available'],future_first=q[0]['day'],future_last=q[-1]['day'])
    # State persistence counts loss of observability as transition to UNKNOWN;
    # do not condition its denominator on valid FUTURE price windows.
    result.update(state_horizon_complete=True,same_state_continuous=all(x['phase']==r['phase'] for x in q),
        same_state_endpoint=q[-1]['phase']==r['phase'])
    c=r['contract']
    if not c or any(x['contract']!=c for x in q):return dict(result,future_status='ROLL_OR_NO_SELECTION')
    source=sources[c];sessions=[source['sessions'].get(x['day']) for x in [r,*q]]
    if any(s is None or tuple(b.open_time for b in s.bars)!=s.expected_opens for s in sessions):return dict(result,future_status='INCOMPLETE_SESSION')
    first=source['positions'][sessions[0].bars[-1].open_time];last=source['positions'][sessions[-1].bars[-1].open_time]
    if first[0]!=last[0]:return dict(result,future_status='GAP_CENSORED')
    past=_breakout_stats(sessions[:1]);total=_breakout_stats(sessions)
    events=total['completed_breakouts']-past['completed_breakouts'];wins=total['continuations']-past['continuations']
    returns=round((total['return_inside_rate'] or 0)*total['completed_breakouts']-(past['return_inside_rate'] or 0)*past['completed_breakouts'])
    closes=[s.bars[-1].close for s in sessions]
    return dict(result,future_status='OBSERVED',future_er=_efficiency(closes),future_breakouts=events,
        future_continuation=wins/events if events else None,future_return_inside=returns/events if events else None,
        future_abs_pct=abs(closes[-1]/closes[0]-1),future_signed_past_direction_pct=(closes[-1]/closes[0]-1)*r.get('past_direction',0),
        same_state_continuous=result['same_state_continuous'],same_state_endpoint=result['same_state_endpoint'])


def annotate_future(rows,sources):
    for i,r in enumerate(rows):
        r.update(future(rows,i,sources,10))
        f=future(rows,i,sources,5)
        r['future5_status']=f['future_status'];r['future5_available']=f.get('future_available')
        r['future5_first']=f.get('future_first');r['future5_last']=f.get('future_last')
        r['same_state_continuous5']=f.get('same_state_continuous');r['same_state_endpoint5']=f.get('same_state_endpoint')
    return rows


def phase_before(rows,entry,contract,source,signal):
    i=bisect_left([r['available'] for r in rows],entry)-1
    if i<0:return 'UNKNOWN','NO_PRIOR_SNAPSHOT',None
    r=rows[i]
    if r['contract']!=contract:return 'UNKNOWN','CONTRACT_CHANGED_SINCE_SNAPSHOT',r['available']
    if r['phase']=='UNKNOWN':return 'UNKNOWN',r['reason'],r['available']
    pos=source['positions'].get(signal)
    if pos is None or pos[0]!=r['segment']:return 'UNKNOWN','GAP_OR_MISSING_SIGNAL_AFTER_SNAPSHOT',r['available']
    return r['phase'],'CAUSAL_PRE_ENTRY',r['available']


def economics(timelines,sources):
    groups,_,_,_,hashes=load_data();assigned=[]
    for (strategy,symbol),rows in groups.items():
        for t in rows:
            source=sources.get(t['contract']);state,reason,at=phase_before(timelines.get(symbol,[]),t['entry'],t['contract'],source,t['signal']) if source else ('UNKNOWN','BLOCKED_SOURCE',None)
            assigned.append(dict(t,phase=state,phase_reason=reason,phase_available=at))
    summary=[]
    for period in (*PERIODS,'ALL'):
        for symbol in (*sorted(timelines),'ALL'):
            for strategy in MODES:
                for state in STATES:
                    q=[r for r in assigned if r['strategy']==strategy and r['phase']==state and (symbol=='ALL' or r['instrument']==symbol) and (period=='ALL' or epoch(r['entry'])==period)]
                    if not q:continue
                    values=[r['net'] for r in q];w=[v for v in values if v>0];l=[v for v in values if v<0]
                    summary.append(dict(period=period,instrument=symbol,strategy=strategy,phase=state,**statistics(q),
                        model_verification='CONDITIONAL_MIXED_EPOCH_REFERENCES' if period=='ALL' else 'CONDITIONAL_EARLY_SOURCE_PARTIAL_REPLAY' if period==PERIODS[0] else 'PUBLISHED_CONDITIONAL_LOCKED_V1' if period==PERIODS[1] else 'VERIFIED_FROZEN_REPRODUCTION_ORIGINAL_ROW_PARITY_ABSENT',
                        actual_exchange_execution_PF='NOT VERIFIED',
                        mean_win=mean(w) if w else None,mean_loss=mean(l) if l else None,stop_share=mean(r['stop'] for r in q),
                        net_ge4_n=sum(v>=4 for v in values),net_ge5_n=sum(v>=5 for v in values),
                        net_ge4_share_positive=sum(v for v in values if v>=4)/sum(w) if w else None,
                        net_ge5_share_positive=sum(v for v in values if v>=5)/sum(w) if w else None))
    return summary,hashes,dict(assigned=len(assigned),known_phase=sum(r['phase']!='UNKNOWN' for r in assigned),
        reasons=dict(Counter(r['phase_reason'] for r in assigned)),strict_pre_entry=True,
        limitation='Model C1 only; early MIX tick and Si OPEN unverified, Shallow Si missing exit2014;2018 reference restarts; late1589 verified reproduction, original row parity absent.')


def runs(rows):
    result=[]
    for r in rows:
        if result and result[-1]['phase']==r['phase']:result[-1]['n']+=1;result[-1]['end']=r['available']
        else:result.append(dict(phase=r['phase'],start=r['available'],end=r['available'],n=1))
    return result


def aggregate(timelines):
    results=[];allrows=[r for rows in timelines.values() for r in rows]
    for period in (*PERIODS,'ALL'):
        for symbol in (*sorted(timelines),'ALL'):
            bysym={s:[r for r in rows if period=='ALL' or epoch(r['day'])==period] for s,rows in timelines.items() if symbol=='ALL' or s==symbol}
            rr=[r for rows in bysym.values() for r in rows];episodes=[run for rows in bysym.values() for run in runs(rows)]
            for state in STATES:
                q=[r for r in rr if r['phase']==state];durations=[r['n'] for r in episodes if r['phase']==state]
                f=[r for r in q if r['eval_anchor'] and r['future_status']=='OBSERVED']
                fbc=[r for r in f if r['future_continuation'] is not None]
                f5=[r for r in q if r.get('same_state_continuous5') is not None];f10=[r for r in q if r.get('state_horizon_complete')]
                results.append(dict(period=period,instrument=symbol,phase=state,sessions=len(q),denominator=len(rr),
                    fraction=len(q)/len(rr) if rr else None,valid=sum(r['valid'] for r in q),episodes=len(durations),
                    run_mean=mean(durations) if durations else None,run_median=median(durations) if durations else None,
                    one_two_session_runs=sum(v<=2 for v in durations),future5_n=len(f5),future10_n=len(f10),
                    survive5=mean(r['same_state_continuous5'] for r in f5) if f5 else None,
                    survive10=mean(r['same_state_continuous'] for r in f10) if f10 else None,
                    endpoint_same10=mean(r['same_state_endpoint'] for r in f10) if f10 else None,
                    target_nonoverlap_n=len(f),future_er_mean=mean(r['future_er'] for r in f) if f else None,
                    future_er_median=median(r['future_er'] for r in f) if f else None,
                    future_continuation_mean=mean(r['future_continuation'] for r in fbc) if fbc else None,
                    future_return_inside_mean=mean(r['future_return_inside'] for r in fbc) if fbc else None,
                    future_breakout_horizons=len(fbc),future_breakouts=sum(r['future_breakouts'] for r in fbc),
                    past10_er_mean=mean(r['past10_er'] for r in f if 'past10_er' in r) if any('past10_er' in r for r in f) else None,
                    future_abs_pct_mean=mean(r['future_abs_pct'] for r in f) if f else None,
                    future_signed_mean=mean(r['future_signed_past_direction_pct'] for r in f) if f else None,
                    past10_abs_pct_mean=mean(r['past10_abs_pct'] for r in f if 'past10_abs_pct' in r) if any('past10_abs_pct' in r for r in f) else None,
                    median_calibration_span_days=median(r['baseline_span_days'] for r in q if 'baseline_span_days' in r) if any('baseline_span_days' in r for r in q) else None))
    switches=[]
    for symbol,rows in timelines.items():
        for period in (*PERIODS,'ALL'):
            q=[r for r in rows if period=='ALL' or epoch(r['day'])==period];rs=runs(q)
            switches.append(dict(period=period,instrument=symbol,sessions=len(q),switches=max(0,len(rs)-1),
                switches_per100_sessions=100*(len(rs)-1)/len(q) if q else None,
                A_B_A_returns=sum(a['phase']==c['phase']!=b['phase'] for a,b,c in zip(rs,rs[1:],rs[2:])),
                short_A_B_A_returns=sum(a['phase']==c['phase']!=b['phase'] and b['n']<=2 for a,b,c in zip(rs,rs[1:],rs[2:])),
                unknown_sessions=sum(r['phase']=='UNKNOWN' for r in q)))
    return results,switches


def build(archive,old_archive,market,work):
    assert ROOT not in work.resolve().parents and work.resolve()!=ROOT
    sources,plans,hashes,blocked=load_sources(archive,old_archive,market)
    timelines={}
    for s,plan in sorted(plans.items()):
        rows=timeline(s,plan,sources,work/'features');timelines[s]=annotate_future(rows,sources)
        print('PHASE',s,len(rows),dict(Counter(r['phase'] for r in rows)),flush=True)
    aggregates,switches=aggregate(timelines);economic,ledgerhash,assignment=economics(timelines,sources)
    flat=[r for s,rows in sorted(timelines.items()) for r in rows]
    dump_csv(OUT/'MARKET_PHASE_CAUSAL_PROBE.csv',flat)
    comparisons=[]
    for period in PERIODS:
        for s in (*sorted(timelines),'ALL'):
            a,b=[next(r for r in aggregates if r['period']==period and r['instrument']==s and r['phase']==state) for state in ('TREND','CHOP')]
            if a['target_nonoverlap_n'] and b['target_nonoverlap_n']:
                comparisons.append(dict(period=period,instrument=s,trend_n=a['target_nonoverlap_n'],chop_n=b['target_nonoverlap_n'],
                    sufficient=a['target_nonoverlap_n']>=10 and b['target_nonoverlap_n']>=10,
                    delta_future_er=a['future_er_mean']-b['future_er_mean'],
                    delta_future_continuation=a['future_continuation_mean']-b['future_continuation_mean'] if a['future_continuation_mean'] is not None and b['future_continuation_mean'] is not None else None))
    sufficient=[r for r in comparisons if r['sufficient'] and r['instrument']!='ALL']
    support=bool(sufficient and {r['period'] for r in sufficient}==set(PERIODS) and all(r['delta_future_er']>0 and (r['delta_future_continuation'] or 0)>0 for r in sufficient))
    data=dict(schema='v20.market_phase.causal_probe.v1',protocol=PROTOCOL,
        protocol_sha256=hashlib.sha256(json.dumps(PROTOCOL,sort_keys=True).encode()).hexdigest(),source_hashes=hashes,ledger_hashes=ledgerhash,
        blocked=blocked,aggregates=aggregates,switches=switches,contrasts=comparisons,economics=economic,economic_assignment=assignment,
        counts=dict(sessions=len(flat),valid=sum(r['valid'] for r in flat),classified=sum(r['phase']!='UNKNOWN' for r in flat),
            scheduled_nonoverlap_anchors=sum(r['eval_anchor'] for r in flat),observed_nonoverlap_targets=sum(r['eval_anchor'] and r['future_status']=='OBSERVED' for r in flat)),
        verdicts=dict(A='SUPPORTED' if support else 'NOT PROVEN' if sufficient else 'INSUFFICIENT DATA',
            B='NOT PROVEN',C='NOT PROVEN',D='NOT PROVEN',alternative_presets='INSUFFICIENT_EVIDENCE_NO_OPTIMIZATION'),
        latency='NOT AVAILABLE: no independent causal truth of latent phase onset; historical runs are predictions, not external onset truth.',
        tests=dict(status='PENDING'),independent_OOS=False,technical_PASS_is_not_economic_support=True)
    data['coverage_by_instrument']=[dict(instrument=s,observed=len(rows),valid=sum(r['valid'] for r in rows),
        phases=dict(Counter(r['phase'] for r in rows)),first_classified=min((r['available'] for r in rows if r['phase']!='UNKNOWN'),default=None),
        last_source_day=rows[-1]['day'] if rows else None) for s,rows in sorted(timelines.items())]
    (OUT/'MARKET_PHASE_CAUSAL_PROBE.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str,allow_nan=False)+'\n')
    write_report(data)
    return data


def write_report(data):
    def num(x):return f'{x:.4f}' if isinstance(x,(int,float)) else 'Н/Д' if x is None else str(x)
    names=dict(zip(MODES,('Shallow','OBV','Inside')))
    lines=['# V20-04.2 — одна причинная проверка фаз 2012–2026','',
        '**Фиксированная схема:** 20 завершённых сессий существующей карточки, медианы предыдущих40 допустимых снимков. Никакого нового индикатора/окна/порога по результатам. ATR справочный. Один расчёт, ноль replay стратегий.','',
        'Main `6f352acfac7ebdfabba73e143c4dfea3a6e48507`; исходный head `64c03e4583fe355e4ceddd10da181801c51f9d6a`. Точные SHA исходников/обязательных отчетов/модулей и протокол — JSON. Старые отрицательные выводы не пересматриваются.','',
        '## Определения и причинность','',
        'ER — именно существующий session_efficiency_ratio по закрытиям20 сессий, а не ER20 свечей M15. Продолжение — close-breakout предшествующих20 M15 и следующий завершённый M15 той же сессии; Return Inside — отдельное возвращение за пробитый уровень. Эти доли не обязательно дополняют друг друга до1.',
        'Одинаковая прежняя условная область10:00–17:45 MSK,32 M15, доступность18:00. Полные20 сессий, ≥200 баров прогрева сегмента, отсутствие неизвестного gap. Roll/no selection обнуляет OHLC-окно, прежние нормированные снимки того же семейства сохраняются в калибровке. Старый Si не калибрует USDRUBF; MIX не калибрует IMOEXF. Даже после gap база остаётся последними40 допустимыми снимками: её возраст/размах публикуется, нового age-порога нет.',
        'TREND — оба значения строго выше прежних медиан; CHOP — оба ниже; равенство/разные знаки — TRANSITION. Недостаток истории/пробоев/полноты — UNKNOWN. Текущий снимок добавляется в историю лишь после назначения своего состояния. 40 перекрывающихся снимков зависимы.',
        'Внешние цели — следующие5/10 наблюдаемых сессий одного контракта, без gap/пропусков. ER10 использует известный closeT и10 новых закрытий; breakout helper получает известную контекстную сессию, из итоговых счетчиков вычитаются её события. Поэтому внешняя оценка не содержит событий из классификационного окна.',
        'Основное сравнение будущего: фиксированные якоря i%10=0 с первой исследуемой сессии каждого инструмента. Целевые интервалы не перекрываются и не отбираются по фазе/результату. Калибровка и рынок зависимы: эти N не объявляются iid-наблюдениями. Ежедневные оценки сохраняются для переключений, не для умножения статистической силы.','',
        '## Источники и ограничения','',
        'Использованы тот же ZIP88 серий и N4 с подтверждёнными SHA; две Si OHLC2012 карантинированы с принудительным reset. Сетка раннего MIX и исполнимость экстремальных Si OPEN не подтверждены. Сессии/экспирации условны по LOCKED_V1. Валидные OHLC здесь описывают рынок, не заверяют цены исполнения.',
        'Экономика — только опубликованные731 раннее +1004 старых +1589 поздних наблюдаемых закрытий.18 ранних/12 старых цензурированных и открытые позиции не превращаются в прибыль. Shallow/Si неизвестен с12.12.2014, позднейший reference2018 стартует отдельно. Нет непрерывной доходности с2012. Поздний journal — проверенное воспроизведение, оригинальная row parity отсутствует.',
        'Источник отсутствует → BLOCKED/UNKNOWN, не синтетическая история. BLOCKED: '+str(data['blocked']),
        '', '## Покрытие по периодам','', '| Период | Наблюдаемых сессий | Допустимых снимков | TREND | CHOP | TRANSITION | UNKNOWN |','|---|---:|---:|---:|---:|---:|---:|']
    for period in PERIODS:
        q=[r for r in data['aggregates'] if r['period']==period and r['instrument']=='ALL']
        lines.append('| '+period+' | '+str(q[0]['denominator'])+' | '+str(sum(r['valid'] for r in q))+' | '+' | '.join(str(next(r['sessions'] for r in q if r['phase']==s)) for s in STATES)+' |')
    lines+=['','| Инструмент | Наблюдаемых / допустимых | TREND / CHOP / TRANSITION / UNKNOWN | Первая классификация |','|---|---|---|---|']
    for r in data['coverage_by_instrument']:lines.append(f"| {r['instrument']} | {r['observed']} / {r['valid']} | {' / '.join(str(r['phases'].get(s,0)) for s in STATES)} | {str(r['first_classified'])[:10]} |")
    lines+=['','## Фазы и будущее: вся доступная история','',
        '| Фаза | Сессии / доля | Эпизоды | Длительность mean / median | Эпизоды1–2 сессии | Сохранилось5 /10 сессий | Неперекрывающихся целей | Будущий ER | Продолжение / возврат |','|---|---|---:|---|---:|---|---:|---:|---|']
    for r in data['aggregates']:
        if r['period']=='ALL' and r['instrument']=='ALL':lines.append(f"| {r['phase']} | {r['sessions']} / {num(r['fraction'])} | {r['episodes']} | {num(r['run_mean'])} / {num(r['run_median'])} | {r['one_two_session_runs']} | {num(r['survive5'])} / {num(r['survive10'])} | {r['target_nonoverlap_n']} | {num(r['future_er_mean'])} | {num(r['future_continuation_mean'])} / {num(r['future_return_inside_mean'])} |")
    lines+=['','## Сохранение различий между периодами и инструментами','',
        '| Период | Инструмент | N TREND / CHOP | Δ будущего ER | Δ продолжения | ≥10 целей в обеих фазах |','|---|---|---|---:|---:|---|']
    for r in data['contrasts']:lines.append(f"| {r['period']} | {r['instrument']} | {r['trend_n']} / {r['chop_n']} | {num(r['delta_future_er'])} | {num(r['delta_future_continuation'])} | {r['sufficient']} |")
    lines+=['','N≥10 — только прежний описательный минимум сравнения, не торговый порог/доказательство значимости. Направление различий проверено во всех достаточно заполненных cells, не только в удобном инструменте. Пул ALL зависит от состава эпох и не устраняет смешение.','',
        '## Переключения и своевременность','',
        '| Инструмент | Сессий | Переключений | На100 сессий | A→B→A | Возвраты через1–2 сессии | UNKNOWN |','|---|---:|---:|---:|---:|---:|---:|']
    for r in data['switches']:
        if r['period']=='ALL':lines.append(f"| {r['instrument']} | {r['sessions']} | {r['switches']} | {num(r['switches_per100_sessions'])} | {r['A_B_A_returns']} | {r['short_A_B_A_returns']} | {r['unknown_sessions']} |")
    lines+=['','A→B→A — наблюдаемое обратное переключение, не автоматически ложный прогноз: независимой истины режима нет. UNKNOWN не пропускается и разрывает эпизод; все переключения, включая UNKNOWN, показаны. Потеря наблюдаемости в следующие5/10 сессий считается несохранением известного состояния, а не исключается из знаменателя устойчивости. Роллы/неполнота создают долгие UNKNOWN. Длительности на границах архива цензурированы.',
        '**Точная задержка распознавания истинной смены фазы: NOT AVAILABLE.** Нельзя использовать сами предсказанные серии как независимую разметку начала режима. Ниже цена за10 предшествующих и10 последующих наблюдаемых сессий относительно closeT; прошлое и будущее отделены. Это описание запаздывания, не доля пойманного латентного тренда.','',
        '| Фаза | ER прошлых10 | ER следующих10 | Абс. движение прошлых10 | Абс. движение следующих10 | Следующее движение в прежнем направлении |','|---|---:|---:|---:|---:|---:|']
    for r in data['aggregates']:
        if r['period']=='ALL' and r['instrument']=='ALL' and r['phase']!='UNKNOWN':lines.append(f"| {r['phase']} | {num(r['past10_er_mean'])} | {num(r['future_er_mean'])} | {num(r['past10_abs_pct_mean'])} | {num(r['future_abs_pct_mean'])} | {num(r['future_signed_mean'])} |")
    lines+=['','Движения указаны долями цены (0.01=1%), это не R/PnL. ATR не участвует в определении фазы. Полное распределение ATR/базовых значений/времён — CSV.','',
        '## Экономический разрез по исходной V20','',
        'Последнее состояние строго ДО входа. При смене серии или неизвестном gap после снимка — UNKNOWN. Никаких новых сделок, raw/stop-aware proxy вместо net C1 нет. История после18:00 не перерисовывает утреннее состояние. Полные instrument×period×strategy×phase разрезы с mean win/loss, stop-share, net≥4/5 и долей положительных R сохранены в JSON. Ниже исследовательская сводка независимых счетов, не денежный портфель.','',
        '| Робот | Фаза | N | PF C1 | Net C1 R | Стопы | Средний выигрыш / убыток | net≥4 /≥5 | Доля положительных R от≥5 |','|---|---|---:|---:|---:|---:|---|---|---:|']
    for r in data['economics']:
        if r['period']=='ALL' and r['instrument']=='ALL':lines.append(f"| {names[r['strategy']]} | {r['phase']} | {r['n']} | {num(r['PF_C1'])} | {num(r['net_R'])} | {num(r['stop_share'])} | {num(r['mean_win'])} / {num(r['mean_loss'])} | {r['net_ge4_n']} / {r['net_ge5_n']} | {num(r['net_ge5_share_positive'])} |")
    lines+=['','| Период | Робот | TREND N / PF | CHOP N / PF |','|---|---|---|---|']
    for p in PERIODS:
        for m in MODES:
            a,b=[next((r for r in data['economics'] if r['period']==p and r['instrument']=='ALL' and r['strategy']==m and r['phase']==state),None) for state in ('TREND','CHOP')]
            lines.append(f"| {p} | {names[m]} | {a['n'] if a else 0} / {num(a['PF_C1']) if a else 'Н/Д'} | {b['n'] if b else 0} / {num(b['PF_C1']) if b else 'Н/Д'} |")
    lines+=['','Числа ранних лет условны относительно tick/OPEN/цензурирования; это не доказанный PF реального исполнения. Большой UNKNOWN и редкость Inside ограничивают интерпретацию. Историческая связь не равна причинному эффекту фазы и не обосновывает новый preset.','',
        '## Ответ A / B / C / D','', '| Вопрос | Вердикт |','|---|---|']
    for k,v in data['verdicts'].items():lines.append(f'| {k} | {v} |')
    lines+=['','B: устойчивость оценивается по1–2/5/10 сессиям, но отдельной валидации латентного режима нет. C: независимая дата начала движения неизвестна, показатели прошлого нельзя называть предупреждением до движения. D: ограниченный условный модельный разрез не доказывает устойчивой пригодности для всех трёх роботов.',
        '**Оснований переходить к подбору альтернативных пресетов пока недостаточно.** Технический PASS не подтверждает A–D. Новые варианты/окна не подбираются; исследование закрывается. Рабочая карточка не изменена. Далее только основной roadmap8/24: frozen parity04.2 → H1 execution04.3. Draft PR567 без Merge/LIVE; H1, IntradayLab, FINAM, N4, риск1.5%, frozen и ограничения счетов не менялись.','',
        '## Воспроизведение и проверки','',
        '```bash','python -m V20_TradingSystem_M15.v20_runtime.market_phase_probe --archive /external/Si+Mix.zip --old-archive /external/2018-2022.zip --market /external/forever --work /external/phase-cache','python -m unittest V20_TradingSystem_M15.v20_runtime.tests.test_market_phase_probe -v','```','',
        'Статус фактически выполненных проверок: '+json.dumps(data['tests'],ensure_ascii=False),
        'Тяжёлые тесты неизменённых стратегий и749/4431 quote-outcomes повторно не запускались: SKIP с переиспользованием SHA/результатов. CSV содержит причинные поля и явно именованные future_* только для оценки; JSON — протокол, SHA, все агрегаты и ограничения.']
    (OUT/'MARKET_PHASE_CAUSAL_PROBE_RU.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path);ap.add_argument('--old-archive',type=Path)
    ap.add_argument('--market',type=Path,required=True);ap.add_argument('--work',type=Path,required=True);a=ap.parse_args()
    build(a.archive,a.old_archive,a.market,a.work)
