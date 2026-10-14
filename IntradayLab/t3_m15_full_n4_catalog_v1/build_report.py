"""Read-only reporting from pinned PR #514. Standard library; no strategy imports."""
import argparse, csv, gzip, hashlib, html, io, json, subprocess
from pathlib import Path

MAIN = 'd6946056332ce71658a6ca933cefa0740a7570a2'
SOURCE = '4ae4761837937279eee34bc834c7ec75f066ec81'
DATA = 'f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'
PR513 = 'c17709a748f6247e8bd6bf85c9b4f20fac14a4dd'
SOURCE_DIR = 'IntradayLab/t3_m15_build_comparison_2023_2026_v1'
SYMBOLS = ['USDRUBF', 'CNYRUBF', 'GLDRUBF', 'IMOEXF']
ALIASES = dict(zip(SYMBOLS, ['Si', 'CNY', 'GD', 'MIX']))
N4 = 'N4:' + '+'.join(SYMBOLS)
YEARS = ['2023', '2024', '2025', '2026', 'ALL']
MONTHS = [f'{y}-{m:02}' for y in range(2023, 2027) for m in range(1, 13) if y < 2026 or m <= 10]
REPO_URL = 'https://github.com/alkospacer123/market-pattern-discovery'
FEATURED = ['A6_S1_NEXT_OPEN_TRAIL_3625', 'A6_S1_NEXT_OPEN_TRAIL_375',
            'A6_S1_NEXT_OPEN_TRAIL_3875', 'A6_S1_NEXT_OPEN_TRAIL_400',
            'T1_NEXT_OPEN_TRAIL_3p5', 'T1_S1_NEXT_OPEN_TRAIL_3p5']
# Definitions transcribed from inspected executable functions, not prior chat.
DEFS = [
 ('CONTROL', 'CANONICAL — базовый пробой в трендовом режиме', 'База',
  'H1 ADX14>20 и ATR14/mean20(ATR14)>1. LONG: H1 Close>EMA75, EMA75-EMA75.shift(5)>0 и M15 Close>max(High,20).shift(1); SHORT: обратные строгие сравнения. Вход только при свободной позиции; initial Stop=Entry-side*2*ATR14 сигнальной M15; trailing по экстремуму только пережитых свечей, без ослабления.', 't3_m15_forever_v1', 'indicators / execute', 490),
 ('A1', 'ONE_BAR_EXIT — выход при возврате за пробой на первой свече', 'Выход',
  'На первой наблюдаемой свече после входа side*(Close-breakout_level)<=0 → очередь выхода на Open следующей наблюдаемой свечи. Проверяется действующий Stop; защитный gap на Open имеет приоритет над очередью. Это не безусловный выход через одну свечу.', 't3_m15_entry_regime_v1', 'execute', 495),
 ('A2', 'TWO_BAR_EXIT — два закрытия за уровнем в первых четырёх свечах', 'Выход',
  'В первых четырёх наблюдаемых свечах после входа два последовательных side*(Close-breakout_level)<=0 → выход на следующий наблюдаемый Open. Действующий Stop и gap на Open проверяются первыми.', 't3_m15_entry_regime_v1', 'execute', 495),
 ('A3', 'Направленное тело не меньше половины диапазона', 'Вход',
  'High>Low; abs(Close-Open)>=0.5*(High-Low); Signal*(Close-Open)>0 на сигнальной M15.', 't3_m15_entry_regime_v1', 'permits', 495),
 ('A4', 'Рост силы тренда H1', 'Вход', 'H1ADX>H1PreviousADX; строгий рост ADX последнего завершённого H1 против предыдущего завершённого H1.', 't3_m15_entry_regime_v1', 'permits', 495),
 ('A5', 'Усиление наклона EMA H1', 'Вход', 'LONG: H1Slope>H1PreviousSlope; SHORT: abs(H1Slope)>abs(H1PreviousSlope). Slope=EMA75-EMA75.shift(5).', 't3_m15_entry_regime_v1', 'permits', 495),
 ('A6', 'Рост относительной волатильности H1', 'Вход', 'H1ATRRatio>H1PreviousATRRatio, где ATRRatio=H1 ATR14 / скользящее среднее20 H1 ATR14. Предыдущий H1, а не предыдущая M15 и не новое сравнение с 1.', 't3_m15_entry_regime_v1', 'permits / features', 495),
 ('A7', 'Рост ATR сигнальной M15', 'Вход', 'M15 ATR14>ATR14 предыдущей наблюдаемой M15.', 't3_m15_entry_regime_v1', 'permits', 495),
 ('S1', 'Trailing включается после достижения +1R', 'Сопровождение', 'До +1R действует initial Stop. Сначала проверить старый Stop по Open/Low/High; лишь на Close пережитой свечи обновить экстремум и активировать при side*(extreme-Entry)>=initial risk. Рассчитать extreme-side*trail_atr*ATR текущей M15; только ужесточить. Новый Stop действует со следующей наблюдаемой свечи. NEXT_OPEN включает execution bar; SIGNAL_CLOSE — только свечи после сигнальной.', 't3_m15_stop_exit_v1', 'execute', 496),
 ('S2', 'Безубыток после +1R', 'Сопровождение', 'Обычный trailing работает с начала сопровождения. После +1R на пережитом Close добавить границу Entry; выбрать самый защитный из старого Stop, ATR trailing и границы. Эффективен со следующей наблюдаемой свечи.', 't3_m15_stop_exit_v1', 'execute', 496),
 ('S3', 'Защита +1R после достижения +2R', 'Сопровождение', 'Обычный trailing с начала. После +2R на пережитом Close добавить границу Entry+side*initial risk. Выбрать самый защитный Stop; действует со следующей наблюдаемой свечи.', 't3_m15_stop_exit_v1', 'execute', 496),
 ('T1', 'Входы по сигналам с 10:00 до 18:00 МСК', 'Вход', '10:00<=signal Close MSK<18:00. Ограничение времени сигнала, без принудительного вечернего закрытия; не SESSION_10_21.', 't3_m15_session_entry_v1', 'permits', 499),
 ('T2', 'Пропуск первой сигнальной свечи после разрыва', 'Вход', 'Запрет входа, если предыдущей наблюдаемой свечи нет либо текущий Close-предыдущий Close>15 минут. Пропускается первая наблюдаемая свеча после gap; открытая позиция сохраняется.', 't3_m15_session_entry_v1', 'permits', 499),
 ('I1', 'Первоначальный стоп за сигнальной свечой', 'Начальный риск', 'Initial Stop=Low сигнальной M15 для LONG, High для SHORT; новый initial risk=abs(Entry-Stop). Это не фильтр качества входа.', 't3_m15_initial_stop_v1', 'initial / execute', 498),
 ('I2', 'Первоначальный стоп на уровне пробоя', 'Начальный риск', 'Initial Stop=PriorHigh для LONG или PriorLow для SHORT, Donchian20.shift(1). Валидируется конечный положительный риск; нулевой риск пропускается.', 't3_m15_initial_stop_v1', 'initial / execute', 498),
 ('I3', 'Более близкий из 2ATR и экстремума сигнальной свечи', 'Начальный риск', 'LONG: max(Entry-2ATR, signal Low); SHORT: min(Entry+2ATR, signal High). Меняется initial Stop и знаменатель R, а не trailing ATR.', 't3_m15_initial_stop_v1', 'initial / execute', 498),
 ('C1', 'A6+S1 — рост ATRRatio H1 и отложенный trailing', 'Комбинация', 'Вход A6 плюс сопровождение S1. C1 здесь ID правила, не модель издержек C1. Весь текущий каталог GROSS_ONLY: расходы C1 не вычтены.', 't3_m15_combined_v1', 'MECHANISMS / execute', 497),
 ('C2', 'A7+S1 — рост ATR M15 и отложенный trailing', 'Комбинация', 'Вход A7 плюс сопровождение S1; NEXT_OPEN для этой комбинации не исследован.', 't3_m15_combined_v1', 'MECHANISMS / execute', 497),
 ('COMBINED', 'T1+S1 — дневные сигналы и отложенный trailing', 'Комбинация', 'Окно T1 плюс сопровождение S1; A6 отсутствует.', 't3_m15_t1_s1_v1', 'replay', 500),
 ('EARLY_PROTECT_05', 'Ранняя защита −0,5R после +0,5R', 'Сопровождение', 'На пережитом Close при +0.5R ужесточить Stop до Entry-side*0.5*initial risk; S1 после +1R сохранён. Действует со следующей наблюдаемой свечи. Фиксированный ранее отрицательный опыт #508.', 't3_m15_early_risk_protection_v1', 'replay', 508),
]

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()

def rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def write(path, data):
    fields = list(dict.fromkeys(k for r in data for k in r))
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fields, lineterminator='\n'); w.writeheader(); w.writerows(data)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def link(path, commit=SOURCE):
    return f'{REPO_URL}/blob/{commit}/{path}'

def fmt(v, digits=3):
    return '—' if v in ('', None) else f'{float(v):.{digits}f}'.replace('.', ',')

def table(headers, data):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] + ['| '+' | '.join(map(str,r))+' |' for r in data])

def run(source_root, out):
    assert git(source_root, 'rev-parse', 'HEAD') == SOURCE
    assert not git(source_root, 'status', '--porcelain', '--', SOURCE_DIR)
    src = source_root/SOURCE_DIR/'results'; out.mkdir(parents=True, exist_ok=True)
    reg = rows(src/'BUILD_REGISTRY.csv'); builds = [r for r in reg if r['config_identity']]
    assert len(builds) == len({r['config_identity'] for r in builds}) == 51
    defs = {r[0]:r for r in DEFS}
    names = {}
    for b in builds:
        mechanism = 'EARLY_PROTECT_05' if b['version']=='EARLY_PROTECT_05' else b['rule']
        names[b['build_id']] = defs[mechanism][1]+'; '+b['mode']+'; trailing '+fmt(b['trail'], 3).rstrip('0').rstrip(',')+' ATR'
    rank = rows(src/'STABILITY_RANKING.csv'); rank_by = {r['build_id']:r for r in rank}
    annual = [r for r in rows(src/'ANNUAL_COMPARISON.csv') if r['view']=='FULL_AVAILABLE' and r['scope']==N4]
    lookup = {(r['build_id'],r['year']):r for r in annual}
    cov = rows(src/'COVERAGE.csv'); cov_by = {(r['instrument'],r['month']):r for r in cov}
    endpoints = {s:(min(r['first_close'] for r in cov if r['instrument']==s and r['bars']!='0'), max(r['last_close'] for r in cov if r['instrument']==s and r['bars']!='0')) for s in SYMBOLS}
    def status(month, symbols):
        present = [s for s in symbols if int(cov_by[s,month]['bars'])]
        missing = [s for s in symbols if s not in present]
        partial = [s for s in present if (s in ('GLDRUBF','IMOEXF') and endpoints[s][0][:7]==month) or endpoints[s][1][:7]==month]
        code = 'NO_COVERAGE' if not present else 'AVAILABLE_SOURCE_HISTORY'
        if missing and present: code += ';PARTIAL_INSTRUMENT_COVERAGE'
        if partial: code += ';INCOMPLETE_ENDPOINT_MONTH'
        return code, ';'.join(present), ';'.join(missing), ';'.join(partial)
    catalog = []
    for b in builds:
        catalog.append(dict(name_ru=names[b['build_id']],build_id=b['build_id'],rule_id=b['rule'],entry_filter_id=b['entry'],entry_filter_ru=defs[b['entry']][3],exit_id=b['exit'],exit_ru=defs[b['exit']][3],initial_stop_id=b['initial'],initial_stop_ru='Entry-side*2*ATR14 сигнальной M15' if b['initial']=='2ATR' else defs[b['initial']][3],trailing_ATR=b['trail'],execution_model=b['mode'],execution_status=b['admission'],source_PR=b['source_PR'],all_source_PRs=b['all_source_PRs'],source_commit=b['code_commit'],source_engine_url=link(b['source_path']+'/engine.py',b['code_commit']),source_code_blob=b['code_git_blob'],source_code_sha256=b['code_sha256'],source_spec=b['spec_path'],source_spec_sha256=b['spec_sha256'],report_PR=514,report_commit=SOURCE,original_years=b['original_years'],reported_years=b['replay_years'],config_identity=b['config_identity'],config_json=b['config_json'],audit_status='SOURCE_REPLAY_PASS;INDEPENDENT_REPORT_ARITHMETIC_CHECK_REQUIRED;EXTERNAL_REVIEW_PENDING',annual_PF_170_2023_2024=rank_by[b['build_id']]['annual_minimum_2023_2024'],OOS_status='WF_MIXED_2025;ORIGINAL_PR513_OOS_2026_YTD;CURRENT_RANKING_POST_HOC' if b['build_id']=='A6_S1_NEXT_OPEN_TRAIL_375' else 'POST_HOC_2025_2026;OOS_NOT_PROVEN',cost_status='GROSS_ONLY'))
    write(out/'BUILD_CATALOG.csv', catalog)
    write(out/'RULE_DEFINITIONS.csv', [dict(rule_id=d[0],name_ru=d[1],applies_to=d[2],definition_ru=d[3],source_PR=d[6],source_function=d[5],source_url=link('IntradayLab/'+d[4]+'/engine.py', next((b['code_commit'] for b in builds if b['source_PR']==str(d[6])), MAIN)),verification='EXECUTABLE_CODE_INSPECTED;NO_RULE_CHANGES') for d in DEFS])
    write(out/'YEARLY_COMPARISON.csv', [dict(name_ru=names[r['build_id']],**r,zero_covered_months=int(r['zero_months'])-int(r['no_coverage_months']),source_PR=514,source_commit=SOURCE) for r in annual])
    summary=[]
    for r in rank:
        a=lookup[r['build_id'],'ALL']; summary.append(dict(name_ru=names[r['build_id']],**r,OPEN_at_end=a['OPEN_at_end'],win_rate=a['win_rate'],mean_win_R=a['mean_win_R'],mean_loss_R=a['mean_loss_R'],negative_months=a['negative_months'],zero_covered_months=int(a['zero_months'])-int(a['no_coverage_months']),no_coverage_months=a['no_coverage_months']))
    write(out/'BUILD_SUMMARY.csv', summary)
    monthly=[]
    for r in rows(src/'MONTHLY_COMPARISON.csv'):
        if r['view']!='FULL_AVAILABLE' or r['scope']!=N4:continue
        st,present,missing,partial=status(r['month'], SYMBOLS)
        monthly.append(dict(name_ru=names[r['build_id']],build_id=r['build_id'],execution_model=next(b['mode'] for b in builds if b['build_id']==r['build_id']),month=r['month'],year=r['month'][:4],gross_R='' if st=='NO_COVERAGE' else r['gross_R'],CLOSED=r['CLOSED'],gross_PF=r['gross_PF'],win_rate=r['win_rate'],coverage=st,present_instruments=present,missing_instruments=missing,partial_instruments=partial,source_coverage=r['coverage'],cost_status='GROSS_ONLY',source_commit=SOURCE))
    write(out/'MONTHLY_MATRIX.csv',monthly)
    instrument=[]
    for r in rows(src/'INSTRUMENT_COMPARISON.csv'):
        if r['view']!='FULL_AVAILABLE':continue
        s=r['instrument'] or r['instruments']; assert s in SYMBOLS
        months=MONTHS if r['year']=='ALL' else [m for m in MONTHS if m[:4]==r['year']]
        covered=sum(int(cov_by[s,m]['bars'])>0 for m in months)
        instrument.append(dict(name_ru=names[r['build_id']]) | r | dict(instrument=s,alias=ALIASES[s],covered_months=covered,no_coverage_months=len(months)-covered,zero_covered_months=int(r['zero_months'])-(len(months)-covered),positive_share_covered=int(r['positive_months'])/covered if covered else '',cost_status='GROSS_ONLY',source_commit=SOURCE))
    write(out/'INSTRUMENT_MATRIX.csv',instrument)
    inst_month={}
    for r in rows(src/'MONTHLY_COMPARISON.csv'):
        if r['view']=='FULL_AVAILABLE' and r['scope'].startswith('N1:'):inst_month[r['build_id'],r['month'],r['instruments']]=r
    contributions=[]
    for r in monthly:
        if r['build_id'] not in FEATURED:continue
        vals={s:inst_month[r['build_id'],r['month'],s] for s in SYMBOLS}
        gains=sum(float(v['gross_R']) for v in vals.values() if float(v['gross_R'])>0)
        losses=-sum(float(v['gross_R']) for v in vals.values() if float(v['gross_R'])<0)
        contributions.append(dict(build_id=r['build_id'],month=r['month'],**{ALIASES[s]+'_gross_R':vals[s]['gross_R'] if int(cov_by[s,r['month']]['bars']) else '' for s in SYMBOLS},N4_gross_R=r['gross_R'],positive_instruments=';'.join(ALIASES[s] for s in SYMBOLS if float(vals[s]['gross_R'])>0),negative_instruments=';'.join(ALIASES[s] for s in SYMBOLS if float(vals[s]['gross_R'])<0),compensated_losses=bool(gains>losses>0),coverage=r['coverage']))
    write(out/'MONTHLY_CONTRIBUTIONS.csv',contributions)
    statuses=[]
    for d in DEFS:
        family=[b for b in builds if (b['rule']==d[0] and (d[0]!='C1' or b['version']!='EARLY_PROTECT_05')) or (d[0]=='EARLY_PROTECT_05' and b['version']=='EARLY_PROTECT_05')]
        nextopen=any(b['mode']=='NEXT_OPEN' for b in family)
        statuses.append(dict(rule_id=d[0],name_ru=d[1],TESTED=True,REPLAYED=True,AUDITED='SOURCE_PRIMARY_SCALAR_PASS;INDEPENDENT_REPORT_ARITHMETIC_CHECK_REQUIRED',NEXT_OPEN_AVAILABLE=nextopen,SIGNAL_CLOSE_ONLY=not nextopen,NOT_TESTED=False,INCOMPLETE='REAL_EXECUTION_COSTS_CAPITAL_EXTERNAL_REVIEW',OOS_NOT_PROVEN=True,causality='CAUSAL_NEXT_OPEN_MODEL_AVAILABLE' if nextopen else 'CAUSAL_INDICATORS;IDEALIZED_FILL_ONLY',unique_builds=len(family),note_ru='NEXT_OPEN у A6+S1 не доказывает standalone A6 или standalone S1.' if d[0] in ('A6','S1') else 'Технический аудит не равен прибыльности и не утверждает реальное исполнение.'))
    for b in reg:
        if not b['config_identity']:statuses.append(dict(rule_id=b['build_id'],name_ru=b['build_id'],TESTED=False,REPLAYED=False,AUDITED='NOT_APPLICABLE',NEXT_OPEN_AVAILABLE=False,SIGNAL_CLOSE_ONLY=False,NOT_TESTED=b['status']=='NOT_TESTED',INCOMPLETE=False,OOS_NOT_PROVEN=True,causality=b['status'],unique_builds=0,note_ru='Не проверено — не значит провалено.' if b['status']=='NOT_TESTED' else 'Диагностика, не исполняемая сборка.'))
    write(out/'TEST_STATUS.csv',statuses)
    write(out/'COVERAGE.csv',[dict(**r,coverage_corrected=status(r['month'],[r['instrument']])[0],partial_instruments=status(r['month'],[r['instrument']])[3],source_commit=SOURCE) for r in cov])
    # Store a compact historical sequence; never copy market OHLC files.
    historical={}
    for bid in ['A6_S1_SIGNAL_CLOSE_TRAIL_3p5','A6_S1_NEXT_OPEN_TRAIL_3p5']:
        rs=rows(src/'journals'/bid/'trades.csv.gz')
        historical[bid]=next(r for r in rs if r['instrument']=='USDRUBF' and r['entry_time']=='2023-01-25T17:45:00+03:00')
    stoprows=rows(src/'journals/A6_S1_NEXT_OPEN_TRAIL_3p5/stops.csv.gz')
    historical['stop_sequence']=[r for r in stoprows if r['instrument']=='USDRUBF' and r['trade_id']=='T3-M15-Si-000003' and (r['bar_open_time']=='2023-01-25T17:45:00+03:00' or r['threshold_activated_now']=='True' or r['phase']=='EXIT')]
    (out/'EXECUTION_EXAMPLE.json').write_text(json.dumps(historical,ensure_ascii=False,indent=2)+'\n')
    # Keep the source ranking order exactly, with groups separate.
    matrix={(r['build_id'],r['month']):r for r in monthly}
    def grid(bids, year, markup=False):
        cells=[]
        for bid in bids:
            rr=[]; plus=covered=0
            for m in range(1,13):
                key=(bid,f'{year}-{m:02}')
                if key not in matrix:rr.append('<td class="future">вне YTD</td>' if markup else 'вне YTD');continue
                r=matrix[key]; no=r['coverage']=='NO_COVERAGE'; partial='INCOMPLETE' in r['coverage'] or 'PARTIAL_' in r['coverage']
                covered+=not no; plus+=not no and float(r['gross_R'])>0
                label='нет данных' if no else fmt(r['gross_R'],2)+(' †' if partial else '')
                css='no' if no else 'pos' if float(r['gross_R'])>0 else 'neg' if float(r['gross_R'])<0 else 'zero'
                title=html.escape('Gross R: '+r['gross_R']+'; '+r['coverage']+'; отсутствуют: '+r['missing_instruments']+'; неполны: '+r['partial_instruments'])
                rr.append(f'<td class="{css} {"partial" if partial else ""}" title="{title}">{label}</td>' if markup else label)
            label=bid if not markup else html.escape(bid)+'<small>'+html.escape(names[bid])+'</small>'
            cells.append([label,*rr,f'{plus}/{covered}'])
        headers=['Сборка','Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек','Итого +/набл.']
        if not markup:return table(headers,cells)
        return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+x+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr><th>'+r[0]+'</th>'+''.join(r[1:-1])+'<td>'+r[-1]+'</td></tr>' for r in cells)+'</tbody></table></div>'
    heat=['<!doctype html><html lang="ru"><meta charset="utf-8"><title>IntradayLab — FULL N4</title><style>body{font:15px system-ui;margin:28px;background:#fafbfc;color:#17212d}h1{font-size:28px}h2{margin-top:36px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:13px}th,td{padding:9px;border:1px solid #c7d0d9;text-align:right;white-space:nowrap}th:first-child{text-align:left;max-width:440px;white-space:normal}small{display:block;font-weight:400;color:#536171;font-size:11px;margin-top:4px}.pos{background:#d2efdc;color:#155d31}.neg{background:#f7d7d7;color:#952c2c}.no{background:#dfe3e8;color:#555}.zero{background:#fff}.future{background:#f5f5f5;color:#888}.partial{outline:2px dashed #b07000;outline-offset:-3px}a{color:#1758a1}</style><h1>IntradayLab · FULL N4 · календарные месяцы</h1><p>Si + CNY + GD + MIX; LONG и SHORT сохранены. GROSS_ONLY / POST_HOC_COMPARISON. Значения — CLOSED Gross R, не доходность депозита. Зелёный: плюс; красный: минус; серый: NO_COVERAGE; белый: наблюдаемый ноль; † и пунктир: неполный месяц или неполный состав. Вне YTD — ноябрь/декабрь 2026. Покрытие не сертифицирует биржевой календарь.</p><p><a href="MONTHLY_MATRIX.csv">Точные значения CSV</a> · <a href="REPORT_RU.md">Русский отчёт</a></p>']
    for mode in ['NEXT_OPEN','SIGNAL_CLOSE']:
        bids=[r['build_id'] for r in rank if r['mode']==mode]
        heat.append('<h2>'+('13 NEXT_OPEN — причинная исследовательская модель' if mode=='NEXT_OPEN' else '38 SIGNAL_CLOSE — отдельная идеализированная диагностика')+'</h2>')
        for y in range(2023,2027):heat.append(f'<h3>{y}'+(' YTD' if y==2026 else '')+'</h3>'+grid(bids,y,True))
    heat.append('</html>');(out/'MONTHLY_HEATMAP.html').write_text('\n'.join(heat),encoding='utf-8')
    report=[f'''# IntradayLab — единый каталог FULL N4 за 2023–2026

**51 уникальная сборка: 13 NEXT_OPEN и 38 SIGNAL_CLOSE. GROSS_ONLY / POST_HOC_COMPARISON / NOT_LIVE_READY.** Срез GitHub: 14 октября 2026, МСК. Только Si, CNY, GD, MIX; оба направления, без новых весов, правил или торговых прогонов.

Проверены базовый пробой, A1/A2 выходы, A3–A7 входные фильтры, S1–S3 сопровождение, T1/T2 ограничения входа, I1–I3 initial Stop, A6+S1, A7+S1, T1+S1 и ранняя защита 0,5R. Проверка определения не означает полезность механизма. Standalone NEXT_OPEN для большинства механизмов отсутствует; исполнение SIGNAL_CLOSE нельзя напрямую ставить в один рейтинг с NEXT_OPEN. Initial Stop и trailing ATR — разные параметры.

Пять вариантов для содержательного сравнения, без назначения новой production-системы:

1. **Рост волатильности H1 + trailing после +1R, 3,625 ATR** (`A6_S1_NEXT_OPEN_TRAIL_3625`): лидер регулярности, 36/45; PF2024 ниже 1,70.
2. **Та же комбинация, 3,75 ATR** (`A6_S1_NEXT_OPEN_TRAIL_375`): 35/45, лидер общего PF и лучший компромисс среди выполняющих ежегодный ориентир.
3. **Та же комбинация, 3,875 ATR** (`A6_S1_NEXT_OPEN_TRAIL_3875`): максимум Gross R, но более высокая DD и хуже месяцы 2025.
4. **Та же комбинация, 4,0 ATR** (`A6_S1_NEXT_OPEN_TRAIL_400`): самый высокий худший годовой PF среди NEXT_OPEN, ценой большей DD.
5. **Дневное окно сигналов, 3,5 ATR** (`T1_NEXT_OPEN_TRAIL_3p5`, технический эквивалент названия TRAIL_350): минимальная NEXT_OPEN DD; PF2024 не выполняет 1,70.

Шестой обязательный ориентир — дневное окно с trailing после +1R, `T1_S1_NEXT_OPEN_TRAIL_3p5` (T1+S1 TRAIL_350). Полный каталог включает все остальные сборки.

**Сохраняемый исследовательский CONTROL: A6+S1 NEXT_OPEN TRAIL_375 FULL N4.** Это сохранение замороженного ориентира, не решение о production. Не завершены внешний аудит Draft-источников, независимое OOS нового рейтинга, реальные издержки, tick-совместимость, capital/ГО sizing и подтверждение исполнения будущего робота. Следующий шаг в существующем roadmap — независимое ревью опубликованных доказательств и отдельное решение пользователя о дальнейшей проверке замороженного кандидата и его исполнения/экономики. Новых стадий или запуска исследования здесь нет.

## Источники и полнота

Актуальный `main`: `{MAIN}`. Главный источник — [Draft #514]({REPO_URL}/pull/514) на `{SOURCE}`, **не часть main**. В main доступны исходные определения/исследования #490, #495–#508, #510–#512. [Draft #513]({REPO_URL}/pull/513) использован только на `{PR513}` для исходной проверки TRAIL_375; незамержен. #509 закрыт без merge: архивная диагностика, не новый полноценный replay. #516 на `212f2be35d5641da5751d98eb9c5456747d580fa` касается весов; его численные результаты исключены. Живые статусы и SHA: [GITHUB_SOURCES.json](GITHUB_SOURCES.json).

В реестре #514 **73 строки = 51 сборка + 17 NOT_TESTED + 5 DIAGNOSTIC_ONLY**. Только строки с уникальным config_identity считаются сборками. Алиасы CONTROL/C1/COMBINED и повторные исследования не создают дублей. `RULE_DEFINITIONS.csv` в HEAD #514 отсутствует; новый [справочник](RULE_DEFINITIONS.csv) составлен из исполняемых функций. Старые файлы не исправлены.

## Механизмы простыми словами и точные правила
''']
    report.append(table(['ID','Название / область','Фактическое правило','Проверено'],[[d[0],d[1]+' / '+d[2],d[3],f'Код #{d[6]}; [статус](TEST_STATUS.csv)'] for d in DEFS]))
    report.append('''
`TRAIL_300=3,0 ATR`, `TRAIL_350=3,5 ATR`, `TRAIL_3625=3,625 ATR`, `TRAIL_375=3,75 ATR`. В исходных build ID 3,0 и 3,5 записаны как `3p0`/`3p5`; названия не создают новых конфигураций. Базовый первоначальный Stop — 2ATR сигнальной M15; I1–I3 заменяют именно его. R=side×(Exit−Entry)/неизменный initial risk; разные initial Stop меняют знаменатель, поэтому суммы R не равны рублёвой прибыли при одинаковом размере позиции. C1-правило A6+S1 и C1-модель расходов — разные сущности.

## SIGNAL_CLOSE и NEXT_OPEN: последовательность исполнения

1. Источник имеет timestamp начала M15; в исследовании CloseTime=timestamp+15 минут. Сигнал определяется на завершённой M15 по её окончательному Close, ATR и уже опубликованному H1.
2. H1 — четыре смежные M15 в дневном ordinal-блоке, не обязательно час по круглым меткам. Окончательные индикаторы доступны на Close четвёртой свечи; незавершённые/gap-блоки пропускаются. Последний завершённый H1 переносится вперёд, предыдущий H1 берётся отдельным shift(1). Рекурсии и rolling-контекст пересекают дни по замороженному коду.
3. SIGNAL_CLOSE моделирует вход по уже известному Close сигнальной свечи. Это идеализированный исторический fill; он не доказывает возможность исполнения по этой цене. Initial Stop создаётся на Close, а проверяется со следующей наблюдаемой свечи; High/Low сигнальной свечи после такого входа не используется.
4. NEXT_OPEN планирует вход после сигнала. Разрешён только Open смежной наблюдаемой M15: execution OpenTime=signal CloseTime, execution CloseTime=signal CloseTime+15 минут. Численно метки сигнала и входа совпадают, но это граница двух разных свечей. Нулевая задержка на этой границе — исследовательское допущение, не утверждённый контракт робота.
5. NEXT_OPEN initial Stop=фактический моделируемый Open−side×2×ATR завершённой сигнальной M15. Он работает уже на execution bar. Старый Stop проверяется до выгодного экстремума, активации S1 и нового trailing; gap через Stop исполняется по неблагоприятному Open. Stop не округляется автоматически до биржевого tick.
6. Если следующая наблюдаемая свеча несмежная, NEXT_OPEN отменяет вход (`SKIPPED_MISSING_ADJACENT_OPEN`); не ждёт поздний выгодный Open. Последний сигнал без следующей свечи — pending/UNRESOLVED_END_OF_DATA, не CLOSED и не OPEN. SIGNAL_CLOSE уже имеет вход на сигнальном Close и сохраняет позицию через gap, затем проверяет следующий наблюдаемый Open. T2 отдельно пропускает первый сигнал после gap; это иной механизм.

Проверенный пример **Si, 25–26 января 2023**, одинаковое правило A6+S1 и trailing 3,5 ATR, trade ID `T3-M15-Si-000003`:

| Момент МСК | Событие |
| --- | --- |
| 25.01 17:30–17:45 | Сигнальная M15: Close 69,33; пробой уровня 69,24; ATR 0,0679113327749489. H1 опубликован в 17:45: ADX 20,008952; ATRRatio 1,008575698 > предыдущего 0,979028681. |
| 25.01 17:45 | SIGNAL_CLOSE LONG Entry 69,33; initial Stop 69,1941773344501; initial risk 0,1358226655498953. |
| 25.01 17:45–18:00 | NEXT_OPEN LONG на Open 69,32; initial Stop 69,1841773344501; тот же initial risk. Low 69,20 пережил Stop. На Close 18:00 S1 ещё не активирован. |
| 26.01 09:00–09:15 | После overnight-gap позиция сохраняется. Старый Stop пережит; High 69,60 даёт 2,0615R NEXT_OPEN. S1 активируется только в 09:15. ATR на Close 0,05952061060575839 → Stop следующей свечи 69,39167786287985. |
| 26.01 09:15–09:30 | Новый Stop вступил в силу; выход 69,39167786287985. NEXT_OPEN Gross +0,5277312338824695R; SIGNAL_CLOSE +0,4541058197476574R. |

Отчётное exit_time защитного выхода — Close свечи 09:30; точную секунду intrabar источник не доказывает. Числа/Stop-последовательность: [EXECUTION_EXAMPLE.json](EXECUTION_EXAMPLE.json); сверка с исходными свечами включена в AUDIT. NEXT_OPEN и SIGNAL_CLOSE могут изменять не только цену, но и stop-hit, занятость, повторные входы и весь состав сделок.

## Фактическое покрытие
''')
    report.append(table(['Инструмент','Первый Close МСК','Последний Close МСК'],[[ALIASES[s]+' / '+s,*endpoints[s]] for s in SYMBOLS]))
    report.append('''
Data pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. Cutoff исключительный: 13.10.2026 00:00 МСК. В 2026 доступны январь–июль для всех; август неполон у Si/CNY, сентябрь неполон у GD/MIX и отсутствует у Si/CNY; октябрь NO_COVERAGE; ноябрь/декабрь вне YTD. В июле 2023 GD стартует внутри месяца, MIX стартует внутри ноября. До старта инструмент — NO_COVERAGE, а не ноль. Все результаты FULL_AVAILABLE: не сокращать 2023 до общего старта N4.

**45 наблюдаемых месяцев из 46 календарных месяцев окна** (январь 2023–октябрь 2026). Для CONTROL 35 положительных /45 наблюдаемых; 35/46 — другой, календарный denominator. Наблюдаемый нулевой месяц, NO_COVERAGE и будущий месяц различаются. Источник не сертифицирует все биржевые сессии и внутримесячные gaps.

В #514 флаг INCOMPLETE_ENDPOINT_MONTH применялся к августу 2026 также у GD/MIX, хотя у них источник до сентября. Здесь индивидуальный endpoint-флаг вычислен по фактическому первому/последнему Close: август GD/MIX без endpoint-флага, FULL N4 август остаётся неполным из-за Si/CNY. Исходный флаг сохранён отдельно в COVERAGE.csv. Gross R не меняется.

## Таблица 1 — все 51 исследованные сборки

Понятные названия, точные определения, source PR/commit/blob/SHA, причинность, годы и аудит: [BUILD_CATALOG.csv](BUILD_CATALOG.csv). Все результаты #514 имеют source replay/scalar PASS; в этом пакете независимая арифметика таблиц проверяется отдельным verify_report.py. Это проверка отчётности, не новый replay индикаторов/сделок. Внешнее ревью остаётся PENDING.
''')
    report.append(table(['Название','Build ID','Вход','Выход','Initial Stop','Trailing ATR','Исполнение','Источник / commit','Годы','PF≥1,70 23/24'],[[names[b['build_id']],b['build_id'],b['entry'],b['exit'],b['initial'],b['trail'],b['mode'],f"#{b['source_PR']} / {b['code_commit']}",'2023–2026 YTD',rank_by[b['build_id']]['annual_minimum_2023_2024']] for b in builds]))
    report.append('\n## Таблица 2 — годовой PF и общий результат\n\n[Годовые показатели с CLOSED/OPEN, win rate, средними win/loss, expectancy, DD и концентрацией](YEARLY_COMPARISON.csv); [одна строка на сборку](BUILD_SUMMARY.csv). PF считается из сумм выигрышей/убытков CLOSED, не усреднением годовых PF.\n')
    for mode in ['NEXT_OPEN','SIGNAL_CLOSE']:
        report.append('\n### '+mode+(' — причинная модель' if mode=='NEXT_OPEN' else ' — идеализированная диагностика')+'\n')
        report.append(table(['Build ID','PF23','PF24','PF25','PF26 YTD','PF ALL','Gross R','+мес./набл.','DD R','CLOSED'],[[r['build_id'],fmt(r['PF_2023'],4),fmt(r['PF_2024'],4),fmt(r['PF_2025'],4),fmt(r['PF_2026_YTD'],4),fmt(r['gross_PF'],4),fmt(r['gross_R']),f"{r['positive_months']}/{r['covered_months']}",fmt(r['max_DD_R']),r['CLOSED']] for r in rank if r['mode']==mode]))
    report.append('\n### Экономика шести обязательных ориентиров по годам\n')
    report.append(table(['Сборка','Год','Gross R','CLOSED','OPEN конец','Win %','Средний win R','Средний loss R','Expectancy R','−мес. подряд','Лучший месяц %R','Top3 мес. %R'],[[r['build_id'],r['year'],fmt(r['gross_R']),r['CLOSED'],r['OPEN_at_end'],fmt(float(r['win_rate'])*100,2),fmt(r['mean_win_R']),fmt(r['mean_loss_R']),fmt(r['expectancy_R']),r['max_negative_month_streak'],fmt(float(r['best_month_share_R'])*100,2) if r['best_month_share_R'] else 'N/A',fmt(float(r['top3_month_share_R'])*100,2) if r['top3_month_share_R'] else 'N/A'] for bid in FEATURED for y in YEARS[:-1] for r in [lookup[bid,y]]]))
    report.append('''
Концентрация — доля лучшего/трёх лучших месяцев в signed годовом Gross R. При годовом R≤0 доля N/A; абсолютные результаты сохранены. DD — падение последовательной суммы CLOSED R по exit_time, instrument, trade_id, от начального 0; это не MTM или денежная просадка. OPEN не включаются в PF/R, не закрываются на годовой границе. В 2025 CONTROL полный календарный результат 300 CLOSED/PF1,581308 включает одну перенесённую сделку; новая WF-cohort 299 CLOSED/PF1,563150 — другой разрез, не расхождение. Статус WF_MIXED сохраняется.

## Таблица 3 — календарные месяцы, самая важная

[Автономная цветная карта всех 51 сборок](MONTHLY_HEATMAP.html) и [полный точный CSV](MONTHLY_MATRIX.csv). Ниже шесть обязательных ориентиров, Gross R; † — неполный endpoint или неполный инструментальный состав. Отсутствие котировок не заменяется нулём. HTML показывает 13 NEXT_OPEN и отдельно 38 SIGNAL_CLOSE, годы отдельно.
''')
    for y in range(2023,2027):report.append(f'\n### {y}'+(' YTD' if y==2026 else '')+'\n\n'+grid(FEATURED,y))
    report.append('\n## Таблица 4 — инструменты и направления\n\n[INSTRUMENT_MATRIX.csv](INSTRUMENT_MATRIX.csv): все 51 сборка × 4 инструмента × 5 периодов × BOTH/LONG/SHORT = 3060 строк. PF, Gross R, CLOSED, win rate, положительные/наблюдаемые месяцы и CLOSED-R DD. Направления сохранены; индивидуальный PF не служит основанием исключать рынок.\n')
    report.append(table(['Сборка','Рынок','PF23','PF24','PF25','PF26','Gross R ALL','CLOSED','Win %','+мес./набл.','DD R'],[[bid,ALIASES[s],*[fmt(next(r for r in instrument if r['build_id']==bid and r['instrument']==s and r['direction']=='BOTH' and r['year']==y)['gross_PF'],4) for y in YEARS[:-1]],fmt(a['gross_R']),a['CLOSED'],fmt(float(a['win_rate'])*100,2),f"{a['positive_months']}/{a['covered_months']}",fmt(a['max_DD_R'])] for bid in FEATURED for s in SYMBOLS for a in [next(r for r in instrument if r['build_id']==bid and r['instrument']==s and r['direction']=='BOTH' and r['year']=='ALL')]]))
    report.append('\n### Месяцы CONTROL, где выигрыши рынков перекрыли убытки других\n\nПоказаны только исходные четыре вклада и их сумма FULL N4. В [MONTHLY_CONTRIBUTIONS.csv](MONTHLY_CONTRIBUTIONS.csv) все месяцы шести ориентиров; отрицательные рынки также сохранены.\n')
    report.append(table(['Месяц','Si R','CNY R','GD R','MIX R','N4 R','Плюс / минус рынки'],[[r['month'],*[fmt(r[s+'_gross_R']) for s in ['Si','CNY','GD','MIX']],fmt(r['N4_gross_R']),r['positive_instruments']+' / '+r['negative_instruments']] for r in contributions if r['build_id']=='A6_S1_NEXT_OPEN_TRAIL_375' and r['compensated_losses']]))
    report.append('\n## Таблица 5 — полнота исследования\n\n[TEST_STATUS.csv](TEST_STATUS.csv) различает TESTED, REPLAYED, AUDITED, NEXT_OPEN_AVAILABLE, SIGNAL_CLOSE_ONLY, NOT_TESTED, INCOMPLETE, OOS_NOT_PROVEN. Причинность индикаторов не доказывает реалистичный Close-fill. AUDITED — вычислительная проверка источника и отдельно арифметика этого отчёта; внешний человек ещё не утвердил пакет. NOT_TESTED не означает FAILED.\n')
    report.append(table(['Семейство','TESTED','NEXT_OPEN','SIGNAL_CLOSE_ONLY','Чего не хватает'],[[r['rule_id'],r['TESTED'],r['NEXT_OPEN_AVAILABLE'],r['SIGNAL_CLOSE_ONLY'],r['note_ru']] for r in statuses]))
    report.append('\n## Лидеры по разным показателям\n\nПорядок рейтинга сохранён из #514: положительные годы → минимальная годовая доля положительных покрытых месяцев → общее число положительных месяцев → отрицательная серия → худший месяц → DD → концентрация top3 месяцев → концентрация инструмента → число CLOSED → худший годовой PF. Без балльной системы; новый рейтинг не конструировался. Категории лидеров ниже — отдельные описательные экстремумы, не замена порядка рейтинга. «Годовой баланс» здесь означает максимум минимального PF среди 2023, 2024, 2025, 2026 YTD; это не новый PASS.\n')
    for mode in ['NEXT_OPEN','SIGNAL_CLOSE']:
        rr=[r for r in rank if r['mode']==mode]
        leaders=[('Месячная регулярность',max(rr,key=lambda r:int(r['positive_months'])),'positive_months'),('Минимальная CLOSED-R DD',min(rr,key=lambda r:float(r['max_DD_R'])),'max_DD_R'),('Годовой баланс: лучший худший PF',max(rr,key=lambda r:float(r['min_year_PF'])),'min_year_PF'),('Общий PF',max(rr,key=lambda r:float(r['gross_PF'])),'gross_PF')]
        report.append('\n### '+mode+'\n\n'+table(['Критерий','Build ID (все равные лидеры)','Значение'],[[label,'; '.join(q['build_id'] for q in rr if q[key]==r[key]),fmt(r[key],4)] for label,r,key in leaders]))
    report.append('''
Для NEXT_OPEN ежегодный минимум PF≥1,70 в 2023 и 2024 выполняют только TRAIL_375, TRAIL_3875, TRAIL_400. Лучший компромисс этой группы — прежний TRAIL_375: больше положительных месяцев, меньше DD и выше общий PF. TRAIL_3625 регулярнее (36 против 35), но PF2024=1,648640. TRAIL_3875 даёт всего +1,873184R к CONTROL (+0,448%) при DD30,790357 вместо28,637394 и 6/12 положительных месяцев2025 вместо7/12. TRAIL_400 улучшает худший PF, но увеличивает DD. T1 TRAIL_350 уменьшает DD, однако PF2024=1,4609. T1+S1 TRAIL_350 не проходит PF2024≈1,5104 и добавление S1 не следует считать автоматически полезным.

**Единого доказанного победителя нет.** Предпочтительный PF>2 в каждом году не выполнен ни одним NEXT_OPEN. CONTROL 2025 имеет 7/12 положительных месяцев, четыре отрицательных подряд и ~80,51% годового R в трёх лучших месяцах; его устойчивость нельзя оценивать только по ALL PF. Instrument/LONG/SHORT, top5/top10 и результаты без лучших месяцев есть в точных таблицах, но это диагностика без удаления исходных сделок.

## Что завершено по существующему roadmap

| Работа | Фактический источник / статус | Ограничение |
| --- | --- | --- |
| Базовое воспроизведение, механизмы входа/выхода/initial Stop | #490, #495–#500 MERGED | Исторические SIGNAL_CLOSE, в каталоге идеализированные |
| Диагноз слабых месяцев и качества входа | #503, #507 MERGED | Не разрешает новые фильтры или отключение SHORT |
| Чувствительность NEXT_OPEN | #504 MERGED | Причинная OHLC-модель, не подтверждённое broker fill |
| Ограниченная численная Optimization / plateau | #505–#506 MERGED | Уже выполнена; здесь не повторялась |
| Ранняя защита | #508 MERGED, отрицательный опыт | Сохранён, не подбирался новый порог |
| Robustness | #510 MERGED, MIXED | Не автоматический Robustness PASS; #509 незамержен |
| Walk Forward 2025 неизменного TRAIL_375 | #512 MERGED, WF_MIXED | Только замороженный кандидат; не доказательство нового победителя |
| OOS 2026 YTD TRAIL_375 | #513 Draft, опубликованный OOS_2026_YTD | Источник на точном SHA; не часть main, внешний аудит/решение незавершены |
| Сравнение 51 сборки | #514 Draft, POST_HOC_COMPARISON | Источник этого пакета; новый рейтинг OOS_NOT_PROVEN |
| Реальная экономика/исполнение/робот | Не завершены, NOT_LIVE_READY | FINAM/MOEX расходы, spread/slippage/funding, tick, ГО/капитал и инженерные проверки |

Историческая общая таблица stages в ROADMAP содержит более старые M5 статусы NOT_STARTED; она не описывает завершённые T3-specific #505/#510/#512. Фактические T3 результаты выше сверены с main и PR. ROADMAP не переписан и новых этапов не создано. 2023–2024 DEVELOPMENT_EXPOSED. Для остальных сборок 2025–2026 — ретроспективное сравнение, не чистый WF/TRUE OOS. Исходный статус #513 сохранён без распространения на весь каталог.

## Достоверность, границы и воспроизведение

[AUDIT.json](AUDIT.json) — независимая арифметика всех таблиц из первичных журналов, уникальность сделок, календарная принадлежность, OPEN/переносы, source SHA, pinned source #513, хеши входных файлов и выявленные замечания. `verify_report.py` не импортирует генератор или research engine/metrics; Decimal-подсчёт реализован отдельно. Это независимость вычисления, не внешний институциональный аудит. Полный повтор формирования проверяется по побайтным SHA, [REPRODUCIBILITY.json](REPRODUCIBILITY.json).

Никаких новых OHLC replay, оптимизаций, торговых правил/комбинаций/весов, broker calls, merge или auto-merge. Gross суммы R — descriptive pooled независимых сделок, без общего капитала/ГО и межинструментальных лимитов; они не являются RUB доходностью или процентным DD. Реальные расходы не нулевые, а не учтённые. Параметры будущего робота не утверждены.

Только Python standard library. Подготовить отдельный read-only checkout источника #514 на точном SHA, затем:

```sh
python build_report.py --source-root /path/to/pr514-checkout --output /path/to/report
python verify_report.py --source-root /path/to/pr514-checkout --data-root /path/to/market-pattern-data --output /path/to/report
```

Генератор читает существующие CSV, определяет отчётные coverage-флаги и формирует таблицы; verifier заново считает экономику из существующих журналов. Первичные большие trade/Stop журналы не дублируются. Для второго отчётного повтора выбрать другой output и сравнить SHA; торговые движки не запускать. Ссылки source commit неизменны. После публикации одного нового Draft PR — STOP для внешнего аудита и решения пользователя.
''')
    (out/'REPORT_RU.md').write_text('\n'.join(report).rstrip()+'\n',encoding='utf-8')
    provenance=dict(base_main=MAIN,source_PR=514,source_commit=SOURCE,data_pin=DATA,PR513_source_commit=PR513,new_optimization=False,new_trading_replay=False,new_rules=False,portfolio='FULL N4; descriptive pooled Gross R; unchanged instruments and directions',input_files={str(p.relative_to(source_root)):sha(p) for p in sorted(src.rglob('*')) if p.is_file() and (p.suffix in ('.csv','.gz','.json') and ('journals' in p.parts or p.parent==src))})
    (out/'SOURCE_SHA256.json').write_text(json.dumps(provenance,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(builds=len(catalog),yearly=len(annual),months=len(monthly),instruments=len(instrument),status_rows=len(statuses))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-root',type=Path,required=True);p.add_argument('--output',type=Path,default=Path(__file__).resolve().parent);a=p.parse_args();run(a.source_root.resolve(),a.output.resolve())
