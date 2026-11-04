"""Targeted extension/monitoring checks, not new tests of frozen strategies."""
import ast
from datetime import datetime,timedelta
import json
import unittest

from ..market_monitoring import (assess,economic_status,monitoring_card,load_data,INSUF,NORMAL,DIAG,WATCH,STALE)
from ..history_extension import adapted_function,RUNNER
from ..calendar_review import statistics
from ..regime_monthly_comparison import ROOT,FOLDER,read_csv,dt,digest
from ..suitability_research import MODES,trade_row


def trade(t,value=1):
    return dict(strategy=MODES[0],instrument='Si',contract='Si-6.15',entry=t-timedelta(hours=1),
        signal=t-timedelta(hours=1,minutes=15),available=t,exit=t,net=value,gross=value+.01,
        stop=value<0,reason=1 if value<0 else 3,session_span=1,path=None)


class MonitoringUnitTests(unittest.TestCase):
    def test_status_rules_no_parameter_fit(self):
        def w(v,n=True):return dict(net_R=v,sufficient=n)
        self.assertEqual(economic_status(w(1),w(2)),NORMAL)
        self.assertEqual(economic_status(w(-1),w(2)),WATCH)
        self.assertEqual(economic_status(w(-1),w(-2)),DIAG)
        self.assertEqual(economic_status(w(2,False),w(2)),INSUF)

    def test_future_trade_is_not_used(self):
        t=datetime(2015,7,1)
        class Poison:
            def __add__(self,other):raise AssertionError('FUTURE NET ACCESSED')
            __radd__=__add__
        rows=[trade(t-timedelta(days=i),1) for i in range(1,31)]
        a=assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),t)
        rows.append(dict(trade(t+timedelta(days=1)),net=Poison()))
        self.assertEqual(a,assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),t))

    def test_raw_future_horizon_not_parsed(self):
        t=datetime(2015,7,1);r=dict(strategy=MODES[0],signal=t-timedelta(days=1),decision=t-timedelta(days=1),
            outcome=dict(available='2015-07-02',mfe_low='POISON',mfe_high='POISON'))
        card=assess([], [r],datetime(2012,1,1),datetime(2022,1,1),t)
        self.assertEqual(card['w3']['structure']['raw_observed'],0)

    def test_midmonth_uses_completed_months(self):
        rows=[trade(datetime(2015,7,3),-10)]
        c=assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),datetime(2015,7,15))
        self.assertEqual(c['w3']['n'],0);self.assertEqual(c['current_month']['net_R'],-10)

    def test_bounds_right_closed(self):
        t=datetime(2015,7,1)
        rows=[trade(datetime(2015,4,1),100),trade(t,2)]
        c=assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),t)
        self.assertEqual(c['w3']['net_R'],2)

    def test_inside_small_sample_insufficient(self):
        t=datetime(2025,7,1)
        c=assess([trade(t-timedelta(days=i),20) for i in range(1,10)],[],datetime(2023,1,1),t,t)
        self.assertEqual(c['status'],INSUF)

    def test_recovery_not_sticky_exclusion(self):
        t=datetime(2015,7,1);rows=[trade(t-timedelta(days=i),-1) for i in range(1,31)]
        self.assertEqual(assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),t)['status'],DIAG)
        rows += [trade(t+timedelta(days=i),5) for i in range(1,31)]
        self.assertEqual(assess(rows,[],datetime(2012,1,1),datetime(2022,1,1),datetime(2015,10,1))['status'],NORMAL)

    def test_stale_archive_no_live(self):
        c=monitoring_card({}, {'USDRUBF':(datetime(2023,1,1),datetime(2026,1,1))},[],[],datetime(2026,10,23))
        self.assertFalse(c['feed_connected']);self.assertFalse(c['automatic_actions']);self.assertEqual(c['status'],STALE)

    def test_accounts_not_cash_portfolio(self):
        t=datetime(2015,7,1);a=trade(t);b=dict(a,strategy=MODES[1])
        self.assertIsNone(statistics([a,b])['DD_closed_R'])


class ArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.groups,cls.bounds,cls.raw,cls.censored,_=load_data()
        cls.audit=json.loads((FOLDER/'V20_2012_2022_SOURCE_AUDIT.json').read_text())

    def test_source_overlap_and_quarantine(self):
        self.assertEqual(self.audit['overlap_files'],40)
        self.assertTrue(all(r['parity']=='PASS EXACT RECORDS' for r in self.audit['overlap_replay']))
        self.assertEqual(self.audit['bars'],299998);self.assertEqual(self.audit['validated_bars'],299996)
        self.assertEqual(len(self.audit['quarantined']),2)
        self.assertGreater(self.audit['grid_failures'],0)
        self.assertEqual(len(self.audit['early_open_positions']),1)
        self.assertTrue(self.audit['full_early_replay'].startswith('FAIL_PARTIAL'))
        r=self.audit['early_open_positions'][0]
        self.assertEqual(r['contract'],'Si-12.14')
        card=assess([],[],datetime(2012,1,1),datetime(2022,1,1),datetime(2015,7,1),
            [dict(entry=dt(r['entry_dt']),available=datetime.max,unknown_after=dt(r['unknown_after']),scope_end=dt(r['scope_end']))])
        self.assertEqual(card['unresolved_model_positions'],1)
        self.assertIn('заблокирован',card['explanation'])

    def test_frozen_sources_unchanged(self):
        for rel,h in self.audit['frozen_hashes'].items():self.assertEqual(digest(ROOT/rel),h,rel)
        self.assertEqual(digest(RUNNER),self.audit['runner_sha256'])

    def test_date_adaptation_only(self):
        from ..suitability_replay import module
        qd=module(ROOT/'V20-03/comparison/quote_diagnostics.py');env=qd.source_environment(ROOT.parent/'unused')
        a=qd.fn(RUNNER,'replay',env);b=adapted_function('replay',env)
        self.assertEqual(a.__code__.co_code,b.__code__.co_code)
        self.assertEqual(a.__code__.co_consts,b.__code__.co_consts)
        c=adapted_function('replay',env,start_year=2012)
        self.assertEqual(b.__code__.co_code,c.__code__.co_code)
        changes=[(x,y) for x,y in zip(b.__code__.co_consts,c.__code__.co_consts) if x!=y]
        self.assertEqual(changes,[(2018,2012)])

    def test_all_replay_C1_nextopen_ATR_limits(self):
        entries=list(read_csv(FOLDER/'V20_2012_2026_ENTRIES.csv'));counts={};used=set()
        closed=list(read_csv(FOLDER/'V20_2012_2022_REPLAY_TRADES.csv'))
        censored=list(read_csv(FOLDER/'V20_2012_2026_CENSORED_TRADES.csv'))
        self.assertEqual(len(entries),len(closed)+len(censored)+len(self.audit['early_open_positions']))
        for r in entries:
            self.assertEqual(dt(r['entry_dt'])-dt(r['signal_bar_dt']),timedelta(minutes=15))
            self.assertGreaterEqual(float(r['risk'])+1e-8,2*float(r['atr_at_signal']))
            self.assertEqual(r['contract'],r['chosen_contract'])
            key=r['account'],r['entry_session'];counts[key]=counts.get(key,0)+1
            unique=key+(r['family'],);self.assertNotIn(unique,used);used.add(unique)
        self.assertLessEqual(max(counts.values()),2)
        for r in read_csv(FOLDER/'V20_2012_2022_REPLAY_TRADES.csv'):
            gross=int(r['side'])*(float(r['exit'])-float(r['entry']))/float(r['risk'])
            cost=(float(r['tick_entry'])+float(r['tick_exit']))/float(r['risk'])
            self.assertAlmostEqual(float(r['net_C1_R']),gross-cost,places=7)
            self.assertIn(int(r['exit_reason']),(1,2,3,4));self.assertLessEqual(int(r['session_span']),3)

    def test_roll_completed_prior_session_and_monotonic(self):
        from ..suitability_replay import module
        env=module(ROOT/'V20-03/comparison/quote_diagnostics.py').source_environment(ROOT.parent/'unused')
        last={}
        for r in read_csv(FOLDER/'V20_2012_2026_ROLL_DECISIONS.csv'):
            if not r['chosen_contract']:continue
            self.assertLessEqual(dt(r['proof_known_after']),dt(r['decision_time']))
            self.assertLess(dt(r['previous_observed_session']),dt(r['day']))
            self.assertLess(dt(r['day']),env['cutoff'](r['chosen_contract']))
            expiry=env['maturity'](r['chosen_contract']);self.assertGreaterEqual(expiry,last.get(r['family'],expiry));last[r['family']]=expiry

    def test_monthly_yearly_partition(self):
        monthly=list(read_csv(FOLDER/'V20_2012_2026_MONTHLY.csv'))
        for a in read_csv(FOLDER/'V20_2012_2026_ANNUAL.csv'):
            q=[r for r in monthly if r['strategy']==a['strategy'] and r['instrument']==a['instrument'] and r['period'][:4]==a['year']]
            self.assertEqual(sum(int(r['n']) for r in q),int(a['n']))
            self.assertAlmostEqual(sum(float(r['net_R']) for r in q),float(a['net_R']),places=6)

    def test_snapshots_prefix_invariance(self):
        snaps=json.loads((FOLDER/'V20_2012_2026_CARD_SNAPSHOTS.json').read_text())
        for snap in snaps:
            t=dt(snap['card']['as_of_msk'])
            for r in snap['card']['rows']:
                key=r['strategy'],r['instrument'];source=self.groups[key];paths=[x for x in self.raw if (x['strategy'],x['instrument'])==key]
                a=assess(source,paths,*self.bounds[key[1]],t,[c for c in self.censored if (c['strategy'],c['instrument'])==key and c['entry']<=t])
                prefix=[x for x in source if x['available']<=t]
                b=assess(prefix,paths,*self.bounds[key[1]],t,[c for c in self.censored if (c['strategy'],c['instrument'])==key and c['entry']<=t])
                self.assertEqual(a,b);self.assertEqual(a['status'],r['status'])
                self.assertLessEqual(dt(r['source_through']),t)

    def test_forward_never_in_card(self):
        card=monitoring_card(self.groups,self.bounds,self.raw,self.censored,datetime(2019,7,1))
        text=json.dumps(card,default=str)
        self.assertNotIn('next_quarter',text);self.assertNotIn('retrospective_evaluation',text)
        self.assertFalse(card['validated_indicator'])


if __name__=='__main__':unittest.main()
