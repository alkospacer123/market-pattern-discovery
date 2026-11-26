# R099 — offline runbook

## Назначение и границы

Воспроизводится только frozen baseline TRL-R-2026-099. Запуск не обращается к V20, FINAM, SQLite, токенам, заявкам, капиталу или production. Сеть во время расчёта не используется.

## Pinned inputs

- Repository: `alkospacer123/market-pattern-data`.
- Commit: `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`.
- Root должен указывать на каталог `forever/`, содержащий `USDRUBF/USDRUBF_{M5,M15,M30}.csv`.
- M5 SHA256: `3758ed99e4ec0c712af09575ddc74f0437f2fcddda05df2c5d27268296037786`.
- M15 SHA256: `fef80630080a4e2a5e968d620b663f51acd1b7ab9d5d326a42c68cf2b80c67b8`.
- M30 SHA256: `1945489f25cf003d9ca63faa5cbf233282f461f7aafef4112445746146061e4d`.
- Protocol SHA256: `ea2e066085b016b53be58f947b95e9b37aca99554cc5cdfbeff442f8684ffee0`.
- Final code SHA256: `56e99cd46a6f63eefe13be4fd2d95296bc1c67116a5cada929fdb52a858a2fdb`.

Скрипт сам проверяет M5 SHA256 и останавливается при `SOURCE_DRIFT`. Перед запуском следует отдельно сверить M15/M30 по `run_manifest.json` предыдущего canonical run.

## Один canonical run

```bash
python3 run_r099.py \
  --data-root /path/to/market-pattern-data/forever \
  --output-dir /path/to/r099-canonical
```

Ожидаемая среда canonical run: Python 3.12.12, pandas 2.3.2, numpy 2.2.5, Linux. Другие версии требуют отдельной отметки; UNKNOWN не считается PASS.

Ожидаемый терминальный результат:

```text
decision = REJECT_CURRENT_BASELINE
eligible = 922
trades = 910
predictive gate = true
data/bootstrap_economic/pf/years/concentration gates = false
prefix/future controls = true
```

## Обязательные outputs

`daily_ledger.csv`, `excluded_days.csv`, `metrics.csv`, `data_quality.json`, `statistical_tests.json`, `controls.json`, `run.log`, `run_manifest.json`.

`replay_verification.json` создан после двух завершённых запусков и поэтому не входит в сгенерированный во время расчёта `run_manifest.json`; его SHA фиксируется общим `ARTIFACT_MANIFEST.json`.

## Clean replay

```bash
python3 run_r099.py \
  --data-root /path/to/market-pattern-data/forever \
  --output-dir /path/to/r099-replay

for f in controls.json daily_ledger.csv data_quality.json \
         excluded_days.csv metrics.csv statistical_tests.json; do
  cmp "/path/to/r099-canonical/$f" "/path/to/r099-replay/$f" || exit 1
done
```

Все шесть файла обязаны совпасть побайтово. `run.log` содержит разные фактические UTC timestamps; сравниваются его смысловые поля. `run_manifest.json` также будет отличаться из-за hash `run.log`. Это не скрывается и не мешает сравнению аналитических outputs.

## Фактическая финальная пара запусков

- Canonical: 2026-11-26T11:56:18.754856Z — 11:56:47.044624Z.
- Clean replay: 2026-11-26T11:56:48.762444Z — 11:57:11.566222Z.
- Все шесть аналитических outputs совпали; оба процесса вернули `REJECT_CURRENT_BASELINE`.
- Статус `REPRODUCIBLE_VERIFIED` относится к расчёту, не к TRUE OOS или прибыльности.

## Независимая сверка ledger/HAC

```bash
python3 independent_check.py \
  --m5 /path/to/market-pattern-data/forever/USDRUBF/USDRUBF_M5.csv \
  --canonical-dir /path/to/r099-canonical \
  --output /path/to/independent_verification.json
```

Требуется statsmodels 0.14.5. Проверка не импортирует `run_r099.py`: отдельная pivot/shift-логика восстанавливает eligible days, ledger, P&L и OLS/HAC с явной finite-sample correction. Фактический результат `PASS`: 922/910, максимальное денежное расхождение `1,35×10⁻¹¹ ₽`, beta/p совпадают в floating-point tolerance. Код SHA256 `22382754c120527b354e4265b700f7203ebe4dd8c56c9404db528cac511b8070`; evidence SHA256 `b536867c9e9f67cc734245af32fad1fb796b9c15e06c613be05c77c84c9100b0`.

Bootstrap и остальные diagnostics второй реализацией не переписывались; независимая сверка не означает независимый OOS.

## История технических исправлений

1. Первый запуск остановился с `AttributeError` из-за `daily_c2.net_rub` вместо `daily_c2.net_rub_c2`; statistical outputs не были созданы.
2. После исправления имени обнаружен нулевой bootstrap из-за merge `datetime.date` со строковыми датами. Типы приведены к общему строковому формату, и расчёт повторён.
3. Prefix/future controls переведены с ledger nonzero trades на все eligible days; добавлены месячные diagnostics и полный eligible benchmark.
4. Исправлена нормировка benchmark bps на лот.
5. Добавлен post-freeze diagnostic M15 18:45 close. Frozen comparator M15/M30 18:30 сохранён, trading rules и gates не изменены.
6. При независимой HAC-сверке statsmodels default дал немного другую SE; после явного `use_correction=True`, соответствующего frozen manual Newey–West finite-sample factor, beta/SE/p совпали в floating-point tolerance. Canonical statistics не изменялись.

Промежуточные результаты не использовались для выбора параметров, стороны, сессии или фильтров. Протокол не редактировался после freeze.
