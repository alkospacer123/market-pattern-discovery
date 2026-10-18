# CC-03: готовность физической установки manual OS source

Дата подготовки: 18.10.2026 MSK. Инженерная база #549/main `9506d5c8790d4d3b3eabb629d38532a581051e54`. Intel не подключался; physical source activation, установка и любые ACL/account changes не выполнялись и этим Draft не разрешены.

| Условие | Статус / требуемое evidence |
| --- | --- |
| Код ручного Task/process source и отказ без policy | Подготовлен к review; точный Windows-native CI в Draft PR |
| CI sandbox ccpanel/token/ACL/Task/process/replace | Только hosted engineering evidence, не Intel PASS |
| Intel A | NOT_EXECUTED этим заданием; продолжать отдельно от #549 с protected cc03.intel-preflight-policy.v2 |
| Intel B: installation | NOT_AUTHORIZED; существующие ccpanel/owners/DACL/effective rights/listener не проверены |
| Intel C: source binding/TTL | NOT_APPROVED; active manual-os-policy.json не создавался |
| Task/CIM read под реальным ccpanel | NOT_VERIFIED; возможен ACCESS_DENIED, auto repair запрещён |
| FINAM/token/DPAPI/private/trading authority | Не требуются источнику; доступ панели запрещён |
| Полное heartbeat/reconciliation/positions/SLTP | UNKNOWN; sanctioned check-script source отсутствует |
| Cross-terminal-session execution на Intel | NOT_VERIFIED; pipe namespace не session-local, hosted contention/recovery проверяются отдельно |
| Независимый внешний reviewer | Approval не получен этим отчётом; автоматические scope/manifest/ETW audits не заменяют reviewer |

**Физическая установка сейчас не готова к исполнению: отсутствуют отдельные B/C решения и реальные Intel evidence.** Рабочий H1 остаётся вне scope; его Task/ARM/authorization/strategy/account не менять ради панели.

Будущие шаги оператора (документ, не команды к исполнению сейчас):

1. Завершить отдельный readonly preflight A по #549: проверить package/head/digest, protected v2 policy, заранее утверждённый standard observer, exact Task bracket. Сохранить фактический Intel report. A PASS не разрешает B/C и не требует остановки RUNNING H1.
2. После независимого review и отдельного B разрешения проверить существующий enabled стандартный ccpanel, полный primary token, owners/protected DACL всех CC roots и policy ancestors, отсутствие private read/app+venv+export write, единственный 127.0.0.1:8501 listener. Если ACL/account недостаточны — STOP, не создавать/менять их в рамках этого задания.
3. Отдельно утвердить C `cc03.manual-os-policy.v1` с exact Task XML/principal и существующими Task-read правами ccpanel. source_id/alias/random binding — локальные labels, не доказательство FINAM binding. Явно выбрать TTL; process_binding оставить null, пока независимо не утверждены PID/epoch/image/command/owner. Никакого автоматического PID discovery/rebind.
4. Только после такого C решения администратор размещает CC-only policy рядом с app/deployment с trusted owner и readonly правами панели. Не копировать A policy, не помещать secret и не давать private access. Проверить package manifest и что active policy исключена из распространения.
5. В manual WINDOWS_OS_ONLY проверить zero live calls до кнопки; один click → один bounded helper; параллельный click → UNKNOWN/no retry; cache expiration и новая ошибка скрывают facts. При ACCESS_DENIED сохранить UNKNOWN и STOP вместо grants. Task/process факты не заменяют heartbeat или health.
6. Сохранить отдельный Intel acceptance report: exact package/head, SID/ACL/token evidence, Task before/after, timeout/cleanup/gate/recovery, M15 NOT_DEPLOYED и 10 disabled controls. Не называть hosted CI CC03_PHYSICAL_PASS. Не выполнять merge/deployment этим инженерным заданием.

До разрешённой установки rollback здесь не нужен. Для отдельного будущего rollback допустим только собственный процесс/пакет CC по принятому B plan; H1/M15, Task, kill-switch, authorization, SQLite/WAL, FINAM не затрагиваются.
