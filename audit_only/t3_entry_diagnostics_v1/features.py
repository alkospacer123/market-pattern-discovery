"""Signal-time only features. No trade journals/outcomes are read here."""
import io, math, subprocess
from datetime import timedelta
import numpy as np
import pandas as pd
from support import *

CUTOFF = pd.Timestamp('2025-01-01',tz='Europe/Moscow')
START = pd.Timestamp('2023-01-01',tz='Europe/Moscow')
FEATURES_COMMON = ('breakout_atr','range_atr','body_abs_atr','body_signed_atr',
 'close_location','directional_close_location','atr','atr_ratio_cross_day',
 'prior_move4_atr_cross_day','prior_move20_atr_cross_day','prior_pullback20_atr_cross_day')
FEATURES_H1 = ('price_h1_ema100_atr','h1_slope5_atr','h1_adx','price_context_ema_atr',
 'context_adx','context_slope_atr','context_atr','context_atr_ratio','context_age_minutes')
FEATURES_M15 = ('price_context_ema_atr','price_context_ema_context_atr',
 'context_adx','context_slope_atr','context_atr','context_atr_ratio','context_age_minutes',
 'session_minutes','signal_hour_msk')

def prefix_frame(system,symbol):
    """Timestamp-only boundary test before numeric parsing; later fields not ingested."""
    commit='50f1fd2178c18b7ab3bd969be82ad01f47a34745' if system=='H1' else 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
    step=timedelta(minutes=60 if system=='H1' else 15)
    proc=subprocess.Popen(['git','-C',str(DATA),'show',commit+f':forever/{symbol}/{symbol}_{system}.csv'],stdout=subprocess.PIPE)
    header=proc.stdout.readline();lines=[header];last=None;boundary=None
    date_column=header.decode().strip().split(';').index('Datetime')
    for line in proc.stdout:
        stamp=pd.Timestamp(line.decode().split(';')[date_column]).tz_localize('Europe/Moscow')+step
        if stamp>=CUTOFF:
            boundary=stamp.isoformat();break
        assert last is None or stamp>last
        last=stamp;lines.append(line)
    proc.stdout.close();proc.terminate();proc.wait()
    raw=b''.join(lines)
    if system=='H1':
        from TradingSystemLab.core.data_loader import DataLoader
        f=DataLoader.close_index(DataLoader()._read(io.BytesIO(raw)),'1h')
    else:
        f=pd.read_csv(io.BytesIO(raw),sep=';',float_precision='round_trip')
        f.index=pd.DatetimeIndex(pd.to_datetime(f.pop('Datetime'))).tz_localize('Europe/Moscow')+step
        f=f.drop(columns='Ticker')
    assert f.index.max()<CUTOFF
    return f,dict(system=system,instrument=symbol,numeric_rows=len(f),first_close=f.index.min(),
                  last_close=f.index.max(),first_excluded_close=boundary,numeric_2025_2026_rows=0)

def uid(system,life,fold,symbol,at,side):
    return '|'.join((system,life,fold,symbol,at.isoformat(),'LONG' if side==1 else 'SHORT'))

