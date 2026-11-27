# Trading Systems — Recovery & Migration — инженерный журнал

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

### 27.11.2026 — решение о преемственности и консолидации

Владелец согласовал отдельные рабочие статусы и инженерные журналы V20, CC, TRL и Recovery; профильные чаты заполняют их по первоисточникам. TRL использует существующие STATUS.md и journal/. Согласована финальная уборка MAIN в C3: актуализация, проверка зависимостей, устранение дубликатов и ненужных исторических материалов с сохранением provenance. Scope этой записи: документальное решение, не полный допуск Kimi и не разрешение на удаления, Merge или LIVE. Следующий шаг: завершить C2, затем C3 по Roadmap. Доказательство публикации — текущий Draft #608; факт Merge проверяется отдельно.

### 27.11.2026 — C2 закрыт по решению владельца

GPT / GitHub documentation. Владелец отменил E6A/E6B Code High/Max и дальнейшие ресурсные прогоны; SKIPPED_BY_OWNER, не PASS. High штатно, Max для сложных задач; оставить только необходимые Skills/plugins. Результаты и пределы измерений — [Roadmap, C2](../ROADMAP.md#c2-ресурсная-оптимизация--closed_owner_20261127-не-g9-pass). Точная экономия не установлена. Следующий шаг — C3: очистить GitHub до обновления знаний Kimi. Настройки и LIVE не изменены; удаления, Merge и полный допуск остаются отдельными решениями.

### 27.11.2026 — C3.1 общий перенос, CI blocker

GPT / GitHub documentation. Владелец принял начало C3.1 в существующем #608. Pinned MAIN 373d7aea7cba69fa1f01c4378b06488554e788f7, предыдущий HEAD 95637f5bea33a93b856d5aea9565538712d3ad99. Полное tree (6743 blobs), 29 идентичных копий в memory/ (553869 bytes); все пять canonical Skills прочитаны по структуре, два общих — по содержанию. В существующие AGENTS и EXAM_AND_HANDOFF внесён компактный кандидат общего протокола; прежние подробные формы закреплены immutable locator. README и memory/README фиксируют переход, не заменяют текущий fallback. Ни одного файла не удалено. [CC CI job](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45950091294/job/140343688541): CC_SEALED_SOURCE_OR_HISTORICAL_DOC_CHANGED для ControlCenter/STATUS.md и JOURNAL.md, Main Admission PASS, R7 SKIPPED на предыдущем HEAD. CI policy не изменена. Следующее: профильная сверка, точный CI scope, доказанный fallback и отдельное решение об удалении/Merge. INSTALLED/LIVE не проверялись, Intel/FINAM и настройки не затронуты.

### 27.11.2026 — C3.2 профильные HANDOFF, координационная реконструкция

Получены три профильных отчёта и STATUS/JOURNAL CC; оригинальные patches недоступны. MAIN `2ac85eb5bcdd8757144898b5a27369329f4d125c`, исходный HEAD #608 `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e` (CI CC docs/Main Admission PASS, R7 SKIP; Windows native SKIP на docs-only). [#609](https://github.com/alkospacer123/market-pattern-discovery/pull/609) MERGED. В пределах разрешённого CI scope реконструированы статусы/журналы V20 и CC, V20 AGENTS/Start Here, COC entry safeguards; профильные оригиналы не выдаются за применённые patch bytes. Остались CC diagnostics, TRL и общий transition fallback/manifest. Skills, mirrors, runtime, Intel, FINAM, LIVE не изменены. Отдельный допуск удаления/Merge сохраняется.

### 27.11.2026 — C3.2 второй профильный пакет

GPT / GitHub documentation. Исходный HEAD 86a5731f64e039c52c8c296a9dffedab44e161d1: CC docs/Main Admission SUCCESS, R7 SKIP. По original HANDOFF реконструированы CC diagnostic regression classes и #602 addendum, TRL method/roles/card/Start Here/STATUS/Journal. [Commit](https://github.com/alkospacer123/market-pattern-discovery/commit/8da47cca39adfda0b46955b2776717b67f4d39ec): девять изменений существующих файлов, одна запись в существующем TRL journal; relative path check PASS, CI нового HEAD не подтверждён. 29/29 mirror blob identities соответствуют manifest, 25 текущим originals, 4 TRL копии точно соответствуют прежнему accepted MAIN 2ac85eb5bcdd8757144898b5a27369329f4d125c, total 553869 bytes. Не выдавать historical backup за текущий канон. Шесть дополнительных exact CI paths (CC два V20 docs; TRL STATUS, OPERATING_CYCLE, research/RESEARCH_CARD_TEMPLATE, journal/2026-11-27-trl-knowledge-consolidation). Профильный перенос подготовлен; global routing, KDR reconciliation, dependency/export/fallback review, CI и owner deletion decision остаются. Ни одного удаления, install/Skill settings или LIVE action.

### 27.11.2026 — C3 общая маршрутизация и authority reconciliation

GPT / GitHub docs. MAIN `2ac85eb5bcdd8757144898b5a27369329f4d125c`, исходный HEAD #608 `f723a4f172b1df62696a60f5ff66112cac9d5643`: Main Admission PASS, CC docs FAIL с шестью ранее известными отсутствующими путями allowlist (run 45955591360), R7 SKIP. Сокращены 3 паспорта и 3 профиля (19294 → 9523 символов; полные прежние версии на принятом MAIN). Общий AGENTS, COC rc.2 candidate, HANDOFF, README, TRL AGENTS, CC source map, Windows scope согласованы. KDR-001 закрыт владельцем 26.11, старый CRITICAL FAIL сохранён. Backup bytes не изменены: 11 исторических pins, 18 current. C3 migration не принята, Skills по-прежнему обязательны по релевантности, all-three fallback/export и итоговый CI scope pending. Ни одного удаления, Merge, Intel/FINAM/LIVE или settings change.

## 27.11.2026 — C3.2: цель без собственных Skills

- Владелец согласовал целевую архитектуру без пяти активных собственных Skills, при сохранении необходимых требований и безопасного fallback. Не разрешение на удаление/Merge/отключение или LIVE.
- #610 MERGED `807d765fab2eb923f4b745caeafa11a27ef6fc53`; #608 синхронизирован `8d5ac184eb9ea74770b3a9c3afea9e9204bb7240`, CC docs/Main Admission SUCCESS, R7 SKIPPED ([CC CI](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45958387127), [Main CI](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45958387130)). Входной документационный diff 42 файла, новые изменения не наследуют этот CI.
- Перенос оставшихся требований в существующие AGENTS/COC/HANDOFF/V20/CC/TRL; три полные формы HANDOFF/acceptance/outage v1 перенесены из Skill без изменения шаблонов. ML-запрет сохранён в прежнем scope, дальнейшее изменение только отдельным решением. Это статический перенос, не доказанное полное покрытие или executed test.
- Следующий шаг: независимая сверка покрытия и ссылок, обновлённый pinned export, all-three fallback, отдельное разрешение на удаление зеркал/Skill retirement и Merge. Ни одного удаления, настройки и LIVE не изменены.

## 27.11.2026 — C3 READONLY fallback review

- Kimi Code, отчёт владельца: export `C3_Knowledge_Export_143dd141.zip` SHA256 `3aac03bef77ff5f394263f7a70bceed04adb165364a81b5ad19be18c06f7ef8e`, candidate HEAD `143dd141aa6566a5fd119b8804e5dfb9d6cbba0d`. 60/60 manifest identities, ZIP CRC PASS; 44 canonical non-Skill docs read; five Skills not loaded/read as text (reported). V20/CC context PASS, TRL/general PARTIAL; no LIVE or qualification claim. 416 relative links checked, 92 unique missing targets in ZIP, all present in local pinned commit (reported). Checkout HEAD `373d7aea7cba69fa1f01c4378b06488554e788f7` unchanged; PINNED_OFFLINE, not MAIN. GPT independently confirmed 9 missing required paths/blob identities on exact Draft. Earlier audit count 91 used different scope; no claim of full link closure.
- Nine export additions required: root README, recovery REPOSITORY_CURRENT_STATE, TRL README/Roadmap 1.1/2027 calendar, research registry/negative index, MANUAL_FINAM_MONTHLY_INPUT, V20_READONLY_SOURCE_REQUIREMENTS. All canonical; no new repo docs. Preserve local Git object fallback for other task-specific sources.
- GPT review found remaining WF/TRUE OOS/replay specifics from TRL Skill; migrated into existing methodology, no new research requirement; ML erratum appended in existing TRL journal. CI for incoming HEAD Main Admission/CC SUCCESS, R7 SKIP; new HEAD needs own CI. Do not repeat full Kimi task. Remaining: coverage/references/retirement scope, final verified export and owner decision. No deletion, installed Skills/settings or LIVE change. KDR not closed automatically.

## 27.11.2026 — Erratum: приоритет решения владельца над историческим Skill

- Владелец указал на противоречие согласованной методике от 26.11. GPT ошибочно перенёс избыточные формализованные WF/TRUE OOS/replay требования в `5e8390dceef1e05827490ac2ed6dab194f021f39`. Восстановлена точная редакция Research Methodology из `143dd141aa6566a5fd119b8804e5dfb9d6cbba0d`. Никаких новых обязательных исследований или повторных расчётов. Прежняя запись о переносе — историческая, не действующее правило. READONLY результат Kimi и девять недостающих путей остаются в силе. При дальнейшей консолидации переносить только необходимые актуальные требования, не каждое правило старого Skill. MAIN, runtime и LIVE не затронуты.

## 27.11.2026 — C3 exact cleanup и подтверждение внешнего экспорта

- Владелец разрешил #611 Merge и exact cleanup 34 files в #608 после сохранения архива и исправления ссылок; отдельно подтвердил сохранение ZIP на внешнем SSD и разрешил #612 Merge. #611 MERGED `fa06e79faecb6ece7b39c8375841a33a623446ca`; #612 MERGED `85791944750d096ae7d6a86a0e2f40df8f74d80c`. #608 sync `e5bc5441816794004be860a574b62b30c042873e` сохраняет прежний diff 42 files. Финальный Merge #608 не разрешён.
- Export #611 CI [run 45962701886](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/45962701886): 53 current + 16 historical, 69/69 identities; owner-held `C3_final_candidate_45962701886.zip`, SHA256 `3aa88b095b246d42ea591917a8bcb99b3e98b403a0de65432b3c7630d20d7344`. 29 mirror original pins и пять Skills verified Git trees; 9 missing mandatory docs added. CC native 775 pass/15 skip, 56 V20 targeted на HEAD #611, не на #608 и не LIVE. Компактный экспорт не full dependency closure.
- Exact retirement candidate: 29 mirrors + five canonical Skill sources, seven navigation indexes retained and converted to current canonical routes + historical inventory. Active links and former Skill requirements transitioned; historical COC manifest remains unchanged. Old Skill bytes in Git history/verified export. No research methodology changes, no production code, no installed settings, no LIVE. New CI/diff must be verified; no FULL_PARITY or COLD_RESTORE claim.

## 27.11.2026 — C3.3.5: переход от учебной копии к штатной инженерной среде

- Владелец подтвердил C3.3.1–4 (инструкции, вложения, память, Skills/plugins) и изменил назначение `C:\KimiSandbox`: временный учебный checkout, не обязательная постоянная копия. C3.2 baseline после Merge #608: `24cc424abebd1abfca7e93ad1a72191d6a02f5b7`. Настройки owner-reported; не новый независимый тест.
- Решение: Kimi Code исполняет согласованные инженерные операции вместо ручного исполнения владельцем; существующие системы и каталоги сохраняются. Текущая политика в [Windows workspace](kimi/WINDOWS_WORKSPACE_AND_ACCESS.md). C3.3.5 — READONLY инвентаризация и проверка canonical access; удаление только после сохранения уникальной работы/истории, доказанного fallback и отдельного разрешения. C3.4 gates, COC, Always Ask, отдельные approvals на production/deploy/ARM/HALT неизменны.
- Документационная коррекция предложена в отдельной ветке; не подтверждает локальные проверки, удаление учебной копии, расширение полномочий или LIVE. Не запускать повторный учебный экзамен.

## 27.11.2026 — C3.3.5 inventory and C3.4 partial evidence

- Owner-relayed Kimi Code inventory: clean training checkout, no unpublished work found, 3375/3375 unreachable commits covered by remote refs; exhaustive tree/blob check UNKNOWN. GPT independently matched MAIN `be957ba60e6875cc68c54be7b27b77cdb039cc96` and four source blobs. Owner clarified TRL is independent of historical H1/M15; leave both historical roots as-is, no additional cleanup.
- Owner configured separate Code projects V20/CC. V20 pwd + knowledge fallback reported PASS; Separate CC workspace/read check reported PASS (`cc/__init__.py`, `cc/ui.py`), no writes/execution or FINAM. Owner copied C3 ZIP to C:\\TradingSystemsRecovery, GPT independently checked uploaded outer/inner ZIP CRC and 69/69 manifest identity; Code reported matching SHA and reading all three passports/STATUS without GitHub or sandbox. Dated candidate, not full cold restore.
- KDR-002 candidate correction; KDR-003/004/005/006–011 evidence/status reconciled in existing register; no broad repeat qualification, no automatic KDR closure. Await remaining evidence and explicit owner decisions. No deletion, settings change, runtime code change or LIVE authorization in this documentation candidate.
