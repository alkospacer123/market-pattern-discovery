"""Separate stdlib feature/replay and scalar table audit. No primary imports."""
import argparse,csv,json,math,statistics,sys
from pathlib import Path
from datetime import timedelta
from collections import deque
HERE=Path(__file__).resolve().parent
REF=HERE.parent/'t3_m15_t1_s1_v1'
sys.dont_write_bytecode=True;sys.path.insert(0,str(REF))
import independent as C
import independent_combination as IC
SYMBOLS=list(C.SYMBOLS)
FKEYS=['H1ADX','dADX','H1ATRRatio','dATRRatio','signed_slope_ATR','volatility_pct','breakout_ATR','close_location','hour']
def read(p):
    with p.open() as f:return list(csv.DictReader(f))
def mean(v):
    q=[x for x in v if x is not None and math.isfinite(x)];return sum(q)/len(q) if q else None
def ratio(a,b):return a/b if b else None
def features(raw):
    built=C.build_features(raw);day=None;block=[];ha=C.Recursive(1/14,14);prev=None;closes=[];extra={};result=[];oldreg=None;previous_r=None
    for b in built:
        at=b['at']
        if day!=at.date():day=at.date();block=[]
        block.append(b)
        if len(block)==4:
            if all(block[i]['at']-block[i-1]['at']==C.STEP for i in range(1,4)):
                hb={'h':max(x['h'] for x in block),'l':min(x['l'] for x in block),'c':b['c']}
                av=ha.push(C.true_range(hb,prev['c'] if prev else None));prev=hb
                closes.append(b['c'])
                eff=None
                if len(closes)>5:
                    dist=sum(abs(closes[j]-closes[j-1]) for j in range(len(closes)-5,len(closes)))
                    eff=abs(closes[-1]-closes[-6])/dist if dist else None
                extra={'H1ATR':av,'efficiency5':eff}
            block=[]
        h=b['h1'];ph=b['previous_h1'];m=at.hour+at.minute/60
        r=dict(b);r.update(year=at.year,month=at.strftime('%Y-%m'),mmdd=at.strftime('%m-%d'),date=at.strftime('%Y-%m-%d'),hour=m,core=10<=m<18)
        r.update(H1ADX=h['adx'] if h else C.NAN,H1Slope=h['slope'] if h else C.NAN,H1ATRRatio=h['ratio'] if h else C.NAN,H1EMA=h['ema'] if h else C.NAN,H1Close=h['c'] if h else C.NAN,
                 H1ATR=extra.get('H1ATR',C.NAN),efficiency5=extra.get('efficiency5'),dADX=h['adx']-ph['adx'] if h and ph else C.NAN,dATRRatio=h['ratio']-ph['ratio'] if h and ph else C.NAN)
        r['ready']=all(math.isfinite(v) for v in [b['atr'],b['upper'],b['lower'],r['H1ADX'],r['H1Slope'],r['H1ATRRatio'],r['H1EMA']])
        r['base_regime']=1 if r['H1ADX']>20 and r['H1Close']>r['H1EMA'] and r['H1Slope']>0 else -1 if r['H1ADX']>20 and r['H1Close']<r['H1EMA'] and r['H1Slope']<0 else 0
        r['regime']=r['base_regime'] if r['H1ATRRatio']>1 else 0
        r['raw_breakout']=1 if b['c']>b['upper'] else -1 if b['c']<b['lower'] else 0
        r['volatility_pct']=100*b['atr']/b['c'];r['abs_slope_ATR']=abs(r['H1Slope'])/r['H1ATR']
        r['h1_published']=bool(h and h['at']==at);r['regime_flip']=False;r['regime_change']=False
        if r['h1_published']:
            r['regime_flip']=oldreg is not None and r['regime']*oldreg<0;r['regime_change']=oldreg is not None and r['regime']!=oldreg;oldreg=r['regime']
        r['zero_episode_start']=bool(r['ready'] and r['core'] and r['regime']==0 and (previous_r is None or not(previous_r['ready'] and previous_r['core']) or previous_r['regime']!=0 or previous_r['date']!=r['date'] or r['at']-previous_r['at']!=C.STEP))
        previous_r=r
        result.append(r)
    sets={y:{b['mmdd'] for b in result if b['year']==y and b['ready'] and b['core']} for y in [2023,2024]}
    common=sets[2023]&sets[2024]
    for b in result:b['matched']=b['mmdd'] in common
    return built,result,common