def features_for_frame(system,symbol,life,fold,raw,engine):
    from TradingSystemLab.core.data_loader import DataLoader
    from TradingSystemLab.core.indicators import ema,adx,atr
    if system=='H1':
        strategy=engine.T3MTFTrend(engine.T3Parameters(stop_atr=2.5))
        low,high=strategy.calculate_indicators(raw,DataLoader.h4_from_h1(raw))
        high['Regime']=[strategy.regime(row) for _,row in high.iterrows()]
        regime=high.Regime.reindex(low.index,method='ffill')
        low['Signal']=np.select([(regime=='LONG')&(low.Close>low.PriorHigh),
                                 (regime=='SHORT')&(low.Close<low.PriorLow)],[1,-1],default=0)
        low['H1EMA100']=ema(low.Close,100)
        low['H1Slope']=low.H1EMA100-low.H1EMA100.shift(5)
        low['H1ADX']=adx(low)
        for dest,source in [('EMA','EMA100'),('Slope','EMA100Slope'),('ADX','ADX'),('ATR','ATR'),('Close','Close'),('Regime','Regime')]:
            low['Context'+dest]=high[source].reindex(low.index,method='ffill')
        low['ContextATRRatio']=(high.ATR/high.ATRMean20).reindex(low.index,method='ffill')
        low['ContextAvailableAt']=pd.Series(high.index,index=high.index).reindex(low.index,method='ffill')
        bars=[dict(at=at.to_pydatetime(),**row.to_dict()) for at,row in low.iterrows()]
    else:
        bars=engine.m15_module().features(raw)
        low=pd.DataFrame(bars).set_index('at')
        for key in ('EMA','Slope','ADX','ATR','Close','ATRRatio','AvailableAt'):
            low['Context'+key]=low['H1'+key]
    for b in bars: b['Signal']=int(b['Signal'])
    sign=low.Signal
    low['breakout_atr']=np.where(sign==1,(low.Close-low.PriorHigh)/low.ATR,(low.PriorLow-low.Close)/low.ATR)
    low['range_atr']=(low.High-low.Low)/low.ATR
    low['body_abs_atr']=(low.Close-low.Open).abs()/low.ATR
    low['body_signed_atr']=sign*(low.Close-low.Open)/low.ATR
    low['close_location']=(low.Close-low.Low)/(low.High-low.Low).replace(0,np.nan)
    low['directional_close_location']=np.where(sign==1,low.close_location,1-low.close_location)
    low['atr']=low.ATR
    low['atr_ratio_cross_day']=low.ATR/low.ATR.rolling(20).mean()
    for k in (4,20): low[f'prior_move{k}_atr_cross_day']=sign*(low.Close.shift(1)-low.Close.shift(k+1))/low.ATR
    favorable=np.where(sign==1,low.High.shift(1).rolling(20).max(),low.Low.shift(1).rolling(20).min())
    low['prior_pullback20_atr_cross_day']=sign*(favorable-low.Close.shift(1))/low.ATR
    low['price_context_ema_atr']=sign*(low.Close-low.ContextEMA)/low.ATR
    low['price_context_ema_context_atr']=sign*(low.Close-low.ContextEMA)/low.ContextATR
    low['context_adx']=low.ContextADX
    low['context_slope_atr']=sign*low.ContextSlope/low.ContextATR
    low['context_atr']=low.ContextATR
    low['context_atr_ratio']=low.ContextATRRatio
    low['context_age_minutes']=(pd.Series(low.index,index=low.index)-pd.to_datetime(low.ContextAvailableAt)).dt.total_seconds()/60
    if system=='H1':
        low['price_h1_ema100_atr']=sign*(low.Close-low.H1EMA100)/low.ATR
        low['h1_slope5_atr']=sign*low.H1Slope/low.ATR
        low['h1_adx']=low.H1ADX
    else:
        low['session_minutes']=low.index.hour*60+low.index.minute-600
        low['signal_hour_msk']=low.index.hour
    rows=[]
    for at,row in low.loc[(low.Signal!=0)&(low.index>=START)].iterrows():
        available=pd.Timestamp(row.ContextAvailableAt)
        assert available<=at and at<CUTOFF
        side=int(row.Signal)
        r=dict(signal_id=uid(system,life,fold,symbol,at,side),system=system,instrument=symbol,
          lifecycle=life,fold_id=fold,signal_time=at,feature_available_at=at,context_available_at=available,
          direction='LONG' if side==1 else 'SHORT',signal_year=at.year,signal_month=at.strftime('%Y-%m'),
          context_ema=float(row.ContextEMA),context_slope=float(row.ContextSlope),
          context_close=float(row.ContextClose),context_direction='LONG' if row.ContextSlope>0 else 'SHORT',
          prior_donchian=float(row.PriorHigh if side==1 else row.PriorLow),signal_close=float(row.Close))
        for name in FEATURES_COMMON+(FEATURES_H1 if system=='H1' else FEATURES_M15):r[name]=float(row[name])
        rows.append(r)
    return dict(system=system,instrument=symbol,lifecycle=life,fold_id=fold,bars=bars,frame=raw),rows

def build(engine):
    streams=[];entries=[];coverage=[]
    registry=pd.read_csv(ROOT/'TradingSystemLab/results/post_v3_analysis/stage5_structural_validation/canonical_lifecycle_registry.csv',keep_default_na=False)
    registry=registry[(registry.generation=='v3_perpetual')&(registry.strategy=='T3')&(registry.timeframe=='H1')&(registry.lifecycle=='baseline')]
    for system in ('H1','M15'):
        for symbol in SYMBOLS:
            raw,c=prefix_frame(system,symbol)
            post_bars=[dict(at=at.to_pydatetime(),**row.to_dict()) for at,row in raw.iterrows()]
            if system=='H1':
                r=registry.loc[registry.instrument==symbol].iloc[0]
                raw=raw.loc[r.start_timestamp:r.end_timestamp].copy();life='baseline'
            else:life='history_2023_2026'
            stream,rows=features_for_frame(system,symbol,life,'',raw,engine)
            stream['post_bars']=post_bars
            streams.append(stream);entries.extend(rows)
            c.update(lifecycle=life,replay_rows=len(raw),replay_first_close=raw.index.min(),replay_last_close=raw.index.max(),
                     discovery_signals=len(rows),N4_2023_incomplete=symbol in ('GLDRUBF','IMOEXF'))
            coverage.append(c)
    return streams,entries,coverage
