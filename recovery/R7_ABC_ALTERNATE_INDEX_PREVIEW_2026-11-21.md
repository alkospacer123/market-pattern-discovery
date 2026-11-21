# R7 / A+B+C — alternate Git index preflight (21.11.2026)

**Status:** exact preflight tool prepared; synthetic tests 8/8 PASS; full original-repo Intel check PENDING; no deletion approved.
Baseline commit `f15d565755b996252081ed49ed5a094ee1e8d820`; tree `44a5fef98dd8a3b6bc3e6d172f64fafddac5df4b`.

## Scope and expected evidence
Six A/B/C historic study+results directories contain **11,491 tracked paths / 4,159,859,038 logical bytes**. The checker loads a **temporary alternate Git index outside repo**, stages only exact hypothetical deletions and validates `11,491` `D` statuses and **6,948 unchanged SHA+mode**. No `git rm`, checkout, reset, push or commit, no runtime source imports, no FINAM/Windows Tasks.

- Source inventory SHA256: `f3868a4359662bf33804a50847288391a3336753b21e115b985b8f9a63853865`.
- Frozen study impact SHA256: `dbf18a8c07a3397b98a48f7184c7f1710f609d3c0840246425eb3726287692a2`.
- Exact candidate manifest SHA256: `2b42813f1a97882c5af8013641cb4f2edb1a5ff7a87512623453cf7486e33c56`.
- Git backup bundle SHA256: `09C596CF5E8268256AD4511DE5F28C5E8CA8A823F62867FC9ECF441534D15527`.
- Tool + manifest + tests package: `R7_ABC_Alternate_Index_Preview_v1_20261121.zip`; SHA256 `ebf6656cb87be24dcdcbe5f0bf9e4d2d10a7a0eaa56b6bf403e300d4a4755148`. Package delivered as conversation artifact, not committed in GitHub. Internal README gives PowerShell invocation. Check local ZIP hash before use.
- Synthetic fixture tests **8/8 PASS**, including protected-path rejection and unchanged original Git worktree/HEAD. This is not a real-repo result.

## Independent inspections of GitHub entrypoints
The `.github/workflows/` Git tree contains 3 workflows: `controlcenter-cc03-windows-native.yml`, `v20-08-live-windows.yml`, `v20-cap4-research.yml`. Inspected texts target V20/CC, not A/B/C module names. The root `pyproject.toml` still advertises old BBW script entrypoints and `market_pattern_discovery` validation commands. This makes whole-main entrypoint cleanup an independent later subtask; do not blindly delete BBW or shared `src/`.

## Before any removal or merge
1. Verify complete Git bundle SHA on a physically independent drive or SSD; checkpoint on the same Intel storage is insufficient.
2. Review dynamic imports, generated paths, tests, source/provenance and CI beyond literal A/B/C references.
3. Preserve historical frozen A/B/C reproducibility in the original tree; original B/C validation invokes git remote and cannot be treated as an air-gapped PASS without adaptation or isolated procedure.
4. Test disposable 6,948-file checkout and compare offline V20/CC/TRL/H1/M15 regressions, with FINAM/network/Windows Task interaction disabled.
5. Only after all PASS and separate approval: one actual large cleanup PR, no rewrites of Git history and no LIVE changes.

Archive branch ruleset #27793383 PASS: Active, exact ref, no deletions/updates/force push and no bypass. Main and archive commit unchanged when last inspected. **Preview is NOT deletion authorization.**
