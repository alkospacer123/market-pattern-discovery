from __future__ import annotations

import copy
import json
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


def test_overlap_ohlc_revision_preserves_append_only_authority():
    _, first_payload = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    revised_live = rollover_live()
    seam = pd.Timestamp("2026-09-15 14:00:00", tz=MOSCOW)
    revised_live.loc[seam, "Close"] = Decimal("103.5")

    merged, second_payload = extend_rolling_open_h1(
        seed(), first_payload, revised_live, "USDRUBF"
    )

    assert merged.loc[seam, "Close"] == Decimal("104")
    assert second_payload["bars"][: len(first_payload["bars"])] == first_payload["bars"]
    assert [bar["timestamp"] for bar in second_payload["bars"]][-2:] == [
        "2026-09-15T15:00:00+03:00",
        "2026-09-15T16:00:00+03:00",
    ]


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


def test_later_finam_backfill_in_immutable_persisted_overlap_is_ignored():
    # At the first acceptance FINAM did not report 13:00. The accepted
    # persisted continuation contains 14:00 but no 13:00.
    first = frame(
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 14:00:00", "104"),
    )
    accepted, original = extend_rolling_open_h1(
        seed(), None, first, "USDRUBF"
    )
    original_prefix = json.dumps(
        original["bars"], sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    backfilled = frame(
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 14:00:00", "104"),
        ("2026-09-15 15:00:00", "105"),
    )

    merged, updated = extend_rolling_open_h1(
        seed(), original, backfilled, "USDRUBF"
    )

    assert accepted.equals(merged.loc[accepted.index])
    assert pd.Timestamp("2026-09-15 13:00:00", tz=MOSCOW) not in merged.index
    assert pd.Timestamp("2026-09-15 15:00:00", tz=MOSCOW) in merged.index
    assert json.dumps(
        updated["bars"][:len(original["bars"])],
        sort_keys=True, separators=(",", ":")
    ).encode("utf-8") == original_prefix
    assert original["bars"] == [
        {
            "timestamp": "2026-09-15T14:00:00+03:00",
            "open": "104", "high": "105", "low": "103", "close": "104"
        }
    ]


def test_live_backfilled_timestamp_does_not_change_seam_ohlc():
    _, original = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    update = frame(
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 12:30:00", "103"),
        ("2026-09-15 13:00:00", "103"),
        ("2026-09-15 14:00:00", "104"),
        ("2026-09-15 15:00:00", "105"),
    )
    update.loc[pd.Timestamp("2026-09-15 14:00:00", tz=MOSCOW), "Close"] = Decimal("104.5")
    merged, new_payload = extend_rolling_open_h1(
        seed(), original, update, "USDRUBF"
    )
    assert pd.Timestamp("2026-09-15 12:30:00", tz=MOSCOW) not in merged.index
    assert merged.loc[pd.Timestamp("2026-09-15 14:00:00", tz=MOSCOW), "Close"] == Decimal("104")
    assert new_payload["bars"][:len(original["bars"])] == original["bars"]


@pytest.mark.parametrize("invalid", ["duplicate", "reversed"])
def test_live_duplicate_or_invalid_order_fails_closed(invalid):
    _, original = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    live = rollover_live()
    if invalid == "duplicate":
        live = pd.concat([live, live.iloc[[-1]]])
        code = "STAGE8_12_4_H1_SPLICE_DUPLICATE"
    else:
        live = live.iloc[::-1]
        code = "STAGE8_12_4_H1_SPLICE_ORDER_INVALID"
    with pytest.raises(ProductionHistoryError, match=code):
        extend_rolling_open_h1(seed(), original, live, "USDRUBF")


def test_seam_must_be_latest_persisted_bar_not_earlier_overlap():
    _, original = extend_rolling_open_h1(
        seed(), None, first_live(), "USDRUBF"
    )
    earlier_only = frame(
        ("2026-09-15 12:00:00", "102"),
        ("2026-09-15 13:00:00", "103"),
    )
    with pytest.raises(
        ProductionHistoryError, match="STAGE8_12_4_H1_SPLICE_TIMESTAMP_MISMATCH"
    ):
        extend_rolling_open_h1(seed(), original, earlier_only, "USDRUBF")


def test_stale_current_h1_guard_untouched():
    from pathlib import Path
    source = Path("TradingSystemLab/stage8_robot/production_service.py").read_text(
        encoding="utf-8"
    )
    assert 'if expected.astimezone(timezone.utc) not in live_utc:' in source
    assert '"STAGE8_12_4_STALE_COMPLETED_H1_DATA"' in source
