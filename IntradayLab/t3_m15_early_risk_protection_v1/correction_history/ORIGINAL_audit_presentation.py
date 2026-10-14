"""Every rendered Markdown table and decision JSON checked against scalar output."""
import argparse,json,math
from pathlib import Path
import common as C

def check(primary,audit):
    d=json.loads((audit/'TABLES.json').read_text());decision=json.loads((primary/'DECISION.json').read_text());summary=d['summary'];effects=d['effect_summary'];cohort=d['cohort32'];trades=d['trade_comparison']
    def s(v,y):return next(r for r in summary if (r['variant'],r['scope'],r['direction'],r['year'])==(v,'ALL_FOUR','ALL',y))
    e=next(r for r in effects if (r['scope'],r['direction'],r['year'])==('ALL_FOUR','ALL','ALL'))
    reasons=[]
    for y in ['2023','2024']:
        if s('EARLY_PROTECT_05',y)['gross_PF']<s('CONTROL',y)['gross_PF']-1e-8:reasons.append('PF ухудшился в '+y)
        if s('EARLY_PROTECT_05',y)['positive_months']<s('CONTROL',y)['positive_months']:reasons.append('меньше прибыльных месяцев в '+y)
    if s('EARLY_PROTECT_05','ALL')['positive_months']<s('CONTROL','ALL')['positive_months']:reasons.append('месячная регулярность ухудшилась за полный период')
    expected={'decision':'NEGATIVE_RESULT_REJECT_EARLY_PROTECT_05' if reasons else 'REVIEW_REQUIRED_FOR_TREND_DAMAGE_NO_AUTOMATIC_ACCEPTANCE','reasons':reasons,'roadmap_annual_minimum_met':all(s('EARLY_PROTECT_05',y)['gross_PF']>=1.7 for y in ['2023','2024']),'preferred_annual_PF_gt2_met':all(s('EARLY_PROTECT_05',y)['gross_PF']>2 for y in ['2023','2024']),'control_causal_cohort32':sum(r['control_causal_available'] for r in cohort),'actual_causal_cohort32':sum(r['actual_causal_available'] for r in cohort),'cohort32_loss_reduced':sum(r['loss_reduced'] for r in cohort),'effects_all':e,'new_threshold_or_next_variant':False,'status':C.LABEL,'years':'2023–2024 DEVELOPMENT_EXPOSED'}
    cmp=C.Comparison();assert expected.keys()==decision.keys()
    cmp.rows([e],[decision['effects_all']],'DECISION_EFFECTS',['scope','direction','year'])
    # Nested effects have separately compared 45 independent effect-summary rows.
    for k in expected:
        if k not in ('effects_all',):
            if isinstance(expected[k],list):assert expected[k]==decision[k]
            else:cmp.value(expected[k],decision[k],'decision_scalar',0,k)
    threshold=[{'threshold_R':n,**{k[len(f'GE{n}_'):]:v for k,v in e.items() if k.startswith(f'GE{n}_')}} for n in [2,5]]
    attribution=[]
    for cs,xs in sorted({(r['control_status'],r['experiment_status']) for r in trades}):
        rows=[r for r in trades if r['control_status']==cs and r['experiment_status']==xs]
        attribution.append(dict(control_status=cs,experiment_status=xs,entries=len(rows),booked_delta_R=math.fsum(r['booked_delta_R'] for r in rows)))
    months=[]
    for m in C.CALENDAR:
        get=lambda v:next(r for r in d['monthly'] if (r['variant'],r['scope'],r['direction'],r['month'])==(v,'ALL_FOUR','ALL',m))
        c=get('CONTROL');x=get('EARLY_PROTECT_05');months.append(dict(month=m,control_R=c['gross_R'],experiment_R=x['gross_R'],delta_R=x['gross_R']-c['gross_R'],control_PF=c['gross_PF'],experiment_PF=x['gross_PF'],control_closed=c['closed'],experiment_closed=x['closed']))
    expected_tables=[[s(v,y) for y in ['2023','2024','ALL'] for v in ['CONTROL','EARLY_PROTECT_05']],[e],threshold,[e],attribution,[s(v,'2024') for v in ['CONTROL','EARLY_PROTECT_05']],months,[r for r in summary if r['year']!='ALL' and ((r['scope']=='ALL_FOUR' and r['direction']!='ALL') or (r['scope']!='ALL_FOUR' and r['direction']=='ALL'))],summary,effects]
    found=[]
    for filename in ['REPORT.md','DETAIL.md']:
        lines=(primary/filename).read_text().splitlines();i=0
        while i<len(lines):
            if lines[i].startswith('| ') and i+1<len(lines) and lines[i+1].startswith('| ---'):
                fields=[v.strip() for v in lines[i].strip('|').split('|')];rows=[];i+=2
                while i<len(lines) and lines[i].startswith('| '):rows.append([v.strip() for v in lines[i].strip('|').split('|')]);i+=1
                found.append((filename,fields,rows))
            else:i+=1
    assert len(found)==len(expected_tables)
    cells=0
    for ti,((filename,fields,rows),exp) in enumerate(zip(found,expected_tables)):
        assert len(rows)==len(exp),(filename,ti,'ROW_COUNT')
        for i,(actual,truth) in enumerate(zip(rows,exp)):
            assert len(actual)==len(fields)
            for k,v in zip(fields,actual):
                value=truth[k];expected_value='—' if value is None else format(value,'.6f') if isinstance(value,float) else str(value)
                cmp.value(v,expected_value,filename+'_'+str(ti),i,k);cells+=1
    result={'status':'PASS' if not cmp.diffs else 'FAIL','tables':len(found),'cells':cells,'differences':len(cmp.diffs),'decision_checked_against_scalar':True,'booked_delta_checked':abs(math.fsum(r['booked_delta_R'] for r in trades)-(s('EARLY_PROTECT_05','ALL')['gross_R']-s('CONTROL','ALL')['gross_R']))<1e-8}
    C.write_json(audit/'PRESENTATION_AUDIT.json',result);C.write_csv(audit/'PRESENTATION_DIFFERENCES.csv',cmp.diffs,['table','row','field','actual','expected']);assert not cmp.diffs and result['booked_delta_checked'];print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--primary',type=Path,default=C.HERE/'results');p.add_argument('--audit',type=Path,default=C.HERE/'audit');a=p.parse_args();check(a.primary,a.audit)
