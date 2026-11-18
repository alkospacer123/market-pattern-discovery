"""R088: exact historical missing M15 Open labels in FINAM official exports.

18-Nov-2026 user-supplied *official FINAM terminal* M15 re-export. All
underlying observed candles pass basic OHLCV/time checks, no duplicates;
the 14 gaps persist across exports. Absence of a candle is NOT evidence of
zero trades. Never synthesize a candle or modify the frozen EXT2 feature.

This is an explicit exception ONLY for these exact *historical* labels.
Fresh/new missing M15, last completed signal, prev-day eligibility and
independent second GET OHLCV must remain fail-closed. No account/order access.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256

# SHA-256 of exact original terminal TXT bytes (NOT a numeric reinterpretation).
OFFICIAL_FINAM_REEXPORT_SHA256 = {
    "USDRUBF": "dd808379cbddd259164145508b30bc14d29950242032933d0f1eacea3bb80fc2",
    "GLDRUBF": "0c26f9f288697640c4cfd71c51646d09eb177c9e18be2c2fa9e03d0cbb177b91",
    "CNYRUBF": "e505a96bd313bcb3133dab2f0aa81867bbe02ea3848e04d1269d5f16bb0a9348",
    "IMOEXF": "f531ac606df0146cc89420f0465fb07aa12f2ad33dc036a1e71cd2489fadfc11",
}

_MISSING_STRINGS = {
    "USDRUBF": (
        "2026-08-30T12:15:00",
        "2026-09-27T10:45:00", "2026-09-27T11:15:00",
        "2026-10-03T14:30:00", "2026-10-03T14:45:00",
        "2026-10-03T17:15:00",
        "2026-10-18T11:30:00", "2026-10-18T14:00:00",
        "2026-11-01T10:45:00", "2026-11-08T14:00:00",
    ),
    "GLDRUBF": (
        "2026-09-27T10:00:00", "2026-09-27T10:30:00",
        "2026-10-04T12:30:00", "2026-10-10T17:00:00",
    ),
}

APPROVED_HISTORICAL_MISSING_M15 = {
    symbol: tuple(datetime.fromisoformat(ts) for ts in values)
    for symbol, values in _MISSING_STRINGS.items()
}


def accepted_historical_missing_m15(symbol: str) -> tuple[datetime, ...]:
    """Exact missing labels only; never infer accepted gaps from other dates."""
    return APPROVED_HISTORICAL_MISSING_M15.get(symbol, ())
