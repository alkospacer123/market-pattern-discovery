# CC-03 FINAM READONLY immutable broker snapshot — draft implementation

Status: **code only**; never assume installed/activated on Intel. Strictly ControlCenter/.
No merge, no live H1/M15 source access, no Task operations, no trading, no polling.

## Verified starting point

2026-10-20 13:51:25Z: authorized Intel FINAM REAL_READONLY probe **PASS**:
session.readonly=true, permitted account confirmed, 4 N4 quantities 0, 0 account order
rows, 0 active and 0 active SLTP rows, 0 other nonzero instruments. This is a **single
broker endpoint response**. FINAM did not supply an original snapshot clock; original
broker time, full-account pagination/completeness, H1 ownership, fills, stop-position
linkage, PnL and engine health remain **UNKNOWN/UNVERIFIED**. The result was not
published or installed into Streamlit.

Windows CI #39432322512 succeeded for the previous operator-only probe source;
the original operator script hash remains
`33668f23c7ffb774e198b4f7ef55c85d73a6d407cd84b2a3cb1ea5bd6a97fc7c`.

## New minimal bridge

1. `broker_readonly/publish-from-one-shot.ps1` is **operator-side** and PREVIEW by
   default. Only `-execute` calls the existing exact-hash script once. It requires
   REAL_READONLY DPAPI current Windows principal, verifies original probe's bounded
   redacted output, PINs the encrypted DPAPI blob *hash*, and writes **only**
   a small redacted immutable JSON in `C:\Control Center\data\broker-readonly`.
   It does not send network requests itself, edit H1, touch SQLite/WAL/heartbeat,
   restart tasks or submit/cancel orders. No stdout secret/token/account number.
2. The output directory must **already exist**, on local NTFS, no reparse points,
   owned by Administrators/SYSTEM with no write-capable DACL entries for untrusted
   principals (including ccpanel). The publisher refuses creation/ACL changes.
   It writes a uniquely named temp file, flushes/closes it and atomically moves to
   `h1-<20 digits>-<32 hex>-<sha256>.json`; existing completed files are never
   replaced. Publication errors fail closed; no trading state touched.
3. `cc/providers/h1_broker_snapshot.py` is a receiver, **never a broker client**.
   It reads only completed CC files, with native Windows root identity pin and
   digest verification. Admin-owned `deployment/broker-readonly-policy.json` must
   separately pin `export_root_id`, principal SID hash, DPAPI blob hash,
   exact source script hash and TTL 30–600s, and set `source_approved=true`.
   The .example policy is deliberately **false** and cannot activate anything.
   It must be installed using a separately verified physical Intel policy/ACL process.
4. Streamlit's existing manual `Обновить данные` click, in
   `WINDOWS_OS_ONLY` only, independently reads that accepted completed snapshot
   in one attempt. No FINAM token, DPAPI, network request or shell process can
   be reached from the UI. Before physical policy acceptance the broker section
   says UNKNOWN. After accepting a current source it shows **raw observed counts**
   with FINAM REAL_READONLY provenance and received-at time. Cached data expires,
   cannot revert from STALE to CURRENT without another click, and never becomes
   H1 HEALTHY, broker-complete, confirmed-flat or stop-protected.
   All 10 trading controls stay disabled.

## Physical rollout gates (NOT executed)

- Verify current PR CI success and compare exact installed package/manifest hashes,
  protected H1 and M15 files, tasks, owner and listener before any deployment.
- Under Windows administrator, separately provision the dedicated broker snapshot
  directory with admin/SYSTEM ownership, ccpanel **READ ONLY** and no untrusted
  write permissions, without changing `C:\TradingSystemLab`.
- Deploy reviewed ControlCenter-only package and preserve the working panel;
  do not restart or reconfigure the panel before the approved package switch.
- Under the *same previously authorized REAL_READONLY principal*, verify the
  publisher's SHA256 and preview and perform one operator-approved `-execute`
  when needed to publish a current observation. Each execution initiates one new
  FINAM readonly session/details/account/orders lookup; it is **not** the previously
  completed lookup and requires matching operational authorization.
- Independently verify owner/NTFS ACL and physical file ID tuple
  (`volume,index_high,index_low`) using the existing Windows native read helper.
  Write the actual admin-owned `broker-readonly-policy.json`, exact fingerprints
  from the *approved* broker observation and bounded TTL; never auto-trust output
  solely because its shape validates. Do not expose the encrypted blob or FINAM
  token to Streamlit. Verify physical click, timeout, expiry, owner/SID and
  immutable content hash. Leave policy unapproved if any check fails.
- H1 trading account ownership requires **separate independent evidence**.
  A local DPAPI principal/production ID alone does not prove that H1 is assigned
  that broker account. Stop coverage needs position/order-side/quantity/SLTP broker
  reconciliation; aggregate SLTP row count alone is insufficient.

## Scope

No trading source modifications, no M15 integration, no live broker request from
Streamlit, no new background service, no new controls, no automatic polling or
FINAM trade credentials. All work stays inside CC-03 issues #524 and #550.
