# GitHub — проверенный срез 21.11.2026

Источники: GitHub API branch/commit/recursive tree (`truncated=false`), PR #583/#584, PR list, archive tree и ruleset 24745505. **Снимок, не вечный SHA.**

| Область | Факт |
| --- | --- |
| Рабочая база | `market-pattern-discovery/main=e52dd90ef3e85c6ccc3b075f934df3ea8f5ffa8d` перед этим исправительным PR |
| Массовое удаление | #583 merged: 11 491 A/B/C + 103 BBW = 11 594 файлов удалены из рабочего дерева; исходная история и `archive/pre-r7-cleanup` остались |
| Дерево | После #583 — 6 846 Git blobs / 17 корневых папок, но это **не** генеральный перевод в отдельный архив |
| H1 | `TradingSystemLab/` 3 059, из них `results/` 2 508; `stage8_robot` нужен V20 |
| M15 | `IntradayLab/` 2 722, из них `results/` 490 и `t3_m15_*` 1 979; `core` нужен V20 |
| Три основных проекта | V20 446, ControlCenter 163, TRL 168 Git files |
| Корень legacy | `src/` 86, `tests/` 50, `docs/` 34, `audit_only/` 16, plus конфиги, схемы и отчёты — удаление без dependency gate нельзя |
| PR #584 | 21.11 оказался merged с одной строкой README «АКТУАЛИЗИРОВАТЬ ОПИСАНИЕ ПРОЕКТА»; эта новая ветка предлагает содержательную замену, не прямой push |
| GitHub CI | `Protect main` active, обязательный `Main Admission - protected offline baseline` с strict up-to-date, это частичный offline gate, не LIVE |
| Archive | Публичный `market-pattern-archive/main=8d4027c8d53625dfe7780cb7ccfdc354d51b25ba`: 26 файлов, 19 исторических оригиналов, **0/19 blob SHA есть в текущем рабочем main** (проверено дерево 21.11); не полный архив. Draft #5 с 16 STOP/TICK GRID не merged. **Сохранить** до финальной независимой проверки Recovery |

## Открытые PR на момент среза

- [#580](https://github.com/alkospacer123/market-pattern-discovery/pull/580) — подготовка V20 R088 deep-dive и экзамена Kimi, обновить относительно нового main перед Merge; уникальная информация сохраняется.
- [#581](https://github.com/alkospacer123/market-pattern-discovery/pull/581) — устаревший roadmap R7, **но уникальные офлайн инструменты**; без проверки не закрывать/не терять.
- [#582](https://github.com/alkospacer123/market-pattern-discovery/pull/582) — **закрыт без Merge 21.11**, сохранив ветку и исходный двухфайловый исторический снимок; это не текущая инструкция.

## Не подтверждено

Ни ненужность оставшихся 6 846 файлов, ни отсутствие всех legacy dependencies, ни полнота независимого GitHub metadata/TRL originals/ZIP/XLSX; Kimi Code экзамен и cold restore не проведены. GitHub не показывает свежий физический FINAM/ARMED/SLTP. Сохранять сомнительные файлы; для удаления отдельный доказательный gate и санкция.
