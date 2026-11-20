# TRL — аудит готовности исследовательских Draft PR к Merge

**Дата:** 20.11.2026. **Финальный статус:** `MERGED_4_OF_4 / MAIN_CONTENT_VERIFIED / NO_CI_EVIDENCE / LIVE_UNCHANGED`. **Таблицы подготовки ниже — исторический снимок ДО Merge; фактические исходы см. внизу.**
**Репозиторий:** `alkospacer123/market-pattern-discovery`, target `main`; публичный репозиторий.
**Проверка:** чтение реальных PR, изменённых файлов, GitHub mergeability и доступных Commit Status/Workflow Runs/Reviews; эвристический поиск секретов по diff. **Нет** запуска Python-тестов, независимого повторного cash-replay или полного security-аудита.

| PR | Состав | Base | Scope | Mergeable (20.11) | Status |
|---|---|---|---|---|---|
| [#570](https://github.com/alkospacer123/market-pattern-discovery/pull/570) | Календарь и ноябрьский STATUS, 11 файлов | main | Только `TradingResearchLab/` | true | Draft |
| [#572](https://github.com/alkospacer123/market-pattern-discovery/pull/572) | STS R039–R055, 62 файла, в т.ч. offline Python | main | Только `TradingResearchLab/` | true | Draft |
| [#573](https://github.com/alkospacer123/market-pattern-discovery/pull/573) | V20 R051–R080, 54 файла | main | Только `TradingResearchLab/` | true | Draft |
| [#576](https://github.com/alkospacer123/market-pattern-discovery/pull/576) | Финальное решение ноября, R086/R089/R097/R098, Journal, Kimi index | main | Только `TradingResearchLab/` | true | Draft |

### Зафиксированные проверки
- После исключения конкурирующего изменения корневого `TradingResearchLab/README.md` из #572 **нет пересекающихся путей** между парами #570/#572/#573/#576 (на момент проверки).
- Во всех PR только пути `TradingResearchLab/`; бинарных diff и файлов LIVE/FINAM/SQLite/Windows Tasks нет.
- На добавленных строках diff **0 совпадений** с базовыми шаблонами GitHub token / private-key / явных password-secret assignment. Это **не** полный security-аудит.
- GitHub показывает `mergeable=true` для каждого отдельного PR против текущего `main`. **Последовательное слияние может изменить картину:** после каждого Merge обязательно заново проверить следующий PR.
- **Commit Statuses = 0, PR Workflow Runs = 0, Reviews = 0** на проверенных вершинах. Отсутствие CI означает **NOT_TESTED**, а не PASS. Для offline Python в #572 перед Merge обязателен отдельный запуск синтаксической проверки/тестов в разрешённой изолированной среде.
- #570 и #573 явно связывают исторический Nov 12 обзор с финальным #576; #572 обозначает STS как исторический `NO_CORE_REPLACEMENT`.
- #576 показывает конфликт первоначального условного решения R098 и **последующего итогового выбора владельца**: 60/30/45 для всех рассматриваемых масштабов вместо 75/30/30, при неизменных фактах R097.

### Предпочтительный безопасный порядок
1. Review #570, при отсутствии дополнительных изменений подготовить и Merge.
2. Перепроверить `mergeable` #572; выполнить offline проверки Python, затем Review/Merge.
3. Перепроверить #573; документационный Review/Merge.
4. Перепроверить #576; проверить ссылки из README/STATUS и исходные SHA, Review/Merge.
5. После всех Merge провести контроль `main` на актуальный decision trail и исправность ссылок; отдельно подготовить Kimi доступ к **воспроизводимым исходным ZIP/XLSX**, которые **не находятся** в этих PR.

### Вне исследования TRL
**#571 Recovery** содержит состояние на 09.11 и требует отдельного ревью актуальности/конфиденциальности; **#574/#575** имеют нетривиальную цепочку базовых веток V20 и меняют код, поэтому **не включены в TRL Merge GO**.

**Решение:** `CONDITIONAL_GO_FOR_DOCUMENTATION_REVIEW`. PR можно обсуждать и готовить к Merge; не интерпретировать эту запись как одобрение автоматического объединения или LIVE-деплоя.

## Сверка цепочки Merge #570, #572, #573, #576 (20.11.2026)

| PR | Состояние после проверки | Squash merge commit |
|---|---|---|
| #570 | **MERGED** | `f5e28064bc9e6a018292c3b67e8e90e577d59016` |
| #572 | **MERGED** | `95d0f9d1ae358079106907beb550ef12b5ce33ef` |
| #573 | **MERGED** | `5e02b27dc6764e9e165867831d4231ecaaef281c` |
| #576 | **MERGED** | `324e107bd2c9d76c483f920b6786889b84553a3d` |

**Контроль после #573:** `main` содержит действующий `TradingResearchLab/README.md`, `STATUS.md`, архив STS с `NO_CORE_REPLACEMENT` и явно устаревший interim V20 Nov 12. Путь для итогового индекса Kimi появится в `main` при Merge #576.

**Воспроизводимые первоисточники:** локально в исследовательском окружении проверены SHA256 у R060, R097, R097 XLSX, Excel-калькулятора и ноябрьского ZIP closeout (все совпали с `TRL-NOV-2026-ARTIFACT-MANIFEST.md`); ZIP R060 (38 записей), R097 (17) и ноябрьский closeout (8) прошли CRC. **Но** GitHub не содержит исходных бинарных архивов; для воспроизведения Kimi потребуется отдельно авторизованный доступ к этим файлам.

**Ограничение проверок исходников STS:** статически просмотрены `run_r043.py`, `audit_r043.py`, `run_r047.py`, `audit_r047.py`, `sts_exp_001_replay.py` — они не обращаются к брокерскому API в проверенных участках, но требуют локальных зависимостей R038/R039/R041/R042 и архивных данных; эти offline-тесты в данной процедуре **не запускались**. Не приравнивать отсутствие CI к успешному прогону.

**Безопасность:** 0 совпадений типовых паттернов токенов/приватных ключей в добавлениях four PR; это лишь regex-скан, не полная сертификация безопасности. Все изменённые пути были ограничены `TradingResearchLab/`; LIVE-код и исполнительные задания не менялись.

### Фактическая post-merge проверка main

Все PR [#570](https://github.com/alkospacer123/market-pattern-discovery/pull/570), [#572](https://github.com/alkospacer123/market-pattern-discovery/pull/572), [#573](https://github.com/alkospacer123/market-pattern-discovery/pull/573), [#576](https://github.com/alkospacer123/market-pattern-discovery/pull/576) имеют GitHub `state=closed`, `merged=true`, `draft=false`. `main` содержит `TradingResearchLab/README.md`, `STATUS.md`, `TRL_Roadmap_1_1.md`, архив STS, отчёт Nov 12 с оговоркой о промежуточном статусе, оригинальный R089, R097, журнал, Kimi Start Here и SHA-реестр артефактов. После завершения цепочки проверена доступность этих файлов из `main`.

Никаких файлов V20 LIVE и Control Center перечисленные PR не изменяли; PR #571/#574/#575 вне этой цепочки. Архивные STS Python-скрипты не были запущены из-за отсутствующих внешних исходных зависимостей; это **явная незакрытая проверка**, а не PASS. Издержки, GO proxies и TRUE OOS для R097 остаются прежними ограничениями исследований. Для Kimi требуется **отдельно предоставить оригинальные ZIP/XLSX с SHA256**, а не рассчитывать на один репозиторий.

**Исследовательские материалы объединены; готовность к полноценной автономной перепроверке архивов Kimi = HOLD_EXTERNAL_ARTIFACTS, пока бинарные источники не доступны.**
