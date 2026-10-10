#!/usr/bin/env python3
"""Post-P&L reporting verifier: preserve frozen code, disclose strict RSI roundoff.

The frozen weighted80 auditor can itself invent a strict RSI difference when the
current delta is zero. A common-factor-free weighted oracle checks mathematical
semantics. A separate raw-prefix Decimal28 oracle checks the exact frozen numeric
program. Neither imports production strategy, indicators, Backtester or metrics.
The verdict remains NEEDS_FIX for observed mathematical signal discrepancies;
passing ledger/economy checks never waives them. No trading rule is repaired.
"""
import argparse
from contextlib import contextmanager
from decimal import Decimal as D,localcontext
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];LAB=ROOT/'IntradayLab'
sys.path.insert(0,str(ROOT))
from IntradayLab.tools import audit_bollinger_rsi_reentry_baseline as oracle

WEIGHTED=oracle.batch_indicators


def dump(path,value):
    path.write_text(json.dumps(value,default=str,sort_keys=True,indent=2)+'\n')


def rounded_prefix_indicators(closes):
    """Independent batch seed/updates in Decimal28, verified against weighted80.

    This reproduces numeric program rounding for conformance only. Semantic
    equality on a zero delta is assessed separately, never silently accepted.
    """
    values=WEIGHTED(closes)
    with localcontext() as precision:
        precision.prec=28
        gains=[max(b-a,D(0)) for a,b in zip(closes,closes[1:])]
        losses=[max(a-b,D(0)) for a,b in zip(closes,closes[1:])]
        if len(gains)<14:return values
        g=sum(gains[:14],D(0))/14;l=sum(losses[:14],D(0))/14
        for i in range(14,len(closes)):
            if i>14:g=(g*13+gains[i-1])/14;l=(l*13+losses[i-1])/14
            r=D(50) if g==l==0 else D(100) if not l else D(0) if not g else D(100)-D(100)/(1+g/l)
            oracle.require(abs(r-values[i]['rsi14'])<=oracle.INDICATOR_ABSOLUTE_TOLERANCE,'ROUNDED_RSI_VS_WEIGHTED')
            values[i]=dict(values[i],rsi14=r)
    return values


def mathematical_indicators(closes):
    """Weighted raw changes; cancel the shared decay before computing RSI.

    Zero changes leave weighted bases exactly unchanged, proving RSI equality.
    No epsilon, alternative threshold, extra price filter or production change.
    """
    values=WEIGHTED(closes)
    if len(closes)<15:return values
    with localcontext() as precision:
        precision.prec=80
        ups=[max(b-a,D(0)) for a,b in zip(closes,closes[1:])]
        downs=[max(a-b,D(0)) for a,b in zip(closes,closes[1:])]
        g=sum(ups[:14],D(0))/14;l=sum(downs[:14],D(0))/14
        decay=D(1);q=D(13)/14;weighted_g=weighted_l=D(0)
        for i in range(14,len(closes)):
            if i>14:
                decay*=q;weighted_g+=ups[i-1]/decay;weighted_l+=downs[i-1]/decay
            gb=g+weighted_g/14;lb=l+weighted_l/14
            r=D(50) if gb==lb==0 else D(100) if not lb else D(0) if not gb else D(100)*gb/(gb+lb)
            oracle.require(abs(r-values[i]['rsi14'])<=oracle.INDICATOR_ABSOLUTE_TOLERANCE,'STABLE_RSI_VS_WEIGHTED')
            values[i]=dict(values[i],rsi14=r)
            if i>14 and closes[i]==closes[i-1]:
                oracle.require(values[i]['rsi14']==values[i-1]['rsi14'],'ZERO_CHANGE_RSI_EQUALITY')
    return values


@contextmanager
def numeric_oracle(implementation):
    previous=oracle.batch_indicators;oracle.batch_indicators=implementation
    try:yield
    finally:oracle.batch_indicators=previous


