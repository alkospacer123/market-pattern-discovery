# Первичная диагностика CONTROL до нового replay

Первый полный CONTROL совпал по сделкам, Stops, OPEN, PF/R и регулярности, но gate остановился на 16 136 отсутствующих metadata fields: четыре поля (PreviousATR, H1ATRRatio, H1PreviousATRRatio, H1PreviousAvailableAt) × 4 034 A6+S1 entry opportunities. Это неполная схема нового журнала, не расхождение торгового replay.

Поля причинного signal-контекста добавлены до initial pre-result freeze и до любых исторических Next Open. После этого primary и отдельный scalar CONTROL прошли каждый 2 442 256 проверок, 0 расхождений, max delta 5.4569682106375694e−12. Исполнение Next Open до PASS не запускалось. Тот же gate повторяется каждым primary run.

Опубликованные CLOSED: A6+S1 BASELINE 512 / OPTIMIZED 497; T1 568 /549; T1+S1 560 /545. По одному terminal OPEN на каждую конфигурацию. Исходные PF/R/положительные месяцы совпали со всеми шестью строками задания.
