"""Independent batch oracle vs streaming strategy and shared execution paths."""
from decimal import Decimal as D
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from IntradayLab.tests.test_swing_pullback import source,run,T,FIVE
from IntradayLab.core.reports import csv_write
from IntradayLab.tools.audit_swing_pullback_baseline import episodes,replay,read_csv,check_rows,batch_context

LAB=Path(__file__).resolve().parents[1]


class IndependentSwingTests(unittest.TestCase):
    def compare(self,rows):
        ss,tt,_,strategy=run(rows)
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        events,contexts=episodes('USDRUBF',raw,True)
        es,et=replay('USDRUBF',raw,events)
        with TemporaryDirectory(dir=LAB/'work') as folder:
            folder=Path(folder)
            for name,actual,expected in (('signals',ss,es),('trades',tt,et),('contexts',strategy.context_records,contexts)):
                # Oracle is a full-year batch; synthetic engine intentionally executes one day.
                expected=[e for e in expected if str(e.get('signal_start',e.get('test_start',e.get('signal_at'))))[:10]=='2023-01-03']
                csv_write(folder/(name+'.csv'),actual)
                expected=[{k:v for k,v in e.items() if k!='unknown_effective_at'} for e in expected]
                keys=sorted({k for e in expected for k in e})
                check_rows(read_csv(folder/(name+'.csv')),expected,keys,name)

    def test_independent_long_and_short_ledger_and_nine_child_lineage(self):
        for side in (1,-1):self.compare(source(side))

    def test_independent_missing_waiting_entry_exposed(self):
        for i in (12,13,15):
            raw=source();del raw[T+i*FIVE];self.compare(raw)

    def test_independent_every_missing_parent_child(self):
        for i in range(9):
            raw=source();del raw[T+i*FIVE];self.compare(raw)

    def test_oracle_future_m15_prices_do_not_change_context(self):
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in source().items()}
        window=(T,T+48*FIVE);at=T+11*FIVE
        first=batch_context('USDRUBF',raw,at,window,None)
        other={stamp:tuple(map(D,('1','9999','1','2','1'))) if stamp>=T+12*FIVE else b for stamp,b in raw.items()}
        self.assertEqual(first,batch_context('USDRUBF',other,at,window,None))

    def test_context_corruption_is_detected(self):
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in source().items()}
        _,cs=episodes('USDRUBF',raw,True);expected=cs[:12]
        with TemporaryDirectory(dir=LAB/'work') as folder:
            path=Path(folder)/'context.csv';csv_write(path,expected);actual=read_csv(path)
            actual[-1]['p3_high']='9999'
            with self.assertRaises(AssertionError):check_rows(actual,expected,tuple(expected[0]),'CORRUPT_CONTEXT')

    def test_oracle_stop_take_and_cost_corruption_detected(self):
        raw=source();at=T+14*FIVE
        from IntradayLab.tests.test_swing_pullback import bar
        raw[at]=bar(at,103.5,110,103.4,103.5)
        self.compare(raw)
        raw={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in raw.items()}
        _,trades=replay('USDRUBF',raw,episodes('USDRUBF',raw));expected=trades[:1]
        with TemporaryDirectory(dir=LAB/'work') as folder:
            path=Path(folder)/'trades.csv';csv_write(path,expected);actual=read_csv(path)
            for key in ('take','stop','net_R_c1','cost_c1'):
                changed=[dict(actual[0],**{key:'9999'})]
                with self.assertRaises(AssertionError):check_rows(changed,expected,(key,),'CORRUPT_TRADE')


if __name__=='__main__':unittest.main()