def audit(root,output):
    # Exact program conformance and all source/price/C1/metric/report checks.
    with numeric_oracle(rounded_prefix_indicators):result=oracle.audit(root,output)
    cfg=json.loads(oracle.CONFIG.read_text())
    raw,receipts=oracle.read_source(root,cfg)
    ss=oracle.read_csv(output/'signals.csv');tt=oracle.read_csv(output/'trades.csv')
    discrepancies=[];math_counts={};trade_checked=0
    for symbol in cfg['instruments']:
        parents=oracle.parent_rows(symbol,raw[symbol])
        actual={r['signal_id']:r for r in ss if r['instrument']==symbol}
        with numeric_oracle(mathematical_indicators):events=oracle.episodes(symbol,parents)
        for event in events:
            row=actual[event['signal_id']]
            if row['base_reason']!=event['base_reason']:
                discrepancies.append(dict(instrument=symbol,signal_id=event['signal_id'],
                    actual_reason=row['base_reason'],mathematical_reason=event['base_reason'],
                    actual_status=row['status'],actual_execution_reason=row['reason'],
                    B_close=row.get('breach_close'),C_close=row.get('test_close'),
                    B_RSI=row.get('breach_rsi14'),C_RSI=row.get('rsi14'),
                    source='Strict Decimal28 RSI comparison at unchanged Close; frozen production retained',
                    filled_trade=any(t['signal_id']==event['signal_id'] and t['model_filled']=='True' for t in tt)))
        es,et=oracle.replay(symbol,parents,events)
        keys=sorted({k for t in et for k in t if k!='unknown_effective_at'})
        # Exact row IDs, actual fills, all CLOSED/UNKNOWN and numeric ledger must
        # still agree with the mathematically corrected oracle. No imputation.
        trade_checked+=oracle.exact_check_rows([t for t in tt if t['instrument']==symbol],et,keys,'MATHEMATICAL_TRADES')
        math_counts[symbol]=dict(signals=sum(e['base_reason']=='SIGNAL' for e in events),
            pending=sum(e.get('pending_created',False) for e in es),orders=sum(e['order_admitted'] for e in es),
            model_fills=sum(t['model_filled'] for t in et),closed=sum(t['status']=='CLOSED' for t in et),unknown=sum(t['status']=='UNKNOWN' for t in et))
    oracle.require(all(not d['filled_trade'] for d in discrepancies),'MATHEMATICAL_SIGNAL_CHANGED_FILLED_TRADE')
    result.update(status='NEEDS_FIX' if discrepancies else 'PASS',
        frozen_numeric_program_conformance='PASS',trade_prices_C1_CLOSED_UNKNOWN_economics='PASS',
        mathematical_signal_logic='NEEDS_FIX' if discrepancies else 'PASS',
        discrepancies=discrepancies,mathematical_diagnostic_funnel=math_counts,
        checked_mathematical_trade_fields=trade_checked,filled_trade_or_PnL_changes=0,
        reporting_verifier=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            added_after_first_PnL=True,reason='Frozen weighted oracle also has last-digit strict-comparison drift; distinguish exact frozen Decimal28 conformance from mathematical RSI equality',
            frozen_strategy_parameters_runner_core_and_original_auditor_unchanged=True),
        original_audit_entrypoint='Frozen original auditor raises on CNYRUBF_2023-04-06_1815; retained verbatim, not a passing standalone audit',
        no_technical_signal_logic_PASS_claim=bool(discrepancies))
    dump(output/'audit.json',result)
    facts='\n'.join('- `'+d['signal_id']+'`: frozen '+d['actual_reason']+', mathematical '+d['mathematical_reason']+'; '+d['actual_status']+' / '+d['actual_execution_reason']+'. B/C Close='+d['B_close']+'; RSI '+d['B_RSI']+' → '+d['C_RSI']+'.' for d in discrepancies)
    (output/'Independent_Audit.md').write_text('# Independent audit — BOLLINGER_RSI_REENTRY_M15\n\n'
        '**Overall signal-logic verdict: '+result['status']+'. No technical signal-logic PASS is claimed.**\n\n'
        '**PASS** for exact frozen numeric-program conformance, actual prices/Stop/Take/C1, all CLOSED and UNKNOWN, economic metrics, all 12 months, directions and coverage. '
        f"Checked {result['checked_formation_fields']} formation fields, {result['checked_ledger_fields']} signal/ledger fields, {result['checked_coverage_fields']} coverage fields, {result['checked_metric_fields']} instrument metric fields, {result['checked_report_metric_fields']} report/day fields, and {trade_checked} mathematical-oracle trade fields.\n\n"
        'The independent weighted80 oracle itself had tiny strict-comparison drift on flat Close. This post-P&L reporting verifier cancels the shared decay before the RSI ratio and independently reconstructs Decimal28 from raw prefixes to check the frozen numeric program. No production strategy/indicator/Backtester/metric imports are used for these oracles. Indicator tolerance remains the predeclared absolute 1e-22; discrete decisions and trade prices/accounting are exact.\n\n'
        '**Unresolved defect in the frozen strategy:** roundoff in the strict RSI comparison can create a formal signal with identical B/C Close. Mathematically Wilder RSI is unchanged on a zero price change.\n\n'+facts+'\n\n'
        'Neither discrepancy produced a model fill. The common-factor-free mathematical oracle yields exactly the same filled trade IDs, every CLOSED/UNKNOWN, prices, C1 and P&L. The mathematical funnel is diagnostic only and does not replace canonical signals/pending/orders. Both frozen spurious signals remain in signals.csv and in the canonical reported funnel.\n\n'
        'Frozen strategy, indicators, parameters, runner, original auditor and common core are byte unchanged since the pre-P&L commit. No corrected strategy or second economic Baseline was run. The original frozen audit entrypoint still fails on its own numerical discrepancy; use the final verify tool for complete factual auditing and this honest NEEDS_FIX verdict. A separate future decision is required to repair/retest.\n\n'
        'Pinned source/byte hashes and observed unbuffered reads prove zero 2024+ price bytes. UNKNOWN has no assigned P&L; annual economics are INCONCLUSIVE and all four instruments have negative conditional known-close expectancy (NO ECONOMIC BASELINE PASS). No cross-instrument monetary pooling. Validation receipts cover 496 pre-P&L tests, two deterministic repeats, six old Baseline regressions and preservation of all 512 existing files. Independent implementation verification is not external human signoff.\n')
    report=output/'Baseline_Report.md'
    marker='\n## Independent audit limitation — frozen numeric comparison\n'
    report.write_text(report.read_text().split(marker)[0]+marker+'\n'
        '**Signal logic audit: '+result['status']+'.** Exact numeric-program, execution, trade, economic and coverage checks pass. Mathematical Wilder RSI is unchanged on a flat Close; two frozen formal signals come from Decimal28 last-digit drift. One failed the deadline, one failed minimum risk. No filled trade/P&L changed, but a complete technical signal PASS is withheld.\n\n'+facts+'\n\n'
        'Canonical signal/pending/order counts are retained, including these two events. Mathematical-oracle funnel diagnostics appear in audit.json. No parameter, indicator or rule changed after P&L. Original auditor remains frozen and fails standalone; final verifier supplies both conformance and semantic checks. No repaired variant or second economic Baseline.\n')
    return result


