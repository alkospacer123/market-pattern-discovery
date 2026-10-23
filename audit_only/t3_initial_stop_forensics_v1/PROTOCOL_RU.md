# INITIAL STOP FORENSICS V1 — фиксированный протокол

Фактический main проверен через GitHub и локальный checkout 20.10.2026:
38489db7e69336548a583f968f13aab49c20913b. PR557 HEAD 5836971e7ff8e472d8128c675c4f837b40a036ef,
PR518 HEAD d85cf85083d6fea047a1a960c9ead441f7b4a6ed.

До новых расчётов: проверить SHA256 источников/журналов, воспроизвести CONTROL с
frozen precision. Любое необъяснённое расхождение = STOP без альтернатив.
Движки engines/common/reconcile перенесены из PR557; отключена PARTIAL TP,
единственный исследуемый параметр initial_stop_atr: H1 CONTROL 2.5, STOP_2p0,
STOP_1p5; M15 CONTROL 2.0, STOP_1p5. Features и причинный порядок неизменны.
Данные H1 читаются непосредственно из git blob 50f1fd2178c18b7ab3bd969be82ad01f47a34745
в память, потому что текущий checkout data имеет другой H1; M15 из checkout
f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8. Исходные свечи не сохраняются в repo.

## Формальные определения, до forensics/replay

- Signal identifier = system/lifecycle/fold/symbol/signal close MSK/direction;
  последовательные trade_id не используются для сопоставления альтернатив.
- R0 каждой сделки — entry минус frozen initial stop по модулю; CONTROL R0
  неизменен для post-stop. Пересчёт R у альтернативы использует её собственный R0.
  Дополнительно exit варианта выражается в CONTROL R0 для общего сигнала.
- MFE_PRE_STOP: максимум favorable Open и экстремумов пережитых execution bars,
  H1 signal bar исключён, M15 execution bar включён. Exit-bar favorable Open
  допустим только если Open не пробил stop. H/L exit bar не определяет порядок;
  hit благоприятного порога в этой свече при отсутствии прежнего hit = AMBIGUOUS.
  Для гарантированного результата stop-first; сохраняется observed upper bound.
- MAE_EXECUTABLE: неблагоприятный экстремум пережитых баров, exit fill на exit bar;
  MAE observed upper bound включает полный exit bar и явно ретроспективен.
- LOW_FOLLOW_THROUGH: guaranteed MFE < +0.5 CONTROL R0 перед INITIAL_STOP;
  если exit-bar H/L достигает +0.5R, отдельно AMBIGUOUS (нет доказанного отсутствия).
- EARLY_ADVERSE_MOVE: adverse Open первой допустимой свечи < entry либо Close
  первой пережитой свечи < entry (симметрично SHORT); отдельно касание -0.5R
  за первые четыре допустимых бара. Это наблюдение, не ошибка рынка.
- TIGHT_STOP_LOST_WINNER: общий signal, CONTROL closed Gross R>0, вариант
  closed Gross R<0; только полный причинный replay, не вывод из MAE.
- ADVERSE_CONTINUATION_AFTER_STOP: в последующем окне достигнуто -1.5 CONTROL R0.
- RECOVERY_AFTER_STOP: в окне вновь достигнут исходный entry (level touch);
  crossings считаются по строго последовательным неперекрывающимся bar ranges:
  одно событие касания/пересечения на bar, реальное число внутрисвечных пересечений
  UNKNOWN; отдельно переходы completed Close через entry (точный счёт).
- TRAILING_GIVEBACK: exit reason ATR_TRAILING_STOP, max(0,MFE_PRE_STOP-exit R0)>0;
  отдельно отрицательные shifted-trailing exits.
- AMBIGUOUS: favorable/adverse level впервые достигнуты в одном баре и Open не
  доказывает порядок; INSUFFICIENT_DATA: недостаточно наблюдений/полноты окна.

Категории пересекаются; observations отделены от интерпретаций. Время первого
excursion = open при доказуемом Open, иначе интервал свечи (order UNKNOWN).
Bars held = допустимые execution bars, wall-clock отдельно от суммы их длительности.
Торговая дата = дата Open MSK; bar Close в 00:00 относится к предыдущей дате.
Post-stop начинается строго со следующего наблюдаемого бара. Окно включает
остаток stop-date и первый/второй полный следующий наблюдаемый trading date;
полный следующий день консервативно требует наблюдаемой более поздней даты.
Без exchange calendar полнота означает observed-date coverage, не отсутствие
внутридневных пропусков. Если конца окна нет, CENSORED, не negative/no-hit.
Post-stop использует полную историю символа pinned commit, включая границу H1
cold-start, но не переносит позиции/сигналы через неё.

H1 +1R TRAIL1 меняется естественно с R0, trailing 3 ATR неизменен. Диагностика
ранней активации: при общих сигналах сравнить фактический trigger/activation
и активный stop варианта в момент первого CONTROL trigger; никаких дополнительных
торговых моделей/параметров. M15 NEXT_OPEN/trail3.5 и no-adjacency неизменны.

Все calendar tables MSK. NO_DATA не ноль. H1 Baseline и historical TRUE OOS
холодные старты отдельно; WF folds отдельно, без включения в descriptive union.
DD каждого lifecycle от нуля; union DD не определяется (не капитализация).
MTM = сумма нормированных R входов на completed bars, не cash-return.

R15 1.5% realized equity, nominal cap6% не меняются. Денежный Net, RUB DD,
integer qty, cash-return = NOT_VALIDATED без полной исторической authority.
Grid diagnostics отдельно для frozen off-grid stops; округлённый stop не подменяет
research replay. Никаких LIVE, production execution, токенов, FINAM или сервера.

Один Draft PR; no merge/auto-merge. Синтетические тесты, отдельный verifier,
code freeze и минимум два свежих полных побайтных повтора обязательны.
Ретроспективный replay известного TRUE OOS не новый независимый OOS.

## Уточнения реализации до code freeze

LOW_FOLLOW_THROUGH классифицируется только для CONTROL, как определено выше;
альтернативные MAE/MFE и giveback остаются в их собственном frozen initial R0.
MFE−exit включает и потерю ниже entry; дополнительно выводятся возвращённая
положительная MFE и loss below entry. Frozen Close exit label сохраняется
для сверки; фактическое время выхода и observed exposure имеют нижнюю/верхнюю
границы, Open exit точен. Post-stop order сравнивает ordinal свечи и OPEN/INTERVAL,
чтобы различать prior-bar intrabar hit и Open следующей свечи с той же timestamp.
Дополнительные модели не вводятся. Это уточнения наблюдений/сериализации, не
изменения сигналов или торговых параметров.
