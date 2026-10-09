"""Synthetic causal/accounting tests; no market data, future prefixes or tuning."""
import copy
from datetime import datetime, timedelta
from decimal import Decimal as D
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS=Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
from session_mtf import Bar, bounded_lines
from m5_baseline import (Features, Replay, available, allowed, next_slot, protection,
                        level_exit, fill_units, metrics, tick, windows, FIVE)
from run_m5_baseline import read_2023, load_manifest, encoded, write_text, DEST, LAB, group_metrics

P=load_manifest()[0]['parameters']
T=datetime(2023,1,3,10)


def bar(t=T, o='100', h='100.2', l='99.8', c='100',v='10',symbol='USDRUBF', delivery=None):
    return Bar(t,*map(D,(o,h,l,c,v)),available_at=delivery,symbol=symbol)


def bars(end=100):
    return [bar(T+i*FIVE) for i in range(end)]


class Scripted(Replay):
    """One pre-known synthetic signal, isolates execution from feature shape."""
    def __init__(self, at=T+11*FIVE, **kwargs):
        super().__init__('USDRUBF','MOMENTUM',P,**kwargs)
        self.at=at
    def decision(self,b,now,f):
        if b.timestamp==self.at:
            super().decision(b,now,{'atr':D(1),'vwap':D(99),'range_high':D(99),
                                   'range_low':D(98),'MOMENTUM':1})


class PhysicalAndScope(unittest.TestCase):
    def test_manifest_frozen_exact_eight(self):
        m,digest=load_manifest()
        self.assertEqual(len(m['run_matrix']),8)
        self.assertEqual(len({(r['strategy'],r['instrument']) for r in m['run_matrix']}),8)
        self.assertEqual(digest,hashlib.sha256((LAB/'config/stage2_m5_baseline_v1.json').read_bytes()).hexdigest())

    def test_bounded_reader_never_touches_2024_or_2025_sentinel(self):
        class Guard(io.RawIOBase):
            def __init__(self,prefix): self.prefix,self.at=prefix,0
            def read(self,n=-1):
                if n<0 or self.at+n>len(self.prefix):
                    raise AssertionError('Protected future byte requested')
                out=self.prefix[self.at:self.at+n];self.at+=n;return out
        prefix=b'header\n2023 A\n2023 B\n'
        g=Guard(prefix)
        self.assertEqual(b''.join(bounded_lines(g,3)),prefix)
        self.assertEqual(g.at,len(prefix))

    def test_2023_loader_only_published_line_budget(self):
        parent=LAB/'work';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            path=Path(temp)/'synthetic.csv'
            header=b'Ticker;Datetime;Open;High;Low;Close;Volume\n'
            line=b'USDRUBF;2023-01-03 10:00:00;100;101;99;100;10\n'
            protected=b'USDRUBF;2024-01-03 10:00:00;FORBIDDEN;FORBIDDEN;FORBIDDEN;FORBIDDEN;FORBIDDEN\n'+b'2025 TRUE OOS\n'
            path.write_bytes(header+line+protected)
            budget=len(header+line)
            original_open=Path.open
            class Guard(io.FileIO):
                def read(self,n=-1):
                    if n<0 or self.tell()+n>budget: raise AssertionError('Future byte read')
                    return super().read(n)
            def opened(p,*args,**kwargs):
                return Guard(p,'rb') if p==path else original_open(p,*args,**kwargs)
            with patch.object(Path,'open',opened):
                data,prov=read_2023(path,'USDRUBF',{'rows_2023':1,'first':str(T),'blob':'synthetic'})
            self.assertEqual(len(data),1)
            self.assertEqual(prov['prefix_bytes_read'],budget)
            self.assertEqual(prov['bytes_2024_plus_read'],0)
            self.assertEqual(prov['prefix_sha256'],hashlib.sha256(header+line).hexdigest())

    def test_loader_rejects_wrong_budget_before_protected_numeric_parse(self):
        parent=LAB/'work';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            path=Path(temp)/'synthetic.csv'
            path.write_text('Ticker;Datetime;Open;High;Low;Close;Volume\nUSDRUBF;2024-01-01 10:00:00;DO_NOT_PARSE;X;X;X;X\n')
            with self.assertRaisesRegex(ValueError,'BEFORE numeric'):
                read_2023(path,'USDRUBF',{'rows_2023':1,'first':str(T),'blob':'synthetic'})

    def test_replay_rejects_2024_and_2025_before_ohlcv_access(self):
        class Sentinel:
            def __init__(self,year): self.timestamp=datetime(year,1,1)
            def __getattr__(self,name): raise AssertionError('Protected OHLCV accessed')
        for year in (2024,2025,2026):
            with self.assertRaisesRegex(ValueError,'2023 prefix'):
                Replay('USDRUBF','MOMENTUM',P).run([Sentinel(year)])

    def test_output_authority_rejects_other_projects_and_source(self):
        for path in (LAB.parent/'TradingSystemLab/forbidden.txt',LAB.parent/'forbidden.txt',
                     Path('/workspace/market-pattern-data/forbidden.txt')):
            with self.assertRaisesRegex(ValueError,'Output outside'):
                write_text(path,'never written')
            self.assertFalse(path.exists())


