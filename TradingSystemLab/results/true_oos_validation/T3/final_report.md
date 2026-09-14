# T3_candidate_v1 — TRUE OOS

**Classification: PASS**

Frozen one-shot evaluation; no optimization, ranking, filters, or development state. C1 costs (one tick per side) are included.

## Predeclared classification criteria

PASS requires >=50 trades, positive expectancy, bootstrap probability >=95%, >=60% positive observed quarters, non-negative observed instrument/direction slices, and positive net R after top-5 removal. FAIL means non-positive expectancy or bootstrap probability <=50%; otherwise BORDERLINE.

## Evidence

- trades=97 (PASS minimum 50)
- bootstrap P(mean R > 0)=0.9999
- positive quarters=5/7
- net R after top-5 removal=28.07948091106132
