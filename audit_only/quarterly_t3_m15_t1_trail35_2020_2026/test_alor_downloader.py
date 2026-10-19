"""Offline SYNTHETIC tests. They never contact ALOR or certify real quotes."""
import copy
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.parse
import urllib.error
import ssl
import socket

import download_quarterly_m15_alor as d

T = 1788246000  # 2026-09-01 10:00 Europe/Moscow, on a real 15-minute boundary.


def bar(t=T, **changes):
    result = dict(time=t, open=100, high=102, low=99, close=101, volume=7)
    result.update(changes)
    return result


def history(rows=(), **extra):
    result = dict(history=list(rows), next=None, prev=None)
    result.update(extra)
    return json.dumps(result).encode()


def metadata(symbol='Si-9.26', **changes):
    row = dict(symbol=symbol, shortname='SiU6', exchange='MOEX', market='FORTS',
               primary_board='RFUD', type='Фьючерсный контракт ' + symbol, cfiCode='FFXCSX',
               cancellation='2026-09-17T00:00:00Z')
    row.update(changes)
    return row


def contract():
    return d.metadata_contract(metadata(), 'synthetic-metadata-receipt')


class NoNetwork(unittest.TestCase):
    def setUp(self):
        self.block = patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('LIVE_NETWORK_FORBIDDEN_IN_TEST'))
        self.block.start()
        self.addCleanup(self.block.stop)
        self.sleep = patch.object(d.time, 'sleep')
        self.sleep.start()
        self.addCleanup(self.sleep.stop)
        self.stdout = patch('sys.stdout', new_callable=io.StringIO)
        self.stdout.start()
        self.addCleanup(self.stdout.stop)


class ParserTests(NoNetwork):
    def test_valid_ohlcv_and_utc_moscow(self):
        rows, info = d.parse_history(history([bar()]), T, T + 900)
        self.assertEqual(rows[0]['close'], '101')
        self.assertEqual(datetime.fromtimestamp(T, d.MSK).hour, 10)
        self.assertEqual(datetime.fromtimestamp(T, timezone.utc).hour, 7)
        self.assertIsNone(info['next'])

    def test_reject_malformed_nonfinite_wrong_schema(self):
        for body in (b'<html>denied</html>', b'null', b'[]', b'{"history":null}',
                     b'{"history":[{"time":NaN}]}'):
            with self.subTest(body=body), self.assertRaises(d.DataError):
                d.parse_history(body, T, T + 900)

    def test_bad_ohlcv_time_volume(self):
        for change in ({'low': 101}, {'high': 99}, {'volume': -1}, {'open': 0},
                       {'time': T + 1}, {'time': T + 900}, {'time': True},
                       {'close': '101'}, {'close': float('inf')}):
            b = bar()
            b.update(change)
            with self.subTest(change=change), self.assertRaises(d.DataError):
                d.parse_history(history([b]), T, T + 900)

    def test_identical_duplicates_deduplicated_conflicts_rejected(self):
        rows, stats = d.parse_history(history([bar(), bar()]), T, T + 900)
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats['identical_duplicates'], 1)
        other = bar()
        other['close'] = 100
        with self.assertRaisesRegex(d.DataError, 'CONFLICTING_DUPLICATE'):
            d.parse_history(history([bar(), other]), T, T + 900)

    def test_order_is_not_silently_repaired(self):
        with self.assertRaisesRegex(d.DataError, 'NONMONOTONIC'):
            d.parse_history(history([bar(T + 900), bar(T)]), T, T + 1800)

    def test_decimal_values_are_not_binary_rounded(self):
        body = b'{"history":[{"time":1788246000,"open":100.123456789012345678,"high":102,"low":99,"close":101,"volume":7}]}'
        rows, _ = d.parse_history(body, T, T + 900)
        self.assertEqual(rows[0]['open'], '100.123456789012345678')

    def test_fragment_conflict_is_fatal(self):
        a, _ = d.parse_history(history([bar()]), T, T + 900)
        b = copy.deepcopy(a)
        b[0]['close'] = '100'
        with self.assertRaisesRegex(d.DataError, 'CONFLICTING_FRAGMENT'):
            d.merge_bars([a, b])

    def test_monthly_br_ng_and_no_perpetual_substitution(self):
        for symbol in ('BR-2.20', 'NG-11.24'):
            self.assertIsNotNone(d.metadata_contract(metadata(symbol), 'test'))
        for symbol in ('Si', 'SiH0', 'USDRUBF', 'GLDRUBF', 'MXI-9.26', 'GC-9.26'):
            self.assertIsNone(d.metadata_contract(metadata(symbol), 'test'))

    def test_foreign_or_spot_or_option_or_board_rejected(self):
        for changes in ({'exchange': 'SPBX'}, {'market': 'FOND'}, {'primary_board': 'TQBR'},
                        {'type': 'Опцион'}, {'cfiCode': 'OXXXXX'}, {'cancellation': None},
                        {'underlyingSymbol': 'USDRUBF'}):
            with self.subTest(changes=changes), self.assertRaises(d.DataError):
                d.metadata_contract(metadata(**changes), 'test')

    def test_missing_dates_not_invented_from_contract_name(self):
        c = contract()
        self.assertIsNone(c['first_trade_utc'])
        self.assertIsNone(c['expiry_utc'])
        self.assertIsNone(c['last_trade_utc'])
        self.assertEqual(c['alor_symbol'], 'Si-9.26')

    def test_nearby_sampling_does_not_select_2026_for_2020(self):
        self.assertIsNone(d.choose_contract({'x': contract()}, 'Si', d.epoch('2020-01-09'), d.epoch('2020-01-11')))


