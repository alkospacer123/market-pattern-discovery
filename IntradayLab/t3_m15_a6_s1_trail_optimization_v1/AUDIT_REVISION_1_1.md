# Аудит 1.1: только проверка отображаемых timestamp после новых результатов

Первый frozen audit.py дошёл до presentation-check, но остановился на top-winners timestamp: pandas Timestamp в Markdown отображается с пробелом (`2023-04-28 11:15...`), CSV serialization — ISO с `T` (`2023-04-28T11:15...`). Одинаковые instants ошибочно сравнивались как разные display strings. Ошибка сохранена в FIRST_AUDIT_FAILURE.txt, оригинальный audit.py оставлен побайтно неизменным.

`audit_v1_1.py` — отдельно сохранённая копия с двумя добавленными строками: только поля signal_time/entry_time/exit_time для display-check преобразуются через datetime.fromisoformat и str. Replay, все scalar вычисления/критерии/сопоставление экономической траектории, tolerance и primary результаты не меняются. `repeat_v1_1.py` отличается от frozen repeat.py только выбором audit_v1_1.py. Новые файлы отдельно Git-frozen до повторного аудита/двух свежих replay; AUDIT_REVISION_FREEZE.json содержит SHA.

Это исправление после просмотра новых результатов раскрыто явно. Все первые primary results проверяются по FIRST_PRIMARY_SHA256.json; full primary run и отчёты остаются на первоначальном corrected pre-candidate freeze `3b01eccb79f337e1f979d4e734545876f613de64`. Торговые engine/scalar, единственный trail parameter, пять значений и торговые правила не менялись.
