# Kimi knowledge project — Control Center V20

**PINNED SOURCE:** GitHub main `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`. Source prepared; Kimi Code and LIVE access NOT VERIFIED.

Читать: [AGENTS](../../AGENTS.md) → [паспорт CC](../PROJECT_PASSPORT_CONTROL_CENTER.md) blob `9e649ee4820e1849580b85574f58d6084e798018` → [ControlCenter README](../../ControlCenter/README.md) blob `707080ee4daf1b2cf3a754c078a67e78f6612aae` → [CC-08 Operations](../../ControlCenter/docs/V20_CC08_OPERATIONS.md) blob `51781e013f68fc323a4740701ae84e066ef86926`.

CC — панель и операторский контур, не стратегия. Историческое локальное UI: `127.0.0.1:8502`; READONLY refresh ≠ START, PAUSE, STOP, RESTART, RECOVER. HTTP 200 и HEALTHY не доказывают FINAM FLAT, ARMED или брокерский SLTP. При неизвестном результате команды запрещён слепой повтор; сначала независимая проверка.

Исторические operator/adapter Git blobs `10de325be0335733a248c412943f39d45bd93c62` / `ef2fa2cd6b0ddfefc920548995274f123c5884bf` описывают свидетельство 20.11, не нынешний установленный код. Сохранённый CC03 frozen scope-аудит имеет историческое исключение; успешный selected CI не доказывает LIVE.

Kimi Code: прочитать `ControlCenter/tests/test_cc07_command_channel.py`, `test_cc07_admin_control.py`, `test_v20_controller.py`; объяснить неизвестный результат и fail-closed в синтетическом сценарии, выполнить только разрешённые офлайн-тесты в изолированной копии. Без настоящих кнопок, FINAM, DPAPI, Windows Tasks, SQLite или localhost управления.
