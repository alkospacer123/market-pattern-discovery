"""Hand-worked synthetic cases for the fixed ORB economic contract."""
from datetime import datetime, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import orb_false_break_fade_replay as p
import audit_orb_false_break_fade as a
import run_orb_false_break_fade as reporting

T=datetime(2023,1,3,10);F=timedelta(minutes=5)


def row(o='100',h='101',l='99',c='100',v='1'):return tuple(map(D,(o,h,l,c,v)))


def sample():
    return {t:row() for t,w in p.slots(T.date())}


def sw(b,t=T+3*F):b[t]=row(h='101.05',l='100.90',c='100.95')


def events(b):return p.base_signals('USDRUBF',b)[0]


def signal(b):return next(x for x in events(b) if x['base_reason']=='SIGNAL')


def path(b,entry=T+F,direction=1,stop='99',take='101.5',end=T.replace(hour=14)):
    return p.trade_path('USDRUBF',b,dict(entry_at=entry,direction=direction,stop=D(stop),take=D(take),window_end=end))


class ORB(unittest.TestCase):
    def test_fixed_OR_and_clock(self):
        b=sample();sw(b);s=signal(b)
        self.assertEqual((s['or_high'],s['or_low']),(D(101),D(99)))
        self.assertEqual(s['or_available_at'],T+3*F)
        self.assertEqual(s['signal_at'],T+4*F)
        self.assertEqual(s['waiting_bar_closed_at'],T+5*F)
        self.assertEqual(s['order_sent_at'],T+5*F)
        self.assertEqual(s['planned_execution_at'],T+5*F)
        self.assertEqual(s['stop'],D('101.06'))

    def test_missing_OR_each_child(self):
        for i in range(3):
            b=sample();del b[T+i*F];sw(b)
            self.assertTrue(any(x['base_reason']=='NO_OR' for x in events(b)))
            self.assertFalse(any(x['base_reason']=='SIGNAL' for x in events(b)))

    def test_invalid_OR_volume(self):
        b=sample();b[T]=row(v='0');sw(b)
        self.assertFalse(any(x['base_reason']=='SIGNAL' for x in events(b)))

    def test_no_future_signal_dependency(self):
        b=sample();sw(b);s=signal(b);b[T+5*F]=row(o='120',h='150',l='90',c='140')
        self.assertEqual(s,signal(b))

    def test_next_reclaim_and_stop_extreme(self):
        b=sample();b[T+3*F]=row(h='101.05',c='101');b[T+4*F]=row(h='101.10',c='100.98')
        s=signal(b);self.assertEqual(s['signal_at'],T+5*F);self.assertEqual(s['stop'],D('101.11'))

    def test_reclaim_depth_and_opposite_boundary(self):
        for close in ('100.99','98.99'):
            b=sample();b[T+3*F]=row(h='101.05',l='98',c=close);b[T+4*F]=row(h='101',l='98',c=close)
            self.assertFalse(any(x['base_reason']=='SIGNAL' for x in events(b)))

    def test_consumption_no_second_attempt(self):
        b=sample();b[T+3*F]=row(h='101.05',c='101');b[T+4*F]=row(c='101');sw(b,T+6*F)
        e=events(b);self.assertEqual(sum(x['direction']==-1 for x in e),1)
        self.assertEqual(next(x for x in e if x['direction']==-1)['base_reason'],'NO_RECLAIM')

    def test_both_sides_ambiguous(self):
        b=sample();b[T+3*F]=row(h='101.05',l='98.95');sw(b,T+6*F)
        self.assertEqual(sum(x['base_reason']=='AMBIGUOUS_BOTH_SIDES' for x in events(b)),1)
        self.assertFalse(any(x['base_reason']=='SIGNAL' for x in events(b)))

    def test_episode_gap_no_reclaim(self):
        b=sample();b[T+3*F]=row(h='101.05',c='101');del b[T+4*F];sw(b,T+5*F)
        self.assertEqual(next(x for x in events(b) if x['direction']==-1)['base_reason'],'NO_RECLAIM_GAP')

    def test_no_lunch_episode_or_second_OR(self):
        b=sample();sw(b,T.replace(hour=13,minute=55));s=signal(b)
        self.assertEqual(s['or_high'],D(101));self.assertEqual(s['window_end'],T.replace(hour=14))
        ss,_=p.replay('USDRUBF',b,events(b),'A_BASE',{'atr':False,'mtf':False})
        self.assertEqual(next(x for x in ss if x['base_reason']=='SIGNAL')['reason'],'SESSION_LIMIT')

    def test_atr_warmup_and_inclusion(self):
        b=sample();sw(b);self.assertIsNone(signal(b)['atr14'])
        b=sample();sw(b,T+14*F);s=signal(b)
        self.assertEqual(s['atr14'],(D(26)+D('1.05'))/14)
        self.assertFalse(s['atr_pass'])
        ss,_=p.replay('USDRUBF',b,events(b),'B_IND',{'atr':True,'mtf':False})
        self.assertEqual(next(x for x in ss if x['base_reason']=='SIGNAL')['reason'],'ATR_SWEEP_TOO_SMALL')

    def test_atr_gap_reset(self):
        b=sample();del b[T+12*F];sw(b,T+14*F)
        self.assertIsNone(signal(b)['atr14'])

    def test_m15_at_reclaim_not_waiting(self):
        b=sample();b[T+2*F]=row(c='100.5');sw(b);s=signal(b)
        self.assertEqual(s['m15_start'],T);self.assertEqual(s['m15_direction'],1)
        b[T+4*F]=row(c='99.5');self.assertEqual(s['m15_direction'],signal(b)['m15_direction'])
        ss,_=p.replay('USDRUBF',b,events(b),'C_MTF',{'atr':False,'mtf':True})
        self.assertEqual(next(x for x in ss if x['base_reason']=='SIGNAL')['reason'],'M15_DIRECTION')

    def test_m15_missing_no_stale(self):
        b=sample();b[T+2*F]=row(c='100.5');del b[T+3*F];sw(b,T+4*F)
        self.assertIsNone(signal(b)['m15_direction'])

    def test_geometry_and_outward_target(self):
        self.assertIsNone(p.open_adapter(D(101),-1,D(100),D('.01')))
        self.assertEqual(p.open_adapter(D(100),1,D('99.99'),D('.01')),(D('.01'),D('100.02')))
        self.assertEqual(p.open_adapter(D(100),-1,D('100.01'),D('.01')),(D('.01'),D('99.98')))

    def test_dated_tick_CNY(self):
        for t,step in ((datetime(2023,9,27,18,55),'.01'),(datetime(2023,9,27,19),'.001')):
            self.assertEqual(p.tick('CNYRUBF',t),D(step));self.assertEqual(a.grid('CNYRUBF',t),D(step))

    def test_stop_first_and_no_entry_take(self):
        b=sample();b[T+F]=row(h='102',l='98');x=path(b)
        self.assertEqual(x['exit_reason'],'STOP');self.assertEqual(x['exit_price'],D(99))
        b={t:row(h='100.5',l='99.5') for t in sample()};b[T+F]=row(h='102',l='99.5');x=path(b)
        self.assertEqual(x['exit_reason'],'TIME')

    def test_stop_gap_worse_take_no_improvement(self):
        b=sample();b[T+F]=row(o='98',h='100',l='97',c='99');self.assertEqual(path(b)['exit_price'],D(98))
        b={t:row(h='100.5',l='99.5') for t in sample()};b[T+2*F]=row(o='102',h='103',l='100',c='102')
        self.assertEqual(path(b)['exit_price'],D('101.5'))

    def test_time_reads_only_scheduled_Open(self):
        b={t:row(h='100.5',l='99.5') for t in sample()};b[T+13*F]=row(o='100.2',h='150',l='90')
        x=path(b);self.assertEqual(x['exit_reason'],'TIME');self.assertEqual(x['exit_price'],D('100.2'))

    def test_session_flat(self):
        b={t:row(h='100.5',l='99.5') for t in sample()};x=path(b,entry=T.replace(hour=13,minute=35))
        self.assertEqual(x['exit_reason'],'SESSION_FLAT');self.assertEqual(x['exit_at'],T.replace(hour=13,minute=55))

    def test_missing_exposure_or_time_is_unknown(self):
        for missing in (T+2*F,T+13*F):
            b={t:row(h='100.5',l='99.5') for t in sample()};del b[missing]
            self.assertEqual(path(b)['status'],'UNKNOWN')

    def test_missing_entry_vs_waiting(self):
        b=sample();sw(b);s=signal(b);del b[s['planned_execution_at']]
        ss,tt=p.replay('USDRUBF',b,events(b),'A_BASE',{'atr':False,'mtf':False})
        self.assertEqual(tt[0]['unknown_reason'],'MISSING_EXECUTION_BAR');self.assertFalse(tt[0]['model_filled'])
        b=sample();sw(b);del b[T+4*F]
        ss,tt=p.replay('USDRUBF',b,events(b),'A_BASE',{'atr':False,'mtf':False})
        self.assertFalse(tt);self.assertEqual(next(x for x in ss if x['base_reason']=='SIGNAL')['reason'],'NO_WAITING_BAR')

    def test_entry_HLC_no_admission_filter(self):
        b=sample();sw(b);s=signal(b);at=s['planned_execution_at'];b[at]=row(o='100.95',h='150',l='90',c='120')
        ss,tt=p.replay('USDRUBF',b,events(b),'A_BASE',{'atr':False,'mtf':False})
        self.assertTrue(tt[0]['model_filled']);self.assertEqual(tt[0]['entry_price'],D('100.95'))

    def test_independent_full_synthetic_trade_match(self):
        for change in ('normal','missing_entry','missing_path','bad_stop'):
            b=sample();sw(b)
            if change=='missing_entry':del b[T+5*F]
            if change=='missing_path':del b[T+6*F]
            if change=='bad_stop':b[T+5*F]=row(o='102',h='103',l='101',c='102')
            ev=events(b);oe=a.oracle_signals('USDRUBF',b)
            self.assertFalse(a.compare_rows(ev,oe,a.SIGNAL_KEYS,'signals'))
            for arch, spec in {'A_BASE':{'atr':False,'mtf':False},'B_IND':{'atr':True,'mtf':False},'C_MTF':{'atr':False,'mtf':True},'D_MTF_IND':{'atr':True,'mtf':True}}.items():
                ss,tt=p.replay('USDRUBF',b,ev,arch,spec);os,ot=a.oracle_trades('USDRUBF',b,oe,arch,spec)
                self.assertFalse(a.compare_rows(ss,os,a.SIGNAL_KEYS+('status','reason','order_admitted','model_filled'),'signals'))
                self.assertFalse(a.compare_rows(tt,ot,a.TRADE_KEYS,'trades'))

    def test_independent_varied_exit_paths(self):
        for kind in ('take','gap_stop','time','unknown','flat'):
            b=sample();sw(b)
            for t in list(b):
                if t>=T+4*F:b[t]=row(o='100.95',h='101',l='100.90',c='100.95')
            if kind=='take':b[T+6*F]=row(o='100.95',h='101',l='100.70',c='100.8')
            if kind=='gap_stop':b[T+6*F]=row(o='102',h='103',l='101',c='102')
            if kind=='unknown':del b[T+6*F]
            if kind=='flat':
                b=sample();sw(b,T.replace(hour=13,minute=35))
                for t in list(b):
                    if t>=T.replace(hour=13,minute=40):b[t]=row(o='100.95',h='101',l='100.90',c='100.95')
            e=events(b);oe=a.oracle_signals('USDRUBF',b)
            ss,tt=p.replay('USDRUBF',b,e,'A_BASE',{'atr':False,'mtf':False})
            os,ot=a.oracle_trades('USDRUBF',b,oe,'A_BASE',{'atr':False,'mtf':False})
            self.assertFalse(a.compare_rows(tt,ot,a.TRADE_KEYS,'trades'))
            self.assertEqual(tt[0]['exit_reason'],{'take':'TAKE','gap_stop':'STOP','time':'TIME','unknown':'UNKNOWN','flat':'SESSION_FLAT'}[kind])

    def test_months_coverage_null(self):
        b=sample();sw(b);e,dd,cc=p.base_signals('USDRUBF',b)
        ss,tt=p.replay('USDRUBF',b,e,'A_BASE',{'atr':False,'mtf':False})
        cfg={'architectures':{x:{} for x in ('A_BASE','B_IND','C_MTF','D_MTF_IND')},'instruments':['USDRUBF'],'inputs':{'USDRUBF':{'first':str(min(b)),'rows_2023':len(b)}}}
        m,months,_,_=reporting.reports(cfg,ss,tt,dd,cc)
        self.assertEqual(len(months),48);self.assertIsNone(m['A_BASE_USDRUBF']['annual_net_c1'])
        self.assertEqual(months[-1]['classification'],'NO_COVERAGE')
        self.assertEqual(months[-1]['diagnostic_sign'],'NO_COVERAGE')

    def test_C2_identical_fills_replacement(self):
        b=sample();sw(b);ss,tt=p.replay('USDRUBF',b,events(b),'A_BASE',{'atr':False,'mtf':False})
        t=tt[0];self.assertEqual(t['net_c2'],t['gross']-t['cost_c2']);self.assertEqual(t['cost_c2'],2*t['cost_c1'])

    def test_unknown_persists_in_later_months(self):
        b=sample();sw(b)
        for t in list(b):
            if t>=T+4*F:b[t]=row(o='100.95',h='101',l='100.90',c='100.95')
        del b[T+6*F]
        e,dd,cc=p.base_signals('USDRUBF',b);ss,tt=p.replay('USDRUBF',b,e,'A_BASE',{'atr':False,'mtf':False})
        feb=datetime(2023,2,1,10)
        cc.append(dict(instrument='USDRUBF',date='2023-02-01',status='COMPLETE',expected_bars=105,valid_bars=105,missing_bars=0,zero_volume_bars=0,or_available=True))
        dd.append(dict(instrument='USDRUBF',date='2023-02-01',observed=True,or_available=True,base_signals=0))
        cfg={'architectures':{x:{} for x in ('A_BASE','B_IND','C_MTF','D_MTF_IND')},'instruments':['USDRUBF'],'inputs':{'USDRUBF':{'first':str(min(b)),'rows_2023':len(b)}}}
        metrics,months,_,_=reporting.reports(cfg,ss,tt,dd,cc)
        febrow=next(x for x in months if x['architecture']=='A_BASE' and x['month']=='2023-02')
        self.assertEqual(febrow['classification'],'UNKNOWN');self.assertEqual(febrow['unknown_carry_in'],1)
        self.assertIsNone(febrow['full_net_c1'])

    def test_independent_reader_never_crosses_2023_LF(self):
        import hashlib, io, tempfile
        from unittest.mock import patch
        parent=p.LAB/'work';parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as temp:
            root=Path(temp);file=root/'synthetic.csv'
            prefix=b'Ticker;Datetime;Open;High;Low;Close;Volume\nUSDRUBF;2023-01-03 10:00:00;100;101;99;100;1\n'
            file.write_bytes(prefix+b'USDRUBF;2024-01-01 10:00:00;DO_NOT_READ\n')
            class Guard(io.FileIO):
                def read(self,n=-1):
                    if n<0 or self.tell()+n>len(prefix):raise AssertionError('Protected byte read')
                    return super().read(n)
            original=Path.open
            def opened(path,*args,**kwargs):
                return Guard(path,'rb') if path==file else original(path,*args,**kwargs)
            cfg={'inputs':{'USDRUBF':{'path':'synthetic.csv','rows_2023':1,'prefix_bytes':len(prefix),'prefix_sha256':hashlib.sha256(prefix).hexdigest()}}}
            with patch.object(Path,'open',opened):raw=a.source(root,cfg)
            self.assertEqual(len(raw['USDRUBF']),1)

    def test_output_is_confined(self):
        with self.assertRaisesRegex(ValueError,'Output must'):
            reporting.run(Path('/unread'),p.LAB.parent/'TradingSystemLab/forbidden_orb')
        self.assertFalse((p.LAB.parent/'TradingSystemLab/forbidden_orb').exists())

    def test_march_calendar_and_holidays(self):
        for d in (datetime(2023,3,13).date(),datetime(2023,3,21).date(),datetime(2023,3,8).date()):
            self.assertEqual(p.windows(d),a.calendar(d))


if __name__=='__main__':unittest.main()
