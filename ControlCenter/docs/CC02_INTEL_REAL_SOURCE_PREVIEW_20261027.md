# CC-02: Intel real V20 READONLY source preview — 27.10.2026

Source: operator-supplied Intel PowerShell output in the Control Center project conversation. This is **physical operator evidence**, not an independent machine-side check by GitHub, and not a broker reconciliation proof.

```text
cc02_v20-shallow=HALTED task=RUNNING switch=HALTED cycles=2970 events=10
cc02_v20-obv=HALTED task=RUNNING switch=HALTED cycles=2919 events=10
cc02_v20-inside=HALTED task=RUNNING switch=HALTED cycles=2974 events=10
cc02_export=PREVIEW_NO_WRITE
cc02_no_finam_no_task_mutation_no_arm=YES
cc02_intel_readonly_preview=PASS_NO_WRITE
```

Pinned successful native Windows CI: #40509513703, `completed/success`, exact source HEAD `a379a919ec0c26e8baf40cce8c39b1b0f573d915`.

**Accepted:** three isolated real worker log sources; fresh 10 event attempts each; Windows Tasks RUNNING and Kill Switch HALTED at observation; safe preview without publishing or arming. These counts are JSONL *worker attempts*, **not** broker trades or H1 durable production cycles.

**Still not accepted:** local CC-owned snapshot publication, root identity pin, local admin-owned NTFS policy and effective SID read, live Streamlit refresh on 8502, independently observed FINAM positions/stops, and actual START/STOP/RESTART controls. Existing UI buttons stay disabled.

**Next:** inspect actual installed panel/source/NTFS paths on Intel in READONLY mode. Provision only approved CC-owned root and policy after path/ACL acceptance; publish scrubbed JSON and validate Streamlit's manual read. Nothing under V20, TradingSystemLab, IntradayLab, their runtime, Tasks, tokens or FINAM may be written. V20 remains HALTED; do not invoke `-mode start` or `-mode restart` before separately approved ARM.