def events(bars,s):
    out=[]
    for i,b in enumerate(bars):
        sign=b['raw_breakout']
        if not sign or not b['ready']:continue
        window=bars[i+1:i+5]
        valid=len(window)==4 and window[-1]['at']==b['at']+timedelta(minutes=60) and all(x['at'].date()==b['at'].date() for x in window)
        r={'instrument':s,'signal_time':b['at'],'year':b['year'],'month':b['month'],'direction':'LONG' if sign>0 else 'SHORT','eligible_signal':bool(b['signal']),'core':b['core'],'matched':b['matched'],'window_complete':valid,
           'no_continuation':None,'return_behind_level':None,'repeat_after_failure':None,'reverse_after_failure':None}
        if valid:
            level=b['upper'] if sign>0 else b['lower']
            f=max(sign*(x['h' if sign>0 else 'l']-b['c']) for x in window)/b['atr']
            r['no_continuation']=f<1
            r['return_behind_level']=any(sign*(x['c']-level)<=0 for x in window)
            nxt=bars[i+5:i+9]
            known=len(nxt)==4 and nxt[-1]['at']==b['at']+timedelta(minutes=120) and all(x['at'].date()==b['at'].date() for x in nxt)
            if f<1 and known:
                signs=[x['raw_breakout'] for x in nxt if x['raw_breakout']]
                r['repeat_after_failure']=bool(signs and signs[0]==sign);r['reverse_after_failure']=bool(signs and signs[0]==-sign)
        out.append(r)
    return out

