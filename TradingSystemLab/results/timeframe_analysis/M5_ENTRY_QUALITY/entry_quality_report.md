# M5 entry quality diagnostic

Status: `PHASE_M5_ENTRY_QUALITY_DIAGNOSTIC_COMPLETE`

This is descriptive evidence only. No entry, exit, parameter, strategy, or candidate was changed.
All entry fields use candles available by the entry close; ATR percentile ranks use only history observable by that entry.

## T2

### Early failures

- Trades: 370.
- Most common EMA state: above_all (192/370, 51.9%).
- Most common ATR state: high_volatility (154/370, 41.6%).
- Most common candle quality: strong_body (217/370, 58.6%).
- Most common EMA50 location: extended (234/370, 63.2%).

### Long winners

- Trades: 154.
- Most common EMA state: above_all (90/154, 58.4%).
- Most common ATR state: high_volatility (76/154, 49.4%).
- Most common candle quality: strong_body (100/154, 64.9%).
- Most common EMA50 location: extended (93/154, 60.4%).

### Winners versus losers

- Winners' common entry context: above_all (153/251, 61.0%); high_volatility (104/251, 41.4%); strong_body (154/251, 61.4%).
- Losers' common entry context: above_all (315/579, 54.4%); high_volatility (243/579, 42.0%); strong_body (347/579, 59.9%).

## T3

### Early failures

- Trades: 467.
- Most common EMA state: above_all (257/467, 55.0%).
- Most common ATR state: high_volatility (203/467, 43.5%).
- Most common candle quality: strong_body (359/467, 76.9%).
- Most common EMA50 location: extended (422/467, 90.4%).

### Long winners

- Trades: 200.
- Most common EMA state: above_all (118/200, 59.0%).
- Most common ATR state: high_volatility (115/200, 57.5%).
- Most common candle quality: strong_body (153/200, 76.5%).
- Most common EMA50 location: extended (176/200, 88.0%).

### Winners versus losers

- Winners' common entry context: above_all (242/424, 57.1%); high_volatility (200/424, 47.2%); strong_body (317/424, 74.8%).
- Losers' common entry context: above_all (392/707, 55.4%); high_volatility (314/707, 44.4%); strong_body (532/707, 75.2%).

## COMBINED

### Early failures

- Trades: 837.
- Most common EMA state: above_all (449/837, 53.6%).
- Most common ATR state: high_volatility (357/837, 42.7%).
- Most common candle quality: strong_body (576/837, 68.8%).
- Most common EMA50 location: extended (656/837, 78.4%).

### Long winners

- Trades: 354.
- Most common EMA state: above_all (208/354, 58.8%).
- Most common ATR state: high_volatility (191/354, 54.0%).
- Most common candle quality: strong_body (253/354, 71.5%).
- Most common EMA50 location: extended (269/354, 76.0%).

### Winners versus losers

- Winners' common entry context: above_all (395/675, 58.5%); high_volatility (304/675, 45.0%); strong_body (471/675, 69.8%).
- Losers' common entry context: above_all (707/1286, 55.0%); high_volatility (557/1286, 43.3%); strong_body (879/1286, 68.4%).

## Answers to the diagnostic questions

1. **Early-loss entry conditions:** early failures were most often above all EMAs, high-volatility, strong-body, and EMA50-extended. These conditions were also common among long winners, so frequency alone does not identify a failure-specific condition.
2. **Winner structure:** the combined winner/loser shares are close for the leading EMA, ATR, and candle categories. Long winners show more high-volatility entries than early failures, but this is descriptive association rather than evidence of a usable distinction.
3. **Possible causes:** the tables provide evidence for timing through session and instrument/session rows, momentum through body quality and EMA slopes, volatility through causal ATR terciles, and overextension through ATR-normalized EMA distance. The overlap between adverse and favorable groups does not isolate any one of these as the cause of M5 losses.
4. **Future validation:** differences in volatility, instrument/session, wick structure, slopes, and EMA distance are legitimate pre-registered topics for a later validation phase. This diagnostic selects none of them and creates no filter.

The tables quantify bad-timing proxies (session/instrument), weak-momentum proxies (body and EMA slopes), volatility, and overextension. Differences are associations, not validated filters or trading rules.
Market regime is `DATA_UNAVAILABLE` because no existing regime field is present in the frozen ledgers; no new regime model was reconstructed.
Promising areas for future validation are any materially separated categories in the outcome tables, subject to a separately pre-registered causal validation. None is selected here.
