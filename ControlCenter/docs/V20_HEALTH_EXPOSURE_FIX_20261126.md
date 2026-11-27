# V20 Control Center: ложный HEALTHY при локальной экспозиции — 26.11.2026

**Дополнение 27.11.2026 (C3.2):** [PR #602](https://github.com/alkospacer123/market-pattern-discovery/pull/602) MERGED 26.11, merge commit `e70cfed5db274530ba9687f5a9b13f2290fde1e7`. SOURCE fix принят; первоначальный pre-merge отчёт ниже сохраняется без исправления исторического статуса. INSTALLED/LIVE остаются NOT_VERIFIED/UNKNOWN; synthetic local exposure не равен broker protection. Установка только отдельным решением владельца, с CC-only backup/SHA/ACL и READONLY acceptance. Текущий статус — [STATUS](../STATUS.md).
**Статус:** `SOURCE_FIX_READY_FOR_INDEPENDENT_REVIEW`. Это подготовка отдельной ветки и Draft PR, а не установленное или принятое исправление. **Merge, Intel, production-панель, deploy, Windows Tasks, FINAM и роботы не затрагивались.**

## 1. Задача, разрешения и границы

Цель: устранить возможность зелёного общего `HEALTHY`, когда свежий локальный отчёт содержит открытую позицию и ноль локальных защитных стопов, а также когда exposure-поля отсутствуют или противоречат друг другу.

Разрешено владельцем: разработка и изолированное тестирование на резервном компьютере, в отдельной рабочей копии и ветке. Изменения production-панели, Intel, управление роботами, установка обновлений и Merge требуют отдельного разрешения. Доступ к LIVE/FINAM/Tasks/роботам, секретам и DPAPI не запрашивался и не использовался.

| Слой | Результат |
|---|---|
| MAIN / SOURCE | Аудирован pinned BASE `f0d289bd64536975dbcf3ec25ed1811c06116119`; дефект подтверждён в `cc/v20_contract.py` |
| DERIVED | Минимальный фикс и synthetic/AppTest регрессии подготовлены в `kimi/cc-healthy-exposure-20261126`; exact head фиксируется в PR |
| INSTALLED | **UNKNOWN**; фактические байты и версия панели на Intel не проверялись |
| LIVE / FINAM | **UNKNOWN**; позиции, заявки, fills и SLTP у брокера не наблюдались |
| RESEARCH / ARCHIVE | Исторические CC-03/H1/M15 документы не использовались как контракт действующей V20-панели |

Действующий UI — `ControlCenter/v20_app.py`, не исторический `ControlCenter/app.py`. Применён `COC-2026-01` `1.0.0-rc.1`, прежде всего `COC-CC-02`: `None` нельзя превращать в ноль, FLAT или PROTECTED.

## 2. Наблюдение и первопричина

Сообщённый симптом: панель могла показывать зелёный `HEALTHY` при открытой локальной позиции и отсутствии локальных защитных стопов. Ожидаемое поведение: такое сочетание обязано быть видимым текущим `FAULT`; отсутствие данных и противоречие не должны становиться HEALTHY.

На BASE функция `cc.v20_contract.parse()` доверяла входному `engine_state=HEALTHY` после проверки freshness, Task `RUNNING`, kill switch `ARMED` и `unresolved_local=0`. Она не проверяла полноту и согласованность `positions_local` / `stops_local`.

Чистый synthetic BASE-вход с валидной подписью:

```text
engine_state=HEALTHY, task_state=RUNNING, kill_switch=ARMED
positions_local=1, stops_local=0, unresolved_local=0
→ status=HEALTHY
```

Также на BASE были непосредственно получены ошибочные результаты:

```text
positions=1, stops=None, unresolved=0 → HEALTHY
positions=None, stops=0, unresolved=0 → HEALTHY
positions=0, stops=1, unresolved=0   → HEALTHY
```

**Причина на уровне SOURCE:** отсутствовал fail-closed exposure-gate между строгим разбором snapshot и общим статусом. Heartbeat здесь ни при чём: `heartbeat_health()` независимо измеряет только свежесть и должен сохранять это значение.

`deployment/v20_live_export.py` на BASE публикует `positions_local=None`, `stops_local=None`, `unresolved_local=None`; его `engine` не вычисляет HEALTHY. Поэтому BASE-дефект панели подтверждён, но конкретный historical installed snapshot и фактический брокерский эпизод по имеющимся данным не атрибутируются. Это ограничение не отменяет исправление достижимого дефекта контракта.

## 3. Минимальный контракт исправления

Wire-схема `cc.v20.readonly.v1`, digest, exporter, receiver, TTL=300 и robot/account binding не меняются. Возвращаемый `parse()` результат дополняется наружным производным `status_reason`; это поле **не входит** в подписанный JSON.

| Условия свежего отчёта | Итоговый status | status_reason |
|---|---|---|
| `positions>0`, `stops=0`, остальные поля валидны | **FAULT** | `LOCAL_POSITION_WITHOUT_STOPS` |
| Источник HEALTHY, любое exposure-поле `None` | **UNKNOWN** | `LOCAL_EXPOSURE_DATA_MISSING` |
| Источник HEALTHY, `positions=0`, `stops>0` | **UNKNOWN** | `LOCAL_EXPOSURE_CONTRADICTION` |
| Источник HEALTHY, свежесть/Task/ARMED/unresolved не проходят | **UNKNOWN** | `LOCAL_HEALTH_GATES_FAIL` |
| Источник HEALTHY, все gates и exposure-проверки проходят | **HEALTHY** | `LOCAL_HEALTH_GATES_PASS` |
| Отчёт просрочен | **STALE** | `STALE_LOCAL_REPORT`; текущие exposure-метрики скрываются |
| Наблюдение недопустимо из будущего | **STALE** | `FUTURE_LOCAL_REPORT` |

Правила и ограничения:

- Незащищённая локальная позиция переводится в FAULT независимо от заявленного HEALTHY/HALTED/UNKNOWN/FAULT, пока отчёт свежий.
- HALTED/FAULT/UNKNOWN источника не уничтожаются при неполных exposure-полях; причина отдельно показывает отсутствие данных.
- Не вводится требование `stops>=positions` или равенства counts: число стопов не доказывает quantity coverage, а один стоп может относиться к агрегированной позиции.
- Даже `(positions=1, stops=1)` не доказывает брокерские SLTP или полное покрытие всей позиции.
- `ARMED · ЦИКЛ PASS/PENDING` разрешён только для исходного `engine_state=UNKNOWN`, а не для отклонённого HEALTHY или противоречия. При отсутствии exposure-данных рядом явно выводится «НЕТ ДАННЫХ — FLAT и защита не подтверждены».
- Свежий Heartbeat может оставаться зелёным рядом с FAULT: это независимая свежесть, а не оправдание общего HEALTHY.
- Панель не выполняет новых торговых, Task или recovery действий; сообщение FAULT предлагает только авторизованную брокерскую сверку.

Изменения: `cc/v20_contract.py`, `v20_app.py`, `tests/test_v20_control_center.py` и данная документация. Изменений V20, FINAM, Intel, `.github/workflows`, секретов и production paths нет.

## 4. Доказательства и изолированное тестирование

Среда: Linux, Python 3.12, pytest 8.4.2, Streamlit 1.50.0, Plotly 6.3.1, disposable venv. Использовались только synthetic JSON и Streamlit `AppTest`; реальные Windows APIs, Tasks, FINAM, Intel, broker I/O и секреты не вызывались.

| EV | Тип | Проверка | Результат |
|---|---|---|---|
| EV-01 | PERFORMED_CHECK | GitHub MAIN разрешён в полный BASE SHA; критичные источники прочитаны на pinned snapshot | CONFIRMED |
| EV-02 | PERFORMED_CHECK | Статический путь `v20_app.py → export_gate → refresh_once → v20_live_export.py → v20_receiver.acquire → v20_contract.parse → UI` | STATIC_OBSERVED; runtime не утверждается |
| EV-03 | PERFORMED_CHECK | Чистый synthetic BASE `positions=1, stops=0` и матрица неполных/противоречивых полей | Дефект CONFIRMED |
| EV-04 | PERFORMED_CHECK | Финальная редакция 14 целевых cases на pristine BASE с новыми тестами | **14 failed**, как ожидалось для regression proof |
| EV-05 | PERFORMED_CHECK | Те же 14 cases на DERIVED | **14 passed** |
| EV-06 | PERFORMED_CHECK | `tests/test_v20_control_center.py` | **52 passed** |
| EV-07 | PERFORMED_CHECK | Полный `tests` Control Center | **729 passed, 57 skipped, 0 failed** |
| EV-08 | PERFORMED_CHECK | `git diff --check`, инвентарь изменённых путей и границы side effects | PASS для подготовленного дерева; повторяется после финальной документации |
| EV-09 | — | INSTALLED/LIVE/FINAM и физический Intel | **UNKNOWN / NOT_TESTED**, не часть разрешённого scope |

Воспроизводимые команды из `ControlCenter/`:

```bash
python -m pytest -q -p no:cacheprovider \
  tests/test_v20_control_center.py::test_healthy_requires_complete_local_exposure_observations \
  tests/test_v20_control_center.py::test_known_local_position_without_stops_is_fault_not_healthy \
  tests/test_v20_control_center.py::test_healthy_rejects_contradictory_flat_with_local_stops \
  tests/test_v20_control_center.py::test_healthy_positive_controls_reach_exposure_gate \
  tests/test_v20_control_center.py::test_unprotected_exposure_becomes_stale_not_current_fault_after_ttl \
  tests/test_v20_control_center.py::test_ui_shows_local_unprotected_exposure_despite_fresh_heartbeat \
  tests/test_v20_control_center.py::test_ui_armed_cycle_explicitly_marks_missing_exposure_data
python -m pytest -q -p no:cacheprovider tests/test_v20_control_center.py
python -m pytest -q -p no:cacheprovider tests
```

Положительные controls `(positions,stops)=(0,0),(1,1),(2,1)` достигают HEALTHY и доказывают, что не введено ошибочное равенство counts. Негативные controls покрывают None, позицию без стопов при всех четырёх исходных engine states, FLAT со стопами, TTL и UI. BASE failures служат known-bad mutation/oracle: predicates достижимы и тесты чувствительны к исходному дефекту.

Все 57 skips относятся к Windows PowerShell syntax, disposable hosted Windows, native NTFS/ACL/transport. Они не засчитаны как PASS. AppTest проверяет Streamlit-рендер, но не заменяет физический браузер, Windows native или LIVE acceptance.

## 5. Ревью, установка и откат

Самопроверка автора не является независимым ревью. До решения владельца требуется **non-author review** exact PR diff, BASE/head SHA, тестовых входов, отсутствия скрытых side effects и приведённых UNKNOWN.

Установка на Intel **не выполнялась и не разрешена этим отчётом**. Если владелец позже отдельно разрешит CC-only rollout, preconditions: exact reviewed head, backup фактически установленных файлов, побайтовая SHA-сверка, совместимость launcher/dependencies/state, штатные pins/ACL/SID и bounded READONLY postflight. Никаких пробных сделок, ARM/rearm или Task mutations ради приёмки.

Откат этой подготовки до Merge — закрытие Draft PR/удаление только своей remote ветки по решению владельца; production менять не требуется. Откат после возможного будущего установленного изменения — отдельная авторизованная CC-only процедура восстановления точных сохранённых installed bytes, без изменения V20/FINAM/Tasks. Неизвестный результат любой записи не повторять вслепую.

**Следующий разрешённый шаг:** один Draft PR с exact BASE/head, результатами и skips, затем STOP до независимого ревью и решения владельца. `HANDOFF_ACCEPTED`, CI SUCCESS или review сами по себе не означают MERGED, INSTALLED, LIVE_PASS или FINAM SLTP PASS.
