# Final Fixed-Basket Production Reassessment

## Authority and safety

Actual main was authenticated as `c0dfcc9397f0fb825b3937cfc06fcb7a8fde12e8`. Exactly six predeclared identities were replayed; no Stage 7 action occurred. Historical 2025–2026 results are revealed evidence, not fresh OOS. 2026 is a `PARTIAL_YEAR`. The frozen Stage 6 identity and all protected evidence remain unchanged.

| Basket   | Exit      |      2023 |      2024 |      WF24 |      2025 |   2026 YTD |   Chronological Net R |   Worst DD |   Min Recovery |   Worst 6M |   Worst 12M |   Positive Months | Gate   |
|:---------|:----------|----------:|----------:|----------:|----------:|-----------:|----------------------:|-----------:|---------------:|-----------:|------------:|------------------:|:-------|
| A        | canonical |  0.549982 | 50.750000 | 26.643396 | 29.217577 |  33.071561 |            113.589120 |  -7.153150 |       7.903414 |  -6.224979 |    0.549982 |          0.526316 | PASS   |
| B        | TRAIL1    | -3.450404 | 58.873709 | 32.968262 | 32.158460 |  32.908838 |            120.490603 | -12.108415 |       4.577255 |  -9.790881 |   -3.729475 |          0.578947 | FAIL   |
| C        | canonical | 13.698604 | 60.011015 | 38.729866 | 36.347441 |  49.388980 |            159.446041 | -11.719118 |       7.315945 |  -3.494830 |   13.698604 |          0.578947 | PASS   |
| D        | TRAIL1    | 11.927668 | 69.995783 | 46.825228 | 41.617436 |  46.287029 |            169.827916 | -14.451470 |       6.082735 |  -9.260095 |   10.167549 |          0.596491 | PASS   |
| E        | canonical | 12.764529 | 38.162621 | 20.663151 | 26.332705 |  36.638134 |            113.897989 | -10.225463 |       6.158239 |  -1.756235 |   11.828146 |          0.561404 | PASS   |
| F        | TRAIL1    | 12.815822 | 47.014161 | 26.139516 | 30.503246 |  37.248516 |            127.581745 | -11.866656 |       5.709423 |  -5.153166 |    9.726366 |          0.614035 | PASS   |

## Required answers

1. **Negative-year failures:** B.
2. **All-gate passes:** A, C, D, E, F.
3. **Highest annual floor:** C.
4. **Lowest severe DD:** A.
5. **Best minimum recovery:** A.
6. **Highest chronological profitability:** D.
7. **Monthly stability leader by positive-month share:** F.
8. **CNY beside USD:** the diversification table reports both correlations and realized offset months; correlation alone is not treated as substitutability.
9. **Replacing CNY with USD:** compare A/B directly with E/F in the table; the annual floor remains the primary criterion.
10. **CNYRUBF+GLDRUBF+IMOEXF:** TRAIL1 profitability=True, annual-floor=False, DD=False, recovery=False, monthly consistency=True, introduces negative year=True.
10. **USDRUBF+CNYRUBF+GLDRUBF+IMOEXF:** TRAIL1 profitability=True, annual-floor=False, DD=False, recovery=False, monthly consistency=True, introduces negative year=False.
10. **USDRUBF+GLDRUBF+IMOEXF:** TRAIL1 profitability=True, annual-floor=True, DD=False, recovery=False, monthly consistency=True, introduces negative year=False.
11. **Historically best-supported candidate:** C, selected only after the annual gate via the declared hierarchy.
12. **Identity consequence:** requires a new identity and prospective validation after the revealed period; it is not promoted here.

## 2023 diagnosis

| basket   | path      |   USDRUBF_net_R |   CNYRUBF_net_R |   GLDRUBF_net_R |   IMOEXF_net_R |     net_R |
|:---------|:----------|----------------:|----------------:|----------------:|---------------:|----------:|
| A        | canonical |        0.000000 |        0.934075 |       -0.384093 |       0.000000 |  0.549982 |
| B        | TRAIL1    |        0.000000 |       -0.888154 |       -2.562251 |       0.000000 | -3.450404 |
| C        | canonical |       13.148622 |        0.934075 |       -0.384093 |       0.000000 | 13.698604 |
| D        | TRAIL1    |       15.378072 |       -0.888154 |       -2.562251 |       0.000000 | 11.927668 |
| E        | canonical |       13.148622 |        0.000000 |       -0.384093 |       0.000000 | 12.764529 |
| F        | TRAIL1    |       15.378072 |        0.000000 |       -2.562251 |       0.000000 | 12.815822 |

Basket B is the sum of its displayed CNY, GLD, and IMOEX contributions; D remains positive only to the extent the added USD contribution offsets them. This arithmetic, not a redundancy assumption, reconciles the difference.

### Monthly 2023 contribution

