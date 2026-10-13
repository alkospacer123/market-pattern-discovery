# Исправление CONTROL до любых новых trailing-результатов

Первый freeze `f4d17a9833e8830819ef4dac7e7b02e5d3a9d72b`; initial FREEZE сохранён. До первого candidate replay первичный gate остановился с 20 170 MISSING-полями: #504 CSV содержит union schema и пустые cells там, где внутренние sparse dict вообще не имеют optional key. Сверщик ошибочно считал absent key отличием от empty CSV. Все присутствующие значения и опубликованные PF/R/CLOSED/months/DD совпали, max numeric delta 0.0. Ни один новый trailing не был вычислен. Полный негативный gate/diff сохранён в pre_candidate_control_failure/; CONTROL_FIRST_LOG.txt сохранён.

Изменение только `control.py`: actual row нормализуется к union schema reference, absent optional key становится None; comparator уже трактует None как empty CSV. Непустое ожидание по-прежнему даёт FAIL. Торговые engine.py/scalar.py, spec, grid и аналитические правила неизменны. Добавлен synthetic regression test. Новый source/spec/tests freeze commit предшествует повторному CONTROL и всем кандидатам; FREEZE.json заменён ссылкой на него с сохранением initial commit.

В исходный freeze случайно вошёл __pycache__; отдельный pre-result commit `c9c1b6b2` удалил transient Python bytecode. Эти файлы не входят в итоговый diff. Торговый код не менялся.
