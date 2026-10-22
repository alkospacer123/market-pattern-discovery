"""Causal rolling RAW_SIGNAL windows; no trading, prices only in external fixtures."""
from copy import deepcopy
import csv
from datetime import datetime, timedelta
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from V20_TradingSystem_M15.v20_runtime import market_rolling_raw as raw
from V20_TradingSystem_M15.v20_runtime.market_suitability_cli import main,format_raw_text
from V20_TradingSystem_M15.v20_runtime.tests.test_single_instrument_card import published_row


def paths(n, *, strategy=raw.STRATEGIES[0],instrument='TEST',start=datetime(2018,1,1,10),step=3,values=None):
    result=[]
    for i in range(n):
        signal=start+timedelta(days=i*step)
        result.append(dict(strategy=strategy,instrument=instrument,contract=instrument,
            signal=signal,entry=signal+timedelta(minutes=15),available=signal+timedelta(days=2),
            raw_R=values[i] if values is not None else float(i),stop_touch=i%2==0))
    return result


def at(rows,as_of=None,**kwargs):
    return raw.rolling_at(rows,strategy=kwargs.get('strategy',raw.STRATEGIES[0]),
        instrument=kwargs.get('instrument','TEST'),as_of=as_of or max(r['available'] for r in rows))


def parse(rows,**kwargs):
    with tempfile.TemporaryDirectory(prefix='v20_raw_test_') as folder:
        path=Path(folder)/'raw.csv'
        with path.open('w') as stream:
            w=csv.DictWriter(stream,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
        return raw.load_paths(path,expected_sha=None,**kwargs)


class RollingRawTests(unittest.TestCase):
    def test_v20_2025_2026_allowed_and_execution_rows_excluded(self):
        rows=[]
        for year in (2025,2026):
            rows.append(published_row(signal_bar_dt=f'{year}-02-01 10:00:00',
                entry_dt=f'{year}-02-01 10:15:00',horizon_exit_dt=f'{year}-02-03 10:00:00'))
        rows.append(published_row(record_type='EXECUTED_TRADE',horizon_R='NOT_A_RAW_VALUE'))
        parsed,coverage=parse(rows)
        self.assertEqual([r['signal'].year for r in parsed],[2025,2026])
        self.assertEqual(sum(n for k,n in coverage.items() if k.endswith('/raw')),2)

    def test_unknown_horizon_excluded_not_zero(self):
        parsed,coverage=parse([published_row(),published_row(signal_bar_dt='2024-02-02 10:00:00',
            horizon_status='UNKNOWN_INTRASESSION_GAP',horizon_R='UNKNOWN')])
        self.assertEqual(len(parsed),1)
        self.assertEqual(parsed[0]['raw_R'],2)
        self.assertEqual(sum(n for k,n in coverage.items() if k.endswith('/UNKNOWN_INTRASESSION_GAP')),1)

    def test_duplicates_and_competing_selected_contracts_rejected(self):
        with self.assertRaisesRegex(ValueError,'DUPLICATE_RAW'):
            parse([published_row(),published_row(contract='OTHER')])
        parsed,_=parse([published_row(strategy=s) for s in raw.STRATEGIES])
        self.assertEqual(len(parsed),3)  # independent robots may share instrument/time

    def test_horizon_availability_before_outcome_values(self):
        data,_=parse([published_row(),published_row(signal_bar_dt='2024-02-02 10:00:00',
            entry_dt='2024-02-02 10:15:00',horizon_exit_dt='2024-02-06 10:00:00',horizon_R='FUTURE')],
            as_of=datetime(2024,2,5,10))
        self.assertEqual(len(data),1)
        rows=paths(41)
        cutoff=rows[39]['available']
        expected=at(rows[:40],cutoff)
        rows[40]['raw_R']=object()  # future result cannot be consumed
        self.assertEqual(at(rows,cutoff),expected)
        just_before=cutoff-timedelta(seconds=1)
        self.assertEqual(at(rows,just_before)['total_completed'],39)
        self.assertIsNone(at(rows,just_before)['delta_raw_R'])
        self.assertEqual(at(rows,cutoff)['total_completed'],40)

    def test_disjoint_latest_twenty_and_previous_twenty(self):
        rows=paths(60,values=[100]*20+[1]*20+[3]*20)
        state=at(rows)
        self.assertEqual(state['current']['mean'],3)
        self.assertEqual(state['previous']['mean'],1)
        self.assertEqual(state['delta_raw_R'],2)
        self.assertEqual(state['current']['first_signal'],rows[40]['signal'].isoformat())
        self.assertEqual(state['previous']['last_signal'],rows[39]['signal'].isoformat())

    def test_twenty_forty_and_preliminary_count_semantics(self):
        for n in (0,9,10,19,20,39,40):
            rows=paths(n)
            state=at(rows,datetime(2018,5,1))
            self.assertEqual(state['current']['n'],min(n,20))
            self.assertEqual(state['previous']['n'],max(0,n-20))
            if n<40:
                self.assertIsNone(state['previous']['mean'])
                self.assertIsNone(state['delta_raw_R'])
                self.assertEqual(state['trend'],'НЕДОСТАТОЧНО ДАННЫХ')

    def test_simultaneous_horizons_are_processed_atomically(self):
        rows=paths(40,start=datetime(2019,1,1,10),step=0)
        for i,r in enumerate(rows): r['signal']+=timedelta(minutes=15*i)
        states=raw.timeline(rows)
        self.assertEqual(len(states),1)
        self.assertEqual(states[0]['total_completed'],40)
        self.assertIsNotNone(states[0]['delta_raw_R'])

    def test_instruments_strategies_and_contract_provenance(self):
        rows=paths(40,instrument='Si',values=[1]*20+[2]*20)
        for i,r in enumerate(rows): r['contract']='Si-3.18' if i<20 else 'Si-6.18'
        other=paths(40,instrument='USDRUBF',values=[999]*40)+paths(40,instrument='Si',strategy=raw.STRATEGIES[1],values=[888]*40)
        state=at(rows+other,instrument='Si')
        self.assertEqual(state['current']['mean'],2)
        self.assertEqual(state['current']['contracts'],['Si-6.18'])
        self.assertEqual(state['previous']['contracts'],['Si-3.18'])

    def test_inside_long_window_and_clock_staleness(self):
        sparse=paths(40,step=30,strategy=raw.STRATEGIES[2])
        state=at(sparse,strategy=raw.STRATEGIES[2])
        self.assertIsNotNone(state['delta_raw_R'])  # display it, do not grant a trend
        self.assertEqual(state['trend'],'НЕДОСТАТОЧНО ДАННЫХ')
        self.assertIn('CURRENT_WINDOW_OVER_365_DAYS',state['reasons'])
        dense=paths(40)
        last=dense[-1]['available']
        self.assertNotEqual(at(dense,last+timedelta(days=90))['trend'],'НЕДОСТАТОЧНО ДАННЫХ')
        self.assertIn('LAST_HORIZON_OVER_90_DAYS_OLD',at(dense,last+timedelta(days=91))['reasons'])
        later=paths(1,start=last+timedelta(days=200))
        states=raw.timeline(dense+later)
        expired=[s for s in states if s['event_kind']=='STALE_CLOCK']
        self.assertEqual(expired[0]['as_of'],(last+timedelta(days=91)).isoformat())

    def test_2019_unaffected_by_future_outcomes_or_late_reference(self):
        old=paths(40,start=datetime(2018,10,1,10),values=[3]*20+[1]*20)
        future=paths(40,start=datetime(2025,1,1,10),values=[999]*40)
        cutoff=old[-1]['available']
        reference=dict(reference_available_from_msk='2026-10-22T00:00:00',reference_levels={
            s:dict(minimum_reference_R=999,recommended_reference_R=1000) for s in raw.STRATEGIES})
        card=raw.instrument_card(old+future,'TEST',cutoff,profile=reference)
        self.assertEqual(card['rows'][0]['delta_raw_R'],-2)
        self.assertIsNone(card['rows'][0]['minimum_reference_R'])
        before=at(old,cutoff)
        for r in future: r['raw_R']=-999
        self.assertEqual(at(old+future,cutoff),before)
        prefix=[s for s in raw.timeline(old+future) if raw.stamp(s['as_of'])<=cutoff]
        self.assertEqual(prefix,raw.timeline(old))

    def test_outlier_sensitivity_is_descriptive_and_does_not_replace_mean(self):
        rows=paths(40,values=[1]*20+[-1]*19+[100])
        card=raw.instrument_card(rows,'TEST',rows[-1]['available'])
        state=card['rows'][0]
        self.assertEqual(state['current']['mean'],4.05)
        self.assertEqual(state['current']['without_1'],-1)
        self.assertEqual(state['trend'],'НАБЛЮДАЕТСЯ УЛУЧШЕНИЕ')
        self.assertIn('ЧУВСТВИТЕЛЬНО К ВЫБРОСАМ',format_raw_text(card))

    def test_future_twenty_evaluate_warning_only_after_their_availability(self):
        rows=paths(40,values=[3]*20+[1]*20)
        warnings=raw.warning_episodes(raw.timeline(rows),rows)
        self.assertEqual(warnings[0]['result'],'UNRESOLVED')
        self.assertIsNone(warnings[0]['evaluation_available_at'])
        more=paths(20,start=rows[-1]['signal']+timedelta(days=3),values=[4]*20)
        updated=raw.warning_episodes(raw.timeline(rows+more),rows+more)
        self.assertEqual(updated[0]['start'],warnings[0]['start'])
        self.assertEqual(updated[0]['result'],'TEMPORARY_FULL_REBOUND')
        self.assertEqual(updated[0]['evaluation_available_at'],more[-1]['available'].isoformat())

    def test_actual_source_counts_years_and_period_means(self):
        rows,coverage=raw.load_paths()
        self.assertEqual(len(rows),4431)
        self.assertEqual(sum(n for k,n in coverage.items() if k.endswith('/raw')),4986)
        self.assertEqual({r['signal'].year for r in rows},set(range(2018,2027)))
        levels=raw.reference_levels(rows,raw.timeline(rows))
        for strategy,low,high in zip(raw.STRATEGIES,[.406162376937,.226466247747,.204807317998],
                                    [.952612257072,.695266809292,.733492242891]):
            self.assertAlmostEqual(levels[strategy]['minimum_reference_R'],low,places=11)
            self.assertAlmostEqual(levels[strategy]['recommended_reference_R'],high,places=11)
            self.assertIsNone(levels[strategy]['validated_minimum_R'])

    def test_atr_uses_completed_bars_and_existing_wilder_formula(self):
        with tempfile.TemporaryDirectory(prefix='v20_raw_atr_') as folder:
            base=Path(folder); (base/'USDRUBF').mkdir(); p=base/'USDRUBF/USDRUBF_M15.csv'
            lines=['Datetime;Open;High;Low;Close;Volume']
            start=datetime(2025,1,2,10)
            for i in range(14):
                lines.append(f'{start+i*raw.STEP};100;101;99;100;10')
            lines.append(f'{start+14*raw.STEP};FUTURE;FUTURE;FUTURE;FUTURE;FUTURE')
            p.write_text('\n'.join(lines)+'\n')
            with patch.object(raw,'sha',return_value=raw.SOURCE_SHA256['USDRUBF']):
                result=raw.atr_reference(base,'USDRUBF',start+14*raw.STEP)
            self.assertAlmostEqual(result['atr14_pct_close'],.02)
            self.assertEqual(result['data_through'],(start+14*raw.STEP).isoformat())

    def test_unknown_instrument_and_cli_readonly_three_rows(self):
        rows=paths(40)
        empty=raw.instrument_card(rows,'BR',datetime(2026,9,15))
        self.assertEqual(len(empty['rows']),3)
        self.assertTrue(all(s['current']['n']==0 for s in empty['rows']))
        self.assertFalse(empty['affects_signals_or_risk'])
        self.assertFalse(empty['live_authorized'])
        output=io.StringIO()
        with redirect_stdout(output):
            rc=main(['--symbol','BR','--as-of','2026-10-22T17:00:00','--format','json'])
        self.assertEqual(rc,0)
        result=json.loads(output.getvalue())
        self.assertEqual(result['schema'],'v20.confirmed_current_regime.readonly.v1')
        self.assertEqual(result['unique_completed_events'],0)
        self.assertEqual(result['historical_observation'],'STALE_OR_MISSING_COMPLETED_OUTCOMES')
        self.assertFalse(result['prediction_validated'])
        self.assertEqual(result['live_current_status'],'LIVE_FEED_NOT_CONNECTED')
        self.assertFalse(result['trading_gate'])
        previous=io.StringIO()
        with redirect_stdout(previous):
            self.assertEqual(main(['--symbol','BR','--raw-diagnostics',
                                   '--as-of','2026-10-22T17:00:00','--format','json']),0)
        self.assertEqual(json.loads(previous.getvalue())['schema'],'v20.instrument_regime.readonly.v1')


if __name__=='__main__':
    unittest.main()
