"""Descriptive comparison of historical market snapshots; no outcome fitting.

Both epochs call the existing evaluate_market_card unchanged. Daily overlapping
20-session windows remain dependent. LOCKED_V1 selection/gaps are data authority,
not a strategy replay. Raw candles never leave the external source into the repo.
"""
from __future__ import annotations
from bisect import bisect_left
from collections import Counter, defaultdict
from copy import deepcopy
import csv
from datetime import date, datetime, timedelta
import hashlib
import io
import json
from math import isfinite
from pathlib import Path
from statistics import mean, median
import zipfile
from .market_suitability import CompletedSession, M15Bar, METRIC_SCHEMA, STEP, evaluate_market_card
from .market_reference_descriptive import SOURCE_SHA256
from .market_ranges import percentile
from .market_verdict import STRATEGY_METRICS

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT/'V20-03'
DEFAULT_EPOCHS = ROOT/'V20-04/MARKET_EPOCH_PROFILES.json'
ZIP_SHA = 'df1aaf4d23757d18689dfdf61d6fc1ec77f0b26ae7d8af1193322d460707888a'
SCHEMA = 'v20.market_epochs.descriptive.v1'
EPOCHS = ('2018-2022','2023-2024')
FAMILY = {'Si':'USD','MIX':'INDEX','CNY':'CNY',
          'USDRUBF':'USD','IMOEXF':'INDEX','CNYRUBF':'CNY','GLDRUBF':'GOLD'}
FIVE = ('atr14_pct_close','directional_efficiency','continuation_rate',
        'pressure_direction_alignment','range_compression_ratio')
EXTRA = ('inside_session_share','inside_release_continuation_rate','return_inside_rate')
LABELS = dict(zip(FIVE+EXTRA,('ATR/Close','Направленность','Продолжение пробоев',
    'Давление и движение','Сжатие диапазона','Строгие Inside','Продолжение Inside','Возврат за уровень')))
MIN_SNAPSHOTS = 20  # informational sufficiency only, not a confidence bound or market gate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def day_key(ts):
    return (ts-timedelta(hours=9)).date()


def unknown_gap(prev, now):
    """Literal LOCKED_V1 observability rule; verified against all 409 stored gaps."""
    if now-prev<=STEP or prev.date()!=now.date() or day_key(prev)!=day_key(now):
        return False
    return (prev.strftime('%H:%M'),now.strftime('%H:%M')) not in {
        ('18:30','19:00'),('18:30','19:15'),('13:45','14:15')}


def read_bars(stream, *, years=None):
    bars=[]
    for row in csv.DictReader(stream,delimiter=';'):
        stamp=row['Datetime']
        # Filter before prices/volumes are parsed, including locked 2025.
        if stamp.startswith('2025-') or (years is not None and int(stamp[:4]) not in years):
            continue
        ts=datetime.fromisoformat(stamp)
        if ts.tzinfo is not None or ts.minute%15 or ts.second or ts.microsecond:
            raise ValueError('SOURCE_TIME_INVALID')
        values=[float(row[k]) for k in ('Open','High','Low','Close','Volume')]
        o,h,l,c,v=values
        if not all(isfinite(x) for x in values) or min(o,h,l,c)<=0 or v<0 or h<max(o,l,c) or l>min(o,h,c):
            raise ValueError('SOURCE_OHLCV_INVALID')
        if bars and ts<=bars[-1].open_time:
            raise ValueError('SOURCE_ORDER_OR_DUPLICATE')
        bars.append(M15Bar(ts,*values))
    return bars


def series(bars):
    days=defaultdict(list)
    positions={}
    gaps=[]
    segment=0
    warmup=0
    prev=None
    for bar in bars:
        if prev is not None and unknown_gap(prev,bar.open_time):
            gaps.append((prev,bar.open_time))
            segment+=1
            warmup=0
        warmup+=1
        positions[bar.open_time]=(segment,warmup)
        days[day_key(bar.open_time)]  # retain observed sessions with zero daytime bars
        if 600<=bar.open_time.hour*60+bar.open_time.minute<1080:
            days[day_key(bar.open_time)].append(bar)
        prev=bar.open_time
    sessions={}
    for day,bs in days.items():
        start=datetime.combine(day,datetime.min.time()).replace(hour=10)
        expected=tuple(start+STEP*k for k in range(32))
        sessions[day]=CompletedSession(day,expected,tuple(bs),start+timedelta(hours=8))
    return dict(bars=bars,sessions=sessions,positions=positions,gaps=gaps)


