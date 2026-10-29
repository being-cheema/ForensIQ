# A1: feature-group ablation

Which of the three feature groups of the clean set do the results depend on? Each group is tested alone (only that group) and removed (everything except that group), on all three disks.

Settings: Isolation Forest (200 trees, sample 256) with all five seeds, reported as mean±sd over seeds (sd with n-1). **LOF and One-Class SVM were run with seed 42 only** (single value, no sd). Budgets 15% and 20% of the disk; knee = smallest budget (% of disk) reaching >=90% of targets; plateau = budget at which the last target is reached. Targets: img1 = 7, img2 = 19, img3 = 34.

Groups (clean set): Temporal = 7 feature(s) (delta_mc, delta_mb, delta_ab, delta_si_fn, m_before_cr, zero_size_recent, after_hours_touch); Path/File = 9 feature(s) (size, is_exe, is_archive, is_script, temp_path, user_path, path_depth, filename_entropy, is_shortcut_or_trace); Execution/Activity = 3 feature(s) (per_file_prefetch_hit, log_burst_count, log_burst_60s).

## Image 1: XP Hacking (SCHARDT.001) (7 targets, 11,773 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 19 | 7.0±0.0 | 7.0±0.0 | 12.4±1.6 | 12.4±1.6 | 4.0 | 5.0 | 6.0 | 6.0 |
| only Temporal | 7 | 6.0±0.0 | 6.6±0.5 | 19.8±0.8 | 19.8±0.8 | 6.0 | 6.0 | 1.0 | 1.0 |
| all except Temporal | 12 | 7.0±0.0 | 7.0±0.0 | 11.2±0.8 | 11.2±0.8 | 1.0 | 3.0 | 7.0 | 7.0 |
| only Path/File | 9 | 4.4±0.9 | 5.8±0.4 | 34.1±1.1 | 34.1±1.1 | 2.0 | 3.0 | 6.0 | 7.0 |
| all except Path/File | 10 | 7.0±0.0 | 7.0±0.0 | 12.9±1.0 | 12.9±1.0 | 2.0 | 4.0 | 5.0 | 5.0 |
| only Execution/Activity | 3 | 4.0±0.0 | 4.0±0.0 | 38.6±0.0 | 38.6±0.0 | 3.0 | 5.0 | 4.0 | 4.0 |
| all except Execution/Activity | 16 | 6.0±0.0 | 6.0±0.0 | 24.7±1.2 | 24.7±1.2 | 5.0 | 6.0 | 5.0 | 7.0 |

## Image 2: Win7 Data Leakage (19 targets, 85,017 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 19 | 19.0±0.0 | 19.0±0.0 | 9.8±2.5 | 12.9±0.7 | 5.0 | 8.0 | 19.0 | 19.0 |
| only Temporal | 7 | 4.8±0.8 | 5.6±0.5 | 66.4±2.3 | 66.4±2.3 | 4.0 | 7.0 | 12.0 | 12.0 |
| all except Temporal | 12 | 19.0±0.0 | 19.0±0.0 | 4.2±0.5 | 4.9±0.8 | 10.0 | 12.0 | 19.0 | 19.0 |
| only Path/File | 9 | 19.0±0.0 | 19.0±0.0 | 7.9±0.8 | 12.4±1.6 | 7.0 | 9.0 | 19.0 | 19.0 |
| all except Path/File | 10 | 11.2±0.4 | 12.6±2.1 | 27.6±3.0 | 37.3±4.5 | 4.0 | 7.0 | 7.0 | 7.0 |
| only Execution/Activity | 3 | 17.0±0.0 | 17.0±0.0 | 32.8±3.8 | 48.0±3.6 | 9.0 | 17.0 | 6.0 | 6.0 |
| all except Execution/Activity | 16 | 18.0±0.0 | 18.2±0.4 | 10.0±1.3 | 20.8±1.0 | 7.0 | 7.0 | 19.0 | 19.0 |

## Image 3: Win10 Lone Wolf (34 targets, 166,110 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 19 | 32.4±1.9 | 34.0±0.0 | 13.2±1.7 | 16.2±1.5 | 15.0 | 19.0 | 24.0 | 25.0 |
| only Temporal | 7 | 16.4±2.2 | 20.0±0.0 | 75.0±0.7 | 75.0±0.7 | 26.0 | 26.0 | 2.0 | 17.0 |
| all except Temporal | 12 | 34.0±0.0 | 34.0±0.0 | 8.4±1.5 | 10.2±1.6 | 9.0 | 12.0 | 25.0 | 26.0 |
| only Path/File | 9 | 34.0±0.0 | 34.0±0.0 | 9.9±0.6 | 12.2±1.4 | 7.0 | 10.0 | 33.0 | 33.0 |
| all except Path/File | 10 | 19.8±0.8 | 21.6±3.0 | 36.7±5.5 | 45.7±1.2 | 23.0 | 23.0 | 5.0 | 18.0 |
| only Execution/Activity | 3 | 32.2±0.4 | 32.2±0.4 | 8.0±2.2 | 25.2±1.8 | 4.0 | 4.0 | 2.0 | 2.0 |
| all except Execution/Activity | 16 | 28.8±0.4 | 32.0±1.9 | 19.1±1.6 | 20.9±2.2 | 8.0 | 12.0 | 24.0 | 24.0 |

## Pass rules (PROTOCOL A1)

Evaluated on IF seed means. "Lowers recall" = removing the group gives a lower mean at 15% or at 20% on at least one disk.

| group | removal lowers recall on | change at15,at20 when removed (targets) | group alone matches full set on all disks |
|---|---|---|---|
| Temporal | none | img1: +0.0,+0.0 / img2: +0.0,+0.0 / img3: +1.6,+0.0 | no |
| Path/File | img2, img3 | img1: +0.0,+0.0 / img2: -7.8,-6.4 / img3: -12.6,-12.4 | no |
| Execution/Activity | img1, img2, img3 | img1: -1.0,-1.0 / img2: -1.0,-0.8 / img3: -3.6,-2.0 | no |

- Rule 1 (every group's removal lowers recall on >=1 disk): **FAIL**
- Rule 2 (no single group alone matches the full set on all disks): **PASS**
- A1 overall: **FAIL**
