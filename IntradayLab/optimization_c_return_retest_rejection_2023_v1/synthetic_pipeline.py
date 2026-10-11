"""All 288 synthetic evaluations plus exact oracle and seven corruption checks."""
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal as D
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from . import runner,auditor
from .tests import CTests
from .contract import ROOT,STUDY
from IntradayLab.core.reports import dump,csv_write


def run():
    fx=CTests();fx.setUp();policy=json.loads((STUDY/'OPTIMIZATION_C_POLICY.json').read_text())
    _,_,rows,_=fx.fixture('take');raw=dict(rows)
    # Distinct days expose both missing immediate Open and missing filled path.
    for offset,case in ((1,'missing_entry'),(2,'missing_exposure'),(3,'stop_gap')):
        _,_,part,_=fx.fixture(case)
        for at,b in part.items():raw[at+timedelta(days=offset)]=replace(b,start=at+timedelta(days=offset))
    for offset in range(4):
        for i in range(5):
            b=fx.bar(i,'99.99');at=b.start+timedelta(days=offset);raw[at]=replace(b,start=at)
        at=fx.origin+7*timedelta(minutes=5)+timedelta(days=offset);raw[at]=replace(raw[at],close=D('99.99'))
        at=fx.origin+8*timedelta(minutes=5)+timedelta(days=offset);raw[at]=replace(raw[at],open=D('99.97'))
    raw=dict(sorted(raw.items()));oracle={'USDRUBF':{a:dict(o=b.open,h=b.high,l=b.low,c=b.close,v=b.volume) for a,b in raw.items()}}
    with tempfile.TemporaryDirectory(dir=ROOT/'IntradayLab/work') as directory:
        out=Path(directory)/'synthetic_288'
        with patch.object(runner,'verify_freeze',return_value=(policy,'0'*40,{})),patch.object(runner,'protected_check'),patch.object(runner,'load_market_data',return_value=({'USDRUBF':raw},{})):
            selection=runner.run(Path('/workspace/market-pattern-data'),out)
        receipt=auditor.audit(None,out,policy,oracle,synthetic=True)
        checks=[];first=auditor.read_csv(out/'all_candidates.csv')[0]['configuration_id'];folder=out/'evaluations'/first/'USDRUBF'
        # Early corruption failures are enough: algorithms are not adapted.
        for label,path,field in [('PF',out/'all_candidates.csv','PF_R'),('MONTH',out/'monthly_results.csv','Net_R'),('TRADE',folder/'trades.csv','take'),('CONSTRUCTION',folder/'construction_events.csv','level'),('EXCLUSION',folder/'data_quality_exclusions.csv','entry_price')]:
            original=path.read_bytes();rs=auditor.read_csv(path)
            assert rs,label+' fixture needs a record'
            rs[0][field]='999999';csv_write(path,rs)
            try:auditor.audit(None,out,policy,oracle,synthetic=True)
            except AssertionError as e:checks.append(dict(case=label,status='DETECTED',reason=str(e)))
            else:raise AssertionError('UNDETECTED_CORRUPTION '+label)
            finally:path.write_bytes(original)
        # Verify the selector cannot silently drop an evaluated config or month.
        for label,path in [('MISSING_CONFIG',out/'all_candidates.csv'),('MISSING_MONTH',out/'monthly_results.csv')]:
            original=path.read_bytes();rs=auditor.read_csv(path);csv_write(path,rs[1:])
            try:auditor.audit(None,out,policy,oracle,synthetic=True)
            except AssertionError as e:checks.append(dict(case=label,status='DETECTED',reason=str(e)))
            else:raise AssertionError('UNDETECTED_CORRUPTION '+label)
            finally:path.write_bytes(original)
        result=dict(status='PASS',synthetic_evaluations=288,historical_candle_reads=0,independent_checked_fields=receipt['checked_fields'],corruption_checks=checks,selection=selection['overall_result'],adapters='Only in-memory source and freeze metadata; independent computational algorithms unchanged; synthetic control compares current bytes instead of historical ledger')
        dump(STUDY/'synthetic_pipeline_receipt.json',result);print(json.dumps(result,sort_keys=True))

if __name__=='__main__':run()