def card_values(card):
    values=dict(card['strategies']['INSIDE_DAY_RELEASE']['diagnostics'])
    if not values:
        return None
    values['return_inside_rate']=card['metrics']['breakouts']['return_inside_rate']
    return {k:values[k] for k in FIVE+EXTRA}


def snapshots(sources, decisions, *, epoch, family):
    """One snapshot per family/observed day. Never stitch contracts or skip a day."""
    records={}
    counts=Counter()
    history=[]
    previous=None
    for day,contract in decisions:
        in_epoch=(2018<=day.year<=2022 if epoch==EPOCHS[0] else day.year in (2023,2024))
        if in_epoch:
            counts['observed_sessions']+=1
        if contract!=previous:
            history=[]
        previous=contract
        if not contract:
            if in_epoch:
                counts['NO_LOCKED_SELECTION']+=1
            continue
        source=sources[contract]
        session=source['sessions'].get(day)
        if session is None:
            start=datetime.combine(day,datetime.min.time()).replace(hour=10)
            session=CompletedSession(day,tuple(start+STEP*k for k in range(32)),(),start+timedelta(hours=8))
        history.append(session)
        if not in_epoch:
            continue
        counts['selected_sessions']+=1
        counts['incomplete_sessions']+=len(session.bars)!=32
        if len(history)<20:
            counts['INITIAL_OR_ROLL_WARMUP']+=1
            continue
        window=history[-20:]
        if any(tuple(b.open_time for b in s.bars)!=s.expected_opens for s in window):
            counts['INCOMPLETE_WINDOW']+=1
            continue
        first=source['positions'][window[0].bars[0].open_time]
        last=source['positions'][window[-1].bars[-1].open_time]
        if first[0]!=last[0]:
            counts['UNKNOWN_GAP_WINDOW']+=1
            continue
        if last[1]<200:
            counts['SOURCE_WARMUP_200']+=1
            continue
        card=evaluate_market_card(contract.upper(),window,as_of=session.closed_at,
                                  expected_session_days=[s.day for s in window])
        values=card_values(card)
        if values is None:
            raise ValueError('SHARED_CARD_REJECTED_COMPLETE_WINDOW')
        records[day]=dict(epoch=epoch,family=family,contract=contract,
                          cutoff=session.closed_at.isoformat(),values=values)
        counts['snapshots']+=1
    return records,dict(counts)


