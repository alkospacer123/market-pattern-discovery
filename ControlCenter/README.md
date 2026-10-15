# TradingSystemLab Control Center — CC-00 / CC-01

Локальный бесплатный Streamlit-интерфейс на русском для двух независимых контуров:
TradingSystemLab `T3/H1/TRAIL1` и IntradayLab `T3/M15/SESSION`.
**Только SYNTHETIC / DEMO. Торговые системы, FINAM и production SQLite не подключены.**
Это основа будущего мониторинга, не разрешение торговли и не установка на Intel.

В исходном сценарии H1 — **HALTED**, торговля запрещена; identity
`TRAIL1__N4_01__FULL__R15`, N4: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF,
справочный frozen риск 1,5% / максимум 6%. M15 — **NOT_DEPLOYED / NO_RUNTIME_AUTHORITY**:
heartbeat, счёт брокера, позиции, финансы, инструменты и production identity UNKNOWN.
`DEMO-M15-A/B` — искусственные подписи графика, не выбранные инструменты M15.
Документированный выбор [#527](../IntradayLab/SELECTED_T3_M15_SESSION_T1_R20.md):
план `T3_M15_T1_TRAIL35_N4_R20`, SESSION T1 / NEXT_OPEN / FULL N4, R20 2% / 8%.
Это план будущего робота; actual production identity и фактическая capacity неизвестны.
План показан справочно, без присвоения R20 активному runtime.
OOS PASS по сообщению оператора не означает наличие runtime или разрешение LIVE.

Семь разделов: главная панель, мониторы H1/M15, графики и сигналы, сделки и статистика,
журнал событий, управление. Все 10 кнопок управления отключены и не имеют обработчиков.
Капитал, риск, позиции и результаты разных счетов не складываются.

## Windows PowerShell: отдельное окружение

Python **3.11 или 3.12, 64-bit**. Для запуска достаточно скопировать **только этот каталог**
на отдельную машину/в отдельный рабочий каталог. Устанавливать пакет репозитория, подключать
каталоги роботов, рыночные CSV, секреты или брокерский SDK не требуется.

Из корня отдельного checkout (не production checkout Intel):

```powershell
Set-Location .\ControlCenter
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Открыть `http://127.0.0.1:8501`. Остановить локальный UI: Ctrl+C в его консоли.
Активация venv и изменение ExecutionPolicy не нужны. Конфигурация `.streamlit/config.toml`
загружается из текущего каталога: тёмная тема, loopback, без telemetry и file watcher.
Не запускать из корня репозитория с другой конфигурацией.

Для машины без интернета подготовить wheelhouse **на Windows с той же версией Python и архитектурой**:

```powershell
.\.venv\Scripts\python.exe -m pip download -r requirements.txt --dest wheelhouse
# Перенести ControlCenter и wheelhouse в изолированный каталог целевой тестовой машины.
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-index --find-links wheelhouse -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Это инструкция для будущего локального тестирования, не разрешение deployment Intel.
Установка зависимостей требует сети либо заранее подготовленных wheels; само приложение
работает без интернета. Версии прямых зависимостей закреплены; wheelhouse фиксирует
полный набор транзитивных wheels для конкретной Windows/Python. Windows физически
в этой задаче не проверялся; Linux-проверки описаны в отчёте.

## Тестирование

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -c pytest.ini
```

Linux/macOS: `python3 -m venv .venv`, затем `.venv/bin/python -m pip install -r requirements-dev.txt`,
`.venv/bin/python -m pytest -c pytest.ini`, `.venv/bin/python -m streamlit run app.py`.
Зависимости runtime: Streamlit, Plotly; модели и провайдер используют стандартную библиотеку.
Pytest нужен только для проверок, Streamlit AppTest входит в Streamlit.

## Как читать демонстрацию

- Выбор сценария каждого робота независим. Снимки в памяти обновляются раз в 2 секунды,
  без потоков приложения, фоновых циклов и внешних процессов.
- Детерминированность означает одинаковый результат для `(robot, scenario, now)`.
  Настенные часы передаются в провайдер явно. Свечи не меняются в середине периода;
  время локального снимка продвигается с шагом 2 секунды.
- STALE фиксирует старое время источника; UNKNOWN, UNAVAILABLE и MALFORMED скрывают
  неизвестные значения. UNKNOWN никогда не заменяется нулём.
- HEALTHY — только тестовая телеметрия H1, **торговля всё равно запрещена**.
  Сценарии M15 не создают heartbeat, R15, позиции или доходность несуществующего runtime.
- Графики: OHLC, точки DEMO-входа/выхода, вспомогательная DEMO-линия (не T3).
  Сценарий OPEN_POSITION показывает демонстрационный стоп.
- INTENT, REQUESTED, ACK, POSITION_OBSERVED, FILL_CONFIRMED и UNRESOLVED разделены.
  ACK/наблюдение позиции не подтверждают сделку. DEMO-fill имеет отдельное DEMO-доказательство.
- Источник и время показаны рядом с каждым набором данных; строки наследуют provenance
  своего снимка. В таблицах событий дополнительно указаны источник/счёт/время.
- Все времена aware: UTC и MSK (UTC+3). Фильтр дат и месячная статистика — по MSK.

Реальные read-only адаптеры отсутствуют. Следующий этап **CC-02** — отдельный Draft PR
после операторской проверки. Не менять порог 10 секунд DEMO в боевой TTL по аналогии:
он должен учитывать реальный producer, расписание сессий и отдельную authority полей.

Документы: [архитектура](docs/ARCHITECTURE.md), [инвентаризация](docs/SOURCE_INVENTORY.md),
[граница безопасности](docs/SECURITY_BOUNDARY.md), [статус roadmap](docs/ROADMAP_STATUS.md),
[фактическая приёмка](docs/ACCEPTANCE_REPORT.md).
