"""2023 P&L attribution and M30 readiness, separate from frozen PR #449.

No gap restoration. Pre-exit extrema use complete bars strictly before exit;
terminal-bar favorable/adverse extrema are never presumed to precede a fill.
"""
import csv
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
from statistics import median

from independent_corrective_review import (aggregate, coverage, exact_lines, git,
    independent_tick, intervals, encoded, sha, write_csv)
from run_m5_baseline import inputs
from m5_conditional_v2 import FIVE, ZERO, allowed, window_at

LAB = Path(__file__).resolve().parents[1]
BASE = 'ca8922082b0988837f7553e5ff39d6a2c3dece09'
POLICY = 'd000c5e8aad3e0bbae32f55bbf205483b48e9408'
DEST = LAB / 'results/stage2_architecture_diagnostics'
DECIMALS = {'entry','stop','take','entry_cap','exit','gross_price_pnl','c1_entry',
    'c1_exit','c1_total','net_model_c1','net_R','initial_risk_price_units',
    'holding_minutes_bar_starts','signal_close','atr_shifted','vwap_approx',
    'range_high_shifted','range_low_shifted','cap'}


def read_table(path):
    with path.open(newline='') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in DECIMALS & r.keys():
            r[k] = D(r[k]) if r[k] != '' else None
        for k in ('direction_sign','entry_filled_model_units','residual_model_units'):
            if k in r:
                r[k] = int(r[k]) if r[k] else None
    return rows


class Indicators:
    """Window-local Wilder ATR/DI/ADX14 and SMA-seeded EMA50; no carry.

    Seed smoothed TR/DM with 14 intervals; ADX with 14 valid DX values.
    All updates include only the just-delivered completed observation. EMA is
    reserved diagnostic context unless a separately frozen architecture uses it.
    """
    def __init__(self, period=14, ema_period=50):
        self.n, self.en = period, ema_period
        self.reset()

    def reset(self):
        self.previous = None
        self.window = None
        self.closes, self.trs, self.plus, self.minus, self.dx = [], [], [], [], []
        self.tr = self.pdm = self.mdm = self.adx = self.ema = None

    def observe(self, b):
        w = window_at(b.timestamp)
        if not allowed(b.symbol, b.timestamp):
            self.reset()
            return {}
        if w != self.window or (self.previous and b.timestamp != self.previous.timestamp+FIVE):
            self.reset()
        self.window = w
        prev_ema = self.ema
        self.closes.append(b.close)
        if len(self.closes) == self.en:
            self.ema = sum(self.closes, ZERO)/self.en
        elif self.ema is not None:
            self.ema += D(2)/D(self.en+1)*(b.close-self.ema)
        pdi = mdi = None
        if self.previous:
            a = self.previous
            tr = max(b.high-b.low, abs(b.high-a.close), abs(b.low-a.close))
            up, down = b.high-a.high, a.low-b.low
            pdm = up if up > down and up > 0 else ZERO
            mdm = down if down > up and down > 0 else ZERO
            self.trs.append(tr); self.plus.append(pdm); self.minus.append(mdm)
            if len(self.trs) == self.n:
                self.tr = sum(self.trs, ZERO)
                self.pdm = sum(self.plus, ZERO); self.mdm = sum(self.minus, ZERO)
            elif self.tr is not None:
                self.tr = self.tr-self.tr/self.n+tr
                self.pdm = self.pdm-self.pdm/self.n+pdm
                self.mdm = self.mdm-self.mdm/self.n+mdm
            if self.tr is not None:
                pdi = 100*self.pdm/self.tr if self.tr else ZERO
                mdi = 100*self.mdm/self.tr if self.tr else ZERO
                dx = 100*abs(pdi-mdi)/(pdi+mdi) if pdi+mdi else ZERO
                self.dx.append(dx)
                if len(self.dx) == self.n:
                    self.adx = sum(self.dx, ZERO)/self.n
                elif self.adx is not None:
                    self.adx = (self.adx*(self.n-1)+dx)/self.n
        self.previous = b
        return {'atr14': self.tr/self.n if self.tr is not None else None,
            'adx14':self.adx,'plus_di14':pdi,'minus_di14':mdi,'ema50':self.ema,
            'ema50_slope':self.ema-prev_ema if self.ema is not None and prev_ema is not None else None,
            'indicator_reset':'RESEARCH_WINDOW_OR_NONCONTIGUOUS_SLOT',
            'indicator_available_at':str(b.timestamp+timedelta(minutes=10))}


