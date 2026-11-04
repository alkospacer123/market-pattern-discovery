"""Targeted epoch adapter/overlap tests; synthetic data, no market OOS."""
from copy import deepcopy
from datetime import datetime, timedelta
import io
import unittest
from V20_TradingSystem_M15.v20_runtime.market_suitability import M15Bar, METRIC_SCHEMA, evaluate_market_card
from V20_TradingSystem_M15.v20_runtime.market_epochs import (
    EPOCHS, FIVE, EXTRA, SCHEMA, series, snapshots, card_values, read_bars,
    unknown_gap, feature_similarity, overlap, annotate_epochs,
)
from V20_TradingSystem_M15.v20_runtime.market_verdict import apply_market_reference
from V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability import inspect, make_sessions


def bars(year,n=40):
    result=[]
    for day in range(n):
        start=datetime(year,1,1,10)+timedelta(days=day)
        for k in range(32):
            x=100+day*.3+k*.02
            result.append(M15Bar(start+timedelta(minutes=15*k),x,x+1,x-1,x+.5,10))
    return result


def distribution(low=0,high=1):
    return {'n':40,'p25':low,'p75':high,'median':(low+high)/2}


def profile():
    return dict(schema=SCHEMA,metric_schema=METRIC_SCHEMA,available_from_msk='2025-01-01T00:00:00',
        old_contract_families={},epochs={epoch:{family:{'metrics':{m:distribution() for m in FIVE+EXTRA}}
                                               for family in ('USD','INDEX','CNY')} for epoch in EPOCHS})


def card(symbol='USDRUBF'):
    result=apply_market_reference(inspect(make_sessions(),symbol=symbol),None)
    result['strategies']['INSIDE_DAY_RELEASE']['diagnostics'].update({m:.5 for m in FIVE+EXTRA})
    result['metrics']['breakouts']['return_inside_rate']=.5
    return result


