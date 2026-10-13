"""Independent scalar checks of presentation supplements and every Markdown cell."""
import argparse,csv,json,math,re
from datetime import datetime
from pathlib import Path
import common as C


def compute(raw):
    trades=[]
    for x in raw:
        r=dict(x)
        for k in ('gross_R','MFE_R','H1ATRRatio'):r[k]=float(r[k])
        for k in ('signal_time','exit_time'):r[k]=datetime.fromisoformat(r[k])
        r['initial_no_s1']=r['exit_type']=='INITIAL_STOP' and r['threshold_activated']=='False'
        r['failed_lower_MFE']=r['gross_R']<0 and r['MFE_R']<.5
        trades.append(r)
    bands=[]
    for year in (2023,2024):
        for side in ('LONG','SHORT'):
            group=[r for r in trades if r['exit_time'].year==year and r['direction']==side]
            for name,lo,hi in [('LT_0_5',0,.5),('0_5_TO_1',.5,1),('1_TO_2',1,2),('GE2_MFE',2,math.inf)]:
                part=[r for r in group if lo<=r['MFE_R']<hi]
                bands.append({'year':year,'direction':side,'MFE_band':name,'closed':len(part),'fraction':len(part)/len(group),'gross_R':math.fsum(r['gross_R'] for r in part),'initial_no_s1':sum(r['initial_no_s1'] for r in part),'losses':sum(r['gross_R']<0 for r in part)})
    focus=[]
    for month in ('2024-05','2024-10'):
        for side in ('ALL','LONG','SHORT'):
            part=[r for r in trades if r['signal_time'].strftime('%Y-%m')==month and (side=='ALL' or r['direction']==side)]
            focus.append({'signal_month':month,'direction':side,'closed':len(part),'gross_R':math.fsum(r['gross_R'] for r in part),'initial_no_s1':sum(r['initial_no_s1'] for r in part),'failed_lower_MFE':sum(r['failed_lower_MFE'] for r in part),'GE2':sum(r['gross_R']>=2 for r in part),'GE5':sum(r['gross_R']>=5 for r in part),'exit_other_month':sum(r['exit_time'].strftime('%Y-%m')!=month for r in part)})
    extreme=[]
    for year in (2023,2024):
        part=[r for r in trades if r['signal_time'].year==year and r['direction']=='SHORT' and r['H1ATRRatio']>=1.25]
        extreme.append({'year':year,'closed':len(part),'gross_R':math.fsum(r['gross_R'] for r in part),'days':len(set(r['signal_time'].date() for r in part)),'months':len(set(r['signal_time'].strftime('%Y-%m') for r in part)),'initial_no_s1':sum(r['initial_no_s1'] for r in part),'S1_activated':sum(r['threshold_activated']=='True' for r in part),'MFE_GE2':sum(r['MFE_R']>=2 for r in part),'GE2':sum(r['gross_R']>=2 for r in part),'GE5':sum(r['gross_R']>=5 for r in part),'may_2024_entries':sum(r['signal_time'].strftime('%Y-%m')=='2024-05' for r in part),'oct_2024_entries':sum(r['signal_time'].strftime('%Y-%m')=='2024-10' for r in part)})
    return {'MFE_bands':bands,'focus_signal_cohorts':focus,'extreme_ratio_SHORT':extreme},trades


def display(v):
    return '—' if v is None else format(v,'.6f') if isinstance(v,float) else str(v)