def load_old(archive):
    if sha(archive)!=ZIP_SHA:
        raise ValueError('ORIGINAL_2018_2022_ZIP_SHA_MISMATCH')
    metadata=json.loads((STAGE/'results/RUN_METADATA.json').read_text())
    if sha(STAGE/'ROLL_POLICY_LOCKED_V1.md')!=metadata['policy_sha256']:
        raise ValueError('LOCKED_V1_POLICY_CHANGED')
    maps=list(csv.DictReader((STAGE/'results/CONTRACT_MAP.csv').open()))
    by_file={r['file']:r for r in maps}
    sources={}
    audit={}
    gaps=[]
    with zipfile.ZipFile(archive) as zipped:
        names=[name for name in zipped.namelist() if name.endswith('.csv')]
        if len(names)!=43 or set(names)!=set(by_file):
            raise ValueError('ARCHIVE_COMPOSITION_MISMATCH')
        for name in sorted(names):
            data=zipped.read(name)
            info=by_file[name]
            digest=hashlib.sha256(data).hexdigest()
            if digest!=info['sha256'] or digest!=metadata['source_hashes']['history_2018_2022_original/'+name]:
                raise ValueError('ARCHIVE_MEMBER_SHA_MISMATCH')
            bars=read_bars(io.StringIO(data.decode('utf-8-sig')))
            if len(bars)!=int(info['rows']):
                raise ValueError('ORIGINAL_ROW_COUNT_CHANGED')
            for b in bars:
                tick=(1 if info['family']=='Si' else 25 if info['family']=='MIX' else
                      .01 if b.open_time<datetime(2022,10,6,19) else .001)
                if b.volume<=0 or any(abs(v/tick-round(v/tick))>=1e-6 for v in (b.open,b.high,b.low,b.close)):
                    raise ValueError('ORIGINAL_VOLUME_OR_TICK_GRID_INVALID')
            source=series(bars)
            contract=info['contract']
            sources[contract]=source
            for a,b in source['gaps']:
                gaps.append((info['family'],contract,str(a),str(b)))
            grouped=defaultdict(list)
            for bar in bars:
                grouped[day_key(bar.open_time)].append(bar)
            for day,bs in grouped.items():
                audit[(contract,str(day))]=(len(bs),str(bs[0].open_time),str(bs[-1].open_time),len(source['sessions'][day].bars))
    stored=list(csv.DictReader((STAGE/'results/SESSION_AUDIT.csv').open()))
    if len(audit)!=len(stored) or any(audit[(r['contract'],r['day'])]!=(int(r['rows']),r['first_bar'],r['last_bar'],int(r['day_rows'])) for r in stored):
        raise ValueError('PUBLISHED_SESSION_AUDIT_MISMATCH')
    accepted=list(csv.DictReader((STAGE/'results/INVALID_INTERVALS.csv').open()))
    if sorted(gaps)!=sorted((r['family'],r['contract'],r['previous_bar'],r['next_bar']) for r in accepted):
        raise ValueError('PUBLISHED_V1_GAPS_MISMATCH')
    if sum(len(s['bars']) for s in sources.values())!=149028 or len(gaps)!=409:
        raise ValueError('ORIGINAL_TOTALS_MISMATCH')
    decisions=defaultdict(list)
    for r in csv.DictReader((STAGE/'results/ROLL_DECISIONS.csv').open()):
        c=r['chosen_contract']
        if c:
            info=next(m for m in maps if m['contract']==c)
            if (datetime.fromisoformat(r['proof_known_after'])>datetime.fromisoformat(r['decision_time'])
                    or r['day']>=info['entry_cutoff']):
                raise ValueError('NON_CAUSAL_LOCKED_ROLL')
        decisions[FAMILY[r['family']]].append((date.fromisoformat(r['day']),c))
    return sources,decisions,dict(archive_files=43,archive_rows=149028,accepted_session_rows=len(stored),accepted_unknown_gaps=409)


def distribution(records):
    result={}
    for metric in FIVE+EXTRA:
        values=[r['values'][metric] for r in records if r['values'][metric] is not None]
        result[metric]=dict(n=len(values),median=median(values) if values else None,
            p25=percentile(values,.25) if values else None,p75=percentile(values,.75) if values else None)
    return result


def overlap(old,new):
    if old['n']<MIN_SNAPSHOTS or new['n']<MIN_SNAPSHOTS:
        return dict(status='СРАВНЕНИЕ ОГРАНИЧЕНО',intersection_over_union=None)
    a,b,c,d=old['p25'],old['p75'],new['p25'],new['p75']
    width=max(b,d)-min(a,c)
    if a==b or c==d:
        return dict(status='ВЫРОЖДЕННЫЙ IQR',intersection_over_union=None)
    intersection=max(0,min(b,d)-max(a,c))
    return dict(status='IQR ПЕРЕКРЫВАЮТСЯ' if min(b,d)>=max(a,c) else 'IQR НЕ ПЕРЕСЕКАЮТСЯ',
                intersection_over_union=intersection/width)


def feature_similarity(value,old,new):
    if (not isinstance(value,(float,int)) or isinstance(value,bool) or not isfinite(value)
            or old['n']<MIN_SNAPSHOTS or new['n']<MIN_SNAPSHOTS):
        return 'НЕДОСТАТОЧНО СОПОСТАВИМЫХ ДАННЫХ'
    if old['p25']==old['p75'] or new['p25']==new['p75']:
        return 'НЕРАЗЛИЧИМО / ВЫРОЖДЕННЫЙ IQR'
    inside_old=old['p25']<=value<=old['p75']
    inside_new=new['p25']<=value<=new['p75']
    if inside_old and inside_new:
        return 'СМЕШАННЫЙ / ПЕРЕКРЫТИЕ'
    if inside_old:
        return 'БЛИЖЕ К 2018–2022'
    if inside_new:
        return 'БЛИЖЕ К 2023–2024'
    return 'НЕРАЗЛИЧИМО / ВНЕ ОБОИХ IQR'


