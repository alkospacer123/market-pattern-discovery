# V20 Trading System — инженерный журнал

[Текущий статус](STATUS.md) · [Общие правила](../AGENTS.md)

Журнал GPT/Kimi: добавляй записи в конец после значимого результата, принятого решения, незавершённого checkpoint или передачи задачи. Не записывай каждый запрос, действие или полный отчёт; ссылки на PR, commit и доказательства достаточны. Старые записи не переписывай; исправления — новой записью со ссылкой на исходную.

Формат одной записи:

- Дата/TZ, исполнитель и среда; задача.
- Результат и статус; что изменено или не выполнено.
- Проверки и доказательства: точные SHA/PR/артефакты, PASS/FAIL/SKIP/UNKNOWN по факту.
- Решения владельца, остаточные риски/блокеры.
- Следующий шаг и нужное разрешение.

Не включай секреты, идентификаторы счетов, приватные журналы и необезличенные брокерские данные. Запись не разрешает Merge, установку или LIVE. Записывай в рамках разрешённой ветки/PR; Draft не равен принятому MAIN. Если исход записи неизвестен, сначала проверь HEAD/содержимое, не повторяй вслепую.

## Записи

Первые содержательные записи добавит профильный чат после сверки источников. Исторические записи обозначать датой события и датой внесения; не реконструировать неизвестные факты.

### 27.11.2026 — C3.2, историческая сводка (GPT/GitHub documentation)

