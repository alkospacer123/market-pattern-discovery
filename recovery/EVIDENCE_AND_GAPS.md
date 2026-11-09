# Evidence ledger — доказательства и ограничения восстановления

## Иерархия доказательств
1. Сверенный код/commit и checked installed hash; полный runtime witness с временем и ограничениями.
2. FINAM/broker account state и независимое подтверждение операций; только в защищённом операторском контуре.
3. Подписанные или SHA256 проверенные отчёты/SQLite snapshots/CI и журналы инцидентов.
4. Датированные пользовательские выводы и согласованные решения в разговорах.
5. Реконструкция/анализ без оригинала: **RECON**, никогда не выдавать за первичный журнал.

## Известные источники
- [PR #567](https://github.com/alkospacer123/market-pattern-discovery/pull/567): разработка, V20-08 и late fixes; проверить head при продолжении.
- [PR #568](https://github.com/alkospacer123/market-pattern-discovery/pull/568): ControlCenter CC-V20; проверить физически installed vs PR.
- [TRL source index](../TradingResearchLab/STATUS.md), [closeout](../TradingResearchLab/reports/TRL-00-CLOSEOUT-2026-10-31.md), [V1–V24 registry](../TradingResearchLab/reports/TRL-00-V1-V24-REGISTRY-2026-10-31.md).
- [V20 methodology](../V20_TradingSystem_M15/V20-03/comparison/METHODOLOGY_EFFECTS_RU.md), [PF](../V20_TradingSystem_M15/V20-03/comparison/PF_DIAGNOSTIC_REPORT_RU.md), [roadmap](../V20_TradingSystem_M15/docs/ROADMAP_RU.md).
- SSD Recovery-BASE 02.11: original SHA256 `c2d4d935d41405528cfa28033951e5cfefb65c5130997e4455fc643faab2dca5`; 27,589 files; 64 snapshots; hash PASS.
- Новый Recovery v3 09.11: `RECOVERY-BASE-V20-CC-20261109-153322.zip`; SHA256 `b98f80f35ccee6f0716786142c05870f97d9f459221b6b5a314e6883f4aaeaf8`; 27,645 files, SQLite snapshots 78; issues 0, outer ZIP CRC/file SHA/SQLite snapshot SHA = PASS; **копия на SSD подтверждена: `ssd_copy_verified=pass`; cold restore не подтверждён**. Пользовательские backup report/сырые журналы — приватные артефакты, не размещать в публичном репозитории.

## Открытые пробелы (нельзя заполнять догадками)
- Полный дословный архив ChatGPT не получен; повторный запрос экспорта в работе на 09.11. Иные чаты, контекст и скрытые ветки могут не отражаться в документах.
- Несколько V20 fixes и CC updates после 02.11 требуют нового архивного снимка PASS, установленного hash/CI/FINAM reconciliation. Последнее локальное состояние 09.11 устаревает сразу после следующего цикла.
- На `main` V20/CC README устарели по фактическому процессу, так как поздние изменения в Draft PR/Intel; проверять HEAD, pinned blob SHA и installed hash.
- `C:\V20Lab\source` shallow=true. Один ZIP репозитория или копия shallow `.git` не содержит полной Git-истории. На 09.11 два независимых полноисторических GitHub mirrors на Intel **созданы и `git fsck` PASS**; их упаковка/SSD-хэш ещё не подтверждены. Git LFS, PR/Issues/CI вложения отдельно.
- TRL financial READONLY trade ledger отсутствует/не подтверждён, V1–V24 provenance partial; истории H1/M15 125 ГБ **вне текущего архивирования**.
- Восстановление Windows/FINAM/DPAPI/Task/CC-07 на новом ПК **не испытано**; статус CAPTURED_NOT_RESTORE_TESTED.
- Гипотезы ATR и limit-entry, квалификация инвестора/КПУР, альтернативы ГО — не принятые LIVE улучшения.

## Правило обновления
После новых свидетельств добавлять ссылку, временную метку, SHA, команду / тест, PASS/FAIL/PARTIAL/UNKNOWN и разницу с прежним состоянием. Не удалять прежние свидетельства или неопределённость без причины.
