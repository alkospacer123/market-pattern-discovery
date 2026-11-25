# GitHub — проверенное состояние проекта (22.11.2026)

## Checkpoint 25.11.2026 — G6.4 и документационный G6.5

**Актуальный SOURCE BASE для этой ревизии:** `alkospacer123/market-pattern-discovery/main@e05bbd24db88f127a52f0ff1b7282d7c6919cd81`, независимо разрешён через GitHub при подготовке G6.5. Это новый датированный snapshot, а не постоянный HEAD и не свидетельство INSTALLED/LIVE.

- **GitHub READONLY access — PASS** в фактически использованной среде **Kimi Work**.
- **G6.4 — COMPLETE в заявленном scope**, принят оператором.
- По переданному оператором результату независимой сверки GPT: **19/19 Git blob SHA MATCH**, иерархия документации Control Center корректна. Для текущего Kimi Work checkpoint это `REPORTED_ONLY`, а не самостоятельно повторённая сверка 19 blob.
- Полный `CODE_EXAM_PASS` и полный `HANDOFF_PASS` **NOT CONFIRMED**; `OFFLINE_EXECUTOR` **NOT READY / NOT CONFIRMED**; `LIVE=UNKNOWN`; `COLD_RESTORE=NOT_TESTED`.
- G6.5 изменяет только пять разрешённых Markdown-документов через отдельную ветку и Draft PR. До GPT non-author review и решения оператора это не принятый MAIN, не Merge и не полный handoff PASS.

Открытый Draft #597 является отдельной более широкой документационной задачей, не источником принятого MAIN и не дубликатом G6.5. Его пересечение с `ROADMAP.md`, `recovery/kimi/README.md` и `recovery/kimi/WINDOWS_WORKSPACE_AND_ACCESS.md` требует осознанной интеграции владельцем; содержимое #597 не переносится в этот checkpoint как принятое.

Все прежние SHA, таблицы, результаты и статусы ниже сохранены в исходном контексте 22.11. В частности, более раннее «Kimi … NOT VERIFIED / NOT DONE» описывает тот срез и не отменяет принятый G6.4, но также не доказывает Code, executor, INSTALLED или LIVE. Текущий порядок работы уточняют [Roadmap](../ROADMAP.md), [Kimi Phase II](kimi/README.md) и [exam/handoff](kimi/EXAM_AND_HANDOFF.md); другие пункты Roadmap этим checkpoint не закрываются.


**Точка контроля:** `alkospacer123/market-pattern-discovery/main=41d0b48c1d33db29bc1b19497d558748b3db8fb4`, Git tree `5e6aa2a8dee3e30a586d5a0d0204ebd8308a60fc`. Это GitHub API snapshot **до этой документационной ревизии**, а не постоянный HEAD: перед следующими действиями заново проверять `main`. Не путать source MAIN с Intel INSTALLED, текущим LIVE и архивным RESEARCH.

## Принятые изменения и приёмка R7

