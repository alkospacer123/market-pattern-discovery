"""Independent ledger arithmetic and integrity checks. No generator/engine imports."""
import argparse, csv, gzip, hashlib, io, json, math, subprocess
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=40
PIN='4ae4761837937279eee34bc834c7ec75f066ec81'
MAIN='d6946056332ce71658a6ca933cefa0740a7570a2'
DATA='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
PR513='c17709a748f6247e8bd6bf85c9b4f20fac14a4dd'
SOURCE_DIR='IntradayLab/t3_m15_build_comparison_2023_2026_v1'
SYMS=['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF']
CAL=[f'{y}-{m:02}' for y in range(2023,2027) for m in range(1,13) if y<2026 or m<=10]
D=Decimal
checks=defaultdict(int); max_delta=D(0)

def read(path):
    with (gzip.open if str(path).endswith('.gz') else open)(path,'rt',encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])

def same(a,b,label):
    global max_delta
    checks['numeric_fields']+=1
    if a in ('',None) or b in ('',None):assert a in ('',None) and b in ('',None),(label,a,b);return
    delta=abs(D(str(a))-D(str(b)));max_delta=max(max_delta,delta)
    assert delta<=D('1e-8'),(label,str(a),str(b),str(delta))

def streak(vals):
    best=run=0
    for v in vals:run=run+1 if v<0 else 0;best=max(best,run)
    return best

def compute(trades,months):
    rs=sorted(trades,key=lambda r:(r['exit_time'],r['instrument'],r['trade_id']))
    x=[D(r['gross_R']) for r in rs];wins=[z for z in x if z>0];losses=[z for z in x if z<0]
    gain=sum(wins,D(0));loss=-sum(losses,D(0));total=sum(x,D(0));peak=equity=dd=D(0)
    for z in x:equity+=z;peak=max(peak,equity);dd=max(dd,peak-equity)
    per={m:[r for r in rs if r['exit_time'][:7]==m] for m in months}
    # Exact source float values, stable summation: preserve tiny signed months.
    monthly={m:math.fsum(float(r['gross_R']) for r in rr) for m,rr in per.items()}
    best=sorted(months,key=lambda m:(-monthly[m],m));worst=min(months,key=lambda m:monthly[m]) if months else None
    ans=dict(CLOSED=len(x),wins=len(wins),losses=len(losses),zero_trades=sum(z==0 for z in x),positive_R=gain,loss_R=loss,gross_R=total,gross_PF=gain/loss if loss else None,expectancy_R=total/len(x) if x else None,mean_win_R=gain/len(wins) if wins else None,mean_loss_R=-loss/len(losses) if losses else None,win_rate=D(len(wins))/len(x) if x else None,max_DD_R=dd,max_loss_streak=streak(x),positive_months=sum(v>0 for v in monthly.values()),negative_months=sum(v<0 for v in monthly.values()),zero_months=sum(v==0 for v in monthly.values()),max_negative_month_streak=streak(monthly.values()),worst_month_R=monthly[worst] if worst else None,best_month_share_R=D(str(monthly[best[0]]))/total if best and total>0 else None,top3_month_share_R=sum((D(str(monthly[m])) for m in best[:3]),D(0))/total if best and total>0 else None,winners_ge2=sum(z>=2 for z in x),winners_ge5=sum(z>=5 for z in x))
    for n in (1,5,10):
        removed=sum(sorted(wins,reverse=True)[:n],D(0))
        ans.update({f'top{n}_trades_R':removed,f'top{n}_trades_share_signed_R':removed/total if total>0 else None,f'top{n}_trades_share_positive_R':removed/gain if gain>0 else None,f'R_without_top{n}_trades':total-removed,f'PF_without_top{n}_trades':(gain-removed)/loss if loss else None})
    for n in (1,3):
        xx=[D(r['gross_R']) for r in rs if r['exit_time'][:7] not in set(best[:n])]
        gl=sum((v for v in xx if v>0),D(0));ll=-sum((v for v in xx if v<0),D(0))
        ans[f'R_without_top{n}_months']=sum(xx,D(0));ans[f'PF_without_top{n}_months']=gl/ll if ll else None
    by_symbol={s:sum((D(r['gross_R']) for r in rs if r['instrument']==s),D(0)) for s in {r['instrument'] for r in rs}}
    ans['best_instrument_share_R']=max(by_symbol.values())/total if by_symbol and total>0 else None
    return ans

