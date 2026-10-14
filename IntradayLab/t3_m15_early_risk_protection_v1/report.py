"""Deterministic report of the fixed two-path comparison; no further experiments."""
import argparse,json,math
from pathlib import Path
import common as C

def fmt(v):
    if v is None:return '—'
    if isinstance(v,float):return f'{v:.6f}'
    return str(v)
def table(rows,fields):
    return '| '+' | '.join(fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'+''.join('| '+' | '.join(fmt(r.get(k)) for k in fields)+' |\n' for r in rows)
def render(root):
    data=json.loads((root/'TABLES.json').read_text());summary=data['summary'];effects=data['effect_summary'];cohort=data['cohort32'];comp=data['trade_comparison']
    def s(v,y):return next(r for r in summary if r['variant']==v and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['year']==y)
    a={y:s('CONTROL',y) for y in ['2023','2024','ALL']};b={y:s('EARLY_PROTECT_05',y) for y in ['2023','2024','ALL']}
    e=next(r for r in effects if r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['year']=='ALL')
    reasons=[]
    for year in ['2023','2024']:
        if b[year]['gross_PF']<a[year]['gross_PF']-1e-8:reasons.append('PF ухудшился в '+year)
        if b[year]['positive_months']<a[year]['positive_months']:reasons.append('меньше прибыльных месяцев в '+year)
    if b['ALL']['positive_months']<a['ALL']['positive_months']:reasons.append('месячная регулярность ухудшилась за полный период')
    decision='NEGATIVE_RESULT_REJECT_EARLY_PROTECT_05' if reasons else 'REVIEW_REQUIRED_FOR_TREND_DAMAGE_NO_AUTOMATIC_ACCEPTANCE'
    assessment={'decision':decision,'reasons':reasons,'roadmap_annual_minimum_met':all(b[y]['gross_PF']>=1.7 for y in ['2023','2024']),'preferred_annual_PF_gt2_met':all(b[y]['gross_PF']>2 for y in ['2023','2024']),'control_causal_cohort32':sum(r['control_causal_available'] for r in cohort),'actual_causal_cohort32':sum(r['actual_causal_available'] for r in cohort),'cohort32_loss_reduced':sum(r['loss_reduced'] for r in cohort),'effects_all':e,'new_threshold_or_next_variant':False,'status':C.LABEL,'years':'2023–2024 DEVELOPMENT_EXPOSED'}
    C.write_json(root/'DECISION.json',assessment)
    booked=math.fsum(r['booked_delta_R'] for r in comp);actual=b['ALL']['gross_R']-a['ALL']['gross_R'];assert abs(booked-actual)<1e-8
    cohort_saving=math.fsum(r['delta_R'] for r in cohort if r['loss_reduced'])
    doc=f'''# T3/M15 Early Risk Protection v1

**{decision}.** {('; '.join(reasons)+'.') if reasons else 'Автоматическое принятие запрещено; требуется оценка сохранения трендов.'}

**{C.LABEL}. 2023–2024 DEVELOPMENT_EXPOSED.** Все четыре вечных инструмента; полный причинный replay. Два варианта: CONTROL и EARLY_PROTECT_05. Код/параметры/тесты и вычислительная сверка заморожены до первого результата нового варианта. Данные 2025+ не использованы. Costs, tick rounding, slippage, funding, sizing и реальный капитал отложены.

## Правило и база

Actual main `{C.BASE}`, #507 MERGED; #505/#506 MERGED. CONTROL A6+S1 / TRAIL_375 / NEXT_OPEN точно совпал с полными trade/Stop/signal/gap/month-end OPEN/terminal OPEN журналами и summary/monthly #505/#506 в двух реализациях. 480 CLOSED/1 OPEN; PF2023 2,207278, PF2024 1,772134, Gross +212,522656R; 20/24 положительных месяцев; CLOSED-R DD12,628056R.

Единственное изменение: после завершённой пережитой M15 с favorable extreme >=0,5 initial R от фактического Entry Stop следующей наблюдаемой свечи не хуже Entry−0,5R LONG / Entry+0,5R SHORT. На trigger-свече действует прежний Stop; exit-свеча не активирует защиту. Новый Stop никогда не ослабляет текущий. Исходный Stop2ATR, оригинальный S1 после+1R, ATR trail3,75, A6, NEXT_OPEN, stop-first, gaps, occupancy и re-entry сохранены. Adverse gap может дать убыток хуже−0,5R. MFE исключает экстремумы Stop-свечи, поэтому является нижней границей.

## Полные годовые результаты

'''
    doc+=table([s(v,y) for y in ['2023','2024','ALL'] for v in ['CONTROL','EARLY_PROTECT_05']],['variant','year','closed','period_end_OPEN','gross_PF','gross_R','positive_months','months','worst_month','worst_month_R','closed_R_drawdown'])
    doc+='\nЧисло сделок/OPEN в строках 2023/2024 — exit-year и снимок на конец соответствующего года. Последняя строка ALL — terminal OPEN. DD — последовательность CLOSED gross_R по exit Close MSK с детерминированным instrument/trade_id tie-break, сумма R без модели капитала. GLDRUBF начинается в июле2023, IMOEXF — ноябре2023; NO_COVERAGE отдельно в полной monthly-таблице.\n\n## 32 исходных SHORT2024 с MFE0,5–1R\n\n'
    doc+=f"CONTROL: {assessment['control_causal_cohort32']}/32 имеют пережитую trigger-свечу и следующую наблюдаемую свечу до/на исходном Stop-выходе. В полном EARLY_PROTECT_05 replay реально доступная подтянутая защита: {assessment['actual_causal_cohort32']}/32; исходный убыток уменьшен в {assessment['cohort32_loss_reduced']} сделках, экономия {cohort_saving:.6f}R. Исходный сигнал отсутствует в новом пути у {sum(r['experiment_status']=='ABSENT' for r in cohort)} из32; это эффект занятости, а не отсутствие благоприятного движения. Все32 ID, trigger Close, следующая наблюдаемая Open, actual trigger и новая судьба — `cohort32.csv`. Даже при активации gap не гарантирует fill ровно−0,5R.\n\n"
    doc+='## Судьба исходных сделок и трендов\n\n'
    doc+=table([e],['original_closed','matched_closed','original_not_entered','original_open_experiment','loss_reduced','loss_saving_R','winner_premature','winner_damaged','winner_to_loss','winner_lost_R'])
    doc+='\nУменьшенный убыток и преждевременный победитель считаются только для совпавшего исходного сигнала и двух CLOSED-исходов. Premature = новый exit раньше исходного и R меньше; winner_to_loss — переход исходной прибыли в убыток. Отсутствующие и OPEN-исходы отдельно, они не приравниваются к уменьшенным убыткам.\n\n'
    doc+=table([{'threshold_R':n,**{k.removeprefix(f'GE{n}_'):v for k,v in e.items() if k.startswith(f'GE{n}_')}} for n in [2,5]],['threshold_R','original','not_entered','damaged','premature','to_loss','still_above','control_R','matched_experiment_R','matched_loss_R'])
    doc+='\nВсе исходные ≥2R победители сохранены с ID в `winner_retention.csv`; ≥5R отмечены отдельно. Потери matched-trend R не компенсируются автоматически новыми сделками. Произвольный численный cutoff «существенного» повреждения не вводился.\n\n## Занятость и новые входы\n\n'
    doc+=table([e],['new_entries','lost_entries','occupancy_changed','decision_changed'])
    doc+=f'\nВсе2017 исходных сигналов сохранены в `signal_comparison.csv`, со старой/новой причиной, занятостью и signal identity владельца позиции. Ordinal trade_id не используется для сопоставления. Входы считаются по signal-year, экономика — по exit-year. Trade comparison — полный outer join, включая terminal OPEN. Сверка суммы booked_delta_R: {booked:.6f}R = изменение полного CLOSED Gross R {actual:.6f}R. Никакие старые CSV-сделки не редактировались для оценки кандидата.\n\n'
    attribution=[]
    for cs,xs in sorted({(r['control_status'],r['experiment_status']) for r in comp}):
        picked=[r for r in comp if r['control_status']==cs and r['experiment_status']==xs]
        attribution.append({'control_status':cs,'experiment_status':xs,'entries':len(picked),'booked_delta_R':math.fsum(r['booked_delta_R'] for r in picked)})
    doc+=table(attribution,['control_status','experiment_status','entries','booked_delta_R'])
    doc+='\n## Концентрация ноября2024 и крупных месяцев\n\n'
    doc+=table([s(v,'2024') for v in ['CONTROL','EARLY_PROTECT_05']],['variant','nov2024_R','nov2024_share_R','ex_nov2024_PF','ex_nov2024_R','top1_months','top1_share_annual_R','ex_top1_PF','top3_months','top3_share_annual_R','ex_top3_PF'])
    doc+='\nИсключение ноября/лучших месяцев — только арифметическая диагностика концентрации после полного replay, без нового запуска стратегии. Top5/top10 winners и все годовые серии доступны в `summary.csv`.\n\n## Все24 календарных месяца\n\n'
    rows=[]
    for m in C.CALENDAR:
        aa=next(r for r in data['monthly'] if r['variant']=='CONTROL' and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['month']==m)
        bb=next(r for r in data['monthly'] if r['variant']=='EARLY_PROTECT_05' and r['scope']=='ALL_FOUR' and r['direction']=='ALL' and r['month']==m)
        rows.append({'month':m,'control_R':aa['gross_R'],'experiment_R':bb['gross_R'],'delta_R':bb['gross_R']-aa['gross_R'],'control_PF':aa['gross_PF'],'experiment_PF':bb['gross_PF'],'control_closed':aa['closed'],'experiment_closed':bb['closed']})
    doc+=table(rows,['month','control_R','experiment_R','delta_R','control_PF','experiment_PF','control_closed','experiment_closed'])
    doc+='\n## LONG/SHORT и инструменты по каждому году\n\n'
    doc+=table([r for r in summary if r['year']!='ALL' and ((r['scope']=='ALL_FOUR' and r['direction']!='ALL') or (r['scope']!='ALL_FOUR' and r['direction']=='ALL'))],['variant','scope','direction','year','closed','gross_PF','gross_R','positive_months','worst_month_R','closed_R_drawdown'])
    doc+='\nПолные пересечения всех инструментов с обоими направлениями и обоими годами — `summary.csv`/`DETAIL.md`; все720 month/scope/direction/variant ячеек — `monthly.csv`. Эффекты исходных сделок по45 scope/direction/year комбинациям — `effect_summary.csv`.\n\n## Проверка достоверности\n\n'
    doc+='38 synthetic causal tests (26 исходных +12 early), полный feature-control98 305 M15, два отдельных движка и независимые формулы/joins/metrics. `audit/AUDIT_RESULT.json` сверяет все journal/CSV/JSON поля и все causal-bar invariants; `REPEATABILITY.json` — два дополнительных свежих полных primary+scalar replay с прямой побайтной и SHA256 сверкой файлов. Один автор; независимость вычислительная, внешнее человеческое ревью PENDING. `FREEZE.json` и freeze Git commit фиксируют код/параметры/тесты до первого EARLY_PROTECT_05 результата. `SCOPE_CHECK.json` и `FINAL_MAIN_CHECK.json` фиксируют границы.\n\nНикакие значения после просмотра результата не подбирались. Дополнительные варианты, Robustness, WF, TRUE OOS и LIVE не запускались. Один Draft PR / NO MERGE / NO AUTO-MERGE. STOP после создания PR.\n'
    (root/'REPORT.md').write_text(doc)
    detail='# Полные instrument × direction × year результаты\n\n'+C.LABEL+'; 2023–2024 DEVELOPMENT_EXPOSED.\n\n'+table(summary,['variant','scope','direction','year','closed','period_end_OPEN','gross_PF','gross_R','positive_months','worst_month','worst_month_R','closed_R_drawdown'])+'\n# Эффекты на исходные сделки\n\n'+table(effects,['scope','direction','year','loss_reduced','loss_saving_R','winner_premature','winner_to_loss','winner_lost_R','GE2_damaged','GE2_not_entered','GE2_matched_loss_R','GE5_damaged','GE5_not_entered','GE5_matched_loss_R','new_entries','lost_entries'])
    (root/'DETAIL.md').write_text(detail)
    print(json.dumps(assessment),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,default=C.HERE/'results');a=p.parse_args();render(a.results)