class EpochTests(unittest.TestCase):
    def test_same_existing_feature_calculation_for_both_epochs(self):
        output=[]
        for year,epoch in ((2022,EPOCHS[0]),(2024,EPOCHS[1])):
            source=series(bars(year))
            days=sorted(source['sessions'])
            records,counts=snapshots({'TEST':source},[(d,'TEST') for d in days],epoch=epoch,family='USD')
            self.assertEqual(counts['snapshots'],21)
            last=records[days[-1]]
            window=[source['sessions'][d] for d in days[-20:]]
            direct=evaluate_market_card('TEST',window,as_of=window[-1].closed_at)
            self.assertEqual(last['values'],card_values(direct))
            output.append(last['values'])
        self.assertEqual(output[0],output[1])

    def test_price_and_volume_units_do_not_create_epoch_difference(self):
        original=series(bars(2024,20))
        scaled=series([M15Bar(b.open_time,b.open*100,b.high*100,b.low*100,b.close*100,b.volume*1000)
                       for b in bars(2024,20)])
        values=[]
        for source in (original,scaled):
            days=sorted(source['sessions'])
            result,_=snapshots({'TEST':source},[(d,'TEST') for d in days],epoch=EPOCHS[1],family='INDEX')
            values.append(result[days[-1]]['values'])
        for key in FIVE+EXTRA:
            if values[0][key] is not None:
                self.assertAlmostEqual(values[0][key],values[1][key],places=10)

    def test_roll_cannot_stitch_two_contracts(self):
        source=series(bars(2022))
        days=sorted(source['sessions'])
        decisions=[(d,'OLD' if i<20 else 'NEW') for i,d in enumerate(days)]
        records,_=snapshots({'OLD':source,'NEW':source},decisions,epoch=EPOCHS[0],family='USD')
        self.assertEqual(list(records),[days[19],days[39]])
        self.assertEqual(records[days[39]]['contract'],'NEW')

    def test_incomplete_day_remains_in_twenty_session_window(self):
        data=bars(2022)
        missing=data[15*32+4].open_time
        source=series([b for b in data if b.open_time!=missing])
        days=sorted(source['sessions'])
        records,counts=snapshots({'TEST':source},[(d,'TEST') for d in days],epoch=EPOCHS[0],family='USD')
        self.assertEqual(len(records),5)
        self.assertEqual(min(records),days[35])
        self.assertGreater(counts['INCOMPLETE_WINDOW'],0)

    def test_future_gap_does_not_change_completed_past_snapshot(self):
        original=bars(2022,21)
        prefix=series(original[:20*32])
        final=original[20*32-1]
        later=[M15Bar(final.open_time.replace(hour=19,minute=0),100,101,99,100,1)]
        full=series(original[:20*32]+later+original[20*32:])
        outputs=[]
        for source in (prefix,full):
            days=sorted(source['sessions'])
            records,_=snapshots({'TEST':source},[(d,'TEST') for d in days],epoch=EPOCHS[0],family='USD')
            outputs.append(records[day:=sorted(prefix['sessions'])[-1]])
        self.assertEqual(outputs[0],outputs[1])
        self.assertTrue(full['gaps'])
        self.assertFalse(unknown_gap(datetime(2022,1,1,13,45),datetime(2022,1,1,14,15)))

    def test_locked_year_is_discarded_before_numeric_parsing(self):
        stream=io.StringIO('Datetime;Open;High;Low;Close;Volume\n'
            '2024-01-01 10:00:00;100;101;99;100;1\n'
            '2025-01-01 10:00:00;LOCKED;LOCKED;LOCKED;LOCKED;LOCKED\n'
            '2026-01-01 10:00:00;UNUSED;UNUSED;UNUSED;UNUSED;UNUSED\n')
        self.assertEqual(len(read_bars(stream,years={2023,2024})),1)

    def test_overlap_and_conflict_do_not_force_epoch_label(self):
        self.assertEqual(feature_similarity(.5,distribution(),distribution()),'СМЕШАННЫЙ / ПЕРЕКРЫТИЕ')
        self.assertEqual(feature_similarity(2,distribution(),distribution()),'НЕРАЗЛИЧИМО / ВНЕ ОБОИХ IQR')
        self.assertEqual(overlap(distribution(),distribution())['intersection_over_union'],1)
        output=annotate_epochs(card(),profile())
        self.assertTrue(all(s['status']=='СМЕШАННЫЙ / НЕРАЗЛИЧИМО'
                            for s in output['historical_similarity']['strategies'].values()))
        ref=profile()
        ref['epochs'][EPOCHS[0]]['USD']['metrics']['directional_efficiency']=distribution(.4,.6)
        ref['epochs'][EPOCHS[1]]['USD']['metrics']['directional_efficiency']=distribution(.8,.9)
        ref['epochs'][EPOCHS[0]]['USD']['metrics']['continuation_rate']=distribution(.8,.9)
        ref['epochs'][EPOCHS[1]]['USD']['metrics']['continuation_rate']=distribution(.4,.6)
        self.assertEqual(annotate_epochs(card(),ref)['historical_similarity']['strategies']['SHALLOW_PULLBACK']['status'],
                         'СМЕШАННЫЙ / НЕРАЗЛИЧИМО')

    def test_unmatched_family_and_future_profile_cannot_grant_suitability(self):
        for symbol,label in (('BR','ПЕРЕНОС НЕ ПРОВЕРЕН'),('SILV','ПЕРЕНОС НЕ ПРОВЕРЕН'),
                             ('GLDRUBF','НЕДОСТАТОЧНО СОПОСТАВИМЫХ ДАННЫХ')):
            original=card(symbol)
            before=deepcopy(original)
            output=annotate_epochs(original,profile())
            self.assertEqual(output['historical_similarity']['status'],label)
            self.assertEqual(output['strategies'],original['strategies'])
            self.assertEqual(output['reference_evidence'],original['reference_evidence'])
            self.assertEqual(original,before)
            self.assertFalse(output['affects_signals_or_risk'])
        past=card()
        past['as_of_msk']='2024-12-31T18:00:00'
        self.assertEqual(annotate_epochs(past,profile())['historical_similarity'],{'status':'ПРОФИЛЬ ЕЩЁ НЕ ДОСТУПЕН'})


if __name__=='__main__':
    unittest.main()
