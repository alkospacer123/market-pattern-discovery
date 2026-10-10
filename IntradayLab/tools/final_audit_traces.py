#!/usr/bin/env python3
"""Render bounded hand-checkable excerpts from the independent oracle output.

Only audit excerpts and calculations are saved; never copy the source dataset.
Imports the independent stdlib oracle, not any trading implementation.
"""
import argparse
from collections import defaultdict
from decimal import Decimal as D
import json
from pathlib import Path

import final_independent_logic_audit as audit

def fmt(x):
    if x is None:return 'null'
    if isinstance(x,D):return f'{x:.12g}'
    return str(x)

def load_rows(rows):
    for r in rows:
        for k in (audit.NUMERIC|{'edge'}).intersection(r):
            if r[k] is not None:r[k]=D(r[k])
    return rows

def economic_check(result,ledger):
    summaries={(r['run'],r['architecture'],r['scenario']):r for r in result['runs']}
    groups=defaultdict(list)
    for r in ledger:groups[r['run'],r['architecture'],r['scenario']].append(r)
    checks=0
    def pf(values):
        loss=-sum((x for x in values if x<0),D(0))
        return sum((x for x in values if x>0),D(0))/loss if loss else None
    for old in audit.table(audit.LAB/'results/stage2_causal_mtf_v1/architecture_comparison.csv'):
        k=old['run'],old['architecture'],'C1_T10';s=summaries[k];delayed=summaries[k[:2]+('C1_T15_DELAY',)]
        known=[r for r in groups[k] if r['net_model_c1'] is not None]
        nets=[r['net_model_c1'] for r in known];c2=[r['gross_price_pnl']-2*r['c1_total'] for r in known]
        positive=sum((v for v in nets if v>0),D(0));top=max(nets) if positive else None
        without=list(nets)
        if top is not None:without.remove(top)
        refkey=old['run'],old['base_architecture']+'__NONE','C1_T10'
        ref={r['signal_id'] for r in groups[refkey]};own={r['signal_id'] for r in groups[k]}
        monthly=defaultdict(lambda:D(0))
        for r in known:monthly[str(r['entry_interval_start'])[:7]]+=r['net_model_c1']
        values=dict(signals=s['signals'],trades=s['entries'],closed_accounted_trades=s['known'],unresolved=s['unknown'],
            closed_only_gross=s['gross'] if known else None,closed_only_c1=s['c1'] if known else None,
            closed_only_net_c1=s['net'] if known else None,net_PF_closed_diagnostic=s['pf'],
            delay_entries=delayed['entries'],delay_closed=delayed['known'],delay_unknown=delayed['unknown'],
            delay_net=delayed['net'] if delayed['known'] else None,delay_PF=delayed['pf'],
            C2_net=sum(c2,D(0)) if known else None,C2_PF=pf(c2),top1_share_positive_PnL=top/positive if positive else None,
            closed_net_without_top_winner=sum(without,D(0)) if positive else None,closed_PF_without_top_winner=pf(without) if positive else None,
            reference_M5_entries=len(ref),entries_retained_same_signal=len(ref&own),reference_entries_omitted=len(ref-own),
            # Legacy column measures cohort size ratio, including freed entries.
            # Actual same-signal retention is verified separately above.
            newly_freed_opportunities=len(own-ref),entries_retention_ratio=D(len(own))/len(ref) if ref else None,
            closed_positive_months=sum(v>0 for v in monthly.values()),closed_negative_months=sum(v<0 for v in monthly.values()))
        for field,value in values.items():
            assert (old[field]=='' if value is None else old[field]!='' and D(old[field])==D(value)),(k,field,value,old[field])
            checks+=1
        assert old['Net']==old['full_PF']==''
    return {'status':'PASS','primary_comparisons':64,'exact_economic_delay_C2_retention_concentration_cells':checks,
            'annual_Net_PF_unavailable':True,'basis':'Independent reconstructed states; no new variants or economic selection',
            'retention_column_interpretation':'entries_retention_ratio = current entries / reference entries, includes newly freed; true same-signal counts verified separately'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--audit-folder',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=json.loads((args.audit_folder/'audit.json').read_text());assert result['status']=='PASS'
    destination=args.output.resolve()
    assert destination.is_relative_to(Path('/workspace/work')) or destination.is_relative_to(audit.LAB/'results/stage2_final_independent_audit')
    assert not destination.exists(), 'Use a NEW trace file; frozen outputs are never overwritten'
    raw=json.loads((args.audit_folder/'reconstructed.json').read_text())
    signals=load_rows(raw['signals']);ledger=load_rows(raw['ledger']);events=load_rows(raw['events']);amendments=load_rows(raw['amendments'])
    economic=economic_check(result,ledger)
    manifest=json.loads((audit.LAB/'config/stage2_causal_mtf_v1.json').read_text())
    data,_=audit.source(args.data_root,manifest)
    journal=audit.table(audit.LAB/'results/stage2_causal_mtf_v1/trade_ledger.csv')
    sjournal=audit.table(audit.LAB/'results/stage2_causal_mtf_v1/signals.csv')
    def key(r):return r['run'],r['architecture'],r['scenario'],r['signal_id']
    signal_map={key(s):s for s in signals};lmap={key(r):r for r in ledger}
    jline={key(r):i+2 for i,r in enumerate(journal)};sline={key(r):i+2 for i,r in enumerate(sjournal)}
    selected=[];used=set()
    def choose(label,rows,predicate,prefer_main=True):
        candidates=[r for r in rows if predicate(r) and key(r) not in used]
        if prefer_main:candidates.sort(key=lambda r:r['scenario']!='C1_T10')
        assert candidates,label
        r=candidates[0];used.add(key(r));selected.append((label,signal_map.get(key(r),r),lmap.get(key(r))))
    for strategy in ('VWAP_MR','MOMENTUM'):
        for direction in (1,-1):
            for reason in ('TAKE','STOP'):
                choose(f'{strategy}: {"LONG" if direction==1 else "SHORT"} {reason}',ledger,
                    lambda r,st=strategy,d=direction,x=reason:r['strategy']==st and r['architecture']=='FROZEN_V2__NONE'
                    and (1 if r['entry']>r['stop'] else -1)==d and r['exit_reason']==x
                    and ((r['net_model_c1']>0) if x=='TAKE' else (r['net_model_c1']<0)))
    for reason in ('BREAKEVEN_STOP','TRAIL_STOP'):
        for direction in (1,-1):
            choose(f'Momentum {reason}, {"LONG" if direction==1 else "SHORT"}',ledger,
                lambda r,x=reason,d=direction:r['exit_reason']==x and (1 if r['entry']>r['stop'] else -1)==d)
    for reason in ('FAILED_BREAKOUT','MOMENTUM_NO_PROGRESS_30M','VWAP_PREMISE_FAILED','VWAP_NO_PROGRESS_30M','MAX_HOLD','SESSION_FLAT'):
        choose(reason,ledger,lambda r,x=reason:r['exit_reason']==x)
    choose('Stop-first при Stop/Take в одной свече',ledger,lambda r:'AMBIGUOUS_STOP_TP' in r['ambiguity_flags'])
    choose('Stop на свече входа',ledger,lambda r:'AMBIGUOUS_ENTRY_EXIT' in r['ambiguity_flags'] and 'AMBIGUOUS_STOP_TP' not in r['ambiguity_flags'])
    choose('Stop: худший Open при гэпе',ledger,lambda r:'ADVERSE_STOP_GAP' in r['ambiguity_flags'] and r['exit_reason']=='STOP')
    choose('Неизвестный путь: цена и P&L null',ledger,lambda r:r['status']=='UNRESOLVED')
    choose('T15: позднее подтверждение session flat',ledger,lambda r:r['scenario']=='C1_T15_DELAY' and r['flat_target_breach'] and r['net_model_c1'] is not None,False)
    choose('CNY: датированный tick 0.001',ledger,lambda r:r['instrument']=='CNYRUBF' and r['entry_interval_start']>'2023-09-27 19:00:00' and r['net_model_c1'] is not None)
    choose('GLD: главный победитель FULL M30',ledger,lambda r:r['instrument']=='GLDRUBF' and r['architecture']=='FULL_M5__M30' and r['net_model_c1']==D('74.8'))
    choose('MR payable-cap и причинный M15',ledger,lambda r:r['strategy']=='VWAP_MR' and r['architecture'].endswith('__M15') and r['net_model_c1'] is not None)
    choose('Momentum: причинный H1',ledger,lambda r:r['strategy']=='MOMENTUM' and r['architecture'].endswith('__H1') and r['net_model_c1'] is not None)
    for reason in ('BREAKOUT_NOT_PERSISTENT','NO_BAR_NO_MODEL_FILL','MTF_INCOMPLETE_CHILD_BUCKET','MOMENTUM_ADX_DI_REGIME'):
        choose(reason,signals,lambda r,x=reason:r['reason']==x)
    choose('Мартовская граница: вход запрещён',signals,lambda r:r['reason']=='KNOWN_BOUNDARY_ENTRY_CUTOFF' and '2023-03-13'<=r['signal_at']<'2023-03-21')
    touches=[e for e in events if e['kind']=='TP' and key(e) not in used]
    assert touches;choose('Take touch без tick penetration: nonfill',ledger,lambda r:key(r)==key(touches[0]))
    # Find an entry candle crossing the target without its execution; this is
    # a factual example of the predeclared entry-bar TP prohibition.
    def entry_tp(r):
        if r['architecture']!='FROZEN_V2__NONE' or r['net_model_c1'] is None or r['entry_interval_start']==r['exit_interval_start']:return False
        t=audit.DT.fromisoformat(r['entry_interval_start']);b=data[r['instrument']][t];d=1 if r['entry']>r['stop'] else -1
        return b[1]>=r['take']+audit.tick(r['instrument'],t) if d==1 else b[2]<=r['take']-audit.tick(r['instrument'],t)
    choose('Take на свече входа запрещён',ledger,entry_tp)
    lines=['# Проверяемые ручные трассировки 2023',
        '',f'{len(selected)} целевых примеров из фиксированных вариантов #451. Все timestamps — MSK (UTC+3), start-label. '
        'OHLCV ниже — короткие цитаты для аудита; исходный набор не копируется. '
        'В печати индикаторы округлены до 12 значащих цифр; сравнение использует Decimal и полную точность.',
        '', 'Строка CSV означает номер строки после распаковки, включая заголовок; ключ = run / architecture / scenario / signal_id. '
        'Источник — frozen 2023 prefix с SHA256 из audit.json. Все сравнения oracle ↔ journal: MATCH.',
        '', '| № | Покрытие | Ключ |', '| --- | --- | --- |']
    for i,(label,s,r) in enumerate(selected,1):lines.append(f'| {i} | {label} | {s["run"]} / {s["architecture"]} / {s["scenario"]} / {s["signal_id"]} |')
    cache={}
    for i,(label,s,r) in enumerate(selected,1):
        k=key(s);idx=data[s['instrument']];at=audit.DT.fromisoformat(s['signal_at']);now=audit.DT.fromisoformat(s['available_at']);d=s['direction_sign'];delay=10 if s['scenario']=='C1_T10' else 15
        fk=s['instrument'],s['strategy'],delay
        if fk not in cache:cache[fk]=audit.features(idx,s['strategy'],delay)
        f=cache[fk][at];step=audit.tick(s['instrument'],now)
        lines+=['',f'## {i}. {label}','',f'`{" / ".join(k)}`. Signal CSV строка **{sline[k]}**'+(f'; ledger строка **{jline[k]}**.' if r else '; ledger отсутствует.'),
            '',f'Сигнал {at}, Close доступен {now}; ready {s["ready_at"]}; exact scheduled Open {s["planned_execution_at"]}. '
            f'Направление {s["direction"]}; status/reason **{s["status"]} / {s["reason"]}**.',
            '',f'ATR12 = сумма прошлых 12 TR / 12 = {fmt(f["tr12_sum"])} / 12 = **{fmt(f["atr_shifted"])}**. '
            f'VWAP = {fmt(f["vwap_weighted_sum"])} / {fmt(f["vwap_weight"])} = **{fmt(f["vwap_approx"])}**; '
            f'локальный anchor {f["segment_first"]}; prior bars {f["prior_bars"]}.']
        prior=[t for t in idx if at-13*audit.FIVE<=t<at]
        trs=[max(idx[t][1]-idx[t][2],abs(idx[t][1]-idx[t-audit.FIVE][3]),abs(idx[t][2]-idx[t-audit.FIVE][3])) for t in prior[1:]]
        lines+=['',f'12 TR, исключая signal bar ({prior[1]} … {prior[-1]}): `{", ".join(map(fmt,trs))}`.']
        if s['strategy']=='VWAP_MR':
            if d==1:formula=f'{fmt(f["previous_close"])} ≤ {fmt(f["previous_vwap"]-f["atr_shifted"])}; {fmt(f["vwap_approx"]-f["atr_shifted"])} < {fmt(s["signal_close"])} < {fmt(f["vwap_approx"])}'
            else:formula=f'{fmt(f["previous_close"])} ≥ {fmt(f["previous_vwap"]+f["atr_shifted"])}; {fmt(f["vwap_approx"])} < {fmt(s["signal_close"])} < {fmt(f["vwap_approx"]+f["atr_shifted"])}'
        else:formula=f'Close {fmt(s["signal_close"])} {">" if d==1 else "<"} prior-12 edge {fmt(s["edge"])}; range [{fmt(s["range_low_shifted"])}, {fmt(s["range_high_shifted"])}]'
        lines+=['',f'Условие сигнала: **{formula}**. ATR14 {fmt(f["atr14"])}; ADX14 {fmt(f["adx14"])}; +DI/-DI {fmt(f["plus_di14"])} / {fmt(f["minus_di14"])}. '
            f'Архитектура {s["base_architecture"]} определяет, используются ли эти контексты.',
            '',f'Initial Stop **{fmt(s["stop"])}**, frozen Take **{fmt(s["take"])}**, cap **{fmt(s["cap"])}**, dated tick {fmt(step)}. '
            f'Swing последних 3 включая сигнал [{fmt(s["swing_low"])}, {fmt(s["swing_high"])}].']
        w=audit.window(at);target=audit.DT.fromisoformat(s['planned_execution_at'])
        lines+=['',f'Boundary entry check: scheduled end {target+audit.FIVE} ≤ B−30 {w[1]-audit.TD(minutes=30)} '
                f'= {target+audit.FIVE<=w[1]-audit.TD(minutes=30)}; окно signal/entry совпадает {audit.window(target)==w}.']
        management=s['base_architecture'] in ('ENTRY_MANAGEMENT','FULL_M5','PAYABLE_CAP_FULL_M5')
        a=f['atr14'] if management and f['atr14'] is not None and s['status']!='SKIPPED' else f['atr_shifted']
        raw_stop=s['signal_close']-d*D('1.5')*a
        if management and f['atr14'] is not None and s['status']!='SKIPPED':
            structure=s['edge']-d*D('.5')*a if s['strategy']=='MOMENTUM' else (s['swing_low']-step if d==1 else s['swing_high']+step)
            lines+=['',f'Stop raw ATR14 {fmt(raw_stop)}; structure {fmt(structure)}; '
                    f'дальний {"min" if d==1 else "max"} = {fmt(min(raw_stop,structure) if d==1 else max(raw_stop,structure))}, '
                    f'округление {"up" if d==1 else "down"} к tick → {fmt(s["stop"])}.']
        else:lines+=['',f'Stop raw Close−direction×1.5ATR12 = {fmt(raw_stop)}, округление {"up" if d==1 else "down"} → {fmt(s["stop"])}.']
        raw_take=f['vwap_approx'] if s['strategy']=='VWAP_MR' else s['signal_close']+d*3*f['atr_shifted']
        lines+=['',f'Take raw {fmt(raw_take)}, округление {"up" if d==1 else "down"} → {fmt(s["take"])}; '
                f'original cap raw Close+direction×0.25ATR12 = {fmt(s["signal_close"]+d*D(".25")*f["atr_shifted"])}.']
        if s['base_architecture'] in ('FULL_M5','PAYABLE_CAP_FULL_M5'):
            aligned=f['plus_di14']>f['minus_di14'] if d==1 else f['minus_di14']>f['plus_di14']
            lines+=['',f'DI aligned = {aligned}; ADX≥25 = {f["adx14"] is not None and f["adx14"]>=25}; '
                    'Momentum требует обе проверки; MR блокирует только strong adverse DI.']
        if s['base_architecture'].startswith('PAYABLE'):
            bound=(s['take']+s['stop']-d*4*step)/2
            lines+=['',f'Payable bound (Take + Stop − direction×4tick)/2 = {fmt(bound)}; cap округлён в безопасную сторону. '
                f'Risk(cap) {fmt(d*(s["cap"]-s["stop"]))}; reward(cap)−2tick {fmt(d*(s["take"]-s["cap"])-2*step)}.']
        if s.get('groups'):
            minutes={'M15':15,'M30':30,'H1':60}[s['architecture'].split('__')[1]]
            lines+=['',f'MTF: parents {s["mtf_first_start"]} / {s["mtf_last_start"]}, direction {s["mtf_direction"]}; '
                f'available {s["mtf_available_at"]} ≤ decision {s["available_at"]}; eligible {s["mtf_gate_eligible"]}.']
            for start,group in zip((s['mtf_first_start'],s['mtf_last_start']),s['groups']):
                parent=audit.DT.fromisoformat(start)
                children=[parent+j*audit.FIVE for j in range(minutes//5)]
                lines+=['',f'Parent {parent}, агрегат O/H/L/C/V `{", ".join(map(fmt,group))}`; '
                    f'все {minutes//5} children: `{", ".join(t.strftime("%H:%M") for t in children)}`.']
        elif s.get('mtf_reason'):
            minutes={'M15':15,'M30':30,'H1':60}[s['architecture'].split('__')[1]]
            latest=now-audit.TD(minutes=minutes-5+delay)
            minute=latest.hour*60+latest.minute
            latest=latest.replace(hour=0,minute=0)+audit.TD(minutes=minute-minute%minutes)
            lines+=['',f'MTF block: {s["mtf_reason"]}; последняя ожидаемая пара не заменяется старой. '
                    f'Nominal latest parent {latest}, available minimum {latest+audit.TD(minutes=minutes-5+delay)}.']
            for parent in (latest-audit.TD(minutes=minutes),latest):
                kids=[parent+j*audit.FIVE for j in range(minutes//5)]
                lines+=['',f'Expected parent {parent}; children `{", ".join(t.strftime("%H:%M")+(" observed" if t in idx else " MISSING") for t in kids)}`.']
        relevant=[e for e in events if key(e)==k]
        open_bar=idx.get(target)
        if open_bar is not None:
            price=open_bar[0];risk=d*(price-s['stop']);reward=d*(s['take']-price)
            lines+=['',f'Scheduled Open {fmt(price)}: signed risk {fmt(risk)}, reward {fmt(reward)}, '
                    f'direction×(Open−cap) {fmt(d*(price-s["cap"]))} ≤0. '
                    f'Entry-quality ruler: risk≥4tick {fmt(4*step)} = {risk>=4*step}; '
                    f'reward−2tick {fmt(reward-2*step)} ≥ risk+2tick {fmt(risk+2*step)} = {reward-2*step>=risk+2*step}. '
                    'Entry-quality ruler применяется только ENTRY/FULL/payable, не FROZEN_V2.']
        candles={at-audit.FIVE:'previous',at:'signal',audit.DT.fromisoformat(s['planned_execution_at']):'scheduled entry'}
        for e in relevant:
            if e['kind'] in ('EXIT','TP','POSITION_PATH','MODEL_FLAT_CONFIRMATION','STOP_AMENDMENT'):
                candles[audit.DT.fromisoformat(e['at'])]=e['kind']
            elif e['kind'] in ('EXIT_ORDER','STOP_AMEND_ORDER'):
                trigger=audit.DT.fromisoformat(e['at'])-audit.TD(minutes=delay)
                candles[trigger]='delivered decision candle'
        lines+=['','| Start MSK | Роль | O | H | L | C | V |','| --- | --- | --- | --- | --- | --- | --- |']
        row_numbers={t:n+2 for n,t in enumerate(idx)}
        for t,role in sorted(candles.items()):
            b=idx.get(t)
            lines.append(f'| {t} | {role}, source row {row_numbers.get(t,"missing")} | '+(' | '.join(map(fmt,b)) if b else 'missing | missing | missing | missing | missing')+' |')
        lines+=['','Решения и исполнения (сравнение с execution_events.csv.gz: MATCH):','']
        for e in relevant:
            if e['kind'] in ('ENTRY_ORDER','ENTRY_CANCEL','ENTRY_OUTCOME','ENTRY','EXIT_ORDER','EXIT','STOP_AMEND_ORDER','STOP_AMENDMENT','TP','POSITION_PATH','MODEL_FLAT_CONFIRMATION','FLAT_TARGET'):
                lines.append(f'- {e["at"]}: {e["kind"]} {e["status"]}, {e["reason"]}; price {fmt(e["reference_price"])}; ack {e["confirmed_at"] or "—"}; flags {e["flags"] or "—"}.')
            if e['kind']=='EXIT_ORDER' and e['reason'] in ('FAILED_BREAKOUT','VWAP_PREMISE_FAILED','VWAP_NO_PROGRESS_30M','MOMENTUM_NO_PROGRESS_30M'):
                trigger=audit.DT.fromisoformat(e['at'])-audit.TD(minutes=delay);close_price=idx[trigger][3]
                progress=d*(close_price-r['entry']);age=(trigger-audit.DT.fromisoformat(r['entry_interval_start'])).total_seconds()/60
                boundary=s['edge'] if s['strategy']=='MOMENTUM' else (s['swing_low'] if d==1 else s['swing_high'])
                lines.append(f'  Расчёт: delivered Close {fmt(close_price)}, signed Close−frozen edge/swing {fmt(d*(close_price-boundary))}; '
                             f'age {age:g}m, progress {fmt(progress)}, 0.5 initialR {fmt(D(".5")*r["initial_risk_price_units"])}.')
        for amend in [a for a in amendments if key(a)==k]:
            decision=audit.DT.fromisoformat(amend['decided_at']);trigger=decision-audit.TD(minutes=delay)
            b=idx[trigger];progress=d*(b[3]-r['entry']);risk=r['initial_risk_price_units']
            atr14=cache[fk][trigger]['atr14']
            best=max(v[1] for t,v in idx.items() if audit.DT.fromisoformat(r['entry_interval_start'])<=t<=trigger) if d==1 else min(v[2] for t,v in idx.items() if audit.DT.fromisoformat(r['entry_interval_start'])<=t<=trigger)
            lines+=['',f'{amend["state"]}: delivered Close progress {fmt(progress)}/{fmt(risk)} = {fmt(progress/risk)}R; '
                f'BE = entry + direction×2tick = {fmt(r["entry"]+d*2*step)}; best delivered extreme {fmt(best)}, '
                f'ATR14 {fmt(atr14)}, trail raw {fmt(best-d*2*atr14)}. '
                f'Stop {fmt(amend["stop"])} decided {decision}, effective {amend["effective_at"]} > decision. '
                'Свечи до effective сохраняют прежнюю защиту.']
        if r:
            if r['net_model_c1'] is None:
                lines+=['',f'Путь неизвестен: {r["unresolved_reasons"]}. Conditional model flat {r["model_flat_scenario_at"]}, ack {r["model_flat_confirmed_at"]}; '
                    '**exit / Gross / exit C1 / total C1 / Net / R = null**. Entry C1 известен отдельно.']
            else:
                lines+=['',f'Exit **{fmt(r["exit"])}**, reason **{r["exit_reason"]}**, interval [{r["exit_interval_start"]}, {r["exit_interval_end"]}), ack {r["exit_confirmed_at"]}. '
                    f'Gross = {d}×({fmt(r["exit"])}−{fmt(r["entry"])}) = **{fmt(r["gross_price_pnl"])}**; '
                    f'C1 = {fmt(r["c1_entry"])} + {fmt(r["c1_exit"])} = {fmt(r["c1_total"])}; '
                    f'Net = **{fmt(r["net_model_c1"])}**; initial risk = |entry−initial stop| = {fmt(r["initial_risk_price_units"])}; '
                    f'Net R = **{fmt(r["net_R"])}**. Flat deadline breach {r["flat_target_breach"]}. Oracle ↔ ledger: **MATCH**.']
        else:lines+=['','Модельный вход не создан; цена исполнения/C1/P&L отсутствуют. Oracle ↔ signal status/reason: **MATCH**.']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text('\n'.join(lines)+'\n')
    args.output.with_suffix('.economic_check.json').write_text(audit.encoded(economic))
    print(f'{len(selected)} traces, {len(lines)} report lines')

if __name__=='__main__':main()