def run(srcroot,data,out):
    assert git(srcroot,'rev-parse','HEAD').decode().strip()==PIN
    src=srcroot/SOURCE_DIR/'results'
    assert not git(srcroot,'status','--porcelain','--',SOURCE_DIR).strip()
    manifest=json.loads((out/'SOURCE_SHA256.json').read_text())
    for p,h in manifest['input_files'].items():
        q=srcroot/p;assert hashlib.sha256(q.read_bytes()).hexdigest()==h
        assert git(srcroot,'hash-object',str(q)).decode().strip()==git(srcroot,'rev-parse',PIN+':'+p).decode().strip()
        checks['pinned_input_files']+=1
    builds=read(out/'BUILD_CATALOG.csv');assert len(builds)==51
    assert len({r['build_id'] for r in builds})==len({r['config_identity'] for r in builds})==51
    assert sum(r['execution_model']=='NEXT_OPEN' for r in builds)==13
    assert sum(r['execution_model']=='SIGNAL_CLOSE' for r in builds)==38
    origins=read(src/'BUILD_REGISTRY.csv'); origin={r['build_id']:r for r in origins if r['config_identity']}
    for b in builds:
        r=origin[b['build_id']]
        for path,expected in [(r['source_path']+'/engine.py',r['code_sha256']),(r['spec_path'],r['spec_sha256'])]:
            content=git(srcroot,'show',r['code_commit']+':'+path)
            assert hashlib.sha256(content).hexdigest()==expected
            assert content==(srcroot/path).read_bytes()
            checks['code_spec_origin_checks']+=1
        assert git(srcroot,'rev-parse',r['code_commit']+':'+r['source_path']+'/engine.py').decode().strip()==r['code_git_blob']
        cfg=json.loads(r['config_json'])
        assert hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()==r['config_identity']
    # Coverage from pinned raw timestamp metadata. Source data remains read-only.
    assert git(data,'rev-parse','HEAD').decode().strip()==DATA
    rawcov=defaultdict(list); rawprices={}; example_bars={}; raw_sha=[]
    receipts=json.loads((src/'CANONICAL_SOURCE_RECEIPTS.json').read_text())
    for s in SYMS:
        path=data/'forever'/s/(s+'_M15.csv');relative=str(path.relative_to(data))
        blob=git(data,'hash-object',str(path)).decode().strip()
        assert blob==git(data,'rev-parse',DATA+':'+relative).decode().strip()
        rec=next(r for r in receipts if r['instrument']==s)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==rec['prefix_sha256']
        raw_sha.append(dict(instrument=s,git_blob=blob,sha256=rec['prefix_sha256']))
        with path.open() as f:
            reader=csv.DictReader(f,delimiter=';');previous=None
            for r in reader:
                at=(datetime.fromisoformat(r['Datetime'])+timedelta(minutes=15)).isoformat()+'+03:00'
                assert previous is None or at>previous;previous=at
                if at<'2026-10-13T00:00:00+03:00':
                    rawcov[s,at[:7]].append(at)
                    rawprices[s,at]=tuple(r[k] for k in ['Open','High','Low','Close'])
                if s=='USDRUBF' and r['Datetime'] in ('2023-01-25 17:30:00','2023-01-25 17:45:00','2023-01-26 09:00:00','2023-01-26 09:15:00'):example_bars[r['Datetime']]=r
    for r in read(out/'COVERAGE.csv'):
        stamps=rawcov[r['instrument'],r['month']];assert len(stamps)==int(r['bars'])
        assert (stamps[0] if stamps else '')==r['first_close']
        assert (stamps[-1] if stamps else '')==r['last_close'];checks['raw_coverage_rows']+=1
    yearly=read(out/'YEARLY_COMPARISON.csv');instrument=read(out/'INSTRUMENT_MATRIX.csv');monthly=read(out/'MONTHLY_MATRIX.csv')
    assert len(yearly)==255 and len(instrument)==3060 and len(monthly)==2346
    annual_idx={(r['build_id'],r['year']):r for r in yearly}
    inst_idx={(r['build_id'],r['instrument'],r['direction'],r['year']):r for r in instrument}
    month_idx={(r['build_id'],r['month']):r for r in monthly}
    canonical_trades=[];ledger_count=0;carry=0;stop_count=0
    for b in builds:
        bid=b['build_id'];folder=src/'journals'/bid
        trades=read(folder/'trades.csv.gz');terminal=read(folder/'OPEN.csv.gz')
        assert len({(r['instrument'],r['trade_id']) for r in trades})==len(trades)
        assert len({(r['instrument'],r.get('signal_time') or r['entry_time']) for r in trades})==len(trades)
        assert not {(r['instrument'],r['trade_id']) for r in terminal}&{(r['instrument'],r['trade_id']) for r in trades}
        assert {r['direction'] for r in trades}=={'LONG','SHORT'}
        for r in trades:
            assert r['instrument'] in SYMS and r['build_id']==bid
            assert r['entry_time']<=r['exit_time']<'2026-10-13T00:00:00+03:00'
            sig=r.get('signal_time') or r['entry_time'];assert r['H1AvailableAt']<=sig
            if b['execution_model']=='NEXT_OPEN':
                execution_close=(datetime.fromisoformat(sig)+timedelta(minutes=15)).isoformat()
                same(rawprices[r['instrument'],execution_close][0],r['entry_price'],(bid,'raw_next_open'))
                same(rawprices[r['instrument'],sig][3],r['signal_close'],(bid,'raw_signal_close'))
            else:same(rawprices[r['instrument'],sig][3],r['entry_price'],(bid,'raw_close_entry'))
            checks['source_fill_checks']+=1
            risk=abs(D(r['entry_price'])-D(r['initial_stop']));same(risk,r['initial_risk'],(bid,'risk'))
            side=1 if r['direction']=='LONG' else -1
            same(side*(D(r['exit_price'])-D(r['entry_price']))/risk,r['gross_R'],(bid,'trade_R'))
            if b['initial_stop_id']=='2ATR':same(2*D(r['ATR']),r['initial_risk'],(bid,'2ATR'))
            carry+=r['entry_time'][:4]!=r['exit_time'][:4]
        ledger_count+=len(trades)
        if bid=='A6_S1_NEXT_OPEN_TRAIL_375':canonical_trades=trades
        for y in ['2023','2024','2025','2026','ALL']:
            months=CAL if y=='ALL' else [m for m in CAL if m[:4]==y]
            rr=[r for r in trades if y=='ALL' or r['exit_time'][:4]==y]
            target=annual_idx[bid,y];calc=compute(rr,months)
            for key,v in calc.items():same(v,target[key],(bid,y,key))
            begin=('2023-01-01' if y=='ALL' else y+'-01-01')+'T00:00:00+03:00'
            end=('2026-10-13' if y in ('2026','ALL') else str(int(y)+1)+'-01-01')+'T00:00:00+03:00'
            for boundary,key in [(begin,'OPEN_at_start'),(end,'OPEN_at_end')]:
                count=sum(r['entry_time']<boundary<=r['exit_time'] for r in trades)+sum(r['entry_time']<boundary for r in terminal)
                assert count==int(target[key]),(bid,y,key,count,target[key]);checks['open_boundaries']+=1
            assert int(target['inherited_CLOSED'])==sum(r['entry_time']<begin for r in rr)
            for s in SYMS:
                for direction in ['BOTH','LONG','SHORT']:
                    rr2=[r for r in rr if r['instrument']==s and (direction=='BOTH' or r['direction']==direction)]
                    calc2=compute(rr2,months);t=inst_idx[bid,s,direction,y]
                    for key,v in calc2.items():same(v,t[key],(bid,s,direction,y,key))
                    covered=sum(bool(rawcov[s,m]) for m in months)
                    assert covered==int(t['covered_months'])
                    assert int(t['zero_covered_months'])==calc2['zero_months']-(len(months)-covered)
                    checks['instrument_rows']+=1
            same(sum(D(inst_idx[bid,s,'BOTH',y]['gross_R']) for s in SYMS),target['gross_R'],(bid,y,'instrument_sum'))
            same(sum(D(month_idx[bid,m]['gross_R'] or '0') for m in months),target['gross_R'],(bid,y,'month_sum'))
            checks['yearly_rows']+=1
        for m in CAL:
            rr=[r for r in trades if r['exit_time'][:7]==m];t=month_idx[bid,m]
            no=not any(rawcov[s,m] for s in SYMS)
            assert (t['coverage']=='NO_COVERAGE')==no
            assert (t['gross_R']=='')==no
            same(sum((D(r['gross_R']) for r in rr),D(0)),t['gross_R'] or '0',(bid,m,'monthly_R'))
            assert len(rr)==int(t['CLOSED']);checks['monthly_rows']+=1
        # Source execution journals: validate accepted decisions and Stop chronology.
        if b['execution_model']=='NEXT_OPEN':
            for e in read(folder/'entries.csv.gz'):
                if e['entry_accepted']!='True':continue
                assert e['execution_open_time']==e['signal_time']
                assert datetime.fromisoformat(e['execution_bar_close'])-datetime.fromisoformat(e['signal_time'])==timedelta(minutes=15)
                if b['entry_filter_id']=='A6':assert D(e['H1ATRRatio'])>D(e['H1PreviousATRRatio'])
                if b['entry_filter_id']=='T1':
                    at=datetime.fromisoformat(e['signal_time']);assert 600<=at.hour*60+at.minute<1080
                checks['accepted_next_open_entries']+=1
            prior={}; positions={(r['instrument'],r['trade_id']):r for r in trades+terminal}
            with gzip.open(folder/'stops.csv.gz','rt') as f:
                for r in csv.DictReader(f):
                    key=r['instrument'],r['trade_id'];q=positions[key];side=1 if q['direction']=='LONG' else -1
                    bar=rawprices[r['instrument'],r['bar_close_time']]
                    for k,val in zip(['open','high','low'],bar[:3]):same(val,r[k],(bid,'raw_stop_bar',k))
                    same(r['active_stop'],prior.get(key,q['initial_stop']),(bid,key,'active_stop_continuity'))
                    if r['phase']=='SURVIVED':
                        assert r['stop_hit']=='False'
                        assert side*(D(r['active_stop_next_bar'])-D(r['active_stop']))>=0
                        if r['threshold_activated_now']=='True':
                            assert r['activation_time_after']==r['bar_close_time'] and D(r['favorable_R_after'])>=1
                        prior[key]=r['active_stop_next_bar']
                    else:assert r['stop_hit']=='True' and not r['active_stop_next_bar']
                    stop_count+=1
    # Source #513 trades, pinned Git object, all common fields without copying ledger.
    originpath='IntradayLab/t3_m15_a6_s1_true_oos_2026_ytd_v1/results/primary/trades.csv'
    old=list(csv.DictReader(io.StringIO(git(srcroot,'show',PR513+':'+originpath).decode())))
    bykey={(r['instrument'],r['trade_id']):r for r in canonical_trades};assert len(old)==len(bykey)==1026
    for r in old:
        q=bykey[r['instrument'],r['trade_id']]
        for k in r:
            assert k in q
            if r[k]!=q[k]:
                try:same(r[k],q[k],('PR513',k))
                except Exception:raise AssertionError(('PR513',k,r[k],q[k]))
            checks['PR513_common_fields']+=1
    example=json.loads((out/'EXECUTION_EXAMPLE.json').read_text())
    assert len(example_bars)==4
    no=example['A6_S1_NEXT_OPEN_TRAIL_3p5'];sc=example['A6_S1_SIGNAL_CLOSE_TRAIL_3p5']
    same(example_bars['2023-01-25 17:30:00']['Close'],sc['entry_price'],'historical_signal_close')
    same(example_bars['2023-01-25 17:45:00']['Open'],no['entry_price'],'historical_next_open')
    for row in example['stop_sequence']:
        stamp=datetime.fromisoformat(row['bar_open_time']).strftime('%Y-%m-%d %H:%M:%S')
        for k in ['Open','High','Low']:same(example_bars[stamp][k],row[k.lower()],('example',stamp,k))
    c=[annual_idx['A6_S1_NEXT_OPEN_TRAIL_375',y] for y in ['2023','2024','2025','2026']]
    for r,pf in zip(c,['2.207278','1.772134','1.581308','2.062109']):assert abs(D(r['gross_PF'])-D(pf))<D('0.0000005')
    a=annual_idx['A6_S1_NEXT_OPEN_TRAIL_375','ALL'];assert (a['positive_months'],a['covered_months'])==('35','45')
    for r in read(out/'MONTHLY_CONTRIBUTIONS.csv'):
        rr=read(src/'journals'/r['build_id']/'trades.csv.gz')
        vals=[]
        for s,alias in zip(SYMS,['Si','CNY','GD','MIX']):
            val=sum((D(t['gross_R']) for t in rr if t['instrument']==s and t['exit_time'][:7]==r['month']),D(0))
            same(val,r[alias+'_gross_R'] or '0',('contributions',r['build_id'],r['month'],s));vals.append(val)
        same(sum(vals,D(0)),r['N4_gross_R'] or '0','contribution_sum')
        # Use source float/f-sum signs for exact tiny month sign conventions.
        g=sum(v for v in vals if v>0);l=-sum(v for v in vals if v<0)
        assert (r['compensated_losses']=='True')==(g>l>0)
        checks['contribution_rows']+=1
    source_rank=read(src/'STABILITY_RANKING.csv');summary=read(out/'BUILD_SUMMARY.csv')
    assert [r['build_id'] for r in summary]==[r['build_id'] for r in source_rank]
    for r,z in zip(summary,source_rank):
        for k in z:assert r[k]==z[k],('unchanged_source_ranking',k)
    # CSV summary, roadmap annual criterion and status completion.
    for b in builds:
        r=next(r for r in summary if r['build_id']==b['build_id']);a=annual_idx[b['build_id'],'ALL']
        for k in ['OPEN_at_end','win_rate','mean_win_R','mean_loss_R','negative_months']:same(r[k],a[k],('summary',k))
        passing=all(D(annual_idx[b['build_id'],y]['gross_PF'])>=D('1.70') for y in ['2023','2024'])
        assert (b['annual_PF_170_2023_2024']=='True')==passing
        checks['catalog_summary_rows']+=1
    # Data and source trees were read-only; report generated from fixed source.
    assert not git(data,'status','--porcelain','--','forever').strip()
    assert not git(srcroot,'status','--porcelain','--',SOURCE_DIR).strip()
    report=(out/'REPORT_RU.md').read_text();assert 'WF_MIXED' in report and 'SIGNAL_CLOSE' in report and 'GROSS_ONLY' in report
    # Mark only completed independent reporting checks; source/external status distinct.
    for name,column in [('BUILD_CATALOG.csv','audit_status'),('TEST_STATUS.csv','AUDITED')]:
        data_rows=read(out/name)
        for r in data_rows:r[column]=r[column].replace('INDEPENDENT_REPORT_ARITHMETIC_CHECK_REQUIRED','INDEPENDENT_REPORT_ARITHMETIC_PASS')
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,list(data_rows[0]),lineterminator='\n');w.writeheader();w.writerows(data_rows)
    audit=dict(status='PASS',scope='Independent arithmetic of existing FULL N4 ledgers; no trading replay',base_main=MAIN,source_commit=PIN,data_pin=DATA,unique_builds=51,NEXT_OPEN=13,SIGNAL_CLOSE=38,closed_ledger_records_across_builds=ledger_count,cross_year_closed_records=carry,stop_rows_verified=stop_count,checks=dict(checks),max_numeric_delta=str(max_delta),tolerance='1e-8',PR513_exact_commit=PR513,PR513_trades_exact_common_fields='PASS',canonical_yearly_PF='PASS',canonical_positive_months='35/45',source_code_spec_origins='102/102 PASS',raw_source_sha256=raw_sha,original_artifacts_unchanged='PASS',independence='Separate standard-library/Decimal implementation; does not import generator or research engine/metrics; same reporting author; external review pending',external_review='PENDING',new_trading_replay=False,new_optimization=False,new_rules=False,source_limitations=['GROSS_ONLY; actual costs, funding, spread, slippage not included','No common capital, margin, sizing or MTM portfolio model','NEXT_OPEN boundary zero-latency OHLC model, not robot execution approval','Source session completeness not independently exchange-certified','GLD/MIX late starts 2023; Si/CNY end Aug2026; GLD/MIX end Sep2026','2023/2024 DEVELOPMENT_EXPOSED; original TRAIL375 WF_MIXED; new ranking OOS_NOT_PROVEN'],findings=[{'id':'REGISTRY_ROWS','type':'CLARIFICATION','detail':'73 source rows = 51 unique builds + 17 NOT_TESTED + 5 DIAGNOSTIC_ONLY.'},{'id':'RULE_DEFINITIONS','type':'MISSING_SOURCE_FILE','detail':'RULE_DEFINITIONS.csv absent at PR514 pinned HEAD; provided from executable definitions.'},{'id':'MONTH_DENOMINATOR','type':'CLARIFICATION','detail':'CONTROL 35/45 observed; 35/46 calendar is a different denominator. NO_COVERAGE shown as blank, not zero.'},{'id':'COVERAGE_FLAGS','type':'REPORTING_CORRECTION_ONLY','detail':'Upstream marks GD/MIX Aug2026 incomplete endpoint despite Sep endpoint; per-instrument flag now derives from actual endpoints. No Gross R changes.'},{'id':'WF_COHORT','type':'CLARIFICATION','detail':'2025 full calendar 300 CLOSED PF1.581308 versus new-entry cohort 299 CLOSED PF1.563150; preserved, not a discrepancy.'}],output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('AUDIT.json','REPRODUCIBILITY.json','PUBLICATION.json')})
    (out/'AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['status','closed_ledger_records_across_builds','cross_year_closed_records','stop_rows_verified','checks','max_numeric_delta']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--data-root',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();run(a.source_root.resolve(),a.data_root.resolve(),a.output.resolve())
