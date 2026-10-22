# V20-04.1 — закреплённая карта источников H1 / M15 (22.10.2026)

**Scope:** `V20_TradingSystem_M15/` only. Это карта интерфейсов и версий, **не разрешение использовать H1 LIVE на V20**, не документ о пройденной offline-приёмке V20-04/05. Три стратегии Shallow / OBV / Inside используют **один** H1-based исполнитель с раздельными состояниями и счетами.

## Проверенные GitHub refs

| Источник | Git commit | Состояние |
| --- | --- | --- |
| фактический `main` H1 и merged IntradayLab/core | `6f352acfac7ebdfabba73e143c4dfea3a6e48507` | Проверен через GitHub ref и Contents 22.10.2026 |
| PR #493 STOP/TICK GRID | merge commit `dbff701cfc111f7860ca7126ac9b32c497051e10`, PR head `bd97a76f5614c9a77f4a47784beb16fc03e8c800` | **MERGED**; использовать **текущие main blobs** ниже, не копировать legacy stop |
| V20-04 Draft PR #567 | `a3dd56a225c1c8e9885ff49ea8934cf69a80f2ff` на момент исходного аудита | OPEN / DRAFT; не READY |
| проверенный M15 frozen foundation checkpoint | `996be71757c77cedb176b78357a01f0099cac850` | Ранее проверенные 110/110 на отдельной Intel-проверке; используем только прицельно прочитанные компоненты, не whole-tree импорт |
| M15 Draft PR #540 (для разграничения) | `71207fe07c2728ebf81bdfb0c34fac8e2ae0ab25` | **OPEN / DRAFT / NOT merged**. Его текущий head **не** приравнивать к `main` или к проверенному checkpoint |

GitHub SHA в таблицах ниже — **Git blob SHA конкретного файла**, а не commit SHA. Они взяты из GitHub Contents на указанных refs. Для исполнения фиксировать *оба* идентификатора: pinned commit + blob. Изменение любого SHA требует сравнения API/контракта до обновления V20.

## H1 — минимальная матрица повторного использования

Все пути ниже имеют префикс `TradingSystemLab/stage8_robot/` и считаны из закреплённого `main` выше.

| Файл | Git blob SHA | Назначение в V20 и граница |
| --- | --- | --- |
| `finam_api.py` | `a1126a7d2c618c19b5895f5c54da8e1ad73b339a` | REST auth/GET, POST orders и POST SLTP, неопределённый результат POST -> reconciliation; H1 `completed_h1_bars` **не** переименовывать вслепую в M15 |
| `instrument_resolver.py` | `a174aee3fb4f5c68f2f00ff39a84527d9cd4642c` | Строгая привязка N4 к биржевой спецификации/тику/лоту, freshness и fingerprint |
| `market_data.py` | `56c0035a066962c9fd631786c3cd6785988caa1a` | Контракт валидации свежих закрытых свечей, но H1-specific normalize не подходит напрямую для M15 |
| `broker.py` | `3573b4f88216086105fb577987f82310daf531dc` | `compact_client_order_id`, BUY/SELL mapping, брокерский интерфейс; ключ обязан включать **отдельную** V20 robot/account identity |
| `live_execution.py` | `0c2fcd742a3157575cdecc5e1dac40d0c906b203` | `AuthorizedFinamProductionTransport`: pre-POST gate/entry, order/SLTP wire contract; сохранить запрет неавторизованной отправки |
| `production_service.py` | `46b258c6b01d79fea4c3be9338185c121e575755` | H1 broker snapshot, order lifecycle, fill reconciliation, стопы и transport orchestration; H1 DecisionCore/timing **заменять интерфейсным адаптером V20**, не копировать в стратегию |
| `production_broker_state.py` | `894321fc0d3101e75eea48f45ff3a26c0c0f58eb` | Строгое чтение позиции, регулярной заявки, 100% SLTP, дедупликация client ID |
| `protective_stop_contract.py` | `51a7ab88d2f64f969088d8ef04927383b7abc1aa` | Stop-only `SLTP_QTY_MEASURE_PERCENT=100` по фактической экспозиции; не вводить TP/trailing |
| `state.py` | `4f12e1cb61eccb0b14c1efb9ff0cdf2532a7b22b` | SQLite intent, transitions, account identity; **не открывать H1 SQLite** из V20 |
| `production_runtime.py` | `4ec35199be9269af5fc10093a086e0feb4207a34` | Атомарный state/recovery, идемпотентные ключи, fill/stop intents; бизнес-решения T3/H1 не переносить |
| `reconciliation.py` | `6585cfa96efd532ff651c23c5ce4b5b3880b88ad` | Local↔broker позиции и заявки, unknown/uncertain -> fail closed |
| `production_safety_gate.py` | `f8c399bba0a373fe5154e96f43118871f90c0228` | Внешний kill switch, healthy heartbeat/reconciliation, запрет входов при mismatch |
| `operations.py` | `0d7ba1f2f9f4e6fa2f772921846bc334469dd3d5` | Одиночный процесс/lock, SQLite backup/check, логи, heartbeat; 3 разные runtime roots |
| `execution_grid.py` | `d8e55d6083153f4854139ffcc9b921b35bdfca8a` | **PR #493:** `initial_projection` / `project_stop` / `require_on_grid` для исполнимого 2×ATR14 stop; outward и Decimal |
| `risk.py` | `afaae0b8fc305dec690967f38ef7d33c7b8da909` | `ContractEconomics` / `size_position`, 1.5% realized equity |
| `margin.py` | `80117ff6ea169305a7c22ee52a12e3e9103c9deb` | `cap_r15_by_margin`, directional GO, lot floor; каждый счёт — собственная authority |
| `deploy/windows/run-production.ps1` | `b5e38eabae6e70582d6f0f2414799702cfec4ecd` | Только шаблон отдельного процесса/запуска в `C:\\V20Lab`; **H1 task не менять** |
| `deploy/windows/install-production-task.ps1` | `e2efbf0e7b4826b779a05944310c44c539e94189` | Только исходная схема Scheduled Task; V20 tasks создаются исключительно в V20-07, Disabled |