| basket   | path      |   month | available_instruments          |     net_R |   USDRUBF |   CNYRUBF |   GLDRUBF |   IMOEXF |
|:---------|:----------|--------:|:-------------------------------|----------:|----------:|----------:|----------:|---------:|
| A        | canonical |       1 | CNYRUBF                        |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| A        | canonical |       2 | CNYRUBF                        | -0.594015 |  0.000000 | -0.594015 |  0.000000 | 0.000000 |
| A        | canonical |       3 | CNYRUBF                        | -0.426541 |  0.000000 | -0.426541 |  0.000000 | 0.000000 |
| A        | canonical |       4 | CNYRUBF                        |  3.724184 |  0.000000 |  3.724184 |  0.000000 | 0.000000 |
| A        | canonical |       5 | CNYRUBF                        |  2.437394 |  0.000000 |  2.437394 |  0.000000 | 0.000000 |
| A        | canonical |       6 | CNYRUBF                        |  1.633938 |  0.000000 |  1.633938 |  0.000000 | 0.000000 |
| A        | canonical |       7 | CNYRUBF+GLDRUBF                | -2.569743 |  0.000000 | -2.569743 |  0.000000 | 0.000000 |
| A        | canonical |       8 | CNYRUBF+GLDRUBF                |  1.284662 |  0.000000 |  1.284662 |  0.000000 | 0.000000 |
| A        | canonical |       9 | CNYRUBF+GLDRUBF                | -1.200308 |  0.000000 | -0.764541 | -0.435767 | 0.000000 |
| A        | canonical |      10 | CNYRUBF+GLDRUBF                | -1.000713 |  0.000000 | -1.000713 |  0.000000 | 0.000000 |
| A        | canonical |      11 | CNYRUBF+GLDRUBF+IMOEXF         | -0.971689 |  0.000000 | -1.025749 |  0.054060 | 0.000000 |
| A        | canonical |      12 | CNYRUBF+GLDRUBF+IMOEXF         | -1.767188 |  0.000000 | -1.764802 | -0.002386 | 0.000000 |
| B        | TRAIL1    |       1 | CNYRUBF                        |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       2 | CNYRUBF                        | -0.042215 |  0.000000 | -0.042215 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       3 | CNYRUBF                        | -0.048216 |  0.000000 | -0.048216 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       4 | CNYRUBF                        |  3.329894 |  0.000000 |  3.329894 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       5 | CNYRUBF                        |  2.437394 |  0.000000 |  2.437394 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       6 | CNYRUBF                        |  0.663620 |  0.000000 |  0.663620 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       7 | CNYRUBF+GLDRUBF                | -3.035069 |  0.000000 | -3.035069 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       8 | CNYRUBF+GLDRUBF                |  1.200489 |  0.000000 |  1.200489 |  0.000000 | 0.000000 |
| B        | TRAIL1    |       9 | CNYRUBF+GLDRUBF                | -2.013649 |  0.000000 | -1.013617 | -1.000032 | 0.000000 |
| B        | TRAIL1    |      10 | CNYRUBF+GLDRUBF                | -1.306469 |  0.000000 | -1.306469 |  0.000000 | 0.000000 |
| B        | TRAIL1    |      11 | CNYRUBF+GLDRUBF+IMOEXF         | -0.971689 |  0.000000 | -1.025749 |  0.054060 | 0.000000 |
| B        | TRAIL1    |      12 | CNYRUBF+GLDRUBF+IMOEXF         | -3.664494 |  0.000000 | -2.048216 | -1.616278 | 0.000000 |
| C        | canonical |       1 | USDRUBF+CNYRUBF                |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| C        | canonical |       2 | USDRUBF+CNYRUBF                | -2.488824 | -1.894809 | -0.594015 |  0.000000 | 0.000000 |
| C        | canonical |       3 | USDRUBF+CNYRUBF                | -1.430154 | -1.003613 | -0.426541 |  0.000000 | 0.000000 |
| C        | canonical |       4 | USDRUBF+CNYRUBF                |  8.039008 |  4.314824 |  3.724184 |  0.000000 | 0.000000 |
| C        | canonical |       5 | USDRUBF+CNYRUBF                |  4.636650 |  2.199256 |  2.437394 |  0.000000 | 0.000000 |
| C        | canonical |       6 | USDRUBF+CNYRUBF                |  3.809423 |  2.175485 |  1.633938 |  0.000000 | 0.000000 |
| C        | canonical |       7 | USDRUBF+CNYRUBF+GLDRUBF        | -2.021883 |  0.547860 | -2.569743 |  0.000000 | 0.000000 |
| C        | canonical |       8 | USDRUBF+CNYRUBF+GLDRUBF        |  6.635231 |  5.350569 |  1.284662 |  0.000000 | 0.000000 |
| C        | canonical |       9 | USDRUBF+CNYRUBF+GLDRUBF        | -1.931409 | -0.731101 | -0.764541 | -0.435767 | 0.000000 |
| C        | canonical |      10 | USDRUBF+CNYRUBF+GLDRUBF        | -2.632438 | -1.631725 | -1.000713 |  0.000000 | 0.000000 |
| C        | canonical |      11 | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF |  0.471806 |  1.443495 | -1.025749 |  0.054060 | 0.000000 |
| C        | canonical |      12 | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF |  0.611194 |  2.378381 | -1.764802 | -0.002386 | 0.000000 |
| D        | TRAIL1    |       1 | USDRUBF+CNYRUBF                |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       2 | USDRUBF+CNYRUBF                | -0.315204 | -0.272990 | -0.042215 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       3 | USDRUBF+CNYRUBF                | -1.051829 | -1.003613 | -0.048216 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       4 | USDRUBF+CNYRUBF                |  7.113136 |  3.783243 |  3.329894 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       5 | USDRUBF+CNYRUBF                |  4.636650 |  2.199256 |  2.437394 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       6 | USDRUBF+CNYRUBF                |  4.396888 |  3.733269 |  0.663620 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       7 | USDRUBF+CNYRUBF+GLDRUBF        | -2.636329 |  0.398740 | -3.035069 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       8 | USDRUBF+CNYRUBF+GLDRUBF        |  6.969128 |  5.768639 |  1.200489 |  0.000000 | 0.000000 |
| D        | TRAIL1    |       9 | USDRUBF+CNYRUBF+GLDRUBF        | -3.015629 | -1.001980 | -1.013617 | -1.000032 | 0.000000 |
| D        | TRAIL1    |      10 | USDRUBF+CNYRUBF+GLDRUBF        | -3.354836 | -2.048367 | -1.306469 |  0.000000 | 0.000000 |
| D        | TRAIL1    |      11 | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF |  0.471806 |  1.443495 | -1.025749 |  0.054060 | 0.000000 |
| D        | TRAIL1    |      12 | USDRUBF+CNYRUBF+GLDRUBF+IMOEXF | -1.286113 |  2.378381 | -2.048216 | -1.616278 | 0.000000 |
| E        | canonical |       1 | USDRUBF                        |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       2 | USDRUBF                        | -1.894809 | -1.894809 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       3 | USDRUBF                        | -1.003613 | -1.003613 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       4 | USDRUBF                        |  4.314824 |  4.314824 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       5 | USDRUBF                        |  2.199256 |  2.199256 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       6 | USDRUBF                        |  2.175485 |  2.175485 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       7 | USDRUBF+GLDRUBF                |  0.547860 |  0.547860 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       8 | USDRUBF+GLDRUBF                |  5.350569 |  5.350569 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |       9 | USDRUBF+GLDRUBF                | -1.166867 | -0.731101 |  0.000000 | -0.435767 | 0.000000 |
| E        | canonical |      10 | USDRUBF+GLDRUBF                | -1.631725 | -1.631725 |  0.000000 |  0.000000 | 0.000000 |
| E        | canonical |      11 | USDRUBF+GLDRUBF+IMOEXF         |  1.497555 |  1.443495 |  0.000000 |  0.054060 | 0.000000 |
| E        | canonical |      12 | USDRUBF+GLDRUBF+IMOEXF         |  2.375995 |  2.378381 |  0.000000 | -0.002386 | 0.000000 |
| F        | TRAIL1    |       1 | USDRUBF                        |  0.000000 |  0.000000 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       2 | USDRUBF                        | -0.272990 | -0.272990 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       3 | USDRUBF                        | -1.003613 | -1.003613 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       4 | USDRUBF                        |  3.783243 |  3.783243 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       5 | USDRUBF                        |  2.199256 |  2.199256 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       6 | USDRUBF                        |  3.733269 |  3.733269 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       7 | USDRUBF+GLDRUBF                |  0.398740 |  0.398740 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       8 | USDRUBF+GLDRUBF                |  5.768639 |  5.768639 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |       9 | USDRUBF+GLDRUBF                | -2.002012 | -1.001980 |  0.000000 | -1.000032 | 0.000000 |
| F        | TRAIL1    |      10 | USDRUBF+GLDRUBF                | -2.048367 | -2.048367 |  0.000000 |  0.000000 | 0.000000 |
| F        | TRAIL1    |      11 | USDRUBF+GLDRUBF+IMOEXF         |  1.497555 |  1.443495 |  0.000000 |  0.054060 | 0.000000 |
| F        | TRAIL1    |      12 | USDRUBF+GLDRUBF+IMOEXF         |  0.762103 |  2.378381 |  0.000000 | -1.616278 | 0.000000 |

## v1/v3 lineage correction

The historical v1 USD/CNY files are continuous/perpetual economic lineages split under Q-style filenames; they are not v2-style quarterly contracts. Actual bar comparison classifications are: USDRUBF=SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL, CNYRUBF=SOURCE_STREAM_SEMANTICALLY_COMPARABLE_BUT_NOT_IDENTICAL. Trade-level reconciliation is published separately. Differences therefore arise from measured source coverage/OHLC and frozen strategy construction differences, not from falsely labelling v1 quarterly.

## Limits

No historical screen guarantees a future positive year. Capital reserve, RUB drawdown tolerance, margin, broker costs, slippage, withdrawals, and emergency reserves remain later production-specification work and are not invented here.

`NEW_PRODUCTION_IDENTITY_REQUIRED_BEFORE_STAGE7`
