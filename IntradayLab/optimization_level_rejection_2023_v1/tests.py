"""Synthetic causality, exact Baseline preservation, bounded grid and selection."""
from copy import deepcopy
from dataclasses import replace
from datetime import date,timedelta
from decimal import Decimal as D
import json,tempfile,unittest
from pathlib import Path
from IntradayLab.tests.test_level_rejection import LevelRejectionTests,FIVE
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.models import Context
from IntradayLab.strategies.level_rejection_m5_optimization_v1 import LevelRejectionM5Optimization
from .contract import STUDY,grid,bounded_reads
from .aggregation import select,criteria,economics


class LRTests(LevelRejectionTests):
    def setUp(self):
        super().setUp();self.policy=json.loads((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text())
        self.strategy=LevelRejectionM5Optimization(self.cfg['parameters']);self.strategy.begin_day(self.symbol,self.day)

    def run_engine(self,rows):
        return Backtester(self.rules,daily_trade_deadline_clock='17:00').run(LevelRejectionM5Optimization(self.cfg['parameters']),
            self.symbol,rows,start=self.day,end_exclusive=self.day+timedelta(days=1))

    def v2(self,rows,p=None):
        return Backtester(self.rules,daily_trade_deadline_clock='17:00',data_gap_policy='DATA_GAP_SKIP_V2').run(
            LevelRejectionM5Optimization(p or self.cfg['parameters']),self.symbol,rows,start=self.day,end_exclusive=self.day+timedelta(days=1))

    def test_grid_unique_72_and_216_matrix(self):
        specs=grid(self.policy);self.assertEqual(len(specs),72)
        self.assertEqual(len({tuple(str(s[k]) for k in self.policy['grid_order']) for s in specs}),72)
        self.assertEqual({s['max_hold_calendar_minutes'] for s in specs},{60,120})

    def test_all_nonvaried_parameters_fixed(self):
        for s in grid(self.policy):
            p={k:v for k,v in s.items() if k!='configuration_id'};LevelRejectionM5Optimization(p)
            for k,v in self.cfg['parameters'].items():
                if k not in self.policy['grid']:self.assertEqual(p[k],v)
        p=dict(self.cfg['parameters'],level_lookback_completed_m5=7)
        with self.assertRaisesRegex(ValueError,'FIXED'):LevelRejectionM5Optimization(p)
        p=dict(self.cfg['parameters'],planned_net_to_net_R='11')
        with self.assertRaisesRegex(ValueError,'GRID'):LevelRejectionM5Optimization(p)

    def test_tighter_completed_close_and_future_open_coupling(self):
        p=dict(self.cfg['parameters'],min_close_reentry_ticks=2)
        self.strategy=LevelRejectionM5Optimization(p);self.strategy.begin_day(self.symbol,self.day);self.seed()
        self.assertEqual(self.observe('10:30',self.rejection(c='100.01')),[])
        self.setUp();rows=self.rows();rows[self.at('10:30')]=self.rejection(c='100.02')
        rows[self.at('10:40')]=self.bar('10:40',o='100.01',c='100.01')
        r=self.v2(rows,p);self.assertEqual(r.trades,[])
        self.assertIn('OPEN_RECLAIM_NOT_PERSISTENT',[s['reason'] for s in r.signals])

    def test_structural_buffer_and_holding_variations(self):
        p=dict(self.cfg['parameters'],stop_beyond_extreme_ticks=2,max_hold_calendar_minutes=60)
        r=self.v2(self.rows(),p);t=r.trades[0]
        self.assertEqual(t['stop'],D('99.96'));self.assertEqual(t['exit_at'],self.at('11:40'))

    def test_full_net_all_nine_targets_and_both_sides(self):
        for side in (1,-1):
            for target in range(2,11):
                r=self.v2(self.rows(side=side),dict(self.cfg['parameters'],planned_net_to_net_R=str(target)))
                t=r.trades[0];s=t['risk'];c=2*t['entry_tick']
                self.assertEqual(t['d_full'],D(target)*(s+c)+c)
                self.assertEqual(t['planned_net_to_net_R'],D(target))

    def test_v2_missing_entry_skip_no_pnl(self):
        rows=self.rows();del rows[self.at('10:40')];r=self.v2(rows)
        self.assertEqual(len(r.data_gap_skips),1);self.assertEqual(r.trades,[]);self.assertEqual(r.data_quality_exclusions,[])
        self.assertFalse(r.days[0]['remainder_of_day_blocked'])
        self.assertNotIn('net_R_c1',r.data_gap_skips[0])

    def test_v2_missing_exposure_excludes_and_blocks(self):
        rows=self.rows();del rows[self.at('10:45')];r=self.v2(rows)
        self.assertEqual(r.trades,[]);self.assertEqual(len(r.data_quality_exclusions),1)
        self.assertTrue(r.days[0]['remainder_of_day_blocked'])
        q=r.data_quality_exclusions[0]
        for k in ('gross','net_c1','net_R_c1','cost_c1'):self.assertNotIn(k,q)
        self.assertIsNone(q['exit_price'])

    def test_baseline_synthetic_legacy_exact_all_fields(self):
        from IntradayLab.strategies.level_rejection import LevelRejection
        for side in (1,-1):
            rows=self.rows(side=side)
            old=Backtester(self.rules,daily_trade_deadline_clock='17:00').run(LevelRejection(self.cfg['parameters']),
                self.symbol,rows,start=self.day,end_exclusive=self.day+timedelta(days=1))
            self.assertEqual(old,self.run_engine(rows))

    def test_original_replay_serialization_and_common_v2_comparison(self):
        from unittest.mock import patch
        from . import baseline_replay
        from IntradayLab.core.reports import csv_write
        from IntradayLab.strategies.level_rejection import LevelRejection
        rows=self.rows();ss,tt,dd=Backtester(self.rules,daily_trade_deadline_clock='17:00').run(LevelRejection(self.cfg['parameters']),self.symbol,rows,start=date(2023,1,1),end_exclusive=date(2024,1,1));v2=self.v2(rows)
        with tempfile.TemporaryDirectory(dir=STUDY.parent/'work') as directory:
            root=Path(directory);lab=root/'IntradayLab';(lab/'config').mkdir(parents=True)
            (lab/'config/level_rejection_2023_m5_v1.json').write_text(json.dumps(self.cfg))
            archive=lab/'results/level_rejection_2023_m5_v1';archive.mkdir(parents=True)
            for name,rs in [('signals',ss),('trades',tt),('days',dd)]:csv_write(archive/(name+'.csv'),rs)
            output=lab/'work/test';folder=output/'evaluations'/self.policy['historical_control_id']/self.symbol;folder.mkdir(parents=True)
            csv_write(folder/'trades.csv',v2.trades);csv_write(folder/'data_gap_skips.csv',[]);csv_write(folder/'data_quality_exclusions.csv',[])
            policy=dict(self.policy,instruments=[self.symbol],instrument_admission={self.symbol:dict(CLOSED=1)})
            with patch.object(baseline_replay,'ROOT',root):
                receipt=baseline_replay.run(Path('/no/source'),output,policy,'0'*40,loaded=({self.symbol:rows},{},[]))
            self.assertEqual(receipt['status'],'PASS');self.assertEqual(receipt['instruments'][self.symbol]['common_CLOSED'],1)

    def test_source_guard_denies_future_byte_and_other_instrument(self):
        with tempfile.TemporaryDirectory(dir=STUDY.parent/'work') as d:
            root=Path(d);(root/'sample.csv').write_bytes(b'2023\n2024\n')
            p={'inputs':{'USDRUBF':dict(path='sample.csv',prefix_bytes=5,blob='synthetic')}}
            with bounded_reads(root,p) as receipts:
                with (root/'sample.csv').open('rb',buffering=0) as f:
                    self.assertEqual(f.read(5),b'2023\n')
                    with self.assertRaisesRegex(ValueError,'FUTURE'):f.read(1)
                with self.assertRaisesRegex(ValueError,'FORBIDDEN'):(root/'other.csv').open('rb',buffering=0)
            self.assertEqual(receipts[0]['bytes_read'],5)

    def test_neighbor_topology_and_fixed_selection_thresholds(self):
        specs=grid(self.policy);rs=[]
        for spec in specs:
            rs.append(dict(spec,instrument='USDRUBF',CLOSED=100,entry_days=40,entry_months=6,
                PF_R=D(2),PF_price=D(2),expectancy_R=D('.1'),positive_exit_months=9,
                conditional_closed_only_DD_R=D(20),largest_winner_share_R=D('.25'),largest_positive_month_share_R=D('.5')))
        for r in rs:r.update({f'pass_{k}':v for k,v in criteria(r,self.policy['selection']).items()})
        edges,selection=select(rs,self.policy)
        self.assertEqual(selection['instruments']['USDRUBF']['full_criteria_pass'],72)
        self.assertEqual({r['positive_neighbor_count'] for r in rs},{4,5})
        for e in edges:
            x=next(r for r in rs if r['configuration_id']==e['configuration_id']);y=next(r for r in rs if r['configuration_id']==e['neighbor_id'])
            self.assertEqual(sum(x[k]!=y[k] for k in self.policy['grid_order']),1)
        r=deepcopy(rs[0]);r['CLOSED']=99;self.assertFalse(criteria(r,self.policy['selection'])['sample'])
        r=deepcopy(rs[0]);r['PF_price']=D('1.999');self.assertFalse(criteria(r,self.policy['selection'])['PF_price'])


if __name__=='__main__':unittest.main()
