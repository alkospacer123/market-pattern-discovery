"""V20-04.2 representative parity against published, unselected RAW_SIGNAL rows.

Uses SHA-pinned external USD quotes only through each 2024 signal; never 2025.
No replay, broker or archived source mutation. Skip explicitly if external inputs
or the already declared numpy/pandas dependencies are unavailable.
"""
from datetime import datetime, timedelta
import csv
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import pandas as pd
    from V20_TradingSystem_M15.v20_runtime import frozen_adapter
except ImportError:
    pd = None

from V20_TradingSystem_M15.v20_runtime.market_reference_descriptive import SOURCE_SHA256

ROOT=Path(__file__).resolve().parents[2]
QUOTES=Path('/workspace/market-pattern-data/forever/USDRUBF/USDRUBF_M15.csv')
RAW=ROOT/'V20-03/comparison/QUOTE_PATH_DIAGNOSTICS.csv'
RAW_SHA='1f936dca02b9c99ed1df6ca30ef52c4c33128c9d06743175b6f5d6f59dee9c0f'


@unittest.skipIf(pd is None,'Declared offline pandas/numpy dependencies unavailable')
class FrozenAdapterParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QUOTES.exists():
            raise unittest.SkipTest('External SHA-pinned USD quotes unavailable')
        if hashlib.sha256(QUOTES.read_bytes()).hexdigest()!=SOURCE_SHA256['USDRUBF']:
            raise AssertionError('FROZEN_USD_SOURCE_CHANGED')
        if hashlib.sha256(RAW.read_bytes()).hexdigest()!=RAW_SHA:
            raise AssertionError('PUBLISHED_RAW_SOURCE_CHANGED')
        cls.cases={}
        with RAW.open() as stream:
            for row in csv.DictReader(stream):
                if (row['record_type']=='RAW_SIGNAL' and row['instrument']=='USDRUBF'
                        and row['signal_bar_dt'].startswith('2024-')):
                    key=(row['strategy'],int(row['side']))
                    cls.cases.setdefault(key,row)
        if len(cls.cases)!=6:
            raise AssertionError('THREE_STRATEGIES_BOTH_SIDES_NOT_COVERED')

    @staticmethod
    def prefix(row):
        cutoff=datetime.fromisoformat(row['signal_bar_dt'])
        records=[]
        with QUOTES.open() as stream:
            for source in csv.DictReader(stream,delimiter=';'):
                stamp=datetime.fromisoformat(source['Datetime'])
                if stamp>cutoff:
                    break  # no future prices/volumes are parsed
                records.append(dict(Datetime=stamp,**{k:float(source[k]) for k in
                                                     ('Open','High','Low','Close','Volume')}))
        return pd.DataFrame(records)

    def check_signal(self,strategy,side):
        row=self.cases[(strategy,side)]
        source=self.prefix(row)
        before=source.copy(deep=True)
        at=datetime.fromisoformat(row['signal_bar_dt'])
        signal=frozen_adapter.completed_signal('USDRUBF',strategy,source,observed_at=at+timedelta(minutes=15))
        self.assertIsNotNone(signal)
        self.assertEqual((signal.strategy,signal.symbol,signal.side,signal.signal_bar_open),
                         (strategy,'USDRUBF',side,at))
        expected=float(row['ATR14_price_pct'])*source.Close.iloc[-1]/100
        self.assertAlmostEqual(float(signal.atr14),expected,delta=max(1e-11,abs(expected)*1e-9))
        pd.testing.assert_frame_equal(source,before)

    def test_shallow_long(self):
        self.check_signal('SHALLOW_PULLBACK',1)

    def test_shallow_short(self):
        self.check_signal('SHALLOW_PULLBACK',-1)

    def test_obv_long(self):
        self.check_signal('OBV_PRESSURE',1)

    def test_obv_short(self):
        self.check_signal('OBV_PRESSURE',-1)

    def test_inside_long(self):
        self.check_signal('INSIDE_DAY_RELEASE',1)

    def test_inside_short(self):
        self.check_signal('INSIDE_DAY_RELEASE',-1)

    def test_next_open_and_duplicate_boundaries(self):
        row=self.cases[('SHALLOW_PULLBACK',1)]
        source=self.prefix(row)
        at=datetime.fromisoformat(row['signal_bar_dt'])
        with self.assertRaisesRegex(ValueError,'ONLY_COMPLETED_SIGNAL_AT_IMMEDIATE_NEXT_OPEN'):
            frozen_adapter.completed_signal('USDRUBF','SHALLOW_PULLBACK',source,observed_at=at+timedelta(minutes=14))
        duplicate=pd.concat([source,source.tail(1)],ignore_index=True)
        with self.assertRaisesRegex(ValueError,'M15_TIMESTAMP_ORDER_OR_TIMEZONE'):
            frozen_adapter.completed_signal('USDRUBF','SHALLOW_PULLBACK',duplicate,observed_at=at+timedelta(minutes=15))

    def test_locked_csv_adapter_scratch_is_outside_repository(self):
        row=self.cases[('INSIDE_DAY_RELEASE',1)]
        source=self.prefix(row)
        created=[]
        original=tempfile.TemporaryDirectory
        def capture(*args,**kwargs):
            manager=original(*args,**kwargs)
            created.append(Path(manager.name).resolve())
            return manager
        with patch.object(frozen_adapter.tempfile,'TemporaryDirectory',capture):
            frozen_adapter._frozen_immutable_features(source)
        self.assertGreaterEqual(len(created),2)
        repository=ROOT.parent
        self.assertTrue(all(p!=repository and repository not in p.parents for p in created))
        self.assertTrue(all(not p.exists() for p in created))


if __name__=='__main__':
    unittest.main()
