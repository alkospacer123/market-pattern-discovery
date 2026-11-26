# V20 Trading System M15 — паспорт

**Решение владельца 26.11.2026:** сохранить сигналы и R088 60/30/45 + TP6 + Protect3 + HOLD5, EXT2 OFF, Market NEXT_OPEN. После 1–2 месяцев фактической торговой статистики рассмотреть лимитные входы, без автоматической смены. #601 — принятый SOURCE-кандидат диагностического журналирования Protect3, не установлен; подготовить единый пакет Shallow/OBV/Inside с installed identities, SHA/pins, offline regressions, backup/rollback и отдельным разрешением на установку, READONLY postflight. Историческая внутренняя причина 20.11 UNKNOWN. Не менять торговую логику или ARM ради квалификации.

**ACTIVE system; LIVE state not re-verified here.** Канонический [release R088 20.11](../V20_TradingSystem_M15/V20-08/LIVE_RELEASE_R088_20261120_RU.md) и [V20 AGENTS](../V20_TradingSystem_M15/AGENTS.md).

Три робота: **Shallow / OBV / Inside**, каждый на независимом FINAM-счёте. N4: USDRUBF, CNYRUBF, GLDRUBF, IMOEXF; M15, Market NEXT_OPEN, initial SL 2×ATR14, 1.5% risk per new trade, nominal 6% cap, capital **60/30/45**. **TP6 + Protect3 (+3R→SL +1R) + HOLD5** (5 наблюдаемых торговых сессий включая вход, выход на первом доступном Open шестой), **EXT2 OFF**.

**MAIN ≠ INSTALLED:** базовый `V20_TradingSystem_M15/v20_runtime/finam_live.py` blob `b80fb9eb135f7cdcb4c78337e2b808c4d7135195`; установленный согласно операторскому R088 отчету — blob `5d30270d3936fb52f58a61aa3abbf070d7df6b57` после **9 последовательных патчей**, порядок в [Windows offline CI](../.github/workflows/v20-08-live-windows.yml). Не искать готовый installed Python-модуль как единственный файл Git main.

V20 имеет зависимости `TradingSystemLab.stage8_robot` и `IntradayLab.core`; удалять их нельзя. История 2025–2026 использовалась в исследованиях и **не untouched TRUE OOS**. ZERO LOOK-AHEAD, costs/slippage и frozen signal rules обязательны.

Датированный 20.11 вывод: workers Running, switches HALTED 3/3, no automatic ARM. Текущее FINAM/SLTP/ARMED на момент этого документа **не проверялось**.

**Экзамен Kimi Code:** объяснить base+9-patch, SHA, последствия STOP/Protect3/HOLD5, разделение MAIN/INSTALLED/LIVE, выполнить R088 только в одноразовом offline checkout, показать stdout, тесты и git diff. Никаких живых приказов/кнопок/FINAM.
