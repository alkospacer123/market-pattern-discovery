# Post-v3 Stage 6 IMOEXF Marginal Contribution Audit

## Status

**AUDIT-ONLY / NO STAGE 6 DECISION CHANGE**

This artifact records the observed marginal contribution of `IMOEXF` inside the frozen
v3 `T3/H1` Stage 6 production-parent evidence. It is a diagnostic/audit record only.
It does **not** modify the frozen Stage 6 production assembly and does **not** authorize
Stage 7 to remove an instrument.

## Provenance

- Repository: `alkospacer123/market-pattern-discovery`
- Audited `main` SHA: `3687b65d591659f91ae9ecf8c93f775c3b10a44c`
- Stage 6 assembly ID: `PROD_STAGE6_83C7B31BB42C`
- Frozen Stage 6 instrument set: `CNYRUBF;GLDRUBF;IMOEXF`
- Strategy / timeframe: `T3 / H1`
- Stage 6 structural overlay: `TRAIL1`
- Economic authority: `CORRECTED_SINGLE_C1`
- Research tick: `0.001`
- External audit workbook: `TradingSystemLab_T3H1_instrument_monthly_yearly_audit.xlsx`
- External workbook SHA-256: `6c4478411929fd1476a43b9c2b35a766bce86752cd3bbd937747b43971fbfbcb`

The XLSX is intentionally not committed as a repository research authority. Its SHA-256
is recorded here so the exact external workbook can be identified later. The underlying
source of truth remains repository text/CSV/JSON trade evidence.

## Important scope distinction

The marginal-contribution figures in this document are from the corrected
`CORRECTED_SINGLE_C1` **canonical/base-exit basket verification** reconstructed from
immutable v3 `T3/H1` trades. They are **not** an exact two-instrument `TRAIL1` backtest.

Therefore this audit cannot answer whether the selected `TRAIL1` overlay remains equally
useful after removing `IMOEXF`. That question requires a separate predeclared test.

## Marginal contribution of IMOEXF

Relative to the same-period `CNYRUBF + GLDRUBF` artifact-only basket, adding `IMOEXF`
contributed:

| Lifecycle | CNY+GLD net R | CNY+GLD+IMOEX net R | IMOEXF marginal net R |
|---|---:|---:|---:|
| Baseline | 42.194012 | 55.960683 | **+13.766671** |
| Walk Forward | 18.291429 | 26.643396 | **+8.351967** |
| TRUE OOS | 58.966032 | 62.289137 | **+3.323105** |

The contribution is positive in all three lifecycle views, but its magnitude is much
smaller in revealed TRUE OOS than in Baseline or Walk Forward.

## TRUE OOS: two-instrument vs three-instrument basket

Period represented by the current TRUE OOS trade evidence: `2025-01` through `2026-09`
(last admitted parent OOS close is in September 2026).

| Metric | CNYRUBF + GLDRUBF | CNYRUBF + GLDRUBF + IMOEXF |
|---|---:|---:|
| Trades | 92 | 150 |
| Net R | 58.966032 | 62.289137 |
| PF | **3.187491** | 2.223430 |
| Expectancy R/trade | **0.640935** | 0.415261 |
| Trade-level max DD R | **-5.757188** | -7.153150 |
| Positive-month share | 0.523810 | 0.523810 |
| Monthly std R | **6.137669** | 6.242182 |
| Worst month R | **-2.519658** | -3.643717 |
| Monthly-equity DD R | **-4.599157** | -5.434723 |
| Co-loss months | **4** | 6 |

Adding `IMOEXF` increases TRUE OOS net R by approximately `+3.32 R`, but also adds 58
trades and worsens PF, expectancy, trade-level drawdown, worst month, monthly-equity
drawdown, and the count of co-loss months in this canonical/base-exit comparison.

## IMOEXF standalone recent evidence

For `IMOEXF` in calendar year 2026 through the available September 2026 evidence:

- Trades: `30`
- Net R: **`-0.502042 R`**
- PF: **`0.961720`**
- Rolling 6-month net R ending `2026-09`: **`-1.709737 R`**

