# R7 — аудит оставляемых файлов: V1 недостоверен, V2 подготовлен (21.11.2026)

**R7_RETAINED_STATIC_V1=INVALID_AS_EVIDENCE; no deletion, no merge.**

Оператор выполнил `r7_retained_static_audit.py` на изолированном checkout D: и передал `r7-retained-static-audit-v1.json`. Его SHA256 **b5928f1c2421b4c132185789769045ec0271c75de4de712e18a45b3e443eeb02** совпадает с Windows stdout. Исходные HEAD/tree прежние: `f15d565755b996252081ed49ed5a094ee1e8d820` / `44a5fef98dd8a3b6bc3e6d172f64fafddac5df4b`. Отчёт содержит **6,948 retained**, **3,747 content_read_errors**, только **4 text_scanned** и **4 python_parse_successes**, 15 oversize text files skipped и 3,182 files excluded by extension. Список ошибок обрезан до 120, в основном `SIZE_MISMATCH`. Сообщённые нули AST imports/dynamic hotspots **НЕ ДОКАЗЫВАЮТ отсутствие зависимостей**.

**Причина дефекта V1:** в строках исходного сканера `filename.read_bytes()` и `len(content) != entry['logical_bytes']` происходит сравнение байтов рабочего Windows checkout с исходными Git blob. Git checkout может применять CRLF/autocrlf/filters; в нём размеры могут не соответствовать blob, даже если исходный Git snapshot не менялся. Это дефект метода, не доказательство повреждения файла. До повторного Git-object скана нельзя делать вывод о содержимом 3,747 неразобранных файлов.

**V2 исправление:** сканировать зафиксированные Git blob SHA из проверенного inventory через бинарный `git cat-file --batch`, проверить type=blob, точный размер и Git blob SHA1, затем статически прочитать текст и AST без выполнения/импорта. Исходная история и Windows файлы не меняются. На синтетическом Git fixture, включая CRLF vs LF рабочего дерева, **13/13 unit tests PASS** и end-to-end static audit PASS. **Фактический прогон V2 на Intel ещё не выполнялся.**

- Комплект: `R7_Retained_Static_Audit_v2_20261121.zip`, bytes=9096, SHA256 `04B9BD1520807F60A491E0804E9E4137D7B8687C692119345FA018E96F408E22`. Содержит программу `r7_retained_static_audit_v2.py`, 13 тестов и README; распространяется как артефакт чата, не установлен на LIVE.
- Сохранять предыдущий V1 JSON как доказательство дефекта; для V2 новое имя `r7-retained-static-audit-v2.json`, новая папка установки. ZIP и новый выход строго проверять на существование; без перезаписи.
- Для запуска использовать исключительно isolated checkout `D:\TradingSystemsR7\discovery-checkpoint-20261120\market-pattern-discovery-scan-checkout`, существующий `whole-main-inventory-v1.json` (SHA256 `f3868a4359662bf33804a50847288391a3336753b21e115b985b8f9a63853865`), временный `GIT_CONFIG_COUNT=1` / `safe.directory` для D: и существующий embedded Python на C:.
- **Не отменяет** изоляционных offline регрессий V20/CC/TRL/H1/M15, исторической A/B/C воспроизводимости, динамических/внешних потребителей, 15 oversized текстовых и бинарных исследований. Нельзя выполнять реальный `git rm`, Git merge или воздействовать на LIVE/FINAM.

Git archive branch `archive/pre-r7-cleanup` protected under ruleset #27793383; separate USB Seagate D: Git bundle SHA verified PASS. Главное ограничение R7: cleanup Merge только после проверенного source closure и отдельного разрешения оператора.

## 21.11.2026 — фактический V2 Git-blob scan на Intel, отчет оператора

Evidence key: R7_RETAINED_STATIC_V2_OPERATOR_STDOUT_20261121. Пользователь выполнил V2 на изолированной копии `D:\TradingSystemsR7\discovery-checkpoint-20261120\market-pattern-discovery-scan-checkout`. Вывод программы: 6,948 retained; 3,751 immutable Git blobs text_scanned; 1,322 Python AST parsed; 0 read errors, 0 AST parse errors, 0 direct A/B/C imports, 0 candidate code refs; 40 generic dynamic import/exec/eval hotspot files. Verdict `STATIC_GIT_BLOB_ONLY_NOT_DEPENDENCY_CLOSURE_NO_DELETE_AUTHORIZATION`; shell `R7_STATIC_V2=REPORT_CREATED`. SHA256 reported by Windows **95526ac4716dc6f19da888ad57e34bc8e89840a081fd23f252ca177689075994**.

**Evidence limitation:** screenshot/stdout only; original `r7-retained-static-audit-v2.json` NOT YET uploaded for independent SHA verification and inspection of all 40 paths/sites. Do not interpret `0` literal matches as dynamic closure. There are skipped unselected extensions and 15 oversized text blobs. Old V1 bad results remain invalid.

**Next decision:** upload/inspect full V2 JSON, categorize 40 by concrete path/function/argument and classify any dynamic candidate reachability; then safe disposable reduced-tree regression of protected V20/CC/TRL/H1/M15 and original A/B/C historical replay. Merging a cleanup PR and real deletion are still blocked.
