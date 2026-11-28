# Control Center V20 — START HERE / SOURCE MAP

**27.11.2026: FULL_PARITY_OWNER_ADMITTED.** Допуск и границы — Roadmap/Recovery STATUS. Общие COC и разрешения на операции неизменны.

**Действующий маршрут 27.11.2026:** начни с [STATUS](../STATUS.md) и релевантного [JOURNAL](../JOURNAL.md), общего AGENTS/COC; ниже dated SOURCE map, проверяй актуальный ref/blob и #602 SOURCE fix отдельно от INSTALLED. Для задачи открывай только необходимые CC-07/CC-08/data-security документы. Kimi exam — историческое evidence, не повторять.
**HISTORICAL SOURCE audit: 22.11.2026.** Baseline MAIN `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. Это точка проверки GitHub, НЕ доказательство состояния Intel/FINAM. Сначала прочесть [AGENTS](../../AGENTS.md), [паспорт Control Center](../../recovery/PROJECT_PASSPORT_CONTROL_CENTER.md), [правила источников](../../recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md), затем этот документ.

**CURRENT SOURCE pointer, проверен 28.11.2026:** MAIN после Merge #617 `568b339a1bb3ebc3f025d74762ae66c344278be9`. Актуальные Git blob: `v20_app.py` — `b255565b0267b111ecadf4bfb108ab997b577d66`; `cc/v20_contract.py` — `680a3c4b6344738f07b78aa5d6d361dcdca3d9e2`. Остальные восемь blob соответствуют датированной таблице ниже. Это SOURCE-only сведения, не INSTALLED/LIVE; исторические pins 22.11 сохранены без перезаписи.

**PG10.2 coordinated SOURCE candidate, PR #618:** кодовый checkpoint `05078a26d9b65b4e04b71b3e9b614d580cd519f6`; окончательный PR HEAD и CI фиксируются в STATUS отдельно. Candidate pins: UI `2b941f54848dbd6509eae555b5e63cdbc4376ee1`, admin `2b6c8c8b628d7270bc6271c663c42ae9d54b5ee0`, controller `27f16169c819bd06e267394215ba04a1dd7bd73c`, exporter `60cdac39845f85ecb63f45aca217d35975d5841e`, history `a4357a44c950db61ab889fe996e35982a4c62e2d`, manual exporter `6daa04103a89f7001e6b21f7eb9e278185d668ab`; V20 operator `83cc20df33abadf0895bb42bf9508de8ab45c08e`, launcher `3f017a7e697a9a9b1907bee0757cee77d33d466d`. DERIVED и ordered patches — [release manifest](../../V20_TradingSystem_M15/V20-08/pg10-2-release-manifest.json). Candidate НЕ INSTALLED, LIVE UNKNOWN; #602 `cc/v20_contract.py=680a3c4b…` включён в package, физическая установка не выполнялась.

## Архитектурные границы
- **MAIN:** действующий V20 Streamlit entrypoint `ControlCenter/v20_app.py`. Три робота `v20-shallow`, `v20-obv`, `v20-inside` и вкладки «Главная / Журнал / Управление». `ControlCenter/app.py` — исторический CC-03/H1/M15 на 8501, **не** этот UI.
- **INSTALLED (свидетельство 20.11):** `C:\Control Center\v20-preview-d80f2446\v20_app.py`; локально `http://127.0.0.1:8502`. Текущая побайтовая проверка Intel — **NOT_VERIFIED**.
- **LIVE:** Task/switch/cycle из V20, отдельно FINAM positions/orders/SLTP. MAIN и HTTP 200 не доказывают брокерскую защиту.

## Путь данных при ручном refresh
`v20_app.py` (только явная кнопка) → `cc.manual_gate.export_gate` → `cc.v20_manual_export.refresh_once` (проверяет Git blob экспортёра и запускает фиксированный Python с `--publish`) → `deployment/v20_live_export.py` (stock V20 check, локальные `live-m15.jsonl` и switch, очищенный CC-owned JSON; без FINAM API, order, Task mutation) → `cc.v20_receiver.acquire` (отдельно утверждённая NTFS policy/ACL/root-ID, schema/digest/TTL) → UI. При `NOT_CONNECTED` может применяться исторический `cc.v20_staging.acquire_staging`. Отсутствие источника не превращать в HEALTHY.

