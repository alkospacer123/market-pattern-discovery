#!/usr/bin/env python3
"""Aggregate frozen result journals only. No strategy imports, candles, replay or search."""
import csv, gzip, io, json, subprocess, hashlib
from collections import defaultdict, Counter
from decimal import Decimal, localcontext
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = 'f7a1ff5f12779a2b3dfbe5e4dbfe8f265096d3d8'
ORB = '9c65d03aae117c6d88bbb4e6186f6a4fbb6b73ec'
BB = '82ec9ffe61e18a43cd7510e398f6913b25f045e1'
CMD = '728d23e25d4bd41fdb6d50e134d1f099c206c6b2'
OLD = 'e38e018c1c7be3863178cd30237cbc5748216de7'
NA = 'NOT_AVAILABLE'
SYMS = ['USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF']
FAMILIES = {
 'A': ('Equal High / Equal Low', 'touch count; exact/tolerant extremes; consecutive vs bounded window; zone width; structural Stop buffer and risk bounds; entry displacement; Take 2R–10R; hold; causal trailing if separately justified'),
 'B': ('High/Low Cluster', 'construction length 4–10; boundary touch count; zone width in dated ticks/ATR; structural Stop buffer and risk bounds; entry displacement; Take 2R–10R; hold; causal trailing if justified'),
 'C': ('Return / Retest / Rejection', 'distinct approaches; whole-bar retreat depth/time; local-extreme lookback; zone width/expiry; rejection Close; structural Stop/risk bounds; entry displacement; Take 2R–10R; hold; causal trailing if justified'),
 'LEVEL_REJECTION': ('Level Rejection', 'prior-level lookback; breach/reentry confirmation; zone tolerance; dedup/expiry; structural Stop buffer/distance; Take 2R–10R; holding/time exit; displacement; applicable causal filters'),
 'R16': ('Compression Breakout', 'compression window/ATR width; breakout confirmation; Stop boundary/buffer/distance; Take 2R–10R; hold; entry extension; applicable causal trend filter/trailing'),
 'R17': ('ORB Breakout / Retest', 'opening-range duration; distinct retest count/tolerance/expiry; confirmation; structural Stop/distance; entry extension; Take 2R–10R; hold; applicable causal trend context/trailing'),
 'R18': ('ORB False Break Fade', 'opening-range duration; sweep/reclaim depth and confirmation; reclaim window; ATR/context gate only if justified; structural Stop buffer/distance; entry displacement; Take 2R–10R; hold; applicable trailing'),
 'SWING_PULLBACK': ('Swing Pullback M5/M15', 'causal swing/context formation; correction depth/bars; continuation confirmation; structural correction Stop/distance; Take 2R–10R; hold; entry displacement; applicable context/trailing'),
 'TREND_PULLBACK': ('Trend Pullback M15/H1', 'causal H1 trend; M15 correction and continuation confirmation; Stop on observed correction/signal extrema; risk distance; Take 2R–10R; hold; displacement; applicable causal trailing'),
 'VWAP_MR': ('VWAP Mean Reversion', 'causal VWAP anchor/reset; ATR band/period and reentry; payable target/adverse cap; structural/volatility Stop; hold/no-progress; context filter if justified; fixed Take 2R–10R only as separately declared alternative to VWAP target'),
 'MOMENTUM': ('Momentum Breakout', 'prior range/ATR periods; completed breakout confirmation; extension cap; structural/volatility Stop; Take 2R–10R; hold/no-progress; applicable ADX/DI/context/BE/trailing'),
 'SQUEEZE_M5': ('Volatility Squeeze M5', 'BB/KC periods/widths; episode length; release/breakout confirmation; entry extension; structural Stop/ATR distance; Take 2R–10R; hold/failed breakout; applicable M30 filter/trailing'),
 'SQUEEZE_M15': ('Volatility Squeeze M15', 'M15 BB/KC periods/widths; exact-parent episode length; release confirmation; entry extension; structural Stop/ATR distance; Take 2R–10R; hold/failed breakout; applicable H1 filter/trailing'),
 'BOLLINGER_RSI': ('Bollinger / RSI Reentry', 'first verify strict RSI comparisons; BB period/width; RSI period/threshold; reentry/confirmation bars; structural Stop/distance; Take 2R–10R or declared midpoint exit; hold; entry displacement; applicable filters/trailing'),
 'VWAP_EXHAUSTION': ('Session VWAP Exhaustion / Reclaim (R14)', 'excursion band; reclaim window/confirmation; session anchor; structural episode Stop/distance; target VWAP vs separately declared Take 2R–10R; hold; applicable efficiency filter'),
 'PRIOR_DAY_SWEEP': ('Prior-day High/Low Sweep / Reclaim (R15)', 'prior-day level; sweep depth; reclaim count/inside tolerance; structural Stop/buffer/distance; Take 2R–10R; hold; displacement; applicable filters'),
 'STRUCTURAL_FALSE_BREAK': ('Structural Complex False Break', 'causal level/zone; distinct breach/reclaim; confirmation; structural Stop/distance; Take 2R–10R; hold; displacement; applicable filters'),
 'GERCHIK_PROXY': ('Gerchik A M5 proxy', 'verify proxy/source fidelity; past level touches/tolerance; rejection confirmation; structural Stop/distance; Take 2R–10R; hold; displacement'),
 'ORB_DIRECT': ('ORB Direct Breakout', 'opening-range duration; completed breakout confirmation; opposite/midpoint Stop and distance; Take 2R–10R; hold; entry extension; applicable filters/trailing'),
}
INPUTS = {}
CATALOG = []
ROWS = []
CHECKS = []
CACHE = {}

def git(*args):
 return subprocess.check_output(['git', '-C', str(ROOT), *args])

