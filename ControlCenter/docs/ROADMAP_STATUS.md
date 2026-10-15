# Статус roadmap Control Center v1.0

Основание: [Issue #524, roadmap 15.10.2026](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6198924792).
Не изменяет roadmap других проектов. Выполнены только CC-00 и CC-01.

| Этап | Статус этой поставки | Остаток |
| --- | --- | --- |
| CC-00 | Анализ кода, source inventory, архитектура и граница достоверности готовы | Intel-файлы и M15 production runtime spec не проверены; план #527 прочитан; это явно указано |
| CC-01 | Автономный Streamlit DEMO, 2 монитора, графики, журнал, типы и тесты готовы | Внешний аудит Draft PR и решение оператора; Windows smoke на физическом хосте не выполнен |
| CC-02 | НЕ НАЧАТ | Следующий отдельный Draft PR: read-only H1 snapshot adapter |
| CC-03 | НЕ НАЧАТ | Отдельная физическая Intel read-only приёмка, identity/ACL и before/after evidence |
| CC-04 | НЕ НАЧАТ | M15 адаптер после появления approved runtime/spec/account contract |
| CC-05 | НЕ НАЧАТ | Реальные decision trace и отдельная финансовая authority; текущие таблицы только DEMO |
| CC-06 / CC-07 | НЕ НАЧАТЫ | Control-plane design/mock, независимый аудит и отдельные разрешения на каждое действие |
| CC-08 | НЕ НАЧАТ | Реальные alerts, readiness, backup/retention и эксплуатационная приёмка |

## Реализовано в CC-01

- Русский тёмный адаптивный интерфейс; семь разделов, отдельные H1 и M15.
- 10 детерминированных локальных сценариев; отсутствие/ошибки/устаревание отображаются явно.
- H1 frozen identity и справочный риск без изменения торговых исходников.
- M15 NOT_DEPLOYED, production identity/heartbeat/финансы UNKNOWN, отдельные DEMO-символы; выбранный план #527 показан справочно.
- Типизированные immutable snapshot contracts, provenance, cross-account guards.
- Все шесть уровней фактов заявки; ACK не считается fill.
- Автообновление 2s, таблицы, candles, DEMO-вход/выход/линия/стоп и event filters.
- Статистика и риск отдельных счетов; M15 без выдуманного капитала.
- Отключённые кнопки, отсутствие DB/broker/process capability в runtime.
- Русская документация, тесты, browser screenshots и отчёт проверки границ.

## Следующая задача CC-02 (только после проверки оператором)

Согласовать allowlist экспортов H1, версию/authority контракта и independent field TTL;
создать read-only reader готовых атомарных снимков с валидацией identity/account,
размера, времён, stale/missing/malformed/partial/wrong-account, source outage и WAL busy
при допустимом SQLite-пути. Не добавлять UI FINAM polling, команды или прямые engine
imports. Не изменять HALTED и production checkout. Реальная M15-интеграция — CC-04.

**После одного Draft PR — STOP. NO MERGE / NO AUTO-MERGE / NO INTEL DEPLOYMENT.**
