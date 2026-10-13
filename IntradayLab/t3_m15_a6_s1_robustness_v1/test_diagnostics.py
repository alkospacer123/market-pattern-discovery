"""Hand-calculated diagnostic cases plus immutable-trajectory/causal composition tests."""
import copy,unittest
from datetime import datetime
import common as C,analysis as A,scalar_analysis as I
from test_execution import fixture,frame
import engine as E,scalar as S

def trade(i,r,month=1,symbol='USDRUBF',side='LONG',year=2024):
    at=datetime(year,month,2,10,tzinfo=C.TZ)
    return {'instrument':symbol,'trade_id':str(i),'gross_R':r,'exit_time':at,'entry_time':at-C.STEP,'signal_time':at-C.STEP,'direction':side}

def output(rows):return {'trades':rows,'OPEN_POSITIONS':[],'PERIOD_END_OPEN_POSITIONS':[]}

def scenario(tables,name,year='2024',side='ALL',scope='ALL_FOUR'):
    return next(r for r in tables['scenario_summary'] if r['scenario']==name and r['year']==year and r['direction']==side and r['scope']==scope)

class Diagnostics(unittest.TestCase):
    def test_fixed_candidate_budget(self):
        self.assertEqual(C.VERSIONS,{'TRAIL_375':3.75})
    def test_stress_reclassifies_small_winner_and_zero(self):
        out=output([trade(i,r) for i,r in enumerate([2.,-1.,.03,0.])])
        for tables in [A.build(out),I.evaluate(out)]:
            r=scenario(tables,'R_STRESS_005')
            self.assertEqual((r['wins'],r['losses'],r['zero_trades']),(1,3,0))
            self.assertAlmostEqual(r['gross_PF'],1.95/1.12);self.assertAlmostEqual(r['gross_R'],.83)
            self.assertAlmostEqual(r['closed_R_drawdown'],1.12);self.assertEqual(r['months'],12)
    def test_month_removal_preserves_original_denominator(self):
        out=output([trade(1,3.,1),trade(2,1.,2),trade(3,-2.,3)])
        for tables in [A.build(out),I.evaluate(out)]:
            r=scenario(tables,'EX_BEST1_MONTHS');self.assertEqual(r['excluded_months'],'2024-01')
            self.assertEqual((r['months'],r['retained_calendar_months'],r['positive_months']),(12,11,1))
            self.assertEqual(r['gross_R'],-1.);self.assertEqual(r['gross_PF'],.5)
    def test_winner_ties_deterministic_and_only_positive(self):
        rows=[trade(2,2.),trade(1,2.),trade(3,-1.)]
        for tables in [A.build(output(rows)),I.evaluate(output(list(reversed(rows))))]:
            r=scenario(tables,'EX_TOP1_WINNERS');self.assertEqual(r['gross_R'],1.);self.assertEqual(r['gross_PF'],2.)
            members=[r for r in tables['scenario_ledger'] if r['scenario']=='EX_TOP1_WINNERS' and r['direction']=='ALL' and r['year']=='2024' and not r['retained']]
            self.assertEqual(members[0]['trade_id'],'1')
    def test_diagnostics_do_not_mutate_input_or_OPEN(self):
        out=output([trade(1,2.),trade(2,-1.)]);out['OPEN_POSITIONS']=[{'instrument':'USDRUBF','direction':'LONG','gross_R':999.}]
        old=copy.deepcopy(out)
        for fn in [A.build,I.evaluate]:
            tables=fn(out);self.assertEqual(out,old)
            self.assertAlmostEqual(scenario(tables,'R_STRESS_010')['gross_R'],.8)
            self.assertTrue(scenario(tables,'R_STRESS_010')['original_OPEN_unchanged'])
    def test_leave_out_additivity_and_calendar(self):
        rows=[trade(i,r,symbol=s) for i,(s,r) in enumerate(zip(C.SYMBOLS,[3.,1.,-1.,2.]))]
        for tables in [A.build(output(rows)),I.evaluate(output(rows))]:
            self.assertEqual(scenario(tables,'LEAVE_OUT_USDRUBF')['gross_R'],2.)
            self.assertEqual(scenario(tables,'LEAVE_OUT_USDRUBF')['months'],12)
    def test_no_coverage_distinct_from_available_zero(self):
        for fn in [A.build,I.evaluate]:
            tables=fn(output([trade(1,1.,7,'GLDRUBF',year=2023)]))
            gl=[r for r in tables['monthly'] if r['scope']=='GLDRUBF' and r['direction']=='ALL']
            self.assertEqual(gl[0]['status'],'NO_COVERAGE');self.assertEqual(gl[6]['coverage'],'AVAILABLE_PARTIAL_START')
            self.assertEqual(gl[7]['status'],'AVAILABLE_NO_CLOSED')
    def test_november2023_noop_and_2024_excluded(self):
        for tables in [A.build(output([trade(1,2.,11)])),I.evaluate(output([trade(1,2.,11)]))]:
            self.assertEqual(scenario(tables,'EX_NOV2024','2023')['excluded_months'],'')
            self.assertEqual(scenario(tables,'EX_NOV2024')['closed'],0)
    def test_independent_accounting_hand_drawdown_and_runs(self):
        rows=[trade(i,r,month=i+1) for i,r in enumerate([2.,-1.,-2.,4.])]
        for tables in [A.build(output(rows)),I.evaluate(output(rows))]:
            r=next(r for r in tables['summary'] if r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['year']=='2024')
            self.assertEqual(r['gross_R'],3.);self.assertEqual(r['closed_R_drawdown'],3.)
            self.assertEqual(r['max_negative_month_run'],2);self.assertEqual(r['max_losing_trade_run'],2)
    def test_cross_instrument_state_isolation(self):
        # Synthetic runs only. Omitting another symbol cannot change this symbol's state.
        bars=fixture(signals=[1,1,0]);bars[1]['l']=97.
        for engine in ['primary','scalar']:
            replay=(lambda sym:E.replay(frame(bars),sym,'TRAIL_375','C1','NEXT_OPEN')) if engine=='primary' else (lambda sym:S.simulate(bars,sym,'TRAIL_375','C1','NEXT_OPEN'))
            first=copy.deepcopy(replay('USDRUBF'))
            for sym in C.SYMBOLS[1:]:replay(sym)
            self.assertEqual(C.plain(first),C.plain(replay('USDRUBF')))

    def test_presentation_matches_independent_small_case(self):
        import tempfile
        from pathlib import Path
        import report,audit
        with tempfile.TemporaryDirectory(dir=C.HERE/'work') as temp:
            folder=Path(temp);out=output([trade(1,2.),trade(2,-1.,2)])
            report.render(A.build(out),folder)
            self.assertEqual(audit.presentation(folder,I.evaluate(out),folder)['status'],'PASS')

if __name__=='__main__':unittest.main(verbosity=2)
