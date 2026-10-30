"""Addressed causality/quality tests of the one phase probe; no strategy replay."""
from copy import deepcopy
from datetime import date,datetime,timedelta
import json
from statistics import median
import unittest

from ..market_phase_probe import (phase,prepare_series,timeline,snapshot,future,annotate_future,phase_before,OUT,STATES,epoch)
from ..market_suitability import M15Bar,STEP,evaluate_market_card
from ..regime_monthly_comparison import read_csv,dt


def fixture(n=65):
    bars=[]
    for i in range(n):
        t=datetime(2015,1,1,10)+timedelta(days=i)
        for j in range(32):
            o=100+2*i+.03*j
            bars.append(M15Bar(t+STEP*j,o,o+.08,o-.02,o+.05,10))
    s=prepare_series(bars)
    return s,[(d,'ONE') for d in sorted(s['sessions'])]


class PhaseTests(unittest.TestCase):
    def test_prior40_and_strict_ties(self):
        t=datetime(2015,1,1)
        past=[dict(er=.2,continuation=.4,available=t+timedelta(days=i)) for i in range(40)]
        self.assertEqual(phase(dict(er=.3,continuation=.5),past)['phase'],'TREND')
        self.assertEqual(phase(dict(er=.1,continuation=.3),past)['phase'],'CHOP')
        self.assertEqual(phase(dict(er=.2,continuation=.5),past)['phase'],'TRANSITION')
        self.assertEqual(phase(dict(er=.3,continuation=.3),past)['phase'],'TRANSITION')
        self.assertEqual(phase(dict(er=.3,continuation=.5),past[:39])['phase'],'UNKNOWN')

    def test_invalid_current_does_not_read_numeric_history(self):
        self.assertEqual(phase(None,[{'er':'POISON'}]*40)['phase'],'UNKNOWN')

    def test_prefix_invariance_actual_card(self):
        source,plan=fixture()
        full=timeline('TEST',plan,{'ONE':source})
        cut=plan[59][0];end=datetime.combine(cut,datetime.min.time()).replace(hour=18)
        prefix=prepare_series([b for b in source['bars'] if b.open_time+STEP<=end])
        q=timeline('TEST',plan[:60],{'ONE':prefix})
        self.assertEqual(full[:60],q)
        self.assertTrue(all(r['baseline_last']<r['available'] for r in q if 'baseline_last' in r))

    def test_M15_not_available_before_close(self):
        source,plan=fixture(20);sessions=[source['sessions'][d] for d,c in plan]
        with self.assertRaisesRegex(ValueError,'SESSION_NOT_OBSERVABLY_COMPLETE'):
            evaluate_market_card('TEST',sessions,as_of=sessions[-1].closed_at-timedelta(minutes=1))

    def test_roll_does_not_stitch_OHLC(self):
        source,plan=fixture(65)
        changed=[(d,'ONE' if i<60 else 'TWO') for i,(d,c) in enumerate(plan)]
        rows=timeline('TEST',changed,{'ONE':source,'TWO':source})
        self.assertTrue(all(r['phase']=='UNKNOWN' for r in rows[60:]))
        self.assertTrue(all(r['reason']=='ROLL_OR_INITIAL20_WARMUP' for r in rows[60:]))

    def test_missing_session_and_no_selection_are_unknown(self):
        source,plan=fixture(65)
        source['sessions'].pop(plan[50][0])
        rows=timeline('TEST',plan,{'ONE':source})
        self.assertEqual(rows[50]['phase'],'UNKNOWN')
        self.assertEqual(rows[50]['reason'],'INCOMPLETE20_WINDOW')
        plan[60]=(plan[60][0],'')
        rows=timeline('TEST',plan,{'ONE':source})
        self.assertEqual(rows[60]['reason'],'NO_LOCKED_SELECTION')
        self.assertEqual(rows[61]['reason'],'ROLL_OR_INITIAL20_WARMUP')

    def test_gap_invalidates_snapshot_and_future(self):
        source,plan=fixture(65)
        missing=datetime.combine(plan[50][0],datetime.min.time()).replace(hour=12)
        source=prepare_series([b for b in source['bars'] if b.open_time!=missing])
        rows=timeline('TEST',plan,{'ONE':source})
        self.assertEqual(rows[50]['phase'],'UNKNOWN')
        self.assertNotEqual(future(rows,45,{'ONE':source})['future_status'],'OBSERVED')

    def test_quarantine_at_known_break_forces_reset(self):
        t=datetime(2012,10,3,18,30)
        bars=[M15Bar(t,100,101,99,100,1),M15Bar(t+STEP*3,100,101,99,100,1)]
        source=prepare_series(bars,[t+STEP*2])
        self.assertNotEqual(source['positions'][bars[0].open_time][0],source['positions'][bars[1].open_time][0])
        self.assertEqual(source['positions'][bars[1].open_time][1],1)

    def test_future_is_not_part_of_current_classification(self):
        source,plan=fixture(65);rows=timeline('TEST',plan,{'ONE':source});original=deepcopy(rows)
        annotate_future(rows,{'ONE':source})
        for a,b in zip(original,rows):
            for key in a:self.assertEqual(a[key],b[key])

    def test_future_ten_uses_only_future_progress_and_is_censored(self):
        source,plan=fixture(65);rows=timeline('TEST',plan,{'ONE':source})
        f=future(rows,40,{'ONE':source});self.assertEqual(f['future_status'],'OBSERVED')
        self.assertGreater(f['future_first'],rows[40]['day']);self.assertGreater(f['future_available'],rows[40]['available'])
        self.assertEqual(future(rows,60,{'ONE':source})['future_status'],'CENSORED_END_OF_ARCHIVE')
        rows[45]['contract']='OTHER'
        self.assertEqual(future(rows,40,{'ONE':source})['future_status'],'ROLL_OR_NO_SELECTION')
        # Its price window is invalid, but losing the state is still counted.
        self.assertTrue(future(rows,40,{'ONE':source})['state_horizon_complete'])

    def test_pre_entry_strict_boundary_contract_and_gap(self):
        source,plan=fixture();rows=timeline('TEST',plan,{'ONE':source});r=rows[60]
        entry=r['available'];signal=entry-STEP
        state,reason,available=phase_before(rows,entry,'ONE',source,signal)
        self.assertLess(available,entry)
        self.assertEqual(phase_before(rows,entry,'OTHER',source,signal)[0],'UNKNOWN')
        known=dict(r,phase='TREND',future_er='POISON')
        self.assertEqual(phase_before([known],entry+STEP,'ONE',source,signal)[0],'TREND')
        source['positions'][signal]=(999,100)
        self.assertEqual(phase_before([known],entry+STEP,'ONE',source,signal)[0],'UNKNOWN')


class SavedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=list(read_csv(OUT/'MARKET_PHASE_CAUSAL_PROBE.csv'))
        cls.data=json.loads((OUT/'MARKET_PHASE_CAUSAL_PROBE.json').read_text())

    def test_all_published_baselines_use_prior40_only(self):
        previous={}
        for r in self.rows:
            history=previous.setdefault(r['instrument'],[])
            if r['phase']!='UNKNOWN':
                self.assertEqual(len(history[-40:]),40)
                self.assertAlmostEqual(float(r['baseline_er']),median(float(x['er']) for x in history[-40:]),places=8)
                self.assertAlmostEqual(float(r['baseline_continuation']),median(float(x['continuation']) for x in history[-40:]),places=8)
                self.assertLess(dt(r['baseline_last']),dt(r['available']))
            if r['valid']=='True':history.append(r)

    def test_no_overlap_in_external_target_sessions(self):
        used={}
        for r in self.rows:
            if r['eval_anchor']=='True' and r['future_status']=='OBSERVED':
                s=r['instrument'];first=date.fromisoformat(r['future_first']);last=date.fromisoformat(r['future_last'])
                if s in used:self.assertGreater(first,used[s])
                used[s]=last
                self.assertGreater(dt(r['future_available']),dt(r['available']))
            if r['future5_available']:
                self.assertGreater(dt(r['future5_available']),dt(r['available']))

    def test_unknown_and_coverage_totals(self):
        c=self.data['counts'];self.assertEqual(len(self.rows),c['sessions'])
        self.assertEqual(sum(r['phase']!='UNKNOWN' for r in self.rows),c['classified'])
        self.assertTrue(all(r['phase']=='UNKNOWN' for r in self.rows if r['valid']=='False'))
        for e in ('2012-2017','2018-2022','2023-2024','2025-2026_YTD'):
            group=[r for r in self.data['aggregates'] if r['period']==e and r['instrument']=='ALL']
            self.assertEqual(sum(r['sessions'] for r in group),group[0]['denominator'])
        # Same accepted 20-session feature domain as the published epoch probe.
        for period,expected in (('2018-2022',1088),('2023-2024',579)):
            q=[r for r in self.data['aggregates'] if r['period']==period and r['instrument']=='ALL']
            self.assertEqual(sum(r['valid'] for r in q),expected)

    def test_economics_uses_existing_observed_ledgers(self):
        q=[r for r in self.data['economics'] if r['period']=='ALL' and r['instrument']=='ALL']
        self.assertEqual(sum(r['n'] for r in q),3324)
        self.assertEqual(self.data['economic_assignment']['assigned'],3324)
        self.assertEqual(self.data['protocol']['replay_batches'],0)
        self.assertEqual(self.data['protocol']['parameter_searches'],0)


if __name__=='__main__':unittest.main()
