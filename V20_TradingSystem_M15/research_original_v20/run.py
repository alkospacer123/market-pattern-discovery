from pathlib import Path
import numpy as np,pandas as pd,hashlib,json
import base as b
R=Path(__file__).resolve().parent
M=['PAUSE_REACCEL','BREAK_HOLD','PREVDAY_VOL_BREAK','COMPRESSION_EXPAND','SHALLOW_PULLBACK','OBV_PRESSURE','H1_BODY_ACCEL','MORNING_RETEST','TWO_STAGE_VOL','CLOSE_IMPULSE_RETAKE']
b.MODES=M

def sig(cond,long,short): return np.select([cond & long,cond & short],[1,-1],default=0).astype('int8')

def signals(s):
 d=b.prepare(s);o,h,l,c,v=[d[z].astype(float) for z in ['Open','High','Low','Close','Volume']];a=d.atr
 r=h-l;body=c-o;cr=r.replace(0,np.nan);tr=pd.concat([r,(h-c.shift(1)).abs(),(l-c.shift(1)).abs()],axis=1).max(axis=1)
 up=(d.ema50>d.ema200)&(d.ema50>d.ema50.shift(4));dn=(d.ema50<d.ema200)&(d.ema50<d.ema50.shift(4));time=d.mins.between(600,1020)
 vmax=v.shift(1).rolling(20,min_periods=20).mean();hi6=h.shift(1).rolling(6,min_periods=6).max();lo6=l.shift(1).rolling(6,min_periods=6).min()
 # Strong impulse on bar t-3, then t-2 and t-1 pause, current engulf continuation
 thrust=body.shift(3);postr=pd.concat([r.shift(2),r.shift(1)],axis=1).max(axis=1)
 d[M[0]]=sig(time & (postr<.95*a.shift(1)) & (v>=.75*vmax),up&(thrust>1.0*a.shift(3))&(l.shift(2)>o.shift(3)-.6*a.shift(3))&(l.shift(1)>o.shift(3)-.6*a.shift(3))&(c>h.shift(3))&(c>o),dn&(thrust< -1.0*a.shift(3))&(h.shift(2)<o.shift(3)+.6*a.shift(3))&(h.shift(1)<o.shift(3)+.6*a.shift(3))&(c<l.shift(3))&(c<o))
 # previous bar breakout and today's bar holds price level, rebreaks previous extreme
 levhi=h.shift(2).rolling(12,min_periods=12).max();levlo=l.shift(2).rolling(12,min_periods=12).min()
 d[M[1]]=sig(time & (r>.45*a),up&(c.shift(1)>levhi)&(l>=levhi-.2*a)&(c>h.shift(1))&(body>.25*a),dn&(c.shift(1)<levlo)&(h<=levlo+.2*a)&(c<l.shift(1))&(body<-.25*a))
 # previous COMPLETE day from prepare; daily is full [10:00..17:45], body ratio is normalized ATR
 yd_range=(d.y_dh-d.y_dl).replace(0,np.nan)
 y_up=(d.y_dc-d.y_do)/yd_range>.6; y_dn=(d.y_dc-d.y_do)/yd_range<-.6
 ful=d.y_full.fillna(False).astype(bool)
 d[M[2]]=sig(time&(d.mins>=660)&ful&(tr>.8*a),up&y_up&(c>d.y_dh)&(c.shift(1)<=d.y_dh)&(body>.4*a),dn&y_dn&(c<d.y_dl)&(c.shift(1)>=d.y_dl)&(body<-.4*a))
 # narrow preceding 8bar range / ATR at t-1, fresh full-body current breakout
 r8=h.shift(1).rolling(8,min_periods=8).max()-l.shift(1).rolling(8,min_periods=8).min()
 d[M[3]]=sig(time&(r8<2.4*a.shift(1))&(r>1.05*a)&(v>=1.1*vmax),up&(c>hi6)&(body>.6*a),dn&(c<lo6)&(body<-.6*a))
 # 8 bar prior imp (ends before the 3-bar pause), with the 3-bar pause distance restrained
 prior_drive=c.shift(3)-c.shift(11); min3=l.shift(1).rolling(3,min_periods=3).min();max3=h.shift(1).rolling(3,min_periods=3).max()
 d[M[4]]=sig(time & (r>.5*a),up&(prior_drive>1.8*a.shift(3))&(min3>c.shift(3)-.85*a)&(c>max3)&(body>.2*a),dn&(prior_drive< -1.8*a.shift(3))&(max3<c.shift(3)+.85*a)&(c<min3)&(body<-.2*a))
 # cumulative signed volume of previous 12 bars 
 clv=((c-l)-(h-c))/cr
 flow=clv.fillna(0)*v
 cmfr=flow.shift(1).rolling(12,min_periods=12).sum()/v.shift(1).rolling(12,min_periods=12).sum().replace(0,np.nan)
 d[M[5]]=sig(time&(v>=vmax)&(r>.65*a),up&(cmfr>.35)&(c>h.shift(1).rolling(10).max())&(body>.3*a),dn&(cmfr<-.35)&(c<l.shift(1).rolling(10).min())&(body<-.3*a))
 # Full H1 candle from LAST FOUR M15 bars: t is :45, bars timestamp are :00 :15 :30 :45; check adjacency
 end=(d.Datetime.dt.minute==45)&time
 fullhour=(d.Datetime-d.Datetime.shift(3)==pd.Timedelta(minutes=45))&(d.Datetime.shift(3).dt.minute==0)
 h_body=c-o.shift(3);prh_body=c.shift(4)-o.shift(7); pre_hour_full=(d.Datetime.shift(4)-d.Datetime.shift(7)==pd.Timedelta(minutes=45))&(d.Datetime.shift(7).dt.minute==0)
 d[M[6]]=sig(end&fullhour&pre_hour_full&(v.rolling(4).sum()>v.shift(4).rolling(4).sum()),up&(h_body>1.05*a)&(h_body>1.25*prh_body)&(c>h.shift(1).rolling(4).max()),dn&(h_body< -1.05*a)&(h_body<1.25*prh_body)&(c<l.shift(1).rolling(4).min()))
 # Morning first 10-11 complete; use only after 11am
 mo=d.m_full.fillna(False).astype(bool)&d.mins.between(720,945)
 # after touching firsthour breakout back within it 1 bar ago, then reclaim prior hour high
 d[M[7]]=sig(mo&(r>.5*a),up&(d.m_fc-d.m_fo>1.0*a)&(l.shift(1)<d.m_fh)&(c.shift(1)<d.m_fh)&(c>d.m_fh)&(body>.4*a),dn&(d.m_fo-d.m_fc>1.0*a)&(h.shift(1)>d.m_fl)&(c.shift(1)>d.m_fl)&(c<d.m_fl)&(body<-.4*a))
 # relative recent ATR of TR to 48 bars earlier, precursor quiet, current high-energy
 atr12=tr.shift(1).rolling(12,min_periods=12).mean();oldatr=tr.shift(13).rolling(36,min_periods=36).mean()
 d[M[8]]=sig(time&(atr12<.7*oldatr)&(tr>1.5*atr12)&(v>vmax),up&(c>hi6)&(body>.65*a),dn&(c<lo6)&(body<-.65*a))
 # prior strong candle 2 bars ago, 1-bar small pause, current restarts
 d[M[9]]=sig(time&(d.mins>=840)&(r.shift(1)<.8*a.shift(1))&(v>=.85*vmax),up&(body.shift(2)>1.15*a.shift(2))&(c>h.shift(1))&(c>h.shift(2))&(body>.35*a),dn&(body.shift(2)< -1.15*a.shift(2))&(c<l.shift(1))&(c<l.shift(2))&(body<-.35*a))
 for m in M:
  d[m+'_target']=np.nan;d[m+'_tpr']=np.nan
 return d

