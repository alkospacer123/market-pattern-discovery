"""V20-04.2 diagnostics-only tests. Synthetic sessions; NO FINAM, no live mode."""
from __future__ import annotations

import json
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta

from V20_TradingSystem_M15.v20_runtime.market_suitability import (
    M15Bar, CompletedSession, evaluate_market_card, clv_pressure_prior12,
    _pressure_stats, _compression_stats,
)

START = date(2026, 9, 1)


def make_sessions(n=20, *, first_volume=10, last_volume=10, base_volume=10):
    data = []
    for i in range(n):
        d = START + timedelta(days=i)
        start = datetime.combine(d, datetime.min.time()).replace(hour=10)
        expected = tuple(start + timedelta(minutes=15 * k) for k in range(4))
        volume = first_volume if i == 0 else (last_volume if i == n - 1 else base_volume)
        bars = tuple(
            M15Bar(t, 100 + i + k, 101 + i + k, 99 + i + k,
                   100.5 + i + k, volume) for k, t in enumerate(expected)
        )
        data.append(CompletedSession(d, expected, bars, expected[-1] + timedelta(minutes=15)))
    return tuple(data)


def inspect(sessions, *, symbol="CNYRUBF", previous=None, as_of=None, execution=None):
    return evaluate_market_card(
        symbol, sessions,
        as_of=as_of or sessions[-1].closed_at,
        previous=previous, execution_readonly=execution,
    )


