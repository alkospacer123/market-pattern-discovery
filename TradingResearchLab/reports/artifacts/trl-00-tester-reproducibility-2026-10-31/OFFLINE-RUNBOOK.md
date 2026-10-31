# Offline runbook — TRL-00.2, 2026-10-31

Это воспроизведение неизменённого существующего тестера, без новых правил стратегии. Рабочая директория — `/workspace`. Исходный code SHA — `9457da1f49578f940859a678d20b3c4f505bc394`; data SHA — `f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8`. В checkout discovery должен быть доступен также reference commit `7927d3d6b465ec1bceae51ec8121def5e7c7e191`.

Каталоги `run1/`, `run2/` должны быть новыми/пустыми. При переносе заменить абсолютные пути согласованно; не направлять output в исходный пакет или production. Python — 3.12.14. Подготовка зависимостей может использовать сеть; все replay ниже выполняются с запрещённой сетью.

## Подготовка

```bash
mkdir -p /workspace/work/trl-00-2/{source,run1,run2,tmp}
git -C /workspace/market-pattern-discovery archive \
  9457da1f49578f940859a678d20b3c4f505bc394 \
  IntradayLab/t3_m15_forever_v1 \
  | tar -x -C /workspace/work/trl-00-2/source
chmod -R a-w /workspace/work/trl-00-2/source
python -m venv /workspace/work/trl-00-2/venv
/workspace/work/trl-00-2/venv/bin/python -m pip --disable-pip-version-check install \
  numpy==2.3.5 pandas==2.2.3 python-dateutil==2.9.0.post0 \
  pytz==2026.3.post1 tzdata==2026.3 six==1.17.0
```

Требуется Linux с `libseccomp.so.2`. Следующий вспомогательный guard — только запрет сетевых syscalls перед `exec`, без изменения исследовательского кода. Сохранить буквально как `/workspace/work/trl-00-2/offline_exec.py`; SHA256 проверенного guard указан в `VERIFICATION.json`.

```python
"""Execution environment guard only: deny network syscalls, then exec unchanged code."""
import ctypes
import errno
import os
import sys

lib = ctypes.CDLL('libseccomp.so.2', use_errno=True)
lib.seccomp_init.argtypes = [ctypes.c_uint32]
lib.seccomp_init.restype = ctypes.c_void_p
lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
lib.seccomp_rule_add.restype = ctypes.c_int
lib.seccomp_load.argtypes = [ctypes.c_void_p]
lib.seccomp_load.restype = ctypes.c_int
lib.seccomp_release.argtypes = [ctypes.c_void_p]
ctx = lib.seccomp_init(0x7fff0000)
assert ctx, 'seccomp_init failed'
for name in (b'socket', b'socketpair', b'connect'):
    nr = lib.seccomp_syscall_resolve_name(name)
    assert nr >= 0, name
    assert lib.seccomp_rule_add(ctx, 0x00050000 | errno.EPERM, nr, 0) == 0, name
assert lib.seccomp_load(ctx) == 0, 'seccomp_load failed'
lib.seccomp_release(ctx)
os.execv(sys.argv[1], sys.argv[1:])
```

Проверка запрета: создание socket обязано завершиться `PermissionError: [Errno 1] Operation not permitted`, без обращения к внешнему хосту.

```bash
python /workspace/work/trl-00-2/offline_exec.py \
  /workspace/work/trl-00-2/venv/bin/python -c 'import socket; socket.socket()'
```

## Два одинаковых исторических запуска

Ниже та же последовательность аргументов и окружение, которые использованы в проверке. Различается только `--output`. В фактическом исполнении внешний Python-оркестратор также сохранил elapsed/exit/stdout/stderr в `VERIFICATION.json`; он не рассчитывает стратегию.

```bash
for run in run1 run2; do
  PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/work/trl-00-2/tmp \
  python /workspace/work/trl-00-2/offline_exec.py \
    /workspace/work/trl-00-2/venv/bin/python \
    /workspace/work/trl-00-2/source/IntradayLab/t3_m15_forever_v1/research.py \
    --data-root /workspace/market-pattern-data \
    --reference-root /workspace/market-pattern-discovery \
    --output "/workspace/work/trl-00-2/$run" \
    > "/workspace/work/trl-00-2/$run.stdout.log" \
    2> "/workspace/work/trl-00-2/$run.stderr.log" || exit 1
done
```

