"""Separate oracle comparisons and deliberately corrupted facts must fail."""
from decimal import Decimal as D
from dataclasses import replace
from datetime import timedelta
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
from copy import deepcopy
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from IntradayLab.tests.test_bollinger_rsi_reentry import source,run,B,C,SIGNAL,ENTRY,T,DAY,PRE,FIVE,FIFTEEN,set_parent,CFG,LAB,RULES
from IntradayLab.core.backtester import Backtester
from IntradayLab.core.m15_bars import aggregate_m15
from IntradayLab.strategies.bollinger_rsi_reentry_m15 import BollingerRSIReentry,FIXED_PARAMETERS
from IntradayLab.core.reports import csv_write
from IntradayLab.tools import audit_bollinger_rsi_reentry_baseline as oracle
from IntradayLab.tools import run_bollinger_rsi_reentry_baseline as runner


class IndependentBollingerTests(unittest.TestCase):
    def expected(self,raw):
        tuples={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()}
        p=oracle.parent_rows('USDRUBF',tuples)
        ev=[s for s in oracle.episodes('USDRUBF',p) if s['date']<=str(DAY)]
        return oracle.replay('USDRUBF',p,ev)

    def compare(self,raw):
        ss,tt,_=run(raw);es,et=self.expected(raw)
        with TemporaryDirectory(dir=LAB/'work') as folder:
            for name,actual,expected in (('signals',ss,es),('trades',tt,et)):
                path=Path(folder)/(name+'.csv');csv_write(path,actual)
                keys=sorted({k for r in expected for k in r if k!='unknown_effective_at'})
                oracle.check_rows(oracle.read_csv(path),expected,keys,name)

    def test_long_short_indicators_signals_execution_every_field(self):
        for side in (1,-1):self.compare(source(side))

    def test_each_missing_wait_entry_and_path_child(self):
        for at in (SIGNAL,SIGNAL+FIVE,SIGNAL+2*FIVE,ENTRY,ENTRY+FIVE,ENTRY+2*FIVE,ENTRY+FIFTEEN,ENTRY+FIFTEEN+FIVE):
            raw=source();del raw[at];self.compare(raw)

    def test_gap_reset_missing_b_or_c_child(self):
        for at in (T,T+FIVE,B,B+FIVE,C,C+FIVE):
            raw=source();del raw[at];self.compare(raw)

    def test_conflict_take_gap_no_entry_take(self):
        for at,values in ((ENTRY+FIFTEEN,(95,120,80,95)),(ENTRY+FIFTEEN,(85,86,84,85)),(ENTRY+FIFTEEN,(95,120,94.9,95)),(ENTRY,(95,120,94.9,95))):
            raw=source();set_parent(raw,at,values);self.compare(raw)

    def test_corrupted_indicators_and_causal_stop_fail(self):
        es,_=self.expected(source());expected=[next(s for s in es if s['test_start']==C)]
        with TemporaryDirectory(dir=LAB/'work') as folder:
            p=Path(folder)/'signals.csv';csv_write(p,expected);actual=oracle.read_csv(p)
            for k in ('sma20','lower_band','upper_band','population_sigma','rsi14','breach_rsi14','stop','breach_start','signal_at'):
                changed=[dict(actual[0],**{k:'99999'})]
                with self.assertRaises(AssertionError):oracle.check_rows(changed,expected,(k,),'CORRUPT_SIGNAL')

    def test_corrupted_prices_cost_target_and_net_fail(self):
        _,expected=self.expected(source())
        with TemporaryDirectory(dir=LAB/'work') as folder:
            p=Path(folder)/'trades.csv';csv_write(p,expected);actual=oracle.read_csv(p)
            for k in ('entry_price','stop','take','exit_price','cost_c1','net_c1','net_R_c1','risk'):
                with self.assertRaises(AssertionError):oracle.check_rows([dict(actual[0],**{k:'99999'})],expected,(k,),'CORRUPT_TRADE')

    def test_weighted_oracle_past_invariant_to_future_mutation(self):
        raw=source();es,_=self.expected(raw)
        for at in list(raw):
            if at>=SIGNAL:set_parent(raw,at.replace(minute=at.minute//15*15),(1,999,1,1))
        fs,_=self.expected(raw)
        # Formation values only: subsequent submission/fill diagnostics vary.
        keys=('base_reason','direction','signal_at','stop','test_start','test_closed_at','rsi14','breach_rsi14','lower_band','upper_band')
        original=[s for s in es if s['recorded_at']<=SIGNAL];changed=[s for s in fs if s['recorded_at']<=SIGNAL]
        self.assertEqual([{k:s.get(k) for k in keys} for s in original],[{k:s.get(k) for k in keys} for s in changed])

    def test_oracle_has_no_production_imports(self):
        for module in (oracle,):
            tree=__import__('ast').parse(inspect.getsource(module))
            imports=[n.module for n in __import__('ast').walk(tree) if isinstance(n,__import__('ast').ImportFrom)]
            self.assertTrue(all(not (m or '').startswith(('IntradayLab.core','IntradayLab.strategies')) for m in imports))

    def test_full_synthetic_report_audit_and_corrupt_economics(self):
        cfg=deepcopy(CFG);cfg['instruments']=['USDRUBF'];cfg['inputs']={'USDRUBF':cfg['inputs']['USDRUBF']};cfg['execution_code_sha256']={}
        raw=source();tuples={t:(b.open,b.high,b.low,b.close,b.volume) for t,b in raw.items()}
        spec=cfg['inputs']['USDRUBF'];freeze='0'*40
        receipts={'USDRUBF':dict(spec,bytes_read=spec['prefix_bytes'],bytes_2024_plus_read=0)}
        audit_receipts={'USDRUBF':dict(bytes_read=spec['prefix_bytes'],sha256=spec['prefix_sha256'])}
        original=subprocess.check_output
        with TemporaryDirectory(dir=LAB/'work') as folder:
            folder=Path(folder);config=folder/'synthetic.json';config.write_text(json.dumps(cfg))
            config.with_suffix('.sha256').write_text(hashlib.sha256(config.read_bytes()).hexdigest()+'\n')
            reach=folder/'bollinger_rsi_reentry_m15_2023_v1_reachability.json';reach.write_bytes((LAB/'config'/reach.name).read_bytes())
            output=folder/'results';data_root=folder/'synthetic_source'
            def git_output(args,*a,**kw):
                if freeze+':' in str(args):return config.read_bytes()
                if len(args)>2 and args[2]==str(data_root):
                    if args[3]=='rev-parse':return cfg['source_ref']+'\n'
                    if args[3]=='status':return ''
                    if args[3]=='ls-files':return '100644 '+spec['blob']+' 0 '+spec['path']
                return original(args,*a,**kw)
            # The source is explicitly synthetic; these identity stubs validate
            # reporting mechanics, not real-input provenance or a market Baseline.
            with patch.object(runner,'CONFIG',config),patch.object(runner,'FREEZE',freeze),patch.object(oracle,'CONFIG',config),patch.object(oracle,'FREEZE',freeze),patch('subprocess.check_output',side_effect=git_output),patch.object(runner,'load_market_data',return_value=({'USDRUBF':raw},receipts)),patch.object(oracle,'read_source',return_value=({'USDRUBF':tuples},audit_receipts)):
                # The runner's calendar receipt remains the fixed committed path.
                runner.run(data_root,output);result=oracle.audit(data_root,output)
                self.assertEqual(result['status'],'PASS')
                metrics=json.loads((output/'metrics.json').read_text())
                metrics['instruments']['USDRUBF']['conditional_closed_only_C1']['Net_R']='99999'
                (output/'metrics.json').write_text(json.dumps(metrics))
                with self.assertRaises(AssertionError):oracle.audit(data_root,output)

    def test_old_baseline_files_equal_base_git_blobs(self):
        base=CFG['base_main'];paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,'--','IntradayLab/results','IntradayLab/config','IntradayLab/strategies','IntradayLab/core'],text=True).splitlines()
        for path in paths:
            before=subprocess.check_output(['git','show',base+':'+path])
            self.assertEqual(hashlib.sha256((LAB.parent/path).read_bytes()).digest(),hashlib.sha256(before).digest(),path)

    def test_unknown_following_day_flat_contract_and_blank_economics(self):
        raw=source();third=DAY+timedelta(days=1)
        raw.update({t+timedelta(days=1):replace(b,start=t+timedelta(days=1)) for t,b in raw.copy().items() if t.date()==DAY})
        del raw[ENTRY+FIVE]
        p,_=aggregate_m15(raw,RULES,PRE,third+timedelta(days=1))
        _,tt,_=Backtester(RULES,timeframe_minutes=15,daily_trade_deadline_clock='17:00').run(
            BollingerRSIReentry(FIXED_PARAMETERS),'USDRUBF',p,start=PRE,end_exclusive=third+timedelta(days=1))
        q=tt[0]
        self.assertEqual(q['status'],'UNKNOWN')
        self.assertTrue(all(q.get(k) is None for k in ('exit_price','gross','net_R_c1','net_c1','cost_c1')))
        self.assertEqual(len(tt),2);self.assertTrue(tt[1]['prior_unknown_requires_flat_assumption'])
        self.assertEqual(tt[1]['status'],'CLOSED')


if __name__=='__main__':unittest.main()
