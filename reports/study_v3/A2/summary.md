# A2: threshold and seed stability

Clean feature set. 5 seeds (42, 1337, 9999, 7, 2024). LOF is deterministic, so its 5 seeds are identical by construction.
Full per-seed curves: `curves.csv`; per disk and model statistics: `summary.csv`. Targets are counted as in the protocol (a target is caught if any of its files is in the top K).

## img1 (Image 1: XP Hacking (SCHARDT.001)): 7 targets, 11,773 files, 90% = 7 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 6.0 (0.0, 6.0-6.0) | 6.0 (0.0, 6.0-6.0) | 24.57 (3.17, 21.4-30.03) | 24.57 | 1/5 | 75.43 | 1754.8 / 2342.8 |
| LOF | 5.0 (0.0, 5.0-5.0) | 6.0 (0.0, 6.0-6.0) | 37.17 (0.0, 37.17-37.17) | 37.17 | 5/5 | 62.83 | 1758.0 / 2345.0 |
| OC-SVM | 6.0 (0.0, 6.0-6.0) | 6.8 (0.4, 6.0-7.0) | 19.06 (1.0, 17.42-20.38) | 19.06 | 2/5 | 80.94 | 1757.0 / 2344.0 |

## img2 (Image 2: Win7 Data Leakage): 19 targets, 85,017 files, 90% = 18 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 18.0 (0.0, 18.0-18.0) | 18.0 (0.0, 18.0-18.0) | 9.26 (1.83, 7.27-12.01) | 21.93 | 1/5 | 78.07 | 12721.0 / 16969.2 |
| LOF | 8.0 (0.0, 8.0-8.0) | 8.0 (0.0, 8.0-8.0) | 52.92 (0.0, 52.92-52.92) | 62.42 | 5/5 | 37.58 | 12745.0 / 16995.0 |
| OC-SVM | 19.0 (0.0, 19.0-19.0) | 19.0 (0.0, 19.0-19.0) | 2.51 (0.45, 1.89-3.26) | 3.86 | 3/5 | 96.14 | 12719.0 / 16969.0 |

## img3 (Image 3: Win10 Lone Wolf): 34 targets, 166,110 files, 90% = 31 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 28.2 (1.33, 26.0-30.0) | 30.8 (1.94, 29.0-34.0) | 19.85 (2.58, 15.35-22.28) | 21.61 | 1/5 | 78.39 | 24846.0 / 33142.2 |
| LOF | 8.0 (0.0, 8.0-8.0) | 12.0 (0.0, 12.0-12.0) | 76.65 (0.0, 76.65-76.65) | 82.65 | 5/5 | 17.35 | 24900.0 / 33198.0 |
| OC-SVM | 22.8 (1.94, 19.0-24.0) | 24.0 (0.0, 24.0-24.0) | 57.24 (5.13, 52.0-64.35) | 77.86 | 1/5 | 22.14 | 24857.6 / 33159.6 |

## Pass rule (knee spread <= 2pp on every disk, and headline budget catches >= 90% of targets in every seed on every disk)

| model | headline | knee spread ok | min catch >= 90% every seed/disk | result |
|---|---|---|---|---|
| IF | 15% | FAIL | FAIL | FAIL |
| IF | 20% | FAIL | FAIL | FAIL |
| LOF | 15% | PASS | FAIL | FAIL |
| LOF | 20% | PASS | FAIL | FAIL |
| OC-SVM | 15% | FAIL | FAIL | FAIL |
| OC-SVM | 20% | FAIL | FAIL | FAIL |

False alarms at the headline budget = files reviewed (K) minus ground-truth files among them (all target files, not just first hits).
