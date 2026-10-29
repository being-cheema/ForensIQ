# A4: models versus plain rules

Rules use no ground truth and no learning; each gives a score per file, ranked the same way as the models (ties by path order). Models are seed means.
R1 delta_si_fn; R2 m_before_cr then delta_mb; R3 temp_path+user_path+is_exe+is_script+is_archive; R4 most recent m_time first; R5 random order (mean of 5 seeds).

## img1: 7 targets

| method | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF | 6.0 | 6.0 | 24.57 | 24.57 |
| LOF | 5.0 | 6.0 | 37.17 | 37.17 |
| OC-SVM | 6.0 | 6.8 | 19.06 | 19.06 |
| R1 timestamp mismatch (delta_si_fn) | 5 | 5 | 24.24 | 24.24 |
| R2 modified before created | 3 | 3 | 47.31 | 47.31 |
| R3 location (temp+user+exe+script+archive) | 6 | 7 | 15.31 | 15.31 |
| R4 recency (latest m_time first) | 1 | 1 | 97.64 | 97.64 |
| R5 random order (mean of 5 seeds) | 2.8 | 2.8 | 77.74 | 77.74 |

## img2: 19 targets

| method | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF | 18.0 | 18.0 | 9.26 | 21.93 |
| LOF | 8.0 | 8.0 | 52.92 | 62.42 |
| OC-SVM | 19.0 | 19.0 | 2.51 | 3.86 |
| R1 timestamp mismatch (delta_si_fn) | 0 | 0 | 90.37 | 90.38 |
| R2 modified before created | 0 | 1 | 56.53 | 56.54 |
| R3 location (temp+user+exe+script+archive) | 16 | 16 | 53.81 | 55.72 |
| R4 recency (latest m_time first) | 16 | 16 | 95.49 | 95.7 |
| R5 random order (mean of 5 seeds) | 5.4 | 7.0 | 73.51 | 83.64 |

## img3: 34 targets

| method | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF | 28.2 | 30.8 | 19.85 | 21.61 |
| LOF | 8.0 | 12.0 | 76.65 | 82.65 |
| OC-SVM | 22.8 | 24.0 | 57.24 | 77.86 |
| R1 timestamp mismatch (delta_si_fn) | 0 | 0 | 70.7 | 70.71 |
| R2 modified before created | 15 | 17 | 57.11 | 57.11 |
| R3 location (temp+user+exe+script+archive) | 34 | 34 | 11.31 | 11.31 |
| R4 recency (latest m_time first) | 34 | 34 | 4.87 | 7.54 |
| R5 random order (mean of 5 seeds) | 11.6 | 14.8 | 83.14 | 95.28 |

## Pass rule (model beats the best rule, strictly, at the headline budget on >= 2 of 3 disks)

| model | headline | per disk | result |
|---|---|---|---|
| IF | 15% | img1: no (best rule R3 = 6); img2: win (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
| IF | 20% | img1: no (best rule R3 = 7); img2: win (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
| LOF | 15% | img1: no (best rule R3 = 6); img2: no (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
| LOF | 20% | img1: no (best rule R3 = 7); img2: no (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
| OC-SVM | 15% | img1: no (best rule R3 = 6); img2: win (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
| OC-SVM | 20% | img1: no (best rule R3 = 7); img2: win (best rule R3 = 16); img3: no (best rule R3 = 34) | FAIL |
