"""Reusable causal checks over synthetic or authorized data only."""
from __future__ import annotations
import pandas as pd
from .models import validate_predictors

class CausalityViolation(RuntimeError): pass

def assert_prefix_invariance(signal_fn, frame: pd.DataFrame, decision_index: int) -> None:
    prefix=signal_fn(frame.iloc[:decision_index+1].copy()).reset_index(drop=True)
    full=signal_fn(frame.copy()).iloc[:decision_index+1].reset_index(drop=True)
    if not prefix.equals(full): raise CausalityViolation("prefix invariance failed")

def assert_future_mutation_invariance(signal_fn, frame: pd.DataFrame, decision_index: int) -> None:
    baseline=signal_fn(frame.copy()).iloc[:decision_index+1].reset_index(drop=True)
    mutated=frame.copy()
    cols=[x for x in ("open","high","low","close","volume") if x in mutated]
    mutated.loc[mutated.index[decision_index+1:],cols] = 1e12
    replay=signal_fn(mutated).iloc[:decision_index+1].reset_index(drop=True)
    if not baseline.equals(replay): raise CausalityViolation("future mutation changed a past signal")

def assert_closed_m5(m1_close_time, m5_close_time) -> None:
    if pd.notna(m5_close_time) and m5_close_time > m1_close_time:
        raise CausalityViolation("M5 candle was not closed at M1 decision time")

def assert_reference_known(reference_observed_at, decision_time) -> None:
    if reference_observed_at > decision_time: raise CausalityViolation("reference level is future-confirmed")

def assert_deterministic_replay(signal_fn, frame: pd.DataFrame) -> None:
    if not signal_fn(frame.copy()).equals(signal_fn(frame.copy())): raise CausalityViolation("replay differs")

def validate_executable_fields(fields: list[str]) -> None: validate_predictors(fields)
