"""Offline transfer adapter; imports frozen research components without edits."""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from pathlib import Path
import json
import pandas as pd

from TradingSystemLab.core.data_loader import DataLoader
from TradingSystemLab.strategies.trend.T3_MTF_Trend import T3MTFTrend, T3Parameters
from TradingSystemLab.results.post_v3_analysis.stage5_structural_validation.stage5_trail1_execution import Trail1State

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / 'TradingSystemLab/results/post_v3_analysis/stage7_production_specification_freeze'
SPEC = json.loads((SPEC_DIR / 'production_specification.json').read_text())
PARAMETERS = SPEC['strategy']['parameters']
SCENARIOS = {
    'LONG_SHORT_C1': {'long_only': False, 'grid': None, 'cost_price': .002},
    'LONG_ONLY_C1': {'long_only': True, 'grid': None, 'cost_price': .002},
    # Explicit stock execution diagnostic, not a replacement frozen authority.
    'LONG_ONLY_STOCK_PROXY': {'long_only': True, 'grid': .01, 'cost_price': .02},
}


def project(direction, value, step):
    rounding = ROUND_FLOOR if direction == 'LONG' else ROUND_CEILING
    return float((Decimal(str(value)) / Decimal(str(step))).to_integral_value(rounding=rounding) * Decimal(str(step)))


def features(frame):
    return T3MTFTrend(T3Parameters(**PARAMETERS)).calculate_indicators(frame, DataLoader.h4_from_h1(frame))


def run(frame, scenario, prepared=None):
    """Signal-close entry. No processing of entry-bar extremes. No forced exit."""
    cfg = SCENARIOS[scenario]
    strategy = T3MTFTrend(T3Parameters(**PARAMETERS))
    low, high = prepared if prepared is not None else features(frame)
    # A completed H4 regime remains fixed until publication of the next H4.
    regimes = [strategy.regime(b) for _, b in high.iterrows()]
    cursor = -1
    pos = None
    trades, trace = [], []
    sequence = 0
    for t, b in low.iterrows():
        while cursor + 1 < len(high) and high.index[cursor + 1] <= t:
            cursor += 1
        regime = regimes[cursor] if cursor >= 0 else None
        if pos is not None:
            state = pos['state']
            old = state.activate_before_event(t, pos['stop'])
            if cfg['grid']:
                old = project(pos['direction'], old, cfg['grid'])
            pos['stop'] = old
            hit = strategy.exit_signal(pos['direction'], b, old)
            if hit:
                price = state.stop_fill(float(b.Open), old)
                gross = (1 if pos['direction'] == 'LONG' else -1) * (price - pos['entry_price']) / pos['initial_risk_price']
                cost = cfg['cost_price'] / pos['initial_risk_price']
                trades.append({k: v for k, v in pos.items() if k not in ('state', 'extreme', 'stop')} | state.event_fields() | {
                    'scenario': scenario, 'exit_time': t, 'exit_price': price, 'final_stop': old,
                    'exit_reason': 'INITIAL_STOP' if old == pos['initial_stop_price'] else 'ATR_TRAILING_STOP',
                    'gap_through_stop': price != old, 'gross_R': gross, 'cost_R': cost, 'net_R': gross - cost,
                    'bars_held': pos['bars_held'] + 1,
                })
                trace.append({'trade_id': pos['trade_id'], 'time': t, 'event': 'EXIT', 'stop_before': old,
                              'stop_after': old, 'triggered': state.triggered, 'activated': state.activated})
                pos = None
            else:
                pos['bars_held'] += 1
                pos['extreme'] = max(pos['extreme'], float(b.High)) if pos['direction'] == 'LONG' else min(pos['extreme'], float(b.Low))
                candidate = float(strategy.manage_position(pos['direction'], pos['extreme'], float(b.ATR)))
                if cfg['grid']:
                    candidate = project(pos['direction'], candidate, cfg['grid'])
                triggered_now = state.observe_completed_bar(t, float(b.High), float(b.Low), candidate, old)
                pos['stop'] = state.candidate_after_bar(old, candidate)
                trace.append({'trade_id': pos['trade_id'], 'time': t, 'event': 'TRIGGER' if triggered_now else 'HOLD',
                              'canonical_candidate': candidate, 'stop_before': old, 'stop_after': pos['stop'],
                              'triggered': state.triggered, 'activated': state.activated})
        if pos is None and pd.notna(b.ATR):
            signal = strategy.generate_signal(b, regime)
            if signal and (not cfg['long_only'] or signal == 'LONG'):
                entry = float(b.Close)
                stop = float(strategy.calculate_stop_loss(signal, entry, float(b.ATR)))
                if cfg['grid']:
                    stop = project(signal, stop, cfg['grid'])
                sequence += 1
                pos = {'trade_id': f'SBER-{sequence:06d}', 'direction': signal, 'entry_time': t, 'entry_price': entry,
                       'initial_stop_price': stop, 'initial_risk_price': abs(entry - stop), 'stop': stop,
                       'extreme': entry, 'bars_held': 0, 'state': Trail1State(signal, entry, stop)}
                trace.append({'trade_id': pos['trade_id'], 'time': t, 'event': 'ENTRY', 'stop_before': stop,
                              'stop_after': stop, 'triggered': False, 'activated': False})
    open_position = None
    if pos is not None:
        open_position = {k: v for k, v in pos.items() if k != 'state'} | pos['state'].event_fields() | {
            'scenario': scenario, 'asof': frame.index[-1], 'status': 'OPEN', 'realized_net_R': None,
        }
    return pd.DataFrame(trades), pd.DataFrame(trace), open_position
