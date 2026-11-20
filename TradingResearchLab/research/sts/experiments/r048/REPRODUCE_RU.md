# TRL-R048 — воспроизведение из изолированного ZIP

Это research-only пакет без API, FINAM, Windows Tasks, токенов, доступа к LIVE или production SQLite.

## Содержимое

- `FROZEN_PROTOCOL.md` — фиксирован 11.11.2026 **до** расчёта P&L; SHA256 `da6327e30ea8e8f6c69f02294177ac95938b1a7c743814eebb33d77cd96c021c`.
- `run_r048.py` — 4 заранее определённых качественных фильтра на raw Early Trend Resume R047; полный каузальный денежный replay через НЕИЗМЕНЁННЫЙ замороженный движок.
- `audit_r048.py` — независимый расчёт денежных результатов 11 444 исполненных сделок и проверка лимитов.
- `diagnostics_r048.py` — парные месячные разницы и описательная 3-месячная блочная оценка (НЕ OOS).
- `deps/r047/` — копия R047 `run_r047.py`, `FROZEN_PROTOCOL.md`, SHA-verified N4 M15 OHLCV, `trl_fixed_engine_sts.py`, `research_extended.py`, R031 catalog, R045 financial ledger.
- `results/` — CSV, исходные JSON и контрольные показатели.
- `TRL_R_2026_048_Early_Trend_Quality_Research.md`, Excel и Journal.

## Команды в распакованной папке с установленными Python, numpy, pandas

`python run_r048.py`

`python audit_r048.py`

`python diagnostics_r048.py`

Тесты не имеют зависимости от исходного абсолютного пути: локальный `deps/r047` имеет приоритет. Скрипты переписывают только `results/` внутри своей распакованной копии. Для сохранённых исходных CSV сверяйте SHA256 по `MANIFEST_SHA256.txt`.

## Проверки

- Classic BASE `773` и TP6_PROTECT3 `808`, net R `505.4766203967774` и `499.2860389864027`.
- R047 raw Early TP6 `822` и `+13893.4 ₽` Oct GO.
- V20 45/45/45 TP6 Oct `+381607.6 ₽`.
- 500 prefix-causality signal checks.
- 11444 executed cash trades verified.

**Исторический период 2023–Sep2026 не является TRUE OOS; фиксированные GO proxies, C1 не равны реальным FINAM расходам и нет полноценного MTM/вариационной маржи.**