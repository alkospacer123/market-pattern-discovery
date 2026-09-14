# BBW 03B-2A readiness — CNYRUBF

| Item | Status | Frozen result / blocker |
|---|---|---|
| instrument identity | VERIFIED | MOEX CNY/RUB daily cash-settled futures |
| source timezone | REQUIRES_CONFIRMATION | Finam export selection is not embedded |
| timestamp start/end semantics | REQUIRES_CONFIRMATION | Need saved export selection plus M1 check |
| exchange timezone | VERIFIED | `Europe/Moscow` |
| series type | VERIFIED | `exchange_perpetual_daily_autoprolong` |
| lot | VERIFIED | 1,000 CNY |
| tick-size regimes | EFFECTIVE_DATED_VERIFIED | 0.01 then 0.001 RUB/CNY at 2023-09-27 19:05 MSK |
| tick-value regimes | EFFECTIVE_DATED_VERIFIED | 10 then 1 RUB/contract at same boundary |
| session regimes | EFFECTIVE_DATED_VERIFIED | weekday, morning, unified, expanded regimes encoded |
| trading-date assignment | EFFECTIVE_DATED_VERIFIED | evening next-day before 2026-03-23; current-day after |
| calendar | REQUIRES_CONFIRMATION | versioned annual/special-day artifacts not frozen |
| funding | UNRESOLVED | historical series/application/sign audit absent |
| GO/margin | UNRESOLVED | historical effective-dated series absent |
| exchange fees | UNRESOLVED | effective-dated archived schedules absent |
| broker commission | REQUIRES_USER_INPUT | RUB/contract/side or complete formula |

## Decisions

* `FUNDING_MODEL_READY_FOR_IMPLEMENTATION = NO`
* Historical 75%-margin-cap sizing reproducible: **NO**
* Transaction-cost model baseline-ready: **NO**
* `READY_FOR_03B2B = NO`

03B-2A authorizes no normalization, H4 construction, BBW calculation,
strategy run, trades, baseline, optimizer, or performance measurement.