class TransportTests(NoNetwork):
    def test_public_get_sends_no_authorization_and_only_production(self):
        seen = []
        class Response:
            status = 200
            headers = {'Content-Type': 'application/json'}
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, limit):
                return history()
        class Opener:
            def open(self, request, **kwargs):
                seen.append(request)
                return Response()
        with patch('urllib.request.build_opener', return_value=Opener()):
            code, _, _ = d.network_get(d.url_for('/md/v2/history', d.history_params(contract(), T, T + 900)))
        self.assertEqual(code, 200)
        self.assertEqual(seen[0].get_method(), 'GET')
        self.assertFalse(any(k.lower() in ('authorization', 'cookie') for k in seen[0].headers))
        with self.assertRaisesRegex(d.DataError, 'PRODUCTION_ONLY'):
            d.network_get('https://apidev.alor.ru/md/v2/history')

    def test_dns_tls_and_proxy_errors_are_distinct(self):
        for reason, expected in [(socket.gaierror('synthetic DNS'), 'DNS_ERROR'),
                                 (ssl.SSLError('synthetic TLS'), 'TLS_ERROR'),
                                 ('Tunnel connection failed: 403 Forbidden', 'PROXY_CONNECT_403_BEFORE_PROVIDER')]:
            class Opener:
                def open(self, *args, **kwargs):
                    raise urllib.error.URLError(reason)
            with self.subTest(expected=expected), patch('urllib.request.build_opener', return_value=Opener()):
                with self.assertRaisesRegex(d.DataError, expected):
                    d.network_get(d.url_for('/md/v2/history', {}))


