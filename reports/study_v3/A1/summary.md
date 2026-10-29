# A1: feature-group ablation

Which of the three feature groups of the clean set do the results depend on? Each group is tested alone (only that group) and removed (everything except that group), on all three disks.

Settings: Isolation Forest (200 trees, sample 256) with all five seeds, reported as mean±sd over seeds (sd with n-1). **LOF and One-Class SVM were run with seed 42 only** (single value, no sd). Budgets 15% and 20% of the disk; knee = smallest budget (% of disk) reaching >=90% of targets; plateau = budget at which the last target is reached. Targets: img1 = 7, img2 = 19, img3 = 34.

Groups (clean set): Temporal = 7 feature(s) (delta_mc, delta_mb, delta_ab, delta_si_fn, m_before_cr, zero_size_recent, after_hours_touch); Path/File = 9 feature(s) (size, is_exe, is_archive, is_script, temp_path, user_path, path_depth, filename_entropy, is_shortcut_or_trace); Execution/Activity = 1 feature(s) (per_file_prefetch_hit).

## Image 1: XP Hacking (SCHARDT.001) (7 targets, 11,773 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 17 | 6.0±0.0 | 6.0±0.0 | 24.6±3.5 | 24.6±3.5 | 5.0 | 6.0 | 6.0 | 7.0 |
| only Temporal | 7 | 6.0±0.0 | 6.6±0.5 | 19.8±0.8 | 19.8±0.8 | 6.0 | 6.0 | 1.0 | 1.0 |
| all except Temporal | 10 | 5.2±0.4 | 6.0±0.0 | 36.4±0.7 | 36.4±0.7 | 2.0 | 2.0 | 7.0 | 7.0 |
| only Path/File | 9 | 4.4±0.9 | 5.8±0.4 | 34.1±1.1 | 34.1±1.1 | 2.0 | 3.0 | 6.0 | 7.0 |
| all except Path/File | 8 | 6.0±0.0 | 6.6±0.5 | 19.8±0.7 | 19.8±0.7 | 7.0 | 7.0 | 6.0 | 6.0 |
| only Execution/Activity | 1 | 5.0±0.0 | 7.0±0.0 | 18.1±0.0 | 18.1±0.0 | 1.0 | 5.0 | 5.0 | 7.0 |
| all except Execution/Activity | 16 | 6.0±0.0 | 6.0±0.0 | 24.7±1.2 | 24.7±1.2 | 5.0 | 6.0 | 5.0 | 7.0 |

## Image 2: Win7 Data Leakage (19 targets, 85,017 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 17 | 18.0±0.0 | 18.0±0.0 | 9.3±2.0 | 21.9±1.3 | 8.0 | 8.0 | 19.0 | 19.0 |
| only Temporal | 7 | 4.8±0.8 | 5.6±0.5 | 66.4±2.3 | 66.4±2.3 | 4.0 | 7.0 | 12.0 | 12.0 |
| all except Temporal | 10 | 19.0±0.0 | 19.0±0.0 | 4.8±1.1 | 13.0±0.8 | 7.0 | 9.0 | 19.0 | 19.0 |
| only Path/File | 9 | 19.0±0.0 | 19.0±0.0 | 7.9±0.8 | 12.4±1.6 | 7.0 | 9.0 | 19.0 | 19.0 |
| all except Path/File | 8 | 4.8±0.8 | 5.6±0.5 | 63.2±2.0 | 63.5±2.0 | 5.0 | 7.0 | 6.0 | 13.0 |
| only Execution/Activity | 1 | 16.0±0.0 | 17.0±0.0 | 25.8±0.0 | 41.3±0.0 | 16.0 | 17.0 | 16.0 | 17.0 |
| all except Execution/Activity | 16 | 18.0±0.0 | 18.2±0.4 | 10.0±1.3 | 20.8±1.0 | 7.0 | 7.0 | 19.0 | 19.0 |

## Image 3: Win10 Lone Wolf (34 targets, 166,110 files)

| feature set | #feat | IF at15 | IF at20 | IF knee % | IF plateau % | LOF at15 | LOF at20 | OCSVM at15 | OCSVM at20 |
|---|---|---|---|---|---|---|---|---|---|
| full clean set | 17 | 28.2±1.5 | 30.8±2.2 | 19.9±2.9 | 21.6±3.2 | 8.0 | 12.0 | 24.0 | 24.0 |
| only Temporal | 7 | 16.4±2.2 | 20.0±0.0 | 75.0±0.7 | 75.0±0.7 | 26.0 | 26.0 | 2.0 | 17.0 |
| all except Temporal | 10 | 34.0±0.0 | 34.0±0.0 | 9.4±0.5 | 11.6±1.3 | 7.0 | 10.0 | 33.0 | 33.0 |
| only Path/File | 9 | 34.0±0.0 | 34.0±0.0 | 9.9±0.6 | 12.2±1.4 | 7.0 | 10.0 | 33.0 | 33.0 |
| all except Path/File | 8 | 16.2±1.1 | 20.0±0.0 | 70.9±0.5 | 70.9±0.5 | 26.0 | 26.0 | 16.0 | 17.0 |
| only Execution/Activity | 1 | 0.0±0.0 | 0.0±0.0 | 22.8±0.0 | 22.8±0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| all except Execution/Activity | 16 | 28.8±0.4 | 32.0±1.9 | 19.1±1.6 | 20.9±2.2 | 8.0 | 12.0 | 24.0 | 24.0 |

## Pass rules (PROTOCOL A1)

Evaluated on IF seed means. "Lowers recall" = removing the group gives a lower mean at 15% or at 20% on at least one disk.

| group | removal lowers recall on | change at15,at20 when removed (targets) | group alone matches full set on all disks |
|---|---|---|---|
| Temporal | img1 | img1: -0.8,+0.0 / img2: +1.0,+1.0 / img3: +5.8,+3.2 | no |
| Path/File | img2, img3 | img1: +0.0,+0.6 / img2: -13.2,-12.4 / img3: -12.0,-10.8 | no |
| Execution/Activity | none | img1: +0.0,+0.0 / img2: +0.0,+0.2 / img3: +0.6,+1.2 | no |

- Rule 1 (every group's removal lowers recall on >=1 disk): **FAIL**
- Rule 2 (no single group alone matches the full set on all disks): **PASS**
- A1 overall: **FAIL**
