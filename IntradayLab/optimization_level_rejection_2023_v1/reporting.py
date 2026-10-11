"""Frozen rendering, including predeclared diagnostic ordering; no strategy logic."""
from decimal import Decimal as D
import csv,json
from .contract import STUDY


def ordered(rows):
    return sorted(rows,key=lambda r:(-int(r['positive_exit_months']),-min(D(r['PF_R']),D(r['PF_price'])),D(r['conditional_closed_only_DD_R']),-int(r['CLOSED']),r['configuration_id']))


def report(policy,freeze,candidates,monthly,selection):
    lines=['# Optimization Level Rejection M5 — 2023','',f'**{selection["overall_result"]}**','',
        f'Base `{policy["base_main"]}`; pre-P&L freeze `{freeze}`. 72 unique configurations × 3 instruments = 216 evaluations.',
        '2023 M5 development data only. CLOSED economics after C1 are conditional; full annual return/account equity remains unavailable. Missing months never count as profitable.',
        'Original six completed-bar level, one-bar breach/reentry, directional 30-minute dedup, one complete waiting M5 then future Open, structural Stop, 4-tick risk, 35-minute reserve, 17:00 deadline, session flat, Stop-first, no entry-bar Take; shared engine unchanged.',
        'Reentry 1/2 ticks (completed Close and future Open, original parameter coupling); Stop buffer 1/2 ticks; holding 120/60 minutes; Take 2..10 FULL_NET_C1_R. No duplicate configurations or architecture incompatibilities.',
        'Let s be initial gross price risk, c=2×entry tick. Planned Take distance q×(s+c)+c, outward rounded; ideal after-C1 Stop loses s+c, ideal net/net Stop is -1; adverse Open gaps can lose more. net_R_c1=(gross−actual C1)/s preserves A/B/C reporting; planned/realized net/net R use s+planned/actual C1. Never mix these denominators.',
        'Selection: ≥100 CLOSED, ≥40 entry days, ≥6 entry months; both PF ≥2, expectancy >0, ≥9 positive exit months, conditional CLOSED DD ≤20R, winner share ≤25%, positive-month share ≤50%, ≥2 adjacent one-parameter neighbors with ≥100 CLOSED/PF R ≥1.5/expectancy >0.',
        'Ranking: positive months DESC, min(PF R,price) DESC, DD ASC, CLOSED DESC, stable ID ASC. Only complete passes can be candidates. Diagnostic rows below use that same ordering without implying qualification.',
        'Full journals in evaluations/<ID>/<instrument>/; all_candidates.csv, monthly_results.csv (12 months each), direction_results.csv, execution_funnel.csv, parameter_neighborhood.csv and detailed_artifact_index.csv preserve every evaluation. SKIP and EXCLUDED have separate ledgers and blank economics.','',
        '| Instrument | Evaluated | Sample pass | Both PF pass | Months pass | Neighbor pass | Full pass |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for symbol,s in selection['instruments'].items():lines.append('| '+symbol+' | '+' | '.join(str(s[k]) for k in ('evaluated','sample_pass','both_PF_pass','months_pass','neighbors_pass','full_criteria_pass'))+' |')
    lines+=['','Best three diagnostic configurations per instrument, under the published ranking order:','',
        '| Instrument / ID | CLOSED | PF R / price | Net R | + months | DD R | Failed gates |','| --- | ---: | --- | ---: | ---: | ---: | --- |']
    for symbol in policy['instruments']:
        for r in ordered([r for r in candidates if r['instrument']==symbol])[:3]:
            lines.append(f'| {symbol} / {r["configuration_id"]} | {r["CLOSED"]} | {r["PF_R"]} / {r["PF_price"]} | {r["Net_R"]} | {r["positive_exit_months"]} | {r["conditional_closed_only_DD_R"]} | {r["failure_reasons"]} |')
    return '\n'.join(lines)+'\n'


def task_summary(output,validation):
    selection=json.loads((output/'selection_report.json').read_text());baseline=json.loads((output/'baseline_replay.json').read_text());audit=json.loads((output/'audit.json').read_text());policy=json.loads((STUDY/'OPTIMIZATION_LEVEL_REJECTION_POLICY.json').read_text())
    with (output/'all_candidates.csv').open() as f:rows=list(csv.DictReader(f))
    lines=['# Task Summary — Optimization Level Rejection M5 2023','',f'**{selection["overall_result"]}**','',
        f'Base SHA `{policy["base_main"]}`. Freeze SHA `{validation["freeze_commit"]}`.',
        '72/72 configurations for each of USDRUBF, CNYRUBF, GLDRUBF; 216/216 total. IMOEXF excluded (22 Baseline CLOSED).',
        'Full passes: '+str({s:v['full_criteria_pass'] for s,v in selection['instruments'].items()})+'.',
        'Original Baseline replay and V2 comparison: '+json.dumps(baseline['instruments'],sort_keys=True)+'.',
        'Best diagnostic rows under frozen ordering:']
    for symbol in policy['instruments']:
        r=ordered([r for r in rows if r['instrument']==symbol])[0]
        lines.append(symbol+': '+str({k:r[k] for k in ('configuration_id','CLOSED','PF_R','PF_price','Net_R','expectancy_R','positive_exit_months','conditional_closed_only_DD_R','failure_reasons')})+'.')
    lines+=['','Pre-P&L technical/regression/synthetic corruption checks: preflight.json. Independent auditor: '+str(audit.get('checked_fields'))+'. Three full audits; two complete deterministic repeats: '+str(validation['full_repeats'])+'.',
        'Independent auditor was implemented by a separate delegated agent using raw M5 batch slices and its own chronological execution/metrics/selector; no production calculation functions as reference. External human review is pending.',
        'All saved economics are conditional CLOSED-only after model C1; no complete annual return or continuous equity claim. Original results/config/strategies and A/B/C remain byte-identical.',
        'Protection: '+str(validation['protected_scope'])+'. No TradingSystemLab, live robot, broker settings or source changes. Zero 2024+ candle reads; content-hidden syscall receipts published.',
        'Changed files: only new study package, separate parameterized strategy and new results under IntradayLab/. No Roadmap lifecycle advancement. One Draft PR; no merge/auto-merge; STOP.','']
    (output/'Task_Summary.md').write_text('\n'.join(lines))