class PaginationTests(NoNetwork):
    def test_request_boundaries_and_no_countback(self):
        q = d.history_params(contract(), T, T + 900)
        self.assertEqual(q['from'], T)
        self.assertEqual(q['to'], T + 899)
        self.assertEqual(q['tf'], 900)
        self.assertEqual(q['untraded'], 'true')
        self.assertEqual(q['splitAdjust'], 'false')
        self.assertNotIn('countBack', q)
        for path, params in (('/commandapi/orders', {}), ('/md/v2/history', {'token': 'forbidden'}),
                             ('/md/v2/history', {'countBack': 5})):
            with self.assertRaises(d.DataError):
                d.url_for(path, params)

    def test_fixed_chunks_cover_range_exactly(self):
        pieces = list(d.windows(T, T + 20 * 86400 + 900, 7))
        self.assertEqual(pieces[0][0], T)
        self.assertEqual(pieces[-1][1], T + 20 * 86400 + 900)
        self.assertTrue(all(a[1] == b[0] for a, b in zip(pieces, pieces[1:])))
        self.assertTrue(all(b - a <= 7 * 86400 for a, b in pieces))

    def test_history_follows_both_neighbor_subranges(self):
        class Fake:
            def __init__(self):
                self.calls = []

            def get(self, path, params, **kwargs):
                a, b = params['from'], params['to'] + 1
                self.calls.append((a, b))
                if (a, b) == (T, T + 2700):
                    return history([bar(T + 900)], prev=T, next=T + 1800), 'middle'
                return history([bar(a)]), str(a)

        fake = Fake()
        rows, _, _ = d.history_range(fake, contract(), T, T + 2700)
        self.assertEqual([r['time'] for r in rows], [T, T + 900, T + 1800])
        self.assertEqual(set(fake.calls), {(T, T + 2700), (T, T + 900), (T + 1800, T + 2700)})

    def test_empty_history_does_not_expand_to_neighbor_outside_request(self):
        class Fake:
            def get(self, *args, **kwargs):
                return history([], next=T + 86400), 'empty'

        rows, receipts, _ = d.history_range(Fake(), contract(), T, T + 900)
        self.assertEqual(rows, [])
        self.assertEqual(receipts, ['empty'])

    def test_stuck_cursor_rejected(self):
        class Fake:
            def get(self, *args, **kwargs):
                return history([], next=T), 'stuck'

        with self.assertRaisesRegex(d.DataError, 'NO_PROGRESS'):
            d.history_range(Fake(), contract(), T, T + 900)

    def test_security_page_repetition_rejected(self):
        class Fake:
            def get(self, *args, **kwargs):
                return json.dumps([metadata()] * 100).encode(), 'test'

        with self.assertRaisesRegex(d.DataError, 'PAGINATION_NO_PROGRESS'):
            d.search(Fake(), 'Si')