class CausalityAndFeatures(unittest.TestCase):
    def test_availability_is_start_plus_ten_or_later(self):
        b=bar()
        self.assertEqual(available(b,P),T+2*FIVE)
        delayed=bar(delivery=T+3*FIVE)
        self.assertEqual(available(delayed,P),T+3*FIVE)
        f=Features(P)
        with self.assertRaisesRegex(ValueError,'not available'):
            f.observe(delayed,T+2*FIVE)
        self.assertIsNone(f.observe(delayed,T+3*FIVE))

    def test_execution_strictly_later_even_equal_open(self):
        self.assertEqual(next_slot(T+2*FIVE),T+3*FIVE)
        self.assertEqual(next_slot(T+timedelta(minutes=10,seconds=1)),T+3*FIVE)
        r=Scripted().run(bars())
        s=r.signals[0];trade=r.ledger[0]
        self.assertGreater(datetime.fromisoformat(trade['entry_interval_start']),datetime.fromisoformat(s['ready_at']))
        self.assertEqual(trade['entry_interval_start'],s['planned_execution_at'])
        self.assertNotEqual(trade['entry_interval_start'],s['signal_at'])

    def test_momentum_price_features_do_not_filter_by_volume(self):
        f=Features(P,price_only=True)
        for b in bars(13): f.observe(bar(b.timestamp,v='0'),available(b,P))
        b=bar(T+13*FIVE,h='101',c='101',v='0')
        x=f.observe(b,available(b,P))
        self.assertEqual(x['MOMENTUM'],1)
        self.assertEqual(x['atr'],D('.4'))
        self.assertIsNone(x['vwap'])

    def test_shifted_breakout_excludes_signal_high_and_atr(self):
        f=Features(P)
        for b in bars(13): self.assertIsNone(f.observe(b,available(b,P)))
        huge=bar(T+13*FIVE,h='150',l='50',c='101')
        x=f.observe(huge,available(huge,P))
        self.assertEqual(x['range_high'],D('100.2'))
        self.assertEqual(x['range_low'],D('99.8'))
        self.assertEqual(x['atr'],D('0.4'))
        self.assertEqual(x['MOMENTUM'],1)

    def test_future_prices_and_existence_do_not_change_submitted_signal(self):
        original=bars()
        altered=bars()
        target=T+14*FIVE
        altered[14]=bar(target,o='101',h='101.2',l='100.8',c='101',v='999999')
        r1,r2=Scripted().run(original),Scripted().run(altered)
        columns=('signal_at','available_at','ready_at','planned_execution_at','direction','stop','take','cap','atr_shifted')
        self.assertEqual({k:r1.signals[0][k] for k in columns},{k:r2.signals[0][k] for k in columns})
        missing=Scripted().run([b for b in original if b.timestamp!=target])
        self.assertEqual({k:r1.signals[0][k] for k in columns},{k:missing.signals[0][k] for k in columns})
        self.assertEqual(missing.signals[0]['status'],'NONFILL')

    def test_vwap_reset_on_gap_and_session_not_carried(self):
        f=Features(P)
        for b in bars(15): f.observe(b,available(b,P))
        b=bar(T+16*FIVE,o='110',h='110',l='110',c='110',v='1')
        self.assertIsNone(f.observe(b,available(b,P)))
        self.assertEqual(f.vwaps,[D(110)])
        b=bar(datetime(2023,1,3,14,5),o='90',h='90',l='90',c='90',v='2')
        self.assertIsNone(f.observe(b,available(b,P)))
        self.assertEqual(f.vwaps,[D(90)])

    def test_weight_normalization_does_not_change_vwap(self):
        f1,f2=Features(P),Features(P)
        for i in range(14):
            a=bar(T+i*FIVE,o=str(100+i),h=str(101+i),l=str(99+i),c=str(100+i),v=str(i+1))
            b=bar(a.timestamp,o=str(a.open),h=str(a.high),l=str(a.low),c=str(a.close),v=str(a.volume*D(100)))
            f1.observe(a,available(a,P));f2.observe(b,available(b,P))
        self.assertEqual(f1.vwaps,f2.vwaps)

    def test_vwap_symmetric_return_rule(self):
        for direction in (1,-1):
            f=Features(P)
            for b in bars(13): f.observe(b,available(b,P))
            edge=bar(T+13*FIVE,o=str(100-direction*2),h=str(100-direction*2+D('0.2')),
                     l=str(100-direction*2-D('0.2')),c=str(100-direction*2))
            f.observe(edge,available(edge,P))
            returned=bar(T+14*FIVE,o=str(100-direction*D('0.2')),h=str(100-direction*D('0.2')+D('0.2')),
                         l=str(100-direction*D('0.2')-D('0.2')),c=str(100-direction*D('0.2')))
            self.assertEqual(f.observe(returned,available(returned,P))['VWAP_MR'],direction)

    def test_no_unknown_stop_used_as_known_boundary(self):
        # 13 September halt is observed via missing bars, no future B/restart.
        w=windows(datetime(2023,9,13).date())
        self.assertEqual(w[0],(datetime(2023,9,13,10),datetime(2023,9,13,14)))
        self.assertEqual(windows(datetime(2023,3,13).date())[1][0].minute,15)
        self.assertEqual(windows(datetime(2023,3,21).date())[1][0].minute,5)

    def test_quarantine_remains_in_common_guard(self):
        self.assertFalse(allowed('IMOEXF',datetime(2024,8,16,18,45)))
        self.assertTrue(allowed('IMOEXF',datetime(2024,8,16,18,40)))
        self.assertFalse(allowed('USDRUBF',datetime(2023,1,3,14)))

    def test_late_delivery_never_generates_early_signal(self):
        data=bars()
        at=T+11*FIVE
        data[11]=bar(at,delivery=at+4*FIVE)
        r=Scripted().run(data)
        self.assertEqual(r.signals,[])  # late observation not reused as current