def read(path, ref=BASE):
 # Explicitly reject market data and protected production files.
 assert path.startswith(('IntradayLab/', 'research/autonomous/', 'config/top5_v4/', 'src/market_pattern_discovery/backtest/top5_v4/'))
 assert 'TradingSystemLab' not in path and 'forever/' not in path
 key=(ref,path)
 if key not in CACHE:
  b=git('show',f'{ref}:{path}')
  CACHE[key]=b
  INPUTS[key]={'ref':ref,'path':path,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
 return CACHE[key]

def exists(path, ref=BASE):
 return subprocess.run(['git','-C',str(ROOT),'cat-file','-e',f'{ref}:{path}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0

def obj(path, ref=BASE): return json.loads(read(path,ref))
def table(path,ref=BASE):
 b=read(path,ref)
 if path.endswith('.gz'): b=gzip.decompress(b)
 return list(csv.DictReader(io.StringIO(b.decode())))
def ser(x): return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def dec(x): return Decimal(str(x))
def textnum(x): return str(x) if x is not None else NA

def empty(family,cid,typ,ref,path,config,audit,code,tf='M5',context='NONE',scenario='C1',selectors=None):
 c=obj(config,ref) if config else {}
 a=obj(audit,ref) if audit and exists(audit,ref) else {}
 status=a.get('status',a.get('audit',a.get('verdict',NA)))
 if isinstance(status,dict):status=ser(status)
 manifest_path=path.rsplit('/',1)[0]+'/manifest.json'
 manifest=obj(manifest_path,ref) if exists(manifest_path,ref) else {}
 freeze=manifest.get('pre_pnl_freeze_commit',manifest.get('pre_pnl_commit',a.get('config_freeze_commit',NA)))
 row={'record_type':typ,'family_id':family,'strategy_name':FAMILIES[family][0], 'configuration_id':cid,
 'instrument':None,'directions':'LONG|SHORT','signal_timeframe':tf,'execution_timeframe':tf,'context_timeframe':context,
 'result_commit_sha':ref,'pre_pnl_freeze_commit':freeze,'code_source':code or NA,'config_source':config or NA,
 'config_sha256':hashlib.sha256(read(config,ref)).hexdigest() if config else NA,
 'data_repository':c.get('source_repository',c.get('source_repo','alkospacer123/market-pattern-data')),
 'data_commit_sha':c.get('source_ref',NA),'data_source':NA,'input_provenance':NA,
 'baseline_source':path,'baseline_url':f'https://github.com/alkospacer123/market-pattern-discovery/blob/{ref}/{path}',
 'independent_audit_source':audit or NA,'independent_audit_status':str(status),'technical_status':'VERIFIED_FROZEN_MODEL',
 'reproducibility_status':'PINNED_CODE_CONFIG_RESULT_AND_PUBLISHED_INDEPENDENT_AUDIT',
 'period_start':'2023-01-01','period_end_exclusive':'2024-01-01','cost_model':scenario,'entry_stop_take_execution':ser({k:c[k] for k in ['parameters','rules','fixed_rules','execution','unchanged_rules','defaults'] if k in c}),
 'code_provenance':ser(c.get('execution_code_sha256',c.get('provenance',{}))),'entry_rules':NA,'stop_rules':NA,'take_rules':NA,'C1_rules':NA,'execution_constraints':NA,
 'signals':NA,'executed_entries':NA,'closed':NA,'historical_unknown':NA,'unknown_filled_paths':NA,'unknown_possible_entries':NA,'data_gap_skip':NA,'data_quality_excluded':NA,
 'unique_closed_trade_days':NA,'active_closed_months':NA,'positive_closed_months':NA,'negative_closed_months':NA,
 'gross_R':NA,'cost_R':NA,'net_R':NA,'gross_price':NA,'cost_price':NA,'net_price':NA,'PF_after_C1_R':NA,'PF_after_C1_price':NA,'expectancy_R':NA,'expectancy_price':NA,'win_rate':NA,
 'observed_closed_drawdown_R':NA,'observed_closed_drawdown_price':NA,'largest_winner_share_R':NA,'top3_winners_share_R':NA,'largest_positive_month_share_R':NA,
 'source_coverage':NA,'complete_annual_result':NA,'economic_scope':'CONDITIONAL_KNOWN_CLOSED; not complete annual account equity',
 'uncertain_outcome_share':NA,'uncertain_outcome_denominator':NA,'selection_bias_warning':NA,
 'eligibility':NA,'eligibility_reasons':NA,'sample_count_pass':False,'calendar_pass':False,
 'overlap_group':family,'independence_rule':'NEVER_SUM_ACROSS_CONFIGURATIONS_OR_COST_SCENARIOS',
 'potential_tuning_directions':FAMILIES[family][1], 'not_available_reasons':'{}','evidence_selectors':ser(selectors or {})}
 if c:
  inp=c.get('inputs',{});row['_inputs']=inp
  prov=path.rsplit('/',1)[0]+'/input_provenance.json'
  if exists(prov,ref):row['input_provenance']=prov
  row['entry_rules']=ser(c.get('execution',c.get('rules',c.get('fixed_rules',{}))))
  row['stop_rules']=ser(c.get('parameters',{}))
  row['take_rules']=ser(c.get('parameters',{}))
  row['C1_rules']='One historical dated tick per side; separate cost; exact frozen contract at linked config. CNY tick change retained.'
  row['execution_constraints']=ser(c.get('execution',c.get('rules',c.get('fixed_rules',{}))))
 CATALOG.append({'configuration_id':cid,'family_id':family,'ref':ref,'result':path,'config':config,'audit':audit,'code':code,'record_type':typ,'selectors':selectors or {}})
 return row

def metric_stats(trades):
 if not trades: return {'closed':0,'unique_closed_trade_days':0,'active_closed_months':0,'positive_closed_months':0,'negative_closed_months':0}
 vals=[]; monthly=defaultdict(lambda:Decimal(0))
 with localcontext() as ctx:
  ctx.prec=50
  for t in trades:
   net=next((t.get(k) for k in ['net_R_c1','net_R'] if t.get(k) not in ['',None]),None)
   price=next((t.get(k) for k in ['net_c1','net_model_c1','net'] if t.get(k) not in ['',None]),None)
   gross=next((t.get(k) for k in ['gross','gross_price_pnl'] if t.get(k) not in ['',None]),None)
   cost=next((t.get(k) for k in ['cost_c1','c1_total','c1'] if t.get(k) not in ['',None]),None)
   risk=next((t.get(k) for k in ['risk','initial_risk_price_units','initial_risk'] if t.get(k) not in ['',None]),None)
   if None in [net,price,gross,cost,risk]: raise ValueError(('Incomplete CLOSED',t))
   nr,pr,gr,co,ri=map(dec,[net,price,gross,cost,risk])
   # Prefer published risk-normalized amounts; deriving absent R is aggregation of saved trade amounts.
   gross_r=dec(t['gross_R']) if t.get('gross_R') else gr/ri
   cost_r=dec(t['cost_R']) if t.get('cost_R') else co/ri
   when=next((t.get(k) for k in ['resolved_at','exit_confirmed_at','exit_interval_end','exit_ack','exit_at'] if t.get(k)),None)
   entry=t.get('entry_at') or t.get('entry_interval_start')
   assert entry.startswith('2023-') and when.startswith('2023-')
   vals.append((when,t.get('signal_id',''),nr,pr,gross_r,cost_r,gr,co,entry))
   monthly[when[:7]]+=nr
  vals.sort(key=lambda x:(x[0],x[1]))
  nets=[v[2] for v in vals];prices=[v[3] for v in vals];wins=sorted((n for n in nets if n>0),reverse=True)
  def total(k):return sum((v[k] for v in vals),Decimal(0))
  def pf(ns):
   losses=-sum((n for n in ns if n<0),Decimal(0));return sum((n for n in ns if n>0),Decimal(0))/losses if losses else None
  def dd(ns):
   eq=peak=draw=Decimal(0)
   for n in ns: eq+=n;peak=max(peak,eq);draw=max(draw,peak-eq)
   return draw
  positive_months=[n for n in monthly.values() if n>Decimal('1e-20')]
  return {'closed':len(vals),'unique_closed_trade_days':len({v[8][:10] for v in vals}), 'active_closed_months':len({v[8][:7] for v in vals}),'positive_closed_months':len(positive_months),'negative_closed_months':sum(n<Decimal('-1e-20') for n in monthly.values()),
  'gross_R':total(4),'cost_R':total(5),'net_R':total(2),'gross_price':total(6),'cost_price':total(7),'net_price':total(3),'PF_after_C1_R':pf(nets),'PF_after_C1_price':pf(prices),'expectancy_R':total(2)/len(vals),'expectancy_price':total(3)/len(vals),'win_rate':Decimal(len(wins))/len(vals),'observed_closed_drawdown_R':dd(nets),'observed_closed_drawdown_price':dd(prices),
  'largest_winner_share_R':wins[0]/sum(wins) if wins else None,'top3_winners_share_R':sum(wins[:3])/sum(wins) if wins else None,'largest_positive_month_share_R':max(positive_months)/sum(positive_months) if positive_months else None}

def apply(row,sym,ledger,signals=None,published=None,coverage=None,skip=None,excluded=None,unknown_extra=0):
 r=dict(row); r['instrument']=sym
 inp=r.pop('_inputs',{});r['data_source']=ser(inp.get(sym,{})) if sym in inp else NA
 ts=[t for t in ledger if t.get('instrument')==sym]
 closed=[t for t in ts if t['status'] in ['CLOSED','MODELLED'] and not t.get('unresolved_reasons')]
 unknown=[t for t in ts if t not in closed]
 r.update({k:textnum(v) for k,v in metric_stats(closed).items()})
 r['ledger_cohort_sha256']=hashlib.sha256(ser(sorted([{k:t.get(k,'') for k in ['signal_id','status','entry_at','entry_interval_start','entry_price','entry','risk','initial_risk','initial_risk_price_units','net_R_c1','net_R','net_c1','net_model_c1','net','exit_reason']} for t in ts],key=ser)).encode()).hexdigest() if ts else NA
 r['cohort_equivalence_warning']='Exact saved ledger fingerprint; repeated comparator cohorts retain separate provenance but are not independent samples'
 r['historical_unknown']=len(unknown)+unknown_extra
 if ts and 'model_filled' in ts[0]:
  r['executed_entries']=sum(t['model_filled'].lower()=='true' for t in ts)
  r['unknown_filled_paths']=sum(t.get('model_filled','').lower()=='true' for t in unknown)
  r['unknown_possible_entries']=sum(t.get('model_filled','').lower()!='true' for t in unknown)+unknown_extra
 else:
  r['executed_entries']=len(ts);r['unknown_filled_paths']=len(unknown);r['unknown_possible_entries']=unknown_extra
 if signals is not None:r['signals']=len([s for s in signals if s.get('instrument')==sym])
 if published is not None:
  aliases={'closed':['closed','closed_accounted_trades','closed_trades'], 'signals':['signals','raw_signals','accepted_signals'], 'executed_entries':['model_fills','entry_count','entries','fills','trades'], 'historical_unknown':['unknown','unresolved'], 'data_gap_skip':['data_gap_skips','no_bar_no_model_fill'], 'data_quality_excluded':['data_quality_excluded']}
  for k,alts in aliases.items():
   for a in alts:
    if a in published and published[a] is not None:
     if k=='closed':CHECKS.append({'configuration':r['configuration_id'],'instrument':sym,'metric':k,'registry':str(r[k]),'published':str(published[a]),'match':int(r[k])==int(published[a])})
     elif k=='signals':r[k]=published[a]
     elif k in ['data_gap_skip','data_quality_excluded']:r[k]=published[a]
     break
  dist=published.get('distribution',{})
  for target,sourcekey in [('unique_closed_trade_days','unique_trade_days'),('active_closed_months','active_months'),('positive_closed_months','positive_months'),('negative_closed_months','negative_months')]:
   if sourcekey in dist:CHECKS.append({'configuration':r['configuration_id'],'instrument':sym,'metric':target,'registry':str(r[target]),'published':str(dist[sourcekey]),'match':int(r[target])==int(dist[sourcekey])})
  # Saved economic outputs are cross-checked, never used to model an outcome.
  em=published.get('conditional_closed_only_C1',published.get('conditional_closed_only_c1',published.get('closed_only_diagnostic',{})))
  if 'c1' in em:em=em['c1']
  source=dict(published);source.update(em)
  aliases2={'net_R':['Net_R','net_R','net_R_closed_diagnostic','closed_net_R'],'net_price':['Net_price','closed_only_net_c1','closed_net','net'],'PF_after_C1_R':['PF_C1_R','net_PF_R'],'PF_after_C1_price':['PF_C1_price','net_PF_closed_diagnostic','closed_net_PF','net_PF','PF'],'gross_price':['closed_only_gross','closed_gross','gross'],'cost_price':['cost_C1','closed_only_c1','closed_cost','cost']}
  for k,ks in aliases2.items():
   if r[k]==NA:continue
   for a in ks:
    v=source.get(a)
    if v is not None and v!='':
     delta=abs(dec(r[k])-dec(v));CHECKS.append({'configuration':r['configuration_id'],'instrument':sym,'metric':k,'registry':str(r[k]),'published':str(v),'absolute_delta':str(delta),'match':delta<Decimal('1e-20')});break
  cov=published.get('coverage_status',published.get('coverage_classification',published.get('coverage_complete',None)))
  if cov is not None:r['source_coverage']=ser(cov)
 if skip is not None:r['data_gap_skip']=len([x for x in skip if x.get('instrument')==sym])
 if excluded is not None:
  r['data_quality_excluded']=len([x for x in excluded if x.get('instrument')==sym]);r['executed_entries']=int(r['executed_entries'])+r['data_quality_excluded']
 if coverage is not None:r['source_coverage']=ser(coverage)
 if r['source_coverage']==NA:r['source_coverage']='PARTIAL_SOURCE; pre-inception/gaps retained; see input_provenance and coverage reports'
 unc=int(r['historical_unknown'])+(int(r['data_quality_excluded']) if r['data_quality_excluded']!=NA else 0)
 denom=int(r['closed'])+unc
 r['uncertain_outcome_share']=str(Decimal(unc)/denom) if denom else NA
 r['uncertain_outcome_denominator']='CLOSED + historical UNKNOWN (including possible fills) + EXCLUDED; SKIP excluded'
 r['selection_bias_warning']='UNRESOLVED_OR_EXCLUDED_OUTCOMES; conditional cohort may be biased' if unc else 'SOURCE_GAPS_OR_LIMITED_HISTORY; not complete annual evidence'
 finish(r);ROWS.append(r)

def finish(r):
 r.pop('_inputs',None)
 reasons=[];closed=r['closed'];days=r['unique_closed_trade_days'];months=r['active_closed_months']
 r['sample_count_pass']=closed!=NA and int(closed)>=100
 r['calendar_pass']=days!=NA and months!=NA and int(days)>=40 and int(months)>=6
 if r['record_type']=='DIAGNOSTIC_ONLY':reasons.append('DIAGNOSTIC_ONLY')
 elif r['technical_status'] in ['NEEDS_VERIFICATION','SIGNAL_LOGIC_NEEDS_FIX']:reasons.append('NEEDS_VERIFICATION')
 elif closed==NA or days==NA or months==NA or r['independent_audit_status']==NA:reasons.append('INSUFFICIENT_EVIDENCE')
 if closed!=NA and int(closed)<100:reasons.append('INSUFFICIENT_TRADES')
 if (days!=NA and int(days)<40) or (months!=NA and int(months)<6):reasons.append('INSUFFICIENT_CALENDAR')
 if r['record_type']=='HISTORICAL_REFERENCE' and 'NEEDS_VERIFICATION' not in reasons:reasons.insert(0,'NEEDS_VERIFICATION')
 r['eligibility']=reasons[0] if reasons else 'ELIGIBLE'
 r['eligibility_reasons']='|'.join(reasons) if reasons else '100_CLOSED_AND_40_DAYS_AND_6_MONTHS; audited reproducible conditional model; PF unrestricted'
 missing={k:('No saved value / not applicable to this contract; consult exact linked source' if k not in ['complete_annual_result','PF_after_C1_R','PF_after_C1_price'] else 'Full annual result unavailable due coverage/unresolved outcomes' if k=='complete_annual_result' else 'No known losses or no CLOSED; finite PF undefined') for k,v in r.items() if v==NA}
 missing.update(json.loads(r.get('not_available_reasons','{}')))
 r['not_available_reasons']=ser(missing)

# Canonical current frozen journal families; different B durations stay one family.
BASELINES=[('A','equal_high_low_m5_2023_a_v1','equal_high_low_m5'),('B','high_low_cluster_m5_2023_b4_v1','high_low_cluster_m5'),('B','high_low_cluster_m5_2023_b7_v1','high_low_cluster_m5'),('B','high_low_cluster_m5_2023_b10_v1','high_low_cluster_m5'),('C','return_retest_rejection_m5_2023_c_v1','return_retest_rejection_m5'),('R16','r16_compression_breakout_2023_m5_v1','compression_breakout'),('R17','r17_orb_breakout_retest_2023_m5_v1','orb_breakout_retest'),('R18','orb_a_base_2023_canonical_v1','orb_false_break_fade'),('LEVEL_REJECTION','level_rejection_2023_m5_v1','level_rejection'),('SWING_PULLBACK','swing_pullback_m5_m15_2023_v1','swing_pullback_m5_m15'),('TREND_PULLBACK','trend_pullback_m15_h1_2023_v1','trend_pullback_m15_h1')]
for fam,name,code in BASELINES+[('BOLLINGER_RSI','bollinger_rsi_reentry_m15_2023_v1','bollinger_rsi_reentry_m15')]:
 ref=BB if fam=='BOLLINGER_RSI' else BASE;typ='HISTORICAL_REFERENCE' if ref==BB else 'BASELINE_CONFIGURATION'
 d='IntradayLab/results/'+name;ledger=table(d+'/trades.csv',ref);m=obj(d+'/metrics.json',ref)['instruments']
 if fam=='C':
  research=obj(d+'/research_metrics.json',ref)['instruments']
  m={sym:dict(m[sym],**research[sym]['counts'],distribution=research[sym]['distribution']) for sym in SYMS}
 r=empty(fam,name,typ,ref,d+'/trades.csv','IntradayLab/config/'+name+'.json',d+'/audit.json','IntradayLab/strategies/'+code+'.py',tf='M15' if fam in ['TREND_PULLBACK','BOLLINGER_RSI'] else 'M5',context='M15' if fam=='SWING_PULLBACK' else 'H1' if fam=='TREND_PULLBACK' else 'NONE')
 if ref==BB:r['technical_status']='SIGNAL_LOGIC_NEEDS_FIX'
 for sym in SYMS:
  coverage=table(d+'/coverage_summary.csv',ref) if exists(d+'/coverage_summary.csv',ref) else None
  apply(r,sym,ledger,published=m[sym],coverage=next((v for v in coverage or [] if v.get('instrument')==sym),None),skip=table(d+'/data_gap_skips.csv',ref) if fam=='C' else None,excluded=table(d+'/data_quality_exclusions.csv',ref) if fam=='C' else None)
# Oracle remains an execution diagnostic; copied metrics never qualify.
d='IntradayLab/results/equal_high_low_m5_2023_a_v1/diagnostics'
r=empty('A','A_ENTRY_CLOSE_ORACLE','DIAGNOSTIC_ONLY',BASE,d+'/close_oracle_trades.csv','IntradayLab/config/equal_high_low_m5_2023_a_v1.json','IntradayLab/results/equal_high_low_m5_2023_a_v1/audit.json','IntradayLab/tools/run_equal_high_low_baseline.py')
r['technical_status']='NONEXECUTABLE_SIGNAL_CLOSE_ORACLE';r['economic_scope']='ORACLE_DIAGNOSTIC_ONLY; synthetic same-close entry'
for sym in SYMS:apply(r,sym,table(d+'/close_oracle_trades.csv'),published=obj(d+'/close_oracle_metrics.json')['instruments'][sym])
# Legacy v1 and corrective v2 (including preserved pre-correction journal).
for name,ref in [('stage2_m5',BASE),('stage2_m5_conditional_v2',BASE),('stage2_m5',OLD)]:
 d='IntradayLab/results/'+name;c='stage2_m5_baseline_v1' if name=='stage2_m5' else name
 ledger=table(d+'/trade_ledger.csv',ref);runs=obj(d+'/results.json',ref)['runs'];signals=table(d+'/signals.csv',ref)
 for fam in ['VWAP_MR','MOMENTUM']:
  cid=name+'_'+fam+('_PRE_CORRECTION' if ref==OLD else '')
  r=empty(fam,cid,'HISTORICAL_REFERENCE' if ref==OLD else 'BASELINE_CONFIGURATION' if name=='stage2_m5' else 'EXECUTION_VARIANT',ref,d+'/trade_ledger.csv','IntradayLab/config/'+c+'.json',d+'/verification.json','IntradayLab/tools/m5_baseline.py' if name=='stage2_m5' else 'IntradayLab/tools/m5_conditional_v2.py',selectors={'strategy':fam})
  if name=='stage2_m5':r['technical_status']='NEEDS_VERIFICATION';r['reproducibility_status']='LEGACY_YEAR_LATCH; initial missing-entry handling corrected; research acceptance failed'
  for sym in SYMS:
   run=next(x for x in runs if x['run']==fam+'_'+sym);summ=run['summary']
   pub=dict(summ,signals=run['signals'])
   skip=run.get('execution_counts',{}).get('no_bar_no_model_fill')
   r['data_gap_skip']=skip if skip is not None else NA
   apply(r,sym,[x for x in ledger if x['strategy']==fam],published=pub,unknown_extra=int(summ.get('unknown_entry_orders',0)))
# Complete architectures and derived MTF, separately audited; no sum across repeats/comparators.
for name in ['stage2_complete_architectures_v1','stage2_vwap_payable_cap_v1','stage2_causal_mtf_v1']:
 d='IntradayLab/results/'+name;ledger_path=d+('/trade_ledger.csv' if name=='stage2_vwap_payable_cap_v1' else '/trade_ledger.csv.gz')
 ledger=table(ledger_path);runs=obj(d+'/results.json')['runs']
 groups=defaultdict(list)
 for p in runs:groups[(p['strategy'],p['architecture'],p['scenario'])].append(p)
 for (fam,arch,sc),ps in sorted(groups.items()):
  cid=name+'_'+fam+'_'+arch+'_'+sc
  audit='IntradayLab/results/stage2_final_independent_audit/audit.json' if name=='stage2_causal_mtf_v1' else 'IntradayLab/results/stage2_architecture_review/independent_audit.json'
  code='IntradayLab/tools/causal_mtf.py' if name=='stage2_causal_mtf_v1' else 'IntradayLab/tools/stage2_vwap_payable_cap.py' if name=='stage2_vwap_payable_cap_v1' else 'IntradayLab/tools/stage2_architecture_replay.py'
  sel={'strategy':fam,'architecture':arch,'scenario':sc}
  r=empty(fam,cid,'EXECUTION_VARIANT',BASE,ledger_path,'IntradayLab/config/'+name+'.json',audit,code,context=ps[0].get('context_tf','NONE'),scenario=sc,selectors=sel)
  lt=[x for x in ledger if all(x.get(k)==v for k,v in sel.items())]
  for sym in SYMS:
   p=next(x for x in ps if x['instrument']==sym);r['data_gap_skip']=p.get('execution_counts',{}).get('no_bar_no_model_fill',NA)
   apply(r,sym,lt,published=p)
# Squeeze M5 and standalone M15, plus their actual derived context and delay variants.
for fam,name in [('SQUEEZE_M5','stage2_squeeze_v1'),('SQUEEZE_M15','stage2_squeeze_m15_v1')]:
 d='IntradayLab/results/'+name;ledger=table(d+'/trade_ledger.csv.gz');pub=table(d+'/metrics.csv');signals=table(d+'/signals.csv.gz')
 for arch,sc in sorted({(p['architecture'],p['scenario']) for p in pub}):
  sel={'architecture':arch,'scenario':sc}
  audit=d+('/independent_audit.json' if fam=='SQUEEZE_M5' else '/pre_publication_verification.json')
  r=empty(fam,name+'_'+arch+'_'+sc,'BASELINE_CONFIGURATION' if arch in ['SQUEEZE_M5','SQUEEZE_M15'] and sc=='T10' else 'EXECUTION_VARIANT',BASE,d+'/trade_ledger.csv.gz','IntradayLab/config/'+name+'.json',audit,'IntradayLab/tools/squeeze_replay.py' if fam=='SQUEEZE_M5' else 'IntradayLab/tools/squeeze_m15_replay.py',tf='M5' if fam=='SQUEEZE_M5' else 'M15',context='M30' if arch=='SQUEEZE_M30_M5' else 'H1' if arch=='SQUEEZE_H1_M15' else 'NONE',scenario='C1_'+sc,selectors=sel)
  lt=[x for x in ledger if all(x.get(k)==v for k,v in sel.items())]
  ss=[x for x in signals if all(x.get(k)==v for k,v in sel.items())]
  for sym in SYMS:apply(r,sym,lt,signals=ss,published=next(p for p in pub if p['instrument']==sym and all(p[k]==v for k,v in sel.items())))
# Published ORB strict-year, v1 daywise, and v2 daywise models on the independent historical branch.
for name,suffix in [('stage2_orb_false_break_fade_m5_v1',''),('stage2_orb_false_break_fade_m5_v2_research',''),('stage2_orb_false_break_fade_m5_v2_research','/v1_daywise')]:
 d='IntradayLab/results/'+name+suffix;ledger=table(d+'/trades.csv',ORB);pub=obj(d+'/metrics.json',ORB)
 config='IntradayLab/config/'+('stage2_orb_false_break_fade_m5_v1' if name.endswith('v1') or suffix else name)+'.json'
 for arch in ['A_BASE','B_IND','C_MTF','D_MTF_IND']:
  r=empty('R18',name+suffix.replace('/','_')+'_'+arch,'HISTORICAL_REFERENCE',ORB,d+'/trades.csv',config,d+('/independent_audit.json' if not suffix else '/audit.json'),'IntradayLab/tools/orb_false_break_fade_replay.py',context='M15' if 'MTF' in arch else 'NONE',selectors={'architecture':arch})
  r['technical_status']='NEEDS_VERIFICATION';r['reproducibility_status']='ARCHIVED_INDEPENDENT_AUDIT_RECORDED; requires separate acceptance of historical configuration/source before Optimization'
  for sym in SYMS:apply(r,sym,[x for x in ledger if x['architecture']==arch],published=pub[arch+'_'+sym])
# Non-executable opportunity preflight, overlapping exit-only seeds, and blocked native context.
for fam,name,config,path in [('LEVEL_REJECTION','level_opportunity','stage2_level_rejection_m5_opportunity_v1','IntradayLab/results/stage2_level_rejection_m5_opportunity_v1/opportunity_funnel.json'),('LEVEL_REJECTION','level_economic_rules_only_PR460','stage2_level_rejection_m5_economic_v1','IntradayLab/reports/STAGE2_LEVEL_REJECTION_M5_ECONOMIC_PREREGISTRATION.md'),('LEVEL_REJECTION','level_FAST0_PR462','stage2_level_rejection_m5_fast_execution_v1','IntradayLab/reports/STAGE2_LEVEL_REJECTION_M5_FAST_EXECUTION_PREREGISTRATION.md'),('LEVEL_REJECTION','level_FAST5_PR462','stage2_level_rejection_m5_fast_execution_v1','IntradayLab/reports/STAGE2_LEVEL_REJECTION_M5_FAST_EXECUTION_PREREGISTRATION.md')]:
 ref=BASE if name=='level_opportunity' else '53442b49e31f6409567e31c4fa14d738814eab49' if '460' in name else '7a9c5d3759a5c07d002d5ed3e630132829dd7ebf'
 r=empty(fam,name,'DIAGNOSTIC_ONLY' if name=='level_opportunity' else 'HISTORICAL_REFERENCE',ref,path,'IntradayLab/config/'+config+'.json','IntradayLab/results/stage2_level_rejection_m5_opportunity_v1/independent_audit.json' if ref==BASE else '', 'IntradayLab/tools/run_level_rejection_opportunities.py' if ref==BASE else '')
 r['technical_status']='NONEXECUTABLE_PREFLIGHT' if ref==BASE else 'NEEDS_VERIFICATION';r['economic_scope']='NO_EXECUTED_ECONOMIC_BASELINE_PUBLISHED; prospective grammar only'
 for sym in SYMS:
  rr=dict(r,instrument=sym);rr['not_available_reasons']=ser({'closed':'No executed trade journal exists; opportunities/rules are not CLOSED'});finish(rr);ROWS.append(rr)
for fam in ['VWAP_MR','MOMENTUM']:
 d='IntradayLab/results/stage2_exit_only_ablation_v1'
 r=empty(fam,'exit_only_ablation_'+fam,'DIAGNOSTIC_ONLY',BASE,d+'/trade_ledger.csv.gz','IntradayLab/config/stage2_exit_only_ablation_v1.json','IntradayLab/results/stage2_architecture_review/independent_audit.json','IntradayLab/tools/stage2_exit_only_ablation.py',selectors={'strategy':fam})
 r['technical_status']='NONEXECUTABLE_OVERLAPPING_SEEDS';r['economic_scope']='Independent overlapping known-entry counterfactual seeds; not strategy execution cohort'
 for sym in SYMS:
  rr=dict(r,instrument=sym);finish(rr);ROWS.append(rr)
 r=empty(fam,'native_M30_BLOCKED_'+fam,'DIAGNOSTIC_ONLY',BASE,'IntradayLab/results/stage2_architecture_diagnostics/mtf_readiness.json','IntradayLab/config/stage2_complete_architectures_v1.json','IntradayLab/results/stage2_architecture_review/independent_audit.json','IntradayLab/tools/stage2_architecture_replay.py',context='M30')
 r['technical_status']='NATIVE_MTF_BLOCKED_NO_AUTHORIZED_CONTEXT';r['economic_scope']='No native M30 delivery/composition authorization; not a tested native MTF strategy'
 for sym in SYMS:
  rr=dict(r,instrument=sym);finish(rr);ROWS.append(rr)
# The old isolated v2 delay sensitivity has summary evidence but no saved separate trade journal.
for fam in ['VWAP_MR','MOMENTUM']:
 path='IntradayLab/results/stage2_m5_conditional_v2/delay_sensitivity.json'
 r=empty(fam,'isolated_v2_T15_summary_'+fam,'EXECUTION_VARIANT',BASE,path,'IntradayLab/config/stage2_m5_conditional_v2.json','IntradayLab/results/stage2_m5_conditional_v2/verification.json','IntradayLab/tools/m5_conditional_v2.py',scenario='C1_T15')
 r['technical_status']='NEEDS_VERIFICATION';r['reproducibility_status']='SUMMARY_ONLY; no separate saved T15 journal here; later architectures record separate T15 cohorts'
 for sym in SYMS:
  p=next(x for x in obj(path) if x['run']==fam+'_'+sym)['sensitivity_summary'];rr=dict(r,instrument=sym,closed=p['closed_accounted_trades'],executed_entries=p['trades'],historical_unknown=p['unresolved'],net_R=p.get('net_R',NA),net_price=p['closed_only_net_c1'],PF_after_C1_price=p['PF'] if p['PF'] is not None else NA)
  finish(rr);ROWS.append(rr)
# Preserve all 141 historically retained CMD/V4 positive candidates, without inventing unretained results.
for cycle,fam in [(15,'PRIOR_DAY_SWEEP'),(16,'R16'),(17,'R17'),(18,'R18')]:
 path=f'research/autonomous/registry/cycle{cycle}_profitable.csv';protocol=f'research/autonomous/cycle{cycle}_protocol.md'
 for p in table(path,CMD):
  # Protocol is Markdown: keep its hash as the frozen configuration source.
  r=empty(fam,p['candidate_id'],'HISTORICAL_REFERENCE',CMD,path,'','',protocol,tf='M5',scenario='HISTORICAL_BASE_TICK_FRICTION')
  r.update(instrument='CNYRUBF',execution_timeframe='M1',config_source=protocol,config_sha256=hashlib.sha256(read(protocol,CMD)).hexdigest(),period_start='2026-01-05',period_end_exclusive='2026-05-16',technical_status='NEEDS_VERIFICATION',reproducibility_status='ARCHIVED_SELECTED_SUMMARY; no saved trade journal/source audit for every retained candidate',economic_scope='HISTORICAL_SELECTED_2026_BPS; neither C1 R nor per-instrument price PF',data_commit_sha=NA,data_source='CNYRUBF M1; reported permitted 2026 research prefix; no candle read in registry task',executed_entries=p['executed_trades'],unique_closed_trade_days=NA,positive_closed_months=NA,entry_stop_take_execution=ser(p),C1_rules='Historical BASE one adverse tick/side excluding commission; bps relative entry; not equated to IntradayLab C1 R',not_available_reasons=ser({'closed':'Reported executed_trades without saved CLOSED/UNKNOWN split; not counted as verified CLOSED','active_closed_months':'Positive months reported; active CLOSED months not independently reconstructible','unique_closed_trade_days':'Historical BASE days remain in historical_reported_metrics; no audited CLOSED cohort','positive_closed_months':'Historical BASE bps months are not verified IntradayLab C1 CLOSED months','PF_after_C1_R':'Historical BASE bps PF is methodologically different','PF_after_C1_price':'No saved per-trade quote P&L for price PF'}))
  r['data_repository']=NA;r['code_source']=NA;r['historical_reported_metrics']=ser(p);finish(r);ROWS.append(r)
path='research/autonomous/registry/legacy_v4_dev_positive.csv'
for p in table(path,CMD):
 fam='BOLLINGER_RSI' if p['family']=='BOLLINGER_RSI' else 'R17' if p['submodel']=='BREAKOUT_RETEST' else 'ORB_DIRECT' if p['family']=='ORB' else 'GERCHIK_PROXY' if p['submodel']=='GERCHIK_A_M5_PROXY' else 'STRUCTURAL_FALSE_BREAK'
 r=empty(fam,p['candidate_id'],'HISTORICAL_REFERENCE',CMD,path,'config/top5_v4/strategy_contract.json','','src/market_pattern_discovery/backtest/top5_v4/families.py',tf='M1' if p['family']=='ORB' else 'M5',scenario='V4_DEV_BASE_BPS')
 r.update(instrument=NA,execution_timeframe='M1',period_start='2026-01-05',period_end_exclusive='2026-03-01',technical_status='NEEDS_VERIFICATION',reproducibility_status='RETAINED_DEV_SUMMARY; instrument attribution and trade ledger missing from retained CSV',economic_scope='V4_SELECTED_DEV_BPS; later rejection/validation unchanged',historical_reported_metrics=ser(p),data_source='Original V4 source metadata only; retained CSV has no instrument column',executed_entries=p['trades'],not_available_reasons=ser({'instrument':'No per-instrument attribution in retained CSV; never assign pooled count to CNY/USD','closed':'Reported trades without verifiable terminal-status journal','PF_after_C1_R':'Published historical bps PF not comparable to C1 R','PF_after_C1_price':'Published bps PF is not price-unit PF'}))
 r['data_repository']=NA;finish(r);ROWS.append(r)
# R14 was actually run but had no executable candidates. Not 48 new strategies.
r=empty('VWAP_EXHAUSTION','R14_NO_EXECUTABLE_CANDIDATE','HISTORICAL_REFERENCE',CMD,'research/autonomous/cycle14_report.md','','','research/autonomous/cycle14_protocol.md')
r.update(instrument='CNYRUBF',execution_timeframe='M1',period_start='2026-01-05',period_end_exclusive='2026-05-16',technical_status='NEEDS_VERIFICATION',executed_entries=0,economic_scope='48 preregistered candidates; 1282 reclaim events; zero executed trades in published report; no per-config journal',historical_reported_metrics=ser({'grid_candidates':48,'executed_trades':0}))
r['data_repository']=NA;r['code_source']=NA;r['config_source']='research/autonomous/cycle14_protocol.md';r['config_sha256']=hashlib.sha256(read(r['config_source'],CMD)).hexdigest();finish(r);ROWS.append(r)

POLICY={'schema':'IntradayLab.optimization_policy.v1','decision_date':'2026-10-11','timezone':'Europe/Moscow','base_sha':BASE,'lifecycle':['Baseline','Optimization','Robustness','Walk Forward','TRUE OOS'],'per_instrument_minimum':{'verified_closed_trades':100,'unique_closed_entry_days':40,'active_closed_entry_months':6,'baseline_PF_requirement':'ANY_PF','signal_and_execution_credibility_required':True,'reproducible_code_config_source_required':True},'closed_exclusions':['UNKNOWN','UNRESOLVED','SKIP','EXCLUDED','REJECTED','NONFILL','synthetic_oracle','overlapping_exit_only_seeds'],'classifications':['ELIGIBLE','INSUFFICIENT_TRADES','INSUFFICIENT_CALENDAR','INSUFFICIENT_EVIDENCE','DIAGNOSTIC_ONLY','NEEDS_VERIFICATION'],'all_failed_requirements_recorded':True,'calendar_definition':'Distinct MSK entry dates/months among resolved known CLOSED, never source-coverage days or signal days; positive/negative months use saved closure dates and after-C1 R','aggregation_numeric_precision':{'Decimal_digits':50,'published_comparison_absolute_tolerance_R':'1e-20','monthly_zero_sign_tolerance_R':'1e-20','reason':'Saved Decimal28 ratios carry final-digit rounding; this reporting tolerance is not a trade/PnL or eligibility adjustment'},'missing_value':'NOT_AVAILABLE with field-specific reason; never missing-as-zero','PF_units':'Per instrument C1 price PF and raw initial-risk R PF separately; no mixed-instrument price PF','unknown_policy':'Immutable historical UNKNOWN; report exclusions/skips separately; conditional known economics do not establish annual profitability','historical_reference_policy':'Recorded archive audit is not present acceptance/verification of a historical configuration; NEEDS_VERIFICATION until separately confirmed, never discard positive summaries','C2_policy':'Published replacement-cost stress is retained in COST_STRESS_REFERENCES.csv; same fills are not new independent observations or new strategy configurations','goals':{'after_C1_PF_minimum':'2.0','sufficient_closed_trades':True,'positive_expectancy':True,'priority':'regular positive calendar-month results','drawdown':'controlled; quantitative bound frozen before each individual study','concentration':'no excessive single-trade/month dependence; bounds frozen before each individual study','neighboring_parameter_stability':True,'Take_profit_range_R':[2,10],'Take_R_definition':'Explicitly freeze gross/raw-risk/net-net denominator for each individual study; do not silently change old target conventions'},'optimization_history_year':2023,'before_each_individual_optimization':['Separate explicit authorization','Freeze family-specific bounded grid','Freeze search budget','Freeze exact parameters, source, entry/execution/Stop/Take conventions','Freeze candidate IDs and evaluation rules before P&L'],'queue_rule':'A then B then C then other eligible families in documented working order; never max historical PF','authorization':'Registry preparation only; no Optimization authorized or executed','prohibited_in_this_task':['new economic Baseline','parameter search','trading logic changes','execution reinterpretation/replay','Robustness','WF','TRUE OOS','2024+ candle reads','TradingSystemLab modifications','market-pattern-data modifications','Draft PR472 mutations','merge','auto-merge']}

def writecsv(name,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 if name=='MASTER_STRATEGY_REGISTRY.csv':
  for r in rows:
   reasons=json.loads(r.get('not_available_reasons','{}'))
   for k in keys:
    if k not in r or r[k] is None:
     r[k]=NA;reasons[k]='Not applicable to family-definition row' if r['record_type']=='STRATEGY_FAMILY' else 'No saved field for this record type'
   r['not_available_reasons']=ser(reasons)
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys,lineterminator='\n');w.writeheader();w.writerows(rows)

def writejson(name,x): (OUT/name).write_text(json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
# For reproducible provenance, inspect/hash all 719 main files and all unique archived additions.
mainfiles=git('ls-tree','-r','--name-only',BASE,'IntradayLab').decode().splitlines()
for path in mainfiles:read(path)
for ref in sorted({r['sha'] for r in json.loads((OUT/'DISCOVERY_SNAPSHOT.json').read_text())['intraday_branch_trees']}):
 for p in git('ls-tree','-r','--name-only',ref,'IntradayLab').decode().splitlines():
  if p not in mainfiles:read(p,ref)
for p in git('ls-tree','-r','--name-only',CMD,'research/autonomous').decode().splitlines():read(p,CMD)
# Attach source-file row selectors and field-specific missing reasons; family definitions contain no pooled observations.
for fam,(name,tuning) in FAMILIES.items():
 rows=[r for r in ROWS if r['family_id']==fam]
 ROWS.append({'record_type':'STRATEGY_FAMILY','family_id':fam,'strategy_name':name,'configuration_id':fam+'_FAMILY','instrument':'FAMILY_DEFINITION','directions':'LONG|SHORT','potential_tuning_directions':tuning,'eligibility':'NOT_APPLICABLE','eligibility_reasons':'Family definition; assess each configuration/instrument separately','not_available_reasons':ser({'trade_metrics':'No family-level pooling; overlapping models are not independent'})})
ROWS.sort(key=lambda r:(r['family_id'],r['configuration_id'],r['instrument']))
for c in CATALOG:
 source=next(r for r in ROWS if r['configuration_id']==c['configuration_id'])
 c['config']=source.get('config_source') if source.get('config_source')!=NA else None
 c['code']=source.get('code_source') if source.get('code_source')!=NA else None
writecsv('MASTER_STRATEGY_REGISTRY.csv',ROWS)
elig=[{k:r[k] for k in ['family_id','configuration_id','record_type','instrument','closed','historical_unknown','data_gap_skip','data_quality_excluded','unique_closed_trade_days','active_closed_months','sample_count_pass','calendar_pass','technical_status','eligibility','eligibility_reasons','uncertain_outcome_share','selection_bias_warning','baseline_source','result_commit_sha']} for r in ROWS if r['record_type']!='STRATEGY_FAMILY']
writecsv('INSTRUMENT_ELIGIBILITY.csv',elig);writejson('OPTIMIZATION_POLICY.json',POLICY);writejson('STUDY_CATALOG.json',CATALOG);writejson('SOURCE_FILE_INVENTORY.json',list(INPUTS.values()));writejson('PUBLISHED_METRIC_RECONCILIATION.json',CHECKS)
# Preserve saved C2 overlays, including whole published rows; never run changed-cost execution.
stresses=[]
for name in ['stage2_squeeze_v1','stage2_squeeze_m15_v1']:
 path='IntradayLab/results/'+name+'/sensitivity.csv'
 for p in table(path):
  if p.get('cost')=='C2':stresses.append({'source_commit':BASE,'source_path':path,'family_id':'SQUEEZE_M5' if name=='stage2_squeeze_v1' else 'SQUEEZE_M15','instrument':p['instrument'],'reference_kind':'SAME_FILL_COST_OVERLAY','source_selector':ser({k:p[k] for k in ['architecture','scenario','cost']}),'saved_metrics':ser(p),'independent_observation':False})
for name in ['stage2_complete_architectures_v1','stage2_vwap_payable_cap_v1','stage2_causal_mtf_v1']:
 path='IntradayLab/results/'+name+'/results.json'
 for p in obj(path)['runs']:
  stresses.append({'source_commit':BASE,'source_path':path,'family_id':p['strategy'],'instrument':p['instrument'],'reference_kind':'SAME_FILL_COST_OVERLAY','source_selector':ser({k:p[k] for k in ['architecture','scenario','run']}),'saved_metrics':ser({k:v for k,v in p.items() if k.startswith('C2')}),'independent_observation':False})
for name in ['stage2_orb_false_break_fade_m5_v1','stage2_orb_false_break_fade_m5_v2_research','stage2_orb_false_break_fade_m5_v2_research/v1_daywise']:
 path='IntradayLab/results/'+name+'/metrics.json'
 for key,p in obj(path,ORB).items():
  stress=p.get('conditional_closed_only_c2',p.get('closed_only_diagnostic',{}).get('c2',{}))
  stresses.append({'source_commit':ORB,'source_path':path,'family_id':'R18','instrument':p.get('instrument',key.rsplit('_',1)[-1]),'reference_kind':'HISTORICAL_SAME_FILL_COST_OVERLAY','source_selector':key,'saved_metrics':ser(stress),'independent_observation':False})
writecsv('COST_STRESS_REFERENCES.csv',stresses)
writejson('SOURCE_FILE_INVENTORY.json',list(INPUTS.values()))
counts=Counter(r['eligibility'] for r in elig);summary={'family_count':len(FAMILIES),'published_configuration_and_variant_count':len(CATALOG),'instrument_rows':len(elig),'rows_by_record_type':dict(Counter(r['record_type'] for r in elig)),'classifications':dict(counts),'eligible_families':sorted({r['family_id'] for r in elig if r['eligibility']=='ELIGIBLE'}),'published_metric_checks':len(CHECKS),'published_metric_failures':sum(not x['match'] for x in CHECKS),'cost_overlay_rows':len(stresses),'main_files':len(mainfiles),'source_files_read':len(INPUTS)}
writejson('REGISTRY_COUNTS.json',summary)
print(ser(summary))
if summary['published_metric_failures']:
 print(ser([x for x in CHECKS if not x['match']]));raise SystemExit('Saved metric discrepancy must be explained before publication')
