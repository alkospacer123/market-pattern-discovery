"""Monthly boundaries, event timing, non-circular evaluation and selection cost."""
import unittest
from datetime import datetime,timedelta

from V20_TradingSystem_M15.v20_runtime.regime_monthly_comparison import (
    Track,GOOD,BAD,UNKNOWN,assign_signals,episode_spans,evaluate_episode,
    seconds_between,filter_result,months_until,detect_periods,
)

T=datetime(2019,1,1)


def outcomes(values):
    return [dict(instrument='Si',contract='Si',signal=T+timedelta(days=i),
                 entry_time=T+timedelta(days=i,minutes=15),available=T+timedelta(days=i+2),
                 raw_R=float(v),stop_aware=float(v),fp2=int(v>0),fp5=0,stop_touch=v<0)
            for i,v in enumerate(values)]


def signals(rows):
    return [dict(instrument=r['instrument'],signal=r['signal'],decision=r['entry_time'],outcome=r)
            for r in rows]


class MonthlyComparisonTests(unittest.TestCase):
    def test_month_boundary_leap_and_partial_2026(self):
        months=list(months_until(datetime(2026,9,16)))
        self.assertEqual(len(months),105)
        feb=next((b-a).days for a,b,_ in months if a.strftime('%Y-%m')=='2020-02')
        self.assertEqual(feb,29)
        self.assertEqual(months[-1][1],datetime(2026,9,16))
        self.assertEqual((months[-1][1]-months[-1][0]).days,15)

    def test_calendar_days_are_intervals_and_outside_archive_is_unknown(self):
        track=Track([(T,GOOD),(T+timedelta(days=10),BAD)],T,T+timedelta(days=20))
        seconds,available=seconds_between(track,T-timedelta(days=5),T+timedelta(days=25))
        self.assertEqual(available/86400,20)
        self.assertEqual({s:v/86400 for s,v in seconds.items()},{GOOD:10,BAD:10,UNKNOWN:10})

    def test_decision_uses_known_state_and_not_own_future_outcome(self):
        rows=outcomes([1,-1,1])
        change=rows[1]['available']
        track=Track([(T,GOOD),(change,BAD)],T,T+timedelta(days=10))
        assigned=assign_signals(signals(rows),track)
        self.assertTrue(all(s['state']==GOOD for s in assigned))
        poisoned=[dict(s,outcome=object()) for s in signals(rows)]
        self.assertEqual([s['state'] for s in assign_signals(poisoned,track)],
                         [s['state'] for s in assigned])
        self.assertEqual(track.at(change),BAD)
        self.assertEqual(track.at(change-timedelta(microseconds=1)),GOOD)

    def test_episode_count_and_recovery_through_unknown(self):
        points=[(T,GOOD),(T+timedelta(days=1),BAD),(T+timedelta(days=2),BAD),
                (T+timedelta(days=3),UNKNOWN),(T+timedelta(days=4),GOOD),
                (T+timedelta(days=5),UNKNOWN),(T+timedelta(days=6),GOOD)]
        warnings,returns=episode_spans(Track(points,T,T+timedelta(days=10)))
        self.assertEqual((len(warnings),len(returns)),(1,1))
        self.assertEqual(returns[0]['prior_warning'],T+timedelta(days=1))

    def test_two_bad_blocks_do_not_make_the_external_alert_true(self):
        rows=outcomes([1]*40+[-1]*40+[2]*40)
        t=rows[79]['available']
        result=evaluate_episode(rows,dict(start=t,end=t+timedelta(days=10)),'WARNING')
        self.assertEqual(result['verdict'],'FALSE')
        self.assertEqual(result['persistence'],'RECOVERED')
        self.assertTrue(result['full_return_observed'])
        self.assertGreater(result['evaluation_available'],t)

    def test_mixed_future_and_archive_tail_are_unresolved(self):
        rows=outcomes([1]*40+[-1]*20+[1]*20)
        t=rows[39]['available']
        result=evaluate_episode(rows,dict(start=t,end=t),'WARNING')
        self.assertEqual(result['verdict'],'UNRESOLVED')
        tail=evaluate_episode(rows,dict(start=rows[69]['available'],end=rows[-1]['available']),'WARNING')
        self.assertEqual(tail['next40_n'],10)
        self.assertIsNone(tail['evaluation_available'])
        self.assertEqual(tail['verdict'],'UNRESOLVED')

    def test_filter_counts_excluded_positive_negative_and_unknown(self):
        ss=signals(outcomes([2,-1,3]))
        ss=[dict(s,state=state) for s,state in zip(ss,(BAD,GOOD,UNKNOWN))]
        ss.append(dict(instrument='Si',signal=T,decision=T,outcome=None,state=UNKNOWN))
        permissive=filter_result(ss,'NOT_BAD')
        self.assertEqual((permissive['total_raw'],permissive['observed'],permissive['censored']),(3,2,1))
        self.assertEqual((permissive['excluded_positive'],permissive['excluded_negative']),(1,0))
        self.assertEqual(permissive['excluded_positive_share'],.5)
        strict=filter_result(ss,'ONLY_FAVORABLE')
        self.assertEqual(strict['total_raw'],1)
        self.assertEqual(strict['excluded_positive_share'],1)
        self.assertEqual(strict['excluded_censored'],1)

    def test_confirmation_at_period_end_is_not_hidden_as_early_detection(self):
        end=T+timedelta(days=100)
        track=Track([(T,UNKNOWN),(end,BAD)],T,end+timedelta(days=20))
        period=dict(kind='WEAK',start=T,end=end,label_available=end)
        rows,_=detect_periods(track,[period],[])
        self.assertEqual(rows[0]['delay_days'],100)
        self.assertTrue(rows[0]['confirmation_at_period_end'])
        silent=Track([(T,UNKNOWN)],T,end+timedelta(days=20))
        rows,_=detect_periods(silent,[period],[])
        self.assertTrue(rows[0]['missed'])


if __name__=='__main__':
    unittest.main()