class ExecutionAndAccounting(unittest.TestCase):
    def test_stop_first_both_directions(self):
        b=bar(h='105',l='95')
        for direction,stop,take in ((1,D(98),D(102)),(-1,D(102),D(98))):
            price,reason,flags=level_exit(b,direction,stop,take,D('0.01'))
            self.assertEqual((price,reason),(stop,'STOP'))
            self.assertIn('AMBIGUOUS_STOP_TP',flags)

    def test_entry_bar_tp_forbidden_adverse_stop_permitted(self):
        b=bar(h='105',l='99')
        self.assertIsNone(level_exit(b,1,D(98),D(102),D('0.01'),True))
        b=bar(h='105',l='95')
        ex=level_exit(b,1,D(98),D(102),D('0.01'),True)
        self.assertIn('AMBIGUOUS_ENTRY_EXIT',ex[2])
        data=bars();data[14]=bar(T+14*FIVE,h='105',l='95')
        r=Scripted().run(data)
        self.assertEqual(r.ledger[0]['exit_reason'],'STOP')
        self.assertEqual(r.ledger[0]['gross_price_pnl'],D('-1.5'))

    def test_touch_is_not_passive_fill_penetration_required(self):
        self.assertIsNone(level_exit(bar(h='102'),1,D(98),D(102),D('0.01')))
        self.assertEqual(level_exit(bar(h='102.01'),1,D(98),D(102),D('0.01'))[:2],(D(102),'TAKE'))
        self.assertIsNone(level_exit(bar(l='98'),-1,D(102),D(98),D('0.01')))

    def test_gap_stop_uses_worse_open(self):
        self.assertEqual(level_exit(bar(o='95',h='96',l='94',c='95'),1,D(98),D(102),D('0.01'))[0],D(95))
        self.assertEqual(level_exit(bar(o='105',h='106',l='104',c='105'),-1,D(102),D(98),D('0.01'))[0],D(105))

    def test_absolute_protection_and_adverse_cap_not_repriced(self):
        data=bars();data[14]=bar(T+14*FIVE,o='101',h='101',l='101',c='101')
        r=Scripted().run(data)
        self.assertEqual(r.signals[0]['status'],'NONFILL')
        self.assertEqual(r.ledger,[])
        self.assertEqual(r.signals[0]['stop'],D('98.50'))
        self.assertTrue(any(e['kind']=='ENTRY_CANCEL' and e['status']=='CANCELLED' for e in r.events))

    def test_nonfill_partial_and_residual_units(self):
        self.assertEqual(fill_units(2,0),(0,2,'NONFILL'))
        self.assertEqual(fill_units(2,1),(1,1,'PARTIAL'))
        self.assertEqual(fill_units(2),(2,0,'MODELLED'))
        with self.assertRaises(ValueError): fill_units(1,D('0.5'))
        r=Scripted(abstract_units=2,capacities={('ENTRY',T+14*FIVE):1}).run(bars())
        row=r.ledger[0]
        self.assertEqual(row['entry_filled_model_units'],1)
        self.assertEqual(row['entry_cancelled_model_units'],1)
        self.assertEqual(row['residual_model_units'],0)
        self.assertTrue(any(e['status']=='PARTIAL' for e in r.events))
        self.assertEqual(row['c1_total'],D('.02'))

    def test_partial_exit_retry_cost_once_per_executed_unit(self):
        # Hold 90m; order at entry+85m, eligible exit at entry+90m.
        at=T+14*FIVE+timedelta(minutes=90)
        r=Scripted(abstract_units=2,capacities={('EXIT',at):1}).run(bars())
        row=r.ledger[0]
        self.assertEqual(row['exit_filled_model_units'],2)
        self.assertEqual(row['residual_model_units'],0)
        self.assertEqual(row['c1_entry'],D('.02'))
        self.assertEqual(row['c1_exit'],D('.02'))
        self.assertEqual(row['c1_total'],D('.04'))
        self.assertEqual(row['net_model_c1'],D('-.04'))
        self.assertEqual(r.counts['partial_events'],1)

    def test_missing_bar_does_not_create_entry_fill_or_carry_signal(self):
        target=T+14*FIVE
        r=Scripted().run([b for b in bars() if b.timestamp!=target])
        self.assertEqual(len(r.signals),1)
        self.assertEqual(r.signals[0]['status'],'NONFILL')
        self.assertEqual(r.ledger,[])
        self.assertTrue(any(e['kind']=='ENTRY_CANCEL' for e in r.events))

    def test_pending_entry_gap_not_retroactively_cancelled_or_free(self):
        for missing_index in (12,13):
            data=[b for b in bars() if b.timestamp!=T+missing_index*FIVE]
            r=Scripted().run(data)
            row=r.ledger[0]
            self.assertEqual(row['entry_interval_start'],str(T+14*FIVE))
            self.assertEqual(row['status'],'UNRESOLVED')
            self.assertIn('PENDING_ENTRY_GAP',row['unresolved_reasons'])
            self.assertIsNone(row['net_model_c1'])
            self.assertTrue(any(e['kind']=='ENTRY_CANCEL_REQUEST' and e['status']=='UNRESOLVED' for e in r.events))
            self.assertEqual(row['residual_model_units'],0)

    def test_missing_exit_and_open_residual_not_deleted_at_cutoff(self):
        data=bars(15)  # entry is last observed bar, entire remainder of day absent
        r=Scripted().run(data)
        self.assertEqual(len(r.ledger),1)
        row=r.ledger[0]
        self.assertEqual(row['status'],'UNRESOLVED')
        self.assertEqual(row['residual_model_units'],1)
        self.assertIsNone(row['net_model_c1'])
        self.assertEqual(row['c1_exit'],0)
        self.assertEqual(metrics(r.ledger)['metric_status'],'INCOMPLETE / CLOSED-ONLY DIAGNOSTIC')
        self.assertTrue(any(e['kind']=='EXIT' and e['status']=='NONFILL' for e in r.events))

    def test_zero_exit_capacity_keeps_residual_then_retries(self):
        at=T+14*FIVE+timedelta(minutes=90)
        r=Scripted(capacities={('EXIT',at):0}).run(bars())
        self.assertTrue(any(e['kind']=='EXIT' and e['status']=='NONFILL' and e['residual_model_units']==1 for e in r.events))
        self.assertEqual(r.ledger[0]['residual_model_units'],0)
        self.assertEqual(r.ledger[0]['c1_total'],D('.02'))

    def test_emergency_gap_keeps_unknown_cost_even_if_later_flat(self):
        data=[b for b in bars() if b.timestamp!=T+16*FIVE]
        r=Scripted().run(data)
        row=r.ledger[0]
        self.assertEqual(row['status'],'UNRESOLVED')
        self.assertEqual(row['residual_model_units'],0)
        self.assertIsNone(row['net_model_c1'])
        self.assertEqual(row['funding_and_emergency_costs'],'UNRESOLVED')
        self.assertIsNone(metrics(r.ledger)['net_model_c1'])

    def test_scheduled_boundary_entry_cutoff_and_flat_attempt(self):
        r=Scripted(at=datetime(2023,1,3,13,20)).run(bars())
        self.assertEqual(r.signals[0]['reason'],'KNOWN_BOUNDARY_ENTRY_CUTOFF')
        r=Scripted(at=datetime(2023,1,3,13)).run(bars())
        row=r.ledger[0]
        self.assertEqual(row['exit_reason'],'SESSION_FLAT')
        submitted=[e for e in r.events if e['kind']=='EXIT_ORDER'][0]
        self.assertEqual(submitted['at'],'2023-01-03 13:40:00')
        self.assertEqual(row['exit_interval_start'],'2023-01-03 13:45:00')
        self.assertEqual(row['exit_confirmed_at'],'2023-01-03 13:55:00')
        self.assertTrue(row['flat_target_breach'])
        self.assertEqual(row['status'],'MODELLED') # actual model flat before B, no invented funding

    def test_lunch_boundary_residual_liability_unresolved(self):
        data=[b for b in bars() if not datetime(2023,1,3,13,40)<=b.timestamp<datetime(2023,1,3,14,5)]
        r=Scripted(at=datetime(2023,1,3,13)).run(data)
        self.assertEqual(r.ledger[0]['status'],'UNRESOLVED')
        self.assertIn('BOUNDARY_EXPOSURE',r.ledger[0]['unresolved_reasons'])
        self.assertEqual(r.ledger[0]['residual_model_units'],0)
        self.assertIsNone(r.ledger[0]['net_model_c1'])

    def test_c1_and_historical_cny_tick_each_side(self):
        old=datetime(2023,9,27,18,45);new=datetime(2023,9,27,19)
        self.assertEqual(tick('CNYRUBF',old),D('.01'))
        self.assertEqual(tick('CNYRUBF',new),D('.001'))
        self.assertEqual(tick('CNYRUBF',old)+tick('CNYRUBF',new),D('.011'))
        r=Scripted().run(bars())
        row=r.ledger[0]
        self.assertEqual(row['c1_total'],D('.02'))
        self.assertEqual(row['net_model_c1'],row['gross_price_pnl']-row['c1_total'])
        self.assertEqual(row['holding_minutes_bar_starts'],90)

    def test_rounding_conservative_and_shared(self):
        st,tp,cap=protection(1,D('100'),D('.333'),D('101'),'MOMENTUM',D('.01'),P)
        self.assertGreaterEqual(st,D('100')-D('1.5')*D('.333'))
        self.assertGreaterEqual(tp,D('100')+D(3)*D('.333'))
        self.assertLessEqual(cap,D('100')+D('.25')*D('.333'))

    def test_no_coverage_distinct_from_zero_trade(self):
        data=[bar(datetime(2023,7,11,10),symbol='GLDRUBF')]
        r=Replay('GLDRUBF','MOMENTUM',P).run(data)
        groups,_=group_metrics(r,data)
        by={g['period']:g for g in groups if g['group']=='MONTH'}
        self.assertEqual(by['2023-01']['month_outcome'],'NO_COVERAGE')
        self.assertIsNone(by['2023-01']['net_model_c1'])
        self.assertEqual(by['2023-07']['month_outcome'],'ZERO_TRADES')
        self.assertEqual(by['2023-07']['net_model_c1'],0)

    def test_mtm_drawdown_includes_observed_open_exposure(self):
        data=bars();data[15]=bar(T+15*FIVE,h='101.2',l='99.8',c='101')
        r=Scripted().run(data)
        self.assertGreater(r.mtm_drawdown,metrics(r.ledger)['closed_only_drawdown_price_units'])
        self.assertEqual(r.month_marks['2023-01']['residual_model_units'],0)

    def test_replay_deterministic_and_no_real_quantity_equity(self):
        a,b=Scripted().run(bars()),Scripted().run(bars())
        self.assertEqual(encoded(a.ledger),encoded(b.ledger))
        self.assertEqual(encoded(a.signals),encoded(b.signals))
        self.assertEqual(encoded(a.events),encoded(b.events))
        self.assertFalse(any(k in a.ledger[0] for k in ('equity','q_real','CAGR')))


if __name__=='__main__': unittest.main()
