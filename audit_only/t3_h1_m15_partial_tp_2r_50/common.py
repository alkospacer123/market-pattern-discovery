"""Serialization and position accounting only; no strategy or broker dependencies."""
import csv, gzip, hashlib, io, json, math, subprocess
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path
from datetime import datetime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SYMBOLS=('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF')
TICKS=dict(USDRUBF='.01',CNYRUBF='.001',GLDRUBF='.1',IMOEXF='.5')
BASE='38489db7e69336548a583f968f13aab49c20913b'
H1_DATA='50f1fd2178c18b7ab3bd969be82ad01f47a34745'
M15_DATA='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
PROTOCOL_COMMIT='4b61ca35ab8e6903bc6d330a2569e1f523c8fafe'
PR540_HEAD='8b2c23fdf2960a201b086c4ad69d07ac1bfd8257'

def git(*args,root=ROOT): return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def clean(x):
    if isinstance(x,datetime): return x.isoformat()
    if isinstance(x,float) and not math.isfinite(x): return None
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [clean(v) for v in x]
    return x
def js(path,obj): Path(path).write_text(json.dumps(clean(obj),indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n')
def csvout(path,rows,fields=None):
    fields=fields or list(dict.fromkeys(k for r in rows for k in r))
    buf=io.StringIO(newline='');w=csv.DictWriter(buf,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(clean(r) for r in rows)
    raw=buf.getvalue().encode();Path(path).write_bytes(gzip.compress(raw,mtime=0) if str(path).endswith('.gz') else raw)
def csvin(path):
    raw=Path(path).read_bytes()
    if str(path).endswith('.gz'):raw=gzip.decompress(raw)
    return list(csv.DictReader(io.StringIO(raw.decode())))

def target(entry,initial,side,tick):
    e,s,t=map(lambda v:Decimal(str(v)),(entry,initial,tick));raw=e+side*2*abs(e-s)
    return float((raw/t).to_integral_value(rounding=ROUND_CEILING if side==1 else ROUND_FLOOR)*t)
def partial_quantity(qty,integer=False):
    if integer:
        assert qty>=0 and int(qty)==qty
        return qty//2
    return qty/2

def new_position(system,symbol,life,fold,tid,at,entry,initial,side,variant,index):
    risk=abs(entry-initial);assert risk>0
    return dict(system=system,instrument=symbol,lifecycle=life,fold_id=fold,trade_id=tid,
        variant=variant,model='FRACTIONAL_REFERENCE',direction='LONG' if side==1 else 'SHORT',
        entry_time=at,entry_price=entry,initial_stop_price=initial,initial_risk_price=risk,
        target_price=target(entry,initial,side,TICKS[symbol]),price_step=float(TICKS[symbol]),
        initial_quantity=1.,part1_quantity=.5,part2_quantity=.5,
        part1_exit_time=None,part1_exit_price=None,part1_gross_R=None,part1_reason=None,
        part2_exit_time=None,part2_exit_price=None,part2_gross_R=None,part2_reason=None,
        reached_2R=False,partial_executed=False,ambiguous_stop_tp_bars=0,
        status='OPEN',_side=side,_stop=initial,_extreme=entry,_index=index,_held=0,
        _realized=0.,_remaining=1.,_triggered=False,_activated=False,_stored=None,
        trigger_bar_time=None,trail1_activation_time=None,candidate_already_looser=False,
        gap_through_activated_trail=False)

def fill_part(p,part,at,price,reason):
    assert p[f'part{part}_exit_time'] is None
    qty=p[f'part{part}_quantity'];r=qty*p['_side']*(price-p['entry_price'])/p['initial_risk_price']
    p.update({f'part{part}_exit_time':at,f'part{part}_exit_price':price,f'part{part}_gross_R':r,f'part{part}_reason':reason})
    p['_remaining']-=qty;p['_realized']+=r
    assert p['_remaining']>=0

def protect_and_tp(p,b):
    """Old stop first; zero retroactive TP on an ambiguous bar."""
    side=p['_side'];stop=p['_stop'];opening=side*(b['Open']-stop)<=0
    hit=opening or (b['Low']<=stop if side==1 else b['High']>=stop)
    touched=b['High']>=p['target_price'] if side==1 else b['Low']<=p['target_price']
    p['reached_2R'] |= (b['High']>=p['entry_price']+2*p['initial_risk_price'] if side==1 else b['Low']<=p['entry_price']-2*p['initial_risk_price'])
    if hit and touched and not p['partial_executed']:p['ambiguous_stop_tp_bars']+=1
    if hit:
        price=b['Open'] if opening else stop
        reason='INITIAL_STOP' if stop==p['initial_stop_price'] else 'ATR_TRAILING_STOP'
        for part in (1,2):
            if p[f'part{part}_exit_time'] is None:fill_part(p,part,b['at'],price,reason)
        p.update(status='CLOSED',exit_time=b['at'],exit_price=price,exit_reason=reason,
            gross_R=p['_realized'],cost_R=.002/p['initial_risk_price'] if p['system']=='H1' else None,
            net_R_C1=p['_realized']-.002/p['initial_risk_price'] if p['system']=='H1' else None,
            active_stop_at_exit=stop,exit_at_open=bool(opening),gap_exit=price!=stop)
        p['gap_through_activated_trail']=bool(p['_activated'] and price!=stop)
        return True
    if touched and p['variant']=='PARTIAL_TP_2R_50' and not p['partial_executed']:
        fill=max(b['Open'],p['target_price']) if side==1 else min(b['Open'],p['target_price'])
        assert b['Low']<=fill<=b['High'],'TP_FILL_OUTSIDE_OBSERVED_RANGE'
        fill_part(p,1,b['at'],fill,'PARTIAL_TP_2R_50');p['partial_executed']=True
    return False

def public(p):
    result={k:v for k,v in p.items() if not k.startswith('_')}
    result.update(remaining_quantity=p['_remaining'],active_stop=p['_stop'],
                  trail1_triggered=p['_triggered'],trail1_activated=p['_activated'],stored_trail_candidate=p['_stored'])
    for part in (1,2):
        # Original normalized C1 only, never broker commissions.
        result[f'part{part}_entry_C1_R']=.0005/p['initial_risk_price'] if p['system']=='H1' else None
        result[f'part{part}_exit_C1_R']=.0005/p['initial_risk_price'] if p['system']=='H1' and p[f'part{part}_exit_time'] else None
        result[f'part{part}_status']='CLOSED' if p[f'part{part}_exit_time'] else 'OPEN'
        result[f'part{part}_unrealized_gross_R']=0. if p[f'part{part}_exit_time'] else .5*p['_side']*(p['last_mark_price']-p['entry_price'])/p['initial_risk_price']
        result[f'part{part}_broker_commission_RUB']=None
        result[f'part{part}_broker_slippage_RUB']=None
    result['cost_validation']='C1_NORMALIZED_ONLY_NO_BROKER_COSTS' if p['system']=='H1' else 'GROSS_ONLY'
    return result

def mark(p,b,realized,c1):
    floating=p['_remaining']*p['_side']*(b['Close']-p['entry_price'])/p['initial_risk_price'] if p else 0.
    return dict(at=b['at'],gross_realized_R=realized,gross_unrealized_R=floating,gross_MTM_R=realized+floating,
                C1_normalized_paid_R=c1,C1_normalized_MTM_R=realized+floating-c1,
                active_trade_id=p['trade_id'] if p else None,remaining_quantity=p['_remaining'] if p else 0.)
