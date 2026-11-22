# R7 source-audit utilities — retained from historical Draft #581

**Status (22.11.2026): STAGED FOR REVIEW / SYNTHETIC TESTS ONLY / NO LIVE.** These two standalone utilities and their tests were copied without byte changes from [historical PR #581](https://github.com/alkospacer123/market-pattern-discovery/pull/581), commit `94be1d88913adcb3efb0f72676c331b168ad97a4`. No original source code, H1/M15 research, archives, or operator tasks are modified.

## Original blob IDs and role

| File | Original Git blob SHA | Role |
| --- | --- | --- |
| `r7_dependency_scan.py` | `edd407d56b46e2e396da6a3d1853d09445a3c044` | Read-only text and Git-index inventory of historic path references; **not** dependency closure |
| `r7_git_checkpoint.py` | `cbef060072b359a02df0477dddf69d6fb0dac0c6` | Creates mirror, bundle and independent **Git-only** restore/checkpoint in a **new** destination; **NOT** final disaster recovery |
| `tests/test_r7_dependency_scan.py` | `3f35238fb52b80e688d43dccacf7d665bcf7c55a` | Temporary synthetic Git repo tests |
| `tests/test_r7_git_checkpoint.py` | `67333a50bc66e84ead2ab32299ce1defdbc748e5` | Temporary synthetic mirror/bundle tests |

The older `r7_cc_scope_guard.py` is **not copied**: its pin `f15d565...`, historical A/B/C removal scope, and frozen CC tree rules do not represent post-R7 main.

## Safe testing

Use disposable CI/isolated checkout only; no FINAM credentials, installed Windows roots, Scheduled Tasks, LIVE orders or broker connectivity:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s recovery/tools/tests -p 'test_r7_dependency_scan.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s recovery/tools/tests -p 'test_r7_git_checkpoint.py' -v
```

`r7_dependency_scan.py` classifies `research_domains.md` as a legacy path even though it is a **retained archive pointer** in post-R7 main; its count is **not** proof that the removed platform still exists. Its scanned matches may be provenance. It does **not** establish dynamic/external consumer safety; large/binary files may be skipped.

`r7_git_checkpoint.py` is **not executed against the real GitHub repo or any external drive by this PR**. Its real-run destination must be a deliberately selected fresh isolated location and requires separate operator approval. Mirror/bundle/checkout are not the independent 10–30 year V20/CC/TRL Recovery: they omit private Intel state, SQLite, DPAPI, TRL original archives and GitHub PR/Issues/CI metadata. Final backup and cold restore occur only **after Kimi Chat+Code acceptance**.

All historical source links remain available in PR #581 until disposition is reviewed. **Do not merge #581 as-is or execute its other historical A/B/C/H1/M15 cleanup scripts.**
