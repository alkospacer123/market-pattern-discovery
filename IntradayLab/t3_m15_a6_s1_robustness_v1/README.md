# TRAIL_375 Robustness v1

**MIXED:** полный кандидат остаётся положительным во всех фиксированных портфельных диагностиках, но зависит от USDRUBF2023, ноября2024 и хвоста SHORT2024. Не автоматический Robustness PASS.

**2023–2024 DEVELOPMENT_EXPOSED. GROSS_ONLY / COSTS_DEFERRED / NOT_LIVE_READY.**

[Русское решение и четыре обязательных ответа](CONCLUSIONS.md) · [Полный отчёт](results/REPORT.md) · [Все24 месяца по инструментам и сторонам](results/MONTHLY_DETAIL.md) · [Машинное решение](DECISION.json)

| Показатель | CONTROL | −0,05R/CLOSED | −0,10R/CLOSED |
| --- | ---: | ---: | ---: |
| PF2023 | 2,207278 | 2,033245 | 1,876833 |
| PF2024 | 1,772134 | 1,636882 | 1,514730 |
| Полный PF | 1,911934 | 1,764694 | 1,631937 |
| Полный Gross R | +212,522656 | +188,522656 | +164,522656 |
| Положительные месяцы | 20/24 | 18/24 | 16/24 |
| CLOSED-R DD | 12,628056 | 14,936730 | 19,686730 |

R-stress — абстрактное снижение исхода каждой CLOSED, не FINAM комиссии, C1 или реальное проскальзывание. CLOSED480/terminal OPEN1 сохранены; OPEN не включён в PF/R и не ликвидирован. DD и сумма R не являются MTM/доходностью капитала.

USD2023 даёт73,608559% годового R; без него PF1,524816,6/12 положительных месяцев. Ноябрь2024 даёт44,005603% R2024; без него PF1,452043,+68,387068R. Без10 крупнейших победителей ALL: PF1,565589,+131,808371R,17/24. SHORT2024 без его пяти крупнейших: PF0,988208,−0,954381R. Все исключения диагностические; кандидат, состав и обе стороны сохраняются.

Есть основания для **отдельного решения пользователя о Walk Forward неизменного кандидата после ревью**. Новый архитектурный фильтр текущими данными не обоснован. Exposed2024 не становится чистым WF/OOS. Следующий этап не запускался.

## Проверяемые материалы

- [Предрегистрация](PROTOCOL.md), [SPEC](SPEC.json), [freeze receipt](FREEZE.json): код/методология заморожены и опубликованы до первого исторического расчёта в `eb4397a8256cd1164ac687c030cfbbf6e59540b3`.
- [CONTROL primary](results/control/CONTROL_GATE.json), [CONTROL scalar](results/control_scalar/CONTROL_GATE.json), [полные журналы #506–#508](results/control/PR506_508_GATE.json), [features](results/FEATURE_CONTROL.json), [causal invariants](results/CAUSAL_INVARIANTS.json).
- [Независимая сверка](audit/AUDIT_RESULT.json), [presentation audit](audit/PRESENTATION_AUDIT.json), [сверка заключения](CONCLUSION_REVIEW.json), [38 synthetic tests](PRECALC_TESTS.txt).
- [Два полных побайтных повтора](REPEATABILITY.json), [все сравнения файлов](REPEAT_FILES.csv), [первые SHA](FIRST_PIPELINE_SHA256.json).
- [Исходные таблицы](results/TABLES.json), [все сценарии](results/scenario_summary.csv), [месяцы сценариев](results/scenario_monthly.csv), [каждая CLOSED в сценариях](results/scenario_ledger.csv), [отрицательные серии](results/loss_runs.csv), [winner IDs](results/top_winners.csv), [ноябрь](results/november2024.csv).
- [PR #505–#508](PR_CONTEXT.json), [source/provenance](SOURCE_ORIGIN.json), [source manifest](results/SOURCE_MANIFEST.json), [scope](SCOPE_CHECK.json), [final main](FINAL_MAIN_CHECK.json), [полный SHA inventory](ARTIFACT_SHA256.json).

Исходный data pin `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8` read-only. Timestamp-first останавливает reader до numeric suffix2025+; full hashes используют только opaque bytes. Все четыре прежних artifact inventories проверены. Frozen engine/scalar/metrics — побайтные копии#506. Межинструментальных ограничений в модели нет; leave-one-out допустим лишь для независимой суммы R, без реального sizing/capital inference. GLD partial start июль2023, IMOEX ноябрь2023;12/24 denominator сохранён, NO_COVERAGE отдельно.

Независимость вычислительная: отдельные streaming indicators/dict replay/accounting, без primary engine/analysis/metrics imports. Автор один; внешнее человеческое ревью PENDING. Первые code/result bytes неизменны после freeze. Численные admission thresholds не вводились; trailing optimization не возобновлялась.

## Воспроизведение

В новом checkout с исходным freeze commit в Git history, Python3.12 и зависимостями `requirements.txt`:

```sh
export PYTHONDONTWRITEBYTECODE=1
python IntradayLab/t3_m15_a6_s1_robustness_v1/run.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_a6_s1_robustness_v1/audit.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_a6_s1_robustness_v1/repeat.py --data-root /workspace/market-pattern-data
python IntradayLab/t3_m15_a6_s1_robustness_v1/seal.py
```

Repeat требует свежих, ещё не существующих `work/repeat_1` и `work/repeat_2` внутри этого каталога. Freeze guard сверяет filesystem и Git SHA. `run.py` не достигает diagnostics до PASS всех CONTROL. `audit.py` заново читает только разрешённый source prefix и исполняет неизменный scalar CONTROL. Не запускать новый торговый replay по sensitivity.

Все новые файлы исключительно в этом каталоге. ROADMAP, TradingSystemLab/робот, прежние IntradayLab, original checkout и рыночные данные неизменны. Один **Draft PR / NO MERGE / NO AUTO-MERGE**. **STOP для ревью.** Walk Forward, TRUE OOS, OHLC2025+ и LIVE не выполнялись.
