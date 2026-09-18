# M15 Bounded Optimization

Independent bounded T2 and T3 development searches; no cross-strategy or cross-timeframe ranking or winner selection.

## T2

- Baseline metrics: trades=384, PF=1.52360105929, expectancy_R=0.246956503781, net_R=94.831297452, max_drawdown_R=-18.0698473818
- Tested configurations: 19
- Robust plateau count: 2
- Selected configuration: `T2-M15-0014-26fb9b19bd4f`
- Selection status: **ROBUST_PLATEAU**
- Optimized candidate metrics: trades=328, PF=1.5459158617210869, expectancy_R=0.2561411948263278, net_R=84.01431190303552, max_drawdown_R=-19.213384354471067, recovery_factor=4.372697196550117
- Parameter changes vs baseline: `{"ema_fast": {"baseline": 20, "selected": 25}}`
- Top-five dependency: net_R_without_top5=32.36805537403673, PF_without_top5=1.210324103614002

## T3

- Baseline metrics: trades=425, PF=1.54244483808, expectancy_R=0.237046699065, net_R=100.744847102, max_drawdown_R=-33.0753212176
- Tested configurations: 22
- Robust plateau count: 9
- Selected configuration: `T3-M15-0011-76dd2f3526c3`
- Selection status: **ROBUST_PLATEAU**
- Optimized candidate metrics: trades=401, PF=1.6401650508028935, expectancy_R=0.302966847340464, net_R=121.48970578352606, max_drawdown_R=-31.30136775277552, recovery_factor=3.88129064336984
- Parameter changes vs baseline: `{"trail_atr": {"baseline": 3.0, "selected": 3.5}}`
- Top-five dependency: net_R_without_top5=76.77712890872911, PF_without_top5=1.404561310864757

Full development period: 2023-01-01 through 2024-12-31.

2025+ TRUE OOS, walk-forward, and portfolio construction were not accessed. H1 C1 costs remain one tick per side with zero additional slippage.

PHASE_M15_OPTIMIZATION_COMPLETE