def annotate_epochs(card, profile):
    """Separate HISTORICAL SIMILARITY; never alter suitability/evidence/trading."""
    result=deepcopy(card)
    if profile.get('schema')!=SCHEMA or profile.get('metric_schema')!=METRIC_SCHEMA:
        raise ValueError('EPOCH_PROFILE_SCHEMA_INVALID')
    if datetime.fromisoformat(card['as_of_msk'])<datetime.fromisoformat(profile['available_from_msk']):
        result['historical_similarity']={'status':'ПРОФИЛЬ ЕЩЁ НЕ ДОСТУПЕН'}
        return result
    aliases={k.upper():v for k,v in FAMILY.items()}
    aliases.update(profile['old_contract_families'])
    family=aliases.get(card['symbol'])
    comparison={'family':family,'limitation':'Квартальные и вечные контракты — экономические прокси; календарь условный.',
                'strategies':{},'metrics':{}}
    old=profile['epochs'][EPOCHS[0]].get(family)
    new=profile['epochs'][EPOCHS[1]].get(family)
    if family is None or old is None or new is None:
        reason='ПЕРЕНОС НЕ ПРОВЕРЕН' if family is None else 'НЕДОСТАТОЧНО СОПОСТАВИМЫХ ДАННЫХ'
        comparison.update(status=reason)
        for strategy in STRATEGY_METRICS:
            comparison['strategies'][strategy]=dict(status=reason,reasons=[
                'Нет сопоставимого профиля двух эпох для этого инструмента.'])
        result['historical_similarity']=comparison
        return result
    values=card_values(card)
    for metric in FIVE+EXTRA:
        value=values.get(metric) if values else None
        comparison['metrics'][metric]=dict(label=LABELS[metric],value=value,
            old=old['metrics'][metric],new=new['metrics'][metric],
            status=feature_similarity(value,old['metrics'][metric],new['metrics'][metric]))
    for strategy, fields in STRATEGY_METRICS.items():
        facts=[comparison['metrics'][m] for m in sorted(fields)]
        directions={f['status'] for f in facts if f['status'].startswith('БЛИЖЕ')}
        status=(next(iter(directions)) if len(directions)==1 else 'СМЕШАННЫЙ / НЕРАЗЛИЧИМО')
        if any(f['status']=='НЕДОСТАТОЧНО СОПОСТАВИМЫХ ДАННЫХ' for f in facts):
            status='НЕДОСТАТОЧНО СОПОСТАВИМЫХ ДАННЫХ'
        comparison['strategies'][strategy]=dict(status=status,
            reasons=[f"{f['label']}: {f['status']}" for f in facts])
    comparison['status']='ТОЛЬКО ОПИСАНИЕ СХОДСТВА'
    result['historical_similarity']=comparison
    return result


def signal_brief(records,calendars):
    """Published raw outcomes and prior snapshots, never an accepted-trade replay."""
    expected=json.loads((ROOT/'V20-04/MARKET_CARD_RESEARCH_V2.json').read_text())['source_sha256']
    path=STAGE/'comparison/QUOTE_PATH_DIAGNOSTICS.csv'
    if sha(path)!=expected['V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv']:
        raise ValueError('PUBLISHED_RAW_SOURCE_CHANGED')
    total=Counter()
    observed=defaultdict(list)
    joined=defaultdict(list)
    locked=Counter()
    with path.open() as stream:
        for r in csv.DictReader(stream):
            if r['record_type']!='RAW_SIGNAL':
                continue
            year=int(r['signal_bar_dt'][:4])
            if year not in (2018,2019,2020,2021,2022,2023,2024):
                continue  # no numeric feature/outcome processing of 2025 or 2026
            epoch=EPOCHS[0] if year<=2022 else EPOCHS[1]
            key=(epoch,r['strategy'])
            total[key]+=1
            if r['horizon_exit_dt'].startswith('2025-'):
                locked[key]+=1
                continue
            if r['horizon_status']!='OBSERVED_V1':
                continue
            item=dict(horizon_R=float(r['horizon_R']),stop_touch=r['horizon_stop_touch']=='True')
            observed[key].append(item)
            family=FAMILY[r['instrument']]
            signal=datetime.fromisoformat(r['signal_bar_dt'])
            days=calendars[(epoch,family)]
            day=day_key(signal)
            i=bisect_left(days,day)
            if not i or i>=len(days) or days[i]!=day:
                continue
            before=records[(epoch,family)].get(days[i-1])
            if before is None or before['contract']!=r['contract']:
                continue
            if datetime.fromisoformat(before['cutoff']).date()>=day:
                raise ValueError('SIGNAL_FEATURE_NOT_BEFORE_DAY')
            joined[key].append(dict(item,values=before['values']))
    output=[]
    for (epoch,strategy),n in sorted(total.items()):
        obs=observed[(epoch,strategy)]
        matches=joined[(epoch,strategy)]
        output.append(dict(epoch=epoch,strategy=strategy,raw=n,observed_horizons=len(obs),
            locked_target_excluded=locked[(epoch,strategy)],
            mean_horizon_R=mean(r['horizon_R'] for r in obs) if obs else None,
            stop_touch_share=mean(r['stop_touch'] for r in obs) if obs else None,
            matched_prior_snapshots=len(matches),
            matched_mean_horizon_R=mean(r['horizon_R'] for r in matches) if matches else None,
            prior_feature_medians={m:median(v) if (v:=[r['values'][m] for r in matches if r['values'][m] is not None]) else None
                                   for m in FIVE+EXTRA}))
    return output


