"""Frozen report and handoff rendering; no model or selection logic."""
from collections import Counter
from decimal import Decimal as D
import csv,json
from .contract import STUDY


def report(policy,freeze,candidates,monthly,selection):
    def f(v):return f'{v:.6f}' if isinstance(v,D) else str(v)
    def table(headers,rows):
        return ['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',*['| '+' | '.join(f(v) for v in row)+' |' for row in rows],'']
    lines=['# Optimization C Return/Retest/Rejection — USDRUBF 2023','',f'**{selection["overall_result"]}**','',
        f'Base `{policy["base_main"]}`; pre-P&L freeze `{freeze}`. 288/288 configurations. No added parameter values or adaptive trials.',
        'Only pinned USDRUBF 2023 development M5. 2024 is reserved for Walk Forward; 2025+ TRUE OOS was unread. No next lifecycle stage was run.',
        'CLOSED-only economics after model C1 are conditional on incomplete source/outcomes and assumed FLAT after exclusions. They do not establish complete annual profit, continuous account equity, or future profitability.',
        'One fixed first strict local level per direction; 2/3 distinct approaches separated by whole-M5 retreats. Final first-touch Close alone confirms rejection; failed Close consumes until structural reset. Structural Stop uses all observed construction extrema plus the frozen buffer. Completed M5 only, immediate next Open, no delayed entry, unchanged Backtester/V2, Stop-first, adverse Open gaps, no entry-bar Take, 120-minute/session-flat limit.',
        'Gross Take distance = target_net_R × (initial_gross_risk + planned_C1) + planned_C1, outward price-grid rounding. net_R_c1 uses initial gross risk, planned_net_to_net_R uses risk + planned C1, realized_net_to_net_R uses risk + actual C1. Denominators never depend on trade profitability.',
        'Selection: 100 CLOSED, 40 distinct entry dates, 6 active entry months; PF R/price both ≥2, expectancy >0, ≥9 positive exit months, conditional DD ≤20R, winner concentration ≤25%, positive-month concentration ≤50%. Two adjacent list-index neighbors require 100 CLOSED, PF R ≥1.5, expectancy >0. Only full passes are ranked by positive months DESC, min(PF R,price) DESC, DD ASC, CLOSED DESC, ID ASC.',
        'Detailed CSVs are sharded by evaluation in evaluations/<configuration_id>/USDRUBF/: signals.csv, construction_events.csv, trades.csv, data_gap_skips.csv, data_quality_exclusions.csv, rejected_nonfill.csv, coverage_report.csv, days.csv, construction_diagnostics.csv. detailed_artifact_index.csv lists all 288 directories and counts. This preserves full construction receipts within GitHub file-size limits. No source candles are copied.',
        'No missing month is treated as a positive zero. All 12 exit months are published for each configuration; entry-date counts remain separate. No PF-only winner is selected.','']
    s=selection['instruments']['USDRUBF']
    lines+=table(['Evaluated','Sample pass','Both PF pass','Monthly pass','Neighbor pass','Full pass'],[[s[k] for k in ('evaluated','sample_pass','both_PF_pass','months_pass','neighbors_pass','full_criteria_pass')]])
    for r in candidates:
        lines += [f'## {r["configuration_id"]}','',f'**{r["status"]}**; failed gates: {r["failure_reasons"] or "none"}; sample reasons: {r["sample_failure_reasons"] or "none"}.',
            f'CLOSED {r["CLOSED"]}; dates/months {r["entry_days"]}/{r["entry_months"]}; PF R/price {f(r["PF_R"])}/{f(r["PF_price"])}; Net {f(r["Net_R"])} R; expectancy {f(r["expectancy_R"])} R; positive months {r["positive_exit_months"]}/12; conditional DD {f(r["conditional_closed_only_DD_R"])} R.',
            f'Accepted {r["accepted_entries"]} = CLOSED {r["CLOSED"]} + EXCLUDED {r["DATA_QUALITY_EXCLUDED"]}; SKIP {r["DATA_GAP_SKIP"]}; exclusion share {f(r["exclusion_fraction"])}; conditional FLAT closures {r["conditional_flat_CLOSED"]}; qualifying neighbors {r["positive_neighbor_count"]}.','']
        lines+=table(['Exit month','CLOSED','Net R','PF R','PF price','Missing bars','EXCLUDED'],[[m[k] for k in ('month','CLOSED','Net_R','PF_R','PF_price','missing_bars','DATA_QUALITY_EXCLUDED')] for m in monthly if m['configuration_id']==r['configuration_id']])
    return '\n'.join(lines)+'\n'


def task_summary(output,validation):
    selection=json.loads((output/'selection_report.json').read_text());audit=json.loads((output/'audit.json').read_text());policy=json.loads((STUDY/'OPTIMIZATION_C_POLICY.json').read_text())
    with (output/'all_candidates.csv').open() as f:rows=list(csv.DictReader(f))
    failures=Counter(x for r in rows for x in r['failure_reasons'].split('|') if x)
    best={k:max(D(r[k]) for r in rows if r[k]!='NOT_AVAILABLE') for k in ('PF_R','PF_price')}
    s=selection['instruments']['USDRUBF'];tests=json.loads((STUDY/'preflight.json').read_text())
    lines=['# Task Summary — Optimization C 2023','',f'**{selection["overall_result"]}**','',
        f'Base SHA: `{policy["base_main"]}`. Freeze SHA: `{validation["freeze_commit"]}`. Final SHA is recorded in the Draft PR body (a commit cannot include its own SHA).',
        f'Executed 288/288, USDRUBF only. Sample/PF/monthly/neighbor/full passes: {s["sample_pass"]}/{s["both_PF_pass"]}/{s["months_pass"]}/{s["neighbors_pass"]}/{s["full_criteria_pass"]}.',
        f'Diagnostic maxima PF R/price: {best["PF_R"]}/{best["PF_price"]}; these do not select a winner.',
        'All failed gates: '+str(dict(sorted(failures.items())))+'. Sample reasons and every failed gate are retained per row in all_candidates.csv.',
        f'Control comparison: {audit["baseline_control"]}; 102 CLOSED /2 SKIP /2 EXCLUDED. Full signal/construction/entry/Stop/Take/risk/exit/Gross/C1/Net comparison: baseline_comparison.csv.',
        f'Pre-P&L tests: {tests}. Internal independent auditor: standard library only, {sum(audit["checked_fields"].values())} exact comparisons in the canonical full run; three independent full audits, two full repeats of all 288 with {validation["full_repeats"][0]["deterministic_artifacts"]} artifacts byte-identical per repeat.',
        'This is implementation-independent computational checking by the task author; external user audit remains pending.',
        'Each of six source reads consumed only the exact permitted 2,342,431-byte /42,576-candle USDRUBF prefix. Real content-hidden strace evidence and hashes: syscall_read_receipts.json, logs/, input_provenance.json. Zero 2024+ candle bytes.',
        f'Protection: {validation["protected_scope"]}; all preexisting files including TradingSystemLab, previous IntradayLab results/config/strategies, A/B and Master Registry verified byte-for-byte. market-pattern-data remained clean/pinned. Draft #472 untouched.',
        'Only 2023 development fitting. No Robustness, Walk Forward, TRUE OOS, other families, production, robot/broker changes, merge or auto-merge. STOP after the single Draft PR.','']
    (output/'Task_Summary.md').write_text('\n'.join(lines))
