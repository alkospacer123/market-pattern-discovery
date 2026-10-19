"""Fix N4 report identity validation, preserving every source row and all economics."""
import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
from .. import report, study


def n4_comparison(out):
    source=study.ROOT/'TradingSystemLab/results/post_v3_analysis/stage6_unified_candidate_comparison/portfolio_trade_scaling_registry.csv'
    assert study.sha(source)=='8f0493f5dd4edf087881622005efde0531c6146903a38c362e72dbc508071b1e'
    n=pd.read_csv(source)
    n=n[(n.variant=='TRAIL1') & n.instrument.isin(['USDRUBF','CNYRUBF','GLDRUBF','IMOEXF']) & n.lifecycle.isin(['baseline','historical_true_oos'])].copy()
    assert len(n)==355
    assert not n[['lifecycle','source_trade_id']].duplicated().any()
    n['exit']=pd.to_datetime(n.exit_time,utc=True).dt.tz_convert('Europe/Moscow')
    s=pd.read_csv(out/'all_trades.csv')
    s['exit']=pd.to_datetime(s.exit_time,utc=True).dt.tz_convert('Europe/Moscow')
    endpoint=pd.Timestamp('2026-09-15 21:00:00',tz='UTC').tz_convert('Europe/Moscow')
    rows=[]
    for year in [2024,2025,2026]:
        start=pd.Timestamp(f'{year}-01-01',tz='Europe/Moscow')
        end=min(pd.Timestamp(f'{year+1}-01-01',tz='Europe/Moscow')-pd.Timedelta(nanoseconds=1),endpoint)
        for label,g,r_column in [('N4_NORMALIZED_C1',n,'strategy_R'),('SBER_LONG_SHORT_C1',s[s.scenario=='LONG_SHORT_C1'],'net_R'),('SBER_LONG_ONLY_C1',s[s.scenario=='LONG_ONLY_C1'],'net_R')]:
            order=['exit','source_trade_id','lifecycle'] if 'source_trade_id' in g else ['exit','trade_id']
            g=g[(g.exit>=start)&(g.exit<=end)].sort_values(order,kind='stable')
            x=g[r_column];curve=pd.concat([pd.Series([0.]),x.reset_index(drop=True).cumsum()],ignore_index=True)
            rows.append({'series':label,'year':year,'window_start':start,'window_end':end,'trades':len(g),
                         'normalized_net_PF':float(x[x>0].sum()/-x[x<0].sum()) if (x<0).any() else None,
                         'normalized_net_R':float(x.sum()),'max_closed_R_DD':float((curve-curve.cummax()).min()),
                         'comparison_scope':'same nominal normalized C1 only; different assets/scales and basket breadth; no capital-return ranking'})
    result=pd.DataFrame(rows)
    study.write_csv(out/'n4_same_window.csv',result)
    # Separate stdlib check against the original N4 CSV, without using dataframe filtering.
    with source.open() as f: original=list(csv.DictReader(f))
    errors=[]
    for r in rows:
        if r['series']!='N4_NORMALIZED_C1':continue
        values=[]
        for v in original:
            if v['variant']!='TRAIL1' or v['instrument'] not in ('USDRUBF','CNYRUBF','GLDRUBF','IMOEXF') or v['lifecycle'] not in ('baseline','historical_true_oos'):continue
            t=datetime.fromisoformat(v['exit_time'])
            if r['window_start'].to_pydatetime()<=t<=r['window_end'].to_pydatetime(warn=False):values.append(float(v['strategy_R']))
        if len(values)!=r['trades'] or abs(sum(values)-r['normalized_net_R'])>1e-9:errors.append(str(r['year']))
    study.write_json(out/'n4_report_audit.json',{'status':'FAIL' if errors else 'PASS','errors':errors,
        'source_rows_retained':len(n),'duplicate_bare_ids':int(n.source_trade_id.duplicated().sum()),
        'duplicate_lifecycle_ids':0,'source_sha256':study.sha(source),'main_sha':study.MAIN,
        'correction':'Bare IDs restart per lifecycle. Use (lifecycle, source_trade_id); no deduplication or economics changes.'})
    assert not errors
    return result


if __name__=='__main__':
    frozen=report.HERE/'FREEZE.json'
    import json
    identity=json.loads(frozen.read_text())['setup_hashes']
    report_path=str(Path(report.__file__).relative_to(study.ROOT))
    assert identity[report_path]==study.sha(report.__file__)
    report.n4_comparison=n4_comparison
    report.render()