def indicator_maps(data):
    out = {}
    for symbol, bars in data.items():
        ind = Indicators()
        out[symbol] = {b.timestamp: ind.observe(b) for b in bars}
    return out


def attribution(row, signal, index, context):
    r = row.copy()
    at = datetime.fromisoformat(r['entry_interval_start'])
    s_at = datetime.fromisoformat(r['signal_at'])
    d = 1 if r['direction']=='LONG' else -1
    risk = r['initial_risk_price_units']
    edge = signal['range_high_shifted'] if d == 1 else signal['range_low_shifted']
    atr = signal['atr_shifted']
    step = independent_tick(r['instrument'],at)
    r.update(context.get(s_at, {}))
    r.update(month=str(at)[:7], session_half='AM' if at.hour<14 else 'PM',
        time_bucket=f'{at.hour:02d}:{30*(at.minute//30):02d}',
        entry_drift_atr=d*(r['entry']-signal['signal_close'])/atr,
        entry_to_vwap_atr=d*(signal['vwap_approx']-r['entry'])/atr if signal['vwap_approx'] else None,
        breakout_entry_extension_atr=d*(r['entry']-edge)/atr,
        breakout_signal_extension_atr=d*(signal['signal_close']-edge)/atr,
        entry_inside_range=signal['range_low_shifted'] <= r['entry'] <= signal['range_high_shifted'],
        projected_cost_R=2*step/risk,
        projected_net_reward_risk=(d*(r['take']-r['entry'])-2*step)/(risk+2*step),
        target_pays_C1=d*(r['take']-r['entry'])>2*step,
        net_outcome='UNKNOWN' if r['net_model_c1'] is None else 'WIN' if r['net_model_c1']>0 else 'LOSS' if r['net_model_c1']<0 else 'ZERO',
        stop_within_10m=r['exit_reason']=='STOP' and r['holding_minutes_bar_starts'] is not None and r['holding_minutes_bar_starts']<=10,
        excursion_basis='Complete bars strictly before exit; terminal extrema excluded. Lower bounds, not exact intrabar excursion.',
        mfe_pre_exit_lower_bound_R=None, mae_pre_exit_lower_bound_R=None,
        mfe_observable_before_exit_lower_bound_R=None, profit_to_loss_confirmed=None,
        excursions_null_reason=None)
    adx, pdi, mdi = r.get('adx14'), r.get('plus_di14'), r.get('minus_di14')
    r['adx_regime'] = 'NOT_READY' if adx is None else 'TREND_25_PLUS' if adx>=25 else 'SUB_25'
    r['di_aligned'] = None if pdi is None else (pdi>mdi if d==1 else mdi>pdi)
    slope = r.get('ema50_slope')
    r['ema_aligned'] = None if slope is None else d*slope>0
    r['breakout_entry_class'] = 'INSIDE_RANGE' if r['entry_inside_range'] else 'EXTENDED_GT_1_ATR' if r['breakout_entry_extension_atr']>1 else 'PERSISTENT_LE_1_ATR'
    r['cost_class'] = 'TARGET_CANNOT_PAY_C1' if not r['target_pays_C1'] else 'NET_RR_LT_1' if r['projected_net_reward_risk']<1 else 'NET_RR_GE_1'
    for level in ('0.5','1','2','3'):
        r[f'reached_{level}R_before_exit_confirmed'] = None
        r[f'reached_{level}R_terminal_ambiguous'] = None
    if r['net_model_c1'] is None:
        r['excursions_null_reason'] = 'UNKNOWN_OUTCOME_FROM_FROZEN_LEDGER_NOT_REEXAMINED'
        return r
    end = datetime.fromisoformat(r['exit_interval_start'])
    times=[]; t=at
    while t<end:
        if t not in index:
            r['excursions_null_reason']='NONCONTIGUOUS_KNOWN_PATH'
            return r
        times.append(t); t+=FIVE
    path=[index[t] for t in times]
    mfe=max([ZERO]+[d*((b.high if d==1 else b.low)-r['entry'])/risk for b in path])
    mae=max([ZERO]+[-d*((b.low if d==1 else b.high)-r['entry'])/risk for b in path])
    observable=[b for b in path if b.timestamp+timedelta(minutes=10)<=end]
    obs=max([ZERO]+[d*((b.high if d==1 else b.low)-r['entry'])/risk for b in observable])
    terminal=index[end]
    terminal_mfe=d*((terminal.high if d==1 else terminal.low)-r['entry'])/risk
    r.update(mfe_pre_exit_lower_bound_R=mfe,mae_pre_exit_lower_bound_R=mae,
        mfe_observable_before_exit_lower_bound_R=obs,
        profit_to_loss_confirmed=mfe>=D('.5') and r['net_model_c1']<0,
        positive_gross_to_negative_net=r['gross_price_pnl']>0 and r['net_model_c1']<0)
    for level in ('0.5','1','2','3'):
        hit=mfe>=D(level)
        # Market Open exit: remaining terminal candle is after exit. For Stop/TP
        # its ordering is unobserved. Never classify possible extrema as achieved.
        ambiguous=not hit and r['exit_reason'] in ('STOP','TAKE','TRAIL_STOP','BREAKEVEN_STOP') and terminal_mfe>=D(level)
        r[f'reached_{level}R_before_exit_confirmed']=hit
        r[f'reached_{level}R_terminal_ambiguous']=ambiguous
    return r


