"""216 synthetic evaluations and adversarial independent artifact checks, no real bars."""
from dataclasses import replace
from datetime import date,timedelta
from decimal import Decimal as D
import json,tempfile
from pathlib import Path
from unittest.mock import patch
from . import runner,auditor
from .contract import ROOT,STUDY
from IntradayLab.core.calendar import MarketRules
from IntradayLab.core.data_loader import validate_bar
from IntradayLab.core.reports import dump,csv_write
FIVE=timedelta(minutes=5)


def fixture(policy):
    rules=MarketRules(policy);data={}
    for symbol in policy['instruments']:
        rows={}
        for day,case in ((date(2023,12,26),'take'),(date(2023,12,27),'missing_entry'),(date(2023,12,28),'missing_exposure'),(date(2023,12,29),'stop_gap')):
            tick=rules.tick(symbol,rules.at(day,'10:00'))
            def bar(clock,o=D('100.5'),h=D(101),l=D(100),c=D('100.5'),v=D(10)):
                at=rules.at(day,clock)
                return validate_bar(at,(o,h,l,c,v),FIVE,tick)
            for a,z in rules.windows(day):
                while a<z:
                    rows[a]=validate_bar(a,(D('100.5'),D(101),D(100),D('100.5'),D(10)),FIVE,tick);a+=FIVE
            rows[rules.at(day,'10:30')]=bar('10:30',l=D(100)-2*tick,c=D(100)+2*tick)
            rows[rules.at(day,'10:45')]=bar('10:45',h=D(150))
            if case=='missing_entry':del rows[rules.at(day,'10:40')]
            elif case=='missing_exposure':del rows[rules.at(day,'10:45')]
            elif case=='stop_gap':rows[rules.at(day,'10:45')]=bar('10:45',o=D(99),h=D(99),l=D(99),c=D(99))
        data[symbol]=dict(sorted(rows.items()))
    return data


def run():
    policy=json.loads((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text());data=fixture(policy)
    raw={s:{a:(b.open,b.high,b.low,b.close,b.volume) for a,b in rs.items()} for s,rs in data.items()}
    with tempfile.TemporaryDirectory(dir=ROOT/'IntradayLab/work') as directory:
        out=Path(directory)/'synthetic_216'
        with patch.object(runner,'verify_freeze',return_value=(policy,'0'*40,{})),patch.object(runner,'protected_check'),patch.object(runner,'baseline_replay'),patch.object(runner,'load_market_data',return_value=(data,{})):
            selection=runner.run(Path('/workspace/market-pattern-data'),out)
        receipt=auditor.audit(None,out,policy,raw,synthetic=True)
        checks=[];first=auditor.read_csv(out/'all_candidates.csv')[0]['configuration_id'];folder=out/'evaluations'/first/'USDRUBF'
        for label,path,field in [('PF',out/'all_candidates.csv','PF_R'),('MONTH',out/'monthly_results.csv','Net_R'),('TRADE',folder/'trades.csv','take'),('SIGNAL',folder/'signals.csv','stop'),('EXCLUSION',folder/'data_quality_exclusions.csv','entry_price'),('NEIGHBOR',out/'parameter_neighborhood.csv','neighbor_PF_R')]:
            original=path.read_bytes();rs=auditor.read_csv(path)
            row=next((r for r in rs if r.get(field) not in ('',None)),None);assert row,label+' needs record'
            row[field]='999999';csv_write(path,rs)
            try:auditor.audit(None,out,policy,raw,synthetic=True)
            except AssertionError as e:checks.append(dict(case=label,status='DETECTED',reason=str(e)))
            else:raise AssertionError('UNDETECTED_CORRUPTION '+label)
            finally:path.write_bytes(original)
        for label,path in [('MISSING_CONFIG',out/'all_candidates.csv'),('MISSING_MONTH',out/'monthly_results.csv')]:
            original=path.read_bytes();rs=auditor.read_csv(path);csv_write(path,rs[1:])
            try:auditor.audit(None,out,policy,raw,synthetic=True)
            except AssertionError as e:checks.append(dict(case=label,status='DETECTED',reason=str(e)))
            else:raise AssertionError('UNDETECTED_CORRUPTION '+label)
            finally:path.write_bytes(original)
        result=dict(status='PASS',synthetic_evaluations=216,historical_candle_reads=0,independent_checked_fields=receipt['checked_fields'],corruption_checks=checks,selection=selection['overall_result'],adapters='In-memory synthetic sources/freeze metadata only; production runner and independent computational oracle unchanged')
        dump(STUDY/'synthetic_pipeline_receipt.json',result);print(json.dumps(result,sort_keys=True))

if __name__=='__main__':run()
