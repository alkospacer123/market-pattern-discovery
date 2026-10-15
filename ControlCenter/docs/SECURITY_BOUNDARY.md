# Граница безопасности — CC-03

Изменения исключительно ControlCenter. TradingSystemLab/IntradayLab byte/Git trees защищены. No strategy/frozen/risk/execution/trading authorization changes. Нет FINAM client, Trading Token, production SQLite/WAL open, robot Task mutation, production service launch, rearm/order/cancel/flatten. UI не управляет брокерскими позициями. Все десять controls disabled без handlers.

Три разные capabilities:

| Компонент | Разрешено | Доверие/отказ |
| --- | --- | --- |
| Panel `app.py`, `cc/` | DEMO в памяти, fixed fixture, fixed sanitized export + safe receiving policy, rendering | Никаких write paths; source unknown/mismatch/error → новый UNKNOWN, без raw errors/cache |
| File worker | POSIX fixture no-follow или Windows Kernel32 local NTFS readonly handles; policy owner/DACL read | API unavailable, reparse, traversal, hardlink, replacement, partial/size/timeout → reject; child process не shell |
| Independent `exporter/` | Два admin-approved pinned JSON read, bounded strict redaction, atomic CC-only write | Не импортируется panel/H1; no broker/DB/network/Task; default preview, real policy отдельно |
| Deployment scripts | После `-Execute`: own file copy/venv/offline pip, foreground CC launch/verify/rollback | По умолчанию PREVIEW; не применяют ACL, не управляют robot Task; exact manual task probe read-only отдельно |

Windows file `CreateFileW` access только FILE_READ_ATTRIBUTES|READ_CONTROL dirs и GENERIC_READ leaf, OPEN_EXISTING. No write/create/truncate request. Leaf FILE_SHARE_DELETE разрешает producer atomic replace; after/path checks reject changed observation. Security descriptors читаются GetSecurityInfo; policies должны принадлежать SYSTEM/Admin, никакие другие SID не могут менять их или policy ancestors (кроме drive root, проверяемого отдельно physical ACL review). Policy боoleans не являются доказательством своих ACL. Export/source producer доверяется только после отдельно утверждённого root/ACL/evidence. [Ограничения, гонки, ACL matrix и native tests](CC03_WINDOWS_SECURITY.md).

Application policy и private policy раздельны. Exporter не может писать receiver policy; panel не может читать private policy или H1 sources/token directories. Active policy файлы не входят в Git/release manifest. Поставляемые examples нерабочие, production TTL нет. SHA-256 подтверждает целостность, не broker/source authentication. Случайный binding reference/alias разрешён к показу, account hash и actual paths не попадают в export/UI. Unknown/unexpected fields отвергаются, ошибки фиксированные safe codes.

Данные исполнения CC-02 сохраняют шесть уровней фактов; CC-03 partial exporter не публикует их вовсе. Heartbeat counters/protection rows не становятся FILL_CONFIRMED, нулём позиций/риска или active SLTP. Неполные финансы UNKNOWN, cashflows не прибыль. Статическое HALTED из исторической документации не выдаётся за измерение; actual Task/process пока NEEDS_SOURCE_APPROVAL. M15 не получает H1-account/R15/financial identity.

OS isolation — необходимая часть future acceptance, не свойство Python sandbox. Start scripts проверяют dedicated SID/root ACL; effective group/privileges, source ancestors/leaf и negative access checks ещё требуют Windows оператора. Application/venv admin-owned, panel только logs write, exporter только export write. Никакие права не наследуются от robot identity. При невозможности узких grants оставить source UNAVAILABLE, не читать SQLite/секреты обходным путём.

Сеть: Streamlit 127.0.0.1, CORS/XSRF включены. VPN/authenticated restricted proxy только будущий отдельно утверждённый доступ; public 8501/admin credentials запрещены. Нет физического Intel контакта, deployment или Windows tests в этой итерации. Процедура физической приёмки и rollback — только документы, не выполненные действия.
