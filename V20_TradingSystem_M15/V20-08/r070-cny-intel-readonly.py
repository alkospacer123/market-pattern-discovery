"""R070 CNY M15 Intel physical acceptance: original SHA-pinned sources + FINAM GET ONLY.

Does not call V20LiveJournal, production SQLite, order/SLTP endpoints or
scheduled tasks. Requires a trusted PowerShell launcher to inject scoped DPAPI
account/token into this process's environment only; no secret is written to disk.

No transfer or approval of LIVE entry comes from a PASS here. The separately
isolated account-scoped candidate checkpoint still needs StateStore bootstrap.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from io import BytesIO
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse
from zipfile import ZipFile

import pandas as pd

TARGET = "CNYRUBF"
FINAM = "CNYRUBF@RTSX"
ORIGINAL_END = datetime(2026, 11, 15, 17, 45)
LATEST_ALLOWED_DATE = date(2026, 11, 17)
HISTORY_SHA = "6fcd14c5d473652d014e47577597d22512b97319ef73996aad04cbc38b9ff79c"
SOURCE_SHA = "80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31"
TERMINAL_SHA = "f6ae045a074fea9be3f7c9b5ca47dfc7dedae4481f61e8a71fc60d16b502d4f2"
ARCHIVE = "r070-cnyrubf-20261115-verified-offline.zip"
MOSCOW = timezone(timedelta(hours=3))
UTC = timezone.utc


class Hold(RuntimeError):
    pass


def need(condition: bool, label: str) -> None:
    if not condition:
        raise Hold("R070_CNY_" + label)


def exact_checkpoint(path: Path) -> tuple[pd.DataFrame, str]:
    need(path.is_file() and not path.is_symlink(), "CHECKPOINT_MISSING")
    raw = path.read_bytes()
    with ZipFile(BytesIO(raw)) as archive:
        need(archive.namelist() == ["manifest.json", "history.csv"], "CHECKPOINT_MEMBERS_INVALID")
        manifest = json.loads(archive.read("manifest.json"))
        csv = archive.read("history.csv")
    need(manifest.get("schema") == "v20.r070.m15_candidate_checkpoint.v1" and
         manifest.get("symbol") == TARGET and manifest.get("rows") == 59951 and
         manifest.get("history_sha256") == HISTORY_SHA and
         manifest.get("source_r060_csv_sha256") == "259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4" and
         manifest.get("source_finam_terminal_csv_sha256") == TERMINAL_SHA and
         manifest.get("latest_m15_open_msk") == ORIGINAL_END.isoformat() and
         sha256(csv).hexdigest() == HISTORY_SHA, "CHECKPOINT_MANIFEST_OR_SHA_INVALID")
    frame = pd.read_csv(BytesIO(csv), parse_dates=["Datetime"], float_precision="round_trip")
    need(len(frame) == 59951 and frame.Datetime.iloc[-1] == ORIGINAL_END and
         frame.Datetime.is_unique and frame.Datetime.is_monotonic_increasing,
         "CHECKPOINT_HISTORY_INVALID")
    return frame, sha256(raw).hexdigest()


def load_or_build(sources: Path, checkpoint: Path, builder_script: Path) -> tuple[pd.DataFrame, str]:
    need(sources.is_dir() and not sources.is_symlink() and checkpoint.parent.is_dir() and
         not checkpoint.parent.is_symlink() and builder_script.is_file() and
         not builder_script.is_symlink(), "LOCAL_SOURCE_SCOPE_INVALID")
    need(sha256((sources / "TRL-R060-V20-Cash-Parity-2023-2026-Reproducible.zip").read_bytes()).hexdigest() == SOURCE_SHA and
         sha256((sources / "CNYRUBF_260830_261116.csv").read_bytes()).hexdigest() == TERMINAL_SHA,
         "RAW_ORIGINAL_SOURCE_SHA_MISMATCH")
    if not checkpoint.exists():
        modspec = importlib.util.spec_from_file_location("r070_cny_original_builder", str(builder_script))
        need(modspec is not None and modspec.loader is not None, "BUILDER_LOAD_INVALID")
        module = importlib.util.module_from_spec(modspec)
        modspec.loader.exec_module(module)
        result = module.build(sources, checkpoint)
        need(result.get("status") == "OFFLINE_CNY_M15_CHECKPOINT_PASS_NOT_LIVE" and
             result.get("history_sha256") == HISTORY_SHA, "BUILDER_VERIFICATION_FAILED")
    return exact_checkpoint(checkpoint)


def price_equals(a, b, step: Decimal) -> bool:
    """Accept only binary float representation noise, never one exchange tick."""
    try:
        original = Decimal(str(a))
        received = Decimal(str(b))
        gap = abs(original - received)
        return (original.is_finite() and received.is_finite()
                and step > 0 and gap <= step * Decimal("0.000000001"))
    except (InvalidOperation, ValueError, TypeError):
        return False


def parse_finam_bars(body: dict, from_utc: datetime, to_utc: datetime, parse_decimal) -> pd.DataFrame:
    need(isinstance(body, dict) and body.get("symbol") in (None, FINAM) and
         isinstance(body.get("bars"), list) and body["bars"], "FINAM_M15_RESPONSE_INVALID")
    rows = []
    prev = None
    for bar in body["bars"]:
        need(isinstance(bar, dict) and isinstance(bar.get("timestamp"), str), "FINAM_M15_ROW_INVALID")
        try:
            at = datetime.fromisoformat(bar["timestamp"].replace("Z", "+00:00"))
            need(at.tzinfo is not None, "FINAM_TIMESTAMP_WITHOUT_ZONE")
            t = at.astimezone(UTC)
            need(from_utc <= t < to_utc and (prev is None or t > prev) and
                 not (t.minute % 15 or t.second or t.microsecond), "FINAM_M15_SEQUENCE_OR_TIME")
            values = [parse_decimal(bar.get(x)) for x in ("open", "high", "low", "close", "volume")]
            need(all(v.is_finite() for v in values) and all(v > 0 for v in values[:4]) and
                 values[4] >= 0 and values[1] >= max(values[0], values[2], values[3]) and
                 values[2] <= min(values[0], values[1], values[3]), "FINAM_M15_OHLCV_INVALID")
            msk = t.astimezone(MOSCOW).replace(tzinfo=None)
            rows.append((msk, *values))
            prev = t
        except (ValueError, KeyError, TypeError, InvalidOperation) as exc:
            raise Hold("R070_CNY_FINAM_M15_PARSE_INVALID") from exc
    return pd.DataFrame(rows, columns=["Datetime", "Open", "High", "Low", "Close", "Volume"])


def compare(checkpoint: pd.DataFrame, broker: pd.DataFrame, clock_utc: datetime, tick: Decimal) -> dict:
    now_msk = clock_utc.astimezone(MOSCOW).replace(tzinfo=None)
    need(now_msk.date() == LATEST_ALLOWED_DATE and now_msk >= datetime(2026, 11, 17, 11, 15),
         "PHYSICAL_DATE_NOT_17NOV_OR_TOO_EARLY")
    boundary = (now_msk - timedelta(minutes=2)).replace(second=0, microsecond=0)
    boundary = boundary.replace(minute=boundary.minute // 15 * 15)
    end = boundary - timedelta(minutes=15)
    need(datetime(2026, 11, 17, 10, 0) <= end <= datetime(2026, 11, 17, 17, 45),
         "FINAL_COMPLETED_SESSION_BAR_INVALID")
    h = checkpoint.set_index("Datetime")
    f = broker.set_index("Datetime")
    common = h.index.intersection(f.index)
    need(len(common) >= 4 and h.index[-1] == ORIGINAL_END and
         any(t.date() == ORIGINAL_END.date() for t in common), "FINAM_HISTORICAL_OVERLAP_MISSING")
    matches = 0
    for t in common:
        hv = h.loc[t]; bv = f.loc[t]
        need(all(price_equals(hv[k], bv[k], tick) for k in ("Open", "High", "Low", "Close")) and
             Decimal(str(hv["Volume"])) == Decimal(str(bv["Volume"])),
             "FINAM_HISTORICAL_OHLCV_DISAGREEMENT")
        matches += 1
    for day, final_time in [(date(2026, 11, 15), "17:45"),
                            (date(2026, 11, 16), "17:45"),
                            (date(2026, 11, 17), end.strftime("%H:%M"))]:
        expected = pd.date_range(f"{day} 10:00", f"{day} {final_time}", freq="15min")
        observed = f.index[(f.index.date == day) & (f.index.hour >= 10) &
                           ((f.index.hour < 17) | ((f.index.hour == 17) & (f.index.minute <= 45)))]
        if day == date(2026, 11, 17):
            observed = observed[observed <= end]
        need(observed.equals(expected), "FINAM_SESSION_M15_MISSING_" + str(day).replace("-", ""))
    fresh = f.loc[(f.index > h.index[-1]) & (f.index <= end)]
    need(not fresh.empty and fresh.index[-1] == end, "FINAM_LAST_M15_NOT_FRESH")
    return {"status": "PASS_CNYRUBF_FRESH_M15_READONLY_NO_LIVE", "overlap_verified": matches,
            "new_completed_m15": len(fresh), "last_completed_open_msk": end.isoformat(),
            "m15_missing": 0, "account_bound_sqlite": False, "live_authorized": False,
            "orders_sent": 0, "orders_cancelled": 0}


def fetch_from_finam(*, token: str, account: str, start: datetime,
                     until: datetime, source_dir: Path):
    sys.path.insert(0, str(source_dir))
    from TradingSystemLab.stage8_robot.finam_api import (FinamAPI, SESSION_PATH, SESSION_DETAILS_PATH)
    from TradingSystemLab.stage8_robot.margin import parse_rest_decimal_value_object

    class GETOnly(FinamAPI):
        bound = False

        def _request(self, method, path, payload=None, auth=True, retries=0):
            auth_call = (method == "POST" and auth is False and isinstance(payload, dict)
                         and ((path == SESSION_PATH and set(payload) == {"secret"})
                              or (path == SESSION_DETAILS_PATH and set(payload) == {"token"})))
            allowed_get = False
            if (method == "GET" and auth is True and payload is None and self.bound):
                q = urlparse(path)
                if not q.fragment and not q.params and q.path == f"/v1/instruments/{FINAM}/bars":
                    try:
                        fields = parse_qs(q.query, strict_parsing=True)
                        if (set(fields) == {"timeframe", "interval.start_time", "interval.end_time"}
                                and fields["timeframe"] == ["TIME_FRAME_M15"]):
                            a = datetime.fromisoformat(fields["interval.start_time"][0]); b = datetime.fromisoformat(fields["interval.end_time"][0])
                            allowed_get = (a.tzinfo is not None and b.tzinfo is not None
                                           and start <= a <= b <= until and (b-a) <= timedelta(days=3))
                    except (ValueError, KeyError, TypeError):
                        pass
            need(auth_call or allowed_get, "FINAM_NON_READONLY_HTTP_BLOCKED")
            return super()._request(method, path, payload=payload, auth=auth, retries=retries)

    api = GETOnly(token)
    api.create_session(); details = api.session_details()
    need(isinstance(details, dict) and details.get("readonly") is False and
         isinstance(details.get("account_ids"), list) and
         details["account_ids"].count(account) == 1,
         "FINAM_EXACT_TRADING_ACCOUNT_BINDING_FAILED")
    api.bound = True
    query = urlencode({"timeframe": "TIME_FRAME_M15",
                       "interval.start_time": start.isoformat(),
                       "interval.end_time": until.isoformat()})
    response = api._request("GET", f"/v1/instruments/{FINAM}/bars?" + query).body
    return parse_finam_bars(response, start, until, parse_rest_decimal_value_object)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--robot", choices=("v20-shallow", "v20-obv"), required=True)
    parser.add_argument("--builder", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    need(os.name == "nt" and os.environ.get("COMPUTERNAME", "").upper() == "URIU-PC" and
         root.name.casefold() == "v20lab" and not root.is_symlink(), "PHYSICAL_INTEL_V20_ONLY")
    account = os.environ.get("V20_FINAM_ACCOUNT", "")
    token = os.environ.get("V20_FINAM_TOKEN", "")
    scope = os.environ.get("V20_FINAM_ACCOUNT_SHA256", "")
    need(bool(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", account)) and
         bool(token) and bool(re.fullmatch(r"[0-9a-f]{64}", scope)) and
         sha256(account.encode("utf-8")).hexdigest() == scope, "DPAPI_ACCOUNT_SCOPE_INVALID")
    sources = root / "r070-candidate" / "sources"
    work = root / "r070-candidate" / "m15"
    work.mkdir(parents=True, exist_ok=True)
    checkpoint, digest = load_or_build(sources, work / ARCHIVE, args.builder)
    observed = datetime.now(UTC)
    local = observed.astimezone(MOSCOW)
    need(local.date() == LATEST_ALLOWED_DATE, "PHYSICAL_DATE_NOT_17NOV")
    start = datetime(2026, 11, 15, 7, 0, tzinfo=UTC)
    end = observed - timedelta(minutes=1)
    broker = fetch_from_finam(token=token, account=account, start=start,
                              until=end, source_dir=root / "source-raw")
    from TradingSystemLab.stage8_robot.production_runtime import _load_registry
    tick = Decimal(str(_load_registry()[TARGET]["price_step"]))
    outcome = compare(checkpoint, broker, observed, tick)
    outcome.update({"schema": "r070.cny.finam_readonly_physical.v1", "robot": args.robot,
                    "account_sha256": scope, "checkpoint_history_sha256": HISTORY_SHA,
                    "checkpoint_file_sha256": digest,
                    "source_r060_zip_sha256": SOURCE_SHA,
                    "source_terminal_csv_sha256": TERMINAL_SHA,
                    "observed_at_utc": observed.isoformat(),
                    "readonly_http_method": "FINAM GET /bars only plus session authentication",
                    "report_contains_token_or_account_id": False})
    report = work / ("r070-cny-physical-" + args.robot + "-20261117.json")
    need(not report.exists() and not report.is_symlink(), "REPORT_ALREADY_EXISTS")
    with report.open("x", encoding="utf-8") as out:
        json.dump(outcome, out, indent=2, ensure_ascii=False)
    print("R070_" + args.robot.replace("-", "_").upper() + "_CNY_PHYSICAL_READONLY=PASS")
    print("R070_CNY_LAST_COMPLETED_OPEN_MSK=" + outcome["last_completed_open_msk"])
    print("R070_CNY_BROKER_OVERLAP=" + str(outcome["overlap_verified"]))
    print("R070_CNY_NO_ORDER_NO_CANCEL_NO_LIVE_CHANGE=YES")


if __name__ == "__main__":
    try:
        main()
    except Hold as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
