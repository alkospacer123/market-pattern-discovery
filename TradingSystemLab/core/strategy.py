"""Stable interface implemented by every Trading System Lab strategy."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

import pandas as pd

Direction = Literal["LONG", "SHORT"]


class Strategy(ABC):
    name: str

    @abstractmethod
    def calculate_indicators(self, h1: pd.DataFrame, h4: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]: ...

    @abstractmethod
    def regime(self, h4_bar: pd.Series) -> Direction | None: ...

    @abstractmethod
    def generate_signal(self, h1_bar: pd.Series, regime: Direction | None) -> Direction | None: ...

    @abstractmethod
    def calculate_stop_loss(self, direction: Direction, entry: float, atr_value: float) -> float: ...

    @abstractmethod
    def calculate_take_profit(self, direction: Direction, entry: float, atr_value: float) -> float | None: ...

    @abstractmethod
    def manage_position(self, direction: Direction, extreme: float, atr_value: float) -> float: ...

    @abstractmethod
    def exit_signal(self, direction: Direction, bar: pd.Series, stop: float) -> bool: ...