**Смысл fix #493:** LONG stop = floor(raw_stop/tick)*tick; SHORT = ceil(raw_stop/tick)*tick; **заново** пересчитывать количество от executable stop, затем ограничивать GO. Старую raw-stop quantity не переиспользовать. Реальный fill, SLTP и комиссии требуют собственного FINAM доказательства. Frozen H1 ATR=2.5 и TRAIL1 **не переносить**: V20 initial=2×ATR14 Wilder, без trailing.

## M15 — только проверенная причинность и бары, без T3/T1 параметров

| Путь | Commit ref / blob SHA | Использование |
| --- | --- | --- |
| `IntradayLab/core/m15_bars.py` | `main` / `7d2eefb949de05cbd53936a713bd37644bb01a35` | M15 агрегация, полные сессионные slots |
| `IntradayLab/core/calendar.py` | `main` / `55798e1d266a953d94879dabb8f9b6f938b85619` | Exchange/session windows, не подменять V20 календарь T1 (10:00–18:00) |
| `IntradayLab/core/execution.py` | `main` / `5268a3673b980dc0063d177fa2da81ee8e36bcf7` | NEXT_OPEN reference execution и stop-before-exit checks |
| `IntradayLab/m15_robot/bar_bridge.py` | `996be71757c77cedb176b78357a01f0099cac850` / `71e08a490df5f8467efe564b197bb472725dd6a0` | `completed_close_labeled_m15`: witnessed completed bar и проверенный session-end; FINAM open-label authority физически пока не доказана для V20 |
| `IntradayLab/m15_robot/feature_adapter.py` | `996be71757c77cedb176b78357a01f0099cac850` / `120453bbbdcc502f9cfa9fa379076a6d9b4e51fd` | `validate_completed_history` и `consecutive_next_open_allowed` как интерфейсный **образец**; T3 indicators/features НЕ брать |
| `IntradayLab/m15_robot/continuation.py` | `996be71757c77cedb176b78357a01f0099cac850` / `2f2b16242919b534c10d1934af629ea263c14278` | `immutable_prefix_splice`: проверка seam/gaps, не менять исходную историю |

**Важно:** `996be...` — проверенная точка M15, но **не часть main**. Head #540 уже другой. Цифра 110 PASS относится только к зафиксированной ранее проверке M15, **не** к новым V20-тестам. Котировки FINAM M15 и фактическое время закрытия надо отдельно подтвердить в V20-06; 30-дневный REST window не заменяет теплую историю.

## V20 frozen sources (без правки)

- `V20_TradingSystem_M15/V20-03/offline/stress_v20_03.py` — исходная существующая frozen AST обвязка для Shallow/OBV/Inside; используется в `v20_runtime/frozen_adapter.py` (offline).
- `V20_TradingSystem_M15/research_original_v20/base.py`, `run.py`, `legacy_v4/study_v4.py` — research authority, **никаких изменений формул**.
- `V20_TradingSystem_M15/v20_runtime/offline_planner.py` — текущий reference-only вызов H1 grid/risk/GO, не умеет работать с реальной ценой fill, SQLite или FINAM.

## Реальный порядок дальнейшей сборки (без новых этапов)

1. **V20-04.2:** existing frozen signals -> завершённая M15 -> NEXT_OPEN; отдельная карточка пригодности по последним 20 завершённым сессиям (READONLY, только метрики, NEVER FILTER).
2. **V20-04.3:** reuse H1 broker/transport, persistent intent, uncertain POST lockout, partial-fill protective SLTP, broker reconciliation/restart с отдельной V20 account identity.
3. **V20-04.4:** actual fill risk, 1.5% per position/6% aggregate, current directional GO, fail-closed.
4. **V20-04.5/04.6:** separate config/process/task names/log/state for all three, offline only; tests and acceptance, не объявлять непроведённые проверки PASS.

**Границы:** Никаких импортов runtime-root, токенов, БД или live-операторских состояний H1. H1 и IntradayLab не меняются. Никакие Task, API или реальные заявки этим документом не активируются. Карта фиксирует просмотренные GitHub refs/blob SHA (source-map PASS); **runtime/CI/Intel acceptance новых V20 компонентов: NOT RUN**.
