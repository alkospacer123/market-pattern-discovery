from __future__ import annotations
from dataclasses import dataclass
import itertools
import pandas as pd

from .config import BBWConfig, InstrumentConfig
from .exits import BaselineExitManager, Position
from .reports import DiagnosticWriter
from .strategy import Range, Rejection, entry_rejection, position_size, structural_stop
from .prices import adverse_fill


@dataclass
class Portfolio:
    open_trade_id: str | None = None

    def reserve(self, trade_id: str) -> bool:
        if self.open_trade_id is not None:
            return False
        self.open_trade_id = trade_id
        return True

    def release(self, trade_id: str) -> None:
        if self.open_trade_id == trade_id:
            self.open_trade_id = None


class CoreEngine:
    """Deterministic execution primitives; callers feed bars in chronological close order."""
    def __init__(self, config: BBWConfig, instrument: InstrumentConfig, equity: float, reports: DiagnosticWriter | None = None):
        self.config, self.instrument, self.equity = config, instrument, equity
        self.reports = reports or DiagnosticWriter()
        self.portfolio = Portfolio()
        self._setups, self._trades = itertools.count(1), itertools.count(1)

    def new_setup_id(self) -> str:
        return f"SETUP-{next(self._setups):08d}"

    def enter_after_confirmation(self, setup_id: str, direction: str, value: Range, atr_value: float, confirmation_bar: pd.Series, next_bar: pd.Series) -> Position | None:
        """Use next_bar.open only; confirmation close can never execute itself."""
        if next_bar.name <= confirmation_bar.name:
            raise ValueError("entry bar must be the next real bar after confirmation")
        entry = adverse_fill(float(next_bar.open), "BUY" if direction == "LONG" else "SELL",
                             self.config.slippage_ticks, self.instrument.tick_size)
        rejection = entry_rejection(entry, value.high if direction == "LONG" else value.low, atr_value, value.width, confirmation_bar, self.config)
        stop = structural_stop(direction, entry, value, atr_value, self.config, self.instrument)
        rejection = rejection or stop.rejection
        contracts = position_size(self.equity, stop.distance, self.instrument, self.config) if rejection is None else 0
        if rejection is None and contracts < 1:
            rejection = Rejection.POSITION_SIZE_ZERO
        trade_id = f"TRADE-{next(self._trades):08d}"
        if rejection is None and not self.portfolio.reserve(trade_id):
            rejection = Rejection.POSITION_ALREADY_OPEN
        if rejection:
            self.reports.append("rejected_setups", setup_id=setup_id, symbol=self.instrument.symbol,
                direction=direction, datetime=next_bar.name, planned_entry_time=next_bar.name,
                rejection_reason=rejection.value, reason=rejection.value, actual_entry=entry, entry=entry,
                structural_stop=stop.stop, stop_distance_price=stop.distance,
                stop_distance_ticks=stop.distance / self.instrument.tick_size,
                stop_atr=stop.stop_atr, stop_range_ratio=stop.stop_range_ratio)
            return None
        position = Position(direction, entry, stop.stop, contracts)
        self.reports.append("setups", setup_id=setup_id, symbol=self.instrument.symbol,
            direction=direction, planned_entry_time=next_bar.name, actual_entry=entry,
            range_bars=value.bars, range_high=value.high, range_low=value.low,
            range_width=value.width, structural_stop=stop.stop,
            stop_distance_price=stop.distance, stop_distance_ticks=stop.distance / self.instrument.tick_size,
            stop_atr=stop.stop_atr, stop_range_ratio=stop.stop_range_ratio, rejection_reason=None)
        self.reports.append("events", setup_id=setup_id, trade_id=trade_id, timestamp=next_bar.name,
                            datetime=next_bar.name, from_state="CONFIRMATION", to_state="POSITION",
                            reason="NEXT_BAR_ENTRY", state="POSITION", event="NEXT_BAR_ENTRY")
        return position

    def manage(self, position: Position, bars: pd.DataFrame) -> list[dict]:
        manager = BaselineExitManager(self.config.partial_levels, self.config.partial_fractions,
            self.config.intrabar_policy, self.instrument.tick_size,
            self.instrument.tick_value_per_contract, self.config.commission_per_contract,
            self.config.slippage_ticks, allow_lower_tf_fallback=self.config.allow_lower_tf_fallback)
        manager.charge_entry(position)
        events = []
        for timestamp, bar in bars.sort_index(kind="stable").iterrows():
            for event in manager.process(position, float(bar.high), float(bar.low),
                                         float(bar.get("open", position.entry))):
                event["datetime"] = timestamp
                events.append(event)
            if position.closed:
                break
        return events

    def close_position(self, trade_id: str, position: Position) -> None:
        """Apply realized costs/PnL before the next setup can size and reserve."""
        if not position.closed:
            raise ValueError("cannot close portfolio reservation for an open position")
        self.equity += position.net_pnl
        self.portfolio.release(trade_id)


def choose_global_candidate(candidates: list[dict], instrument_priority: tuple[str, ...] = ()) -> dict | None:
    """Timestamp, configured priority, then stable symbol is the sole tie-break."""
    if not candidates: return None
    rank = {symbol: i for i, symbol in enumerate(instrument_priority)}
    return sorted(candidates, key=lambda x: (x["timestamp"], rank.get(x["symbol"], len(rank)), x["symbol"]))[0]
