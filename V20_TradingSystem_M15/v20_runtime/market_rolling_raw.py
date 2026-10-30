"""V20-only READONLY rolling RAW_SIGNAL diagnostics, owner task 4fef4eb2.

20 completed paths versus the previous disjoint 20. Availability is horizon
Open time, never signal time. No replay, PnL, portfolio admission or trade gate.
2025/2026 are explicitly permitted by V20_TradingSystem_M15/AGENTS.md only.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
import json
from math import isfinite, isclose
from pathlib import Path
from statistics import mean, median
import zipfile

from .market_epochs import ROOT, STAGE, ZIP_SHA, sha, unknown_gap
from .market_ranges import percentile
from .market_reference_descriptive import SOURCE_SHA256
from .market_suitability import M15Bar, STRATEGIES, STEP, SYMBOL_PATTERN, _atr_wilder

RAW_PATH = STAGE/'comparison/QUOTE_PATH_DIAGNOSTICS.csv'
RAW_SHA = '1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f'
DEFAULT_PROFILE = ROOT/'V20-04/ROLLING_RAW_CARD_RESULTS.json'
SCHEMA = 'v20.rolling_raw.readonly.v1'
WINDOW = 20
# Fixed operational freshness limits, NOT fitted strategy/filter parameters.
MAX_SPAN_DAYS = 365
MAX_AGE_DAYS = 90
NAMES = dict(zip(STRATEGIES, ('Shallow','OBV','Inside')))


def stamp(value):
    ts=datetime.fromisoformat(value)
    if ts.tzinfo is not None:
        raise ValueError('MOSCOW_NAIVE_TIMESTAMP_REQUIRED')
    return ts


def load_paths(path=RAW_PATH, *, expected_sha=RAW_SHA, as_of=None):
    if expected_sha is not None and sha(path)!=expected_sha:
        raise ValueError('RAW_PUBLICATION_SHA_MISMATCH')
    paths=[]
    coverage=Counter()
    seen=set()
    for row in csv.DictReader(path.open()):
        if row['record_type']!='RAW_SIGNAL':
            continue
        instrument=row['instrument']
        strategy=row['strategy']
        if strategy not in STRATEGIES:
            raise ValueError('UNKNOWN_FROZEN_STRATEGY')
        signal=stamp(row['signal_bar_dt'])
        if as_of is not None and signal>as_of:
            continue
        if signal.year not in range(2018,2027):
            raise ValueError('SOURCE_YEAR_OUTSIDE_V20_2018_2026')
        key=(strategy,instrument,signal)  # one selected contract per instrument/signal
        if key in seen:
            raise ValueError('DUPLICATE_RAW_SIGNAL')
        seen.add(key)
        base=f'{strategy}/{instrument}/{signal.year}'
        coverage[base+'/raw']+=1
        if row['horizon_status']!='OBSERVED_V1':
            coverage[base+'/'+row['horizon_status']]+=1
            continue
        entry=stamp(row['entry_dt'])
        available=stamp(row['horizon_exit_dt'])
        if as_of is not None and available>as_of:
            continue  # do not even parse a not-yet-available numeric outcome
        value=float(row['horizon_R'])
        if (not isfinite(value) or entry-signal!=STEP or available<=entry
                or available.year>2026 or row['horizon_stop_touch'] not in ('True','False')):
            raise ValueError('OBSERVED_RAW_PATH_INVALID')
        paths.append(dict(strategy=strategy,instrument=instrument,contract=row['contract'],
            signal=signal,entry=entry,available=available,raw_R=value,
            stop_touch=row['horizon_stop_touch']=='True'))
        coverage[base+'/observed']+=1
    paths.sort(key=lambda r:(r['available'],r['signal'],r['strategy'],r['instrument'],r['contract']))
    return paths,dict(coverage)


def distribution(values):
    return dict(n=len(values),mean=mean(values) if values else None,median=median(values) if values else None,
        minimum=min(values) if values else None,p25=percentile(values,.25) if values else None,
        p75=percentile(values,.75) if values else None,maximum=max(values) if values else None)


def window_summary(paths):
    if not paths:
        return dict(n=0,mean=None,first_signal=None,last_signal=None,completed_at=None,
                    span_days=None,stop_touch_share=None,without_1=None,without_2=None,contracts=[])
    values=[r['raw_R'] for r in paths]
    # Descriptive leave-largest-|R| sensitivity; it never changes the mean/trend.
    trimmed=sorted(values,key=abs,reverse=True)
    return dict(n=len(paths),mean=mean(values),
        first_signal=min(r['signal'] for r in paths).isoformat(),
        last_signal=max(r['signal'] for r in paths).isoformat(),
        completed_at=max(r['available'] for r in paths).isoformat(),
        span_days=(max(r['available'] for r in paths)-min(r['signal'] for r in paths)).days,
        stop_touch_share=mean(r['stop_touch'] for r in paths),
        without_1=mean(trimmed[1:]) if len(paths)>1 else None,
        without_2=mean(trimmed[2:]) if len(paths)>2 else None,
        contracts=sorted({r['contract'] for r in paths}))


def rolling_at(paths, *, strategy, instrument, as_of):
    """No outcome value is inspected until available <= as_of. Atomic close times."""
    if as_of.tzinfo is not None:
        raise ValueError('MOSCOW_NAIVE_TIMESTAMP_REQUIRED')
    eligible=sorted((r for r in paths if r['strategy']==strategy and r['instrument']==instrument
                     and r['available']<=as_of),key=lambda r:(r['available'],r['signal'],r['contract']))
    current=window_summary(eligible[-WINDOW:])
    previous=window_summary(eligible[-2*WINDOW:-WINDOW])
    if previous['n']<WINDOW:
        previous['mean']=None
    delta=(current['mean']-previous['mean'] if current['n']==previous['n']==WINDOW else None)
    reasons=[]
    if current['n']<WINDOW:
        reasons.append('FEWER_THAN_20_COMPLETED_PATHS')
    if current['span_days'] is not None and current['span_days']>MAX_SPAN_DAYS:
        reasons.append('CURRENT_WINDOW_OVER_365_DAYS')
    age=(as_of-stamp(current['completed_at'])).days if current['completed_at'] else None
    if age is not None and age>MAX_AGE_DAYS:
        reasons.append('LAST_HORIZON_OVER_90_DAYS_OLD')
    if previous['span_days'] is not None and previous['span_days']>MAX_SPAN_DAYS:
        reasons.append('PREVIOUS_WINDOW_OVER_365_DAYS')
    if delta is None:
        reasons.append('FEWER_THAN_40_COMPLETED_PATHS_FOR_TREND')
    trend=('НЕДОСТАТОЧНО ДАННЫХ' if reasons else
           'НАБЛЮДАЕТСЯ СНИЖЕНИЕ' if delta<0 else
           'НАБЛЮДАЕТСЯ УЛУЧШЕНИЕ' if delta>0 else 'БЕЗ ИЗМЕНЕНИЙ')
    return dict(strategy=strategy,instrument=instrument,as_of=as_of.isoformat(),
        total_completed=len(eligible),current=current,previous=previous,delta_raw_R=delta,
        age_days=age,trend=trend,reasons=reasons,warning=trend=='НАБЛЮДАЕТСЯ СНИЖЕНИЕ')


def timeline(paths):
    """One state after ALL paths becoming observable at T; no partial tie batches."""
    groups=defaultdict(list)
    for r in paths:
        groups[(r['strategy'],r['instrument'])].append(r)
    output=[]
    archive_end=max((r['available'] for r in paths),default=None)
    for (strategy,instrument),group in sorted(groups.items()):
        closes=sorted({r['available'] for r in group})
        times=set(closes)
        for i,available in enumerate(closes):
            expires=available+timedelta(days=MAX_AGE_DAYS+1)
            next_time=closes[i+1] if i+1<len(closes) else archive_end
            if next_time is not None and expires<next_time:
                times.add(expires)
        for available in sorted(times):
            state=rolling_at(group,strategy=strategy,instrument=instrument,as_of=available)
            state['event_kind']='COMPLETED_PATHS' if available in closes else 'STALE_CLOCK'
            output.append(state)
    return output


def warning_episodes(states,paths):
    """Evaluate subsequent 20 ONLY retrospectively, never inside rolling_at.

    A temporary warning is followed by mean(next 20) >= the PRE-warning mean.
    Further decline is mean(next 20) < the current mean. Other cases are mixed.
    Neither measure is a trade win rate or a forward-validated alert accuracy.
    """
    groups=defaultdict(list)
    for state in states:
        groups[(state['strategy'],state['instrument'])].append(state)
    episodes=[]
    for (strategy,instrument),series in sorted(groups.items()):
        active=None
        for state in series:
            if state['warning'] and active is None:
                active=dict(strategy=strategy,instrument=instrument,start=state['as_of'],
                    current_raw_R=state['current']['mean'],previous_raw_R=state['previous']['mean'],
                    delta_raw_R=state['delta_raw_R'],end=None,return_positive_at=None)
                episodes.append(active)
            elif not state['warning'] and active is not None:
                active['end']=state['as_of']
                active['end_reason']=state['trend']
                active=None
        group=[r for r in paths if r['strategy']==strategy and r['instrument']==instrument]
        for event in (e for e in episodes if e['strategy']==strategy and e['instrument']==instrument):
            after=sorted((r for r in group if r['available']>stamp(event['start'])),
                         key=lambda r:(r['available'],r['signal'],r['contract']))[:WINDOW]
            positive=next((s for s in series if s['as_of']>event['start'] and not s['reasons']
                and s['current']['mean']>0 and s['delta_raw_R']>=0),None)
            event['return_positive_at']=positive['as_of'] if positive else None
            event['next_n']=len(after)
            event['evaluation_available_at']=max(r['available'] for r in after).isoformat() if len(after)==WINDOW else None
            event['next20_mean']=mean(r['raw_R'] for r in after) if len(after)==WINDOW else None
            event['result']=('UNRESOLVED' if len(after)<WINDOW else
                'TEMPORARY_FULL_REBOUND' if event['next20_mean']>=event['previous_raw_R'] else
                'FURTHER_DECLINE' if event['next20_mean']<event['current_raw_R'] else 'MIXED_PARTIAL_REBOUND')
    return episodes


def yearly_table(paths,coverage,states):
    rows=[]
    for key,nraw in sorted((key[:-4],n) for key,n in coverage.items() if key.endswith('/raw')):
        strategy,instrument,year=key.split('/')
        q=[r for r in paths if r['strategy']==strategy and r['instrument']==instrument and r['signal'].year==int(year)]
        windows=[s['current']['mean'] for s in states if s['strategy']==strategy and s['instrument']==instrument
                 and stamp(s['as_of']).year==int(year) and s['current']['n']==WINDOW
                 and s['event_kind']=='COMPLETED_PATHS']
        rows.append(dict(strategy=strategy,instrument=instrument,signal_year=int(year),raw=nraw,
            observed=len(q),excluded=nraw-len(q),**window_summary(q),rolling20=distribution(windows)))
    return rows


def reference_levels(paths,states):
    """Published weak/late PERIOD means are tested as references, never fitted.

    No independently supported minimum/recommendation is inferred from overlapping
    distributions. The actual ranges/counts and crossovers are exposed instead.
    """
    refs={}
    for strategy in STRATEGIES:
        old=[r['raw_R'] for r in paths if r['strategy']==strategy and r['signal'].year<=2022]
        new=[r['raw_R'] for r in paths if r['strategy']==strategy and r['signal'].year>=2023]
        low,high=mean(old),mean(new)
        windows={period:[s['current']['mean'] for s in states if s['strategy']==strategy
            and s['current']['n']==WINDOW and s['event_kind']=='COMPLETED_PATHS'
            and (stamp(s['as_of']).year<=2022)==(period=='2018-2022')]
            for period in ('2018-2022','2023-2026')}
        refs[strategy]=dict(minimum_reference_R=low,recommended_reference_R=high,
            old_observed=len(old),late_observed=len(new),validated_minimum_R=None,validated_recommended_R=None,
            status='DESCRIPTIVE_PERIOD_MEANS_NOT_VALIDATED_LIMITS',
            rolling20={period:dict(**distribution(values),
                below_minimum_reference=sum(v<low for v in values),
                at_or_above_recommended_reference=sum(v>=high for v in values)) for period,values in windows.items()})
    return refs


def verify_sources(archive,data_dir):
    """Byte provenance reuse, no replay or new signal extraction."""
    if sha(archive)!=ZIP_SHA:
        raise ValueError('OLD_ZIP_SHA_MISMATCH')
    if sha(RAW_PATH)!=RAW_SHA:
        raise ValueError('RAW_PUBLICATION_SHA_MISMATCH')
    observed=[r for r in csv.DictReader(RAW_PATH.open())
              if r['record_type']=='RAW_SIGNAL' and r['horizon_status']=='OBSERVED_V1']
    needed=defaultdict(set)
    opens=defaultdict(dict)
    for r in observed:
        needed[r['contract']].update((r['entry_dt'],r['horizon_exit_dt']))
    mapping=list(csv.DictReader((STAGE/'results/CONTRACT_MAP.csv').open()))
    with zipfile.ZipFile(archive) as zipped:
        names={n for n in zipped.namelist() if n.endswith('.csv')}
        if names!={r['file'] for r in mapping}:
            raise ValueError('OLD_ZIP_MEMBERS_MISMATCH')
        import hashlib
        for r in mapping:
            data=zipped.read(r['file'])
            if hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('OLD_CSV_SHA_MISMATCH')
            import io
            for bar in csv.DictReader(io.StringIO(data.decode('utf-8-sig')),delimiter=';'):
                if bar['Datetime'] in needed[r['contract']]:
                    opens[r['contract']][bar['Datetime']]=float(bar['Open'])
    sources={'2018-2022.zip':ZIP_SHA,'QUOTE_PATH_DIAGNOSTICS.csv':sha(RAW_PATH)}
    ends={}
    for symbol,digest in SOURCE_SHA256.items():
        path=data_dir/symbol/(symbol+'_M15.csv')
        if sha(path)!=digest:
            raise ValueError('N4_QUOTES_SHA_MISMATCH')
        sources[symbol]=digest
        # Dates only for coverage. 2026 end is the actual file end, never Dec 31.
        with path.open(encoding='utf-8-sig') as stream:
            for r in csv.DictReader(stream,delimiter=';'):
                ends[symbol]=r['Datetime']
                if r['Datetime'] in needed[symbol]:
                    opens[symbol][r['Datetime']]=float(r['Open'])
    checks=Counter()
    for r in observed:
        entry=opens[r['contract']][r['entry_dt']]
        close=opens[r['contract']][r['horizon_exit_dt']]
        risk=float(r['risk'])
        if (risk<=0 or not isclose(entry,float(r['entry']),abs_tol=1e-7)
                or not isclose(abs(entry-float(r['stop'])),risk,abs_tol=1e-7)
                or not isclose(int(r['side'])*(close-entry)/risk,float(r['horizon_R']),rel_tol=1e-9,abs_tol=1e-8)):
            raise ValueError('PUBLISHED_RAW_HORIZON_SOURCE_MISMATCH')
        checks[r['signal_bar_dt'][:4]]+=1
    return dict(source_sha256=sources,quote_last_open_msk=ends,old_files=len(mapping),
                old_rows=sum(int(r['rows']) for r in mapping),horizon_source_checks_by_signal_year=dict(checks),
                horizon_source_checks=sum(checks.values()))


def atr_reference(data_dir, symbol, as_of):
    """Existing Wilder formula, completed M15 only, current V1 segment, reference."""
    if data_dir is None or symbol not in SOURCE_SHA256:
        return dict(atr14_pct_close=None,reason='VERIFIED_QUOTES_NOT_PROVIDED',data_through=None)
    path=data_dir/symbol/(symbol+'_M15.csv')
    if sha(path)!=SOURCE_SHA256[symbol]:
        raise ValueError('N4_QUOTES_SHA_MISMATCH')
    bars=[]
    previous=None
    with path.open(encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream,delimiter=';'):
            ts=stamp(row['Datetime'])
            if ts+STEP>as_of:
                break  # no future numeric OHLCV ingestion
            if previous is not None and unknown_gap(previous,ts):
                bars=[]
            bars.append(M15Bar(ts,*[float(row[k]) for k in ('Open','High','Low','Close','Volume')]))
            previous=ts
    atr=_atr_wilder(bars) if len(bars)>=14 else None
    return dict(atr14_pct_close=atr/bars[-1].close if atr is not None else None,
        data_through=(bars[-1].open_time+STEP).isoformat() if bars else None,
        bars_in_v1_segment=len(bars),reason='REFERENCE_ONLY_NOT_A_VERDICT')


def instrument_card(paths,symbol,as_of, *, profile=None,atr=None):
    if SYMBOL_PATTERN.fullmatch(symbol.upper()) is None:
        raise ValueError('INVALID_MARKET_ANALYSIS_SYMBOL')
    instrument=next((r['instrument'] for r in paths if r['instrument'].upper()==symbol.upper()),symbol.upper())
    reference_ready=bool(profile and as_of>=stamp(profile['reference_available_from_msk']))
    rows=[]
    for strategy in STRATEGIES:
        state=rolling_at(paths,strategy=strategy,instrument=instrument,as_of=as_of)
        ref=profile['reference_levels'][strategy] if reference_ready else {}
        state.update(minimum_reference_R=ref.get('minimum_reference_R'),
            recommended_reference_R=ref.get('recommended_reference_R'),
            validated_minimum_R=None,validated_recommended_R=None)
        rows.append(state)
    last=max((r['available'] for r in paths if r['instrument']==instrument and r['available']<=as_of),default=None)
    return dict(schema=SCHEMA,symbol=instrument,as_of_msk=as_of.isoformat(),
        raw_data_through=last.isoformat() if last else None,rows=rows,atr_reference=atr or {},
        references_available_as_of=reference_ready,
        warning_rule='CURRENT20_MEAN_LT_PREVIOUS_DISJOINT20_MEAN',
        affects_signals_or_risk=False,live_authorized=False,independent_validation=False,
        trading_instrument_authority='OPERATOR_ONLY',transfer_to_unseen_symbol='NOT_VERIFIED')


def build(archive,data_dir):
    provenance=verify_sources(archive,data_dir)
    paths,coverage=load_paths()
    states=timeline(paths)
    episodes=warning_episodes(states,paths)
    yearly=yearly_table(paths,coverage,states)
    summaries=[]
    for strategy,instrument in sorted({(r['strategy'],r['instrument']) for r in paths}):
        group=[r for r in states if r['strategy']==strategy and r['instrument']==instrument]
        observed=[r for r in paths if r['strategy']==strategy and r['instrument']==instrument]
        first=min(r['signal'] for r in observed)
        collect={}
        for n in (20,40):
            state=next((s for s in group if s['total_completed']>=n),None)
            collect[f'first_{n}_at']=state['as_of'] if state else None
            collect[f'days_to_{n}']=(stamp(state['as_of'])-first).days if state else None
        alerts=[e for e in episodes if e['strategy']==strategy and e['instrument']==instrument]
        favorable=[e for e in alerts if next((r['mean'] for r in yearly if r['strategy']==strategy
                    and r['instrument']==instrument and r['signal_year']==stamp(e['start']).year),0)>0]
        first2019=next((s for s in group if s['as_of'].startswith('2019-') and s['warning']),None)
        summaries.append(dict(strategy=strategy,instrument=instrument,first_signal=first.isoformat(),**collect,
            first_warning_2019=first2019['as_of'] if first2019 else None,
            warning_episodes=len(alerts),episode_results=dict(Counter(e['result'] for e in alerts)),
            favorable_year_warning_episodes=len(favorable),
            favorable_year_results=dict(Counter(e['result'] for e in favorable))))
    # Compact column arrays preserve every availability event without copying quotes.
    columns=['strategy','instrument','as_of','total_completed','raw_R','previous_raw_R','delta_raw_R',
             'span_days','first_signal','last_signal','trend','event_kind','completed_at',
             'previous_first_signal','previous_last_signal','previous_completed_at']
    matrix=[[s['strategy'],s['instrument'],s['as_of'],s['total_completed'],s['current']['mean'],
        s['previous']['mean'],s['delta_raw_R'],s['current']['span_days'],s['current']['first_signal'],
        s['current']['last_signal'],s['trend'],s['event_kind'],s['current']['completed_at'],
        s['previous']['first_signal'],s['previous']['last_signal'],s['previous']['completed_at']] for s in states]
    return dict(schema=SCHEMA,reference_available_from_msk='2026-10-22T00:00:00',
        years=list(range(2018,2027)),scope='V20_ONLY_OWNER_EXCEPTION_2025_2026',
        window=WINDOW,max_span_days=MAX_SPAN_DAYS,max_age_days=MAX_AGE_DAYS,
        source=provenance,coverage=coverage,observed_paths=len(paths),raw_signals=sum(
            n for k,n in coverage.items() if k.endswith('/raw')),
        yearly=yearly,reference_levels=reference_levels(paths,states),collection_and_alert_summary=summaries,
        timeline_columns=columns,timeline=matrix,warning_episodes=episodes,
        affects_signals_or_risk=False,independent_validation=False,
        method='ONE_PREDECLARED_20_VS_20_DELTA_SIGN_NO_PF_FIT')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    report=build(args.archive,args.data_dir)
    args.output.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
    print(f"RAW {report['raw_signals']}; OBSERVED {report['observed_paths']}; EVENTS {len(report['timeline'])}")


if __name__=='__main__':
    main()
