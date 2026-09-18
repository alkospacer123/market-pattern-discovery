# M5 overextension + session candidate validation

Status: `PHASE_M5_OVEREXTENSION_SESSION_CANDIDATE_COMPLETE`

This candidate-validation phase reports evidence only; it creates no trading rule and selects no production candidate.

## Answers

1. **10:00–17:00 session:** Improved combined expectancy versus baseline (0.07046907434064777 to 0.15267973824458642); PF changed from 1.133527094399683 to 1.2997451804824602.
2. **EMA50 overextension:** Extended expectancy is 0.029885212996431737 versus normal 0.23795304358587577; measurable degradation: **yes**.
3. **Interaction separation:** session+extended occurs in 453/837 (54.1%) early failures and 161/354 (45.5%) long winners. Detailed session, instrument, and distance counts are in `outcome_comparison.csv`.
4. **Future validation:** **Yes, but only as a bounded follow-up hypothesis.** The session improvement is present in both T2 and T3, while EMA50 degradation is not uniform across them and the interaction separation is modest. This is not evidence for a production rule.

All thresholds were inherited unchanged from the entry-quality diagnostic (near <= 0.5 ATR; normal > 0.5 and <= 1.5 ATR; extended > 1.5 ATR). TRUE OOS remained blocked.

