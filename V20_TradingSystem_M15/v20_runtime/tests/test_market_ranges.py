"""Fixed interval semantics and causal provenance; synthetic observations only."""
from copy import deepcopy
from datetime import datetime, timedelta
import unittest
from V20_TradingSystem_M15.v20_runtime.market_ranges import (
    CHECKS, calibrate_ranges, percentile, bucket, evaluate_ranges, summarize,
    validate_observations, annotate_card,
)
from V20_TradingSystem_M15.v20_runtime.market_verdict import apply_market_reference
from V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability import make_sessions, inspect


def observations(year):
    rows=[]
    for strategy in ('SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE'):
        for i in range(40):
            signal=datetime(year,2,1,10)+timedelta(days=i)
            rows.append(dict(strategy=strategy,symbol='USDRUBF',signal_day=str(signal.date()),
                signal_dt=signal.isoformat(),cutoff=(signal-timedelta(days=1)).replace(hour=18).isoformat(),
                outcome_at=(signal+timedelta(days=2)).isoformat(),
                block='2026_YTD' if year==2026 else '2023-2024',
                features={metric:float(i) for _,metric,_ in CHECKS.values()},
                horizon_R=2.0 if 10<=i<=29 else -1.0,horizon_stop_touch=not 10<=i<=29))
    return rows


def profile():
    rows=observations(2023)+observations(2026)
    result=calibrate_ranges(rows)
    result['checks']=evaluate_ranges(rows,result)[1]
    result['outcomes_observed_through_msk']=max(r['outcome_at'] for r in rows)
    return result


class RangeTests(unittest.TestCase):
    def test_p25_p75_interpolation_and_closed_boundaries(self):
        self.assertEqual(percentile([30,0,20,10],.25),7.5)
        self.assertEqual(percentile([30,0,20,10],.75),22.5)
        for value,position in ((7.49,'НИЖЕ'),(7.5,'ВНУТРИ'),(22.5,'ВНУТРИ'),(22.51,'ВЫШЕ')):
            self.assertEqual(bucket(value,7.5,22.5),position)
        self.assertEqual(bucket(None,7.5,22.5),'НЕИЗВЕСТНО')
        self.assertEqual(bucket(float('nan'),7.5,22.5),'НЕИЗВЕСТНО')

    def test_boundaries_ignore_outcomes_2026_and_locked_year(self):
        rows=observations(2023)
        expected=calibrate_ranges(rows)
        changed=deepcopy(rows)
        for r in changed:
            r['horizon_R']=object()  # calibration must never inspect outcome values.
            r['horizon_stop_touch']=object()
        future=observations(2026)
        for r in future:
            r['features']={metric:object() for _,metric,_ in CHECKS.values()}
        locked=observations(2025)
        for r in locked:
            r['features']={metric:object() for _,metric,_ in CHECKS.values()}
        self.assertEqual(calibrate_ranges(changed+future+locked),expected)

    def test_control_keeps_bounds_and_detects_reversal(self):
        rows=observations(2023)+observations(2026)
        for r in rows:
            if r['block']=='2026_YTD':
                r['horizon_R']=-r['horizon_R']
        ranges=calibrate_ranges(rows)
        before=deepcopy(ranges)
        table,checks=evaluate_ranges(rows,ranges)
        self.assertEqual(ranges,before)
        for result in checks.values():
            self.assertTrue(result['periods']['2023-2024']['inside_better_mean_and_median'])
            self.assertFalse(result['periods']['2026_YTD']['inside_better_mean_and_median'])
            self.assertEqual(result['interval_hypothesis'],'НЕ ПОДТВЕРЖДЕНО')
        for check in CHECKS:
            count=sum(r['n'] for r in table if r['check']==check and r['period']=='2026_YTD' and r['symbol']=='ALL')
            self.assertEqual(count,120 if check=='COMMON_ATR' else 40)

    def test_outcomes_include_nonpositive_and_stop_touch_denominators(self):
        rows=observations(2023)[:4]
        for r,value,touch in zip(rows,[-1,0,2,4],[True,False,False,True]):
            r['horizon_R'],r['horizon_stop_touch']=value,touch
        result=summarize(rows)
        self.assertEqual(result['n'],4)
        self.assertEqual(result['mean_horizon_R'],1.25)
        self.assertEqual(result['median_horizon_R'],1)
        self.assertEqual(result['positive_share'],.5)
        self.assertEqual(result['stop_touch_share'],.5)

    def test_small_or_degenerate_calibration_is_not_verified(self):
        small=calibrate_ranges(observations(2023)[:3])
        self.assertTrue(all(r['base_status']=='НЕ ПРОВЕРЕНО' for r in small['ranges'].values()))
        rows=observations(2023)
        for r in rows:
            r['features']={metric:1.0 for _,metric,_ in CHECKS.values()}
        self.assertTrue(all(r['base_status']=='НЕ ПРОВЕРЕНО' for r in calibrate_ranges(rows)['ranges'].values()))

    def test_cutoff_and_locked_2025_rejected_before_features(self):
        validate_observations(observations(2023)+observations(2026))
        rows=observations(2023)
        rows[0]['cutoff']=rows[0]['signal_dt']
        with self.assertRaisesRegex(ValueError,'NON_CAUSAL'):
            validate_observations(rows)
        with self.assertRaisesRegex(ValueError,'LOCKED_2025'):
            validate_observations(observations(2025))
        rows=observations(2026)
        rows[0]['cutoff']='2024-12-31T18:00:00'
        with self.assertRaisesRegex(ValueError,'LOCKED_2025'):
            validate_observations(rows)

    def test_descriptive_bounds_never_grant_or_reject_market(self):
        original=apply_market_reference(inspect(make_sessions(),symbol='BR'),None)
        before=deepcopy(original)
        output=annotate_card(original,profile())
        self.assertEqual(original,before)
        self.assertEqual(output['strategies'],original['strategies'])
        self.assertEqual(output['reference_evidence'],original['reference_evidence'])
        self.assertFalse(output['affects_signals_or_risk'])
        self.assertFalse(output['typical_ranges']['symbol_in_reference'])
        self.assertTrue(all(s['suitability']=='НЕ ОЦЕНЕНО' for s in output['strategies'].values()))
        attempted_reference=apply_market_reference(original,profile())
        self.assertEqual(attempted_reference['reference_evidence']['reason'],'REFERENCE_SCHEMA_NOT_VALIDATED')

    def test_incomplete_card_remains_incomplete_and_future_calibration_hidden(self):
        card=apply_market_reference(inspect(make_sessions(19)),None)
        output=annotate_card(card,profile())
        self.assertTrue(all(s['suitability']=='НЕДОСТАТОЧНО ДАННЫХ' for s in output['strategies'].values()))
        self.assertEqual(output['typical_ranges']['values']['COMMON_ATR']['position'],'НЕИЗВЕСТНО')
        older=deepcopy(card)
        older['as_of_msk']='2024-12-31T18:00:00'
        hidden=annotate_card(older,profile())['typical_ranges']
        self.assertEqual(hidden,{'state':'CALIBRATION_NOT_YET_AVAILABLE'})


if __name__=='__main__':
    unittest.main()