class StorageTests(NoNetwork):
    def test_resume_success_uses_exact_cached_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def transport(url):
                calls.append(url)
                return 200, history([bar()]), {}

            c = d.Client(tmp, transport=transport)
            q = d.history_params(contract(), T, T + 900)
            first = c.get('/md/v2/history', q)
            c2 = d.Client(tmp, transport=lambda u: self.fail('SUCCESS_REDOWNLOADED'))
            self.assertEqual(c2.get('/md/v2/history', q), first)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(d.verify_store(Path(tmp))), 1)
            raw = next(Path(tmp).glob('requests/*/attempt-*/response.json'))
            raw.write_bytes(b'corrupt')
            with self.assertRaisesRegex(d.DataError, 'SHA256_MISMATCH'):
                c2.get('/md/v2/history', q)

    def test_http_errors_are_distinct_and_preserved_without_retry(self):
        for code in (400, 401, 403, 404, 429, 500):
            with self.subTest(code=code), tempfile.TemporaryDirectory() as tmp:
                c = d.Client(tmp, transport=lambda u: (code, b'{"error":"synthetic"}', {}))
                q = d.history_params(contract(), T, T + 900)
                with self.assertRaisesRegex(d.DataError, 'HTTP_OR_NETWORK_BLOCK'):
                    c.get('/md/v2/history', q)
                r = load_receipt(tmp)
                self.assertEqual(r['provider_http_status'], code)
                self.assertIsNone(r['proxy_connect_status'])
                with self.assertRaisesRegex(d.DataError, 'CACHED_FAILURE'):
                    c.get('/md/v2/history', q)
                self.assertEqual(c.new_requests, 1)

    def test_proxy_failure_is_not_provider_403_and_explicit_retry_is_new_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            def blocked(url):
                raise d.DataError('PROXY_CONNECT_403_BEFORE_PROVIDER: synthetic')

            q = d.history_params(contract(), T, T + 900)
            with self.assertRaises(d.DataError):
                d.Client(tmp, transport=blocked).get('/md/v2/history', q)
            r = load_receipt(tmp)
            self.assertEqual(r['proxy_connect_status'], 403)
            self.assertIsNone(r['provider_http_status'])
            self.assertIsNone(r['raw_sha256'])
            d.Client(tmp, retry_failed=True, transport=lambda u: (200, history(), {})).get('/md/v2/history', q)
            self.assertEqual(len(list(Path(tmp).glob('requests/*/attempt-*'))), 2)

    def test_interrupted_attempt_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = d.Client(tmp, transport=lambda u: self.fail('INTERRUPTED_RETRIED'))
            q = d.history_params(contract(), T, T + 900)
            request = dict(method='GET', url=d.url_for('/md/v2/history', q), replica=False, version=d.VERSION)
            path = Path(tmp) / 'requests' / d.sha(d.encoded(request)) / 'attempt-0001'
            path.mkdir(parents=True)
            (path / 'request.json').write_bytes(d.encoded(request))
            with self.assertRaisesRegex(d.DataError, 'INTERRUPTED_REQUEST'):
                c.get('/md/v2/history', q)

    def test_download_without_successful_probe_fails_before_requests(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.snapshot(root, 'probe_result', dict(status='BLOCKED_OR_PARTIAL'))
            with self.assertRaisesRegex(d.DataError, 'SUCCESSFUL_PROBE_REQUIRED'):
                d.download(d.Client(root, transport=lambda u: self.fail('DOWNLOAD_BEFORE_PROBE')), {}, {}, 7)

    def test_immutable_raw_and_versioned_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.immutable(root / 'raw.json', b'one')
            d.immutable(root / 'raw.json', b'one')
            with self.assertRaisesRegex(d.DataError, 'OVERWRITE_REFUSED'):
                d.immutable(root / 'raw.json', b'two')
            d.snapshot(root, 'derived', {'x': 1})
            d.snapshot(root, 'derived', {'x': 2})
            self.assertEqual(len(list((root / 'reports').glob('derived-*.json'))), 2)

    def test_pilot_repeat_price_change_is_fatal(self):
        class Fake:
            def get(self, path, params, replica=False):
                r = bar()
                if replica:
                    r['close'] = 100
                return history([r, bar(T + 900)]), 'repeat' if replica else 'first'

        with self.assertRaisesRegex(d.DataError, 'OHLCV_CHANGED'):
            d.sample(Fake(), {'Si-9.26': contract()}, 'Si', '2026-09-01', '2026-09-03', 'Si_2026')

    def test_request_budget_stops_before_next_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = d.Client(tmp, budget=0, transport=lambda u: self.fail('OVER_BUDGET'))
            with self.assertRaisesRegex(d.DataError, 'BUDGET_EXHAUSTED'):
                c.get('/md/v2/history', d.history_params(contract(), T, T + 900))

    def test_single_bar_does_not_pass_m15_pilot(self):
        class Fake:
            def get(self, *args, **kwargs):
                return history([bar()]), 'one'

        result = d.sample(Fake(), {'Si-9.26': contract()}, 'Si', '2026-09-01', '2026-09-03', 'Si_2026')
        self.assertEqual(result['status'], 'INSUFFICIENT_M15_ADJACENCY')

    def test_changed_contract_identity_not_overwritten(self):
        original = contract()
        inventory = {original['alor_symbol']: original}
        modified = copy.deepcopy(original)
        modified['provider_completion_epoch'] += 86400
        with self.assertRaisesRegex(d.DataError, 'METADATA_CHANGED'):
            d.accept_contract(inventory, modified)
        self.assertEqual(inventory[original['alor_symbol']], original)


class IntegrationTests(NoNetwork):
    def test_complete_synthetic_probe_resume_gate_and_manifest(self):
        """Nine fake samples; no API or economics; exercise actual cache and gate."""
        catalog = []
        for root in ('Si', 'GOLD', 'CNY'):
            for month, year in ((3, 2020), (6, 2024), (9, 2026)):
                symbol = f'{root}-{month}.{year % 100:02d}'
                catalog.append(metadata(symbol, cancellation=f'{year}-{month:02d}-17T00:00:00Z'))
        calls = []

        def transport(url):
            calls.append(url)
            u = urllib.parse.urlsplit(url)
            q = urllib.parse.parse_qs(u.query)
            if u.path.endswith('/Securities'):
                query = q['query'][0]
                return 200, json.dumps([r for r in catalog if r['symbol'].startswith(query)]).encode(), {}
            a, b = int(q['from'][0]), int(q['to'][0]) + 1
            self.assertGreaterEqual(b - a, 2 * 900)
            return 200, history([bar(a), bar(a + 900)]), {}

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = dict(start_epoch=d.epoch('2020-01-01'), end_epoch=d.epoch('2026-10-20'))
            client = d.Client(root, transport=transport)
            inventory = {}
            result = d.probe(client, config, inventory)
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(len(result['samples']), 9)
            self.assertTrue(all(s['rows'] == 2 for s in result['samples']))
            count = len(calls)
            # Resuming the same protocol reuses BOTH stability captures, not new network calls.
            d.probe(d.Client(root, transport=lambda u: self.fail('REDOWNLOADED')), config, inventory)
            self.assertEqual(len(calls), count)
            packet = d.manifest(root, config, inventory, 'SYNTHETIC_TEST_ONLY')
            self.assertEqual(len(packet['coverage_by_market_year']), 42)
            self.assertEqual(packet['strategy_replay'], 'NOT_RUN')
            self.assertFalse(packet['continuous_series_created'])
            self.assertTrue(all(r['raw_sha256'] for r in packet['requests']))
            # Exercise real gate and download orchestration while bounding the
            # synthetic transport to one small chunk per fixture contract.
            with patch.object(d, 'discover'), patch.object(d, 'search', return_value=[]), \
                 patch.object(d, 'windows', return_value=[(T, T + 1800)]):
                self.assertEqual(d.download(client, config, inventory, 7),
                                 'DOWNLOAD_FINISHED_COMPLETENESS_UNVERIFIED')
            d.verify_store(root)

    def test_cli_blocked_probe_preserves_evidence_and_invalidates_old_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d.snapshot(root, 'probe_result', dict(status='PASS'))
            def blocked(url):
                raise d.DataError('PROXY_CONNECT_403_BEFORE_PROVIDER: SYNTHETIC')
            with patch.object(d, 'network_get', side_effect=blocked), \
                 patch('sys.stdout', new_callable=io.StringIO), patch('sys.stderr', new_callable=io.StringIO):
                code = d.main(['--mode', 'probe', '--output-dir', tmp])
            self.assertEqual(code, 2)
            self.assertNotEqual(d.load(root / 'probe_result.json')['status'], 'PASS')
            self.assertEqual(d.load(root / 'manifest.json')['status'], 'BLOCKED_OR_INTERRUPTED')
            self.assertEqual(load_receipt(tmp)['proxy_connect_status'], 403)
            self.assertFalse((root / '.downloader.lock').exists())


def load_receipt(tmp):
    return json.loads(next(Path(tmp).glob('requests/*/attempt-*/receipt.json')).read_bytes())


if __name__ == '__main__':
    unittest.main(verbosity=2)
