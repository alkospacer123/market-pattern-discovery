"""Pre-read synthetic boundary, carry, causality, accounting and decision tests."""
import io,json,unittest,tempfile,hashlib
from pathlib import Path
from datetime import datetime,timedelta
from unittest.mock import patch
import common as C,scalar as S,engine as E,safe_source as B,accounting as A
from test_execution import fixture,frame
END=datetime(2026,1,1,tzinfo=C.TZ)
ROW=b'X;2025-12-30 10:00:00;100;101;99;100;1\n'
class Spy(io.BytesIO):
    def __init__(self,data,limit):super().__init__(data);self.limit=limit
    def read(self,n=-1):
        assert n>=0 and self.tell()+n<=self.limit,'FORBIDDEN_READ'
        return super().read(n)
    def readline(self,n=-1):
        assert self.tell()<self.limit,'FORBIDDEN_SUFFIX'
        out=super().readline(n);assert self.tell()<=self.limit;return out
    def close(self):pass
class WF(unittest.TestCase):
    def setUp(self):self.ce=C.END;self.se=S.END
    def tearDown(self):C.END=self.ce;S.END=self.se
    def readers(self,data,end,limit):
        for fn in (B.read_primary,B.read_scalar):
            stream=Spy(data,limit)
            with patch.object(B,'open_raw',return_value=stream):rows,rec=fn('synthetic',end)
            self.assertEqual(stream.tell(),rec['bytes_read']);yield rows,rec
    def test_locked_year_no_timestamp_no_prices_no_volume(self):
        data=B.HEADER+ROW+b'X;2026-01-01 10:00:00;POISON\n'
        for rows,r in self.readers(data,END,len(B.HEADER+ROW+b'X;2026')):
            self.assertEqual(len(rows),1);self.assertEqual(r['OHLCV_suffix_reads'],1);self.assertFalse(r['locked_timestamp_decoded'])
    def test_completion_equal_cutoff_excluded_before_tail(self):
        lead=b'X;2025-12-31 23:45:00;'
        for rows,r in self.readers(B.HEADER+ROW+lead+b'POISON\n',END,len(B.HEADER+ROW+lead)):self.assertEqual(len(rows),1)
    def test_control_no_2025_timestamp_or_prices(self):
        good=ROW.replace(b'2025',b'2024');lead=b'X;2025'
        for rows,r in self.readers(B.HEADER+good+lead+b'-01-01 00:00:00;POISON\n',self.ce,len(B.HEADER+good+lead)):self.assertEqual(len(rows),1)
    def test_quarter_reads_2025_then_stops(self):
        good=ROW.replace(b'12-30',b'03-30');lead=b'X;2025-04-01 00:00:00;'
        for rows,r in self.readers(B.HEADER+good+lead+b'POISON\n',datetime(2025,4,1,tzinfo=C.TZ),len(B.HEADER+good+lead)):self.assertEqual(len(rows),1)
    def test_future_poison_cannot_change_prefix_digest(self):
        for poison in (b'0',b'999999',b'NOT_NUMERIC'):
            lead=b'X;2026'
            for rows,r in self.readers(B.HEADER+ROW+lead+b'-01-01 00:00:00;'+poison+b'\n',END,len(B.HEADER+ROW+lead)):
                self.assertEqual(r['allowed_prefix_sha256'],hashlib.sha256(B.HEADER+ROW).hexdigest())
    def test_unbuffered_FileIO(self):
        with tempfile.TemporaryDirectory(dir='/workspace/work/wf-task') as d:
            p=Path(d)/'test.csv';p.write_bytes(B.HEADER+ROW)
            with B.open_raw(p) as f:self.assertIsInstance(f,io.FileIO)
    def test_unsorted_duplicate_rejected(self):
        for suffix in (ROW,ROW.replace(b'12-30',b'12-29')):
            for fn in (B.read_primary,B.read_scalar):
                with patch.object(B,'open_raw',return_value=io.BytesIO(B.HEADER+ROW+suffix)):
                    with self.assertRaises(AssertionError):fn('test',END)
    def test_2026_replay_forbidden(self):
        C.END=END;S.END=END;b=fixture(['2025-12-31 23:45','2026-01-01 00:00'],[1,0])
        with self.assertRaises(AssertionError):E.replay(frame(b),'USDRUBF','TRAIL_375','C1','NEXT_OPEN')
        with self.assertRaises(AssertionError):S.simulate(b,'USDRUBF','TRAIL_375','C1','NEXT_OPEN')
    def test_quarter_position_initial_R_Stop_extreme_carry(self):
        C.END=END;S.END=END
        for side in (1,-1):
            b=fixture(['2025-03-31 23:15','2025-03-31 23:30','2025-04-01 00:15'],[side,0,0],side)
            for fn in (lambda x:E.replay(frame(x),'USDRUBF','TRAIL_375','C1','NEXT_OPEN'),lambda x:S.simulate(x,'USDRUBF','TRAIL_375','C1','NEXT_OPEN')):
                old=fn(b[:2]);new=fn(b);self.assertEqual(old[1]['trade_id'],new[1]['trade_id']);self.assertEqual(old[1]['initial_risk'],new[1]['initial_risk'])
                self.assertEqual(new[2][-1]['active_stop'],old[1]['active_stop']);self.assertEqual(new[2][-1]['extreme_before'],old[1]['favorable_extreme'])
    def test_pending_cross_quarter_adjacent(self):
        C.END=END;S.END=END;b=fixture(['2025-03-31 23:45','2025-04-01 00:00'],[1,0])
        for fn in (lambda x:E.replay(frame(x),'USDRUBF','TRAIL_375','C1','NEXT_OPEN'),lambda x:S.simulate(x,'USDRUBF','TRAIL_375','C1','NEXT_OPEN')):
            self.assertTrue(fn(b[:1])[3][0]['pending_at_end']);r=fn(b);self.assertEqual(r[1]['entry_time'],b[0]['at']);self.assertEqual(r[3][0]['decision_reason'],'EXECUTED_NEXT_OPEN')
    def test_fixed_stress_reclassifies_and_winner_ties(self):
        at=datetime(2025,2,1,tzinfo=C.TZ);rows=[{'instrument':'USDRUBF','trade_id':str(i),'exit_time':at,'gross_R':r} for i,r in enumerate((2.,2.,-1.,.03,0.))]
        scenarios={n:r for n,r,_,_ in A.scenarios(rows,A.MONTHS)}
        stressed=scenarios['R_STRESS_0.05'];self.assertAlmostEqual(sum(r['gross_R'] for r in stressed),3.03-.25)
        self.assertEqual([r['trade_id'] for r in scenarios['EX_TOP1_WINNERS']],['1','2','3','4']);self.assertEqual(A.metrics(stressed,A.MONTHS)['losses'],3)
    def test_recovery_hand_case(self):
        at=datetime(2025,1,2,tzinfo=C.TZ);rows=[{'instrument':'USDRUBF','trade_id':str(i),'exit_time':at+timedelta(days=i),'gross_R':v} for i,v in enumerate((2.,-1.,-2.,4.,-1.))]
        r=A.recovery(rows);self.assertEqual(r[0]['max_depth_R'],3.);self.assertTrue(r[0]['recovered']);self.assertEqual(r[0]['days_to_recovery'],2.);self.assertFalse(r[1]['recovered'])
    def test_inherited_not_new(self):
        self.assertFalse(A.cohort({'signal_time':datetime(2024,12,30,tzinfo=C.TZ),'entry_time':datetime(2024,12,30,tzinfo=C.TZ)}))
        self.assertTrue(A.cohort({'signal_time':datetime(2025,1,2,tzinfo=C.TZ),'entry_time':datetime(2025,1,2,tzinfo=C.TZ)}))
    def test_authorization_nonoverlap(self):
        s=json.loads((C.HERE/'SPEC.json').read_text());a=json.loads((C.HERE/'USER_AUTHORIZATION.json').read_text())
        self.assertTrue(a['WF_2025_AUTHORIZED']);self.assertTrue(a['TRUE_OOS_2026_LOCKED'])
        for x,y in zip(s['quarters'],s['quarters'][1:]):self.assertEqual(x['end'],y['start'])
        self.assertEqual(s['quarters'][-1]['end'],s['TRUE_OOS']['start']);self.assertFalse(s['TRUE_OOS']['read'])
    def test_positive_PF_not_auto_PASS(self):
        r={'period':'FULL_WF','cohort':'CALENDAR_CLOSED','scope':'ALL_FOUR','direction':'ALL','closed':2,'gross_PF':1.1,'gross_R':.1,'expectancy_R':.05};n=r|{'cohort':'NEW_WF_COHORT'}
        t={'summary':[r,n],'scenario_summary':[],'coverage':[{'status':'AVAILABLE'}]*48}
        self.assertEqual(A.decide(t)['status'],'WF_REVIEW_REQUIRED')
        t['summary'][1]=n|{'gross_R':-1.};self.assertEqual(A.decide(t)['status'],'WF_GROSS_EDGE_NOT_CONFIRMED')
        t['summary'][1]=n;t['summary'].append(r|{'period':'W1','gross_R':-1.});self.assertEqual(A.decide(t)['status'],'WF_MIXED')
        t['coverage']=[];self.assertEqual(A.decide(t)['status'],'WF_INSUFFICIENT_EVIDENCE')
if __name__=='__main__':unittest.main(verbosity=2)
