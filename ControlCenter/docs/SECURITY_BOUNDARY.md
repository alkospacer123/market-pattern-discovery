# Граница безопасности CC-00 / CC-01

Весь новый код и документация находятся в `ControlCenter/`. Текущий процесс имеет
только синтетические данные в памяти. Отсутствуют импорты TradingSystemLab,
IntradayLab, FINAM SDK, sqlite3, OS/process/network API в runtime приложения.
Streamlit использует свой HTTP/WebSocket server для браузера; это единственный
необходимый локальный сетевой сервис. Сам прикладной код не выполняет сетевые запросы.

## Запрещённые операции

- Реальные заявки, отмены, flatten, FINAM polling, trading tokens и credential storage.
- Изменение любых существующих файлов торговых проектов, стратегий/параметров,
  результатов исследований, market data, production-конфигурации и дорожных карт.
- Чтение или запись production SQLite/WAL из UI, миграции, снятие unresolved gate.
- Windows Tasks start/stop/rebind/restart, shell/PowerShell/subprocess и arbitrary commands.
- Изменение HALTED, FINAM_FILL_AUTHORITY_VERIFIED, frozen identity, R15 или разрешений.
- Intel rollout, обновление production checkout, merge и auto-merge.

Кнопки «Пауза новых входов», «Аварийная остановка», «Безопасная остановка»,
«Перезапуск», «Диагностика» всегда `disabled=True`; on_click и обработчиков нет.
Переключение сценария меняет только локальную демонстрацию.

## Изоляция и отсутствие данных

H1 и M15 имеют разные scopes DEMO-H1 / DEMO-M15, независимые снимки и ошибки.
Cross-account snapshot отвергается. UNKNOWN не равен 0; stale snapshot не превращается
в HEALTHY при получении/перерисовке. ACK и POSITION_OBSERVED не дают доказательства fill;
стоп-цена не утверждает реальную защиту. Ни одна DEMO-запись не является broker truth.
Ошибка будущего источника не должна показывать raw exception с секретами.

M15 не наследует параметры/инструменты H1. Нет production runtime authority;
DEMO-график M15 не служит свидетельством развёртывания или прибыли.

## Локальный запуск

Обычный loopback `127.0.0.1:8501`, отдельный venv, CORS/XSRF включены, usage statistics
отключены. Приёмка выполнена из копии только ControlCenter, в процессе с очищенным
окружением (без переданных токенов и путей роботов), без production checkout рядом.
Приложение не требует project-root imports. Это подтверждает автономность CC-01,
**не** фактические ACL или состояние Intel: доступа к нему не было.

UI не является OS sandbox. При будущем подключении обязательна отдельная
непривилегированная Windows identity с файловыми ACL без доступа к секретам/торговым
каталогам. Установка и проверка этих ACL — CC-03, сейчас не выполнена.
На этой итерации нет auth/RBAC, TLS или remote access. Порт нельзя публиковать;
VPN/authenticated reverse proxy требуют отдельного проектирования и разрешения.

## Проверки

AST-аудит runtime использует allowlist imports и запрещает динамические imports,
файловые write/open, DB/process/command calls и button callbacks. Поведенческий тест
блокирует socket/urlopen/sqlite/subprocess/os.system при выполнении сценариев.
AppTest проверяет disabled-кнопки и независимые состояния. Фактический git diff,
Git tree IDs и SHA-256 защищённых файлов сравниваются отдельным способом в ходе
приёмки. Эти проверки не заменяют внешний review, permission boundary ОС или
физическую broker reconciliation. Независимый внешний аудит PR ожидается.
