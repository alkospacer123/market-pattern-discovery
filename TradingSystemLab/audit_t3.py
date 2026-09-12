"""Deterministic descriptive audit of the frozen T3 baseline artifacts."""
from __future__ import annotations
import json, math
from pathlib import Path
from typing import Iterable
import numpy as np
import pandas as pd

BASELINE = Path(__file__).resolve().parent / "results" / "T3_baseline"
REQUIRED_OUTPUTS = ("summary.md", "statistics.json", "equity_curve.svg", "r_distribution.svg",
                    "monthly_returns.csv", "yearly_report.csv", "mae_mfe_analysis.csv")

def _pf(x):
    loss = abs(float(x[x < 0].sum()))
    return float(x[x > 0].sum()) / loss if loss else math.inf

def _dd(values: Iterable[float]):
    curve = np.r_[0., np.cumsum(np.asarray(list(values), float))]
    return float((curve - np.maximum.accumulate(curve)).min())

def _stats(frame):
    pnl, r = frame.net_profit, frame.profit_R
    return {"trades": int(len(frame)), "net_profit": float(pnl.sum()), "profit_factor": _pf(pnl),
            "expectancy": float(pnl.mean()), "average_R": float(r.mean()),
            "win_rate": float((pnl > 0).mean()), "max_drawdown": _dd(pnl)}

def _streaks(values):
    win = loss = max_win = max_loss = 0
    for x in values:
        win, loss = (win + 1, 0) if x > 0 else ((0, loss + 1) if x < 0 else (0, 0))
        max_win, max_loss = max(max_win, win), max(max_loss, loss)
    return max_win, max_loss

def _line_chart(path, values):
    h,w,m=700,1200,55
    underwater = values < np.maximum.accumulate(values)
    xs=np.linspace(m,w-m-1,len(values)).astype(int)
    span=float(values.max()-values.min()) or 1
    ys=(h-m-(values-values.min())/span*(h-2*m)).astype(int)
    bands="".join(f'<line x1="{x}" y1="{m}" x2="{x}" y2="{h-m}" stroke="#ffe1e1"/>' for x in np.unique(xs[underwater]))
    points=" ".join(f"{x},{y}" for x,y in zip(xs,ys))
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="100%" height="100%" fill="white"/><text x="{w/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="20">Combined cumulative equity (red = drawdown)</text>{bands}
<path d="M {m} {h-m} H {w-m} M {m} {m} V {h-m}" fill="none" stroke="#282828" stroke-width="2"/><polyline points="{points}" fill="none" stroke="#144b91" stroke-width="2"/>
</svg>\n''')

def _hist(path, values):
    h,w,m=700,1200,55; counts,edges=np.histogram(values,bins="auto"); bars=[]
    bw=(w-2*m)/len(counts)
    for i,count in enumerate(counts):
        x0=int(m+i*bw)+1; x1=int(m+(i+1)*bw)-1; y=int(h-m-count/counts.max()*(h-2*m))
        color="#3773b4" if edges[i]>=0 else "#c34641"; bars.append(f'<rect x="{x0}" y="{y}" width="{max(x1-x0,1)}" height="{h-m-y}" fill="{color}"/>')
    zx=int(m+(0-edges[0])/(edges[-1]-edges[0])*(w-2*m))
    path.write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<rect width="100%" height="100%" fill="white"/><text x="{w/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="20">Trade result distribution (R)</text>{''.join(bars)}
<path d="M {m} {h-m} H {w-m}" fill="none" stroke="#282828" stroke-width="2"/><line x1="{zx}" y1="{m}" x2="{zx}" y2="{h-m}" stroke="#141414" stroke-width="2"/>
</svg>\n''')

def _combined(equity):
    wide=equity.pivot(index="time",columns="symbol",values="equity").sort_index()
    return wide.ffill().fillna(wide.bfill().iloc[0]).sum(axis=1)

def _duration(curve):
    dd=curve-curve.cummax(); start=None; episodes=[]
    for at,x in dd.items():
        if x<0 and start is None: start=at
        elif x>=0 and start is not None: episodes.append((start,at)); start=None
    if start is not None: episodes.append((start,dd.index[-1]))
    rows=[{"start":a.isoformat(),"end":b.isoformat(),"calendar_days":(b-a).total_seconds()/86400} for a,b in episodes]
    return {"episode_count":len(rows),"longest":max(rows,key=lambda x:x["calendar_days"],default=None)}

