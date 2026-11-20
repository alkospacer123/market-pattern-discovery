# Recovery / Kimi — состояние после исторического закрытия PR

**Последующие подтверждённые события 20.11:** Recovery #571 объединён в `main=ccc0ed57fcf9eec5a2d0673575580b4f58a35627`; ZIP точного коммита `main` с SHA256 `36D387EB106F13E2EC6CA7DF6F3D2BA59204DDEAC3216A46CCFABFEB8F48C329` скопирован на SSD с `ssd_copy_verified=pass`; создан публичный пока пустой `market-pattern-archive`, но все шесть каталогов остаются в рабочем репозитории. [Актуальная карта для Kimi](KIMI_REPOSITORY_BOUNDARIES_2026-11-20.md). Дальнейший текст — исходный срез до этих событий, не считать его главным текущим статусом.

**Срез:** 20.11.2026. **Статус:** `DOCS_ONLY / RECONCILED_WITH_GITHUB / NOT_LIVE_PASS / NOT_COLD_RESTORED`. Датированные свидетельства, а не постоянная LIVE-телеметрия. Старый `CURRENT_STATE_2026-11-09.md` остаётся неизменным.

## Правила источников

- **MAIN:** принятый код GitHub; `alkospacer123/market-pattern-discovery`, `main=e6b8480b493365e0a4ff2bb56041891fde0a6f22`. Девять merged PR: V20 #567/#574/#575; CC #568; TRL #570/#572/#573/#576/#577.
- **INSTALLED:** совпадение конкретных байтов на Intel, подтверждённое физическими проверками.
- **LIVE:** свежие локальные циклы и независимое брокерское состояние; не определяется GitHub, CI или панелью.
- **RESEARCH:** воспроизводимые исследования и решения TRL; не подтверждают LIVE.
- **ARCHIVE:** закрытые исторические PR и старые H1/M15/T3; не являются текущими исходниками.
- **RECON:** восстановленный контекст с явно перечисленными пробелами.

## V20 / R088

Точка входа: `V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md` (Git blob `d61b0ac5b30ff706534f4b5c65e523705aa04d3b`). Shallow/OBV/Inside; N4, M15, NEXT_OPEN; 60/30/45 + TP6 + Protect3 + HOLD5, **EXT2 OFF**, риск 1,5%/6%. Установленный `finam_live.py` получается из базового модуля и девяти патчей; прямое равенство одному Git-файлу не предполагается.

Последняя представленная локальная READONLY-проверка **20.11.2026 15:27:35 МСК**: Shallow, OBV и Inside — `Task=Running`, `Switch=HALTED`, `cycle_code=HALTED_NO_NEW_ENTRIES`, возраст цикла 13/10/11 секунд; `V20_08_5_HEALTH_PARTIAL`; `NO_ORDER_NO_CANCEL_NO_FINAM_API_NO_SQLITE_OPEN_NO_TASK_MUTATION_NO_REARM=YES`. **ARMED, позиции, заявки, SLTP и реальный Protect3 этой командой не проверены**. Не менять LIVE для подтверждения документации.

## Control Center / installed

На Intel **20.11.2026** локальный health endpoint `127.0.0.1:8502/_stcore/health` вернул HTTP 200. Три файла побайтно совпали с GitHub `main` по `git hash-object --no-filters`:

| Компонент | Git blob SHA-1 | Intel SHA256 |
|---|---|---|
| CC-07 operator | `10de325be0335733a248c412943f39d45bd93c62` | `586cc55f0fb10cf6e0c8f2e8d51ac15e74bb5b421312520f3afe3a934d87944b` |
| V20 Python adapter | `ef2fa2cd6b0ddfefc920548995274f123c5884bf` | `d669c898e455f7afb98c0a0deaf3c82fa3a09bd21127e715cd9bbc94bd46cb9a` |
| V20 Streamlit UI | `9b9b0f0cf3cba4fbe3203286f793a5a0f8ec5e6c` | `2a40449afcff59a6001a11607a2adfbe942d86889f6183c825cc3b2edda5f02a` |

Это **MATCH 3/3 для конкретных файлов**, но не полная операторская/брокерская приёмка. Актуальные инструкции: `ControlCenter/README.md` (верхний V20-раздел) и `ControlCenter/docs/V20_CC08_OPERATIONS.md`. Исторический CC-03/H1 в старом README не считать текущей панелью.

## Trading Research Lab / ноябрь

Финальный выбор: **60/30/45, TP6+Protect3+HOLD5, EXT2 OFF**. `TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md` и `TRL-NOV-2026-FINAL-CLOSEOUT.md` — точки входа. R097/R098: 75/30/30 остаётся историческим лидером Net/PF в конкретном исследовании, не выбранной LIVE-моделью; отрицательные результаты не удалять. Оригиналы R060/R097 ZIP и XLSX требуют собственной проверки байтов и SHA256.

## Исторические PR и репозитории

По отдельному разрешению оператора **десять исторических PR #540/#544/#557/#559/#560/#561/#562/#563/#564/#566 закрыты без Merge**. Проверено `state=closed`, `merged_at=null`; архивные пояснения и HEAD SHA опубликованы в обсуждениях; ветки в GitHub сохранены. Их HEAD-коммиты обнаружены в проверенном Git mirror 09.11 и закреплены локальными `refs/archive/pre-r7-20261120/pr-NNN`. Окончательный экспорт PR/Issues/CI и независимый Recovery **не подтверждены**.

**PR #571** — единственный оставшийся открытый Draft; его исходный HEAD до этой документационной актуализации `0f9c3c8ed375c595c9b63ffa835f5f54c98850be`. Не смешивать с историческими закрытыми PR.

`market-pattern-autonomous-engine` удалён самим владельцем; GitHub отвечает 404. Независимое резервирование его истории **не доказано**. `market-pattern-data` сохранён отдельным репозиторием.

## Защитный снимок — только частично

- Git mirror ZIP 09.11 SHA256 `9e5d490410f7fbe3ddab983d557b981eb96146f2e5c023e42b2a1d0ee9fd0754`; восстановленная копия Discovery: `git fsck=0`, 41 047 объектов, 1 163 refs, `main=0881d1e08b51a564fb54bb7d334d1578fc130400`.
- Новый `market-pattern-data` mirror 20.11: `fsck=0`, 8 refs, `main=f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
- ZIP текущего `main` Discovery скачан владельцем, но его путь и SHA256 не проверены. ZIP ветки не содержит полную историю Git, PR, Issues, CI.
- Текущий Git mirror Discovery после девяти Merge пока не обновлён из-за нестабильного HTTPS. **Полный защитный комплект / rollback не PASS**. R5 Final Backup и R6 isolated restore test остаются завершающими этапами.

## Kimi

Три проекта: V20 Trading System, Control Center, Trading Research Lab. GPT/Codex и Kimi AI/Kimi Code — равные партнёры при разных авторизациях и общем доказательном каталоге. Kimi начинает с текущих принятых первоисточников, а закрытые PR и H1/M15/T3 использует лишь как архив. Никакого самовольного Merge, удаления, FINAM/LIVE или изменения торговых правил.

Порядок: **R0 → R4 → защитный снимок → R7 → R1 → R2 → R3 → R5 → R6 → R8**.