def stat(t):
    q=sorted(t,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    x=[r['gross_R'] for r in q];win=[v for v in x if v>0];loss=[v for v in x if v<0]
    pos=sum(win);neg=-sum(loss);total=sum(x);n=len(q)
    eq=peak=dd=0.
    for v in x:eq+=v;peak=max(peak,eq);dd=max(dd,peak-eq)
    a={'closed':n,'gross_PF':ratio(pos,neg),'gross_R':total,'positive_R':pos,'negative_R':neg,'expectancy_R':ratio(total,n),'DD_closed_R':dd,
       'wins':len(win),'losses':len(loss),'win_share':ratio(len(win),n),'mean_win_R':mean(win),'mean_loss_R':mean(loss),
       'holding_mean_minutes':mean([r['holding_minutes'] for r in q]),'holding_median_minutes':statistics.median([r['holding_minutes'] for r in q]) if q else None,
       'bars_mean':mean([r['bars_held'] for r in q]),'S1_count':sum(r['threshold_activated'] for r in q),
       'initial_without_S1':sum(r['exit_type']=='INITIAL_STOP' and not r['threshold_activated'] for r in q),
       'failed_entries':sum(r['MFE_R']<.5 and r['gross_R']<0 for r in q),'failed_loss_R':-sum(r['gross_R'] for r in q if r['MFE_R']<.5 and r['gross_R']<0),
       'loss_R_after_MFE1':-sum(r['gross_R'] for r in q if r['MFE_R']>=1 and r['gross_R']<0),'MFE2_then_loss':sum(r['MFE_R']>=2 and r['gross_R']<0 for r in q),
       'gap_exits':sum(r['gap_exit'] for r in q),'cross_day':sum(r['cross_calendar_day'] for r in q),'GE2_count':sum(v>=2 for v in x),'GE2_R':sum(v for v in x if v>=2),
       'GE5_count':sum(v>=5 for v in x),'GE5_R':sum(v for v in x if v>=5),'MFE_mean':mean([r['MFE_R'] for r in q]),'MAE_mean':mean([r['MAE_R'] for r in q])}
    for k in ['S1_count','initial_without_S1','failed_entries']:a[k+'_share']=ratio(a[k],n)
    for v in [.5,1,2]:a[f'MFE_ge_{v}_share']=ratio(sum(r['MFE_R']>=v for r in q),n)
    wins=sorted(win,reverse=True)
    for n in [1,3,5,10]:a[f'top{n}_R']=sum(wins[:n]);a[f'top{n}_share_positive_R']=ratio(sum(wins[:n]),pos)
    for k in FKEYS:a['mean_'+k]=mean([r[k] for r in q])
    return a

def chosen(t,row):
    col='exit_time' if row['basis']=='EXIT' else 'entry_time';period=row['period'];out=[]
    for r in t:
        stamp=r[col].isoformat()
        if period=='2024Q2':
            if stamp[:7] not in ['2024-04','2024-05','2024-06']:continue
        elif period!='ALL' and not stamp.startswith(period):continue
        if row['scope']=='FX' and r['instrument'] not in SYMBOLS[:2]:continue
        if row['scope'] not in ['ALL','FX',r['instrument']]:continue
        if row['direction'] not in ['ALL',r['direction']]:continue
        if row['cut']!='ALL' and str(r[row['cut']])!=row['value']:continue
        outcome=row['outcome'];v=r['gross_R']
        if outcome=='WIN' and v<=0 or outcome=='LOSS' and v>=0 or outcome=='GE2' and v<2 or outcome=='GE5' and v<5:continue
        out.append(r)
    return out

def market(bars,ev):
    a=[b for b in bars if b['ready'] and b['core']];e=[b for b in ev if b['core']];v=[b for b in e if b['window_complete']];eligible=[b for b in v if b['eligible_signal']]
    known=[b for b in v if b['no_continuation'] and b['repeat_after_failure'] is not None]
    out={'core_ready_bars':len(a),'observed_days':len({b['date'] for b in a}),
      'base_directional_share':mean([b['base_regime']!=0 for b in a]),'tradable_regime_share':mean([b['regime']!=0 for b in a]),'no_tradable_share':mean([b['regime']==0 for b in a]),
      'LONG_regime_share':mean([b['regime']==1 for b in a]),'SHORT_regime_share':mean([b['regime']==-1 for b in a]),
      'mean_ADX':mean([b['H1ADX'] for b in a]),'mean_dADX':mean([b['dADX'] for b in a]),'ADX_rising_share':mean([b['dADX']>0 for b in a]),
      'mean_ATRRatio':mean([b['H1ATRRatio'] for b in a]),'mean_dATRRatio':mean([b['dATRRatio'] for b in a]),'ATRRatio_rising_share':mean([b['dATRRatio']>0 for b in a]),
      'mean_abs_slope_ATR':mean([b['abs_slope_ATR'] for b in a]),'mean_volatility_pct':mean([b['volatility_pct'] for b in a]),'mean_efficiency5':mean([b['efficiency5'] for b in a]),
      'signals':sum(b['signal']!=0 for b in a),'raw_breakouts':len(e),'complete_breakout_windows':len(v),'no_continuation_count':sum(b['no_continuation'] for b in v),
      'no_continuation_share':mean([b['no_continuation'] for b in v]),'return_behind_share':mean([b['return_behind_level'] for b in v]),
      'regime_flips_H1':sum(b['regime_flip'] for b in a),'H1_publications':sum(b['h1_published'] for b in a),'regime_changes_H1':sum(b['regime_change'] for b in a),
      'no_regime_episode_starts':sum(b['zero_episode_start'] for b in a),'no_regime_episodes_per_1000bars':ratio(1000*sum(b['zero_episode_start'] for b in a),len(a)),'eligible_complete_windows':len(eligible),
      'eligible_no_continuation_share':mean([b['no_continuation'] for b in eligible]),'failure_followup_windows':len(known),
      'repeat_after_failure_count':sum(b['repeat_after_failure'] for b in known),'reverse_after_failure_count':sum(b['reverse_after_failure'] for b in known)}
    return out

def run(root,target,output):
    assert output.resolve().is_relative_to(HERE);output.mkdir(parents=True,exist_ok=True)
    frames,sources=C.load_sources(root);comp=C.Comparison()
    tt=[];ss=[];ee=[];gg=[];oo=[];sn=[];bars=[];ev=[];hlogs=[];coverage=[];matched=[]
    for src in sources:
        s=src['instrument'];raw,_=C.parse_prefix(root/src['path']);built,feat,common=features(raw)
        t,o,d,e,g,n=IC.simulate(built,s,'OPTIMIZED','COMBINED');tt+=t;ss+=d;ee+=e;gg+=g;sn+=n
        if o:oo.append(o)
        bytime={b['at']:b for b in feat}
        for r in t:
            b=bytime[r['entry_time']];h=b['h1'];ph=b['previous_h1'];sign=1 if r['direction']=='LONG' else -1
            r.update(dADX=b['dADX'],dATRRatio=b['dATRRatio'],signed_slope_ATR=sign*h['slope']/b['H1ATR'],volatility_pct=b['volatility_pct'],breakout_ATR=sign*(b['c']-r['breakout_level'])/b['atr'],
                     close_location=(b['c']-b['l'] if sign>0 else b['h']-b['c'])/(b['h']-b['l']) if b['h']>b['l'] else None,hour=b['hour'],matched=b['matched'],A6=b['dATRRatio']>0,
                     ADX_rising=b['dADX']>0,slope_strengthening=abs(h['slope'])>abs(ph['slope']),M15_ATR_rising=b['atr']>b['previous_atr'],hour_bin='10-12' if b['hour']<12 else '12-15' if b['hour']<15 else '15-18')
        for b in feat:
            b['instrument']=s
            if b['h1_published']:hlogs.append({'instrument':s,'close_time':b['at'],**{k:b[k] for k in ['H1ADX','dADX','H1ATRRatio','dATRRatio','H1ATR','H1EMA','H1Close','H1Slope','efficiency5','base_regime','regime','regime_flip']}})
        bars+=feat;ev+=events(feat,s);matched.extend({'instrument':s,'mmdd':v} for v in sorted(common))
        for y in [2023,2024]:
            q=[b for b in feat if b['year']==y];gaps=[(p,b) for p,b in zip(q,q[1:]) if b['at']-p['at']>C.STEP]
            coverage.append({'instrument':s,'year':y,'M15_bars':len(q),'first_close':q[0]['at'],'last_close':q[-1]['at'],'observed_Close_days':len({b['date'] for b in q}),
                'ready_core_days':len({b['date'] for b in q if b['ready'] and b['core']}),'H1_valid_blocks':sum(b['h1_published'] for b in q),'H1_ready_core_bars':sum(b['ready'] and b['core'] for b in q),
                'within_date_gaps_gt15':sum(p['date']==b['date'] for p,b in gaps),'cross_date_gaps':sum(p['date']!=b['date'] for p,b in gaps),'matched_MMDD_days':len(common)})
    for name,rows,keys in [('trades.csv',tt,['instrument','entry_time']),('trade_diagnostics.csv',tt,['instrument','entry_time']),('stop_decisions.csv',ss,['instrument','bar_close_time']),('entry_opportunities.csv',ee,['instrument','signal_time']),('observed_gaps.csv',gg,['instrument','current_close']),('h1_features.csv',hlogs,['instrument','close_time']),('breakout_diagnostics.csv',ev,['instrument','signal_time']),('coverage.csv',coverage,['instrument','year']),('matched_dates.csv',matched,['instrument','mmdd'])]:
        comp.rows(rows,read(target/name),name,keys)
    for name,rows,keys in [('OPEN_POSITIONS.json',oo,['instrument']),('PERIOD_END_OPEN_POSITIONS.json',sn,['instrument','month'])]:comp.rows(rows,json.loads((target/name).read_text()),name,keys)
    expected={'yearly.csv':54,'monthly.csv':432,'entry_quality.csv':450,'causal_cuts.csv':198,'matched_coverage_trades.csv':12}
    for name,count in expected.items():
        rows=read(target/name);comp.value(len(rows),count,name,0,'row_universe');seen=set()
        for i,row in enumerate(rows):
            key=tuple(row[k] for k in ['basis','period','scope','direction','cut','value','outcome']);assert key not in seen;seen.add(key)
            q=chosen(tt,row);a=stat(q)
            if name=='monthly.csv':
                comp.value('NO_COVERAGE' if row['scope'] in SYMBOLS and not any(b['instrument']==row['scope'] and b['month']==row['period'] for b in bars) else 'AVAILABLE',row['coverage'],name,i,'coverage')
                for s in SYMBOLS:a['R_'+s]=sum(r['gross_R'] for r in q if r['instrument']==s)
                for side in ['LONG','SHORT']:a['R_'+side]=sum(r['gross_R'] for r in q if r['direction']==side)
            if name=='yearly.csv':
                months={}
                for r in q:m=r['exit_time'].strftime('%Y-%m');months[m]=months.get(m,0)+r['gross_R']
                values=list(months.values());positives=sum(v for v in values if v>0);best=max(values) if values else None;top3=sum(sorted(values,reverse=True)[:3])
                a.update(positive_months=sum(v>0 for v in values),calendar_months=24 if row['period']=='ALL' else 12,best_month_R=best,top3_months_R=top3,
                         best_month_share_GrossR=ratio(best,a['gross_R']) if best is not None else None,top3_months_share_GrossR=ratio(top3,a['gross_R']),
                         best_month_share_positive_month_R=ratio(best,positives) if best is not None else None,top3_months_share_positive_month_R=ratio(top3,positives))
            for k,v in a.items():comp.value(v,row[k],name,i,k)
    rows=read(target/'entry_feature_distributions.csv');comp.value(len(rows),810,'entry_feature_distributions',0,'row_universe')
    for i,row in enumerate(rows):
        q=chosen(tt,row|{'cut':'ALL','value':'ALL'});x=sorted(r[row['feature']] for r in q if r[row['feature']] is not None and math.isfinite(r[row['feature']]))
        def percentile(p):
            if not x:return None
            loc=p*(len(x)-1);j=int(loc);return x[j]+(loc-j)*(x[min(j+1,len(x)-1)]-x[j])
        a={'count':len(x),'min':min(x) if x else None,'p25':percentile(.25),'median':percentile(.5),'p75':percentile(.75),'max':max(x) if x else None}
        for k,v in a.items():comp.value(v,row[k],'entry_feature_distributions',i,k)
    rows=read(target/'breakout_direction.csv');comp.value(len(rows),52,'breakout_direction',0,'row_universe')
    for i,row in enumerate(rows):
        q=[r for r in ev if r['core'] and r['month'].startswith(row['period']) and r['direction']==row['direction']];v=[r for r in q if r['window_complete']];e=[r for r in v if r['eligible_signal']]
        a={'raw_core_breakouts':len(q),'complete_windows':len(v),'raw_no_continuation_share':mean([r['no_continuation'] for r in v]),'eligible_complete_windows':len(e),
           'eligible_no_continuation_share':mean([r['no_continuation'] for r in e]),'eligible_return_behind_share':mean([r['return_behind_level'] for r in e])}
        for k,v in a.items():comp.value(v,row[k],'breakout_direction',i,k)
    rows=read(target/'market_regime.csv');comp.value(len(rows),312,'market_regime',0,'row_universe')
    for i,row in enumerate(rows):
        scope=row['scope'];period=row['period'];mode=row['coverage_mode']
        filt=lambda b:b['month'].startswith(period) and (scope=='ALL' or scope=='FX' and b['instrument'] in SYMBOLS[:2] or b['instrument']==scope) and (mode=='FULL' or b['matched'])
        a=market([b for b in bars if filt(b)],[b for b in ev if filt(b)])
        for k,v in a.items():comp.value(v,row[k],'market_regime',i,k)
    rows=read(target/'signal_funnel.csv');comp.value(len(rows),468,'signal_funnel',0,'row_universe')
    for i,row in enumerate(rows):
        a=[r for r in ee if r['signal_time'].isoformat().startswith(row['period']) and (row['scope']=='ALL' or row['scope']=='FX' and r['instrument'] in SYMBOLS[:2] or r['instrument']==row['scope']) and row['direction'] in ['ALL',r['direction']]]
        fields={'signals_all_hours':len(a),'signals_T1':sum(r['rule_pass'] for r in a),'accepted_including_OPEN':sum(r['entry_accepted'] for r in a),'T1_busy':sum(r['rule_pass'] and r['position_occupied'] for r in a),
                'outside_T1':sum(not r['rule_pass'] for r in a),'same_close_reentry':sum(r['entry_accepted'] and r['same_close_exit_trade_id'] is not None for r in a)}
        for k,v in fields.items():comp.value(v,row[k],'signal_funnel',i,k)
    comp.rows([r for r in tt if r['gross_R']>=2],read(target/'large_winners.csv'),'large_winners',['instrument','entry_time'])
    # Read-only economic transcription of previous A6 full replays.
    hist=read(HERE.parent/'t3_m15_entry_regime_v1/results/trades.csv');rows=read(target/'historical_A6.csv')
    for i,row in enumerate(rows):
        x=[float(r['gross_R']) for r in hist if r['version']=='OPTIMIZED' and r['rule']==row['rule'] and r['exit_time'].startswith(row['period'])]
        for k,v in {'closed':len(x),'gross_R':sum(x),'gross_PF':ratio(sum(v for v in x if v>0),-sum(v for v in x if v<0))}.items():comp.value(v,row[k],'historical_A6',i,k)
    C.write_csv(output/'DISCREPANCIES.csv',comp.diffs,['table','row','field','actual','expected'])
    result={'status':'PASS' if not comp.diffs else 'FAIL','fields_compared':comp.fields,'discrepancies':len(comp.diffs),'numeric_tolerance':1e-8,'closed':len(tt),'terminal_OPEN':len(oo),'H1_rows':len(hlogs),'breakouts':len(ev),'tables':comp.tables,
        'maximum_numeric_delta':max(comp.maxima.values()),'implementation':'stdlib scalar #500 features/replay + separately written scalar aggregation; no primary diagnostic imports','human_independent_review':'PENDING','data_commit':C.DATA_SHA,'future_OHLC_parsed':False,'labels':C.LABEL}
    C.write_json(output/'AUDIT_RESULT.json',result)
    print(json.dumps({k:result[k] for k in ['status','fields_compared','discrepancies','maximum_numeric_delta']}));assert not comp.diffs,comp.diffs[:3]

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True);p.add_argument('--target',type=Path,default=HERE/'results');p.add_argument('--output',type=Path,default=HERE/'audit');a=p.parse_args();run(a.data_root,a.target,a.output)
