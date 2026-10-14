"""Read-only source and frozen code receipts, no reference trade access."""
import csv,hashlib,json,platform,subprocess
from collections import Counter
from datetime import datetime,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas,numpy
from io_utils import digest,write_csv

HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent;SPEC=json.loads((HERE/'SPEC.json').read_text())
EXPECTED=dict(USDRUBF='fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8',CNYRUBF='259298733d1528c0d917b100118896009519a9f08bdad33d4b373d9ce86f99b4',GLDRUBF='7381d672485b5687ca2c4d92aa5960c24bb132f527589bae3c622b2dfa20a83d',IMOEXF='a1b9fa6102a955103d61b28e81533ed19de68117e30fd84ceb53e8e617559773')

def git(*args,root=ROOT):return subprocess.check_output(['git','-C',str(root),*args])

def manifest(data,out):
    assert git('rev-parse','HEAD',root=data).decode().strip()==SPEC['data']
    assert not git('status','--porcelain',root=data).strip(),'DATA_DIRTY'
    sources=[];gaps=[];monthly=[]
    for s in SPEC['symbols']:
        relative=f'forever/{s}/{s}_M15.csv';path=data/relative
        full=digest(path);assert full==EXPECTED[s]
        blob=git('rev-parse',SPEC['data']+':'+relative,root=data).decode().strip()
        assert git('hash-object',str(path),root=data).decode().strip()==blob
        with path.open() as f:rows=list(csv.DictReader(f,delimiter=';'))
        stamps=[datetime.fromisoformat(r['Datetime']).replace(tzinfo=ZoneInfo('Europe/Moscow')) for r in rows]
        duplicate=len(stamps)-len(set(stamps));unsorted=sum(b<=a for a,b in zip(stamps,stamps[1:]))
        assert duplicate==unsorted==0
        hist=Counter();missing=0
        for a,b in zip(stamps,stamps[1:]):
            delta=(b-a).total_seconds()/60
            if delta!=15:
                hist[delta]+=1;missing+=int(delta//15)-1
                gaps.append(dict(instrument=s,previous_open=a,next_open=b,delta_minutes=delta,unobserved_grid_slots=int(delta//15)-1,cross_date=a.date()!=b.date(),classification='OBSERVED_GAP_UNCLASSIFIED_NOT_SYNTHESIZED'))
        sources.append(dict(instrument=s,path=relative,sha256=full,git_blob_sha=blob,rows=len(rows),first_open=stamps[0],first_close=stamps[0]+timedelta(minutes=15),last_open=stamps[-1],last_close=stamps[-1]+timedelta(minutes=15),duplicate_timestamps=duplicate,nonincreasing_pairs=unsorted,gap_count=sum(hist.values()),unobserved_grid_slots=missing,gap_delta_histogram={str(k):v for k,v in sorted(hist.items())}))
        counts=Counter((t+timedelta(minutes=15)).strftime('%Y-%m') for t in stamps)
        for year in range(2023,2027):
            for month in range(1,13):
                if (year,month)>(2026,10):continue
                ym=f'{year}-{month:02d}'
                ts=[t for t in stamps if (t+timedelta(minutes=15)).strftime('%Y-%m')==ym]
                monthly.append(dict(instrument=s,month=ym,candles=counts[ym],coverage='OBSERVED' if ts else 'NO_COVERAGE',first_close=ts[0]+timedelta(minutes=15) if ts else None,last_close=ts[-1]+timedelta(minutes=15) if ts else None))
    frozen=[]
    for name in ('engine.py','common.py','scalar.py','SPEC.json','PROTOCOL.md'):
        rel='IntradayLab/t3_m15_execution_sensitivity_v1/'+name
        raw=git('show',SPEC['main']+':'+rel)
        assert raw==(ROOT/rel).read_bytes()
        frozen.append(dict(path=rel,ref=SPEC['main'],sha256=hashlib.sha256(raw).hexdigest(),direct_bytes_unchanged=True))
    write_csv(out/'source_gaps.csv',gaps);write_csv(out/'source_monthly_coverage.csv',monthly)
    return dict(repository='alkospacer123/market-pattern-discovery',refs={k:SPEC[k] for k in ('main','pr514','pr517','data')},source_files=sources,frozen_logic_files=frozen,code_freeze=json.loads((HERE/'FREEZE.json').read_text()) if (HERE/'FREEZE.json').exists() else None,new_code_sha256={p.name:digest(p) for p in sorted(HERE.iterdir()) if p.suffix=='.py' or p.name in ('SPEC.json','requirements.txt','README.md','initial_git_context.json')},all_source_candles_used=True,data_read_only=True,raw_candles_copied=False,available_period='All pinned source M15 candles; no invented candles or extrapolation to current date',gap_limitation='Unobserved slots include weekends, clearing and scheduled breaks; without exchange-calendar evidence they are not all asserted to be missing market data',runtime=dict(python=platform.python_version(),pandas=pandas.__version__,numpy=numpy.__version__))
