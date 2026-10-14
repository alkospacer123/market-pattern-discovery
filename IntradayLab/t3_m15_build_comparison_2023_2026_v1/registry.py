"""Finite registry of previously executed frozen configurations. No grid."""
from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
PIN='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
MAIN='d6946056332ce71658a6ca933cefa0740a7570a2'
PR513='c17709a748f6247e8bd6bf85c9b4f20fac14a4dd'
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
CUTOFF='2026-10-13T00:00:00+03:00'
BASE=dict(ema_period=75,slope_lookback=5,adx_period=14,adx_threshold=20,atr_period=14,atr_average_period=20,breakout_period=20,stop_atr=2.)
CATALOG={
 'entry_regime':495,'stop_exit':496,'combined':497,'initial_stop':498,
 'session_entry':499,'t1_s1':500,'execution_sensitivity':504,
 'a6_s1_trail_optimization':505,'a6_s1_trail_plateau':506,'early_risk_protection':508}
SOURCE_NAMES={'a6_s1_trail_plateau':'t3_m15_a6_s1_trail_plateau_v2'}
ENTRY_DESC={'CONTROL':'EMA75 / H1 ADX14>20 / H1 ATRRatio>1 / directional slope5 / Donchian20 shift(1)',
 'A3':'directional body >= 0.5*(High-Low)','A4':'H1 ADX > previous H1 ADX',
 'A5':'LONG slope grows; SHORT abs(slope) grows','A6':'H1 ATRRatio > previous H1 ATRRatio',
 'A7':'M15 ATR > previous M15 ATR','T1':'10:00 <= signal Close MSK <18:00',
 'T2':'skip first observed bar after gap>15min; skip absent predecessor'}
def folder(group):return SOURCE_NAMES.get(group,'t3_m15_'+group+'_v1')
def builds():
 out=[]
 def add(group,rule,version,trail,mode='SIGNAL_CLOSE',name=None):
  mechanism={'C1':'A6_S1','C2':'A7_S1','COMBINED':'T1_S1'}.get(rule,rule)
  entry='A6' if rule=='C1' else 'A7' if rule=='C2' else 'T1' if rule in ('T1','COMBINED') else rule if rule in ('A3','A4','A5','A6','A7','T2') else 'CONTROL'
  exit='EARLY_PROTECT_05' if version=='EARLY_PROTECT_05' else 'S1' if rule in ('S1','C1','C2','COMBINED') else rule if rule in ('A1','A2','S2','S3') else 'CONTROL'
  initial=rule if rule in ('I1','I2','I3') else '2ATR'
  ident=f'{mechanism}_{mode}_TRAIL_{str(trail).replace(".","p")}' if not name else name
  cfg=BASE|dict(trail_atr=trail,entry=entry,exit=exit,initial=initial,mode=mode)
  p=HERE.parent/folder(group); spec=next(iter(sorted(p.glob('*SPEC*.json'))),p/'engine.py')
  out.append(dict(build_id=ident,group=group,rule=rule,version=version,trail=trail,mode=mode,
    entry_filter=ENTRY_DESC['CONTROL']+(' + '+ENTRY_DESC[entry] if entry!='CONTROL' else ''),entry=entry,exit=exit,initial=initial,
    config=cfg,config_identity=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
    source_PR=CATALOG[group],source_path=str(p.relative_to(ROOT)),spec_path=str(spec.relative_to(ROOT)),
    admission='CAUSAL_MODEL' if mode=='NEXT_OPEN' else 'IDEALIZED_EXECUTION_DIAGNOSTIC',
    original_years='2023;2024',replay_years='2023;2024;2025;2026_YTD',status='FROZEN_REPRODUCIBLE_PENDING_CURRENT_REPLAY',
    instruments=';'.join(SYMBOLS),aliases=[]))
 for v,tr in [('BASELINE',3.),('OPTIMIZED',3.5)]:
  for r in ('CONTROL','A1','A2','A3','A4','A5','A6','A7'):add('entry_regime',r,v,tr)
  for r in ('S1','S2','S3'):add('stop_exit',r,v,tr)
  for r in ('C1','C2'):add('combined',r,v,tr)
  for r in ('I1','I2','I3'):add('initial_stop',r,v,tr)
  for r in ('T1','T2'):add('session_entry',r,v,tr)
  add('t1_s1','COMBINED',v,tr)
  for r in ('C1','T1','COMBINED'):add('execution_sensitivity',r,v,tr,'NEXT_OPEN')
 for v,tr in [('TRAIL_275',2.75),('TRAIL_325',3.25),('TRAIL_375',3.75)]:add('a6_s1_trail_optimization','C1',v,tr,'NEXT_OPEN',name='A6_S1_NEXT_OPEN_'+v)
 for v,tr in [('TRAIL_3625',3.625),('TRAIL_3875',3.875),('TRAIL_400',4.)]:add('a6_s1_trail_plateau','C1',v,tr,'NEXT_OPEN',name='A6_S1_NEXT_OPEN_'+v)
 add('early_risk_protection','C1','EARLY_PROTECT_05',3.75,'NEXT_OPEN',name='A6_S1_EARLY_PROTECT_05_NEXT_OPEN_TRAIL_375')
 # Preserve all duplicating investigations as origins of the same executable behavior.
 for b in out:
  r=b['rule'];m=b['mode'];tr=b['trail']
  origins=[b['source_PR']]
  if m=='SIGNAL_CLOSE' and tr in (3.,3.5):
   if r=='CONTROL':origins += [490,491,495,496,497,498,499,500]
   if r in ('A6','A7','S1'):origins += [497]
   if r in ('S1','T1','COMBINED'):origins += [500]
   if r in ('C1','T1','COMBINED'):origins += [504]
   if r=='COMBINED' and tr==3.5:origins += [503]
  if m=='NEXT_OPEN' and r=='C1' and b['version']!='EARLY_PROTECT_05':
   if tr in (3.,3.5):origins += [505]
   if tr in (3.5,3.75):origins += [506]
   if tr==3.75:origins += [507,508,509,510,511,512,513];b['original_years']='2023;2024;2025;2026_YTD'
  b['aliases']=sorted(set(origins));b['all_source_PRs']=';'.join(map(str,b['aliases']))
 assert len(out)==51 and len({x['config_identity'] for x in out})==51
 return out

MISSING=[dict(build_id=x,status='NOT_TESTED',admission='EXCLUDED',reason='No frozen independently checked combination; no new combination replayed') for x in (
 'A7_S1_NEXT_OPEN','A1_NEXT_OPEN','A2_NEXT_OPEN','A3_NEXT_OPEN','A4_NEXT_OPEN','A5_NEXT_OPEN','A6_WITHOUT_S1_NEXT_OPEN','A7_WITHOUT_S1_NEXT_OPEN',
 'S1_WITHOUT_A6_NEXT_OPEN','S2_NEXT_OPEN','S3_NEXT_OPEN','I1_NEXT_OPEN','I2_NEXT_OPEN','I3_NEXT_OPEN','T2_NEXT_OPEN','TRAIL_375_SIGNAL_CLOSE','SESSION_FORCE_FLAT_HOLDING_PROTOCOL')]
DIAGNOSTIC=[dict(build_id=x,status='DIAGNOSTIC_ONLY',admission='EXCLUDED',reason='Post-trade classification or economic haircut; not an executable frozen strategy') for x in (
 'HOLDING_SAME_DATE','HOLDING_CROSS_MIDNIGHT','ROBUSTNESS_R_HAIRCUT_005','ROBUSTNESS_R_HAIRCUT_010','POST_TRADE_WINNER_REMOVAL')]
