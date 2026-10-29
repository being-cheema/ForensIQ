# A2: threshold and seed stability

Clean feature set. 5 seeds (42, 1337, 9999, 7, 2024). LOF is deterministic, so its 5 seeds are identical by construction.
Full per-seed curves: `curves.csv`; per disk and model statistics: `summary.csv`. Targets are counted as in the protocol (a target is caught if any of its files is in the top K).

## img1 (Image 1: XP Hacking (SCHARDT.001)): 7 targets, 11,773 files, 90% = 7 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 7.0 (0.0, 7.0-7.0) | 7.0 (0.0, 7.0-7.0) | 12.42 (1.42, 10.93-14.8) | 12.42 | 2/5 | 87.58 | 1752.0 / 2340.4 |
| LOF | 4.0 (0.0, 4.0-4.0) | 5.0 (0.0, 5.0-5.0) | 35.72 (0.0, 35.72-35.72) | 35.72 | 5/5 | 64.28 | 1761.0 / 2347.0 |
| OC-SVM | 6.0 (0.0, 6.0-6.0) | 6.0 (0.0, 6.0-6.0) | 32.53 (4.97, 28.68-41.68) | 32.53 | 1/5 | 67.47 | 1757.8 / 2345.0 |

## img2 (Image 2: Win7 Data Leakage): 19 targets, 85,017 files, 90% = 18 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 19.0 (0.0, 19.0-19.0) | 19.0 (0.0, 19.0-19.0) | 9.85 (2.27, 7.24-12.47) | 12.93 | 1/5 | 87.07 | 12715.0 / 16965.0 |
| LOF | 5.0 (0.0, 5.0-5.0) | 8.0 (0.0, 8.0-8.0) | 88.25 (0.0, 88.25-88.25) | 93.18 | 5/5 | 6.82 | 12748.0 / 16995.0 |
| OC-SVM | 19.0 (0.0, 19.0-19.0) | 19.0 (0.0, 19.0-19.0) | 2.32 (0.24, 2.04-2.71) | 3.34 | 4/5 | 96.66 | 12716.6 / 16966.0 |

## img3 (Image 3: Win10 Lone Wolf): 34 targets, 166,110 files, 90% = 31 targets

| model | at15 mean (sd, min-max) | at20 mean (sd, min-max) | knee % mean (sd, min-max) | plateau % mean | seeds within 0.5pp of median knee | dead zone % (100-plateau) | false alarms@15 / @20 (mean) |
|---|---|---|---|---|---|---|---|
| IF | 32.4 (1.74, 29.0-34.0) | 34.0 (0.0, 34.0-34.0) | 13.21 (1.48, 11.0-15.25) | 16.19 | 1/5 | 83.81 | 24836.4 / 33137.0 |
| LOF | 15.0 (0.0, 15.0-15.0) | 19.0 (0.0, 19.0-19.0) | 43.32 (0.0, 43.32-43.32) | 84.03 | 5/5 | 15.97 | 24899.0 / 33193.0 |
| OC-SVM | 22.0 (2.28, 18.0-24.0) | 23.4 (1.36, 21.0-25.0) | 46.93 (6.31, 39.42-57.94) | 80.88 | 1/5 | 19.12 | 24861.6 / 33163.6 |

## Pass rule (knee spread <= 2pp on every disk, and headline budget catches >= 90% of targets in every seed on every disk)

| model | headline | knee spread ok | min catch >= 90% every seed/disk | result |
|---|---|---|---|---|
| IF | 15% | FAIL | FAIL | FAIL |
| IF | 20% | FAIL | PASS | FAIL |
| LOF | 15% | PASS | FAIL | FAIL |
| LOF | 20% | PASS | FAIL | FAIL |
| OC-SVM | 15% | FAIL | FAIL | FAIL |
| OC-SVM | 20% | FAIL | FAIL | FAIL |

False alarms at the headline budget = files reviewed (K) minus ground-truth files among them (all target files, not just first hits).
