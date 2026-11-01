# A3: feature-set ablations

Settings: Isolation Forest with all five seeds (mean±sd over seeds, sd with n-1). **LOF and One-Class SVM were run with seed 42 only** (single value). Budgets 15%/20% of the disk. Targets: img1 = 7, img2 = 19, img3 = 34.

## (a) drop-one: clean minus a single feature

Cells are the change in targets caught (removed minus full clean) at 15% / 20%. IF = seed mean over 5 seeds; LOF and OCSVM = seed 42. Last column lists disks where IF recall goes UP when the feature is removed (the protocol's drop criterion).

| feature removed | IF img1 | IF img2 | IF img3 | LOF img1 | LOF img2 | LOF img3 | OCSVM img1 | OCSVM img2 | OCSVM img3 | IF raises on |
|---|---|---|---|---|---|---|---|---|---|---|
| delta_mc | +0.0/+0.0 | +0.0/+0.2 | +0.8/+2.0 | -1/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+1 | img2, img3 |
| delta_mb | +0.0/+0.0 | +0.0/+0.0 | +1.2/+3.0 | -1/-1 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | img3 |
| delta_ab | +0.0/+0.2 | +0.0/+0.2 | +2.4/+3.2 | +1/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+1 | img1, img2, img3 |
| delta_si_fn | +0.0/+0.0 | +0.0/+0.2 | +1.6/+3.0 | -1/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | img2, img3 |
| m_before_cr | +0.0/+0.0 | -0.6/+0.2 | +1.6/+2.0 | +0/-1 | -1/-1 | -4/-2 | +0/-1 | +0/+0 | +1/+1 | img2, img3 |
| zero_size_recent | +0.0/+0.0 | +0.0/+0.0 | +0.6/+1.6 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | img3 |
| after_hours_touch | +0.0/+0.0 | +0.0/+0.0 | +0.8/+3.2 | +1/+0 | -1/-1 | +0/+2 | +0/+0 | +0/+0 | +1/+1 | img3 |
| size | +0.0/+0.0 | -0.6/+0.8 | -8.0/-4.6 | -2/-1 | +0/+3 | +0/+2 | +0/+0 | +0/+0 | +0/+0 | img2 |
| is_exe | +0.0/+0.0 | +0.0/+0.8 | +1.4/+2.2 | -1/+0 | +0/+0 | +0/-3 | +0/-1 | +0/+0 | +0/+1 | img2, img3 |
| is_archive | +0.0/+0.0 | +0.0/+0.2 | +0.0/+1.2 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | +0/+0 | img2, img3 |
| is_script | +0.0/+0.0 | +0.0/+0.4 | +1.4/+2.2 | +0/+0 | +0/+0 | +0/-1 | +0/+0 | +0/+0 | +0/+1 | img2, img3 |
| temp_path | +0.0/+0.0 | +0.0/+0.0 | +1.0/+2.0 | +0/+0 | +0/+0 | +1/+7 | +0/+0 | +0/+0 | +0/+0 | img3 |
| user_path | +0.0/+0.0 | -1.0/-0.8 | -21.6/-15.4 | +0/+0 | -2/+0 | +16/+15 | +0/+0 | -2/-2 | -21/-21 | - |
| path_depth | +0.0/+0.0 | +0.0/+0.0 | +0.4/+1.2 | +0/+0 | -1/+0 | +22/+18 | +0/-1 | -1/-1 | -15/-9 | img3 |
| filename_entropy | +0.0/+0.0 | +0.0/+0.4 | +0.6/+2.4 | +1/+1 | +4/+4 | +16/+15 | +1/+0 | +0/+0 | +1/+1 | img2, img3 |
| is_shortcut_or_trace | +0.0/+0.0 | -6.0/-0.6 | +0.8/+1.2 | +0/+0 | -4/+1 | +0/-3 | +0/+0 | -9/-9 | +0/+1 | img3 |
| per_file_prefetch_hit | +0.0/+0.0 | +0.0/+0.2 | +0.6/+1.2 | +0/+0 | -1/-1 | +0/+0 | -1/+0 | +0/+0 | +0/+0 | img2, img3 |

## (b) clean vs clean + burst

Burst candidates ['log_burst_count', 'log_burst_60s'] (counts of files sharing the same modified second / minute) added to the clean set; same models, same seeds.

**Image 1: XP Hacking (SCHARDT.001)** (7 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 6.0±0.0 | 6.0±0.0 | 24.6±3.5 | 24.6±3.5 | 5.0 | 6.0 | 37.2 | 37.2 | 6.0 | 7.0 | 18.9 | 18.9 |
| clean+burst | 7.0±0.0 | 7.0±0.0 | 12.4±1.6 | 12.4±1.6 | 4.0 | 5.0 | 35.7 | 35.7 | 6.0 | 6.0 | 29.4 | 29.4 |

**Image 2: Win7 Data Leakage** (19 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 18.0±0.0 | 18.0±0.0 | 9.3±2.0 | 21.9±1.3 | 8.0 | 8.0 | 52.9 | 62.4 | 19.0 | 19.0 | 1.9 | 4.6 |
| clean+burst | 19.0±0.0 | 19.0±0.0 | 9.8±2.5 | 12.9±0.7 | 5.0 | 8.0 | 88.2 | 93.2 | 19.0 | 19.0 | 2.0 | 2.7 |

**Image 3: Win10 Lone Wolf** (34 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 28.2±1.5 | 30.8±2.2 | 19.9±2.9 | 21.6±3.2 | 8.0 | 12.0 | 76.7 | 82.7 | 24.0 | 24.0 | 52.0 | 74.8 |
| clean+burst | 32.4±1.9 | 34.0±0.0 | 13.2±1.7 | 16.2±1.5 | 15.0 | 19.0 | 43.3 | 84.0 | 24.0 | 25.0 | 39.4 | 79.3 |

IF change with burst (targets at 15% / 20%): img1 +1.0/+1.0; img2 +1.0/+1.0; img3 +4.2/+3.2.
Raises on: img1, img2, img3. Lowers on: none. Protocol rule (raise on >=1 disk and lower on none; a disk that goes up at one budget and down at the other counts as lowering): **PASS**.

## (c) Protocol rules and the final feature set

Rule: a feature is kept only if removing it does not raise IF seed-mean recall at 15% or 20% on any disk. Burst enters only if it raises recall on at least one disk and lowers it on none.

| feature | decision | removal raises recall on | change when removed (at15/at20) |
|---|---|---|---|
| delta_mc | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.2; img3 +0.8/+2.0 |
| delta_mb | DROP | img3 | img1 +0.0/+0.0; img2 +0.0/+0.0; img3 +1.2/+3.0 |
| delta_ab | DROP | img1, img2, img3 | img1 +0.0/+0.2; img2 +0.0/+0.2; img3 +2.4/+3.2 |
| delta_si_fn | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.2; img3 +1.6/+3.0 |
| m_before_cr | DROP | img2, img3 | img1 +0.0/+0.0; img2 -0.6/+0.2; img3 +1.6/+2.0 |
| zero_size_recent | DROP | img3 | img1 +0.0/+0.0; img2 +0.0/+0.0; img3 +0.6/+1.6 |
| after_hours_touch | DROP | img3 | img1 +0.0/+0.0; img2 +0.0/+0.0; img3 +0.8/+3.2 |
| size | DROP | img2 | img1 +0.0/+0.0; img2 -0.6/+0.8; img3 -8.0/-4.6 |
| is_exe | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.8; img3 +1.4/+2.2 |
| is_archive | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.2; img3 +0.0/+1.2 |
| is_script | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.4; img3 +1.4/+2.2 |
| temp_path | DROP | img3 | img1 +0.0/+0.0; img2 +0.0/+0.0; img3 +1.0/+2.0 |
| user_path | keep | - | img1 +0.0/+0.0; img2 -1.0/-0.8; img3 -21.6/-15.4 |
| path_depth | DROP | img3 | img1 +0.0/+0.0; img2 +0.0/+0.0; img3 +0.4/+1.2 |
| filename_entropy | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.4; img3 +0.6/+2.4 |
| is_shortcut_or_trace | DROP | img3 | img1 +0.0/+0.0; img2 -6.0/-0.6; img3 +0.8/+1.2 |
| per_file_prefetch_hit | DROP | img2, img3 | img1 +0.0/+0.0; img2 +0.0/+0.2; img3 +0.6/+1.2 |

Features failing the rule (candidates to drop): ['delta_mc', 'delta_mb', 'delta_ab', 'delta_si_fn', 'm_before_cr', 'zero_size_recent', 'after_hours_touch', 'size', 'is_exe', 'is_archive', 'is_script', 'temp_path', 'path_depth', 'filename_entropy', 'is_shortcut_or_trace', 'per_file_prefetch_hit']. Burst: included.

**FINAL set (3 features)**: user_path, log_burst_count, log_burst_60s.

Note: each feature was tested by removing it alone from the full clean set; all failing features are dropped together, so the combined effect is checked directly by scoring the FINAL set below rather than assumed.

**Image 1: XP Hacking (SCHARDT.001)** (7 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 6.0±0.0 | 6.0±0.0 | 24.6±3.5 | 24.6±3.5 | 5.0 | 6.0 | 37.2 | 37.2 | 6.0 | 7.0 | 18.9 | 18.9 |
| FINAL | 0.0±0.0 | 1.0±0.0 | 40.2±0.0 | 40.2±0.0 | 3.0 | 5.0 | 24.9 | 24.9 | 0.0 | 0.0 | 94.9 | 94.9 |

**Image 2: Win7 Data Leakage** (19 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 18.0±0.0 | 18.0±0.0 | 9.3±2.0 | 21.9±1.3 | 8.0 | 8.0 | 52.9 | 62.4 | 19.0 | 19.0 | 1.9 | 4.6 |
| FINAL | 18.0±0.0 | 18.0±0.0 | 8.5±0.9 | 34.6±2.0 | 14.0 | 18.0 | 16.8 | 45.6 | 15.0 | 15.0 | 34.5 | 40.2 |

**Image 3: Win10 Lone Wolf** (34 targets)

| set | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | LOF knee % | LOF plateau % | OCSVM at15 | OCSVM at20 | OCSVM knee % | OCSVM plateau % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| clean | 28.2±1.5 | 30.8±2.2 | 19.9±2.9 | 21.6±3.2 | 8.0 | 12.0 | 76.7 | 82.7 | 24.0 | 24.0 | 52.0 | 74.8 |
| FINAL | 34.0±0.0 | 34.0±0.0 | 3.4±0.5 | 4.4±0.3 | 11.0 | 11.0 | 24.6 | 24.6 | 4.0 | 5.0 | 49.6 | 59.0 |

FINAL minus clean, IF targets at 15%/20%: img1 -6.0/-5.0; img2 +0.0/+0.0; img3 +5.8/+3.2.

Caveat, reported as found: the rule counts any increase of the seed mean (even +0.2 of a target) on any disk as a raise, and on img3 removing almost any single feature raises recall (the 17-feature model is diluted there). Applied mechanically, the rule therefore keeps only 1 of 17 clean features. The FINAL set is not uniformly better: see the img1 and the LOF/OCSVM columns above. Nothing was re-tuned after seeing this.
