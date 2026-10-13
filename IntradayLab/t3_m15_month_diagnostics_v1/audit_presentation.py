"""Read human tables independently and reconcile every displayed source cell."""
import argparse,csv,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent

def run(source,output):
    text=(source/'REPORT.md').read_text()+(source/'MONTHLY_DETAIL.md').read_text()
    inventory=json.loads((source/'REPORT_TABLES.json').read_text());cells=0;numeric=0;counts={}
    for table in inventory:
        name=table['source']
        if name not in counts:
            with (source/name).open() as f:counts[name]=list(csv.DictReader(f))
        raw=[line.strip().strip('|').split('|') for line in table['markdown'].splitlines()]
        assert len(raw)==len(table['rows'])+2
        assert table['markdown'] in text,('MISSING_HUMAN_TABLE',name)
        for row,printed in zip(table['rows'],raw[2:]):
            assert any(all(candidate[k]==str(v) for k,v in row.items()) for candidate in counts[name]),('NON_SOURCE_ROW',name,row)
            for (field,label,kind),cell in zip(table['columns'],printed):
                cell=cell.strip();value=row[field];cells+=1
                if kind=='s':assert cell==(value if value else '—')
                elif not value:assert cell=='—'
                else:
                    x=float(value);numeric+=1
                    if kind=='i':assert int(cell)==int(x) and int(x)==x
                    elif kind=='p':assert cell.endswith('%') and abs(float(cell[:-1])-100*x)<=.05000000001
                    else:assert abs(float(cell)-x)<=.00005000001
    # Report must contain the full 24-month portfolio table, not just focus months.
    assert any(t['source']=='monthly.csv' and len(t['rows'])==24 and 'R_LONG' in t['rows'][0] for t in inventory)
    result={'status':'PASS','human_tables':len(inventory),'source_cells_checked':cells,'numeric_cells_checked':numeric,'table_sources':sorted(counts),'independent_scalar_CSV_audit_required':True}
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=HERE/'results');p.add_argument('--output',type=Path,default=HERE/'audit/PRESENTATION_AUDIT.json');a=p.parse_args();run(a.source,a.output)
