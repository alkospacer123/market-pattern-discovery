# Kimi Chat + Kimi Code — практический экзамен и GPT ↔ Kimi handoff

## Действующий рабочий маршрут — C3 candidate, 27.11.2026

Текущий ход квалификации и решения владельца — [Roadmap](../../ROADMAP.md), [STATUS](../STATUS.md), [KDR](KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). Датированные разделы ниже — исторический протокол G0–G6, не очередь повторных экзаменов. A/B/C приняты в документированных пределах; FULL_PARITY_OWNER_ADMITTED утверждён 27.11.2026. Оба ИИ самостоятельно работают по общим gates. Технические требования к HANDOFF применимы к обоим ИИ и людям; конкретный поставщик ИИ не получает исключительных полномочий.

### Компактный протокол совместной работы

- Инициализация: task ID, проект, проверяемая цель/критерии, scope/exclusions, действующие разрешения по операциям, actor/client/execution context, pinned MAIN/AUDITED_REF/PR base/head, предыдущий принятый checkpoint, failed attempts, defects, UNKNOWN. Применяй общий AGENTS, профильные источники и релевантный COC.
- Ownership: один writer на scope; authority locator, actor, branch/paths/operations, expected base/head, issued/expires, lease state. При смене исполнителя — подтверждённая передача, не самоназначение. Перед записью проверяй scope, expiry, dirty state, конкурирующий writer, ожидаемый HEAD и технический compare-and-set/expected-ref guard. Не force-push и не повторяй unknown write. Неатомарная проверка HEAD/текстовый lease не доказывают технический lock. При недоступном обязательном guard — BLOCKED.
- Выполнение: действительные действия, diff/identities, evidence и отрицательные результаты. Повторно используй прежнюю проверку только при совпадении объекта/bytes, конфигурации, зависимостей, метода, freshness и scope; иначе проверяй delta. Для P0 — actual call path, first side effect, target gate reachability, positive/negative witnesses и независимый oracle/known-bad mutation там, где требует контракт; только в разрешённой изоляции.
- Checkpoint/HANDOFF при смене агента/чата, устойчивом результате, blocker, outage или перед рискованным допуском: цель/scope, permissions, pinned refs, changes, verification evidence, failures/UNKNOWN, ownership и следующий разрешённый шаг. Для полного record используй закреплённые формы ниже; compact record явно перечисляет опущенные секции/immutable annexes. Обновляй существующие STATUS/JOURNAL; не копируй документы.
- Приёмка: non-author проверяет первоисточники, refs/diff, фактические changes, полномочия, ownership, provenance тестов, failures/conflicts и границы. Другой чат/модель не доказывают независимость; саморевью явно обозначай. ACCEPTED только проверенный scope; PARTIALLY_ACCEPTED — отделимая часть; REJECTED/PENDING при соответствующих пробелах. Handoff acceptance не равна TESTED/MERGED/INSTALLED/LIVE_PASS/QUALIFIED/COLD_RESTORE_PASS.
- Разногласие решай evidence и минимальным различающим тестом, не голосованием моделей. Владелец определяет разрешение/риск, а не истинность факта. При отсутствии нового finding/evidence прекращай цикл ревью; P0 не компенсируется баллами.
- Роли: OWNER — человек; AUTHOR/EXECUTOR, non-author REVIEWER, RECEIVER, назначенный INTEGRATOR. Независимость требует доступа к evidence и права отклонить результат; два пересказа одного отчёта не две проверки. Новая версия HANDOFF при смене snapshot, без перезаписи истории. Перед приёмкой повторно разреши moving refs и проверь delta. При expiry или unknown write заморозь scope до независимой сверки. Параллельные writes только в непересекающихся scope/ветвях с назначенным integrator. Не переносить approvals автоматически. Для исполнения отдельно проверить разрешённый runner, границы credentials/mounts/egress, benign canaries по применимому контракту; designated folder/OAuth/Always Ask не OS isolation.
- Outage: восстанови принятый checkpoint и источники, проверь refs/freshness/dirty state, собственные права и ownership; in-flight operation без квитанции — UNKNOWN, не повторять до независимой сверки. Продолжай разрешённую автономную часть; обязательное независимое ревью не заменяй саморевью. При возврате — обратный HANDOFF.
- Закрытие: результат/остаточный риск/решение владельца отдельно, подтверждённое освобождение lease, компактный STATUS/JOURNAL. Без автоматического Merge, deploy, ARM, FINAM, LIVE. Не передавай секреты, реальные account IDs или приватные артефакты.

