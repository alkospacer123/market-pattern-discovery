"""Fail-closed synthetic checks for YTD source cutoff and gross-only R."""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import run_ytd_oos as T

TZ=ZoneInfo("Europe/Moscow")
HEADER=b"Ticker;Datetime;Open;High;Low;Close;Volume\n"

class YTDPreRead(unittest.TestCase):
    def write(self,content):
        td=tempfile.TemporaryDirectory()
        file=Path(td.name)/'input.csv'
        file.write_bytes(HEADER+content)
        return td,file

    def test_first_excluded_bar_has_poison_ohlc(self):
        td,p=self.write(
            b"USDRUBF;2026-10-12 23:30:00;90;92;88;91;100\n"
            b"USDRUBF;2026-10-12 23:45:00;SECRET_LOCKED_UNREADABLE_SUFFIX\n"
        )
        with td:
            for mode in ('primary','scalar'):
                rows,receipt=T.parse_file(p,T.CUTOFF,mode)
                self.assertEqual(len(rows),1)
                self.assertTrue(receipt['excluded_OHLCV_decoded']==False)
                self.assertEqual(receipt['stop_reason'],'FIRST_COMPLETION_OUTSIDE_AUTHORIZED_CUTOFF')

    def test_future_wrong_prices_not_read(self):
        td,p=self.write(
            b"USDRUBF;2026-10-12 23:30:00;90;92;88;91;100\n"
            b"USDRUBF;2026-11-01 00:00:00;BAD_NOT_PERMITTED\n"
        )
        with td:
            a,x=T.parse_file(p,T.CUTOFF,'primary')
            b,y=T.parse_file(p,T.CUTOFF,'scalar')
            self.assertEqual(len(a),1)
            self.assertEqual(len(b),1)
            self.assertEqual(x['prefix_sha256'],y['prefix_sha256'])

    def test_sortedness_and_finite_values_fail_closed(self):
        td,p=self.write(
            b"USDRUBF;2026-03-01 10:00:00;90;92;88;91;100\n"
            b"USDRUBF;2026-03-01 10:00:00;90;92;88;91;100\n"
        )
        with td:
            with self.assertRaises(AssertionError):T.parse_file(p,T.CUTOFF,'primary')

    def test_2025_control_reader_uses_2026_boundary(self):
        td,p=self.write(
            b"USDRUBF;2025-12-30 10:00:00;90;92;88;91;100\n"
            b"USDRUBF;2026-01-01 00:00:00;LOCKED_NOT_ALLOWED\n"
        )
        with td:
            a,x=T.parse_file(p,T.YEAR_START,'primary')
            self.assertEqual(len(a),1)
            self.assertFalse(x['excluded_OHLCV_decoded'])

    def test_gross_no_fee_penalty_and_dd(self):
        rows=[
            {'gross_R':2.0,'exit_time':datetime(2026,1,5,tzinfo=TZ),'instrument':'USDRUBF','trade_id':'a'},
            {'gross_R':-1.0,'exit_time':datetime(2026,1,6,tzinfo=TZ),'instrument':'CNYRUBF','trade_id':'b'},
            {'gross_R':-0.5,'exit_time':datetime(2026,1,7,tzinfo=TZ),'instrument':'IMOEXF','trade_id':'c'}
        ]
        r=T.metrics(rows)
        self.assertEqual(r['closed'],3)
        self.assertAlmostEqual(r['gross_PF'],4/3)
        self.assertAlmostEqual(r['gross_R'],0.5)
        self.assertAlmostEqual(r['closed_R_drawdown'],1.5)
        self.assertIsNone(T.metrics([])['gross_PF'])

if __name__=="__main__":
    unittest.main()
