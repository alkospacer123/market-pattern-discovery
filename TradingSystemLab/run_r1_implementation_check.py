"""Run the frozen R1 implementation check on development data only."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from .core.data_loader import DataLoader
from .strategies.range.R1_Bollinger_False_Breakout import STRATEGY_ID, R1BollingerFalseBreakout

def load_h1(root: Path, symbol: str) -> pd.DataFrame:
    paths=[p for year in (2023,2024) for p in sorted((root/"2026"/symbol).glob(f"{symbol}_H1_{year}_Q*.csv"))]
    if not paths: raise FileNotFoundError(f"no 2023-2024 H1 data for {symbol} under {root}")
    data=DataLoader().close_index(DataLoader().load_csv(paths))
    if data.index.min() < pd.Timestamp("2023-01-01",tz=data.index.tz) or (data.index >= pd.Timestamp("2025-01-01",tz=data.index.tz)).any():
        raise ValueError("R1 development coverage must be 2023-2024 only")
    return data

def _pf(v):
    gains=float(v[v>0].sum()); losses=float(-v[v<0].sum())
    return gains/losses if losses else None

def metrics_for(t):
    gross=t.gross_R if len(t) else pd.Series(dtype=float); net=t.net_R_C1 if len(t) else pd.Series(dtype=float)
    curve=pd.concat([pd.Series([0.]),net.reset_index(drop=True).cumsum()],ignore_index=True); dd=curve-curve.cummax()
    count=lambda reason:int((t.exit_reason==reason).sum())
    mean=lambda s:float(s.mean()) if len(s) else 0.; median=lambda s:float(s.median()) if len(s) else 0.
    return {"total_trades":len(t),"LONG_trades":int((t.direction=="LONG").sum()),"SHORT_trades":int((t.direction=="SHORT").sum()),
      "Si_trades":int((t.symbol=="Si").sum()),"CNY_trades":int((t.symbol=="CNY").sum()),"gross_R":float(gross.sum()),
      "PF_C0":_pf(gross),"expectancy_C0":mean(gross),"PF_C1":_pf(net),"expectancy_C1":mean(net),"net_R_C1":float(net.sum()),
      "winrate_C1":float((net>0).mean()) if len(net) else 0.,"max_DD_R_C1":float(dd.min()),"STOP_exits":count("STOP"),
      "MIDDLE_BAND_exits":count("MIDDLE_BAND_TARGET"),"RANGE_FAILURE_exits":count("RANGE_FAILURE"),"TIME_exits":count("TIME_EXIT"),
      "median_holding_bars":median(t.bars_held),"mean_MAE_R":mean(t.MAE_R),"median_MAE_R":median(t.MAE_R),
      "mean_MFE_R":mean(t.MFE_R),"median_MFE_R":median(t.MFE_R)}

def run(data_root:Path,output:Path):
    strategy=R1BollingerFalseBreakout(); pieces=[strategy.run(load_h1(data_root,s),s,tick_size=.001) for s in ("Si","CNY")]
    t=pd.concat(pieces,ignore_index=True).sort_values(["exit_time","symbol","trade_id"],kind="mergesort").reset_index(drop=True)
    output.mkdir(parents=True,exist_ok=True); m=metrics_for(t)
    t.to_csv(output/"trades.csv",index=False,date_format="%Y-%m-%dT%H:%M:%S%z")
    (output/"metrics.json").write_text(json.dumps(m,indent=2,allow_nan=False)+"\n")
    manifest={"strategy_id":STRATEGY_ID,"implementation_version":"1.0","symbols":["Si","CNY"],"timeframe":"H1","development_start":"2023-01-01","development_end":"2024-12-31","frozen_parameters":strategy.frozen_parameters(),"cost_scenarios":{"C0":"zero cost","C1":"1 tick per side"},"true_oos_blocked":True,"implementation_check_only":True,"optimization_performed":False,"walk_forward_performed":False}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    summary=f'''# R1 Bollinger False Breakout Mean Reversion v1.0

## Hypothesis
A failed excursion from a range may revert toward its Bollinger equilibrium.

## Frozen Range Regime
ADX(14) <= 20, current BBW <= the median of the previous 100 BBW observations, and absolute 10-bar EMA200 slope / ATR14 <= 0.25.

## Bollinger Excursion
LONG Low < Lower; SHORT High > Upper on a regime-valid closed H1 bar.

## Reclaim
Exactly the next regime-valid bar must close inside the relevant band and beyond the excursion close.

## Entry
At the reclaim-bar Close, with one position maximum.

## Initial Stop
The two-bar extreme plus a 0.10 ATR outward buffer; risk above 2 ATR is skipped.

## Mean Reversion Target
Intrabar execution uses the prior closed bar's Bollinger middle, never the current bar's close-derived value.

## Range Failure Exit
ADX(14) > 25 exits at Close after intrabar exits are checked.

## Time Exit
Exit at the tenth executable H1 bar Close.

## Causality
Closed H1 data only; prior-only percentile window and target; TRUE OOS 2025+ hard blocked.

## Development Coverage
Si and CNY, 2023-01-01 through 2024-12-31.

## Implementation Check Results
IMPLEMENTATION_CHECK_ONLY

Trades: {m['total_trades']} (LONG {m['LONG_trades']}, SHORT {m['SHORT_trades']}).

## Limitations
No optimization, walk-forward analysis, cross-strategy comparison, or trading verdict was performed.

## Status
STATUS: IMPLEMENTED — NOT YET OPTIMIZED OR VALIDATED
'''
    (output/"summary.md").write_text(summary); return m

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--data-root",required=True,type=Path); ap.add_argument("--output",type=Path,default=Path("TradingSystemLab/results/R1_implementation_check")); a=ap.parse_args(); run(a.data_root,a.output)
