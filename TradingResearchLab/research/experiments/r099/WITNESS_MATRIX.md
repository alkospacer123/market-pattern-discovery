# R099 — witness matrix

| Контроль | Требование | Фактический witness | Статус |
|---|---|---|---|
| Source identity | Pinned data commit и M5 bytes | Commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`; M5 SHA256 `3758ed99…6037786`; blob SHA1 `2b621e1c…f825e` | `SOURCE_VERIFIED` |
| Frozen protocol | Hash до результата, без последующего редактирования | `ea2e0660…f8684ffee0`; frozen 2026-11-26T11:37:04Z | PASS |
| Raw quality | Нет NA, duplicates, non-monotonic timestamps, invalid OHLCV | Все четыре счётчика = 0 на 159752 строках | PASS |
| Exclusions | Не более 2%, каждый отказ записан | 3/925 = 0,324%; `excluded_days.csv` | PASS |
| Eligible N | N≥850 | 922, включая 12 zero-signal | PASS |
| Zero-signal gate | ≤1% eligible | 12/922 = 1,302% | **FAIL** |
| Causal prefix | Сигнал truncated-through-10:25 совпадает с полным | 922 проверки, mismatch 0 | PASS |
| Future perturbation | OHLC после 10:25 ×1,01 не меняет direction | 922 проверки, mismatch 0 | PASS |
| Ledger uniqueness | Одна строка на nonzero-сигнал/день | 910 строк, 910 уникальных дат | PASS |
| Net identity | Net пересчитывается из direction/fills/lot | 910 проверок, mismatch 0 | PASS |
| M5→M30 first30 | Open/High/Low/Close/Volume совпадают | 922 проверки, mismatch 0 | PASS |
| Frozen M15 close | M15 18:30 Close против M5 18:45 Close | 807 mismatch | **OBSERVED_LIMITATION**; comparator не эквивалентен по интервалу |
| Frozen M30 close | M30 18:30 Close против M5 18:45 Close | 106 mismatch | **OBSERVED_LIMITATION** |
| Diagnostic M15 18:45 | Одноимённые M15/M5 18:45 Close | 105 mismatch | **OBSERVED_LIMITATION**, post-freeze diagnostic только для качества |
| Predictive gate | beta>0, HAC p<0,05 | beta=0,0354943; p=0,0162874 | PASS |
| Bootstrap economic gate | Mean C2>0 и CI low>0 | Mean −27,592 ₽; CI [−36,432; −18,319] ₽ | **FAIL** |
| PF gate | C2≥1,10; C4>1 | 0,5277; 0,2229 | **FAIL** |
| Yearly gate | ≥3/4 положительных, включая 2025/2026 | 0/4; каждый год отрицателен | **FAIL** |
| Concentration gate | Net без top-10>0; yearly share≤60% | −29620 ₽; positive yearly share UNDEFINED | **FAIL** |
| Clean replay | Отдельный процесс/output; обязательные analytical bytes совпадают | 6/6 файлов byte-identical; hashes в `replay_verification.json` | PASS |
| Independent calculation | Другая vectorized extraction и статистическая реализация | 922/910; ledger money diff≤1,35×10⁻¹¹ ₽; statsmodels HAC beta/p совпали в float tolerance | PASS; bootstrap/прочие diagnostics не переписаны |
| OOS | Независимый untouched период | Отсутствует; весь 2023–2026 retrospective development | `NOT_AVAILABLE`, не PASS |
| Фактические издержки/ГО/ликвидность | Наблюдаемые fees/spread/depth/fills/ГО | Отсутствуют; C1/C2/C4 — модельный drag | `MISSING_DATA` |
| V20/LIVE boundary | Нет production изменений | Изменены только research documents/code/artifacts | PASS |

**Итог:** вычислительный расчёт воспроизводим; торговый baseline отклонён. `REPRODUCIBLE_VERIFIED` не отменяет ни одного экономического FAIL и не создаёт CANDIDATE.
