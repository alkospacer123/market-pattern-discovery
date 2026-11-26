# TRL R100 — идентичность и переназначение ID

Канонический идентификатор: **TRL-R-2026-100 / R100**, USDRUBF First-to-Last Half-Hour Momentum. Решение: `REJECT_CURRENT_BASELINE`; не кандидат LIVE. Исходный Kimi-пакет ошибочно использовал R099, уже зарезервированный по отчёту от 25.11.2026 за DAILY_TSMOM60 (предрегистрация, не выполненный backtest; полный отдельный протокол здесь отсутствует).

Это исключительно исправление идентификатора публикации. Правила, frozen protocol, код, исходные метрики и артефакты расчёта не пересчитываются и не меняются. Внутренние ID, имя `run_r099.py` и исторические ссылки внутри оригинальных доказательств остаются legacy. Весь каталог [experiments/r100](experiments/r100/FROZEN_PROTOCOL.md) перенесён побайтово, включая неизменный ARTIFACT_MANIFEST.json. Канонические внешние ссылки в карточке, отчёте, журнале и реестрах обновлены. Оригинальные документы сохранены в предшествующем commit импортированного патча; оригинальный локальный commit Kimi заявлен в заголовке format-patch, не приравнивается к вновь созданному Git commit.

- Original Kimi commit: `7487d9490fa83478dd3e7169ed672d57ae23993d`.
- Original uploaded ZIP SHA256: `0e5eb76bccb97c0c2d094ecdfa7623f6768dd711027afef9bbec317a708eb1f6`.
- Original format-patch SHA256: `256f867a587bde00e7e04d8a89ecd6c92932a990005aac5825c0face57a4b3ef`.
- Frozen protocol SHA256: `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`.
- Original research base: `f0d289bd64536975dbcf3ec25ed1811c06116119`.
- Pinned data commit: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
- Manifest: 17/17 entries validated by SHA256 and size; entire 18-file experiment byte-identical after relocation.

Kimi reported two matching analytical replays (6 outputs) and separate vectorized ledger/HAC verification. GPT's previously reported independent calculation matched eligible 922, trades 910, Gross +10960 ₽, Net C2 −25440 ₽, PF C2 0.5277, Net C4 −61840 ₽ and beta 0.03549. Full independent HAC/bootstrap/cross-timeframe replay by GPT not claimed. Current publication verification is byte/manifest/link integrity, not a new backtest. Retrospective 2023–2026 is NOT TRUE OOS; no actual broker cost, GO, depth or LIVE acceptance. No V20 or capital changes.
