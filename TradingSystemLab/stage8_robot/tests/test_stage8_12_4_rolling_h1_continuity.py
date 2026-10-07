from __future__ import annotations

import copy
from decimal import Decimal

import pandas as pd
import pytest

from TradingSystemLab.stage8_robot.production_history import (
    CONTINUATION_SCHEMA,
    ProductionHistoryError,
    extend_rolling_open_h1,
)


MOSCOW = "Europe/Moscow"


def frame(*rows):
    index = pd.DatetimeIndex(
        [pd.Timestamp(stamp, tz=MOSCOW) for stamp, _ in rows],
        name="OpenTime",
    )
    values = []
    for _, raw in rows:
        price = Decimal(str(raw))
        values.append((
            price,
            price + Decimal("1"),
            price - Decimal("1"),
            price,
        ))
    return pd.DataFrame(
        values,
        index=index,
        columns=("Open", "High", "Low", "Close"),
        dtype=object,
    )


def seed():
    return frame(
        ("2026-09-15 10:00:00", "100"),
        ("2026-09-15 11:00:00", "101"),
        ("2026-09-15 12:00:00", "102"),
    )


def first_live():
    return frame(
        ("2026-09-15 11:00:00", "101"),
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 14:00:00", "104"),
    )


def rollover_live():
    # No direct overlap with Stage-5 seed. Continuity is proved only through
    # the already-persisted FINAM continuation from the first accepted splice.
    return frame(
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 14:00:00", "104"),
        ("2026-09-15 15:00:00", "105"),
        ("2026-09-15 16:00:00", "106"),
    )


def test_initial_seed_overlap_creates_durable_continuation_payload():
    merged, payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )

    assert merged.index[-1] == pd.Timestamp(
        "2026-09-15 14:00:00", tz=MOSCOW
    )
    assert payload["schema"] == CONTINUATION_SCHEMA
    assert [bar["timestamp"] for bar in payload["bars"]] == [
        "2026-09-15T13:00:00+03:00",
        "2026-09-15T14:00:00+03:00",
    ]
    assert len(payload["bars_sha256"]) == 64


def test_initial_overlap_preserves_authority_only_historical_bar():
    sparse_live = frame(
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 14:00:00", "104"),
    )
    merged, payload = extend_rolling_open_h1(
        seed(), None, sparse_live, "USDRUBF"
    )

    assert pd.Timestamp(
        "2026-09-15 11:00:00", tz=MOSCOW
    ) in merged.index
    assert [bar["timestamp"] for bar in payload["bars"]] == [
        "2026-09-15T13:00:00+03:00",
        "2026-09-15T14:00:00+03:00",
    ]


def test_restart_after_seed_window_rollover_uses_persisted_finam_tail():
    _, first_payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )

    merged, second_payload = extend_rolling_open_h1(
        seed(), first_payload, rollover_live(), "USDRUBF"
    )

    assert merged.index[-1] == pd.Timestamp(
        "2026-09-15 16:00:00", tz=MOSCOW
    )
    assert second_payload["bars"][: len(first_payload["bars"])] == first_payload["bars"]
    assert [bar["timestamp"] for bar in second_payload["bars"]][-2:] == [
        "2026-09-15T15:00:00+03:00",
        "2026-09-15T16:00:00+03:00",
    ]


def test_same_finam_window_is_idempotent():
    _, payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    _, repeated = extend_rolling_open_h1(
        seed(), payload, first_live(), "USDRUBF"
    )
    assert repeated == payload


def test_downtime_longer_than_available_overlap_fails_closed():
    _, first_payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    no_overlap = frame(
        ("2026-09-15 15:00:00", "105"),
        ("2026-09-15 16:00:00", "106"),
    )
    with pytest.raises(
        ProductionHistoryError,
        match="STAGE8_12_4_H1_SPLICE_NO_OVERLAP",
    ):
        extend_rolling_open_h1(
            seed(), first_payload, no_overlap, "USDRUBF"
        )


def test_overlap_ohlc_mutation_fails_closed():
    _, first_payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    bad = rollover_live()
    bad.loc[pd.Timestamp("2026-09-15 14:00:00", tz=MOSCOW), "Close"] = Decimal("103.5")
    with pytest.raises(
        ProductionHistoryError,
        match="STAGE8_12_4_H1_SPLICE_OHLC_MISMATCH",
    ):
        extend_rolling_open_h1(
            seed(), first_payload, bad, "USDRUBF"
        )


def test_overlap_timestamp_gap_fails_closed():
    _, first_payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    gap = frame(
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 15:00:00", "105"),
        ("2026-09-15 16:00:00", "106"),
    )
    with pytest.raises(
        ProductionHistoryError,
        match="STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH",
    ):
        extend_rolling_open_h1(
            seed(), first_payload, gap, "USDRUBF"
        )


def test_persisted_continuation_corruption_fails_closed_before_t3():
    _, payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    corrupted = copy.deepcopy(payload)
    corrupted["bars_sha256"] = "0" * 64

    with pytest.raises(
        ProductionHistoryError,
        match="STAGE8_12_4_H1_CONTINUATION_INTEGRITY_INVALID",
    ):
        extend_rolling_open_h1(
            seed(), corrupted, rollover_live(), "USDRUBF"
        )
