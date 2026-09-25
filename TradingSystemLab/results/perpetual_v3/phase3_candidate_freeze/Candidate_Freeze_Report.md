# TradingSystemLab v3 Perpetual Phase 3 Candidate Freeze

**Status:** `V3_PERPETUAL_PHASE_3_CANDIDATE_FREEZE_COMPLETE`

This artifact-only freeze applies the original H1 predeclared-candidate contract to committed v3 Phase 2 Development evidence.

No metric ranking, parameter search, raw market-data read, strategy execution, Robustness, Walk Forward, or TRUE OOS access occurred.

## T2 / M30 — `T2_M30_candidate_v3`

- Phase 2 configuration ID: `T2-M30-608dc87d09f1`
- Single Baseline change: `max_initial_stop_atr: 3.0 -> 2.5`
- Phase 2 classification: `ROBUST_PLATEAU`
- Trades: 324; PF: 1.7118816595; expectancy: 0.310463258155; net R: 100.590095642; max DD: -16.3334012952; recovery: 6.15855165892
- Instrument expectancies: USDRUBF 0.353647615402; CNYRUBF 0.249324632747; GLDRUBF 0.256821689906; IMOEXF 0.382662754787
- Year expectancies: 2023 0.260229266002; 2024 0.336641535756
- Direction expectancies: LONG 0.406009030942; SHORT 0.164158793574
- Top-3 positive-R share: 0.137424664978; expectancy without top 3: 0.209807462063
- Full parameter hash: `608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b`
- Selection reason: Predeclared ROBUST_PLATEAU member with positive instrument, Development-year, direction, and top-three-removed expectancy evidence. Maximum PF was not used as the selection method; declaration preceded Robustness and used no validation or future data.

## T2 / H1 — `T2_H1_candidate_v3`

- Phase 2 configuration ID: `T2-H1-608dc87d09f1`
- Single Baseline change: `max_initial_stop_atr: 3.0 -> 2.5`
- Phase 2 classification: `ROBUST_PLATEAU`
- Trades: 156; PF: 2.39295957746; expectancy: 0.575052042961; net R: 89.708118702; max DD: -6.88205022139; recovery: 13.0350863211
- Instrument expectancies: USDRUBF 0.955413840294; CNYRUBF 0.510119909468; GLDRUBF 0.24672749816; IMOEXF 0.577886945127
- Year expectancies: 2023 0.642222075901; 2024 0.540488822128
- Direction expectancies: LONG 0.768074826871; SHORT 0.165843741073
- Top-3 positive-R share: 0.198164164771; expectancy without top 3: 0.386726768403
- Full parameter hash: `608dc87d09f10aa0e03026ebb525f6b8ec865060c7890cee08fa0c7ed14cf86b`
- Selection reason: Predeclared ROBUST_PLATEAU member with positive instrument, Development-year, direction, and top-three-removed expectancy evidence. Maximum PF was not used as the selection method; declaration preceded Robustness and used no validation or future data.

## T3 / M30 — `T3_M30_candidate_v3`

- Phase 2 configuration ID: `T3-M30-d6feb972db57`
- Single Baseline change: `breakout_period: 20 -> 30`
- Phase 2 classification: `ROBUST_PLATEAU`
- Trades: 341; PF: 1.93094457407; expectancy: 0.376193476605; net R: 128.281975522; max DD: -15.012134415; recovery: 8.54521895261
- Instrument expectancies: USDRUBF 0.596841887079; CNYRUBF 0.272441005258; GLDRUBF 0.195361667183; IMOEXF 0.407065971914
- Year expectancies: 2023 0.455063193545; 2024 0.326993796038
- Direction expectancies: LONG 0.337958257864; SHORT 0.436732572945
- Top-3 positive-R share: 0.0917419420782; expectancy without top 3: 0.3073115794
- Full parameter hash: `d6feb972db575bf6e66ac901be95fe079dccc82d9e2c3e880d17faeae8d1adf9`
- Selection reason: Predeclared ROBUST_PLATEAU member with positive instrument, Development-year, direction, and top-three-removed expectancy evidence. Maximum PF was not used as the selection method; declaration preceded Robustness and used no validation or future data.

## T3 / H1 — `T3_H1_candidate_v3`

- Phase 2 configuration ID: `T3-H1-4e73cdb77246`
- Single Baseline change: `stop_atr: 2.0 -> 2.5`
- Phase 2 classification: `ROBUST_PLATEAU`
- Trades: 181; PF: 2.31342650378; expectancy: 0.399304363394; net R: 72.2740897743; max DD: -5.67342240555; recovery: 12.7390637622
- Instrument expectancies: USDRUBF 0.352462573457; CNYRUBF 0.42264272293; GLDRUBF 0.254664073019; IMOEXF 0.69511314551
- Year expectancies: 2023 0.215617210473; 2024 0.492678666128
- Direction expectancies: LONG 0.329007784983; SHORT 0.530970970575
- Top-3 positive-R share: 0.170746383517; expectancy without top 3: 0.283920601325
- Full parameter hash: `4e73cdb77246cb07b5953160b9fc0ab36bfd4bd6d9a7f7faaae7e6e392ee340a`
- Selection reason: Predeclared ROBUST_PLATEAU member with positive instrument, Development-year, direction, and top-three-removed expectancy evidence. Maximum PF was not used as the selection method; declaration preceded Robustness and used no validation or future data.

## Lifecycle lock

After merge, these candidate parameters are immutable for the next Robustness task. Robustness must consume the exact registry bytes from this directory. A weak, borderline, or rejected result does not permit replacement, return to the 25-member inventory, or a second selection. Any parameter change creates a new research identity and requires return to an earlier research stage.

TRUE OOS >= 2025-01-01 remains `BLOCKED_NOT_READ_NOT_EXECUTED`. No validation or future data were used for declaration.
