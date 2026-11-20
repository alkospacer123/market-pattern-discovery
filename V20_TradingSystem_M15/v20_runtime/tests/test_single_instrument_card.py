"""Final outcome-led card: causal availability and separate sample populations."""
from copy import deepcopy
import csv
from datetime import date, datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from V20_TradingSystem_M15.v20_runtime import market_epochs as epochs
from V20_TradingSystem_M15.v20_runtime.market_suitability_cli import format_text
from V20_TradingSystem_M15.v20_runtime.tests.test_market_epochs import card, profile
from V20_TradingSystem_M15.v20_runtime.tests.test_market_suitability import make_sessions, inspect
from V20_TradingSystem_M15.v20_runtime.market_verdict import apply_market_reference


def final_profile():
    ref=profile()
    ref['outcome_diagnosis']={'checks':{m:{'joint_SL_win_direction_consistent':False}
                                      for m in epochs.DIAGNOSTIC_METRICS}}
    return ref


def published_row(**changes):
    row=dict(record_type='RAW_SIGNAL',signal_bar_dt='2024-02-01 10:00:00',
        entry_dt='2024-02-01 10:15:00',exit_dt='',horizon_exit_dt='2024-02-05 10:00:00',
        horizon_status='OBSERVED_V1',stat_eligible='True',actual_path_status='OBSERVED_V1',
        strategy='SHALLOW_PULLBACK',instrument='USDRUBF',contract='USDRUBF',
        horizon_R='2',horizon_MFE_R='3',horizon_MAE_R='.5',horizon_stop_touch='False',
        net_C1_R='1.9',exit_reason='3')
    row.update(changes)
    return row


def read_rows(rows):
    with tempfile.TemporaryDirectory(prefix='v20_card_test_') as folder:
        path=Path(folder)/'published.csv'
        with path.open('w') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return epochs.diagnostic_rows(path)