def run():
 D={};u=set();h={};trs=[];cnt=[];op={}
 for sym in b.SYMS:
  d=signals(sym);D[sym]=d;u.update(d.loc[d.mins.between(600,1020),'day'].dt.strftime('%Y-%m-%d'));h[sym]=hashlib.sha256((R/'marketdata_m15'/f'{sym}_M15.csv').read_bytes()).hexdigest();print('loaded',sym,len(d),flush=True)
 for m in M:
  t,opened=b.merged(D,m);op[m]=len(opened);cnt.extend([{'model':m,'symbol':s,'signals':int((D[s][m]!=0).sum())} for s in b.SYMS]);print(m,'closed',len(t),'unclosed',len(opened),flush=True)
  if not t.empty:trs.append(t)
 alltr=pd.concat(trs,ignore_index=True)
 summary,daily,monthly,symbol=b.stats(alltr,sorted(u))
 for n,z in [('trades',alltr),('summary',summary),('daily',daily),('monthly',monthly),('by_symbol',symbol),('signals',pd.DataFrame(cnt))]:z.to_csv(R/f'{n}.csv',index=False)
 (R/'LINEAGE.json').write_text(json.dumps({'source_sha256':h,'protocol_sha256':hashlib.sha256((R/'PROTOCOL_RU.md').read_bytes()).hexdigest(),'terminal_open':op,'independent_OOS':False},ensure_ascii=False,indent=2))
 print(summary[summary.period.isin(['2023','2024','2025','2026'])].pivot(index='model',columns='period',values='PF').round(3).to_string(),flush=True)
 print(summary[summary.period.eq('LATE')][['model','closed','PF','avg_entries_day','pct_days_zero','pct_days_1or2']].round(3).to_string(index=False),flush=True)
if __name__=='__main__':run()
