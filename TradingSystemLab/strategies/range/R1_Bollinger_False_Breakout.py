"""Frozen causal R1 Bollinger false-breakout mean-reversion strategy."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from enum import Enum
import pandas as pd

from ...core.indicators import (
    adx,
    atr,
    bollinger_bands,
    bollinger_bandwidth,
    ema,
    previous_window_percentile,
)
from ...core.portfolio import FixedRiskPortfolio

STRATEGY_ID = "R1_Bollinger_False_Breakout_Mean_Reversion_v1.0"

class R1State(str, Enum):
    FLAT_NO_SETUP = "FLAT_NO_SETUP"
    LONG_EXCURSION_ARMED = "LONG_EXCURSION_ARMED"
    SHORT_EXCURSION_ARMED = "SHORT_EXCURSION_ARMED"
    POSITION_OPEN = "POSITION_OPEN"

@dataclass(frozen=True)
class R1Parameters:
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    bbw_percentile_lookback: int = 100
    bbw_percentile_threshold: float = 50.0
    adx_period: int = 14
    adx_range_max: float = 20.0
    range_failure_adx: float = 25.0
    atr_period: int = 14
    ema_flat_period: int = 200
    ema_slope_lookback: int = 10
    ema_slope_max_atr: float = 0.25
    confirmation_window: int = 1
    stop_buffer_atr: float = 0.10
    max_initial_stop_atr: float = 2.0
    max_holding_bars: int = 10
    target: str = "bollinger_middle_previous_bar"

@dataclass
class Excursion:
    direction: str
    index: int
    time: pd.Timestamp
    close: float
    extreme: float

class R1BollingerFalseBreakout:
    """One-position, exactly-next-bar state machine over closed H1 bars."""
    name = STRATEGY_ID
    def __init__(self, parameters: R1Parameters | None = None):
        self.parameters = parameters or R1Parameters()

    @staticmethod
    def _validate(frame: pd.DataFrame) -> None:
        if frame.empty or frame.index.tz is None or not frame.index.is_monotonic_increasing:
            raise ValueError("closed H1 timestamps must be timezone-aware, nonempty, and sorted")
        if frame.index.has_duplicates:
            raise ValueError("closed H1 timestamps must be unique")
        if (frame.index >= pd.Timestamp("2025-01-01", tz=frame.index.tz)).any():
            raise ValueError("timestamp >= 2025-01-01 TRUE OOS is locked")
        if not {"Open", "High", "Low", "Close"}.issubset(frame.columns):
            raise ValueError("H1 OHLC columns are required")

    def calculate_indicators(self, h1: pd.DataFrame) -> pd.DataFrame:
        self._validate(h1)
        p, out = self.parameters, h1.copy()
        bands = bollinger_bands(out.Close, p.bollinger_period, p.bollinger_std)
        out[["Middle", "Upper", "Lower"]] = bands[["middle", "upper", "lower"]]
        # Use the shared implementation so R1 cannot silently diverge from the
        # Bollinger/BBW convention used by the other lab strategies.
        out["BBW"] = bollinger_bandwidth(
            out.Close, p.bollinger_period, p.bollinger_std
        )
        out["BBW_reference"] = previous_window_percentile(out.BBW, p.bbw_percentile_lookback, p.bbw_percentile_threshold)
        # Diagnostic percentile rank against the same strictly-prior distribution.
        out["BBW_percentile"] = pd.Series([
            (100.0 * (out.BBW.iloc[max(0, i-p.bbw_percentile_lookback):i] <= out.BBW.iloc[i]).mean())
            if i >= p.bbw_percentile_lookback and out.BBW.iloc[max(0, i-p.bbw_percentile_lookback):i].notna().all() and pd.notna(out.BBW.iloc[i]) else float("nan")
            for i in range(len(out))], index=out.index)
        out["ATR"] = atr(out, p.atr_period)
        out["ADX"] = adx(out, p.adx_period)
        out["EMA200"] = ema(out.Close, p.ema_flat_period)
        out["EMA200_slope_ATR"] = (out.EMA200 - out.EMA200.shift(p.ema_slope_lookback)).abs() / out.ATR
        out["Target_previous_middle"] = out.Middle.shift(1)
        out["RangeRegime"] = ((out.ADX <= p.adx_range_max) & (out.BBW <= out.BBW_reference) &
                              (out.EMA200_slope_ATR <= p.ema_slope_max_atr))
        return out

    def frozen_parameters(self): return asdict(self.parameters)

    def run(self, h1: pd.DataFrame, symbol: str, *, tick_size: float = .001,
            portfolio: FixedRiskPortfolio | None = None) -> pd.DataFrame:
        d, p = self.calculate_indicators(h1), self.parameters
        portfolio = portfolio or FixedRiskPortfolio()
        state, setup, pos, records, equity = R1State.FLAT_NO_SETUP, None, None, [], portfolio.initial_capital
        def close(i, price, reason, low, high):
            nonlocal pos, state, equity
            sign = 1 if pos["direction"] == "LONG" else -1
            risk = pos["initial_risk_points"]
            gross = sign * (price-pos["entry_price"])/risk
            cost = 2*tick_size/risk
            min_low, max_high = min(pos["min_low"], low), max(pos["max_high"], high)
            rec = {**pos["metadata"], "exit_time": d.index[i], "exit_price": price, "exit_reason": reason,
                   "bars_held": pos["bars_held"]+1, "gross_R": gross, "cost_R_C1": cost, "net_R_C1": gross-cost,
                   "MAE_R": max(0., pos["entry_price"]-min_low if sign==1 else max_high-pos["entry_price"])/risk,
                   "MFE_R": max(0., max_high-pos["entry_price"] if sign==1 else pos["entry_price"]-min_low)/risk,
                   "quantity": pos["quantity"]}
            records.append(rec); equity += (gross-cost)*equity*portfolio.risk_fraction
            pos, state = None, R1State.FLAT_NO_SETUP
        for i, (_, bar) in enumerate(d.iterrows()):
            if pos is not None:
                direction, stop, target = pos["direction"], pos["initial_stop"], bar.Target_previous_middle
                stop_hit = bar.Low <= stop if direction=="LONG" else bar.High >= stop
                target_hit = pd.notna(target) and (bar.High >= target if direction=="LONG" else bar.Low <= target)
                if stop_hit:
                    price = min(float(bar.Open),stop) if direction=="LONG" else max(float(bar.Open),stop)
                    # Unknown movement after an intrabar fill cannot affect MAE/MFE.
                    low = price if direction == "LONG" else pos["min_low"]
                    high = pos["max_high"] if direction == "LONG" else price
                    close(i, price, "STOP", low, high); continue
                if target_hit:
                    low = pos["min_low"] if direction == "LONG" else float(target)
                    high = float(target) if direction == "LONG" else pos["max_high"]
                    close(i, float(target), "MIDDLE_BAND_TARGET", low, high); continue
                if bar.ADX > p.range_failure_adx:
                    close(i, float(bar.Close), "RANGE_FAILURE", float(bar.Low), float(bar.High)); continue
                next_held = pos["bars_held"] + 1
                pos["min_low"], pos["max_high"] = min(pos["min_low"],float(bar.Low)), max(pos["max_high"],float(bar.High))
                if next_held >= p.max_holding_bars:
                    # bars_held in the record counts executable bars after close entry.
                    close(i, float(bar.Close), "TIME_EXIT", float(bar.Low), float(bar.High)); continue
                pos["bars_held"] = next_held
                continue
            if setup is not None:
                # Exactly one subsequent close gets a chance; it cannot replace this setup.
                if i == setup.index + 1 and bool(bar.RangeRegime):
                    reclaim = (bar.Close > bar.Lower and bar.Close > setup.close) if setup.direction=="LONG" else (bar.Close < bar.Upper and bar.Close < setup.close)
                    if reclaim:
                        entry=float(bar.Close); extreme=min(setup.extreme,float(bar.Low)) if setup.direction=="LONG" else max(setup.extreme,float(bar.High))
                        stop=extreme-p.stop_buffer_atr*bar.ATR if setup.direction=="LONG" else extreme+p.stop_buffer_atr*bar.ATR
                        risk=entry-stop if setup.direction=="LONG" else stop-entry
                        if pd.notna(risk) and risk>0 and risk <= p.max_initial_stop_atr*bar.ATR:
                            meta={"trade_id":f"{symbol}-{len(records)+1:06d}","strategy_id":self.name,"symbol":symbol,"direction":setup.direction,
                                  "excursion_time":setup.time,"reclaim_time":d.index[i],"entry_time":d.index[i],"entry_price":entry,
                                  "initial_stop":stop,"initial_risk_points":risk,"initial_risk_ticks":risk/tick_size,
                                  "target_reference":p.target,"target_at_entry":float(bar.Middle),"ADX_entry":float(bar.ADX),"BBW_entry":float(bar.BBW),
                                  "BBW_percentile_entry":float(bar.BBW_percentile),"EMA200_slope_ATR_entry":float(bar.EMA200_slope_ATR)}
                            pos={"direction":setup.direction,"entry_price":entry,"initial_stop":stop,"initial_risk_points":risk,"bars_held":0,
                                 "min_low":entry,"max_high":entry,"quantity":portfolio.size(equity,entry,stop),"metadata":meta}; state=R1State.POSITION_OPEN
                setup=None
                if pos is None: state=R1State.FLAT_NO_SETUP
                continue
            if bool(bar.RangeRegime):
                long_exc, short_exc = bar.Low < bar.Lower, bar.High > bar.Upper
                # Deterministic tie break: downside before upside.
                if long_exc:
                    setup=Excursion("LONG",i,d.index[i],float(bar.Close),float(bar.Low)); state=R1State.LONG_EXCURSION_ARMED
                elif short_exc:
                    setup=Excursion("SHORT",i,d.index[i],float(bar.Close),float(bar.High)); state=R1State.SHORT_EXCURSION_ARMED
        cols=["trade_id","strategy_id","symbol","direction","excursion_time","reclaim_time","entry_time","entry_price","initial_stop","initial_risk_points","initial_risk_ticks","target_reference","target_at_entry","exit_time","exit_price","exit_reason","bars_held","gross_R","cost_R_C1","net_R_C1","MAE_R","MFE_R","ADX_entry","BBW_entry","BBW_percentile_entry","EMA200_slope_ATR_entry","quantity"]
        return pd.DataFrame(records,columns=cols)
