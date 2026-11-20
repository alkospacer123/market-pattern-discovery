# TRL Journal — R055 — 12.11.2026

User corrected two assumptions: 60-second cancellation of the limit is not agreed or required, and existing stop is intended to cover 100% of the current position and must not be changed in TRL. Question: physical pullback versions (depth, duration, real opposing candles, ADX) and missed Classic trends.

R055 frozen 8 model families before historical evaluation. OctGO TP6+protect3 independent 45k: Classic 736/+208507 PF1.9614; physical one 590/+159640 PF1.895; deep 647/+187211 PF1.933; long 445/+129317 PF1.937; ADX 117/+23219 PF1.608. Outside Classic position overlaps deep +662 RUB and long +5211 RUB, no robust independent advantage; USD/CNY/IMOEX Nov9–10 no raw signals for any physical model. 3-account Classic+Deep+Inside profit +442224 PF1.937, closedDD17942 vs V20 +381608 PF1.845 DD11775 — risk increase, not approval.

Finam API includes LIMIT DAY, GTC, IOC, FOK; DAY retains unfilled quantity for returns without arbitrary timer. At 1449 frozen market entries, 1-tick favorable hypothetical passive LIMIT M15 later-touch 71.4% in hour vs 77.9% by session end before old trade exit, +95 extra late touches, NO real fill or expected return. Entry leftover must be canceled at position-close/stop/invalidation/end of session to prevent ghost re-entry; no changes to user SLTP. LIVE API quantity_sl behavior must be observed GET-only in separate LIVE project.

R055 complete workbook, report, autonomous ZIP with raw history/code, Journal; independent rerun 9 main CSV byte identical. OOS compromised; GO static; costs incomplete; GLD L2 unavailable.

Decision: NO_NEW_CORE_APPROVAL / LIMIT_DAY_FORWARD_CANDIDATE / LIVE_UNCHANGED.
