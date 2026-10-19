#!/usr/bin/env python3
"""Anonymous ALOR production market-data downloader, Python 3.12, stdlib only.

No trading endpoints, credentials, external proxies, generated candles or rolls.
Synthetic tests are separate; real provider acceptance has NOT been established
in Codex. UTC+03 is Europe/Moscow throughout this study's 2020--2026 interval.
"""
import argparse
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

VERSION = 'alor-m15-1'
BASE = 'https://api.alor.ru'
STEP = 900
MSK = timezone(timedelta(hours=3), 'Europe/Moscow')
UTC = timezone.utc
MARKETS = ('Si', 'CNY', 'GD', 'MIX', 'BR', 'NG')
ROOTS = {'Si': ('Si',), 'CNY': ('CNY',), 'GD': ('GOLD', 'GD'),
         'MIX': ('MIX',), 'BR': ('BR',), 'NG': ('NG',)}
FIELDS = ('open', 'high', 'low', 'close', 'volume')
SYMBOL = re.compile(r'^(Si|CNY|GOLD|GD|MIX|BR|NG)-(0?[1-9]|1[0-2])\.(20\d{2}|\d{2})$')
MAX_BODY = 16 * 1024 * 1024


class DataError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise DataError(message)


def now():
    return datetime.now(UTC).isoformat()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + '\n').encode('utf-8')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def immutable(path, body):
    """Never overwrite raw data, receipts, checkpoints or original settings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_bytes() == body, f'OVERWRITE_REFUSED: {path}')
        return
    with path.open('xb') as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())


def snapshot(root, name, value):
    """Versioned derived report plus atomically replaced convenience pointer."""
    body = encoded(value)
    immutable(root / 'reports' / f'{name}-{sha(body)}.json', body)
    tmp = root / f'.{name}-{uuid.uuid4().hex}.tmp'
    immutable(tmp, body)
    os.replace(tmp, root / f'{name}.json')


def load(path):
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError) as exc:
        raise DataError(f'INVALID_JSON_FILE: {path}: {exc}') from exc


def parse_json(body):
    try:
        return json.loads(body, parse_float=Decimal,
                          parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, UnicodeError) as exc:
        raise DataError(f'INVALID_PROVIDER_JSON: {exc}') from exc


def integer(value, label):
    require(isinstance(value, int) and not isinstance(value, bool), f'INVALID_INTEGER: {label}')
    return value


def numeric(value, label):
    require(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool),
            f'INVALID_NUMBER: {label}')
    n = Decimal(str(value))
    require(n.is_finite(), f'NONFINITE_NUMBER: {label}')
    return n


def canonical_number(value):
    return format(value.normalize(), 'f')


def parse_history(body, start, end):
    """Validate all returned bars; no clipping, repair, filling or silent sorting."""
    obj = parse_json(body)
    require(isinstance(obj, dict) and isinstance(obj.get('history'), list), 'HISTORY_SCHEMA')
    rows, duplicates = {}, 0
    previous = None
    for r in obj['history']:
        require(isinstance(r, dict) and all(k in r for k in ('time',) + FIELDS), 'BAR_SCHEMA')
        t = integer(r['time'], 'time')
        require(start <= t < end, f'OUT_OF_REQUEST_RANGE: {t} not [{start},{end})')
        require(t % STEP == 0, f'NOT_M15_BOUNDARY: {t}')
        require(previous is None or t >= previous, 'NONMONOTONIC_HISTORY')
        previous = t
        x = {k: numeric(r[k], k) for k in FIELDS}
        require(all(x[k] > 0 for k in FIELDS[:4]), 'NONPOSITIVE_PRICE')
        require(x['low'] <= min(x['open'], x['close']) <= max(x['open'], x['close']) <= x['high'],
                'OHLC_INEQUALITY')
        require(x['volume'] >= 0, 'NEGATIVE_VOLUME')
        bar = dict(time=t, **{k: canonical_number(x[k]) for k in FIELDS})
        if t in rows:
            require(rows[t] == bar, f'CONFLICTING_DUPLICATE: {t}')
            duplicates += 1
        rows[t] = bar
    for key in ('next', 'prev'):
        if obj.get(key) is not None:
            integer(obj[key], key)
            require(obj[key] % STEP == 0, 'INVALID_NEIGHBOR_BOUNDARY')
    return list(rows.values()), dict(next=obj.get('next'), prev=obj.get('prev'),
                                     identical_duplicates=duplicates)


def merge_bars(parts):
    merged = {}
    for part in parts:
        for r in part:
            t = r['time']
            require(t not in merged or merged[t] == r, f'CONFLICTING_FRAGMENT: {t}')
            merged[t] = r
    return [merged[t] for t in sorted(merged)]


def url_for(path, params):
    require(path in ('/md/v2/history', '/md/v2/Securities'), 'ENDPOINT_NOT_PUBLIC_ALLOWLIST')
    require(not any(k.lower() in ('token', 'authorization', 'access_token', 'countback') for k in params),
            'FORBIDDEN_REQUEST_PARAMETER')
    return BASE + path + '?' + urllib.parse.urlencode(sorted(params.items()))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def network_get(url):
    """No authentication/cookie handlers, no proxy/TLS overrides, no redirects."""
    require(url.startswith(BASE + '/md/v2/'), 'PRODUCTION_ONLY')
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(urllib.request.Request(url, headers={'Accept': 'application/json'}, method='GET'),
                         timeout=45) as response:
            body = response.read(MAX_BODY + 1)
            require(len(body) <= MAX_BODY, 'RESPONSE_TOO_LARGE')
            return response.status, body, dict(content_type=response.headers.get('Content-Type'))
    except urllib.error.HTTPError as exc:
        body = exc.read(MAX_BODY + 1)
        require(len(body) <= MAX_BODY, 'ERROR_RESPONSE_TOO_LARGE')
        return exc.code, body, dict(retry_after=exc.headers.get('Retry-After'))
    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if 'Tunnel connection failed: 403' in reason:
            kind = 'PROXY_CONNECT_403_BEFORE_PROVIDER'
        elif isinstance(exc.reason, socket.gaierror):
            kind = 'DNS_ERROR'
        elif isinstance(exc.reason, ssl.SSLError):
            kind = 'TLS_ERROR'
        else:
            kind = 'CONNECT_OR_TIMEOUT_ERROR'
        raise DataError(f'{kind}: {reason}') from exc


class Client:
    def __init__(self, output, delay=1.0, retry_failed=False, budget=20000, transport=None):
        self.root = Path(output)
        self.delay = max(1.0, delay)
        self.retry_failed = retry_failed
        self.budget = budget
        self.transport = transport or network_get
        self.last_call = 0.0
        self.new_requests = 0

    def get(self, path, params, *, replica=False):
        url = url_for(path, params)
        request = dict(method='GET', url=url, replica=replica, version=VERSION)
        key = sha(encoded(request))
        folder = self.root / 'requests' / key
        attempts = sorted(folder.glob('attempt-*')) if folder.exists() else []
        for attempt in reversed(attempts):
            receipt_path = attempt / 'receipt.json'
            require(receipt_path.exists(), f'INTERRUPTED_REQUEST_REQUIRES_REVIEW: {attempt}')
            receipt = load(receipt_path)
            require(receipt['request'] == request, 'CACHE_REQUEST_MISMATCH')
            if receipt.get('raw_sha256'):
                raw = attempt / 'response.json'
                require(raw.exists() and sha(raw.read_bytes()) == receipt['raw_sha256'], 'CACHE_SHA256_MISMATCH')
            if receipt['status'] == 200:
                return (attempt / 'response.json').read_bytes(), str(receipt_path.relative_to(self.root))
            require(self.retry_failed, f'CACHED_FAILURE_NO_AUTOMATIC_RETRY: {receipt.get("error", receipt["status"])}')
            if receipt.get('retry_not_before_epoch'):
                require(time.time() >= receipt['retry_not_before_epoch'], 'RETRY_AFTER_NOT_ELAPSED')
            break
        require(self.new_requests < self.budget, 'REQUEST_BUDGET_EXHAUSTED_RESUME_SAME_COMMAND')
        attempt = folder / f'attempt-{len(attempts) + 1:04d}'
        immutable(attempt / 'request.json', encoded(request))
        wait = self.delay - (time.monotonic() - self.last_call)
        if wait > 0:
            time.sleep(wait)
        receipt = dict(request=request, checked_at_utc=now(), status=None,
                       provider_http_status=None, proxy_connect_status=None,
                       dns_connect_tls='NOT_SEPARATELY_OBSERVABLE_WITH_INHERITED_PROXY',
                       raw_sha256=None, bytes=0)
        self.new_requests += 1
        print(f'GET {url}' + (' [pilot stability repeat]' if replica else ''), flush=True)
        try:
            status, body, info = self.transport(url)
            immutable(attempt / 'response.json', body)
            receipt.update(status=status, provider_http_status=status, bytes=len(body), raw_sha256=sha(body))
            if status != 200:
                receipt['error'] = {400: 'PROVIDER_BAD_REQUEST', 401: 'PROVIDER_AUTH_REQUIRED',
                                    403: 'PROVIDER_FORBIDDEN', 404: 'PROVIDER_UNKNOWN_RESOURCE',
                                    429: 'PROVIDER_RATE_LIMIT'}.get(status, 'PROVIDER_HTTP_ERROR')
                if status == 429:
                    try:
                        receipt['retry_not_before_epoch'] = time.time() + max(60, int(info.get('retry_after') or 60))
                    except ValueError:
                        from email.utils import parsedate_to_datetime
                        receipt['retry_not_before_epoch'] = max(time.time() + 60,
                            parsedate_to_datetime(info['retry_after']).timestamp())
        except (DataError, OSError, TimeoutError) as exc:
            receipt['error'] = str(exc)
            if 'PROXY_CONNECT_403' in str(exc):
                receipt['proxy_connect_status'] = 403
        except KeyboardInterrupt:
            receipt['error'] = 'INTERRUPTED_BY_USER'
            raise
        finally:
            self.last_call = time.monotonic()
            immutable(attempt / 'receipt.json', encoded(receipt))
        require(receipt['status'] == 200, f'HTTP_OR_NETWORK_BLOCK: {receipt.get("error")}; receipt={attempt}')
        return body, str((attempt / 'receipt.json').relative_to(self.root))


def metadata_contract(row, receipt):
    require(isinstance(row, dict), 'SECURITY_SCHEMA')
    match = SYMBOL.fullmatch(str(row.get('symbol', '')))
    if not match:
        return None  # Never accept perpetuals, mini contracts, spot or prefix matches.
    root, month, year = match.groups()
    year = int(year) if len(year) == 4 else 2000 + int(year)
    require(2020 <= year <= 2027, 'CONTRACT_YEAR_OUTSIDE_DISCOVERY_SCOPE')
    market = next(m for m in MARKETS if root in ROOTS[m])
    require(row.get('exchange') == 'MOEX' and row.get('market') == 'FORTS', 'NOT_MOEX_FORTS')
    board = row.get('primary_board') or row.get('board')
    require(board == 'RFUD', 'UNVERIFIED_FUTURES_BOARD')
    kind = str(row.get('type', '')).lower()
    require(('фьючерс' in kind or 'future' in kind) and 'опцион' not in kind and 'option' not in kind,
            'NOT_CONFIRMED_FUTURE')
    require(str(row.get('cfiCode', '')).startswith('F'), 'FUTURES_CFI_REQUIRED')
    cancellation = row.get('cancellation')
    end = None
    if cancellation:
        try:
            # ALOR schema defines UTC even when the serialized offset is absent.
            d = datetime.fromisoformat(cancellation.replace('Z', '+00:00'))
            end = int(d.replace(tzinfo=UTC).timestamp()) if d.tzinfo is None else int(d.timestamp())
        except (ValueError, TypeError) as exc:
            raise DataError('INVALID_CANCELLATION_TIME') from exc
    require(end is not None, 'DATED_CONTRACT_COMPLETION_REQUIRED')
    underlying = row.get('underlyingSymbol')
    if underlying:
        require(underlying in ROOTS[market], 'CONFLICTING_UNDERLYING')
    return dict(market=market, alor_symbol=row['symbol'], exchange='MOEX', board=board,
                secid=row.get('SECID'), shortname=row.get('shortname'),
                contract_label_year=year, contract_label_month=int(month),
                identity='PUBLIC_ALOR_METADATA_CONFIRMED_NOT_INDEPENDENTLY_MOEX_CERTIFIED',
                underlying=market, underlying_evidence='canonical dated symbol + futures type + CFI',
                first_trade_utc=None, last_trade_utc=None, expiry_utc=None,
                provider_cancellation_utc=cancellation, provider_completion_epoch=end,
                metadata_receipt=receipt,
                date_limitation='cancellation is completion, not a proven first/last trade or futures expiry date')


def search(client, query):
    result, signatures = {}, set()
    for offset in range(0, 2000, 100):
        body, receipt = client.get('/md/v2/Securities', dict(query=query, exchange='MOEX',
                    sector='FORTS', format='Simple', limit=100, offset=offset))
        rows = parse_json(body)
        require(isinstance(rows, list) and len(rows) <= 100, 'SECURITIES_PAGE_SCHEMA_OR_LIMIT')
        signature = sha(encoded([r.get('symbol') for r in rows if isinstance(r, dict)]))
        require(not rows or signature not in signatures, 'SECURITIES_PAGINATION_NO_PROGRESS')
        signatures.add(signature)
        for row in rows:
            # Search may return unrelated instruments; they are never accepted.
            if not isinstance(row, dict) or not SYMBOL.fullmatch(str(row.get('symbol', ''))):
                continue
            y = SYMBOL.fullmatch(row['symbol']).group(3)
            if not 2020 <= (int(y) if len(y) == 4 else 2000 + int(y)) <= 2027:
                continue
            c = metadata_contract(row, receipt)
            if c:
                accept_contract(result, c)
        if len(rows) < 100:
            return list(result.values())
    raise DataError('SECURITIES_PAGINATION_LIMIT_REQUIRES_REVIEW')


def discover(client, markets, inventory):
    for market in markets:
        for root in ROOTS[market]:
            for c in search(client, root):
                if c['market'] == market:
                    accept_contract(inventory, c)


def accept_contract(inventory, contract):
    old = inventory.get(contract['alor_symbol'])
    if old:
        require({k: v for k, v in old.items() if k != 'metadata_receipt'} ==
                {k: v for k, v in contract.items() if k != 'metadata_receipt'},
                'CONTRACT_METADATA_CHANGED_REQUIRES_REVIEW')
    else:
        inventory[contract['alor_symbol']] = contract


def dated_candidates(client, market, year, month, inventory):
    # Candidate names are search terms only. They NEVER authorize a history request.
    for delta in range(4):
        ym = year * 12 + month - 1 + delta
        y, m = divmod(ym, 12)
        for root in ROOTS[market]:
            for c in search(client, f'{root}-{m + 1}.{y % 100:02d}'):
                if c['market'] == market:
                    accept_contract(inventory, c)


def history_params(contract, a, b):
    require(b > a, 'INVALID_RANGE')
    return dict(symbol=contract['alor_symbol'], exchange='MOEX', instrumentGroup=contract['board'],
                tf=STEP, **{'from': a, 'to': b - 1}, untraded='true', splitAdjust='false', format='Simple')


def history_range(client, contract, a, b, *, replica=False):
    """Bounded forward/backward neighbor traversal; no countBack range expansion.

    next/prev are candle neighbors, NOT opaque page tokens. Follow only strictly
    shrinking missing subranges inside the original interval. Never infer that
    absence of neighbors proves exchange-calendar completeness.
    """
    pending, seen, parts, receipts, diagnostics = [(a, b)], set(), [], [], []
    while pending:
        lo, hi = pending.pop()
        require((lo, hi) not in seen and len(seen) < 2048, 'HISTORY_PAGINATION_NO_PROGRESS')
        seen.add((lo, hi))
        body, receipt = client.get('/md/v2/history', history_params(contract, lo, hi), replica=replica)
        rows, d = parse_history(body, lo, hi)
        parts.append(rows)
        receipts.append(receipt)
        diagnostics.append(dict(start=lo, end_exclusive=hi, rows=len(rows), **d))
        low_edge = rows[0]['time'] if rows else hi
        high_edge = rows[-1]['time'] if rows else lo - STEP
        prev, nxt = d['prev'], d['next']
        if prev is not None and lo <= prev < hi:
            require(prev < low_edge, 'PREV_CURSOR_NOT_BEFORE_FIRST')
            sub = (lo, prev + STEP)
            require(sub != (lo, hi), 'PREV_CURSOR_NO_PROGRESS')
            pending.append(sub)
        if nxt is not None and lo <= nxt < hi:
            require(nxt > high_edge, 'NEXT_CURSOR_NOT_AFTER_LAST')
            sub = (nxt, hi)
            require(sub != (lo, hi), 'NEXT_CURSOR_NO_PROGRESS')
            pending.append(sub)
    return merge_bars(parts), receipts, diagnostics


def epoch(day):
    return int(datetime.combine(date.fromisoformat(day), datetime.min.time(), MSK).timestamp())


def windows(start, end, days=7):
    while start < end:
        stop = min(start + days * 86400, end)
        yield start, stop
        start = stop


def choose_contract(inventory, market, start, end):
    month = datetime.fromtimestamp(start, MSK).date()
    candidates = [c for c in inventory.values() if c['market'] == market
                  and (c['contract_label_year'], c['contract_label_month']) >= (month.year, month.month)
                  and c['contract_label_year'] * 12 + c['contract_label_month'] <= month.year * 12 + month.month + 3
                  and c['provider_completion_epoch'] >= end - 86400]
    # This chooses a DATA SAMPLE, never an active-contract roll or a trade series.
    return min(candidates, key=lambda c: (c['provider_completion_epoch'], c['alor_symbol'])) if candidates else None


def sample(client, inventory, market, start, end, label, end_epoch_cap=None):
    a, b = epoch(start), epoch(end)
    if end_epoch_cap is not None:
        b = min(b, end_epoch_cap)
    require(b > a, 'SAMPLE_AFTER_COMPLETED_DATA_CUTOFF')
    c = choose_contract(inventory, market, a, b)
    if c is None:
        d = date.fromisoformat(start)
        dated_candidates(client, market, d.year, d.month, inventory)
        c = choose_contract(inventory, market, a, b)
    r = dict(label=label, market=market, from_utc=a, to_exclusive_utc=b,
             status='METADATA_NOT_FOUND', contract=None)
    if c is None:
        return r
    rows, receipts, diagnostics = history_range(client, c, a, b)
    r.update(contract=c['alor_symbol'], rows=len(rows), receipts=receipts, diagnostics=diagnostics)
    if not rows:
        r['status'] = 'HTTP200_EMPTY_NOT_PROOF_OF_DELETION'
        return r
    if len(rows) < 2 or not any(y['time'] - x['time'] == STEP for x, y in zip(rows, rows[1:])):
        r['status'] = 'INSUFFICIENT_M15_ADJACENCY'
        return r
    again, repeated, _ = history_range(client, c, a, b, replica=True)
    require(rows == again, 'PILOT_OHLCV_CHANGED_ON_REPEAT')
    r.update(status='PASS', first_observed_utc=rows[0]['time'], last_observed_utc=rows[-1]['time'],
             semantic_sha256=sha(encoded(rows)), repeated_receipts=repeated,
             repeat_reason='one explicit independent pilot repeat to check price stability')
    return r


def probe(client, config, inventory):
    discover(client, ('Si', 'GD', 'CNY'), inventory)
    samples = []
    for market in ('Si', 'GD'):
        for start, end, label in [('2020-01-09', '2020-01-11', '2020'),
                                  ('2024-04-02', '2024-04-04', '2024'),
                                  ('2026-09-01', '2026-09-03', '2026')]:
            samples.append(sample(client, inventory, market, start, end, market + '_' + label))
    for start, end, label in [('2024-04-02', '2024-04-04', 'CNY_2024'),
                              ('2026-09-01', '2026-09-03', 'CNY_2026')]:
        samples.append(sample(client, inventory, 'CNY', start, end, label))
    # Oldest identity-confirmed CNY contract, bounded availability discovery.
    cny = sorted((c for c in inventory.values() if c['market'] == 'CNY'),
                 key=lambda c: (c['provider_completion_epoch'], c['alor_symbol']))
    first = dict(label='CNY_FIRST_OBSERVED', market='CNY', status='FIRST_AVAILABILITY_NOT_ESTABLISHED')
    if cny:
        c = cny[0]
        a, b = config['start_epoch'], min(config['start_epoch'] + 2 * 86400, config['end_epoch'])
        rows, receipts, d = history_range(client, c, a, b)
        hinted = rows[0]['time'] if rows else next((x['next'] for x in d if x['next'] is not None and
                                                   b <= x['next'] < config['end_epoch']), None)
        if hinted is not None:
            day = datetime.fromtimestamp(hinted, MSK).date()
            first = sample(client, {c['alor_symbol']: c}, 'CNY', day.isoformat(),
                           (day + timedelta(days=2)).isoformat(), 'CNY_FIRST_OBSERVED', config['end_epoch'])
            first['availability_discovery_receipts'] = receipts
            first['limitation'] = 'First tested availability, not certified listing date or provider retention limit'
    samples.append(first)
    recent = [r for r in samples if r['label'] not in ('Si_2020', 'GD_2020')]
    status = 'PASS' if all(r['status'] == 'PASS' for r in samples) else (
        'PASS_AVAILABLE_PARTIAL' if all(r['status'] == 'PASS' for r in recent) else 'BLOCKED_OR_PARTIAL')
    result = dict(status=status, created_at_utc=now(), script_sha256=sha(Path(__file__).read_bytes()),
                  config_sha256=sha(encoded(config)), samples=samples,
                  calendar_completeness='NOT_CERTIFIED', start_end_label='ASSUMED_OPEN_REQUIRES_CROSS_SOURCE_AUDIT',
                  h1_m30_comparison='NOT_COMPARABLE_AUTOMATICALLY_DIFFERENT_CONTRACTS_AND_UNKNOWN_ROLLS',
                  anonymous_untraded_result='TESTED_ONLY_FOR_METADATA_CONFIRMED_SAMPLES',
                  retention_limit='UNKNOWN; empty history is not proof it was deleted')
    snapshot(client.root, 'probe_result', result)
    return result


def verify_store(root):
    receipts = []
    for path in sorted((root / 'requests').glob('*/attempt-*/receipt.json')):
        r = load(path)
        url = urllib.parse.urlsplit(r['request']['url'])
        require(url.scheme == 'https' and url.netloc == 'api.alor.ru' and
                url.path in ('/md/v2/history', '/md/v2/Securities'), 'UNEXPECTED_MANIFEST_ORIGIN')
        raw = path.parent / 'response.json'
        if r['raw_sha256']:
            require(raw.exists() and sha(raw.read_bytes()) == r['raw_sha256'], 'STORED_RAW_SHA256_MISMATCH')
            require(len(raw.read_bytes()) == r['bytes'], 'STORED_RAW_LENGTH_MISMATCH')
        if r['status'] == 200:
            if url.path.endswith('/history'):
                q = urllib.parse.parse_qs(url.query)
                parse_history(raw.read_bytes(), int(q['from'][0]), int(q['to'][0]) + 1)
            else:
                require(isinstance(parse_json(raw.read_bytes()), list), 'STORED_METADATA_SCHEMA')
        receipts.append(dict(path=str(path.relative_to(root)), **r))
    for path in (root / 'requests').glob('*/attempt-*'):
        require((path / 'receipt.json').exists(), f'INTERRUPTED_REQUEST_REQUIRES_REVIEW: {path}')
    return receipts


def manifest(root, config, inventory, status):
    receipts = verify_store(root)
    bars_by_symbol = {}
    for r in receipts:
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(r['request']['url']).query)
        if r['status'] != 200 or '/md/v2/history?' not in r['request']['url']:
            continue
        symbol = q['symbol'][0]
        body = (root / Path(r['path']).parent / 'response.json').read_bytes()
        rows, _ = parse_history(body, int(q['from'][0]), int(q['to'][0]) + 1)
        bars_by_symbol.setdefault(symbol, []).append(rows)
    coverage = []
    for symbol, parts in sorted(bars_by_symbol.items()):
        rows = merge_bars(parts)
        years = {}
        for row in rows:
            year = datetime.fromtimestamp(row['time'], MSK).year
            years[str(year)] = years.get(str(year), 0) + 1
        gaps = sum(b['time'] - a['time'] > STEP for a, b in zip(rows, rows[1:]))
        coverage.append(dict(symbol=symbol, market=inventory.get(symbol, {}).get('market'),
                             distinct_contract_bars=len(rows), counts_by_moscow_open_year=years,
                             first_observed_utc=rows[0]['time'] if rows else None,
                             last_observed_utc=rows[-1]['time'] if rows else None,
                             observed_gap_pairs=gaps, gaps_are_not_automatically_data_errors=True))
    annual = []
    for market in MARKETS:
        for year in range(2020, 2027):
            n = sum(c['counts_by_moscow_open_year'].get(str(year), 0) for c in coverage if c['market'] == market)
            annual.append(dict(market=market, year=year,
                               distinct_contract_bars=n if n else None,
                               state='OBSERVED_CONTRACT_BARS_NOT_CONTINUOUS_SERIES' if n else 'NO_DATA',
                               calendar_complete=False))
    unresolved = []
    for r in receipts:
        if r['status'] == 200 and '/md/v2/Securities?' in r['request']['url']:
            rows = parse_json((root / Path(r['path']).parent / 'response.json').read_bytes())
            if not rows:
                unresolved.append(dict(url=r['request']['url'], result='NO_METADATA_IN_THIS_RESPONSE_NOT_PROOF_OF_NO_CONTRACT'))
    value = dict(version=VERSION, generated_at_utc=now(), status=status, config=config,
                 acquisition_status='PARTIAL_UNAUDITED' if any(c['distinct_contract_bars'] for c in coverage) else 'BLOCKED_NO_CANDLES',
                 probe_status=load(root / 'probe_result.json').get('status') if (root / 'probe_result.json').exists() else 'NOT_RUN',
                 download_status=load(root / 'download_result.json').get('status') if (root / 'download_result.json').exists() else 'NOT_RUN',
                 contracts=sorted(inventory.values(), key=lambda c: c['alor_symbol']),
                 requests=receipts, coverage=coverage, coverage_by_market_year=annual,
                 empty_metadata_responses=unresolved, roll_rule=None, continuous_series_created=False,
                 calendar_completeness='UNKNOWN_WITHOUT_EXCHANGE_CALENDAR',
                 identity_scope='ALOR public metadata only; no independent MOEX identity certification',
                 actual_retention_limit='NOT_ESTABLISHED', h1_m30_comparison='NOT_RUN',
                 strategy_replay='NOT_RUN', tokens_used=False)
    snapshot(root, 'manifest', value)
    return value


def download(client, config, inventory, chunk_days):
    gate = load(client.root / 'probe_result.json')
    require(gate['status'] in ('PASS', 'PASS_AVAILABLE_PARTIAL'), 'SUCCESSFUL_PROBE_REQUIRED')
    require(gate['script_sha256'] == sha(Path(__file__).read_bytes()) and
            gate['config_sha256'] == sha(encoded(config)), 'PROBE_CODE_OR_CONFIG_CHANGED_RERUN_PROBE')
    required_labels = {f'{m}_{y}' for m in ('Si', 'GD') for y in ('2020', '2024', '2026')} | {
        'CNY_2024', 'CNY_2026', 'CNY_FIRST_OBSERVED'}
    samples = {r['label']: r for r in gate.get('samples', [])}
    require(set(samples) == required_labels, 'PROBE_SAMPLE_SET_INVALID')
    recent = required_labels - {'Si_2020', 'GD_2020'}
    require(all(samples[x]['status'] == 'PASS' and samples[x]['rows'] > 0 for x in recent),
            'PROBE_RECENT_SAMPLES_NOT_PASSED')
    if gate['status'] == 'PASS':
        require(all(samples[x]['status'] == 'PASS' for x in required_labels), 'PROBE_STATUS_INCONSISTENT')
    verify_store(client.root)
    discover(client, MARKETS, inventory)
    # Search calendar names for ALL months: BR/NG have no imposed quarterly cycle.
    for market in MARKETS:
        for year in range(2020, 2028):
            for month in range(1, 13):
                for root in ROOTS[market]:
                    for c in search(client, f'{root}-{month}.{year % 100:02d}'):
                        if c['market'] == market:
                            accept_contract(inventory, c)
    snapshot(client.root, 'contracts', dict(contracts=list(inventory.values())))
    for contract in sorted(inventory.values(), key=lambda c: (c['market'], c['provider_completion_epoch'])):
        print(f'DOWNLOAD separate contract {contract["market"]} {contract["alor_symbol"]}', flush=True)
        # No guessed first listing: request the study range, clipped only by
        # provider completion + one day (completion may be serialized midnight).
        end = min(config['end_epoch'], contract['provider_completion_epoch'] + 86400)
        for a, b in windows(config['start_epoch'], end, chunk_days):
            rows, receipts, diagnostics = history_range(client, contract, a, b)
            checkpoint = dict(contract=contract['alor_symbol'], start=a, end_exclusive=b,
                              rows=len(rows), receipts=receipts, diagnostics=diagnostics,
                              completeness='OBSERVED_RESPONSE_ONLY' if rows else 'HTTP200_EMPTY')
            immutable(client.root / 'chunks' / (sha(encoded(checkpoint)) + '.json'), encoded(checkpoint))
    return 'DOWNLOAD_FINISHED_COMPLETENESS_UNVERIFIED'


@contextmanager
def output_lock(root):
    path = root / '.downloader.lock'
    try:
        with path.open('x', encoding='utf-8') as f:
            f.write(f'pid={os.getpid()} created={now()}\n')
    except FileExistsError as exc:
        raise DataError('OUTPUT_LOCKED: another process or interrupted run; inspect before removing lock') from exc
    try:
        yield
    finally:
        path.unlink()


def configuration(root, args):
    request = dict(start_date=args.start_date, end_date_inclusive=args.end_date,
                   production_base=BASE, tf=STEP, markets=list(MARKETS), version=VERSION,
                   chunk_days=args.chunk_days)
    require('2020-01-01' <= args.start_date <= args.end_date <= '2026-10-19', 'STUDY_DATE_RANGE')
    path = root / 'settings.json'
    if path.exists():
        result = load(path)
        require(result['requested'] == request, 'SETTINGS_CHANGED_USE_NEW_OUTPUT_DIRECTORY')
        return result
    start = epoch(args.start_date)
    requested_end = epoch((date.fromisoformat(args.end_date) + timedelta(days=1)).isoformat())
    # Anonymous data delay plus candle completion; frozen once for resumability.
    end = min(requested_end, (int(time.time()) - STEP) // STEP * STEP)
    require(end > start, 'NO_COMPLETED_STUDY_INTERVAL')
    result = dict(requested=request, start_epoch=start, end_epoch=end, frozen_at_utc=now(),
                  timestamp_convention='UTC_UNIX_SECONDS; OPEN_LABEL_ASSUMED_PENDING_AUDIT',
                  timezone='Europe/Moscow = UTC+03 throughout 2020--2026')
    immutable(path, encoded(result))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('probe', 'download', 'verify'), required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--start-date', default='2020-01-01')
    parser.add_argument('--end-date', default='2026-10-19', help='inclusive Moscow date')
    parser.add_argument('--chunk-days', type=int, choices=range(1, 8), default=7)
    parser.add_argument('--request-delay', type=float, default=1.0)
    parser.add_argument('--max-new-requests', type=int, default=20000)
    parser.add_argument('--retry-failed', action='store_true', help='explicit new attempt; never overwrites prior receipts')
    args = parser.parse_args(argv)
    root = args.output_dir.expanduser().resolve()
    require(math.isfinite(args.request_delay) and 1 <= args.request_delay <= 60, 'REQUEST_DELAY_MUST_BE_1_TO_60_SECONDS')
    require(1 <= args.max_new_requests <= 100000, 'REQUEST_BUDGET_MUST_BE_1_TO_100000')
    # Standalone on Windows; reject a Git checkout and its descendants as output.
    require(not any((p / '.git').exists() for p in (root,) + tuple(root.parents)), 'RAW_OUTPUT_MUST_BE_OUTSIDE_GIT_REPOSITORY')
    root.mkdir(parents=True, exist_ok=True)
    with output_lock(root):
        if args.mode == 'verify':
            require((root / 'settings.json').exists(), 'NO_SETTINGS_TO_VERIFY')
            config = load(root / 'settings.json')
        else:
            config = configuration(root, args)
        inventory = {}
        if (root / 'contracts.json').exists():
            inventory = {c['alor_symbol']: c for c in load(root / 'contracts.json')['contracts']}
        client = Client(root, args.request_delay, args.retry_failed, args.max_new_requests)
        status = 'NOT_RUN'
        code = 0
        try:
            if args.mode == 'probe':
                snapshot(root, 'probe_result', dict(status='IN_PROGRESS_NOT_AUTHORIZED_FOR_DOWNLOAD', created_at_utc=now()))
                result = probe(client, config, inventory)
                status = result['status']
                code = 0 if status in ('PASS', 'PASS_AVAILABLE_PARTIAL') else 2
            elif args.mode == 'download':
                snapshot(root, 'download_result', dict(status='IN_PROGRESS', time_utc=now()))
                status = download(client, config, inventory, args.chunk_days)
                snapshot(root, 'download_result', dict(status=status, time_utc=now()))
            else:
                verify_store(root)
                status = 'RAW_SHA256_AND_SCHEMAS_VERIFIED_NOT_CALENDAR_COMPLETENESS'
        except (DataError, OSError, ValueError) as exc:
            status, code = 'BLOCKED_OR_INTERRUPTED', 2
            snapshot(root, 'last_error', dict(error=str(exc), time_utc=now(), mode=args.mode))
            if args.mode == 'download':
                snapshot(root, 'download_result', dict(status=status, time_utc=now()))
            print(f'ERROR: {exc}', file=sys.stderr)
        except KeyboardInterrupt:
            status, code = 'INTERRUPTED_BY_USER', 130
            snapshot(root, 'last_error', dict(error='KeyboardInterrupt', time_utc=now(), mode=args.mode))
            if args.mode == 'download':
                snapshot(root, 'download_result', dict(status=status, time_utc=now()))
            print('INTERRUPTED: receipts preserved; rerun with --retry-failed for an interrupted GET', file=sys.stderr)
        finally:
            snapshot(root, 'contracts', dict(contracts=list(inventory.values())))
            manifest(root, config, inventory, status)
        print(f'{status}; new GET requests={client.new_requests}; output={root}')
        return code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (DataError, OSError, ValueError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(2)
