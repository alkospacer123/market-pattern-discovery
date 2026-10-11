"""Full 585-evaluation synthetic pipeline integration, before any historic P&L.

Only metadata/freezing, raw source load and historical comparator ledgers are
adapted to synthetic fixtures in memory. Production execution/reporting and the
independent auditor's episode/path/statistics/selection code run unchanged.
"""
import json,tempfile
from datetime import timedelta
from decimal import Decimal as D
from pathlib import Path
from unittest.mock import patch
from . import runner,auditor
from .tests import OptimizationBTests
from .contract import ROOT,STUDY,grid
from IntradayLab.core.reports import dump

def run():
    fx=OptimizationBTests();fx.setUp();policy=fx.policy;raw={};oracle={}
    for symbol in policy['instruments']:
        fx.symbol=symbol;rows=fx.rows(dict(policy['parameters'],cluster_bars=10))
        step=fx.rules.tick(symbol,fx.at('10:00'))
        for i in range(10):
            at=fx.at('10:00')+i*timedelta(minutes=5)
            high=D(101)-(step if i in (3,6,9) else 0)
            mid=D(101)-3*step
            rows[at]=fx.bar(at,mid,high,D(101)-(20+i)*step,mid)
        following={at+timedelta(days=1):fx.bar(at+timedelta(days=1),b.open,b.high,b.low,b.close) for at,b in rows.items()}
        rows.update(following)
        # Contrasting opportunities and gaps: USD entry missing; CNY exposure missing.
        del rows[fx.at('10:20' if symbol=='USDRUBF' else '10:25')]
        raw[symbol]=rows;oracle[symbol]={a:(b.open,b.high,b.low,b.close,b.volume) for a,b in rows.items()}
    readtext=Path.read_text;readcsv=auditor.read_csv;usd10_reads=0
    def metadata(path,*args,**kw):
        if path==STUDY/'source_commitments.json':return '{"dependencies_sha256": {}}'
        if path==STUDY/'protected_file_sha256.json':return '{}'
        return readtext(path,*args,**kw)
    def legacy_csv(path):
        nonlocal usd10_reads
        if 'high_low_cluster_m5_2023_b' not in str(path):return readcsv(path)
        if path.parent.name.endswith('b10_v1') and path.name=='trades.csv':
            usd10_reads+=1
            if usd10_reads==1:return readcsv(path) # existing excluded USD reference metadata
        n=int(path.parent.name.split('_b')[1].split('_')[0]);allrows=[]
        for symbol in policy['instruments']:
            if symbol=='USDRUBF' and n==10:continue
            p=dict(policy['parameters'],cluster_bars=n,configuration_id=f'B{n}')
            ev=auditor.episodes(symbol,oracle[symbol],p)
            ev=[dict(e,signal_id=f'B{n}_'+e['episode_id'],cluster_id=f'B{n}_'+e['episode_id']) for e in ev]
            ss,tt,_,_=auditor.replay(symbol,oracle[symbol],ev,p,legacy=True);auditor.enrich_expected(ss,tt)
            allrows.extend(ss if path.name=='signals.csv' else tt)
        return allrows
    with tempfile.TemporaryDirectory(dir=ROOT/'IntradayLab/work') as directory:
        out=Path(directory)/'synthetic_585'
        with patch.object(runner,'verify_freeze',return_value=(policy,'0'*40,{})),patch.object(runner,'protected_check'),patch.object(runner,'load_market_data',return_value=(raw,{})):
            selection=runner.run(Path('/workspace/market-pattern-data'),out)
        with patch.object(Path,'read_text',metadata),patch.object(auditor,'read_source',return_value=(oracle,{'synthetic':True})),patch.object(auditor,'read_csv',side_effect=legacy_csv):
            receipt=auditor.audit(Path('/workspace/market-pattern-data'),out)
        assert receipt['status']=='PASS' and receipt['evaluations']==585
        result=dict(status='PASS',synthetic_evaluations=585,historical_candle_reads=0,
            independent_checked_fields=receipt['checked_fields'],selection=selection['overall_result'],
            adapters='In-memory synthetic source/freezing metadata and synthetic legacy comparator ledgers only; every algorithm unchanged')
        dump(STUDY/'synthetic_pipeline_receipt.json',result)
        print(json.dumps(result,sort_keys=True))

if __name__=='__main__':run()
