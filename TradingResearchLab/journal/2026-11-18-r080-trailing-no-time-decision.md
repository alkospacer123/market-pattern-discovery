# TRL Journal — 18.11.2026 R080: перенос H1/M15-trailing и удаление TIME_3RD

**Идея:** убрать TP6 и TIME3 в V20 60/30/45+EXT2, повторив старые H1/M15 механизмы ATR trailing. Для причинной проверки также убрать **только TIME3** при TP6+Protect3.

**Доказательство:** оригинальный R060/R073 cash engine и N4 OHLCV, 2023–Sep2026 + новые бары до 16.11, C1/C2/C4/GLD30, два GO. OOS_COMPROMISED. Отдельный addendum: финальный M15 T1 TRAIL3.5 **без ожидания +1R** (архивный A6+S1 с +1R не является финальным M15).

**Результаты OLD OCT C1:** CTRL TP6+Protect3+TIME3 1436/+443168,2 ₽/PF2,0029/DD18666,9; без TIME3 1382/+487930,5/PF2,1308/DD20049,4 (1 terminal GLD SHORT, mark+3864 отдельно); ATR3,5 после +3R без TP/time +446618,4/PF2,0006/DD16302,6; H1 ATR3,0+1R +244133,4/PF1,6707; финальный M15 ATR3,5 сразу +287999,6/PF1,7841. NOV C1 CTRL +301000/PF1,8587, noTIME +346160,9/PF2,0234, ATR3.5 after+3R noTP +313814,7/PF1,8962.

**EXTENDED OCT C1:** CTRL +459895,3/PF1,9867; TP6+Protect3 noTIME +506206,2/PF2,1097; noTP ATR3.5 after+3R +464722,3/PF1,9828; H1 trail +243943,1/PF1,6323; M15 trail immediate +283363,4/PF1,7255. Все 0 terminal open.

**Риски:** noTIME max 11,94 дня и 16 >7-дневных сделок vs CTRL max6,93 и ноль >7; M15-DD растёт, основная прибавка OCT +31,2 из +44,8 тыс ₽ в уже анализированном 2026; 2025 PF noTIME1,660<1,7. Ретроспективные ГО и условные издержки, реальная брокерская защита многодневного удержания не проверена.

**Решение:** `KEEP_R070 / REJECT_PURE_TRAIL_H1_M15 / CANDIDATE_NO_TIME_TP6_PROTECT3 / NO_LIVE_CHANGE`. Нужны prospective-данные и отдельная техническая оценка stop/GO/weekend/rollover. Отчёт [R080 Evolution](../evolution/2026-11-18-r080-no-time-no-tp-trail.md).