def diagnostics(rows):
    result=[]
    for run in sorted({r['run'] for r in rows}):
        for direction in ('ALL','LONG','SHORT'):
            base=[r for r in rows if r['run']==run and (direction=='ALL' or r['direction']==direction)]
            for dimension in ('ALL','exit_reason','time_bucket','session_half','net_outcome','adx_regime','di_aligned','ema_aligned','breakout_entry_class','cost_class'):
                keys=['ALL'] if dimension=='ALL' else sorted({str(r.get(dimension)) for r in base})
                for key in keys:
                    sub=base if dimension=='ALL' else [r for r in base if str(r.get(dimension))==key]
                    summary=aggregate(sub,'PARTIAL_COVERAGE')
                    known=[r for r in sub if r['mfe_pre_exit_lower_bound_R'] is not None]
                    wins=[r for r in sub if r['net_model_c1'] is not None and r['net_model_c1']>0]
                    losses=[r for r in sub if r['net_model_c1'] is not None and r['net_model_c1']<0]
                    rec={'run':run,'direction':direction,'dimension':dimension,'bucket':key}|summary
                    for field in ('mfe_pre_exit_lower_bound_R','mae_pre_exit_lower_bound_R','net_R','projected_cost_R','entry_drift_atr'):
                        vals=[r[field] for r in sub if r.get(field) is not None]
                        rec['median_'+field]=median(vals) if vals else None
                        rec['mean_'+field]=sum(vals,ZERO)/len(vals) if vals else None
                    rec.update(excursion_denominator=len(known),profit_to_loss_confirmed=sum(r['profit_to_loss_confirmed'] is True for r in sub),
                        stop_within_10m=sum(r['stop_within_10m'] for r in sub),
                        winners_median_hold=median([r['holding_minutes_bar_starts'] for r in wins]) if wins else None,
                        losers_median_hold=median([r['holding_minutes_bar_starts'] for r in losses]) if losses else None)
                    for level in ('0.5','1','2','3'):
                        count=sum(r[f'reached_{level}R_before_exit_confirmed'] is True for r in known)
                        rec[f'confirmed_{level}R_count']=count
                        rec[f'confirmed_{level}R_share']=D(count)/len(known) if known else None
                        rec[f'terminal_ambiguous_{level}R_count']=sum(r[f'reached_{level}R_terminal_ambiguous'] is True for r in known)
                    result.append(rec)
    return result


