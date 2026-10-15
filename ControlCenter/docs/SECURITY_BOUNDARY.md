# Граница безопасности — CC-02

Изменения только в ControlCenter. Runtime capabilities: synthetic generation,
Streamlit/Plotly rendering и readonly чтение **одного packaged fixture JSON**.
FINAM/network clients, trading tokens, production SQLite/WAL, engine imports,
StateStore constructors, subprocess/PowerShell, Windows Tasks, permissions,
kill switch/authorization, broker order/cancel/flatten отсутствуют.

Единственный OS module — `cc/providers/readonly_file.py`: directory/file readonly
open, read/stat/fstat/close. Нет write/create/truncate/append, rename/unlink/chmod,
процессных/сетевых функций. Ослабление общего import allowlist не выполнялось:
новые stdlib imports разрешены только по трём конкретным receiving modules;
дополнительно проверяются AST и runtime read flags/side effects.

Фиксированный allowlist: `fixtures/h1/h1.snapshot.json` внутри standalone пакета.
Нет UI/file upload/user path/env/query configuration. Файл не может выбрать новый
путь/схему/source/account. Перед показом exact H1/spec/active/commit/test account
binding, строгий nested field allowlist, max 128 KiB, UTF-8/JSON/schema/hash/time и
cross-record validation. Unknown/free-form fields (включая raw IDs/secrets/errors)
отвергаются целиком. Source provenance задаёт код, не `synthetic=false` в JSON.

Reader не следует symlink ни в одном ancestor/root/file, не принимает hardlink,
FIFO/не regular files; bounded read + identity/size/mtime/ctime/root recheck ловят
частичную запись и substitution. Unsupported secure primitive → UNKNOWN. Не применяет
небезопасный cross-platform fallback. На текущем Windows backend физический reader
не принят; безопасная реализация handle/ACL или sanctioned transport требуется CC-03.
Checksum не подпись. Trust directory ACL/producer authentication нельзя доказать JSON.

Приложение не является OS sandbox. Будущая установка потребует low-privilege identity,
доступ только к export directory, запрет чтения токенов/robot directories и записи
в H1/M15, проверку reparse points/ACL, loopback/VPN/auth separately. Сейчас Intel
не трогался; реальное разграничение OS/physical data не заявляется выполненным.

UNKNOWN не равен 0. Неполные позиции/финансы скрываются; stale/unavailable H1 не
оставляет HEALTHY/цифры из прошлого снимка. HALTED со старым heartbeat не означает
неисправность, но датированное HALTED не считается новым наблюдением. ACK не fill;
position не exact fill price; planned stop не действующее поручение; evidence fixture
не broker truth. Все числовые fixture значения явно OFFLINE_FIXTURE. M15 остаётся
NOT_DEPLOYED/SYNTHETIC без H1-account/risk/финансов/runtime authority.

Ordinary exceptions возвращают фиксированный `H1_SNAPSHOT_INVALID_OR_UNAVAILABLE`;
payload не логируется/не показывается, прежний снимок не кешируется. KeyboardInterrupt/
SystemExit сохраняются. Fault harness инъецирует RuntimeError/DatabaseError без открытия
БД и проверяет модели/логи/UI/журнал и независимость M15.

Все 10 controls `disabled=True`, без callbacks; UI не выдаёт торговую авторизацию.
Loopback/CORS/XSRF/usage settings сохранены. Нет auth/RBAC, TLS/remote-access rollout,
LIVE profile, exporter или физической приёмки. Один Draft PR, NO MERGE, NO AUTO-MERGE,
NO INTEL DEPLOYMENT. Внешний review PR остаётся отдельным решением, не подменяется
авторскими тестами или отчётом проверок.
