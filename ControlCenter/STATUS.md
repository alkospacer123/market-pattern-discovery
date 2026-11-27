# Control Center — рабочий статус

[Паспорт](../recovery/PROJECT_PASSPORT_CONTROL_CENTER.md) · [SOURCE map](docs/V20_START_HERE_SOURCE_MAP.md) · [CC-07](docs/V20_CC07_COMMAND_CONTRACT.md) · [CC-08](docs/V20_CC08_OPERATIONS.md) · [Данные и тесты](docs/V20_DATA_SECURITY_TESTS.md) · [Журнал](JOURNAL.md) · [COC](../recovery/CRITICAL_OPERATIONS_CONTRACT.md)

**Post-G9 — SOURCE-аудит и независимое статическое ревью завершены; operator readiness FAIL / INSTALLED UNKNOWN / LIVE UNKNOWN.** Владелец 27.11.2026 утвердил `FULL_PARITY_OWNER_ADMITTED` для V20/CC/TRL; этап II принят в документированных пределах. [Roadmap](../ROADMAP.md), [Recovery STATUS](../recovery/STATUS.md), [KDR](../recovery/kimi/KIMI_DEFECTS_AND_REMEDIATION_REGISTER.md). #614 MERGED; итоговый документационный closeout — #615. Допуск не является разрешением на конкретные критические операции.

Исторический профильный GitHub READONLY срез (UTC+03): MAIN `2ac85eb5bcdd8757144898b5a27369329f4d125c`; исходный [Draft #608](https://github.com/alkospacer123/market-pattern-discovery/pull/608) HEAD `f6c28ad4027fdc1fdfc8c279671f5c3001f3bd1e`. Не свежая проверка Intel/FINAM.

**SOURCE:** Streamlit `v20_app.py`, три робота. READONLY: gate → pinned exporter → CC-owned snapshots → receiver/ACL/schema/TTL → UI. CC-07 отдельно: UI → adapter → pinned PowerShell/stock V20 operator, confirmations, broker-FLAT gates, SID/SHA, audit/postflight. Staged gateway и H1/CC-03/8501 не считать действующей веткой. HEALTHY локального снимка не доказывает FINAM FLAT/SLTP; UNKNOWN не 0.

**MAIN:** [#602](https://github.com/alkospacer123/market-pattern-discovery/pull/602) MERGED 26.11, fail-closed HEALTHY/exposure (synthetic/offline, не LIVE); [#603](https://github.com/alkospacer123/market-pattern-discovery/pull/603) MERGED, frozen CC-03 и active V20 CI раздельны; [#609](https://github.com/alkospacer123/market-pattern-discovery/pull/609) MERGED, точный C3 scope. Предыдущий #608 HEAD: CC docs/Main Admission PASS, Windows native SKIPPED.

**INSTALLED:** историческое свидетельство 20.11: CC-07 install PASS/`already_current`, operator blob `10de325be0335733a248c412943f39d45bd93c62`, adapter blob `ef2fa2cd6b0ddfefc920548995274f123c5884bf`, `C:\Control Center\v20-preview-d80f2446\v20_app.py`, `127.0.0.1:8502`. Текущая byte-parity, #602 installed, deps NOT_VERIFIED. LIVE Tasks/switches/FINAM positions/orders/SLTP и аварийный RECOVER UNKNOWN/NOT_VERIFIED.

**Ограничения:** CC-G53-01 исправлен в SOURCE, rollout не доказан. UI MAIN не отображает request_id; G5.3.1 offline candidate. Технический interlock повторного ручного dispatch с новым ID не доказан; FAILED_UNKNOWN запрещает повтор регламентом, нужна независимая сверка Task/switch/audit/FINAM READONLY. [Отчёт #602](docs/V20_HEALTH_EXPOSURE_FIX_20261126.md) исторический pre-merge. Cold restore NOT_TESTED.

**Post-G9:** H01/M01 ↔ V20 F6 (Protect3/HALTED и CC-07), H02 (idle TTL), H03 (client boundary CONFIG_DEPENDENT), M04 (correlation/unknown retry), M03 (release crash), M02/M05/M06 (availability/timeout/log growth), L01/P01. Доказательства, proposed gates B1–B7, 83/83 reported offline и ограничения — [JOURNAL](JOURNAL.md). CRITICAL не подтверждён; fixes NOT_RUN. #602 SOURCE fix остаётся применим, installed UNKNOWN. Не считать #617 разрешением на изменение кода.

**Далее:** Kimi Code workspace `C:\Control Center`; после разовой TRL Evolution и решения владельца согласовать V20+CC технический пакет/pins, exact CI scope, offline/native/browser tests, фактическую client boundary и paired backup/rollback. #602 включить в согласованный CC rollout; отдельное разрешение на deploy, READONLY acceptance и ARM. Не повторять адаптацию и не запускать роботов ради теста.
