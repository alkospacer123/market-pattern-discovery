"""Fresh presentation audit: Markdown cells, decision identities, literal claims."""
import argparse,csv,json,hashlib
from pathlib import Path
def read(p):
 with p.open() as f:return list(csv.DictReader(f))
def audit(out):
 report=(out/'REPORT_RU.md').read_text();trace=json.loads((out/'REPORT_TABLES.json').read_text());actual=[];block=[]
 for line in report.splitlines()+['']:
  if line.startswith('| '):block.append([x.strip() for x in line.strip().strip('|').split('|')])
  elif block:
   assert all(x=='---' for x in block[1]);actual.append(dict(headers=block[0],rows=block[2:]));block=[]
 assert actual==trace,'MARKDOWN_TABLE_CELLS_CHANGED'
 ranks=[r for r in read(out/'STABILITY_RANKING.csv') if r['mode']=='NEXT_OPEN'];d=json.loads((out/'DECISION.json').read_text())
 assert d['most_regular_N4']==min(ranks,key=lambda r:int(r['rank']))['build_id']
 assert d['highest_Gross_PF_N4']==max(ranks,key=lambda r:float(r['gross_PF']))['build_id']
 assert d['highest_Gross_R_N4']==max(ranks,key=lambda r:float(r['gross_R']))['build_id']
 qualified=[r for r in ranks if r['annual_minimum_2023_2024']=='True'];assert d['best_compromise_N4']==min(qualified,key=lambda r:int(r['rank']))['build_id']
 assert d['overall']=='NO_ROBUST_WINNER' and 'POST_HOC_COMPARISON' in report
 assert not d['automatic_parameter_or_composition_change']
 claims=[('A6_S1_NEXT_OPEN_TRAIL_3625','PF_2024','1,648640'),('A6_S1_NEXT_OPEN_TRAIL_375','gross_PF','1,845936'),('A6_S1_NEXT_OPEN_TRAIL_375','gross_R','418,142777'),('A6_S1_NEXT_OPEN_TRAIL_3875','gross_R','420,015962')]
 for bid,col,value in claims:
  row=next(r for r in ranks if r['build_id']==bid);assert f'{float(row[col]):.6f}'.replace('.',',')==value and value in report
 months=[r for r in read(out/'MONTHLY_COMPARISON.csv') if r['build_id']=='A6_S1_NEXT_OPEN_TRAIL_375' and r['view']=='FULL_AVAILABLE']
 n2={r['month']:float(r['gross_R']) for r in months if r['instruments']=='USDRUBF;CNYRUBF'};n4={r['month']:float(r['gross_R']) for r in months if r['instruments']=='USDRUBF;CNYRUBF;GLDRUBF;IMOEXF'}
 assert [m for m in n2 if n2[m]<0 and n4[m]>0]==['2024-03','2024-04','2024-07','2025-08','2026-04']
 assert [m for m in n2 if n2[m]>0 and n4[m]<=0]==['2025-01']
 result=dict(status='PASS',markdown_tables=len(actual),markdown_cells=sum(len(t['headers'])+sum(map(len,t['rows'])) for t in actual),decision_identities='PASS',key_narrative_numeric_claims='PASS',N2_N4_month_flip_claims='PASS',human_narrative_review='PENDING',report_sha256=hashlib.sha256((out/'REPORT_RU.md').read_bytes()).hexdigest())
 (out/'PRESENTATION_AUDIT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.output)
