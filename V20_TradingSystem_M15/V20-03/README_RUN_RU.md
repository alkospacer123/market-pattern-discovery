> **Актуальное дополнение по котировкам, 21.10.2026:** оригинальный `2018-2022.zip` и все 43 quarterly M15 получены и совпали SHA256. Оригинальный полный offline ZIP/reference ledger 1589 по-прежнему отсутствуют. Диагностика включает проверку исходных траекторий и один необходимый late V1 replay из-за обнаруженного различия gap/reset. Roadmap 8 этапов, V20-04 разработка.

## Воспроизведение quote-добавки

Исходный ZIP и perpetual CSV должны оставаться вне Git. Ни брокер, ни сеть не нужны. Команда использует опубликованные базовые журналы, точные frozen feature-функции и один существующий V1 diagnostic replay; готовые проверенные caches повторно не исполняют replay.

```bash
python V20-03/comparison/quote_diagnostics.py \
  --quarterly-zip /external/2018-2022.zip \
  --market-data /external/forever \
  --work /external/work/v20_quotes \
  --gap-v1
```

Структура perpetual-входов: `forever/USDRUBF/USDRUBF_M15.csv` и аналогично CNYRUBF/GLDRUBF/IMOEXF. Их SHA256 проверяются по исходному архивному индексу. Папка `--work` обязана быть вне репозитория; `--reuse-measurements` допускает только созданные этой задачей cache с проверкой подписи функций и SHA256, а не произвольный pickle.

Основные результаты: comparison/PF_DIAGNOSTIC_REPORT_RU.md, METHODOLOGY_EFFECTS_RU.md, VERIFICATION.json. Проверка публикации ниже не выполняет replay. Описания исходной первой offline-публикации далее исторические и не задают актуальную нумерацию roadmap.


# Проверка опубликованного V20-03 без повторного replay

Это текстовая публикация готового offline-архива с SHA256 `1ab1f85373c2bbd7a385d228ea061f0cd8259f409a73d40babbcfc0ba7f5eb50`. Все 18 файлов `results/` перенесены побайтово. Статус PARTIAL/HOLD, PF условны, полный N4/OOS не заявляется.

Из `V20_TradingSystem_M15/`:

```bash
sha256sum -c PUBLICATION_MANIFEST_SHA256.txt
python V20-03/offline/verify_publication.py
```

Нужен Python 3.11+, только стандартная библиотека. Эти команды не запускают сигналы/сделки и не обращаются в сеть. Они проверяют хеши, сохранённые доказательства и согласованность существующих таблиц. Новые разрезы `publication/STATISTICS_*.csv` и JSON представляют выборку строк/смену формата из неизменённого `results/STATISTICS.csv`; расчёт стратегий не повторялся.

Frozen `base.py`, `run.py`, `study_v4.py` и зависимости включены побайтово. Код runner/test causality сохранён для review. Исходные свечи/ZIP/современные marketdata M15/inside signal grids/полный reference payload не публикуются по корневому `AGENTS.md`. Поэтому напрямую запускать старые main/replay в этом checkout не следует: полный набор входов намеренно отсутствует, а у legacy main есть старые абсолютные пути.

При отдельно поставленной задаче воспроизведения используйте полный прежний offline-архив во **внешней папке вне репозитория** и его оригинальную инструкцию, сохранённую здесь как `evidence/archive_original/V20-03/README_RUN_RU.md`. Для того архива нужны Python 3.12.14, numpy 2.3.5, pandas 2.2.3; команды воспроизведения относятся к полной внешней распаковке, а не к этой публикации. Текущее поручение явно не требует повторного replay/оптимизации.

Архивный `DELIVERY_MANIFEST_SHA256.txt` описывает полный исходный offline-пакет, включая непубликуемые данные. Его индекс сохранён в `publication/ARCHIVE_FILE_INDEX.json`. Для текущей Git-публикации используйте только `PUBLICATION_MANIFEST_SHA256.txt`. Отдельно `results/RESULT_HASHES.json` продолжает проверять ровно исходные 18 результатов (17 хешируемых файлов и сам JSON).
