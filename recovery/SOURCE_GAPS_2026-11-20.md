# Источники истины, SHA и пробелы — 20.11.2026

**Main на момент проверки:** `e6b8480b493365e0a4ff2bb56041891fde0a6f22` в `alkospacer123/market-pattern-discovery`. GitHub не подтверждает установленную Intel-сборку или LIVE.

| Источник в main | Git blob SHA | Назначение |
|---|---|---|
| `V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md` | `d61b0ac5b30ff706534f4b5c65e523705aa04d3b` | Установленный R088 по паспорту, 9 патчей, Running/HALTED, незакрытая проверка Protect3 |
| `V20_TradingSystem_M15/README.md` | `bfbf8144465907427f53adf05d1fa0f89cfb87b3` | Навигация; нижние старые разделы исторические |
| `TradingResearchLab/STATUS.md` | `4c31d8268f66800aeda123c311af69ce3efcaf8a` | Текущее исследовательское решение 60/30/45, HOLD_DATA для финансовых показателей без отчётов |
| `TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md` | `3c0dd263e21d68cb07bf5a2df2a2a919fa3418b5` | Точка входа в TRL |
| `TradingResearchLab/reports/TRL-NOV-2026-FINAL-CLOSEOUT.md` | `ec06839fd233f9909eead53e82b9b7d1d7868fb8` | Финальное решение после R097/R098 |
| `TradingResearchLab/reports/TRL-NOV-2026-ARTIFACT-MANIFEST.md` | `9c56376e087ce40bfd070fcf8056bd81f3ce44c4` | Внешние воспроизводимые ZIP/XLSX |
| `ControlCenter/README.md` | `707080ee4daf1b2cf3a754c078a67e78f6612aae` | V20 текущий верхний раздел, CC03/H1 ниже — ARCHIVE; установленный UI/adapter/operator уже сверены по Git blob 3/3 |

**Исследовательские оригиналы вне GitHub:** R060 ZIP `80291246ba4692485545f58fd28c7563199bf7be28033fc16eb296efee377e31`; R097 ZIP `081fa855e4ffa44b76956863a3c53179d126dd2e93083b988301009d7b35f4f4`; R097 XLSX `f8af967b9149cd84587024d3315a86ed00852de285ccd5b6d491ecf9c88`; калькулятор 60/30/45 XLSX `0f13b097b45f8bd2a86301bab1ca2c92ef4462ddf9cb05c79373affeba0f39c3`. Наличие исходных файлов в доступной среде сейчас не проверено.

**Recovery originals:** 02.11 ZIP SHA256 `c2d4d935d41405528cfa28033951e5cfefb65c5130997e4455fc643faab2dca5`; 09.11 ZIP `b98f80f35ccee6f0716786142c05870f97d9f459221b6b5a314e6883f4aaeaf8`; Git mirror 09.11 ZIP `9e5d490410f7fbe3ddab983d557b981eb96146f2e5c023e42b2a1d0ee9fd0754`. Прежние SHA/SSD PASS, **cold restore NOT_TESTED**.

**Gaps:** fresh FINAM/ARMED/SLTP/Protect3 evidence; CC функциональный UI/Tasks и broker truth (installed Git blob MATCH 3/3 уже проверен); полные экспорты чатов; оригиналы TRL ZIP/XLSX; полный архив PR/Issues/CI и 10 старых Draft; независимый зашифрованный offsite и реальное изолированное восстановление. Не объявлять PASS без доказательств.

## Проверенные дополнения 20.11 после исходного реестра

- **V20:** только локальный READONLY check 15:27 МСК Running/HALTED 3/3, HEALTH_PARTIAL; состояние FINAM/SLTP/ARMED остаётся UNKNOWN. [Доказательства](RECOVERY_STATE_POST_CLOSURE_2026-11-20.md).
- **CC:** HTTP 200 на 127.0.0.1:8502 и физический Git blob MATCH 3/3: operator `10de325be0335733a248c412943f39d45bd93c62`, adapter `ef2fa2cd6b0ddfefc920548995274f123c5884bf`, UI `9b9b0f0cf3cba4fbe3203286f793a5a0f8ec5e6c`. SHA256 и пути в датированном срезе; не утверждать FINAM PASS.
- **GitHub:** 10 исторических PR закрыты без Merge, их ветки сохранены, HEAD SHA в проверенном mirror 09.11 с архивными refs. #571 остаётся OPEN/DRAFT; текущий `main` Discovery `e6b8480b493365e0a4ff2bb56041891fde0a6f22`.
- **Удалённый repo:** `market-pattern-autonomous-engine` удалён владельцем; 404 подтверждён, отдельный проверенный архив истории отсутствует.
- **Защита:** старый Discovery mirror из ZIP 09.11 проверен `fsck=0`, 41 047 объектов, 1 163 refs, исходный `main=0881d1e08b51a564fb54bb7d334d1578fc130400`. Новый Data mirror от 20.11 `fsck=0`, 8 refs. ZIP текущего Discovery `main` скачан оператором, но SHA256/путь и независимый SSD снимок не проверены; Git clone/fetch текущего Discovery неоднократно терпели HTTPS timeout. Это **не** полный защитный PASS.
- **TRL:** существующие SHA256 R060/R097 указаны выше как ожидаемые, не как новая физическая проверка оригинальных архивов. Полный архив PR/Issues/CI, Kimi Code доступы и R6 cold restore остаются PENDING.
