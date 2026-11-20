# Recovery — карта знаний трёх систем для GPT и Kimi

**Актуальная навигация:** 20.11.2026. **Статус:** `DOCUMENTATION_UPDATE_IN_DRAFT / R0_IN_PROGRESS`. Этот каталог находится в PR #571, пока **не** в `main`. Не является подтверждением текущей LIVE торговли или полноценного Disaster Recovery.

## Начать здесь — новое прежде исторического
1. [Agent.md](Agent.md) — правила обоих ИИ, источник истины и запреты.
2. [CURRENT_STATE_2026-11-20.md](CURRENT_STATE_2026-11-20.md) — датированное состояние MAIN/INSTALLED/LIVE/RESEARCH.
3. [PROJECT_ROADMAP_2026-11-20.md](PROJECT_ROADMAP_2026-11-20.md) — согласованный порядок R0→R4→снимок→R7→R1→R2→R3→R5→R6→R8.
4. [DECISIONS_ADDENDUM_2026-11-20.md](DECISIONS_ADDENDUM_2026-11-20.md) — текущие решения; [DECISIONS.md](DECISIONS.md) — решения прежнего периода.
5. [SOURCE_GAPS_2026-11-20.md](SOURCE_GAPS_2026-11-20.md) — GitHub SHA, внешние архивы, недостаточные свидетельства.
6. [HISTORICAL_DRAFT_REGISTER_2026-11-20.md](HISTORICAL_DRAFT_REGISTER_2026-11-20.md) — 11 Draft и правила сохранения уникального.
7. [AI_CONTINUITY_KIMI_2026-11-20.md](AI_CONTINUITY_KIMI_2026-11-20.md) — три будущих проекта Kimi и экзамены.
8. [TIMELINE_ADDENDUM_2026-11-20.md](TIMELINE_ADDENDUM_2026-11-20.md) и [TIMELINE.md](TIMELINE.md) — события с датами.
9. [PROJECT_MASTER.md](PROJECT_MASTER.md), [V20_SYSTEM.md](V20_SYSTEM.md), [CONTROL_CENTER.md](CONTROL_CENTER.md), [TRL.md](TRL.md), [RECOVERY_GUIDE.md](RECOVERY_GUIDE.md), [EVIDENCE_AND_GAPS.md](EVIDENCE_AND_GAPS.md), [MAINTENANCE.md](MAINTENANCE.md) — ранние паспорта и процедуры, сохранять, не принимать автоматически за действующие.
10. [CURRENT_STATE_2026-11-09.md](CURRENT_STATE_2026-11-09.md) — неизменённый исторический срез 09.11, **не** текущая телеметрия.

## Приоритеты первоисточников
**V20:** `V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md` из `main`, девять последовательных патчей + проверенные установленный Intel код/FINAM. Последний документированный статус Running/HALTED 3/3; ARMED неизвестен.

**Control Center:** `ControlCenter/README.md` и проверенный установленный контур `C:\Control Center`, `127.0.0.1:8502`. UI и Windows Task не равны состоянию брокера.

**Trading Research Lab:** `TradingResearchLab/reports/TRL-NOV-2026-KIMI-START-HERE.md` + финальный closeout ноября и внешние исходные ZIP/XLSX, сверяемые по SHA256.

## Безопасность и неполнота
Публичный каталог не содержит FINAM/DPAPI, токены, личные или торговые идентификаторы, production SQLite, сырые приватные журналы и необезличенные чаты. Не запрашивать их в открытом чате. Архивы 02.11/09.11 и Git mirror проверялись по SHA, **cold restore не доказан**. R0, R5, R6 и обучение Kimi не объявлять PASS без независимых испытаний.

## R0: пофайловая ревизия исторических Draft (20.11.2026)

- [R0_HISTORICAL_RESEARCH_DECISIONS_2026-11-20.md](R0_HISTORICAL_RESEARCH_DECISIONS_2026-11-20.md) — смысловые выводы и различие научного PASS от принятой торговой гипотезы.
- [R0_CC_DRAFT_BLOB_AUDIT_2026-11-20.md](R0_CC_DRAFT_BLOB_AUDIT_2026-11-20.md) — 40 файлов старого CC/H1.
- [R0_T3_RESEARCH_DRAFT_BLOB_AUDIT_2026-11-20.md](R0_T3_RESEARCH_DRAFT_BLOB_AUDIT_2026-11-20.md) — 292 файла T3/H1/M15 исследований.
- [R0_V20_M15_DRAFT_BLOB_AUDIT_2026-11-20.md](R0_V20_M15_DRAFT_BLOB_AUDIT_2026-11-20.md) — 93 файла ранней V20 и исторического IntradayLab.

**425 файловых записей** в 10 исторических PR сопоставлены с `main` по Git blob SHA-1. Независимая архивация, проверка полноты PR-обсуждений и разрешение на закрытие остаются отдельными незавершёнными условиями.
