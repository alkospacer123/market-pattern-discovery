# Historical Strategy Registry v1

The Historical Strategy Registry is a deterministic, read-only projection of
the append-only research memory. It enriches each candidate with its market
scope, research lineage, latest evaluation snapshot, and complete lifecycle
event sequence. It does not recalculate performance or alter candidate state.

The projection is ordered by candidate ID and carries a deterministic content
signature. Rebuilding it from identical memory therefore produces identical
content. Missing evaluations remain explicit `null` values rather than being
invented. TRUE OOS data is neither required nor read by this projection.
