"""Independent oracle and corruption guards for causal H1/M15 and C1 ledger."""
from decimal import Decimal as D
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from IntradayLab.tests.test_trend_pullback import source,run,T,FIVE,FIFTEEN,set_parent,DAY
from IntradayLab.core.reports import csv_write
from IntradayLab.tools.audit_trend_pullback_baseline import parent_rows,episodes,replay,read_csv,check_rows,batch_context
LAB=Path(__file__).resolve().parents[1]


class IndependentTrendTests(unittest.TestCase):
    def compare(self,raw):
        ss,tt,_,strategy=run(raw)
        tuples={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()}
        parents=parent_rows('USDRUBF',tuples)
        ev,cs=episodes('USDRUBF',parents,True);es,et=replay('USDRUBF',parents,ev)
        with TemporaryDirectory(dir=LAB/'work') as folder:
            for name,actual,expected in (('signals',ss,es),('trades',tt,et),('contexts',strategy.context_records,cs)):
                expected=[r for r in expected if str(r.get('signal_start',r.get('test_start',r.get('signal_at'))))[:10]==str(DAY)]
                path=Path(folder)/(name+'.csv');csv_write(path,actual)
                keys=sorted({k for r in expected for k in r if k!='unknown_effective_at'})
                check_rows(read_csv(path),expected,keys,name)

    def test_long_short_all_fields_and_lineage(self):
        for side in (1,-1):self.compare(source(side))

    def test_missing_wait_entry_known_open_path(self):
        for offset in (75,90,95,100,110):
            raw=source();del raw[T+FIVE*(offset//5)];self.compare(raw)

    def test_all_missing_h1_children(self):
        for i in range(12):
            raw=source();del raw[T+i*FIVE];self.compare(raw)

    def test_stop_take_gap_oracle(self):
        for vals in ((105,120,100,105),(101,102,100,101),(105,120,104.9,105)):
            raw=source();set_parent(raw,T+7*FIFTEEN,vals);self.compare(raw)

    def test_context_prices_availability_lineage_corruption_detected(self):
        raw=source();p=parent_rows('USDRUBF',{t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()})
        _,cs=episodes('USDRUBF',p,True);expected=cs[:5]
        with TemporaryDirectory(dir=LAB/'work') as folder:
            path=Path(folder)/'context.csv';csv_write(path,expected);actual=read_csv(path)
            for key in ('h1_close','h1_available_at','child_m5_starts','context_direction'):
                changed=[dict(r) for r in actual];changed[-1][key]='CORRUPT'
                with self.assertRaises(AssertionError):check_rows(changed,expected,(key,),'CORRUPT_CONTEXT')

    def test_stop_take_entry_exit_cost_corruption_detected(self):
        raw=source();p=parent_rows('USDRUBF',{t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()})
        _,expected=replay('USDRUBF',p,episodes('USDRUBF',p));expected=expected[:1]
        with TemporaryDirectory(dir=LAB/'work') as folder:
            path=Path(folder)/'trade.csv';csv_write(path,expected);actual=read_csv(path)
            for key in ('stop','take','entry_price','exit_price','net_R_c1','cost_c1'):
                with self.assertRaises(AssertionError):check_rows([dict(actual[0],**{key:'99999'})],expected,(key,),'CORRUPT_TRADE')

    def test_future_prices_do_not_change_context_oracle(self):
        raw=source();p=parent_rows('USDRUBF',{t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()})
        at=T+4*FIFTEEN;w=(T,T+16*FIFTEEN)
        first=batch_context('USDRUBF',p,at,w,None)
        changed={t:((D(1),D(999),D(1),D(1),D(1)) if t>=at+FIFTEEN else b) for t,b in p.items()}
        self.assertEqual(first,batch_context('USDRUBF',changed,at,w,None))


if __name__=='__main__':unittest.main()
