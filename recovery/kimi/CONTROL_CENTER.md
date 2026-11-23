# Kimi knowledge project — Control Center V20

**SOURCE SHA REFRESH 23.11.2026:** README и CC-08 Git blobs ниже обновлены по `main@1413273a1a312802a0ced7a06a4eb73f050d2ec3`. Срез до #589 ниже — исторический base, не текущий HEAD; доступ Kimi и LIVE не испытаны.


> **SOURCE AUTHORITY CHECK 22.11.2026:** последние принятые GitHub-документы после [Merge #589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) зафиксированы на контрольном `main=41d0b48c1d33db29bc1b19497d558748b3db8fb4`. Указанный ниже `bb8c46c1...` — **воспроизводимый исходный base до #589**, а не всегда актуальный HEAD. Перед чтением и практическим экзаменом перепроверять `main`, Git blobs и [иерархию документов](../DOCUMENTATION_AUTHORITY_2026-11-22.md). Никаких Kimi Chat/Code access, установленного LIVE, FINAM или cold restore не подтверждено. **CC warning:** `ControlCenter/README.md` содержит датированное `#568 Draft`; #568 фактически MERGED, а канон — CC-08 и паспорт.

**PINNED SOURCE:** GitHub main `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`. Source prepared; Kimi Code and LIVE access NOT VERIFIED.

Читать: [AGENTS](../../AGENTS.md) → [паспорт CC](../PROJECT_PASSPORT_CONTROL_CENTER.md) blob `9e649ee4820e1849580b85574f58d6084e798018` → [ControlCenter README](../../ControlCenter/README.md) blob `3c01b427b8b9a2bdaff9679dbafa32427428ed37` → [CC-08 Operations](../../ControlCenter/docs/V20_CC08_OPERATIONS.md) blob `18be465651d3747abe99f669967e374cde616252`.

CC — панель и операторский контур, не стратегия. Историческое локальное UI: `127.0.0.1:8502`; READONLY refresh ≠ START, PAUSE, STOP, RESTART, RECOVER. HTTP 200 и HEALTHY не доказывают FINAM FLAT, ARMED или брокерский SLTP. При неизвестном результате команды запрещён слепой повтор; сначала независимая проверка.

Исторические operator/adapter Git blobs `10de325be0335733a248c412943f39d45bd93c62` / `ef2fa2cd6b0ddfefc920548995274f123c5884bf` описывают свидетельство 20.11, не нынешний установленный код. Сохранённый CC03 frozen scope-аудит имеет историческое исключение; успешный selected CI не доказывает LIVE.

Kimi Code: прочитать `ControlCenter/tests/test_cc07_command_channel.py`, `test_cc07_admin_control.py`, `test_v20_controller.py`; объяснить неизвестный результат и fail-closed в синтетическом сценарии, выполнить только разрешённые офлайн-тесты в изолированной копии. Без настоящих кнопок, FINAM, DPAPI, Windows Tasks, SQLite или localhost управления.
