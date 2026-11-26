# Control Center V20 — паспорт

**ACTIVE operator panel, not a trading algorithm.** [CC README](../ControlCenter/README.md), [CC-08 Operations](../ControlCenter/docs/V20_CC08_OPERATIONS.md), `ControlCenter/controller/`, `cc/`, `tests/`.

UI на Intel: `C:\Control Center\v20-preview-d80f2446\v20_app.py`, локальный `http://127.0.0.1:8502`. Три робота V20; READONLY refresh отличается от START/PAUSE/STOP/RESTART/RECOVER в CC-07. Документированный 20.11 install+compatibility PASS — датированное свидетельство, не текущая LIVE проверка.

Установленные по операторскому свидетельству blobs: CC-07 operator `10de325be0335733a248c412943f39d45bd93c62`, Python adapter `ef2fa2cd6b0ddfefc920548995274f123c5884bf`. HTTP 200, Task Running и HEALTHY **не** доказывают broker FLAT/ARMED/SLTP.

Старый CC-03/H1-контент в `ControlCenter/` сохранён как история и test provenance. Его исходный scope_audit давал исторический native exit 1; успех узкого offline CI не означает исправленного полного acceptance.

**Экзамен Kimi Code:** синтетический OFFLINE журнал и gate отказов, различие refresh и операторской команды, unknown POST fail closed, проверка границ с V20, контроль доступа. Не нажимать LIVE-кнопки и не читать DPAPI/FINAM.
