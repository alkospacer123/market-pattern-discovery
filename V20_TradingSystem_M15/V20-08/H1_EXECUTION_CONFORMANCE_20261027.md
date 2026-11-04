# V20 M15 — прикладная сверка исполнения с действующим H1

Дата проверки: 27.10.2026. **Только offline/GitHub, без команд Intel, FINAM LIVE POST и изменений H1.**

## Точная база

- H1 GitHub **main**: `6f352acfac7ebdfabba73e143c4dfea3a6e48507`. Использованные исходники: `TradingSystemLab/stage8_robot/production_service.py` blob `46b258c6b01d79fea4c3be9338185c121e575755`; `production_runtime.py` blob `4ec35199be9269af5fc10093a086e0feb4207a34`; `live_execution.py` blob `0c2fcd742a3157575cdecc5e1dac40d0c906b203`; `finam_api.py` blob `a1126a7d2c618c19b5895f5c54da8e1ad73b339a`; `trading_safety_gate.py` blob `e938048a8dc3caa9db29209489a7050e64d0bb5a`.
- V20: Draft PR #567, разрабатывается **только в V20**; настоящие LIVE процессы на Intel по последнему отчёту продолжают работать из ранее установленного кода, все 3 `HALTED` для новых входов с открытыми защищёнными позициями. **Всё ниже — исходники ветки, НЕ установка на Intel и НЕ разрешение на ARM.**

## Сверка по жизненному циклу

| Обязательный путь | Эталон H1 | V20 / действие | Статус |
|---|---|---|---|
| FINAM auth/GET/5xx retry | `finam_api.FinamAPI` | Импортирует точно существующий H1 API | повторно используется |
| FINAM broker account/orders, broker side/status | `production_broker_state`, `account_cleanliness` | Точно импортируются; изоляция по собственному account hash | повторно используется |
| Защита от чужих активных заявок/позиций | `ProductionService._assert_exact_broker_ownership` | V20 `_ownership`, строгая проверка client id, symbol, account; аккаунты независимы | адаптация M15, fail-closed |
| Стоп на исполнимой сетке | `execution_grid` | Точно импортируется `project_stop/require_on_grid` | повторно используется |
| Market ENTRY и EXIT payload | `AuthorizedFinamProductionTransport._market_payload` | Вызов H1 для входа и выхода | повторно используется |
| SLTP 100% | `percent_position_stop_payload`, `_validate_production_sltp` | Вызов H1 payload/proof, тот же FINAM stop, не повторять сомнительный POST | повторно используется |
| Риск по tick/GO/equity | `risk`, `margin`, `production_runtime` | H1 `cap_r15_by_margin`, `floor_to_trade_lot`, R15/R6; 3 отдельные SQLite | повторно используется с M15 лимитами |
| Pre-POST durable intent и idempotency | `production_runtime.record_entry_submission`, `production_service._submit` | V20 `record_submission_boundary`, `submit_entry_once`, `reconcile_order`, сохранение неопределённого POST | адаптация, fail-closed |
| FINAM order-linked exact fills | `finam_fill_price_readonly`, `StateStore.persist_fill(strict=True)` | Те же H1 методы, VWAP из реальных /trades; повторы не создают новые fills | повторно используется |
| Post-fill снятие только разрешённого pre-POST checkpoint | H1 reconciliation/handoff переходят к `RECONCILED` | **Найден реальный FAIL 3/3**: V20 marker `UNKNOWN_POST_REQUIRE_BROKER_RECONCILIATION` не снимался; однократный recovery 27.10 уже выполнен владельцем, постоянный условный reset в `observe_protected_entry` после exact fill + SLTP + risk PASS в Draft PR | исправлено в ветке, НЕ на Intel |
| Partial fill 1→2, существующий тот же active 100% stop | H1 `ProductionRuntime._confirm_candidate_entry` (строки ~1099–1177) | Сверка доказала возможный ложный HALT при изменении VWAP; теперь только после предыдущего действительного stop proof принимается **тот же broker stop ID и цена**, новый полный fill history, и заново пересчитывается допустимый риск; никакого повторного stop POST. Физическое покрытие следующего контракта остаётся НЕ ДОКАЗАНО, как и в H1 | исправлено в ветке, offline-тест; до первой частичной реальной сделки неизвестно |
| Manual broker-flat при активном stop | H1 `ProductionService._flat_cleanup_and_exit` | Найден разрыв: V20 требовал frozen-exit intent. В ветке добавлен LIVE-only H1 flat cleanup только при exact FINAM flat, прежнем RECONCILED fill и проверенном stop ID; STOP отменяется только ПОСЛЕ flat, строго один раз. Одноразовая техническая проба не меняется | исправлено в ветке; при LIVE исполнении ещё не проверено |
| EXIT rejected/terminal при открытой позиции | H1 `ProductionService._reconcile_intents` (строки ~542–580) | Найден разрыв: V20 мог бесконечно ждать. В ветке терминальный EXIT + OPEN => fail-closed, старый стоп сохраняется, повторной рыночной заявки нет | исправлено в ветке |
| FINAM GET-сбои, цикл и операторский HALT | H1 `ProductionService.run()`: fault/retry 3s без смерти процесса | Исправлено раньше, 3 работающих робота физически приняли H1-style loop. В ветке повторный HALT не увеличивает generation каждые 3s | loop PASS Intel; generation fix пока в ветке |
| State/instance lock/SQLite transaction | H1 `StateStore`, `InstanceLock` | Точно импортируются; три изолированные базы с разными account hashes | повторно используется |
| Операционные CHECK/STOP/ARM/Task | H1 WIN Task, Kill Switch | V20 отдельные задачи и команды V20; оператор H1-style cycle PASS/FAIL; живые задачи не тронуты | адаптация, ручной CHECK физически PASS до инцидента |
| M15 frozen signals / NEXT_OPEN / third session | Этого нет в H1 H1 | Взято из *замороженного* V20/M15, НЕ должно копироваться из H1 TRAIL1/H1; оригинальные исследовательские blobs не менялись | обоснованное отличие |

## Жёсткое условие возвращения новых входов

**Режим автономного входа в LIVE всё ещё ЗАПРЕЩЁН**, пока открыты 3 позиции и текущий установленный исполняемый файл V20 остаётся старым. Проводить только broker-safe сопровождение с `HALTED` и существующим SLTP. После подтверждения у FINAM `FLAT` и отсутствия активных stop/order на **всех** трёх независимых счетах — согласованный SQLite backup, установка только закреплённых LIVE V20-файлов, подтверждение SHA и offline регрессии, затем ручная авторизация нового LIVE ARM по ранее принятому порядку.

**Не объявлять «полное совпадение H1»** без фактического FINAM подтверждения: отличаются M15 сигнал, окно NEXT_OPEN, fixed 2ATR/M15 выход (H1 использует TRAIL1/H1), нет реального наблюдения подросшей на частичном fill позиции. FINAM actual fees (а не budgeted roundtrip) также не подтверждены историей LIVE. Это границы фактической приёмки, а не предложение менять методологию или создавать новые этапы.

Справка: `V20-08/REAL_ACCEPTANCE.json` содержит восстановление владельцем трёх позиций 27.10 (снимок SQLite и `HALTED_NO_NEW_ENTRIES` 3/3); текущая проверка не выполняла никакого запроса к FINAM/Intel.
