# V20-04.2 — начат адресный frozen parity после закрытия карточки

Историческая карточка закрыта коммитом `29089f1502d58e586d20d0114b688c97a855e40f`, 77 runtime-тестов PASS на этом SHA. Исследования карточки не продолжаются.

Возврат к действующему 04.2: `completed_signal` сопоставлен с опубликованными RAW_SIGNAL V20-03 на шести заранее выбранных первых USD-сигналах 2024 года: по long/short для каждой стратегии, без отбора по admission/PnL/horizon. Вход — только префикс исходных SHA-проверенных M15 до signal_bar_dt, без чтения чисел 2025. Проверены side, strategy, symbol, момент NEXT_OPEN и исходный ATR14. DataFrame не изменяется.

| Стратегия | Side | Бар сигнала МСК |
|---|---:|---|
| INSIDE_DAY_RELEASE | -1 | 2024-02-28 13:15:00 |
| INSIDE_DAY_RELEASE | 1 | 2024-01-18 16:30:00 |
| OBV_PRESSURE | -1 | 2024-01-11 10:00:00 |
| OBV_PRESSURE | 1 | 2024-01-18 16:30:00 |
| SHALLOW_PULLBACK | -1 | 2024-01-09 12:15:00 |
| SHALLOW_PULLBACK | 1 | 2024-01-03 12:00:00 |

Дополнительно проверены незавершённый бар/неправильный NEXT_OPEN, дубли timestamp и размещение/удаление временных CSV вне checkout. Найденное нарушение пути исправлено **только в V20 runtime adapter**: изолированный экземпляр locked helper получает внешний scratch parent. Frozen AST, BASE, сигнальные формулы и исходные файлы не редактируются.

**PASS:** 8 фактически выполненных адресных тестов; затем полный текущий runtime suite — **85 тестов PASS** (77 прежних + 8 новых). Зависимости уже присутствовали: numpy 2.3.5, pandas 2.2.3; новых зависимостей не добавлено. При отсутствии внешних котировок эти data-dependent тесты явно SKIP, не PASS; текущий прогон был без SKIP.

**04.2 остаётся PARTIAL:** это шесть сигналов одного N4-символа, не полная реплика ledger 1589 и не production M15/feed parity. Пограничные overnight/session/roll/feed-recovery сценарии и вся исполнительная часть 04.3 — ещё не приняты. Никакой parity по приказам брокера/SLTP/fill здесь не заявляется.

**Следующая работа в существующем roadmap:** закончить 04.2 frozen/feed parity на репрезентативном N4, затем 04.3 — H1 orders/SLTP/reconciliation/recovery для трёх изолированных роботов. Карточка не участвует в решении о сигнале или риске. H1/M15/FINAM/N4/стопы/риск/счета не менялись, LIVE OFF, roadmap 8/24 без новых подэтапов.

Файлы: `v20_runtime/frozen_adapter.py`, `v20_runtime/tests/test_frozen_adapter.py`, этот статус и tracker/README. Команда:

```sh
python -m unittest discover -s V20_TradingSystem_M15/v20_runtime/tests -v
```