This is a monitoring signal, not permission to delete the instrument. The same instrument
was positive in earlier evidence and had a material positive contribution in Baseline and
Walk Forward.

## Co-loss observation

In TRUE OOS, the artifact-only basket comparison records:

- `CNYRUBF + GLDRUBF`: **4** co-loss months
- `CNYRUBF + GLDRUBF + IMOEXF`: **6** co-loss months

For this audit, a co-loss month means at least two available instruments in the basket
have negative monthly `net_R` in the same calendar month.

## Frozen decision guard

**The Stage 6 decision does not change at this stage.**

The following remain frozen by Stage 6:

- production assembly ID: `PROD_STAGE6_83C7B31BB42C`
- generation: `v3`
- strategy: `T3`
- timeframe: `H1`
- instrument set: `CNYRUBF;GLDRUBF;IMOEXF`
- structural overlay: `TRAIL1`

No edit to `production_assembly_decision.csv` is authorized by this audit.

## Identity guard if IMOEXF is removed later

**Removing `IMOEXF` would create a new production/research identity. It is not a Stage 7
specification-freeze edit to the existing Stage 6 assembly.**

Because the `2025-2026` TRUE OOS evidence has already been revealed and is being used to
motivate this question, it cannot become untouched validation evidence for a new
`CNYRUBF + GLDRUBF` identity. A two-instrument identity must be explicitly declared,
its frozen rules recorded, and subsequent validation must not pretend that the already
observed OOS is fresh holdout evidence.

## Required next tests before any assembly change

### Test 1 — TRAIL1 on the two-instrument basket

Predeclare and evaluate the same frozen `TRAIL1` semantics with no threshold change and no
parameter search for:

1. `CNYRUBF + GLDRUBF`
2. `CNYRUBF + GLDRUBF + IMOEXF`
3. standalone `IMOEXF`

Report at minimum: trades, Net R, PF, expectancy, max DD, monthly Net R, monthly-equity DD,
positive-month share, worst month, co-loss months, and per-lifecycle evidence.

The standalone IMOEXF comparison is especially important because current corrected
canonical OOS contribution is only about `+3.32 R`, while the previously observed
TRAIL1 standalone OOS net result is approximately `+13.19 R`. The test must determine
whether this difference is a genuine frozen-overlay effect or an artifact of portfolio
composition/accounting scope. Do not change the `+1R` TRAIL1 trigger or ATR trail rules.

### Test 2 — cost sensitivity

Run a deterministic friction sensitivity from the corrected single-C1 authority for both:

1. `CNYRUBF + GLDRUBF`
2. `CNYRUBF + GLDRUBF + IMOEXF`

Use cost multipliers `1.0x`, `1.5x`, and `2.0x` applied to the same frozen trade paths.
No signal or exit path may change because of this sensitivity calculation.

For T3 corrected economics, interpret this as a cost-only overlay on immutable trades:
`net_R(m) = corrected_single_C1_net_R - (m - 1) * C1_round_trip_cost_R`.

This is a **research friction-sensitivity test**, not yet the literal Stage 7 broker/exchange
production tariff. The actual production cost model remains a Stage 7 item and must be
frozen separately from current broker/exchange data.

Report the break-even/effect-disappearance point for the marginal value of `IMOEXF`, if it
occurs within or can be linearly bracketed from the predeclared multipliers without adding
a parameter search.

## Explicit non-actions

Do **not**:

- silently delete `IMOEXF`;
- edit the current Stage 6 production assembly based on this audit alone;
- optimize or retune TRAIL1;
- change the `+1R` TRAIL1 trigger;
- use revealed `2025-2026` OOS as untouched validation for a new two-instrument identity;
- broaden the instrument search to BR/NG or other markets;
- convert diagnostic evidence into a new rule without an explicit identity and validation
  decision.

## Prospective evidence rule

Any future `extended forward` evidence used to adjudicate a new two-instrument identity
must be strictly prospective relative to the already revealed evidence (i.e. after the
current last admitted OOS data) and must use the predeclared frozen rules unchanged.
Until such genuinely new data accumulates, the existing Stage 6 assembly remains the
frozen production-assembly decision.
