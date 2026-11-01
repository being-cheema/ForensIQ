# ForensIQ study v3: pre-registered protocol

Written before any v3 result was computed. Every number reported for v3 comes from the scripts in this
study and is judged against the pass rules below, fixed in advance.

## Fixed settings
- Disks: img1 (XP hacking, SCHARDT.001), img2 (Win7 data leakage), img3 (Win10 Lone Wolf).
- Artifacts: runs/imgN/artifacts (extracted from the raw images).
- Seeds: 42, 1337, 9999, 7, 2024 (the same five used in every earlier study).
- Budgets: 0-100% of the disk in 0.5% steps; headline budgets 15% and 20%.
- Models: Isolation Forest (200 trees, sample 256), LOF (k=20), One-Class SVM (rbf, nu=0.05, 10,000-row fit sample).
- Feature set: `clean` (Phase 1 result, frozen once built).
- Ground truth: the target lists in multimodel_eval.py, unchanged. Ground truth is used only to score, never to build features.

## Metrics
- Targets caught at a budget (a target counts if any of its files is in the top K).
- Knee: smallest budget reaching >= 90% of targets. Plateau: smallest budget reaching the last target.
- Precision at budget (targets' files / K). Mean and standard deviation over the 5 seeds for everything stochastic.

## Pass rules (decided in advance)
- Reliability A2 (seeds): knee spread across seeds <= 2 percentage points, and the headline budget catches >= 90% of targets in every seed on every disk.
- Reliability A1 (groups): removing any single group lowers recall at the headline budget on at least one disk, and no single group alone matches the full set on all disks.
- Reliability A3 (feature sets): a feature is kept only if removing it does not raise recall on any disk at 15% or 20%. Burst features enter the clean set only if they raise recall on at least one disk and lower it on none.
- Reliability A4 (models): the chosen model must beat the best plain rule baseline at the headline budget on at least two of three disks.
- Reliability A5 (hyperparameters): headline recall changes by <= 1 target across the tested settings.
- Reliability A6 (cross-disk): a budget tuned on any one disk catches >= 90% of targets on the other two.
- Reliability A7 (robustness): with 10% of files dropped or 1-hour timestamp noise, headline recall drops by <= 10%.
- Explainability B1 (faithfulness): scrambling the SHAP top-3 features moves flagged files down the ranking more than scrambling 3 random features (one-sided Wilcoxon, p < 0.01).
- Explainability B2 (stability): mean Jaccard of top-3 reasons across seeds >= 0.7, and >= 0.6 under 1% input noise.
- Explainability B3 (planted attacks): SHAP's top-3 names the planted cause in >= 80% of planted files.
- Remediation C1: every recommendation cites at least one flagged file; precision of triggered indicators against the known scenario is reported for old (v1) and new (v2) triggers.

A failed rule is reported as failed. Nothing is re-tuned after seeing a result.