def build(archive,data_dir):
    old,decisions,receipt=load_old(archive)
    all_records={}
    calendars={}
    coverage={}
    for family,plan in decisions.items():
        key=(EPOCHS[0],family)
        all_records[key],coverage[key]=snapshots(old,plan,epoch=key[0],family=family)
        calendars[key]=[d for d,_ in plan]
    for symbol,digest in SOURCE_SHA256.items():
        path=data_dir/symbol/(symbol+'_M15.csv')
        if sha(path)!=digest:
            raise ValueError('MODERN_SOURCE_SHA_MISMATCH')
        with path.open(encoding='utf-8-sig') as stream:
            source=series(read_bars(stream,years={2023,2024}))
        family=FAMILY[symbol]
        days=sorted(source['sessions'])
        key=(EPOCHS[1],family)
        all_records[key],coverage[key]=snapshots({symbol:source},[(d,symbol) for d in days],epoch=key[0],family=family)
        calendars[key]=days
    epochs={e:{} for e in EPOCHS}
    for (epoch,family),records in all_records.items():
        epochs[epoch][family]=dict(coverage=coverage[(epoch,family)],metrics=distribution(list(records.values())))
    pooled={e:distribution([r for (ep,_),group in all_records.items() if ep==e for r in group.values()]) for e in EPOCHS}
    overlaps={family:{m:overlap(epochs[EPOCHS[0]][family]['metrics'][m],epochs[EPOCHS[1]][family]['metrics'][m])
                       for m in FIVE} for family in sorted(set(epochs[EPOCHS[0]])&set(epochs[EPOCHS[1]]))}
    return dict(schema=SCHEMA,metric_schema=METRIC_SCHEMA,
        status='DESCRIPTIVE_EPOCH_SIMILARITY_NOT_SUITABILITY',available_from_msk='2025-01-01T00:00:00',
        epoch_years={'2018-2022':[2018,2019,2020,2021,2022],'2023-2024':[2023,2024]},
        locked_2025_excluded=True,minimum_snapshots=MIN_SNAPSHOTS,
        calendar='CONDITIONAL_LOCKED_V1_OBSERVED_DATES',overlapping_daily_windows=True,
        old_contract_families={c.upper():FAMILY[c.split('-')[0]] for c in old},
        source_sha256={'2018-2022.zip':ZIP_SHA,**SOURCE_SHA256,
                       'LOCKED_V1':sha(STAGE/'ROLL_POLICY_LOCKED_V1.md'),
                       'ROLL_DECISIONS':sha(STAGE/'results/ROLL_DECISIONS.csv'),
                       'market_suitability.py':sha(Path(__file__).with_name('market_suitability.py'))},
        archive_verification=receipt,epochs=epochs,pooled_available_composition=pooled,
        iqr_overlap=overlaps,raw_signal_reference=signal_brief(all_records,calendars),
        no_outcome_fitting=True,affects_signals_or_risk=False,independent_holdout=False)


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv)
    report=build(args.archive,args.data_dir)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(report['status'])
    for epoch,families in report['epochs'].items():
        for family,data in families.items():
            print(epoch,family,data['coverage'])


if __name__=='__main__':
    main()
