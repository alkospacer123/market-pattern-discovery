# V20-03 — актуальная публикация и provenance

Draft PR #565, существующая ветка `codex/v20-03-publish-partial-hold-20261021`; исходный head `072c4ccc9ab22e5c8b0c3d172272ebe29932fdd3`, фактический main `c3695b1304aef1acdd889264b3451184f7332bf7`. Только `V20_TradingSystem_M15/`, без merge.

Первый commit публиковал готовые результаты без replay. Текущая добавленная диагностика PF описана в [comparison/PF_DIAGNOSTIC_REPORT_RU.md](comparison/PF_DIAGNOSTIC_REPORT_RU.md); её данные и SHA256 — в [comparison/VERIFICATION.json](comparison/VERIFICATION.json). C1 — основной сценарий; C0 только разложение модельных расходов. Новые C2/STRICT, оптимизация и Walk-Forward не проводились.

Индекс offline ZIP SHA256 `1ab1f85373c2bbd7a385d228ea061f0cd8259f409a73d40babbcfc0ba7f5eb50` сохранён в publication/ARCHIVE_FILE_INDEX.json. Сам ZIP, оригинальный журнал 1589 и 43 quarterly M15 сейчас отсутствуют. Их прежние SHA сохранены, но повторная проверка байтов недоступных файлов NOT VERIFIED. Все 18 опубликованных старых результатов, frozen source, locked roll и исторические verification сохранены побайтово.

Четыре имеющихся внешних perpetual M15 CSV точно совпали SHA256 с архивным индексом. Для недостающих late-разрезов выполнено одно ограниченное воспроизведение трёх frozen-стратегий неизменными AST source-функциями и V20-02 run_one. Получены те же count/PF/net R/exit counts; построчная parity с оригиналом не заявляется. Производный журнал и воспроизводимый расчёт находятся в comparison/. Это не повтор всей research/causality/WF процедуры и не восстановление сделок из агрегатов.

Корневой AGENTS.md запрещает копировать source market data в репозиторий. Входные файлы читаются снаружи; временные symlink/cache расположены во внешнем `/workspace/work/v20_pf`. В Git нет исходных свечей/ZIP. Никаких действий FINAM/Intel/H1, изменения токенов/задач/заявок или активации M15.

Актуальные документы приведены к **ровно 8 этапам V20-01–V20-08**, разработка **V20-04**. Исторические originals, исходное ТЗ первой публикации, архивные acceptance и V20-02 сохранены с прежними формулировками как архив; они не определяют текущую нумерацию. Заключение о разработке входит в V20-03. Нового самостоятельного GO/HOLD/NO-GO, денежного replay или Shadow нет.

Текущая диагностика PARTIAL (14 PASS / 2 FAIL / 3 NOT VERIFIED) не меняет исходную приёмку 14 PASS / 4 FAIL и не подтверждает full N4/OOS. Проверка publication hashes/CSV/лимитов/8 этапов может быть PASS при этих оставшихся научных ограничениях. `offline/verify_publication.py` не запускает replay.