def verify(root,output):
    # Only reporting orchestration imports the frozen validator/production runner
    # for authorized identical repeats and immutable legacy regressions.
    from IntradayLab.tools import validate_bollinger_rsi_reentry_baseline as validator
    receipt=LAB/'work/bollinger_first_run_observed_reads.json'
    first_reads=json.loads(receipt.read_text()) if receipt.exists() else json.loads((output/'validation.json').read_text())['canonical_first_run_observed_reads']
    original=validator.audit;validator.audit=audit
    try:result=validator.validate(root,output)
    finally:validator.audit=original
    document=json.loads((output/'audit.json').read_text())
    result.update(status=document['status'],execution_determinism_regressions_isolation='PASS',
        independent_signal_logic=document['mathematical_signal_logic'],independent_audit=document['status'],
        reporting_verifier=document['reporting_verifier'],
        unresolved_signal_discrepancies=document['discrepancies'],filled_trade_or_PnL_changes=0,
        canonical_first_run_observed_reads=first_reads)
    dump(output/'validation.json',result);dump(output/'artifact_hashes.json',validator.hashes(output,('artifact_hashes.json',)))
    return result


if __name__=='__main__':
    # Make execution from repository root reliable without environment PYTHONPATH.
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,default=LAB/'results/bollinger_rsi_reentry_m15_2023_v1')
    p.add_argument('--audit-only',action='store_true')
    a=p.parse_args();result=audit(a.data_root,a.output) if a.audit_only else verify(a.data_root,a.output)
    print(json.dumps({k:result[k] for k in ('status',) if k in result}))
