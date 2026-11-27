# Control Center V20 — START HERE / SOURCE MAP

**C3 candidate 27.11.2026:** начни с [STATUS](../STATUS.md) и релевантного [JOURNAL](../JOURNAL.md), общего AGENTS/COC; ниже dated SOURCE map, проверяй актуальный ref/blob и #602 SOURCE fix отдельно от INSTALLED. Для задачи открывай только необходимые CC-07/CC-08/data-security документы. Kimi exam — историческое evidence, не повторять.
**CURRENT SOURCE audit: 22.11.2026.** Baseline MAIN `0e569be6cb3c7cce1f7224e7f1fef6be38f6ba52`. Это точка проверки GitHub, НЕ доказательство состояния Intel/FINAM. Сначала прочесть [AGENTS](../../AGENTS.md), [паспорт Control Center](../../recovery/PROJECT_PASSPORT_CONTROL_CENTER.md), [правила источников](../../recovery/DOCUMENTATION_AUTHORITY_2026-11-22.md), затем этот документ.

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

## Код и точные Git blob SHA в MAIN

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
