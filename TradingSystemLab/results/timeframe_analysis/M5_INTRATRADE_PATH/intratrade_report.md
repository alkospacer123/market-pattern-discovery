# M5 intratrade path diagnostic

Status: `PHASE_M5_INTRATRADE_PATH_COMPLETE`

Diagnostic only. No strategy, parameter, entry, exit, stop, trailing rule, or candidate selection was changed.

## Entry quality

### T2
- Winners positive after 15m: 69.32%.
- Winners positive after 30m: 81.67%.
- Losers immediately negative at 15m: 63.90%.
- Losers non-negative at 15m but negative at 30m (slow degradation): 13.82%.
- Winners negative at 15m but recovered by 30m: 11.16%.

### T3
- Winners positive after 15m: 72.64%.
- Winners positive after 30m: 81.13%.
- Losers immediately negative at 15m: 66.05%.
- Losers non-negative at 15m but negative at 30m (slow degradation): 15.84%.
- Winners negative at 15m but recovered by 30m: 9.67%.

### COMBINED
- Winners positive after 15m: 71.41%.
- Winners positive after 30m: 81.33%.
- Losers immediately negative at 15m: 65.09%.
- Losers non-negative at 15m but negative at 30m (slow degradation): 14.93%.
- Winners negative at 15m but recovered by 30m: 10.22%.

All checkpoint OHLC is restricted to candles whose M5 close timestamp is after entry and no later than the checkpoint or actual exit. Session-candidate rows are the frozen 10:00–17:00 entry-time subset, not a newly selected candidate.