- 19–20.11 (события): R088 60/30/45 + TP6 + Protect3 + HOLD5, EXT2 OFF; операторское свидетельство `V20_ALL3_PREPOST_PROTECT3_FIX=PASS_3_RUNNING_HALTED_FRESH_CYCLES`. [Release](V20-08/LIVE_RELEASE_R088_20261120_RU.md). Последнее HALTED 3/3 — REPORTED_ONLY, текущий broker state UNKNOWN.
- 26.11: [#601](https://github.com/alkospacer123/market-pattern-discovery/pull/601) MERGED `d6f21355d33b22d35a98a1539f2bae2154f20b94`, diagnostic SOURCE fix Protect3, INSTALLED не доказан. Причина 20.11 UNKNOWN. Market входы сохраняются, лимитные после 1–2 месяцев статистики; единый пакет для трёх роботов, отдельный допуск.
- 27.11: профильный HANDOFF, MAIN `2ac85eb5bcdd8757144898b5a27369329f4d125c`, исходный HEAD #608 `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`; Skill blob `81880e77f97977c3067e923a8516ce52382475eb`, 8/8 mirrored blobs MATCH. Original patch не предоставлен, документы реконструированы координатором; fallback/удаление/отключение Skill и qualification не приняты. Intel/FINAM/LIVE не проверялись.

### 27.11.2026 — итоговый допуск, Post-G9 (GPT/GitHub documentation)

- Владелец утвердил `FULL_PARITY_OWNER_ADMITTED`; #614 MERGED, #615 — документационный closeout. Kimi Code workspace `C:\V20Lab` и чтение резервных знаний подтверждены по отчёту; не свежая INSTALLED/LIVE проверка. Следующая работа — самостоятельная диагностика трёх роботов, #601 и оценка HOLD5 по согласованному scope. Не повторять экзамены. Сохраняются отдельные approvals и COC; deploy/ARM/FINAM не разрешены этим решением. [Recovery STATUS](../recovery/STATUS.md).

### 27.11.2026 — Post-G9: независимый SOURCE-аудит V20 (Kimi Chat → GPT review)

**Контекст:** Kimi Chat, READONLY GitHub, MAIN `a3aa48fee59b0a077794cccc5ae3eef33d62a6c5`; отчёт передан владельцем в GPT. GPT независимо сверил исходники и все девять patch-файлов R088 по релевантным условиям, без rebuild или исполнения тестов. Автор аудита — Kimi; независимое статическое ревью и запись по разрешению владельца — GPT, PR #617. Kimi не публиковал результат из-за явного запрета записи в задании, не нарушение AGENTS. SOURCE-аудит завершён, не readiness PASS. Новых данных INSTALLED/LIVE/FINAM нет. CRITICAL не подтверждён. Сохраняем различие статического дефекта, потенциального сценария и фактически воспроизведённого отказа.

| ID / приоритет после GPT review | Находка, доказательство и следующий шаг |
| --- | --- |
| F1 HIGH / static confirmed | Partial 1→2: [observe_protected_entry](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_execution.py#L675-L785) допускает прежний стоп при росте объёма и PASS риска, сохраняет h1_same_stop_growth_observed; [sealed verifier](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_live.py#L317-L365) требует stop_conforms=True. Девять патчей не снимают это противоречие. Возможный HALT следующего цикла; физическое покрытие выросшей позиции не доказано. Воспроизвести полный growth→RECONCILED→next dispatcher; исправлять узко, сохраняя точный durable fill, ownership, актуальную 100%-защиту, риск, без второго POST; отрицательные свидетели и restart. |
| F2 HIGH / potential, уточнено GPT | [observe/reconcile](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_execution.py#L552-L785) не seal terminal partial/CANCELED; возможна зависимость от исчезнувшего terminal order и старых trades. Но [exit](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_execution.py#L1120-L1166) допускает PARTIAL_FILL, поэтому невозможность HOLD5 не доказана. Тест terminal partial→restart/исчезновение entry→HOLD5/flat cleanup с остаточной позицией; исправить при воспроизведении, не досылать entry и не добавлять второй SLTP. Первичный partial защищается SL без linked TP6; полная TP6/Protect3 модель не гарантирована, изменение политики отдельно владельцем. |
| F3 MEDIUM / static mechanism | [prepare_entry](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_execution.py#L440-L494) признаёт отражённое ГО по первоначальному broker_stop_id, а [account_risk](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/account_risk.py#L134-L150) повторно резервирует неотражённое ГО. После Protect3 возможен лишний отказ/меньший размер входа, не ослабление риска. Проверить с реальным по модели successor proof и исправить при подтверждении; не считать любую позицию автоматически отражённой. |
| F4 HIGH / static confirmed (Kimi MEDIUM) | [installer](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/V20-08/r088-prepost-all3-20261119-install.ps1) меняет pin launcher текстом; [launcher](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/V20-08/v20-08-live-launch.ps1) привязан к прежнему source_commit/authorization. Нет конечной единой цепочки SHA launcher/patches/DERIVED. #601 SOURCE-only не входит в старый installer. Воспроизвести BASE+9/+10, замкнуть manifest и согласовать release/auth compatibility; не менять production authorization самостоятельно. |
| F5 HIGH / transport gate (Kimi MEDIUM) | [H1 transport](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/TradingSystemLab/stage8_robot/finam_api.py#L79-L112) допускает 401 refresh и 429 retry не только GET; [V20 wrapper](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/finam_live.py#L103-L121) лишь обрабатывает итоговое исключение. GPT расширил scope с DELETE до торговых POST и DELETE. Timeout/lost response/5xx/401/429 — fake transport matrix с подсчётом внешних writes и доказательством семантики, не повторять unknown; сам факт 401/429 не доказывает исполнение первой заявки. При необходимости V20-specific fix, не менять H1 без отдельного решения. |
| F6 LOW / static confirmed | [operator](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/V20-08/v20-08-live-operator.ps1#L44-L61) не классифицирует R070_PROTECT3_REPLACED_NEEDS_NEXT_BROKER_CHECK, PROTECT3_QUOTE_UNVERIFIED_KEEP_OLD_STOP, PROTECT3_QUOTE_GET_FAILED_KEEP_OLD_STOP. Передано в CC-аудит; различать retained/pending/fault, не превращать UNKNOWN в HEALTHY/PASS. |
| F7 MEDIUM / validation gap (Kimi LOW) | [H1 SLTP validator](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/TradingSystemLab/stage8_robot/production_broker_state.py#L137-L155) не проверяет TP price/qty/measure; [R070 restart verifier](https://github.com/alkospacer123/market-pattern-discovery/blob/a3aa48fee59b0a077794cccc5ae3eef33d62a6c5/V20_TradingSystem_M15/v20_runtime/r070_linked_sltp.py#L453-L525) строже. Проверить фактическую достижимость проверки wrong TP6 на sealed→HOLD/Protect3 и до новых входов; не утверждать постоянный пропуск или неправильный LIVE TP. |

**Identity:** MAIN blobs finam_live.py `b80fb9eb135f7cdcb4c78337e2b808c4d7135195`, finam_execution.py `6b600451178b42bd4f8b2037995e7db3a9ad27c8`; historical BASE+9 `5d30270d3936fb52f58a61aa3abbf070d7df6b57` / `0fc4c454d55f37e4e87fd74e3370cbc1ad83b53f`. #601 diagnostic-only expected BASE+10 live blob `437d69280a15a2ad67ffbe7f2377583f430d5252`, not rebuilt/installed; bounded protect3_reason, not a fix for F1–F5. R088 architecture and market-entry policy retained.

**Evolution:** Kimi recommends keeping HOLD5, TIME3 443413.20/PF2.00345 vs HOLD5 486684.60/PF2.12691; GPT clarified both are EXT2 ON with known TIME3 +245 RUB parity discrepancy, not current EXT2 OFF comparator or TRUE OOS. Current R089/R097 OFF baseline, no new research replay. Remaining optional optimization in one-time TRL Evolution.

**Next:** CC audit in progress per owner; then one-time TRL Evolution, shared PR #617 documentation only, consolidated independent review and owner Merge decision. Proposed pre-ARM scope: F1 correction, F2/F5/F7 targeted checks and fixes if needed, F4/#601 release identity, F3 if confirmed in comparable test, F6 coordinate with CC. All-three unified package, separate Code execution scope/isolated runner, backup/rollback and read-only postflight; no ARM/deploy/FINAM permission. No code/tests/Intel/LIVE changes in this audit or record.


### 28.11.2026 — PG10.2 V20 SOURCE + Windows CI (Kimi Code, PR #618)

- MAIN `568b339a1bb3ebc3f025d74762ae66c344278be9` (Merge #617); PG10.1 принят владельцем и не повторялся. Кодовый HEAD `ef094d51b7bfc0e32b2916dda9971acd7ff61657`; ветка изолирована от runtime. Выполнены только утверждённые F3/F4/F6 + #601 и совместный CC package; R088, риск, capital 60/30/45, NEXT_OPEN, TP6, Protect3, HOLD5, EXT2 OFF, Python/deps не изменены.
- **F3 CONFIRMED_SYNTHETIC:** Windows run [46133704921](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/46133704921) SUCCESS на кодовом HEAD. BASE+10: 4 tests, 3 ожидаемые ошибки отсутствующего successor-aware API; базовый расчёт подтвердил повторное резервирование (quantity 21 вместо 23). DERIVED+11: 4/4 F3 PASS, включая unknown/wrong successor и missing fresh reader; targeted suite 52 tests OK, 49 выполнены +3 pre-existing optional skips. BASE reverse/restore PASS. `account_risk.py` не менялся; фактическое брокерское ГО признаётся только по полному successor proof.
- **F4 SOURCE_BUILD_PASS:** 11 ordered patches, DERIVED live `98037310ee5238f035ae174285a2f244cc1aeffd`, execution `7f963423aa0e957d4eb5408aa1b77143c270b688`; manifest содержит raw SHA256/raw Git blob/filtered Git blob, CC compatibility, dependencies и install/rollback guards. Deterministic release 24 files, 3/3 release tests PASS; ZIP SHA256 `2b2901efa2553c18609b65bce270401326850572f4ab0cdaf9c2841be67b8c54`, artifact финального exact-head run передаётся в handoff. ZIP identity относится к pinned CI Python 3.12.10; локальный другой Python/deflate не используется как альтернативный release SHA. Installer/launcher проверены native parser, не исполнялись.
- F6: три Protect3 codes согласованы как PENDING; HALTED не смешивается с worker health/PASS. CC native results — CC JOURNAL. #601 diagnostic logging regression PASS. F1/F2/F5/F7 не реализованы и не закрыты. При более широком промежуточном вызове `test_finam_journal` обнаружен несвязанный historical Windows long-path/8.3 comparison failure; он не исправлялся вне scope, целевой restart/no-retry witness включён отдельно.
- INSTALLED=NO, LIVE/FINAM/Tasks=UNKNOWN/UNCHANGED; deploy, production rotation, reboot, ARM/HALT, Merge не выполнялись. Финальная документация и exact-final-head CI публикуются следующим документным commit; кодовый HEAD выше не переносится автоматически на новый SHA.


### 28.11.2026 — PG10.2.1 installer review remediation (Kimi Code, PR #618)

- Без изменения восьми PG10.2 обновлений и BASE+11: installer получил проверяемую installation transaction, полную backup verification, atomic writes после interruption, CC process/listener/health postflight и запрет rollback при несовместимых journals/archives. Forward recovery завершает новый release; unknown bytes и durable state сохраняются. Mixed launcher/runtime требует внешней FINAM READONLY FLAT-аттестации, а не обхода gate.
- Functional Windows harness исполняет реальные installer functions в disposable NTFS trees с mock-only Windows boundaries. Финальные CI и artifact evidence публикуются в описании PR, без дополнительного документального commit. Runtime/Tasks/FINAM/reboot/ARM/HALT/Merge не затронуты.


### 28.11.2026 — PG10.2.2 forward recovery fix

- Устранено противоречие случайного transaction ID: install возобновляет существующую проверенную transaction/BackupRoot без нового GUID или повторного backup. Исходное CC state, known old/new bytes, HALTED/FLAT/quiescence сохранены; после NEW pair FLAT повторяется до workers. Full-path synthetic test исполняет сам installer, включая MIXED refusal, стабильный resume и повторное interruption/recovery. Runtime/FINAM/Tasks/reboot/ARM/HALT/Merge не затронуты; доказательства публикуются в описании PR.


### 28.11.2026 — PG10.5.1A real-Git installed identity remediation

- **Root cause:** PG10.5.1 READONLY check отклонил фактические V20 runtime CRLF blobs `finam_live.py=1eeb71cfaf81a56e65062a375ed9362fd805512a`, `finam_execution.py=36fc779e3a41e3cbe992d88de9802b2b237e17e6`. GPT независимо воспроизвёл BASE+9 и подтвердил, что это CRLF-формы доказанных LF `5d30270d…6b57` / `0fc4c454…b53f`, а не содержательное отклонение. BASE+11 также совпал с manifest.
- Ветка `fix/pg10-2-installed-identity-crlf` от MAIN `37e9e02c4a74ad895510e767aa99ecec0818f95e`. Installer получил общий OLD/NEW/MIXED classifier; manifest содержит только четыре явных OLD raw aliases. NEW принимается только при точных canonical package raw bytes; substantive unknown остаётся отказом. `verify-package`, raw backup/restore, recovery и rollback boundaries не ослаблены.
- Существующий full-path test лишён mock подмены identity: OLD BASE+9 и historical launcher reconstructions проверяются реальным `git hash-object`. Добавлен Windows real-Git сценарий LF/CRLF, NEW, MIXED, substantive-change refusal, exact-byte backup/shared recovery-rollback restore и настоящий `-mode check` из staging вне Git checkout. Локально Python 3.12.10: **6/6 PASS**; deterministic local candidate ZIP SHA256 `9d8a961b836e6b2840b09f7c490afbfa5d3017341f78bb70f2afbf1a2b1e1799`. Exact-head CI и скачанный artifact проверяются после push, результат — описание PR.
- Торговые BASE/BASE+11, strategy/risk и восемь PG10.2 обновлений не изменены. Deploy, production files, FINAM, Tasks, ACL, reboot, ARM/HALT, rollback/recover, rotation и Merge не выполнялись. Остаточные READONLY preflight gaps сохраняются до принятия исправления и отдельных полномочий.


### 28.11.2026 — PG10.5.1C historical venv и process-tree restart fix

- **Root cause:** V20 CC installer запускал base `runtime/python312`, который по provenance является полным CPython только с pip, а не panel venv. Historical `C:\Control Center\venv` сохранил Streamlit 1.50.0 и production `requirements-windows.lock` **40/40 без mismatches**, `pip check=PASS`. CI acceptance lock не использовался как основание для dependency update; никаких установок пакетов.
- Installer использует `venv\Scripts\python.exe`, принимает OLD standalone base и NEW venv launcher/direct runtime child. `started-listener` разрешает только same PID либо непосредственный child запущенного parent; `start-cc` валидирует фактический listener PID. Это сохраняет остановку исходного OLD CC и доказывает NEW process/health/source IDs.
- Изолированный runtime staging: 4068 base +13508 venv files byte-verified, изменены только пути в копии `pyvenv.cfg`. На `127.0.0.1:18502` фактический SOURCE candidate исполнил `start-cc NEW` и общий recover/rollback `start-cc BACKUP`: оба health/root 200 и source-ID PASS, venv parents завершились без orphans. Production 8502 не останавливался. Локальный Python 3.12.10 release suite **6/6 PASS**, включая новый OLD-base/NEW-child regression; deterministic candidate ZIP `d909e9462cf3b39cc9c8a3fa4305769227c4d2992f1674ce1a703dce63d76d5d`. Exact-head CI и скачанный artifact — в описании нового PR.
- Production runtime/dependencies/files, Tasks, FINAM, ACL, reboot, ARM/HALT, physical install/recover/rollback и Merge не выполнялись. Исторические audit UNKNOWN и durable execution_halt limitations сохраняются в Recovery JOURNAL.


### 28.11.2026 — PG10.5.2 coordinated V20/CC installation

- Владелец разрешил install accepted artifact `d909e946…d76d5d`. Preflight: BackupRoot unique, durable NONE 3/3, FINAM FLAT 3/3, Running/HALTED/fresh 3/3. Installer создал 11 backup records и SQLite snapshots 3/3 `v20-live-20261128T185727Z`; DPAPI excluded. Transaction `7e34ea4a6449459296a4beb56ad223e8` = **COMPLETED**, coherent_before/release match=true.
- Postflight: NEW raw identities **11/11**, installer check PASS, Tasks Running 3/3, HALTED/fresh cycles 3/3, FINAM GET-only FLAT 3/3. Торговая стратегия/капитал/dependencies/ACL не изменялись; ARM/reboot/broker writes/rollback/recover не выполнялись.
- Wrapper ожидал постоянный CC descendant и не сохранил stdout install marker; install не повторялся. Wrapper PIDs завершены точечно после COMPLETED/postflight, новый CC не останавливался. Доказательство результата — durable transaction и независимый postflight, не повторная установка.
