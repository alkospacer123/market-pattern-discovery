"""Two bounded public discovery requests, no trading API or candle downloader.

Reuse cached receipts. Inspect network policy before explicitly invoking this
script in a newly configured environment. A CONNECT denial stops that host;
this script never changes proxies, identities or network configuration.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.error
import urllib.request

URLS = (
    'https://www.finam.ru/quote/forts/si/export/',
    'https://iss.moex.com/iss/securities/SiH0.json',
)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def probe(url, cache):
    key = hashlib.sha256(url.encode()).hexdigest()
    meta = cache / (key + '.json')
    raw = cache / (key + '.bin')
    if meta.exists():
        r = json.loads(meta.read_text())
        if r['url'] != url:
            raise RuntimeError('CACHE_URL_MISMATCH')
        if r.get('source_sha256') and (not raw.exists() or
                hashlib.sha256(raw.read_bytes()).hexdigest() != r['source_sha256']):
            raise RuntimeError('CACHE_HASH_MISMATCH')
        return r
    row = dict(url=url, method='GET', observed_at_utc=datetime.now(timezone.utc).isoformat(),
               candle_request=False, request_period=None, provider_http_status=None,
               proxy_connect_http_status=None, source_sha256=None, received_source_bytes=0)
    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(url, timeout=30) as response:
            body = response.read(8 * 1024 * 1024 + 1)
            if len(body) > 8 * 1024 * 1024:
                raise RuntimeError('DISCOVERY_RESPONSE_TOO_LARGE')
            row.update(provider_http_status=response.status,
                       received_source_bytes=len(body),
                       source_sha256=hashlib.sha256(body).hexdigest(),
                       result='DISCOVERY_ONLY_REQUIRES_MANUAL_IDENTITY_AND_ENDPOINT_REVIEW')
            raw.write_bytes(body)
    except urllib.error.HTTPError as exc:
        # Do not persist arbitrary error bodies, headers, cookies or credentials.
        row.update(provider_http_status=exc.code, result='HTTP_ERROR_NO_CANDLE_DATA')
    except urllib.error.URLError as exc:
        error = str(exc)
        row.update(error=error, result='NETWORK_ERROR_BEFORE_PROVIDER')
        if 'Tunnel connection failed: 403' in error:
            row.update(proxy_connect_http_status=403,
                       result='BLOCKED_BY_EXECUTOR_PROXY_BEFORE_PROVIDER')
    meta.write_text(json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return row


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-cache', type=Path, required=True)
    args = parser.parse_args()
    cache = args.private_cache.resolve()
    root = Path(__file__).resolve().parents[2]
    if cache == root or root in cache.parents:
        raise RuntimeError('CACHE_MUST_BE_OUTSIDE_RESEARCH_REPOSITORY')
    cache.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        print(json.dumps(probe(url, cache), ensure_ascii=False, sort_keys=True))
