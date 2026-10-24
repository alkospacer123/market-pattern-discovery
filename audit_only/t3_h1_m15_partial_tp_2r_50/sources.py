"""Fail closed source receipts, before any new experimental calculation."""
import ast, hashlib, json, platform, subprocess
from pathlib import Path
import numpy,pandas as pd
from common import *

POST='TradingSystemLab/results/post_v3_analysis/'
H1_STAGE=POST+'stage7_production_specification_freeze/'
M15='IntradayLab/t3_m15_t1_entry_retest_v1/'

def prepare(h1root,m15root):
    assert git('merge-base','--is-ancestor',BASE,'HEAD')==''
    assert git('show',PROTOCOL_COMMIT+':audit_only/t3_h1_m15_partial_tp_2r_50/PROTOCOL_RU.md').encode()+b'\n'==(HERE/'PROTOCOL_V1_RU.md').read_bytes()
    checked={}
    def check(rel,expected=None):
        raw=(ROOT/rel).read_bytes();digest=hashlib.sha256(raw).hexdigest()
        original=subprocess.check_output(['git','-C',str(ROOT),'show',BASE+':'+rel])
        assert raw==original,('MAIN_FILE_CHANGED',rel)
        assert expected is None or expected==digest,('FROZEN_HASH_MISMATCH',rel,expected,digest)
        checked[rel]=dict(sha256=digest,base_blob=git('rev-parse',BASE+':'+rel))
    for name,x in json.loads((ROOT/(H1_STAGE+'source_provenance.json')).read_text()).items():
        if 'path' in x:check(x['path'],x['sha256'])
    spec=json.loads((ROOT/(H1_STAGE+'production_specification.json')).read_text())
    assert spec['identity']=='TRAIL1__N4_01__FULL__R15'
    assert spec['strategy']['candidate']=='T3_H1_candidate_v3'
    assert tuple(spec['basket']['instruments'])==SYMBOLS
    assert spec['risk']['risk_fraction_per_new_instrument_position']==.015 and spec['risk']['maximum_nominal_simultaneous_initial_risk']==.06
    assert spec['variant']['name']=='TRAIL1' and spec['variant']['trigger_r']==1.
    assert spec['strategy']['parameters']==dict(adx_period=14,adx_threshold=20.,atr_average_period=20,atr_period=14,breakout_period=20,ema_period=100,slope_lookback=5,stop_atr=2.5,trail_atr=3.)
    for x in ('production_specification.json','source_provenance.json','execution_semantics.md','risk_and_sizing_contract.md'):check(H1_STAGE+x)
    for name,expected in json.loads((ROOT/(M15+'FREEZE.json')).read_text())['files'].items():check(M15+name,expected)
    m15spec=json.loads((ROOT/(M15+'SPEC.json')).read_text());assert m15spec['data']==M15_DATA
    for rel in (POST+'stage6_fixed_basket_reassessment/trail1_authoritative_trades.csv',POST+'stage6_fixed_basket_reassessment/basket_monthly_metrics.csv',POST+'stage6_fixed_basket_reassessment/basket_yearly_metrics.csv',M15+'results/next_open_trades.csv',M15+'results/next_open_stops.csv.gz',M15+'results/next_open_signals.csv.gz',M15+'results/monthly_comparison.csv',M15+'results/yearly_comparison.csv','TradingSystemLab/core/data_loader.py','TradingSystemLab/core/indicators.py','TradingSystemLab/stage8_robot/strategy_core.py','TradingSystemLab/stage8_robot/trail1_state.py','TradingSystemLab/stage8_robot/production_instrument_registry.csv','IntradayLab/SELECTED_T3_M15_SESSION_T1_R15.md'):
        check(rel)
    pr540=PR540_HEAD
    raw=subprocess.check_output(['git','-C',str(ROOT),'show',pr540+':IntradayLab/m15_robot/spec.py'])
    assert hashlib.sha256(raw).hexdigest()=='f2e87ec88fce5200b0f103a3b87945a9b10d58210022338511192e796cdc2e08'
    tree=ast.parse(raw);values={}
    for node in tree.body:
        if isinstance(node,ast.Assign):
            try:values[node.targets[0].id]=ast.literal_eval(node.value)
            except (ValueError,TypeError): pass
    assert values['ROBOT_ID']=='T3_M15_T1_TRAIL35_N4_R15' and values['RESEARCH_BUILD_ID']=='T1_NEXT_OPEN_TRAIL_3p5'
    assert values['ENTRY_MODEL']=='NEXT_OPEN' and values['TIMEFRAME_MINUTES']==15
    assert values['INSTRUMENTS']==SYMBOLS
    assert 'INITIAL_STOP_ATR = Decimal("2")' in raw.decode() and 'TRAILING_STOP_ATR = Decimal("3.5")' in raw.decode()
    assert 'RISK_FRACTION = Decimal("0.015")' in raw.decode() and 'MAX_NOMINAL_INITIAL_RISK = Decimal("0.06")' in raw.decode()
    compact=''.join(raw.decode().split())
    assert 'SIGNAL_START_MSK_MINUTE=10*60' in compact and 'SIGNAL_END_MSK_MINUTE=18*60' in compact
    h1hashes=json.loads((ROOT/(POST+'stage5_structural_validation/trail1/manifest_trail1.json')).read_text())['source_hashes']
    m15hashes={r['instrument']:r['sha256'] for r in json.loads((ROOT/(M15+'results/source_manifest.json')).read_text())['source_files']}
    data=[]
    for system,root,commit,tf in [('H1',h1root,H1_DATA,'H1'),('M15',m15root,M15_DATA,'M15')]:
        assert git('rev-parse','HEAD',root=root)==commit
        assert not git('status','--porcelain',root=root)
        for symbol in SYMBOLS:
            rel=f'forever/{symbol}/{symbol}_{tf}.csv';p=root/rel
            digest=sha(p);expected=h1hashes[rel] if system=='H1' else m15hashes[symbol]
            assert digest==expected,('DATA_HASH_MISMATCH',rel)
            assert git('hash-object',str(p),root=root)==git('rev-parse',commit+':'+rel,root=root)
            f=pd.read_csv(p,sep=';');ts=pd.to_datetime(f.Datetime)
            assert ts.is_monotonic_increasing and not ts.duplicated().any()
            data.append(dict(system=system,instrument=symbol,path=rel,commit=commit,sha256=digest,rows=len(f),first_open=str(ts.iloc[0]),last_open=str(ts.iloc[-1]),last_close=str(ts.iloc[-1]+pd.Timedelta(tf.replace('H1','1h').replace('M15','15min')))))
    return dict(status='SOURCE_IDENTITY_PASS',main_at_start=BASE,protocol_commit=PROTOCOL_COMMIT,
        execution_correction_protocol_commit=git('log','-1','--format=%H','--','audit_only/t3_h1_m15_partial_tp_2r_50/PROTOCOL_RU.md'),
        execution_correction='Preliminary target-price gap credits superseded; final TP fills use observed Open for favorable gaps',
        source_files=checked,data=data,h1_identity=spec,m15_spec=m15spec,
        pr518=dict(number=518,head='d85cf85083d6fea047a1a960c9ead441f7b4a6ed',merge='a77fc3ce79db693041c06192f6525f6847017de7'),
        pr540=dict(number=540,head=pr540,spec_sha256=hashlib.sha256(raw).hexdigest(),parsed_literals=values),
        models=['FRACTIONAL_REFERENCE','EXECUTABLE_INTEGER'],cash_status='CASH_MODEL_NOT_VALIDATED',
        cash_missing=['dated historical GO/margin series and changes','dated historical tick value/spec authority','starting equity and cashflows for each separate replay/account','verified historical fees, slippage and perpetual funding/settlement costs'],
        grid_source='Authenticated static production registry snapshot; historical invariance not attested',
        runtime=dict(python=platform.python_version(),pandas=pd.__version__,numpy=numpy.__version__))