class SingleInstrumentTests(unittest.TestCase):
    def test_locked_and_unused_years_filtered_before_numeric_outcomes(self):
        poison=dict(horizon_R='LOCKED',horizon_MFE_R='LOCKED',horizon_MAE_R='LOCKED')
        rows=[published_row(),published_row(signal_bar_dt='2025-02-01 10:00:00',**poison),
              published_row(signal_bar_dt='2026-02-01 10:00:00',**poison),
              published_row(horizon_exit_dt='2025-01-02 10:00:00',**poison),
              published_row(exit_dt='2025-01-02 10:00:00',**poison)]
        parsed,coverage=read_rows(rows)
        self.assertEqual(len(parsed),1)
        self.assertEqual(coverage['2023-2024/RAW_SIGNAL/locked_target'],2)

    def test_path_observability_and_accepted_trade_denominators(self):
        rows=[published_row(),published_row(horizon_status='UNKNOWN_INTRASESSION_GAP'),
              published_row(record_type='EXECUTED_TRADE',stat_eligible='False'),
              published_row(record_type='EXECUTED_TRADE',actual_path_status='UNKNOWN')]
        parsed,coverage=read_rows(rows)
        self.assertEqual(len(parsed),1)
        self.assertEqual(coverage['2023-2024/RAW_SIGNAL/published'],2)
        self.assertEqual(coverage['2023-2024/EXECUTED_TRADE/ineligible_or_unobserved_trade'],2)

    def test_outcome_available_only_when_full_horizon_has_closed(self):
        rows,_=read_rows([published_row(),published_row(horizon_exit_dt='2024-02-06 10:00:00')])
        rows[1]['stop_touch']=object()  # future outcome must not be consumed
        args=dict(contract='USDRUBF',start_day='2024-01-10')
        self.assertEqual(epochs.available_paths(rows,cutoff='2024-02-05 09:59:59',**args),[])
        available=epochs.available_paths(rows,cutoff='2024-02-05 10:00:00',**args)
        self.assertEqual(len(available),1)
        self.assertEqual(sum(not r['stop_touch'] for r in available),1)
        self.assertEqual(epochs.available_paths(rows,cutoff='2024-02-05 10:00:00',
            contract='OTHER',start_day='2024-01-10'),[])
        self.assertEqual(epochs.available_paths(rows,cutoff='2024-02-05 10:00:00',
            contract='USDRUBF',start_day='2024-02-02'),[])

    def test_three_accounts_same_instrument_are_not_deduplicated(self):
        rows,_=read_rows([published_row(record_type='EXECUTED_TRADE',strategy=s)
            for s in ('SHALLOW_PULLBACK','OBV_PRESSURE','INSIDE_DAY_RELEASE')])
        self.assertEqual(len(rows),3)
        self.assertEqual(epochs.path_summary(rows)['winners'],3)

    def test_signal_join_uses_previous_completed_snapshot_and_prior_closed_paths(self):
        rows,_=read_rows([published_row()])
        days=[date(2024,1,12)+timedelta(days=i) for i in range(21)]
        key=(epochs.EPOCHS[1],'USD')
        # A signal-day snapshot must not overwrite the previous day's features.
        values={m:.25 for m in epochs.FIVE+epochs.EXTRA}
        records={key:{days[-2]:dict(contract='USDRUBF',cutoff='2024-01-31T18:00:00',values=values),
                      days[-1]:dict(contract='USDRUBF',cutoff='2024-02-01T18:00:00',
                                    values={m:99 for m in values})}}
        with patch.object(epochs,'diagnostic_rows',return_value=(rows,{})):
            result=epochs.diagnose_outcomes(records,{key:days})
        example=result['examples']['USDRUBF']
        self.assertEqual(example['values']['continuation_rate'],.25)
        self.assertEqual(example['past_paths'],0)  # own outcome not yet observable
        self.assertIsNone(example['values']['past_v20_stop_survival'])
        records[key][days[-2]]['cutoff']='2024-02-01T18:00:00'
        with patch.object(epochs,'diagnostic_rows',return_value=(rows,{})):
            with self.assertRaisesRegex(ValueError,'NOT_BEFORE_DAY'):
                epochs.diagnose_outcomes(records,{key:days})

    def test_path_counts_do_not_become_trade_profit(self):
        rows,_=read_rows([published_row(horizon_R='-1',horizon_MFE_R='2',horizon_stop_touch='True'),
                          published_row(horizon_R='0',horizon_MFE_R='.5'),
                          published_row(horizon_R='3',horizon_MFE_R='4')])
        summary=epochs.path_summary(rows)
        self.assertEqual(summary['n'],3)
        self.assertEqual(summary['reached_1R'],2)
        self.assertEqual(summary['reached_2R'],2)
        self.assertEqual(summary['positive_horizon'],1)
        self.assertEqual(summary['gained_1R_then_nonpositive_horizon'],1)
        self.assertEqual(summary['stop_touch_share'],1/3)
        self.assertEqual(summary['winners'],0)  # raw movement is not C1 win

    def test_one_card_and_no_strategy_verdicts_in_operator_text(self):
        result=epochs.annotate_instrument(card(),final_profile())
        text=format_text(result)
        self.assertEqual(text.count('ОБЩИЙ ИСТОРИЧЕСКИЙ РЕЖИМ:'),1)
        self.assertNotIn('SHALLOW_PULLBACK',text)
        self.assertNotIn('OBV_PRESSURE',text)
        self.assertNotIn('INSIDE_DAY_RELEASE',text)
        self.assertIn('1589',text)
        self.assertIn('от–до',text)

    def test_overlapping_or_conflicting_ranges_cannot_manufacture_confidence(self):
        ref=final_profile()
        original=card()
        before=deepcopy(original)
        for newer in (False,True):
            if newer:
                for m in epochs.DIAGNOSTIC_METRICS:
                    ref['epochs'][epochs.EPOCHS[1]]['USD']['metrics'][m].update(p25=8,p75=9)
            result=epochs.annotate_instrument(original,ref)
            self.assertEqual(result['instrument_assessment']['status'],'НЕЙТРАЛЬНО')
            self.assertEqual(result['instrument_assessment']['verdict_metrics'],[])
            self.assertEqual(result['reference_evidence'],original['reference_evidence'])
            self.assertEqual(result['strategies'],original['strategies'])
        self.assertEqual(original,before)

    def test_one_weak_metric_does_not_exclude_instrument(self):
        ref=final_profile()
        original=card()
        original['strategies']['INSIDE_DAY_RELEASE']['diagnostics']['directional_efficiency']=None
        original['metrics']['compression']['completed_release_breakouts']=1
        result=epochs.annotate_instrument(original,ref)['instrument_assessment']
        self.assertEqual(result['status'],'НЕЙТРАЛЬНО')
        release=next(r for r in result['rows'] if r['metric']=='inside_release_continuation_rate')
        self.assertEqual(release['assessment'],'НЕДОСТАТОЧНО НАБЛЮДЕНИЙ')

    def test_missing_history_profile_or_comparability_is_insufficient(self):
        for original,ref in ((card('BR'),final_profile()),(card('GLDRUBF'),final_profile()),
                             (card(),None),(card(),profile()),
                             (apply_market_reference(inspect(make_sessions(19)),None),final_profile())):
            result=epochs.annotate_instrument(original,ref)
            self.assertEqual(result['instrument_assessment']['status'],'НЕДОСТАТОЧНО ДАННЫХ')
            if original['symbol']=='BR':
                row=result['instrument_assessment']['rows'][0]
                self.assertEqual(row['value'],.5)  # measurements survive absent transfer evidence
                self.assertIsNone(row['old'])
        original=card()
        original['as_of_msk']='2024-12-31T18:00:00'
        self.assertEqual(epochs.annotate_instrument(original,final_profile())['instrument_assessment']['status'],
                         'НЕДОСТАТОЧНО ДАННЫХ')


if __name__=='__main__':
    unittest.main()
