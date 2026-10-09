#!/usr/bin/env python3
"""Prepare then reproduce exactly 8 frozen M5-only 2023 conditional runs.

PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/run_m5_baseline.py prepare --data-root .../market-pattern-data
PYTHONDONTWRITEBYTECODE=1 python IntradayLab/tools/run_m5_baseline.py run --data-root .../market-pattern-data

Only the fixed destination IntradayLab/results/stage2_m5 is writable. No raw
market rows are copied. Source index IDs and physical 2023 prefixes are checked.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess

from audit_session_mtf import HEADER
from session_mtf import Bar, bounded_lines, _validate
from m5_baseline import END, Replay, allowed, metrics, tick, windows, FIVE, ZERO

LAB = Path(__file__).resolve().parents[1]
CONFIG = LAB/'config/stage2_m5_baseline_v1.json'
DEST = LAB/'results/stage2_m5'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_value(v):
    if isinstance(v, Decimal):
        return str(v)  # preserve exact accounting, no binary float roundoff
    raise TypeError(type(v).__name__)


def encoded(obj):
    return json.dumps(obj, default=json_value, ensure_ascii=False,sort_keys=True,indent=2)+'\n'


def write_text(path, content):
    # One explicit output authority, including symlink containment.
    if not path.resolve().is_relative_to(DEST.resolve()) or not DEST.resolve().is_relative_to(LAB.resolve()):
        raise ValueError('Output outside IntradayLab/results/stage2_m5')
    path.write_text(content)


def load_manifest():
    m = json.loads(CONFIG.read_text())
    expected = (CONFIG.with_suffix('.sha256')).read_text().split()[0]
    if sha(CONFIG) != expected:
        raise ValueError('Frozen manifest was modified')
    if m['calendar']['exclusive_end'] != str(END) or len(m['run_matrix']) != 8:
        raise ValueError('Unexpected research scope')
    return m,expected


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()


def verify_source(root,m):
    root = root.resolve()
    if git(root,'rev-parse','HEAD') != m['source_ref'] or git(root,'status','--porcelain=v1','--untracked-files=all'):
        raise ValueError('Source must match frozen clean read-only revision')
    for spec in m['inputs'].values():
        line = git(root,'ls-files','--stage','--',spec['path'])
        if len(line.split()) != 4 or line.split()[1] != spec['blob'] or line.split()[2] != '0':
            raise ValueError('Source M5 index differs')
    return root


def read_2023(path,symbol,spec):
    """Header + published 2023 row count ONLY, no next-row/EOF probe."""
    count = spec['rows_2023']
    if type(count) is not int or count < 1:
        raise ValueError('Invalid 2023 physical line budget')
    first = datetime.fromisoformat(spec['first'])
    if first.year != 2023:
        raise ValueError('Budget crosses protected years')
    before = path.stat()
    digest,nbytes,bars = hashlib.sha256(),0,[]
    with path.open('rb',buffering=0) as raw:
        if not isinstance(raw,io.FileIO):
            raise ValueError('Raw FileIO only')
        for i,line in enumerate(bounded_lines(raw,count+1)):
            digest.update(line)
            nbytes += len(line)
            row = next(csv.reader([line.decode('utf-8-sig' if i == 0 else 'utf-8')],delimiter=';'))
            if i == 0:
                if row != HEADER:
                    raise ValueError('Header mismatch')
                continue
            if len(row) != 7 or row[0] != symbol:
                raise ValueError('Wrong ticker/schema')
            at = datetime.fromisoformat(row[1])
            if at.year != 2023 or at.tzinfo is not None:
                raise ValueError('Protected year: reject BEFORE numeric parsing')
            values = tuple(Decimal(v) for v in row[2:])
            if any(v % tick(symbol,at) != 0 for v in values[:4]):
                raise ValueError('Historical price grid mismatch')
            bars.append(Bar(at,*values,symbol=symbol))
    _validate(bars,5)
    after = path.stat()
    attrs = ('st_size','st_mtime_ns','st_ctime_ns','st_ino','st_mode')
    if any(getattr(before,k) != getattr(after,k) for k in attrs):
        raise ValueError('Read-only source metadata changed')
    if len(bars) != count or bars[0].timestamp != first or bars[-1].timestamp >= END:
        raise ValueError('2023 prefix coverage mismatch')
    return bars,{'rows':count,'first':str(bars[0].timestamp),'last':str(bars[-1].timestamp),
                 'prefix_bytes_read':nbytes,'prefix_sha256':digest.hexdigest(),
                 'frozen_blob':spec['blob'],'bytes_2024_plus_read':0,'bytes_2025_plus_read':0}


def inputs(root,m):
    root = verify_source(root,m)
    bars,provenance = {},{}
    for symbol,spec in m['inputs'].items():
        bars[symbol],provenance[symbol] = read_2023(root/spec['path'],symbol,spec)
    verify_source(root,m)
    return bars,provenance


def csv_text(rows,fields=None):
    out = io.StringIO(newline='')
    columns = fields or (list(rows[0]) if rows else [])
    writer = csv.DictWriter(out,fieldnames=columns,lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def coverage(bars):
    symbol=bars[0].symbol
    observed={b.timestamp for b in bars if allowed(symbol,b.timestamp)}
    dates={b.timestamp.date() for b in bars}
    raw=Counter(str(b.timestamp)[:7] for b in bars)
    result={}
    for month in range(1,13):
        key=f'2023-{month:02d}'
        start=datetime(2023,month,1)
        end=datetime(2023,month+1,1) if month<12 else END
        expected=set()
        day=max(start,bars[0].timestamp.replace(hour=0,minute=0))
        while day<end:
            for a,z in windows(day.date()):
                t=a
                while t+FIVE<=z:
                    if allowed(symbol,t):
                        expected.add(t)
                    t+=FIVE
            day+=timedelta(days=1)
        obs={t for t in observed if str(t)[:7]==key}
        missing=expected-obs
        expected_dates={t.date() for t in expected}
        result[key]={'raw_2023_bars':raw[key],'research_bars':len(obs),'expected_research_slots':len(expected),
                     'missing_slots':len(missing),'research_dates':len({t.date() for t in obs}),
                     'missing_entire_dates':sorted(str(d) for d in expected_dates-dates),
                     'coverage_status':'NO_COVERAGE' if not obs else 'PARTIAL_COVERAGE' if missing else 'COVERED'}
    return result


def group_metrics(replay,bars):
    base={'run':f'{replay.strategy}_{replay.symbol}','strategy':replay.strategy,'instrument':replay.symbol}
    cov=coverage(bars)
    year=metrics(replay.ledger)
    year['observed_close_mtm_drawdown_price_units']=replay.mtm_drawdown if not year['unresolved'] else None
    year['known_cost_mtm_drawdown_diagnostic']=replay.mtm_drawdown
    result=[base|{'group':'YEAR','period':'2023'}|year]
    for direction in ('LONG','SHORT'):
        rows=[r for r in replay.ledger if r['direction']==direction]
        result.append(base|{'group':'DIRECTION','period':direction}|metrics(rows))
    for key,c in cov.items():
        rows=[r for r in replay.ledger if (r['exit_interval_start'] or r['entry_interval_start'])[:7]==key]
        m=metrics(rows)
        # Outstanding uncertain exposure in any intersected month invalidates
        # that month, even if the eventual model exit occurred another month.
        uncertainty=[r for r in replay.ledger if r['status']=='UNRESOLVED' and
                     r['entry_interval_start'][:7]<=key<= (r['exit_interval_start'] or '2023-12')[:7]]
        if uncertainty:
            m.update(metric_status='INCOMPLETE / CLOSED-ONLY DIAGNOSTIC',
                     net_model_c1=None,unresolved=len(uncertainty))
        if c['coverage_status']=='NO_COVERAGE':
            m.update(metric_status='NO_COVERAGE',net_model_c1=None,closed_only_net_c1=None)
        m['observed_close_mtm_drawdown_price_units']=replay.month_drawdowns.get(key) if not uncertainty and c['coverage_status']!='NO_COVERAGE' else None
        m['month_end_known_mtm_after_c1']=replay.month_marks.get(key,{}).get('known_mtm_after_c1_price_units') if c['coverage_status']!='NO_COVERAGE' else None
        m['month_end_residual_model_units']=replay.month_marks.get(key,{}).get('residual_model_units',0)
        m['month_outcome']=('NO_COVERAGE' if c['coverage_status']=='NO_COVERAGE' else
                            'UNRESOLVED' if uncertainty else 'ZERO_TRADES' if not rows else
                            'POSITIVE' if m['net_model_c1']>0 else 'NEGATIVE' if m['net_model_c1']<0 else 'ZERO_NET')
        result.append(base|{'group':'MONTH','period':key}|m|
                      {k:v for k,v in c.items() if k!='missing_entire_dates'})
    return result,cov


def implementation_hashes():
    paths=[LAB/'tools/m5_baseline.py',LAB/'tools/run_m5_baseline.py',LAB/'tools/session_mtf.py',
           LAB/'tools/audit_session_mtf.py',LAB/'tests/test_m5_baseline.py']
    return {str(p.relative_to(LAB)):sha(p) for p in paths}


def prepare(root):
    m,msha=load_manifest()
    _,provenance=inputs(root,m)
    DEST.mkdir(parents=True,exist_ok=True)
    payload={'manifest_sha256':msha,'source_ref':m['source_ref'],'inputs':provenance,
             'state':'INPUT_PROVENANCE_SAVED_BEFORE_FIRST_REAL_STRATEGY_CALCULATION',
             'implementation_sha256':implementation_hashes()}
    path=DEST/'input_provenance.json'
    if path.exists():
        existing=json.loads(path.read_text())
        if any(existing.get(k)!=payload[k] for k in ('manifest_sha256','source_ref','inputs','implementation_sha256')):
            raise ValueError('Provenance frozen: inspect implementation/input, do not overwrite')
        print(encoded(existing))
    else:
        write_text(path,encoded(payload))
        print(encoded(payload))


def run(root):
    m,msha=load_manifest()
    prepared=json.loads((DEST/'input_provenance.json').read_text())
    if prepared['manifest_sha256']!=msha or prepared['implementation_sha256']!=implementation_hashes():
        raise ValueError('Prepare must freeze these exact rules/implementation before any real results')
    data,provenance=inputs(root,m)
    if provenance!=prepared['inputs']:
        raise ValueError('2023 input prefix changed')
    signals,events,ledger,grouped,runs=[],[],[],[],[]
    for item in m['run_matrix']:
        symbol,strategy=item['instrument'],item['strategy']
        replay=Replay(symbol,strategy,m['parameters']).run(data[symbol])
        groups,cov=group_metrics(replay,data[symbol])
        signals.extend(replay.signals); events.extend(replay.events); ledger.extend(replay.ledger); grouped.extend(groups)
        counts=Counter(x['status'] for x in replay.signals)
        outcome=Counter(g['month_outcome'] for g in groups if g['group']=='MONTH')
        runs.append({'run':f'{strategy}_{symbol}','status':'EXECUTED_2023_CONDITIONAL_MODEL',
                     'summary':{k:v for k,v in groups[0].items() if k not in ('run','strategy','instrument','group','period')},'signals':len(replay.signals),'signal_status_counts':dict(counts),
                     'execution_counts':replay.counts,'coverage':cov,'monthly_outcomes':dict(outcome),
                     'month_end_model_marks':replay.month_marks})
    output={'verdict':'STAGE2_M5_BASELINE_IMPLEMENTED_PENDING_AUDIT','manifest_sha256':msha,
            'source_ref':m['source_ref'],'inputs':provenance,'runs':runs,
            'scope':'8 fixed M5-only 2023 runs; 2024 WF reserved unread; 2025+ TRUE OOS locked unread',
            'unit':'normalized price exposure; no actual equity/GO quantity sizing',
            'implementation_sha256':prepared['implementation_sha256']}
    write_text(DEST/'results.json',encoded(output))
    write_text(DEST/'signals.csv',csv_text(signals))
    write_text(DEST/'execution_events.csv',csv_text(events))
    write_text(DEST/'trade_ledger.csv',csv_text(ledger))
    fields=list(dict.fromkeys(k for r in grouped for k in r))
    write_text(DEST/'metrics.csv',csv_text(grouped,fields))
    sums={p.name:sha(p) for p in sorted(DEST.iterdir()) if p.name!='SHA256SUMS' and p.is_file()}
    write_text(DEST/'SHA256SUMS',''.join(f'{v}  {k}\n' for k,v in sums.items()))
    for r in runs:
        print(encoded({k:r[k] for k in ('run','status','summary','execution_counts')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('prepare','run'))
    parser.add_argument('--data-root',type=Path,required=True,help='read-only repository root (not forever/)')
    args=parser.parse_args()
    (prepare if args.command=='prepare' else run)(args.data_root)