def run(results,audit):
    assert json.loads((audit/'AUDIT_RESULT.json').read_text())['status']=='PASS'
    supplements,trades=compute(list(csv.DictReader((audit/'replay/trades.csv').open())))
    published=json.loads((results/'REPORT_SUPPLEMENT.json').read_text());cmp=C.Comparison()
    for name,rows in supplements.items():cmp.rows(rows,published[name],'SUPPLEMENT_'+name,['year','direction','MFE_band','signal_month'])
    sources=json.loads((results/'TABLES.json').read_text())|supplements
    manifests=json.loads((results/'REPORT_TABLES.json').read_text());expected={r['id']:r for r in manifests};seen=set();cells=0;rows_count=0
    for name in ('REPORT.md','MONTHLY_DETAIL.md','CUTS_DETAIL.md'):
        lines=(results/name).read_text().splitlines();i=0
        while i<len(lines):
            match=re.fullmatch(r'<!-- table:(T\d+) -->',lines[i])
            if not match:i+=1;continue
            ident=match[1];assert ident not in seen;seen.add(ident);spec=expected[ident]
            assert [s.strip() for s in lines[i+1].strip('|').split('|')]==spec['columns']
            i+=3;actual=[]
            while i<len(lines) and lines[i].startswith('|'):
                actual.append([s.strip() for s in lines[i].strip('|').split('|')]);i+=1
            source=sources[spec['source']];reference=[[display(source[j].get(k)) for k in spec['columns']] for j in spec['indices']]
            assert actual==reference,('MARKDOWN_MISMATCH',name,ident)
            rows_count+=len(actual);cells+=sum(len(row) for row in actual)
    assert seen==set(expected)
    # Specific narrative numbers/reasoning are independently checked from raw scalar replay.
    short=[r for r in trades if r['exit_time'].year==2024 and r['direction']=='SHORT']
    long=[r for r in trades if r['exit_time'].year==2024 and r['direction']=='LONG']
    intermediate=lambda rows:sum(r['initial_no_s1'] and .5<=r['MFE_R']<1 for r in rows)
    checks={'SHORT2024_intermediate_initial_stops':(intermediate(short),32),'LONG2024_intermediate_initial_stops':(intermediate(long),16),'SHORT2023_intermediate_initial_stops':(intermediate([r for r in trades if r['exit_time'].year==2023 and r['direction']=='SHORT']),7),
      'original_GE2':(sum(r['gross_R']>=2 for r in trades),83),'original_GE5':(sum(r['gross_R']>=5 for r in trades),21),'OCT_SHORT_INITIAL':(sum(r['initial_no_s1'] for r in short if r['exit_time'].month==10),8),'MAY_SHORT_RATCHETED_LOSSES':(sum(r['exit_type']=='RATCHETED_STOP' and r['gross_R']<0 for r in short if r['exit_time'].month==5),5),
      'HIGH_RATIO_SHORT_GE2':(sum(r['gross_R']>=2 for r in trades if r['direction']=='SHORT' and r['H1ATRRatio']>=1.25),0),'HIGH_RATIO_OCT_SHORT_ENTRIES':(sum(r['signal_time'].strftime('%Y-%m')=='2024-10' for r in trades if r['direction']=='SHORT' and r['H1ATRRatio']>=1.25),0)}
    for key,(actual,reference) in checks.items():cmp.value(actual,reference,'NARRATIVE',key,'value')
    window_total=next(r['window_censored'] for r in sources['summary'] if r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['year']=='ALL')
    cmp.value(window_total,7,'NARRATIVE','WINDOW_CENSORED','value')
    decision=json.loads((results/'DECISION.json').read_text());assert decision['decision']=='NO_SUPPORTED_ENTRY_CHANGE' and decision['proposed_mechanisms']==0
    C.write_csv(audit/'PRESENTATION_DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected'])
    C.write_json(audit/'CONCLUSION_REVIEW.json',{'status':'PASS' if not cmp.diffs else 'FAIL','checked_narrative_claims':{k:{'actual':a,'expected':r} for k,(a,r) in checks.items()},'supplements_independently_computed_from_scalar_raw_trades':True,'decision':'NO_SUPPORTED_ENTRY_CHANGE','qualitative_evidence_judgment':'same author; exact numerical claims verified; human review pending'})
    result={'status':'PASS' if not cmp.diffs else 'FAIL','tables':len(manifests),'markdown_rows':rows_count,'markdown_cells':cells,'supplement_fields_compared':cmp.fields,'differences':len(cmp.diffs),'max_numeric_delta':max(cmp.maxima.values(),default=0)}
    C.write_json(audit/'PRESENTATION_AUDIT.json',result);assert not cmp.diffs,'PRESENTATION_AUDIT_FAILED';print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=C.HERE/'results');p.add_argument('--audit',type=Path,default=C.HERE/'audit');a=p.parse_args();run(a.results,a.audit)
