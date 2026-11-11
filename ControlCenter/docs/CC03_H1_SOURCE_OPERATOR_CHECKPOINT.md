# CC-03 / #550: Intel one-shot checkpoint — пока NO_SAFE_SOURCE

Это инструкция для review, не команда на запуск/установку.
[Feasibility report](CC03_H1_SOURCE_FEASIBILITY.md) фиксирует отсутствующий input.
Никакой источник здесь не активируется. Для текущей поставки Intel действий нет.

Уже принятый Task-only UI остаётся доступен существующему standard ccpanel:
выбрать `WINDOWS_OS_ONLY` → один раз «Обновить данные» → сохранить authority,
Task state и original observation/receipt timestamps. Каждый click — максимум
один bounded probe под прежним local + named-pipe gate; navigation/open ничего
не опрашивает. Нет retries/polling/auto-refresh. Task RUNNING не HEALTHY.
Process требует собственного полного approved binding; остальные поля UNKNOWN.
Все десять trading controls disabled, M15 NOT_DEPLOYED.

Для будущих реальных полей порядок после B/package/source acceptance такой:

1. Утверждены exact CC release/manifest, отдельный source producer и перечень его
   полей/authority. Физически проверены owner/standard reader SID, pinned root,
   admin-owned policy и отсутствие writer access к policy у panel/producer.
   Identity/token/ACL не чинятся этой инструкцией.
2. Есть уже закрытый independently produced immutable результат с original
   timestamps, account/robot/release binding, completeness и TTL. Credentials
   остаются у внешнего producer. Live JSON/SQLite не копируются «для удобства».
   Если нужен новый запуск producer, он требует отдельного разрешения; CC UI
   его не инициирует. Сегодня такого принятого результата/adapter нет: STOP.
3. После отдельно reviewed offline ingestion/schema доработки CC и source
   activation: разрешённый внешний one-shot publisher публикует только completed
   уникальный файл в CC root. Никакого постоянного сервиса, перезаписи опубликованного
   leaf или нового доступа ccpanel к H1/FINAM.
4. Оператор выбирает `READONLY_EXPORT` и нажимает кнопку один раз. Проверяет
   source/account binding, исходные clocks, receipt, completeness/TTL и поля
   именно принятой authority; свежий receipt не делает старые данные текущими.
   Current partial receiver пока **не поддерживает** positions/stops/finance:
   generic JSON, stdout #537 и fixture туда не подаются как реальные данные.
5. Missing/corrupt/unbound/stale/timeout/busy → UNKNOWN/STALE/фиксированный код,
   без fallback на legacy reader, автоматического повтора или повышения прав.
   При нарушении границы не выполнять reader на Intel.

Минимальный input для продолжения инженерной работы: sanitized исходник уже
разрешённого внешнего producer + закрытый пример результата + доверенная source
provenance/account mapping/оригинальные timestamps/completeness. Если producer
отсутствует, сначала отдельное решение о допустимом источнике. Простое разрешение
читать heartbeat не исправляет Windows sharing conflict.
