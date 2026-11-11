# T3/M15 BE1 AFTER +1R V1

Результат: **механизм неудачен; остановка без следующего порога**.
[Полный отчёт](REPORT_RU.md) · [Протокол до результатов](PROTOCOL_RU.md) ·
[Независимая сверка](INDEPENDENT_VERIFICATION.json) · [Повторы](REPEATABILITY.json).

Ровно CONTROL и BE1, development 2023–2024. Нет комбинации с PR563,
изменения входов/ATR/SESSION/R15 или оптимизации. Только новый audit-only
каталог; никакого production доступа, merge или auto-merge.

Python 3.11+ (использован 3.12.14), pandas 2.2.3, numpy 2.3.5. Из корня
полного clone с data repository рядом:

```bash
python -m pip install -r audit_only/t3_m15_be1_after_1r_v1/requirements.txt
git fetch origin refs/pull/560/head refs/pull/562/head refs/pull/563/head
python audit_only/t3_m15_be1_after_1r_v1/test_contract.py
python audit_only/t3_m15_be1_after_1r_v1/run.py --output work/my-fresh-be1-run
```

`run.py` требует новый output directory. Полные source pins в support.py,
PR_CONTEXT.json и control/SOURCE_MANIFEST.json. DATA по умолчанию
`../market-pattern-data`; код не меняет исходные файлы и не копирует OHLC в git.
Data commit `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`, все четыре SHA
проверяются до расчётов. Зафиксированные полные SHA PR560/562/563 должны
быть доступны; fetch refs по номеру лишь получает объекты, не меняет pins.

Для трёх свежих полных процессов используйте `repeat.py`: он требует
отсутствия `work/t3_be1/final1`, `final2`, `final3`, сравнивает каждый
созданный файл direct bytes и SHA256 и копирует результаты первого
процесса в этот каталог. Изолированный полный CONTROL за 2023–2026
повторяется в каждом процессе; BE1/его признаки ограничены 2023–2024.
Это ретроспективная сверка, не новый независимый OOS.

Комиссии/проскальзывание доступны как отдельная нормированная
чувствительность `--round-trip-cost-R` и `--round-trip-slippage-R`.
По умолчанию 0/0, Gross отдельно. Это не executable Net или тариф FINAM.
Денежная исполнимость **NOT_VALIDATED**.

Lineage: engine.py — PR518 NEXT_OPEN с единственным BE1 floor и audit marks
(ENGINE_LINEAGE.patch). control.py, support.py, io_utils.py, repeat.py и
calendar/statistics utilities адаптированы из pinned PR563; ни одно правило
подтверждения PR563 не перенесено. Verifier — отдельная event-agenda машина
для BE1, исходные streaming indicators из PR518 scalar. Алгоритмическая
независимость тем же автором; внешняя человеческая/отдельная агентская
проверка NOT_PERFORMED. PR496 код не импортируется и не запускается.

Протокол до результатов: commit `407960fa`. CODE_FREEZE.json фиксирует
финальные код, документацию, schema и исходные references перед тремя
полными процессами. Первый инженерный запуск без freeze выполнен до
финального оформления выводов; параметры механизма после него не менялись.
SHA256SUMS покрывает все deliverables, кроме самого SHA256SUMS.
