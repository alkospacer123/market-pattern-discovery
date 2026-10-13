"""Post-run disclosure only from sealed CSV/JSON. No raw reads or model changes.

Aggregates already preregistered marked-R and execution/carry disclosures. Output
is separately compared across both full repeat directories; replay code frozen.
"""
import argparse,csv,json,hashlib,math
from datetime import datetime,timedelta
from pathlib import Path

def rows(p):
    with p.open() as f:return list(csv.DictReader(f))
def save(output,name,data):
    (output/(name+'.json')).write_text(json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    fields=list(dict.fromkeys(k for r in data for k in r))
    with (output/(name+'.csv')).open('w',newline='') as f:
        w=csv.DictWriter(f,fields,lineterminator='\n');w.writeheader();w.writerows(data)
def run(root,output):
    output.mkdir(parents=True,exist_ok=True);last=root/'results/W4';tables=json.loads((last/'TABLES.json').read_text())
    output_data=[]
    calendar=[f'2025-{m:02d}' for m in range(1,13)]
    for period,months in [('FULL_WF',calendar)]+[(f'W{i+1}',calendar[i*3:i*3+3]) for i in range(4)]:
        for scope in ('ALL_FOUR','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
            for side in ('ALL','LONG','SHORT'):
                seq=[r for r in tables['marked_monthly'] if r['month'] in months and r['scope']==scope and r['direction']==side]
                realized=math.fsum(r['CLOSED_R'] for r in seq);marked=math.fsum(r['marked_R'] for r in seq)
                assert abs(marked-(realized+seq[-1]['U_end_R']-seq[0]['U_start_R']))<1e-8
                output_data.append({'period':period,'scope':scope,'direction':side,'CLOSED_R':realized,'U_start_R':seq[0]['U_start_R'],'U_end_R':seq[-1]['U_end_R'],
                    'marked_R':marked,'marked_positive_months':sum(r['marked_R']>0 for r in seq),'marked_negative_months':sum(r['marked_R']<0 for r in seq),
                    'marked_zero_months':sum(r['marked_R']==0 for r in seq),'CLOSED_positive_months':sum(r['CLOSED_R']>0 for r in seq),'CLOSED_negative_months':sum(r['CLOSED_R']<0 for r in seq),
                    'CLOSED_zero_months':sum(r['CLOSED_R']==0 for r in seq),'months':len(months),'OPEN_start':seq[0]['OPEN_start'],'OPEN_end':seq[-1]['OPEN_end'],'capital_return':False})
    save(output,'MARKED_SUMMARY',output_data)
    staleness=[]
    for label in ('CONTROL','W1','W2','W3','W4'):
        checkpoint=json.loads((root/'results'/label/'CHECKPOINT.json').read_text());end=datetime.fromisoformat(checkpoint['end_exclusive'])
        for r in checkpoint['OPEN']:
            staleness.append({'boundary':label,'cutoff':end.isoformat(),'trade_id':r['trade_id'],'instrument':r['instrument'],'direction':r['direction'],
                'last_allowed_close':r['last_close'],'mark_staleness_hours':(end-datetime.fromisoformat(r['last_close'])).total_seconds()/3600,
                'entry_time':r['entry_time'],'initial_risk':r['initial_risk'],'active_stop':r['active_stop'],'S1_activated':r['threshold_activated'],
                'activation_time':r['activation_time'],'favorable_extreme':r['favorable_extreme'],'marked_R':r['unrealized_gross_R_at_last_close'],
                'pending_signal_IDs':','.join(q['trade_id'] for q in checkpoint['pending'] if q['instrument']==r['instrument'])})
    save(output,'OPEN_STALENESS',staleness)
    entries=rows(last/'primary/entry_opportunities.csv');counts=[]
    for month in calendar:
        for scope in ('ALL_FOUR','USDRUBF','CNYRUBF','GLDRUBF','IMOEXF'):
            for side in ('ALL','LONG','SHORT'):
                e=[r for r in entries if r['signal_time'][:7]==month and (scope=='ALL_FOUR' or r['instrument']==scope) and (side=='ALL' or r['direction']==side)]
                counts.append({'month':month,'scope':scope,'direction':side,'original_signals':len(e),
                  'A6_pass':sum(r['rule_pass']=='True' for r in e),'position_busy':sum(r['position_occupied']=='True' for r in e),
                  'executed_NEXT_OPEN':sum(r['entry_accepted']=='True' for r in e),
                  'skipped_missing_adjacent_open':sum(r['decision_reason']=='SKIPPED_MISSING_ADJACENT_OPEN' for r in e),
                  'unresolved_end_pending':sum(r['decision_reason']=='UNRESOLVED_END_OF_DATA' for r in e)})
    save(output,'EXECUTION_COUNTS',counts)
    summary=tables['summary'];full=next(r for r in summary if r['period']=='FULL_WF' and r['cohort']=='CALENDAR_CLOSED' and r['scope']=='ALL_FOUR' and r['direction']=='ALL')
    cohort=next(r for r in summary if r['period']=='FULL_WF' and r['cohort']=='NEW_WF_COHORT' and r['scope']=='ALL_FOUR' and r['direction']=='ALL')
    declared=json.loads((last/'DECISION.json').read_text())['status']
    insufficient=len(tables['coverage'])!=48 or any(r['status']!='AVAILABLE' for r in tables['coverage']) or any(not r['closed'] or r['gross_PF'] is None for r in [full,cohort])
    gross_bad=any(r['gross_R']<=0 or (r['gross_PF'] is not None and r['gross_PF']<=1) or (r['expectancy_R'] is not None and r['expectancy_R']<=0) for r in [full,cohort])
    negative=[r for r in summary if r['period'] in ('FULL_WF','W1','W2','W3','W4') and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT') and r['closed']>0 and r['gross_R']<=0]
    negative+= [r for r in tables['scenario_summary'] if r['period'] in ('FULL_WF','W1','W2','W3','W4') and r['cohort'] in ('CALENDAR_CLOSED','NEW_WF_COHORT') and r['original_CLOSED']>0 and r['gross_R']<=0]
    expected='WF_INSUFFICIENT_EVIDENCE' if insufficient else 'WF_GROSS_EDGE_NOT_CONFIRMED' if gross_bad else 'WF_MIXED' if negative else 'WF_REVIEW_REQUIRED'
    assert expected==declared
    evidence={'status':'PASS','declared':declared,'recomputed':expected,'criteria_source':'PR511 unchanged','full_calendar':full,'new_WF_cohort':cohort,
        'negative_limiting_cells':len(negative),'no_new_numeric_cutoffs':True,'automatic_WF_PASS':False,'TRUE_OOS_authorized':False,'post_run_role':'presentation/disclosure arithmetic only; sealed replay results untouched'}
    (output/'DECISION_REVIEW.json').write_text(json.dumps(evidence,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    marked=next(r for r in output_data if r['period']=='FULL_WF' and r['scope']=='ALL_FOUR' and r['direction']=='ALL')
    quarters=[next(r for r in summary if r['period']==q and r['cohort']=='CALENDAR_CLOSED' and r['scope']=='ALL_FOUR' and r['direction']=='ALL') for q in ('W1','W2','W3','W4')]
    text=f'''# Итоговое ревью WF 2025 — {declared}

Положительный gross-знак полного календарного WF и новых входов подтверждён в исследовательской модели; регулярность и слабые части неоднородны. Итог **{declared}**, без автоматического PASS или допуска к TRUE OOS.

| Период | CLOSED | OPEN | Gross PF | Gross R |
| --- | --- | --- | --- | --- |
'''
    text+='\n'.join(f"| {r['period']} | {r['closed']} | {r['period_end_OPEN']} | {r['gross_PF']:.6f} | {r['gross_R']:+.6f}R |" for r in [full]+quarters)+'\n'
    text+=f'''
Календарь: **{full['closed']} CLOSED / {full['period_end_OPEN']} OPEN**, PF **{full['gross_PF']:.6f}**, **{full['gross_R']:+.6f}R**, expectancy **{full['expectancy_R']:.6f}R**. Новая WF cohort: **{cohort['closed']} CLOSED / {cohort['period_end_OPEN']} OPEN**, PF **{cohort['gross_PF']:.6f}**, **{cohort['gross_R']:+.6f}R**, expectancy **{cohort['expectancy_R']:.6f}R**. Inherited IMOEXF **+2,713588R** не считается новым входом.

Ограничения: отрицательный W2 **−12,842903R**, 0/3 положительных месяцев; **GLDRUBF SHORT −5,572762R, PF 0,724975**. Год 7/12 положительных CLOSED месяцев, 5 отрицательных, без нулевых. Худший июнь **−12,111285R**; максимальная серия **11 проигрышей** и **4 отрицательных месяца**. CLOSED-R DD **28,637394R**; восстановление 10.09.2025 15:30 MSK, **200,729167 дня** от первого underwater CLOSED. Исторический DD 12,628056R приведён как reference, без fitted cutoff.

Концентрация: сентябрь **42,298813%** годового R; лучшие три месяца (сентябрь, октябрь, декабрь) **80,509708%**. Без top10 победителей остаётся **+4,505390R / PF 1,030146**, без трёх лучших месяцев **+16,932505R / PF 1,145851**. Все четыре full-year leave-one-instrument-out остаются положительными. Это диагностика, инструментов/месяцев/SHORT из первичного результата не исключено.

Фиксированный stress −0,05R/CLOSED: **+71,876613R / PF 1,453618 / DD 33,836047R**; −0,10R/CLOSED: **+56,876613R / PF 1,339503 / DD 39,432673R**. Не реальные FINAM/C1 costs; GROSS_ONLY и COSTS_DEFERRED остаются.

Marked-R отдельно: **{marked['marked_R']:+.6f}R**, **{marked['marked_positive_months']}/12** положительных, **{marked['marked_negative_months']}** отрицательных месяцев. Формула **{marked['CLOSED_R']:+.6f}R + {marked['U_end_R']:.6f}R − {marked['U_start_R']:.6f}R**. Terminal OPEN — USDRUBF LONG T3-M15-Si-000215, вход 30.12.2025 16:15 MSK, initial R 0,3343245512, Stop 78,5856754488, S1 не активирован. Последний разрешённый Close 31.12.2025 00:00 MSK: marked **+0,029911R**, staleness **24 часа** до cutoff. Никаких цен 2026 для отметки/выхода.

MARKED_SUMMARY отделяет CLOSED/marked positive months; OPEN_STALENESS показывает carry на всех квартальных границах; EXECUTION_COUNTS раскрывает signal/A6/busy/skip/pending по месяцу, инструменту и стороне. Полные primary/scalar journals, features, summary/monthly/scenarios/top IDs/recovery/loss runs и русский отчёт — в results/W4. Каждая исходная квартальная seal остаётся неизменной.

Первый DEVELOPMENT-only attempt был остановлен на сериализации служебного checkpoint numpy.int64, до полного CONTROL и любого WF raw-read. Свидетельства сохранены; адаптер исправлен и повторно заморожен до 2025. Нет смены стратегии или параметров. Итоговый CONTROL совпал полностью с #510. Автор один, независимость вычислительная; внешнее человеческое ревью PENDING. Два полных повтора подтверждаются только REPEATABILITY PASS; reporting supplements отдельно сравниваются по bytes/SHA256.

**Один Draft PR; NO MERGE / NO AUTO-MERGE. STOP для независимого аудита и решения пользователя. 2026 TRUE OOS и LIVE не выполнялись. R не доходность капитала.**

DEVELOPMENT_2023_2024_EXPOSED / WF_2025_AUTHORIZED / TRUE_OOS_2026_LOCKED / GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.
'''
    (output/'REVIEW_MEMO_RU.md').write_text(text)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',type=Path,default=Path(__file__).resolve().parent);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();run(a.run_root,a.output)