### Полные формы и долгосрочное восстановление

Не переносить объёмные формы в каждый запрос. Полные формы v1 и требования Recovery перенесены без изменения шаблонов в [приложение](#приложение-c3-полные-формы-и-recovery). Читай его только для полной передачи/приёмки/outage/Recovery. Формы — спецификация, не реализованный валидатор. Полная запись: UTF-8 YAML 1.2 JSON subset, обязательные поля, UNKNOWN с причиной вместо выдуманных значений, уникальные IDs, ISO-8601 offset, проверка типов/ссылок/enum; parse alone не PASS. Не переносить старые результаты как новые. Для автономного пакета все обязательные locators должны разрешаться локально, а не только в GitHub. HANDOFF/ZIP/hash не доказывают cold restore; первый запуск OFF/READONLY/ISOLATED, без автоматической LIVE активации.

Этот раздел — перенос общего рабочего порядка для C3 review, не отказ от действующих safety gates, не доказательство равнозначности всех подробностей Skill. Старые Skill-файлы и зеркала сохраняются в Git history и подтверждённом внешнем экспорте; действующий маршрут — канонические документы.

## G6.4 evidence checkpoint и граница G6.5 — 25.11.2026; исправление G6.5.1

**Pinned SOURCE BASE:** `e05bbd24db88f127a52f0ff1b7282d7c6919cd81` (`main`, независимо разрешён через GitHub при подготовке G6.5).

### Каноническая атрибуция G6.5

| Поле | Исправленное значение |
| --- | --- |
| `CLIENT_ENVIRONMENT` | `KIMI_CHAT` |
| `EXECUTION_CONTEXT` | `AGENT_TOOL_ENABLED_CHAT` |
| `ENVIRONMENT_EVIDENCE` | `OPERATOR_CONFIRMED` |
| `KIMI_WORK` | `NOT_USED` |
| `KIMI_CODE` | `NOT_USED` |
| `GITHUB_PLUGIN_ACCESS` | `READ_WRITE_PASS` |
| `LOCAL_WINDOWS_ACCESS` | `NOT_PERFORMED` |
| `OFFLINE_EXECUTOR` | `NOT_CONFIRMED` |
| `LIVE` | `UNKNOWN` |

GitHub READONLY и разрешённые записи ветки/commit/Draft PR выполнены в Kimi Chat через доступный GitHub plugin. Это не перенос результата на G6.4, Kimi Work, Kimi Code Desktop или Windows checkout.

| Проверка / состояние | Результат и предел применимости |
| --- | --- |
| G6.4 GitHub READONLY | **COMPLETE в заявленном scope**, принято оператором; `G6.4_CLIENT_ENVIRONMENT=UNKNOWN` |
| Независимая сверка GPT | **19/19 Git blob SHA MATCH**; иерархия Control Center корректна по отчёту оператора. Для Kimi — `REPORTED_ONLY`, не новый `PERFORMED_CHECK` всех 19 blob |
| Первое ревью G6.5 | По переданному оператором решению GPT — `PARTIALLY_ACCEPTED`, `MERGE_HOLD` до исправления среды |
| Полный `CODE_EXAM_PASS` | **NOT CONFIRMED**: изолированные code/runtime tests не выполнялись |
| Полный `HANDOFF_PASS` | **NOT CONFIRMED**: требуется повторное GPT-ревью G6.5.1 и решение оператора |
| `COLD_RESTORE` | **NOT TESTED** |

### ENVIRONMENT_ATTRIBUTION_ERROR

- **Причина:** ошибочное отождествление наличия Agent-инструментов с использованием продукта Kimi Work.
- **Последствие:** неправильная атрибуция среды в документации и HANDOFF.
- **Обнаружение:** оператор и GPT.
- **Корректирующая мера:** раздельная фиксация клиента, исполнительного контура, фактически использованных инструментов и полномочий.
- **Запрет:** выводить идентичность исполнительной среды исключительно из наличия Skills, plugins или sandbox.
- **Статус:** `CORRECTION_PENDING_GPT_REVIEW`.

Эта запись подготовлена также для последующего включения в общий журнал недостатков Kimi в PR #597; **PR #597 не изменялся**. Исходный commit G6.5 сохранён, а G6.5.1 добавляет ровно один корректирующий commit в существующий Draft PR #598. Сам факт ветки, commits, Draft PR или зелёного CI не является `CODE_EXAM_PASS`, `HANDOFF_PASS`, Merge, INSTALLED или LIVE_PASS.

Этот checkpoint дополняет, но не закрывает разделы A–C и критерии PASS/FAIL ниже. Датированные `SOURCE HEAD`, `NOT_CONNECTED`, подготовительные Windows SHA и корректные исторические упоминания Work/Code сохранены. См. [индекс Phase II](README.md), [Windows gate](WINDOWS_WORKSPACE_AND_ACCESS.md) и [Roadmap](../../ROADMAP.md).


**OPERATING UPDATE 23.11.2026:** три проекта Kimi и экзамен пока не завершены; два Chat проекта существуют, третий ожидает Pro. Kimi Code авторизован, но GitHub tool reads и offline tests через него **не проверены**. Подтверждённая оператором подготовительная NTFS source-копия: `C:\KimiSandbox\market-pattern-discovery` @ `1413273a1a312802a0ced7a06a4eb73f050d2ec3`; см. [Windows workspace gate](WINDOWS_WORKSPACE_AND_ACCESS.md). Нижеследующий `NOT_CONNECTED` — исторический статус 22.11, не новая диагностика Kimi.


> **SOURCE AUTHORITY CHECK 22.11.2026:** последние принятые GitHub-документы после [Merge #589](https://github.com/alkospacer123/market-pattern-discovery/pull/589) зафиксированы на контрольном `main=41d0b48c1d33db29bc1b19497d558748b3db8fb4`. Указанный ниже `bb8c46c1...` — **воспроизводимый исходный base до #589**, а не всегда актуальный HEAD. Перед чтением и практическим экзаменом перепроверять `main`, Git blobs и [иерархию документов](../DOCUMENTATION_AUTHORITY_2026-11-22.md). Никаких Kimi Chat/Code access, установленного LIVE, FINAM или cold restore не подтверждено.

**SOURCE HEAD:** `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6`. **STATUS: NOT_CONNECTED / NOT_EXAMINED / HANDOFF_NOT_TESTED.** Это спецификация испытания, а не протокол его успешного исполнения.

## A — независимые три проекта Kimi Chat

Для каждого: вопросы, самостоятельные ответы, ссылки на конкретные Git paths, commit и blob SHA, разделение MAIN / INSTALLED / LIVE / RESEARCH / ARCHIVE / UNKNOWN. V20 — R088 и девять патчей, HOLD5, EXT2 OFF; CC — READONLY vs команды, не повторять unknown-result; TRL — выбор 60/30/45 vs исследовательский лидер 75/30/30, внешние ZIP и ложный untouched OOS. Если Kimi не открывал GitHub, пометить SOURCE_NOT_READ.

## B — самостоятельный Kimi Code экзамен

Отдельное подключение к approved GitHub; `git rev-parse HEAD`, `git status --porcelain`, source SHA сверка. Только disposable checkout; без FINAM credentials, локальных LIVE каталогов Intel, установки, kill switch, Task, CC команд, SQLite и broker network. Реальные stdout/stderr, версии Python/Git, exit codes, diff/sha и негативные тесты обязательны; BLOCKED при отсутствии библиотеки или исходного файла.

Три упражнения: (1) V20 исходный R088 base+9-patch stack, offline HOLD5/PREPOST/Protect3 тесты; (2) CC synthetic unknown command result, no retry, read-only tests; (3) TRL R089/R097/R098 и missing original binary proof. Любое утверждение о LIVE из CI = FAIL.

## C — GPT ↔ Kimi реальная совместная задача

После отдельного разрешения оператора Kimi Code создаёт собственную ветку от проверенного main и Draft PR для одной узкой **synthetic test-only или документационной** задачи. Никаких code/runtime изменений без согласованного scope; GPT читает diff, SHA, tests, отмечает замечания; Kimi отвечает и исправляет. Оператор принимает/отклоняет handoff. Автоматического Merge, deploy или LIVE нет.

## PASS / FAIL

PASS только при: независимое чтение трёх проектов, точные источники и правильная иерархия, запущенные изолированные тесты с логами, корректные safety refusals, совместный проверенный Draft PR, подпись оператора. FAIL: выдуманные SHA/результаты, связь исторического T3 с текущим V20 без доказательств, открытие LIVE, токены, повтор broker POST при unknown, неподтверждённый Merge.

## Форма handoff

Дата UTC | Проект | base SHA / branch SHA | допуск оператора | source path/blob SHA | файлы и diff | команды+stdout/exit | PASS/FAIL/SKIP | MAIN/INSTALLED/LIVE границы | открытые вопросы | GPT review | Kimi response | operator decision.

Recovery с реальным cold restore — только **после** завершения этапа Kimi.

## G6.2.3 — историческая documentation integration boundary (25.11; см. актуальный C3 маршрут выше)

Перед критической задачей фиксируй версию/blob [Critical Operations Contract](../CRITICAL_OPERATIONS_CONTRACT.md) и релевантных Skills. Принятие documentation handoff не является Skill installation, TESTED, MERGED, QUALIFIED, LIVE_PASS или COLD_RESTORE_PASS. Отложенные независимые blind испытания G4 обязательны; уже принятые G5 tests заново не разрабатывать. `KDR-001=OPEN`; `G6.2 CRITICAL FAIL` остаётся в истории. Механизм не считается доказанным до независимой приёмки.

**Уточнение 27.11.2026:** абзац выше — историческое свидетельство прежнего экзамена, не текущая очередь или обязательство применять Skills. KDR-001 закрыт владельцем 26.11 в проверенном G6 scope; исторический CRITICAL FAIL сохранён. Для остаточных evidence gaps следовать Roadmap/KDR, не повторять принятые задания. Действующий HANDOFF contract и формы находятся в этом документе.

## Приложение C3: полные формы и Recovery

Перенос канонических форм из `ai-engineering-handoff` v1, blob `d08ccc90065b19a8abff75646b64dd0318688bd9`. Только по необходимости. Шаблоны не являются исполняемыми инструкциями или реализованным валидатором.

Формат UTF-8 YAML 1.2 (JSON-совместимое подмножество: string, number, boolean, map, list; без custom tags, aliases и исполняемых объектов). Ниже три шаблона для заполнения, а не реализованная JSON Schema или доказательство валидатора. Все поля верхнего уровня обязательны для полной записи. Строки-примеры в угловых скобках заменить реальными значениями; не исполнять и не принимать за evidence. Для неизвестного поля используй объект {"status":"UNKNOWN","reason":"конкретная причина"} вместо выдуманных значений; для неизвестного списка используй тот же объект, не пустой список. [] означает проверенное отсутствие, "NONE" — проверенное неприменимое/отсутствующее скалярное значение с обоснованием. Не оставляй null, placeholders, дубли ключей или неразрешённые evidence references. При необходимости компактной передачи укажи явно отсутствующие секции и immutable annexes, не выдавай её за полный record. Используй ISO-8601 с offset, полные идентификаторы и уникальные task/action/evidence IDs. Проверяй parse, types, обязательные поля, enums и ссылочную целостность разрешённым способом; если машинная проверка недоступна — MANUAL_REVIEW/VALIDATION_UNVERIFIED. Не объявляй PASS по одному успешному parse.

### HANDOFF v1

~~~yaml
schema_version: ai-engineering-handoff/v1
handoff_id: "<id>"
version: 1
supersedes: "<previous id/version or NONE>"
created_at: "<ISO-8601>"
created_by: {actor_id: "<id>", role: "<role>", environment: "<sanitized>", session_id: "<nonsecret or NONE>"}
task:
  task_id: "<id>"
  project: "<project>"
  title: "<title>"
  source: "<locator>"
  owner_decision: "<authority locator>"
  objective: "<verifiable>"
  work_status: "<enum>"
  acceptance_criteria: ["<criterion>"]
human_summary: {completed: "<summary>", not_completed: "<summary>", current_risk: "<risk>", next_action: "<action>"}
scope:
  included: ["<scope>"]
  excluded: ["<scope>"]
  account_aliases: []
  forbidden_side_effects: ["<effect>"]
permissions:
  - {operation: "<operation>", decision: "<ALLOWED|FORBIDDEN|REQUIRES_NEW_APPROVAL>", authority: "<locator>", exact_scope: "<scope>", valid_from: "<ISO-8601>", valid_until: "<ISO-8601>", constraints: ["<constraint>"]}
repositories:
  - identity: "<owner/name>"
    main_ref: "<ref>"
    main_commit: "<full SHA>"
    main_observed_at: "<ISO-8601>"
    audited_ref: "<ref>"
    pinned_commit: "<full SHA>"
    snapshot_observed_at: "<ISO-8601>"
    objects: [{path: "<path>", type: "<file/tree/symlink/gitlink/lfs-pointer>", blob_or_object_sha: "<SHA>", locator: "<locator>"}]
    pull_requests: [{number: 1, state: "<OPEN/CLOSED/MERGED>", draft: true, base: "<SHA>", head: "<SHA>", observed_at: "<ISO-8601>", role: "<role>"}]
state_matrix: {SOURCE: "<status+evidence>", DERIVED: "<status+evidence>", INSTALLED: "<status+evidence>", LIVE: "<status+evidence>", RESEARCH_ARCHIVE_RECON: "<status+evidence>"}
ownership:
  owner_authority: "<human decision locator>"
  writer_actor_id: "<id>"
  lease_state: "<enum>"
  write_scope: ["<branch/path/operation>"]
  expected_base: "<SHA>"
  expected_head: "<SHA>"
  issued_at: "<ISO-8601>"
  valid_until: "<ISO-8601>"
  concurrent_write_guard: "<technical evidence or UNKNOWN>"
  parallel_writers: []
  integration_owner: "<id or NONE>"
evidence_registry:
  - {evidence_id: "<EV-id>", type: "<evidence type>", actor_id: "<id>", locator: "<immutable or sanitized locator>", object_identity: "<identity>", observed_at: "<ISO-8601>", operation: "<actual>", limitations: "<limits>"}
actions:
  - {action_id: "<id>", actor_id: "<id>", performed_at: "<ISO-8601>", operation: "<actual>", target: "<identity>", outcome: "<result>", status: "<enum>", evidence: ["<EV-id>"], limitations: "<limits>"}
changed_files:
  - {path: "<path>", change: "<added/modified/deleted/renamed/generated/uncommitted>", base_identity: "<identity>", head_identity: "<identity>", derived_sha256: "<hash>", diff_locator: "<locator>", committed: true, installed_identity: "<separate proof>"}
decisions:
  - {decision_id: "<id>", decision: "<decision>", rationale: "<why>", alternatives_rejected: ["<reason>"], authority: "<locator>", applies_to: "<scope>"}
verifications:
  - {verification_id: "<id>", claim: "<claim>", target_identity: "<identity>", method: "<read/test/replay/review>", environment: "<runner>", configuration: "<identity>", command_or_event: "<sanitized>", executed_at: "<ISO-8601>", exit_or_result: "<result>", stdout_stderr_log: "<locator>", witnesses: ["<witness>"], skips_and_gaps: [], reviewer: "<id or NONE>", evidence: ["<EV-id>"]}
failed_attempts:
  - {attempt_id: "<id>", attempted: "<operation>", observed_result: "<error>", evidence: ["<EV-id>"], why_stopped: "<reason>", unresolved_effect: "<effect>"}
negative_results: ["<rejected hypothesis and evidence>"]
defects:
  - {defect_id: "<id>", severity: "<P0/P1/P2/P3>", observed: "<fact>", expected: "<contract>", evidence: ["<EV-id>"], state: "<OPEN/FIX_PROPOSED/RETEST_REQUIRED/CLOSED>", closure_evidence: ["<EV-id>"]}
conflicts:
  - {conflict_id: "<id>", claim_a: "<claim/source>", claim_b: "<claim/source>", status: "<OPEN/RESOLVED>", resolution_evidence: ["<EV-id>"]}
open_questions: []
blockers:
  - {blocker_id: "<id>", blocked_item: "<item>", reason: "<reason>", required_input_or_permission: "<requirement>", safe_remaining_work: "<work>"}
unknowns: ["<state and reason>"]
rollback_recovery:
  last_known_good: "<identity>"
  preconditions: ["<condition>"]
  rollback_plan: "<locator>"
  state_compatibility: "<status>"
  backup_identities: ["<id+hash>"]
  unknown_write_outcome: "<description or NONE>"
  cold_restore_status: "<status>"
  limitations: ["<limit>"]
checkpoint:
  checkpoint_id: "<id>"
  established_at: "<ISO-8601>"
  snapshot: "<identity>"
  accepted_handoff: "<acceptance id or NONE>"
  confirmed_by: "<actor>"
  confirmed_scope: ["<scope>"]
  evidence: ["<EV-id>"]
  valid_until_or_condition: "<condition>"
  not_proven: ["<claim>"]
next_step:
  action: "<single verifiable action>"
  owner_id: "<writer/receiver actor>"
  preconditions: ["<condition>"]
  required_permission: "<locator or new approval>"
  expected_evidence: "<observable>"
  acceptance_test: "<criterion>"
  stop_conditions: ["<condition>"]
continuity:
  canonical_documents: ["<immutable locator>"]
  adrs_and_journals: ["<locator>"]
  open_task_register: "<locator>"
  recovery_package: "<manifest locator>"
  append_only_addendum: "<locator or NONE>"
resources:
  context_or_quota_state: "<known or UNKNOWN with reason>"
  estimated_remaining_budget: "<known or UNKNOWN with reason>"
  repeated_checks_avoided: ["<check and justification>"]
attachments:
  - {name: "<sanitized>", locator: "<approved>", sha256: "<actually computed hash>", sensitivity: "<public/sanitized/restricted>"}
~~~

### Acceptance v1

~~~yaml
schema_version: ai-engineering-handoff-acceptance/v1
acceptance_id: "<id>"
handoff_id: "<id/version>"
reviewed_at: "<ISO-8601>"
review_status: "<COMPLETE/PARTIAL/BLOCKED>"
decision: "<ACCEPTED/PARTIALLY_ACCEPTED/REJECTED/PENDING>"
reviewer:
  actor_id: "<id>"
  non_author: true
  independence_basis: ["<basis>"]
  independence_limits: ["<limit>"]
review_scope: {included: ["<scope>"], excluded: ["<scope>"]}
snapshot: {previous_main: "<SHA>", rechecked_main: "<SHA>", previous_head: "<SHA>", rechecked_head: "<SHA>", snapshot_changed: false, handling: "<same/focused-recheck/new-review>"}
evidence_registry: [{evidence_id: "<EV-id>", locator: "<locator>", object_identity: "<identity>", observed_at: "<ISO-8601>", operation: "<actual>", limitations: "<limits>"}]
checks:
  - {check_id: "<id>", claim_or_evidence_id: "<id>", operation: "<actual>", result: "<status>", reused_previous_evidence: false, reuse_justification: "<why or NONE>", new_evidence: ["<EV-id>"], limitation: "<limit>"}
repository_comparison: {expected_changes: "<summary>", observed_changes: "<summary>", undisclosed_changes: [], stale_or_duplicate_pr: "<finding or NONE>"}
permission_review: {current_permissions: "<summary>", expired_or_inherited_permissions: "<finding or NONE>", next_step_authorized: false, technical_gates_satisfied: false}
discrepancies: [{severity: "<P0/P1/P2/P3>", discrepancy: "<issue>", evidence: ["<EV-id>"], required_correction: "<correction>"}]
accepted_scope: ["<verified scope>"]
rejected_or_unproven_scope: ["<scope and reason>"]
residual_risks: []
new_blockers: []
required_corrections: []
continuation: {ownership: "<verified or BLOCKED>", checkpoint: "<id or NONE>", next_step: "<action>", stop_conditions: ["<condition>"]}
~~~

ACCEPTED: identity/scope, critical refs, actual changes and necessary claims independently verified; all failed attempts and UNKNOWN disclosed; no hidden critical defect or unknown write in accepted scope; next step safe and authorized or explicitly WAITING_OWNER. Acceptance of an accurate record of a blocker does not authorize the blocked action.
PARTIALLY_ACCEPTED: only separable verified safe scope; list accepted and rejected/unproven claims separately; no execution on rejected scope.
REJECTED: cannot safely use for continuation because of unknown critical identity, incompatible snapshots, unauthorized operations, secrets, hidden unknown outcome, unresolved critical contradiction or missing essential evidence. Rejection of handoff is not proof all claims false. PENDING means review not finished.

### Outage v1

~~~yaml
schema_version: ai-engineering-outage/v1
outage_id: "<id>"
mode: "<GPT_OUTAGE/KIMI_OUTAGE/CODEX_OUTAGE/KIMI_CODE_OUTAGE/OTHER_AGENT_OUTAGE>"
detected_at: "<ISO-8601>"
affected_roles: ["<role>"]
recovery_basis: {last_accepted_handoff: "<id>", last_checkpoint: "<id>", canonical_sources: ["<locator>"], owner_decisions: ["<locator>"], journals_and_adrs: ["<locator>"]}
recovered_state: {task_and_scope: "<summary>", architecture_decisions: ["<decision>"], completed_work: ["<work>"], failed_attempts: ["<attempt>"], open_defects: ["<defect>"], unknowns: ["<state>"]}
freshness_review: {old_main: "<SHA>", current_main: "<SHA>", old_head: "<SHA>", current_head: "<SHA>", historical_live_snapshots: "<NOT_CURRENT or separate evidence>", inflight_unknown_outcomes: ["<operation>"]}
autonomous_authority: {current_owner_permissions: ["<scope>"], expired_or_unconfirmed_permissions: ["<operation>"], ownership: "<confirmed lease or BLOCKED>", forbidden_actions: ["<action>"]}
independent_review: {non_author_available: false, available_evidence: ["<locator>"], self_review_claimed_as_independent: false, deferred_gates: ["<gate>"]}
work_performed: ["<action and evidence>"]
results: {completed: ["<result>"], negative_results: ["<result>"], blocked: ["<item/reason>"], deviations_from_previous_plan: ["<reason>"]}
return_handoff: {handoff_id: "<new id>", checkpoint: "<id or NONE>", next_step: "<action>", owner_decision_required: "<decision or NONE>"}
~~~

### Recovery

Храни канонические контракты, паспорта/source maps, Git history/refs и release identities, ADR, исследования и отрицательные результаты, manifests, тестовые witnesses, handoff/acceptance, task register, recovery runbook и внешние зависимости. Для полного независимого восстановления сохраняй также оригиналы исследовательских входов, Git LFS/внешние артефакты, PR/Issues/CI provenance и доступные логи, необходимые установочные/runtime зависимости, разрешённые конфигурации и инструкции воспроизведения. Не ограничивай backup ссылками на GitHub: manifest должен разрешаться локально. История append-only; датированный PASS/FAIL не переписывай, добавляй erratum. Секреты отдельно у владельца, не в HANDOFF.

HANDOFF не является backup. ZIP, Git mirror, hash или FILES_VERIFIED не доказывают работоспособность. Различай RECOVERY_PLANNED, PACKAGE_VERIFIED, FILES_VERIFIED, ISOLATED_RESTORED, COLD_RESTORE_PASS, RECOVERY_GOLD; ни один автоматически не следует из другого. Для COLD_RESTORE_PASS фактически восстанови все согласованные системы и знания на чистой независимой целевой среде без исходного Intel, основного SSD, GitHub и обеих ИИ-платформ, используя только независимый recovery package и заранее определённые разрешённые локальные зависимости. Зафиксируй фактическую изоляцию, целостность, восстановление Git refs, исходников/данных, зависимостей и конфигурации, необходимые SQLite/ACL/DPAPI recovery ограничения, OFFLINE/READONLY проверки каждого проекта, evidence, независимую приёмку и решение владельца. При недоступной зависимости или неполном scope — PARTIAL/BLOCKED, не полный PASS. Первый запуск OFF/READONLY/ISOLATED; не активируй Tasks, ARM, broker writes или LIVE автоматически. INSTALLED/LIVE и физические брокерские проверки отдельны. Не удаляй прежние копии до подтверждённого восстановления.
