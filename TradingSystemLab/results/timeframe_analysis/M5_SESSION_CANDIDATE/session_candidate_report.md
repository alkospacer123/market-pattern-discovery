# M5 session filter candidate research

Status: `PHASE_M5_SESSION_CANDIDATE_COMPLETE`

## Hypothesis

Entries are restricted to Monday–Friday, 10:00 inclusive to 17:00 exclusive, using the existing trading timezone.

This report evaluates evidence only. It does not claim improvement, select a winner, or optimize a window.

## Overall comparison

- T2 BASELINE: trades=830, PF=1.105729333922172, expectancy_R=0.06103566802799663, net_R=50.6596044632372, max_drawdown_R=-56.42261250073461, recovery_factor=0.8978599575228394, win_rate=0.3024096385542169.
- T2 SESSION_FILTER: trades=535, PF=1.3157170892358236, expectancy_R=0.17361139944744086, net_R=92.88209870438087, max_drawdown_R=-23.42122396180699, recovery_factor=3.965723518798325, win_rate=0.30280373831775703.
- T3 BASELINE: trades=1131, PF=1.1574920463357858, expectancy_R=0.07739191009617423, net_R=87.53025031877306, max_drawdown_R=-42.81216229219696, recovery_factor=2.0445183245212193, win_rate=0.3748894783377542.
- T3 SESSION_FILTER: trades=814, PF=1.2877869999197504, expectancy_R=0.1389224424908676, net_R=113.08286818756622, max_drawdown_R=-24.258024378782835, recovery_factor=4.661668502834617, win_rate=0.3845208845208845.
- COMBINED BASELINE: trades=1961, PF=1.133527094399683, expectancy_R=0.07046907434064777, net_R=138.18985478201026, max_drawdown_R=-46.858478142798795, recovery_factor=2.9490896900425105, win_rate=0.34421213666496686.
- COMBINED SESSION_FILTER: trades=1349, PF=1.2997451804824602, expectancy_R=0.15267973824458642, net_R=205.96496689194709, max_drawdown_R=-34.06924628035392, recovery_factor=6.045480583781423, win_rate=0.352112676056338.

Instrument, direction, weekday, session, and holding-duration evidence is retained in the CSV artifacts.
Only entry eligibility changed; strategy logic, parameters, exits, risk, stops, and trailing logic are unchanged.
TRUE OOS was blocked and no winner was selected.
