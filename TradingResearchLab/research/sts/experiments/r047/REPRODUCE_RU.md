# R047 — локальное независимое воспроизведение

**Только TRL, без LIVE.** [Замороженный протокол](FROZEN_PROTOCOL.md) · [Тестер](run_r047.py) · [Аудит](audit_r047.py) · [Результаты и вывод](../../TRL_R_2026_047_Missed_Trend_Opportunities.md).

В GitHub хранятся протокол, аналитический код, отчёт и решения. **Крупные исторические котировки повторно в GitHub не загружаем.** Полный офлайн-архив R047 (код + исходные SHA-фиксированные котировки N4 + R031 каталог + R045 контроль + ноябрьские CSV + журналы + Excel) подготовлен и приложен в разговоре TRL: `TRL_R_2026_047_Missed_Trend_Reproducible.zip`.

Для воспроизведения разархивировать исходный R047 ZIP в отдельную папку с Python, numpy и pandas. В папке с `run_r047.py` выполнить:

`python run_r047.py`

`python audit_r047.py`

Проверить `results/AUDIT.json`, `results/INDEPENDENT_AUDIT.json`, `MANIFEST_SHA256.txt`. Исходные контрольные состояния: 779 ex-post трендовых эпизодов, 366 пропусков Classic; Exact parity 773 BASE/808 TP6, V20 3×45k GO Oct TP6 +381607,6 ₽; 394 prefix checks и 3133 денежных сделок в независимом аудите.

Все сценарии research-only. Никаких обращений к FINAM API, production SQLite, Windows Tasks, торговым токенам и ордерам. История 2023–2026 уже многократно исследована, это не TRUE OOS. ГО — статичные Oct/Nov 2026 proxy, а DD только по закрытым сделкам.