def mtf_audit(root,data):
    """Native M30 integrity only. No strategy backtest, no gap reconstruction.

    Source has no delivery/finalization stamps. Agreement cannot establish them.
    Skip the exact previously published 2022 prefix without numeric parsing;
    read only the exact 2023 budget and never probe the next (2024) line.
    """
    historic=json.loads((LAB/'reports/STAGE1_2_SESSION_MTF_RESULTS.json').read_text())
    result={}
    for symbol,bars in data.items():
        spec=historic['coverage'][symbol]['M30']
        path=f'forever/{symbol}/{symbol}_M30.csv'
        assert git(root,'ls-files','--stage','--',path).split()[1]==spec['frozen_blob_id']
        before=(root/path).stat()
        parents={}; digest=hashlib.sha256(); skipped_bytes=read_bytes=0
        skip=spec['year_rows'].get('2022',0); count=spec['year_rows']['2023']
        with (root/path).open('rb',buffering=0) as raw:
            for i,line in enumerate(exact_lines(raw,1+skip+count)):
                if i==0:
                    assert line.decode('utf-8-sig').strip()=='Ticker;Datetime;Open;High;Low;Close;Volume'
                    digest.update(line); read_bytes+=len(line); continue
                if i<=skip:
                    # Price fields never parsed/used. Exact skip count is from the
                    # historical audit, so there is no next-year read-ahead.
                    assert line.split(b';',2)[1].startswith(b'2022-')
                    skipped_bytes+=len(line); continue
                row=next(csv.reader([line.decode()],delimiter=';'))
                at=datetime.fromisoformat(row[1])
                assert at.year==2023 and row[0]==symbol
                o,h,l,c,v=map(D,row[2:]); assert l<=min(o,c)<=max(o,c)<=h and v>=0
                assert at not in parents
                parents[at]=(o,h,l,c,v); digest.update(line); read_bytes+=len(line)
        after=(root/path).stat()
        assert (before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
        index={b.timestamp:b for b in bars}; counters=Counter()
        for at,p in parents.items():
            w=window_at(at)
            if not w or at+timedelta(minutes=30)>w[1]:
                counters['outside_or_crosses_research_window']+=1; continue
            children=[index.get(at+i*FIVE) for i in range(6)]
            if any(b is None for b in children):
                counters['incomplete_6_child_bucket']+=1; continue
            o,h,l,c,v=children[0].open,max(b.high for b in children),min(b.low for b in children),children[-1].close,sum((b.volume for b in children),ZERO)
            counters['complete_exact' if (o,h,l,c,v)==p else 'complete_mismatch']+=1
        # Complete M5 buckets without a native parent are composition failures;
        # higher-TF data is never used to impute the M5 children.
        for at in index:
            if at.minute%30 or not window_at(at) or at+timedelta(minutes=30)>window_at(at)[1]: continue
            if all(at+i*FIVE in index for i in range(6)) and at not in parents:
                counters['complete_M5_bucket_without_parent']+=1
        result[symbol]={'native_M30_2023_rows':len(parents),'source_blob':spec['frozen_blob_id'],
            'skipped_2022_rows_not_parsed':skip,'skipped_2022_bytes':skipped_bytes,
            'prefix_2023_plus_header_bytes':read_bytes,'prefix_2023_plus_header_sha256':digest.hexdigest(),
            'bytes_2024_plus_read':0,'bytes_2025_plus_read':0,'composition_counts':dict(counters),
            'native_delivery_finalization':'UNRESOLVED_NO_STAMPS_OR_APPROVED_M30_DELAY_CONTRACT',
            'causal_requirement':'start+30m closed AND known delivery/finalization <= M5 decision; whole bucket inside same approved window; never cross lunch/gap/day',
            'status':'MTF_BLOCKED','strategy_contexts_admitted':0,
            'derived_M30':'Not substituted silently for native M30; a distinct conditional hypothesis is untested'}
    return result


def run(root):
    m=json.loads((LAB/'config/stage2_m5_conditional_v2.json').read_text())
    data,provenance=inputs(root,m); contexts=indicator_maps(data)
    frozen=LAB/'results/stage2_m5_conditional_v2'
    ledger=read_table(frozen/'trade_ledger.csv'); signals={s['signal_id']:s for s in read_table(frozen/'signals.csv')}
    assert len(ledger)==2140 and sum(r['net_model_c1'] is None for r in ledger)==82
    rows=[attribution(r,signals[r['signal_id']],{b.timestamp:b for b in data[r['instrument']]},contexts[r['instrument']]) for r in ledger]
    DEST.mkdir(exist_ok=True,parents=True)
    write_csv(DEST/'trade_attribution.csv',rows)
    write_csv(DEST/'pnl_segments.csv',diagnostics(rows))
    (DEST/'mtf_readiness.json').write_text(encoded(mtf_audit(root,data)))
    summary={'base':BASE,'methodology_head':POLICY,'source':m['source_ref'],'inputs':provenance,
        'frozen_ledger_sha256':sha(frozen/'trade_ledger.csv'),'frozen_signals_sha256':sha(frozen/'signals.csv'),
        'corrective_metrics_sha256':sha(LAB/'results/stage2_m5_v2_corrective_review/metrics.csv'),
        'entries':2140,'closed':2058,'unknown_outcomes_unchanged':82,
        'scope':'All available 2023; no 2024/WF or 2025+/TRUE OOS bytes read',
        'mfe_mae_policy':'Known complete pre-exit candles: confirmed lower bounds; terminal extrema ambiguous; all unknown trade excursions null. No invented intrabar sequence.',
        'implementation_sha256':sha(Path(__file__))}
    (DEST/'provenance.json').write_text(encoded(summary))
    print(encoded([r for r in diagnostics(rows) if r['dimension']=='ALL' and r['direction']=='ALL']))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('--data-root',type=Path,required=True)
    run(p.parse_args().data_root)
