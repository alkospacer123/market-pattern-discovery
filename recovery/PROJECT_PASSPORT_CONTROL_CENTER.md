# Control Center V20 — паспорт

**Решение владельца 26.11.2026:** #602 — принятый SOURCE-кандидат профилактической проверки HEALTHY/локальной экспозиции и свежести, не установлен. Штатный экспортер не вычисляет HEALTHY и публикует exposure=None; дефект воспроизведён на synthetic snapshot, не подтверждён как LIVE инцидент. Сохранить для планового CC-only обновления при реальной необходимости, installed bytes/pins, backup/rollback и отдельном разрешении. Не обновлять исправную панель ради экзамена; UI не доказывает FINAM truth.

**ACTIVE operator panel, not a trading algorithm.** [CC README](../ControlCenter/README.md), [CC-08 Operations](../ControlCenter/docs/V20_CC08_OPERATIONS.md), `ControlCenter/controller/`, `cc/`, `tests/`.

UI на Intel: `C:\Control Center\v20-preview-d80f2446\v20_app.py`, локальный `http://127.0.0.1:8502`. Три робота V20; READONLY refresh отличается от START/PAUSE/STOP/RESTART/RECOVER в CC-07. Документированный 20.11 install+compatibility PASS — датированное свидетельство, не текущая LIVE проверка.

Установленные по операторскому свидетельству blobs: CC-07 operator `10de325be0335733a248c412943f39d45bd93c62`, Python adapter `ef2fa2cd6b0ddfefc920548995274f123c5884bf`. HTTP 200, Task Running и HEALTHY **не** доказывают broker FLAT/ARMED/SLTP.

Старый CC-03/H1-контент в `ControlCenter/` сохранён как история и test provenance. Его исходный scope_audit давал исторический native exit 1; успех узкого offline CI не означает исправленного полного acceptance.

**Экзамен Kimi Code:** синтетический OFFLINE журнал и gate отказов, различие refresh и операторской команды, unknown POST fail closed, проверка границ с V20, контроль доступа. Не нажимать LIVE-кнопки и не читать DPAPI/FINAM.
