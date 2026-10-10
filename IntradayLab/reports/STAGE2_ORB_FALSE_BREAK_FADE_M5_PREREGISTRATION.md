# ORB False-Break Fade M5 — pre-P&L freeze

Explicit user task supersedes historical queue/delay/3R instructions. Exactly A BASE, B ATR14, C completed M15, D both, four instruments, whole physical 2023. Machine authority: `../config/stage2_orb_false_break_fade_m5_v1.json`.

No economic replay executed before this commit. No tuning after P&L. Shared one-tick episodes consume the first side attempt even when a filter rejects it; thus filters never create another opportunity. ATR needs 15 contiguous bars for 14 paired TR, includes completed sweep. Parent is one completed clock-aligned M15 at reclaim close, cleared on gaps.

Signal at reclaim close; wait one entire subsequent M5; submit and model entry at its close / exact next Open. No T10/T15/FAST labels. Entry adapter receives Open only. Stop known before order; target 1.5 gross R outward grid. Max60 calendar minutes, flat at B-5 Open. No entry at B-5. Take touch is a conditional historical fill assumption; entry-bar Take forbidden. Intrabar outcomes reported as time intervals.

Missing scheduled entry or exposed bar retains UNKNOWN and fail-closed blocks further orders through 2023 end. No reconstruction or later favourable substitution. Annual metrics null on incomplete coverage; closed cohorts are diagnostic. Positive Volume is completed-bar validity only, never future entry admission.

Historical Cycle18 used M1 in 2026 and a grid; its selected survivor is provenance, not verification of this fixed 2023 M5 hypothesis. Only historical text was read. PR459 merged; PR460/461/462 remain excluded. New files only under IntradayLab. Stop at one Draft PR, external acceptance pending.