class SuitabilityCardTests(unittest.TestCase):
    def test_pressure_uses_clv_on_red_candles_and_excludes_current_volume(self):
        start = datetime(2026, 9, 1, 10)
        bars = [M15Bar(start+timedelta(minutes=15*i), 100+i+.95,
                       101+i, 100+i, 100+i+.9, 10) for i in range(13)]
        # Every candle is red, yet each close is near its high: CLV = +0.8.
        self.assertAlmostEqual(clv_pressure_prior12(bars), .8)
        bars[-1] = replace(bars[-1], close=bars[-1].low, volume=1e9)
        self.assertAlmostEqual(clv_pressure_prior12(bars), .8)
        self.assertAlmostEqual(_pressure_stats(bars)['pressure_direction_alignment'], .8)
        falling = [replace(b, open=200-i+.95, high=201-i, low=200-i, close=200-i+.9)
                   for i,b in enumerate(bars)]
        self.assertAlmostEqual(_pressure_stats(falling)['pressure_direction_alignment'], -.8)

    def test_pressure_zero_range_zero_volume_and_short_history(self):
        start = datetime(2026, 9, 1, 10)
        bars = [M15Bar(start+timedelta(minutes=15*i), 100,100,100,100,10) for i in range(13)]
        self.assertEqual(clv_pressure_prior12(bars), 0)
        self.assertIsNone(clv_pressure_prior12(bars[:12]))
        self.assertIsNone(clv_pressure_prior12([replace(b, volume=0) for b in bars]))
        self.assertIsNone(_pressure_stats(bars)['pressure_direction_alignment'])

    def test_inside_strict_finished_pairs_and_completed_release(self):
        def day(i, high, low):
            start = datetime(2026,9,1,10)+timedelta(days=i)
            times = tuple(start+timedelta(minutes=15*k) for k in range(32))
            bars = tuple(M15Bar(t,100,high,low,100,10) for t in times)
            return CompletedSession(start.date(),times,bars,times[-1]+timedelta(minutes=15))
        older, inner = day(0,110,90), day(1,108,92)
        prior = _compression_stats([older,inner])
        self.assertIs(prior['latest_pair_strict_inside'], True)
        self.assertAlmostEqual(prior['latest_range_ratio'], .8)
        self.assertEqual(prior['completed_release_breakouts'],0)
        equal = day(1,110,92)
        self.assertIs(_compression_stats([older,equal])['latest_pair_strict_inside'],False)
        release = day(2,112,90)
        bs = list(release.bars)
        bs[0] = replace(bs[0],close=109)
        bs[1] = replace(bs[1],close=110)
        release = replace(release,bars=tuple(bs))
        stats = _compression_stats([older,inner,release])
        self.assertEqual(stats['completed_release_breakouts'],1)
        self.assertEqual(stats['inside_release_continuation_rate'],1)
        self.assertEqual(stats['inside_release_return_rate'],0)
        bs[1] = replace(bs[1],close=107)
        stats = _compression_stats([older,inner,replace(release,bars=tuple(bs))])
        self.assertEqual(stats['inside_release_continuation_rate'],0)
        self.assertEqual(stats['inside_release_return_rate'],1)
        # Incomplete next observation must never be counted as confirmation.
        stats = _compression_stats([older,inner,replace(release,bars=(bs[0],))])
        self.assertEqual(stats['completed_release_breakouts'],0)
        self.assertEqual(stats['unconfirmed_release_breakouts'],1)

    def test_entire_missing_session_cannot_be_hidden_by_twenty_observations(self):
        data = make_sessions(21)
        output = evaluate_market_card('BR', data[:10]+data[11:],as_of=data[-1].closed_at,
                                     expected_session_days=[s.day for s in data])
        self.assertEqual(output['metrics']['data_quality']['missing_sessions'],1)
        self.assertTrue(all(s['suitability']=='НЕДОСТАТОЧНО ДАННЫХ' for s in output['strategies'].values()))

    def test_five_groups_displayed_for_every_strategy(self):
        output = inspect(make_sessions())
        fields = {'atr14_pct_close','directional_efficiency','continuation_rate',
                  'pressure_direction_alignment','range_compression_ratio'}
        for strategy in output['strategies'].values():
            self.assertTrue(fields <= strategy['diagnostics'].keys())

    def test_rolling_pressure_regime_transitions_in_both_directions(self):
        for first_aligned in (True,False):
            data = list(make_sessions(40))
            for i,s in enumerate(data):
                aligned = first_aligned if i<20 else not first_aligned
                bars = []
                for k,b in enumerate(s.bars):
                    low = 100+2*i+k*.1
                    bars.append(replace(b,open=low+.5,high=low+1,low=low,
                                        close=low+(.9 if aligned else .1)))
                data[i] = replace(s,bars=tuple(bars))
            prior = inspect(data[:20])
            after = inspect(data,previous=prior)
            metric = 'pressure_direction_alignment'
            a = prior['metrics']['volume_pressure'][metric]
            b = after['metrics']['volume_pressure'][metric]
            self.assertLess(a*b,0)
            movement = after['metric_changes']['volume_pressure.'+metric]['movement']
            self.assertEqual(movement,'decrease' if first_aligned else 'increase')
            self.assertTrue(all(s['suitability']=='НЕ ОЦЕНЕНО' for s in after['strategies'].values()))

    def test_three_readonly_robot_cards_never_filter(self):
        output = inspect(make_sessions())
        self.assertEqual(output["session_window"], 20)
        self.assertEqual(set(output["strategies"]),
                         {"SHALLOW_PULLBACK", "OBV_PRESSURE", "INSIDE_DAY_RELEASE"})
        self.assertTrue(all(x["suitability"] == "НЕ ОЦЕНЕНО"
                            for x in output["strategies"].values()))
        self.assertIs(output["affects_signals_or_risk"], False)
        self.assertTrue(output["unrestricted_diagnostic_universe"])
        self.assertEqual(output["trading_instrument_authority"], "OPERATOR_ONLY")
        self.assertIs(output["live_authorized"], False)
        self.assertGreater(output["metrics"]["volatility"]["atr14_wilder_price"], 0)
        self.assertAlmostEqual(output["strategies"]["OBV_PRESSURE"]["diagnostics"]["prior12_pressure_abs"],
                               abs(output["strategies"]["OBV_PRESSURE"]["diagnostics"]["prior12_pressure"]))
        json.dumps(output, ensure_ascii=False, allow_nan=False)

    def test_no_invented_spread_cost_or_margin(self):
        data = inspect(make_sessions())["metrics"]["liquidity"]
        self.assertIsNone(data["spread_price"])
        self.assertIsNone(data["roundtrip_cost_rub"])
        self.assertIsNone(data["roundtrip_cost_to_2atr_stop"])
        self.assertIsNone(data["initial_margin_rub"])

    def test_only_optional_readonly_execution_cost(self):
        data = inspect(make_sessions(), execution={
            "price_step": 0.001, "tick_value_rub": 2,
            "roundtrip_cost_rub": 3, "spread_price": 0.002,
        })["metrics"]["liquidity"]
        self.assertGreater(data["roundtrip_cost_to_2atr_stop"], 0)
        with self.assertRaisesRegex(ValueError, "UNKNOWN_READONLY_EXECUTION_FIELD"):
            inspect(make_sessions(), execution={"account_token": "forbidden"})

    def test_19_sessions_means_insufficient_data(self):
        out = inspect(make_sessions(19))
        self.assertEqual(out["metrics"]["data_quality"]["observed_sessions"], 19)
        self.assertIsNone(out["metrics"]["volatility"]["atr14_wilder_price"])
        self.assertTrue(all(x["suitability"] == "НЕДОСТАТОЧНО ДАННЫХ"
                            for x in out["strategies"].values()))

    def test_missing_expected_m15_bar_marks_insufficient(self):
        s = list(make_sessions())
        s[-1] = replace(s[-1], bars=s[-1].bars[:-1])
        out = inspect(tuple(s))
        self.assertEqual(out["metrics"]["data_quality"]["missing_bars"], 1)
        self.assertTrue(all(x["suitability"] == "НЕДОСТАТОЧНО ДАННЫХ"
                            for x in out["strategies"].values()))

    def test_future_session_and_premature_bar_blocked(self):
        s = make_sessions()
        with self.assertRaisesRegex(ValueError, "SESSION_NOT_OBSERVABLY_COMPLETE"):
            inspect(s, as_of=s[-1].closed_at - timedelta(minutes=1))
        x = list(s)
        x[-1] = replace(x[-1], closed_at=x[-1].bars[-1].open_time)
        with self.assertRaisesRegex(ValueError, "M15_BAR_NOT_COMPLETED"):
            inspect(tuple(x))

    def test_last20_rolls_and_older_session_disappears(self):
        s = make_sessions(21, first_volume=999999, last_volume=10)
        a = inspect(s)
        b = inspect(s[1:])
        self.assertEqual(a["metrics"], b["metrics"])
        self.assertEqual(a["last_completed_session"], b["last_completed_session"])

    def test_bidirectional_metric_changes_not_verdicts(self):
        rising = make_sessions(21, first_volume=1, last_volume=100)
        newer = inspect(rising)
        older = inspect(rising[:-1])
        with_delta = inspect(rising, previous=older)
        diff = with_delta["metric_changes"]["liquidity.observed_volume"]
        self.assertGreater(diff["delta"], 0)
        self.assertEqual(diff["movement"], "increase")
        falling = make_sessions(21, first_volume=100, last_volume=1)
        older2 = inspect(falling[:-1])
        diff2 = inspect(falling, previous=older2)["metric_changes"]["liquidity.observed_volume"]
        self.assertLess(diff2["delta"], 0)
        self.assertEqual(diff2["movement"], "decrease")
        self.assertTrue(newer["changes_are_not_suitability_verdicts"])

    def test_bad_previous_symbol_rejected(self):
        older = inspect(make_sessions())
        older["symbol"] = "USDRUBF"
        with self.assertRaisesRegex(ValueError, "PREVIOUS_CARD_SYMBOL_MISMATCH"):
            inspect(make_sessions(), previous=older)

    def test_previous_proxy_schema_cannot_produce_metric_deltas(self):
        older = inspect(make_sessions())
        older.pop('metric_schema')
        with self.assertRaisesRegex(ValueError,'PREVIOUS_CARD_METRIC_SCHEMA_MISMATCH'):
            inspect(make_sessions(21),previous=older)

    def test_future_or_equal_previous_comparison_rejected(self):
        card = inspect(make_sessions())
        with self.assertRaisesRegex(ValueError, "PREVIOUS_CARD_NOT_CAUSALLY_EARLIER"):
            inspect(make_sessions(), previous=card)
        future = dict(card)
        future["as_of_msk"] = (make_sessions()[-1].closed_at
                               + timedelta(days=1)).isoformat()
        with self.assertRaisesRegex(ValueError, "PREVIOUS_CARD_NOT_CAUSALLY_EARLIER"):
            inspect(make_sessions(), previous=future)

    def test_other_futures_have_cards_but_no_trading_authorization(self):
        sessions = make_sessions()
        for symbol in ("BR", "SILV", "CNYRUBF", "IMOEXF"):
            with self.subTest(symbol=symbol):
                output = inspect(sessions, symbol=symbol)
                self.assertEqual(output["symbol"], symbol)
                self.assertTrue(output["unrestricted_diagnostic_universe"])
                self.assertEqual(output["trading_instrument_authority"], "OPERATOR_ONLY")
                self.assertFalse(output["affects_signals_or_risk"])
                self.assertEqual(output["strategies"]["SHALLOW_PULLBACK"]["suitability"],
                                 "НЕ ОЦЕНЕНО")

    def test_untrusted_or_malformed_market_symbol_rejected(self):
        for symbol in ("", "../robots.json", "cnyrubf", "SILV/USDT", "🇷🇺", None):
            with self.subTest(symbol=symbol):
                with self.assertRaisesRegex(ValueError, "INVALID_MARKET_ANALYSIS_SYMBOL"):
                    inspect(make_sessions(), symbol=symbol)

    def test_independent_previous_cards_must_match_symbol(self):
        previous = inspect(make_sessions(), symbol="SILV")
        later = make_sessions(21)
        with self.assertRaisesRegex(ValueError, "PREVIOUS_CARD_SYMBOL_MISMATCH"):
            inspect(later, symbol="BR", previous=previous)

    def test_unsorted_duplicate_or_wrong_session_open_rejected(self):
        s = list(make_sessions())
        s[-1] = replace(s[-1], bars=tuple(reversed(s[-1].bars)))
        with self.assertRaisesRegex(ValueError, "M15_DUPLICATE_OR_UNORDERED"):
            inspect(tuple(s))
        s = list(make_sessions())
        s[-1] = replace(s[-1], expected_opens=(s[-1].expected_opens[0],) * 4)
        with self.assertRaisesRegex(ValueError, "EXPECTED_SESSION_SCHEDULE_INVALID"):
            inspect(tuple(s))

    def test_unrealistic_ohlc_is_rejected(self):
        s = list(make_sessions())
        b = list(s[-1].bars)
        b[-1] = replace(b[-1], high=b[-1].low - 1)
        s[-1] = replace(s[-1], bars=tuple(b))
        with self.assertRaisesRegex(ValueError, "M15_OHLC_INVALID"):
            inspect(tuple(s))


if __name__ == "__main__":
    unittest.main()
