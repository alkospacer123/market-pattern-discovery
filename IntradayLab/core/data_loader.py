"""Read only pinned, exact development bytes; never open future OHLC fields."""
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
from pathlib import Path
import subprocess

from .models import Bar


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def validate_bar(at, values, duration, tick):
    if len(values) != 5 or not all(x.is_finite() for x in values):
        raise ValueError('NONFINITE_OR_SCHEMA')
    o, h, l, c, v = values
    problem = ''
    if not (0 < l <= min(o, c) <= max(o, c) <= h) or v < 0:
        problem = 'OHLC_GEOMETRY_OR_VOLUME'
    elif any(p % tick for p in (o, h, l, c)):
        problem = 'OFF_HISTORICAL_GRID'
    elif v == 0:
        problem = 'ZERO_VOLUME'
    return Bar(at, duration, o, h, l, c, v, problem)


def load_market_data(root: Path, config, rules):
    if git(root, 'rev-parse', 'HEAD') != config['source_ref']:
        raise ValueError('SOURCE_REF')
    if git(root, 'status', '--porcelain=v1', '--untracked-files=all'):
        raise ValueError('SOURCE_NOT_CLEAN')
    duration = timedelta(minutes=config['timeframe_minutes'])
    data, receipts = {}, {}
    for symbol in config['instruments']:
        spec = config['inputs'][symbol]
        if git(root, 'ls-files', '--stage', '--', spec['path']).split()[1] != spec['blob']:
            raise ValueError('SOURCE_BLOB')
        path = root / spec['path']
        before = path.stat()
        with path.open('rb', buffering=0) as stream:
            raw = stream.read(spec['prefix_bytes'])
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns, after.st_ino):
            raise ValueError('SOURCE_CHANGED')
        if len(raw) != spec['prefix_bytes'] or hashlib.sha256(raw).hexdigest() != spec['prefix_sha256'] or not raw.endswith(b'\n'):
            raise ValueError('DEVELOPMENT_PREFIX_MISMATCH')
        lines = raw.decode('utf-8-sig').splitlines()
        if lines[0] != 'Ticker;Datetime;Open;High;Low;Close;Volume' or len(lines)-1 != spec['rows_2023']:
            raise ValueError('HEADER_OR_ROW_BUDGET')
        rows, previous, problems = {}, None, {}
        for line in lines[1:]:
            ticker, stamp, *numbers = line.split(';')
            at = datetime.fromisoformat(stamp)
            if at.tzinfo or ticker != symbol or not config['start'] <= stamp[:10] < config['end_exclusive']:
                raise ValueError('SOURCE_TIMESTAMP_OR_TICKER')
            if at.second or at.microsecond or (at.hour*60+at.minute) % config['timeframe_minutes']:
                raise ValueError('UNALIGNED_TIMESTAMP')
            at = at.replace(tzinfo=rules.zone)
            if previous is not None and at <= previous:
                raise ValueError('DUPLICATE_OR_UNSORTED_TIMESTAMP')
            previous = at
            try:
                values = tuple(Decimal(x) for x in numbers)
            except InvalidOperation as exc:
                raise ValueError('INVALID_NUMBER') from exc
            bar = validate_bar(at, values, duration, rules.tick(symbol, at))
            rows[at] = bar
            if bar.problem:
                problems[bar.problem] = problems.get(bar.problem, 0) + 1
        if min(rows).replace(tzinfo=None).isoformat(sep=' ') != spec['first']:
            raise ValueError('FIRST_OBSERVATION')
        data[symbol] = rows
        receipts[symbol] = dict(spec, bytes_read=len(raw), bytes_2024_plus_read=0,
                                bytes_2025_plus_read=0, last=str(max(rows)),
                                invalid_rows=problems, reader='unbuffered exact byte prefix',
                                label=config['bar_label'], timezone=config['timezone'])
    return data, receipts
