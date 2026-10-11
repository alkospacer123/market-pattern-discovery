"""Independent synthetic oracle and source-budget corruption checks before P&L."""
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from IntradayLab.core.backtester import Backtester
from IntradayLab.core.execution import ENTRY_NEXT_OPEN
from IntradayLab.core.models import Context
from IntradayLab.strategies.equal_high_low_m5 import EqualHighLowM5
from IntradayLab.tests import test_equal_high_low_m5 as fixtures
from IntradayLab.tools.audit_equal_high_low_baseline import episodes,replay
from IntradayLab.tools.audit_canonical_baseline import check_rows
from IntradayLab.tools.equal_high_low_contract import bounded_reads,check_output


class IndependentOracleTests(unittest.TestCase):
    setUp=fixtures.NextOpenTests.setUp
    at=fixtures.NextOpenTests.at
    bar=fixtures.NextOpenTests.bar
    make_day=fixtures.NextOpenTests.make_day
    setup_cluster=fixtures.NextOpenTests.setup_cluster

    def compare(self):
        raw={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in self.rows.items()}
        ss,tt,_=Backtester(self.rules,entry_mode=ENTRY_NEXT_OPEN).run(EqualHighLowM5(fixtures.PARAMETERS),
            'USDRUBF',dict(sorted(self.rows.items())),start=self.day,end_exclusive=max(self.rows).date()+timedelta(days=1))
        es,et=replay('USDRUBF',raw,episodes('USDRUBF',raw))
        for actual,expected,label in ((ss,es,'signals'),(tt,et,'trades')):
            keys=sorted({k for r in expected for k in r if k!='unknown_effective_at'})
            check_rows(actual,expected,keys,label)
        return ss,tt,raw

    def test_independent_long_short_all_fields(self):
        for side in (-1,1):
            self.setup_cluster(side);self.compare()

    def test_missing_and_off_grid_open(self):
        self.setup_cluster();del self.rows[self.at('10:15')];self.compare()
        self.setup_cluster();self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.971')
        self.compare()

    def test_independent_preentry_geometry_reasons(self):
        for op in ('101.01','101','100.99','100.95','100.87'):
            self.setup_cluster();self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o=op,h='101.1',l='100.8',c=op)
            self.compare()

    def test_same_bar_stop_take_and_session_flat(self):
        self.setup_cluster();self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.97',h='101.10',l='100.5',c='100.97')
        _,t,_=self.compare();self.assertEqual(t[0]['exit_reason'],'STOP')
        self.assertTrue(t[0]['stop_take_conflict'])

    def test_invalid_exposed_path_and_later_day_conditional(self):
        self.setup_cluster();self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.97',v='0')
        tomorrow=self.day+timedelta(days=1);self.rows.update(self.make_day(tomorrow))
        for i in range(3):
            t=self.at('10:00',tomorrow)+i*fixtures.FIVE
            self.rows[t]=self.bar(t,o='100.97',h='101',l=str(D('100.90')-i*D('.01')),c='100.97')
        t=self.at('10:15',tomorrow);self.rows[t]=self.bar(t,o='100.97',h='101',l='100.94',c='100.97')
        _,tt,_=self.compare()
        self.assertEqual(tt[0]['status'],'UNKNOWN')
        self.assertTrue(any(t['model_filled'] and t['prior_unknown_requires_flat_assumption'] for t in tt[1:]))

    def test_close_oracle_is_separate_hypothetical_price(self):
        self.setup_cluster();self.rows[self.at('10:15')]=self.bar(self.at('10:15'),o='100.98')
        ss,tt,raw=self.compare();es,et=replay('USDRUBF',raw,episodes('USDRUBF',raw),close_oracle=True)
        self.assertEqual(tt[0]['entry_price'],D('100.98'))
        self.assertEqual(et[0]['entry_price'],D('100.97'))
        self.assertEqual(et[0]['entry_mode'],'ENTRY_CLOSE_ORACLE')

    def test_tick_and_session_reset(self):
        st=EqualHighLowM5(fixtures.PARAMETERS);st.begin_day('USDRUBF',self.day)
        for i in range(3):
            t=self.at('10:00')+i*fixtures.FIVE;b=self.bar(t,o='100.97',h='101',l=str(D('100.90')-i*D('.01')),c='100.97')
            ctx=Context('USDRUBF',t,t+fixtures.FIVE,(self.at('10:00'),self.at('14:00')),
                D('.01') if i<2 else D('.001'),{})
            self.assertEqual(st.on_bar(b,ctx),[])


class ReadBudgetTests(unittest.TestCase):
    def test_guard_refuses_future_bytes_other_files_and_buffering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);path=root/'allowed.csv';path.write_bytes(b'2023\n2024\n')
            cfg={'inputs':{'x':{'path':'allowed.csv','prefix_bytes':5}}}
            with bounded_reads(root,cfg) as receipts:
                with path.open('rb',buffering=0) as stream:
                    self.assertEqual(stream.read(5),b'2023\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):stream.read(1)
                with self.assertRaisesRegex(ValueError,'BUFFERING'):path.open('rb')
                with self.assertRaisesRegex(ValueError,'SOURCE_PATH'):(root/'other.csv').open('rb',buffering=0)
            self.assertEqual(receipts[0]['maximum_offset'],5)
            self.assertEqual(receipts[0]['bytes_2024_plus_read'],0)

    def test_output_guard(self):
        with self.assertRaisesRegex(ValueError,'SCOPE'):check_output(Path('/tmp/not-intraday'))

    def test_synthetic_runner_reports_and_full_independent_audit(self):
        from IntradayLab.tools import run_equal_high_low_baseline as runner
        from IntradayLab.tools import audit_equal_high_low_baseline as auditor
        from IntradayLab.core.calendar import MarketRules
        from IntradayLab.core.data_loader import validate_bar
        cfg=json.loads(runner.CONFIG.read_text());rules=MarketRules(cfg)
        raw={};independent={};day=__import__('datetime').date(2023,1,4)
        for symbol in cfg['instruments']:
            rows={};step=rules.tick(symbol,rules.at(day,'10:00'))
            for a,z in rules.windows(day):
                at=a
                while at<z:
                    prices=[D(100),D(100)+5*step,D(100)-5*step,D(100),D(10)]
                    if at<rules.at(day,'10:15'):
                        i=int((at-rules.at(day,'10:00'))/fixtures.FIVE)
                        prices=[D(100)-3*step,D(100),D(100)-(10+i)*step,D(100)-3*step,D(10)]
                    elif at==rules.at(day,'10:15'):
                        prices=[D(100)-3*step,D(100)-2*step,D(100)-4*step,D(100)-3*step,D(10)]
                    rows[at]=validate_bar(at,tuple(prices),fixtures.FIVE,step);at+=fixtures.FIVE
            raw[symbol]=rows
            independent[symbol]={at:(b.open,b.high,b.low,b.close,b.volume) for at,b in rows.items()}
        work=runner.LAB/'work';work.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=work) as tmp:
            out=Path(tmp)
            with patch.object(runner,'verify_freeze',return_value=(cfg,'0'*40,'synthetic')), \
                 patch.object(runner,'protected_check'), \
                 patch.object(runner,'load_market_data',return_value=(raw,{})):
                runner.run(Path('/workspace/market-pattern-data'),out)
            with patch('IntradayLab.tools.equal_high_low_contract.verify_freeze'), \
                 patch.object(auditor,'read_source',return_value=(independent,{})):
                result=auditor.audit(Path('/workspace/market-pattern-data'),out)
            self.assertEqual(result['status'],'PASS')


if __name__=='__main__':unittest.main()