Ожидаемый stdout **каждого**: `{"Gate_A": "PASS", "artifacts": 17, "trades": 1442}`. Exit 0, stderr пуст. Один только exit 0 недостаточен: необходимо проверить gates, хеши и соответствие эталону.

## Существующие проверки и отдельный алгоритмический аудит

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/work/trl-00-2/tmp \
python /workspace/work/trl-00-2/offline_exec.py \
  /workspace/work/trl-00-2/venv/bin/python \
  -m unittest discover \
  -s /workspace/work/trl-00-2/source/IntradayLab/t3_m15_forever_v1 \
  -p 'test_*.py' -v

PYTHONDONTWRITEBYTECODE=1 TMPDIR=/workspace/work/trl-00-2/tmp \
python /workspace/work/trl-00-2/offline_exec.py \
  /workspace/work/trl-00-2/venv/bin/python \
  /workspace/work/trl-00-2/source/IntradayLab/t3_m15_forever_v1/audit.py \
  --data-root /workspace/market-pattern-data \
  --output /workspace/work/trl-00-2/run1
```

Ожидается 14 tests / OK; аудит — `status=PASS`, 1442 closed, 2 open, 482 report rows, 17 hashes. Аудит проверяет отдельную реализацию; внешний reviewer остаётся PENDING.

## Проверка byte parity

Этот фрагмент только сравнивает контрольные суммы уже существующих результатов, не выполняет торговую симуляцию.

```python
import hashlib
import json
from pathlib import Path

reference = Path('/workspace/market-pattern-discovery/IntradayLab/t3_m15_forever_v1')
run1 = Path('/workspace/work/trl-00-2/run1')
run2 = Path('/workspace/work/trl-00-2/run2')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
expected = json.loads((reference / 'ARTIFACT_SHA256.json').read_text())
assert len(expected) == 17
for name, digest in expected.items():
    assert sha(run1 / name) == sha(run2 / name) == sha(reference / name) == digest
assert sha(run1 / 'ARTIFACT_SHA256.json') == sha(run2 / 'ARTIFACT_SHA256.json') == sha(reference / 'ARTIFACT_SHA256.json')
assert sha(run1 / 'AUDIT_RESULTS.json') == sha(reference / 'AUDIT_RESULTS.json')
manifest = json.loads((run1 / 'SOURCE_MANIFEST.json').read_text())
for row in manifest['sources'] + manifest['historical_quarter_sources']:
    assert sha(Path('/workspace/market-pattern-data') / row['path']) == row['full_sha256']
print('PASS: 17 artifacts, inventory, audit and 16 source checksums')
```

## Сохранённые доказательства

- `SOURCE_MANIFEST.json`: исходный неизменённый manifest выбранного runner, все 16 входов, префиксы, Git blob SHA, старые reference SHA и версия основных зависимостей.
- `VERIFICATION.json`: проверяемый code SHA, фактические команды/окружение/логи, тройные хеши 17 результатов, повторный контроль исходников/данных, сетевой guard и 14 tests.
- `METRICS.csv`: выборка инструментальных и годовых строк существующих отчётов обоих запусков, без исходных свечей и без нового расчёта торговой логики.
- `REPRODUCTION_DETAIL.json`: существующий результат сверки 425 + 401 старых эталонных сделок.
- `AUDIT_RESULTS.json`: результат свежего запуска существующего отдельного алгоритмического аудита.
- `OPEN_POSITIONS.json`: две незакрытые позиции, исключённые из закрытых метрик.

Полный trade ledger не дублируется: он уже опубликован в исходном пакете; его ожидаемый SHA256 зафиксирован в `VERIFICATION.json`. Исходные котировки находятся только во внешнем репозитории данных. PASS относится к техническому воспроизведению этой связки; условия C1/Close fills/неполной истории и OOS-ограничения см. в [отчёте](../../TRL-00-TESTER-REPRODUCIBILITY-2026-10-31.md).