Синтетический пример policy в Git **не является** действующей Intel policy. Кнопка обновления — READONLY, её timestamp означает попытку, а не новое брокерское наблюдение. Исторические CC-05 FINAM-квитанции не читаются как актуальные broker facts.

## Путь оператора
`v20_app.py` → `v20_admin_control.py` → установленный pinned `controller/cc07-v20-operator.ps1` → только штатный V20 operator/check/readonly, Windows Task gate и CC-owned журнал `data/control-audit/v20-control.jsonl`. PAUSE — одно нажатие, остальные команды требуют второго подтверждения. [Контракт и отказы](V20_CC07_COMMAND_CONTRACT.md).

**Отдельный альтернативный путь:** `v20_command_channel.py` + `controller/cc07_command_worker.py` — staged inbox/gateway с другим PIN и набором действий (в частности, без RECOVER). `v20_app.py` **не импортирует** эти компоненты. Их текущая установка на Intel **NOT_VERIFIED**, не включать второй канал рядом с admin adapter.

## Исторический SOURCE audit 22.11.2026 — код и Git blob SHA

| Назначение | Путь под `ControlCenter/` | Git blob |
|---|---|---|
| V20 UI | `v20_app.py` | `9b9b0f0cf3cba4fbe3203286f793a5a0f8ec5e6c` |
| Admin adapter | `v20_admin_control.py` | `ef2fa2cd6b0ddfefc920548995274f123c5884bf` |
| Pinned CC-07 operator | `controller/cc07-v20-operator.ps1` | `10de325be0335733a248c412943f39d45bd93c62` |
| Manual export adapter | `cc/v20_manual_export.py` | `5cc12214843f070db9220c1c00a16a199738cc95` |
| One-shot exporter | `deployment/v20_live_export.py` | `969d9cef2832b5b8ec243ef275de5e63c4e820a2` |
| Receiver/policy | `cc/v20_receiver.py` | `6661b746a19b58b4f810fbda2dc04e4809bcd518` |
| Contract/TTL | `cc/v20_contract.py` | `365065026de1031cdb888798a4419458523dcb20` |
| Old staging fallback | `cc/v20_staging.py` | `b91aae83326fa9498a35168bdc52f3bd79adac4c` |
| Preview-only policy | `controller/v20_live_policy.py` | `178f2b767bc0311460214dc19766ca2201898cbf` |
| Staged worker | `controller/cc07_command_worker.py` | `8ac883f48f79f8b2b5e7b90abd57e13d5cd9b942` |

**Только датированное INSTALLED свидетельство 20.11:** controller и adapter совпадали с приведёнными SHA; V20 launcher Git blob был `e1de4aad7a98cdc84768c1811131c3ad079d7d90`. Сверка сегодняшнего V20 launcher/модулей **NOT_VERIFIED**; восстановимость полного V20 — отдельная ответственность V20.

Далее: [CC-07](V20_CC07_COMMAND_CONTRACT.md) → [CC-08](V20_CC08_OPERATIONS.md) → [телеметрия, security, CI](V20_DATA_SECURITY_TESTS.md) → [реестр](V20_DOCUMENT_REGISTER_20261122.md) → [Kimi exam](V20_KIMI_EXAM.md).

## Critical Operations Contract

Для READONLY и операторского контуров применяй [единый контракт](../../recovery/CRITICAL_OPERATIONS_CONTRACT.md), раздел `COC-CC-*`. Сверяй UI, adapter response, controller proof, Task/switch/audit и broker truth раздельно. Request correlation, MAIN UI и offline-кандидаты не считать установленными без отдельного INSTALLED evidence.
