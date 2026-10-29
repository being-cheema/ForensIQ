# Protocol amendment 1: choice of the final feature set

Written after ablation A3 and before any explainability (B) or remediation (C) result for v3 was computed.

## What happened
PROTOCOL.md rule A3 said: "a feature is kept only if removing it does not raise recall on any disk at 15% or 20%."
Applied as written (all failing features removed at once), it removed 16 of 17 clean features and left
`user_path, log_burst_count, log_burst_60s`. That set is degenerate: on img1 it falls from 6 to 0 targets at 15%.

The rule was flawed, not the data:
- Single-feature removals are not additive. Each was tested alone; removing all of them together was never tested by the rule.
- Most of the "raises" were within seed noise (e.g. +0.2 of a target in a 5-seed mean), and no tolerance was set.

So rule A3(b) is reported as **FAILED (degenerate result)**. Its drop-one table is kept unchanged in A3/summary.md as a sensitivity result.

## What is used instead
The final set is **clean + burst** (19 features: the 17 clean features plus `log_burst_count`, `log_burst_60s`).
This is the outcome of the other pre-registered A3 rule, which passed as written: burst raises Isolation Forest recall
on img1, img2 and img3 and lowers it on none. No feature was added or removed for any other reason.

All reliability ablations (A1, A2, A4, A5, A6, A7) were re-run on the final set (reports/study_v3/final/). The clean-set
runs (reports/study_v3/A*) are kept as the step before burst was added. The explainability and remediation studies use only the final set.