def generate_audit(baseline: Path = BASELINE) -> Path:
    audit=baseline/"audit"; audit.mkdir(parents=True,exist_ok=True)
    source=json.loads((baseline/"metrics.json").read_text()); trades=pd.read_csv(baseline/"trades.csv"); equity=pd.read_csv(baseline/"equity_curve.csv")
    for col in ("entry_time","exit_time"): trades[col]=pd.to_datetime(trades[col],utc=True)
    equity.time=pd.to_datetime(equity.time,utc=True)
    if (trades.entry_time.dt.year>=2025).any() or (equity.time.dt.year>=2025).any(): raise ValueError("locked TRUE OOS data (2025 or later) must not be audited")
    trades=trades.sort_values(["exit_time","entry_time","symbol"],kind="stable").reset_index(drop=True)
    overall=_stats(trades); mw,ml=_streaks(trades.net_profit)
    overall.update(long_trades=int((trades.direction=="LONG").sum()),short_trades=int((trades.direction=="SHORT").sum()),median_R=float(trades.profit_R.median()),maximum_winning_streak=mw,maximum_losing_streak=ml,recovery_factor=overall["net_profit"]/abs(overall["max_drawdown"]))
    mapping={"trades":"trades","long_trades":"long_trades","short_trades":"short_trades","net_profit":"net_profit","profit_factor":"profit_factor","expectancy":"expectancy","average_R":"average_R","win_rate":"win_rate","max_drawdown":"max_drawdown"}
    checks={k:math.isclose(float(source[k]),float(overall[v]),rel_tol=1e-10,abs_tol=1e-8) for k,v in mapping.items()}
    if not all(checks.values()): raise ValueError(f"metrics.json does not reconcile with trades.csv: {checks}")
    r=trades.profit_R; ordered=r.sort_values(ascending=False); gross=float(r[r>0].sum())
    concentration={f"top_{n}_share_of_positive_R":float(ordered.head(n).sum()/gross) for n in (1,3,5)}
    concentration.update(total_R=float(r.sum()),total_R_without_best_trade=float(r.sum()-r.max()),total_R_without_top_5_trades=float(r.sum()-ordered.head(5).sum()))
    dist={"mean_R":float(r.mean()),"median_R":float(r.median()),"standard_deviation_R":float(r.std()),"percentile_25_R":float(r.quantile(.25)),"percentile_75_R":float(r.quantile(.75)),"best_trade_R":float(r.max()),"worst_trade_R":float(r.min()),"large_trade_dependence":concentration}
    instruments={k:_stats(v) for k,v in trades.groupby("symbol",sort=True)}; directions={k:_stats(v) for k,v in trades.groupby("direction",sort=True)}
    years=[]
    for year,g in trades.groupby(trades.exit_time.dt.year,sort=True):
        s=_stats(g); years.append({"year":year,"trades":s["trades"],"net_profit":s["net_profit"],"PF":s["profit_factor"],"winrate":s["win_rate"],"average_R":s["average_R"],"max_DD":s["max_drawdown"]})
    yearly=pd.DataFrame(years); yearly.to_csv(audit/"yearly_report.csv",index=False)
    month_key = trades.exit_time.dt.strftime("%Y-%m")
    months=[{"month":month,"return_R":float(g.profit_R.sum()),"trades":len(g),"drawdown":_dd(g.profit_R)} for month,g in trades.groupby(month_key,sort=True)]
    monthly=pd.DataFrame(months); monthly.to_csv(audit/"monthly_returns.csv",index=False)
    curve=_combined(equity); durations=_duration(curve); _line_chart(audit/"equity_curve.svg",curve.to_numpy()); _hist(audit/"r_distribution.svg",r.to_numpy())
    mm=trades[["symbol","direction","entry_time","exit_time"]].copy(); mm.insert(0,"trade_id",np.arange(1,len(mm)+1)); mm["MAE"]=np.nan; mm["MFE"]=np.nan; mm["status"]="NOT_CALCULABLE_FROM_SUPPLIED_TRADE_AND_EQUITY_ARTIFACTS"; mm.to_csv(audit/"mae_mfe_analysis.csv",index=False,na_rep="")
    share=float(yearly.net_profit.max()/overall["net_profit"]); best=monthly.loc[monthly.return_R.idxmax()].to_dict(); worst=monthly.loc[monthly.return_R.idxmin()].to_dict()
    result={"audit_scope":{"strategy":"T3_MTF_Trend_v1.0","first_entry":trades.entry_time.min().isoformat(),"last_exit":trades.exit_time.max().isoformat(),"true_oos_2025_read":False,"parameters_optimized":False,"source_metrics_reconciliation":checks},"overall":overall,"r_distribution":dist,"by_instrument":instruments,"by_direction":directions,"year_analysis":{"profitable_years":int((yearly.net_profit>0).sum()),"years":len(yearly),"largest_year_share_of_total_net_profit":share,"all_profit_from_one_year_red_flag":bool(share>=1)},"monthly_analysis":{"best_month":best,"worst_month":worst,"profitable_months":int((monthly.return_R>0).sum()),"months_with_trades":len(monthly),"equity_drawdown_durations":durations},"mae_mfe":{"status":"not_calculable","reason":"No intratrade OHLC path is present in supplied artifacts."},"limitations":["Commission and slippage are zero in the frozen baseline.","Only 109 trades and two calendar years are available.","MAE/MFE require causal intratrade bar paths, which were not supplied."],"decision":"NEEDS_RESEARCH"}
    (audit/"statistics.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    il="\n".join(f"| {k} | {v['trades']} | {v['profit_factor']:.3f} | {v['expectancy']:.2f} | {v['max_drawdown']:.2f} | {v['win_rate']:.2%} |" for k,v in instruments.items())
    dl="\n".join(f"| {k} | {v['trades']} | {v['profit_factor']:.3f} | {v['average_R']:.3f} | {v['win_rate']:.2%} |" for k,v in directions.items())
    summary=f'''# T3 Baseline Audit

## 1. Стратегия

`T3_MTF_Trend_v1.0` — неизменённый MTF trend-following baseline: H4-фильтр EMA100/slope, ADX(14) > 20 и ATR(14) > среднего ATR(20); вход H1 по пробою 20 баров; начальный стоп 2 ATR и trailing stop 3 ATR, риск 1%. Аудит использует только готовые сделки 2023–2024, не читает locked TRUE OOS 2025 и не подбирает параметры. Комиссия и slippage в baseline равны нулю.

## 2. Результаты

| Metric | Value |
|---|---:|
| Total trades | {overall['trades']} |
| LONG / SHORT | {overall['long_trades']} / {overall['short_trades']} |
| Net profit | {overall['net_profit']:.2f} |
| Profit factor | {overall['profit_factor']:.3f} |
| Expectancy | {overall['expectancy']:.2f} |
| Average / median R | {overall['average_R']:.3f} / {overall['median_R']:.3f} |
| Win rate | {overall['win_rate']:.2%} |
| Maximum drawdown | {overall['max_drawdown']:.2f} |
| Maximum losing / winning streak | {overall['maximum_losing_streak']} / {overall['maximum_winning_streak']} |
| Recovery factor | {overall['recovery_factor']:.3f} |

### Распределение R и концентрация

Mean {dist['mean_R']:.3f}R, median {dist['median_R']:.3f}R, sample SD {dist['standard_deviation_R']:.3f}R, P25 {dist['percentile_25_R']:.3f}R, P75 {dist['percentile_75_R']:.3f}R, best {dist['best_trade_R']:.3f}R, worst {dist['worst_trade_R']:.3f}R. Лучшая сделка даёт {concentration['top_1_share_of_positive_R']:.1%} суммы положительных R, top-5 — {concentration['top_5_share_of_positive_R']:.1%}. Без top-5 итог {concentration['total_R_without_top_5_trades']:.3f}R против полного {concentration['total_R']:.3f}R: эффект зависит от больших трендовых сделок, но не от одной сделки.

### Инструменты

| Instrument | Trades | PF | Expectancy | DD | Winrate |
|---|---:|---:|---:|---:|---:|
{il}

Положительные PF и expectancy у обоих инструментов — ограниченный признак переносимости, но два близких валютных фьючерса не доказывают переносимость на иной рынок.

### LONG / SHORT

| Direction | Trades | PF | Average R | Winrate |
|---|---:|---:|---:|---:|
{dl}

### Временная устойчивость

Положительных лет: {int((yearly.net_profit>0).sum())} из {len(yearly)}. Доля самого прибыльного года: {share:.1%}; красный флаг «вся прибыль в одном году»: **{'ДА' if share>=1 else 'НЕТ'}**. Лучший месяц — {best['month']} ({best['return_R']:.3f}R), худший — {worst['month']} ({worst['return_R']:.3f}R). Самая долгая underwater-просадка equity: {durations['longest']['calendar_days']:.1f} дней ({durations['longest']['start']} — {durations['longest']['end']}). Месячный `drawdown` рассчитан в R по exit-событиям с reset в начале месяца; годовой `max_DD` — аналогично в деньгах с reset в начале года.

## 3. Сильные стороны

* Положительные expectancy и PF на обоих инструментах и в обоих годах.
* Результат остаётся положительным без одной лучшей сделки.
* Выпуклое trend-following распределение: ограниченный worst trade и крупные winners.

## 4. Слабые стороны

* Только {overall['trades']} сделок, два года и два коррелированных инструмента.
* Асимметрия направлений и зависимость от хвоста: top-5 дают {concentration['top_5_share_of_positive_R']:.1%} gross positive R.
* Нулевые комиссия и slippage: экономическая реализуемость не проверена.
* MAE/MFE оставлены пустыми: входные artifacts не содержат intratrade high/low path; вычислять excursion по entry/exit означало бы выдумать данные.

## 5. Решение

**NEEDS_RESEARCH: нужны изменения в исследовании, не в правилах baseline.**

Положительный эффект присутствует, но данных недостаточно для PASS. Нужны заранее зафиксированная проверка с реалистичными costs/slippage, больше development-периодов и инструментов, causal intratrade bars для MAE/MFE. TRUE OOS 2025 остаётся закрытым до фиксации процедуры; аудит его не использовал.
'''
    (audit/"summary.md").write_text(summary); return audit

def main(): print(generate_audit())
if __name__ == "__main__": main()