| Действие | GitHub-свидетельство | Результат |
| --- | --- | --- |
| Генеральная уборка A/B/C, BBW и root legacy | [#583](https://github.com/alkospacer123/market-pattern-discovery/pull/583), [#586](https://github.com/alkospacer123/market-pattern-discovery/pull/586) | 11 594 + 233 исторических Git path выведены из рабочего дерева, Git history сохранена |
| Канонические паспорта и правила | [#585](https://github.com/alkospacer123/market-pattern-discovery/pull/585) | MERGED |
| Статусная документация, R088 Kimi, H1/M15 retained research | [#587](https://github.com/alkospacer123/market-pattern-discovery/pull/587), merge `8a1c6618f8d3c9f33de9de6cb3f6efae13fe29f0` | MERGED |
| Git scanner/checkpoint и offline synthetic tests | [#588](https://github.com/alkospacer123/market-pattern-discovery/pull/588), merge `bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6` | MERGED, 10/10 synthetic PASS; **не автономный Recovery** |
| Три Kimi knowledge dossier и экзамен | [#589](https://github.com/alkospacer123/market-pattern-discovery/pull/589), merge `41d0b48c1d33db29bc1b19497d558748b3db8fb4` | MERGED; exact-head Main Admission SUCCESS, но **Kimi ещё не подключён** |
| Исторические Draft и неудачный audit_only deletion | [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580), [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581), [#590](https://github.com/alkospacer123/market-pattern-discovery/pull/590) | CLOSED WITHOUT MERGE; исходные ветки/коммиты сохранены |
| PR queue на этот срез | GitHub PR search | 0 OPEN |

**Почему 16 файлов `audit_only` остаются:** [акт R7](R7_STAGE_I_FINAL_ACCEPTANCE_20261122.md), [CI 44998434881](https://github.com/alkospacer123/market-pattern-discovery/actions/runs/44998434881). `TradingSystemLab/stage8_robot/signal_execution_diagnostic.py` читает `full_available_raw_signals.csv`, а `stage8_robot/tests/replay_stop_tick_grid.py` использует `audit.py` и CSV. Удаление сделало бы offline H1 replay неполным. Не путать с LIVE V20.

## Сохранённые проектные Git trees на контрольном коммите

| Область | Git tree SHA | Роль |
| --- | --- | --- |
| `V20_TradingSystem_M15/` | `08e4b1ff98f8599f662ee8724c2d11cea03d85d3` | ACTIVE SOURCE, R088; установленная версия может отличаться |
| `ControlCenter/` | `8052938c83a27b2367309052d455d74d9341df09` | ACTIVE operator/UI SOURCE |
| `TradingResearchLab/` | `a5764c5e693f43cbb09469badf26c8dbe3fd3fa9` | RESEARCH, Nov closeout |
| `TradingSystemLab/` | `08722b448d9b14201284e4dab83693e960a290b2` | HISTORICAL H1 + V20 shared library |
| `IntradayLab/` | `d6b686bcdcbd54eca9d1d25c160fecd5bfd82407` | HISTORICAL M15 + V20 shared library |
| `audit_only/` | `6c7a68b7b51b2d272bd66734835cbece3a25d2b9` | H1 offline source/test dependency; KEEP |

Оригиналы в защищённых архивных refs: `archive/pre-r7-cleanup@f15d565755b996252081ed49ed5a094ee1e8d820` и `archive/pre-root-legacy-20261122@09bca5641cb5bb367e84505ebfc6f8c7f35e2620`. Git refs не заменяют независимый backup.

## Иерархия на текущем этапе

[Корневой README](../README.md) → [AGENTS](../AGENTS.md) → [реестр полномочий документов](DOCUMENTATION_AUTHORITY_2026-11-22.md) → [Roadmap](../ROADMAP.md) → один из [паспортов V20/CC/TRL](README.md) → source Git commit/blob SHA, проектный release/closeout. Исторические заметки с `CURRENT` в имени не являются live-monitoring.

- **V20:** выбранная 60/30/45 + TP6 + Protect3 + HOLD5, EXT2 OFF; base в Git + девять патчей. Датированное Intel свидетельство 20.11 `Running/HALTED 3/3`; **текущий** ARMED/FINAM/SLTP = UNKNOWN.
- **CC:** CC-08 / CC-07, UI 127.0.0.1:8502; READONLY refresh ≠ операторские команды. Сведения о фактической установке датированы 20.11.
- **TRL:** решение 60/30/45; 75/30/30 исторически лидировал по Net/PF, но не выбран; оригиналы ZIP/XLSX/OHLCV физически целиком не доказаны.
- **Kimi:** source dossiers [приняты в main](kimi/README.md); реальные три Kimi Chat projects, отдельный Kimi Code, экзамены и handoff **NOT VERIFIED / NOT DONE**.
- **Recovery:** окончательный автономный backup и cold restore **NOT TESTED**. Старый архивный root-тест **45 PASS / 1 known FAIL**, не превращён в PASS; три большие metadata и полный replay внешних consumers не проверены.

**Ранее проверенные состояния/CI сохраняются в Git history:** [точный snapshot после #586](https://github.com/alkospacer123/market-pattern-discovery/blob/4f118ee1cdeced15406136401faabe4fdc3bb847/recovery/REPOSITORY_CURRENT_STATE.md) и [snapshot до #589](https://github.com/alkospacer123/market-pattern-discovery/blob/bb8c46c1db89ca2b5311f22c755bb4e51ce8f7d6/recovery/REPOSITORY_CURRENT_STATE.md). Их old `OPEN DRAFT`, `main=4f...` и PASS относятся только к датированным исходникам; они не должны переопределять таблицу выше.
