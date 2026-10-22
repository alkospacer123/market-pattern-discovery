"""Offline attribution and shared-calculation checks; no market OOS prices."""
import csv
from dataclasses import replace
from datetime import date, datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from V20_TradingSystem_M15.v20_runtime.market_outcome_research import raw_rows, spearman
from V20_TradingSystem_M15.v20_runtime.market_reference_descriptive import load_sessions, card_windows, regime
from V20_TradingSystem_M15.v20_runtime.market_suitability import evaluate_market_card
from V20_TradingSystem_M15.v20_runtime.market_suitability_cli import main
from V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability import make_sessions


class AttributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Path('work').mkdir(exist_ok=True)

    def test_raw_population_does_not_select_accepted_or_profitable_trades(self):
        rows = [{'record_type':'EXECUTED_TRADE','horizon_R':100},
                {'record_type':'RAW_SIGNAL','admission':'ACCOUNT_TWO_ENTRY_CAP','horizon_R':-3},
                {'record_type':'RAW_SIGNAL','admission':'ACCEPTED','horizon_R':2}]
        selected = raw_rows(rows)
        self.assertEqual(len(selected),2)
        self.assertEqual(sum(r['horizon_R'] for r in selected),-1)

    def test_rank_association_preserves_ties_and_direction(self):
        self.assertAlmostEqual(spearman([1,1,2,3],[2,2,4,6]),1)
        self.assertAlmostEqual(spearman([1,2,3],[3,2,1]),-1)
        self.assertIsNone(spearman([1,1,1],[1,2,3]))

    def test_descriptive_adapter_uses_exact_card_values(self):
        sessions = make_sessions()
        card = evaluate_market_card('BR',sessions,as_of=sessions[-1].closed_at)
        values = regime(sessions)
        for metric in values:
            self.assertEqual(values[metric],card['strategies']['INSIDE_DAY_RELEASE']['diagnostics'][metric])
        broken = list(sessions)
        broken[-1] = replace(broken[-1],bars=())
        self.assertTrue(all(v is None for v in regime(broken).values()))

    def test_locked_year_prices_never_parsed_and_incomplete_days_retained(self):
        # The locked row has intentionally invalid numeric data. It must never
        # reach price/volume parsing or feature calculation.
        with TemporaryDirectory(dir='work') as tmp:
            path = Path(tmp)/'USDRUBF_M15.csv'
            path.write_text('Datetime;Open;High;Low;Close;Volume\n'
                            '2024-12-30 10:00:00;100;101;99;100;1\n'
                            '2025-01-03 10:00:00;LOCKED;LOCKED;LOCKED;LOCKED;LOCKED\n'
                            '2026-01-05 10:00:00;100;101;99;100;1\n')
            with patch.dict('V20_TradingSystem_M15.v20_runtime.market_reference_descriptive.SOURCE_SHA256',
                            {'USDRUBF':hashlib.sha256(path.read_bytes()).hexdigest()}):
                sessions = load_sessions(Path(tmp),'USDRUBF')
            self.assertEqual([s.day.year for s in sessions],[2024,2026])
            self.assertEqual(len(sessions[0].bars),1)
            self.assertEqual(len(sessions[0].expected_opens),32)

    def test_window_must_not_bridge_locked_year(self):
        data = list(make_sessions())
        for i,s in enumerate(data):
            year = 2024 if i<10 else 2026
            day = date(year,9,i+1)
            def shifted(ts):
                return ts.replace(year=year)
            data[i] = replace(s,day=day,closed_at=shifted(s.closed_at),
                              expected_opens=tuple(map(shifted,s.expected_opens)),
                              bars=tuple(replace(b,open_time=shifted(b.open_time)) for b in s.bars))
        self.assertEqual(list(card_windows(data,'BR')),[])

    def test_cli_renders_all_five_groups_and_unknown_execution_fields(self):
        sessions = make_sessions()
        snapshot = {'symbol':'BR','as_of_msk':sessions[-1].closed_at.isoformat(),
                    'expected_session_days':[s.day.isoformat() for s in sessions],
                    'completed_sessions':[{'day':s.day.isoformat(),'closed_at':s.closed_at.isoformat(),
                        'expected_opens':[t.isoformat() for t in s.expected_opens],
                        'bars':[dict(open_time=b.open_time.isoformat(),open=b.open,high=b.high,
                                     low=b.low,close=b.close,volume=b.volume) for b in s.bars]}
                        for s in sessions]}
        with TemporaryDirectory(dir='work') as tmp:
            path = Path(tmp)/'snapshot.json'
            path.write_text(json.dumps(snapshot))
            stream = io.StringIO()
            with redirect_stdout(stream):
                result = main(['--input',str(path),'--details'])
            compact = io.StringIO()
            with redirect_stdout(compact):
                self.assertEqual(main(['--input',str(path)]),0)
        self.assertEqual(result,0)
        output = stream.getvalue()
        for group in ('volatility:','directionality:','breakouts:','volume_pressure:','compression:'):
            self.assertIn(group,output)
        self.assertIn('lot_size=НЕИЗВЕСТНО',output)
        self.assertIn('НЕ ОЦЕНЕНО',output)
        self.assertNotIn('pressure_direction_alignment',compact.getvalue())
        self.assertEqual(compact.getvalue().count('НЕ ОЦЕНЕНО'),3)
        self.assertIn('Нет проверенного профиля классификации.',compact.getvalue())


if __name__ == '__main__':
    unittest.main()
