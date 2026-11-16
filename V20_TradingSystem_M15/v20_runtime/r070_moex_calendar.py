"""R070 candidate-only authoritative MOEX futures market-day calendar.

OFFLINE parser plus explicitly invoked GET of the official MOEX ISS endpoint.
No H1/V20 LIVE worker import, FINAM API access, orders or credentials.

The futures-specific endpoint returns `off_days` with `is_traded`,
`trade_session_date` and `reason`. In 2026 many Saturday/Sunday dates
are real exchange sessions (reason W); do not approximate with weekdays.
A market-day calendar is NOT proof every instrument has every M15 candle.
"""
from __future__ import annotations

from datetime import date, timedelta
from hashlib import sha256
import json
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

from .ext2_history_bridge import EXT2HistoryBlocked

MOEX_ISS_ORIGIN = "https://iss.moex.com"
MOEX_FUTURES_PATH = "/iss/calendars/futures.json"
MOEX_CALENDAR_SOURCE = "MOEX_ISS_FUTURES_SHOW_ALL_DAYS_V1"
REQUIRED = ("tradedate", "is_traded", "trade_session_date", "reason")


def _exact_date(value) -> date:
    if not isinstance(value, str) or len(value) != 10:
        raise ValueError("invalid calendar date")
    day = date.fromisoformat(value)
    if day.isoformat() != value:
        raise ValueError("noncanonical calendar date")
    return day


def parse_moex_futures_calendar(
    response_bytes: bytes, *, date_from: date, date_till: date,
) -> tuple[tuple[date, ...], str]:
    """Parse complete futures-specific ISS daily table; block missing rows.

    Only a response independently fetched from MOEX over HTTPS is authority.
    No inference from Monday-Friday or from M15 volume is permitted.
    The source digest returned here is an audit marker, not a signature.
    """
    if (type(date_from) is not date or type(date_till) is not date
            or date_from > date_till
            or (date_till - date_from).days >= 32
            or date_from.year != date_till.year
            or not isinstance(response_bytes, bytes)
            or not response_bytes or len(response_bytes) > 256_000):
        raise EXT2HistoryBlocked("R070_MOEX_CALENDAR_REQUEST_SCOPE_INVALID")
    try:
        body = json.loads(response_bytes)
        if not isinstance(body, dict) or not isinstance(body.get("off_days"), dict):
            raise ValueError("MOEX off_days missing")
        table = body["off_days"]
        names = table["columns"]
        rows = table["data"]
        if (not isinstance(names, list) or len(names) != len(set(names))
                or any(name not in names for name in REQUIRED)
                or not isinstance(rows, list)):
            raise ValueError("MOEX schema changed")
        indices = [names.index(col) for col in REQUIRED]
        mapped = {}
        for row in rows:
            if not isinstance(row, list) or len(row) != len(names):
                raise ValueError("malformed MOEX row")
            stamp, traded, session, reason = (row[i] for i in indices)
            trading_day = _exact_date(stamp)
            if trading_day < date_from or trading_day > date_till or trading_day in mapped:
                raise ValueError("out-of-range or duplicate MOEX day")
            if type(traded) is not int or traded not in (0, 1):
                raise ValueError("unknown market-day status")
            if reason not in (None, "H", "N", "W", "T"):
                raise ValueError("unrecognized market session")
            if session is not None:
                session_day = _exact_date(session)
                if reason == "W" and session_day <= trading_day:
                    raise ValueError("weekend session cannot be prior day")
            elif reason == "W":
                raise ValueError("weekend session date missing")
            if ((reason == "H" and traded != 0)
                    or (reason in ("W", "N", "T") and traded != 1)):
                raise ValueError("inconsistent MOEX reason and market status")
            mapped[trading_day] = traded
        expected = tuple(date_from + timedelta(days=i) for i in
                         range((date_till - date_from).days + 1))
        if set(mapped) != set(expected):
            raise ValueError("MOEX calendar incomplete or pagination required")
        days = tuple(day for day in expected if mapped[day] == 1)
        return days, sha256(response_bytes).hexdigest()
    except (ValueError, TypeError, KeyError, OverflowError, UnicodeError) as exc:
        raise EXT2HistoryBlocked("R070_MOEX_CALENDAR_INVALID") from exc


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def fetch_moex_futures_calendar(
    *, date_from: date, date_till: date,
) -> tuple[date, ...]:
    """GET-only independent calendar authority, split into <=30-day windows.

    Explicit call only when preparing/refreshing candidate history. Never
    called by installed V20 worker. HTTPS identity is enforced by system TLS,
    redirects are forbidden, and missing/blocked ISS response fails closed.
    """
    if (type(date_from) is not date or type(date_till) is not date
            or date_from > date_till or date_from.year != date_till.year
            or (date_till - date_from).days > 370):
        raise EXT2HistoryBlocked("R070_MOEX_CALENDAR_RANGE_INVALID")
    opener = build_opener(_NoRedirect)
    cursor = date_from
    result = []
    while cursor <= date_till:
        end = min(date_till, cursor + timedelta(days=29))
        query = urlencode({
            "from": cursor.isoformat(), "till": end.isoformat(),
            "show_all_days": "1", "iss.only": "off_days",
        })
        url = MOEX_ISS_ORIGIN + MOEX_FUTURES_PATH + "?" + query
        try:
            with opener.open(Request(
                    url, headers={"Accept": "application/json",
                                  "User-Agent": "V20-R070-Calendar/1.0"},
                    method="GET"), timeout=10) as response:
                final = urlparse(response.geturl())
                if (final.scheme != "https" or final.netloc != "iss.moex.com"
                        or final.path != MOEX_FUTURES_PATH
                        or response.getcode() != 200):
                    raise ValueError("MOEX HTTP origin changed")
                raw = response.read(256_001)
            days, _ = parse_moex_futures_calendar(
                raw, date_from=cursor, date_till=end)
            result.extend(days)
        except Exception as exc:
            raise EXT2HistoryBlocked("R070_MOEX_CALENDAR_READ_UNVERIFIED") from exc
        cursor = end + timedelta(days=1)
    return tuple(result)
