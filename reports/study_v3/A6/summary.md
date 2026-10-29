# A6: cross-disk transfer

For each model, the knee budget (seed-mean % of disk needed for 90% of targets) is learned on one disk and applied to each other disk. Reported: % of targets caught there (mean over seeds).

| model | learned on | applied to | knee % | files reviewed | targets caught (mean) | % caught | % caught, worst seed |
|---|---|---|---|---|---|---|---|
| IF | img1 | img2 | 24.57 | 20889 | 19.0 | 100.0 | 100.0 |
| IF | img1 | img3 | 24.57 | 40813 | 33.6 | 98.82 | 94.12 |
| IF | img2 | img1 | 9.26 | 1090 | 6.0 | 85.71 | 85.71 |
| IF | img2 | img3 | 9.26 | 15382 | 21.2 | 62.35 | 52.94 |
| IF | img3 | img1 | 19.85 | 2337 | 6.0 | 85.71 | 85.71 |
| IF | img3 | img2 | 19.85 | 16876 | 18.0 | 94.74 | 94.74 |
| LOF | img1 | img2 | 37.17 | 31601 | 15.0 | 78.95 | 78.95 |
| LOF | img1 | img3 | 37.17 | 61743 | 22.0 | 64.71 | 64.71 |
| LOF | img2 | img1 | 52.92 | 6230 | 7.0 | 100.0 | 100.0 |
| LOF | img2 | img3 | 52.92 | 87905 | 28.0 | 82.35 | 82.35 |
| LOF | img3 | img1 | 76.65 | 9024 | 7.0 | 100.0 | 100.0 |
| LOF | img3 | img2 | 76.65 | 65166 | 19.0 | 100.0 | 100.0 |
| OC-SVM | img1 | img2 | 19.06 | 16204 | 19.0 | 100.0 | 100.0 |
| OC-SVM | img1 | img3 | 19.06 | 31661 | 24.0 | 70.59 | 70.59 |
| OC-SVM | img2 | img1 | 2.51 | 296 | 5.0 | 71.43 | 71.43 |
| OC-SVM | img2 | img3 | 2.51 | 4169 | 4.2 | 12.35 | 8.82 |
| OC-SVM | img3 | img1 | 57.24 | 6739 | 7.0 | 100.0 | 100.0 |
| OC-SVM | img3 | img2 | 57.24 | 48664 | 19.0 | 100.0 | 100.0 |

## Pass rule (a budget tuned on any one disk catches >= 90% on the other two)

| model | result |
|---|---|
| IF | FAIL |
| LOF | FAIL |
| OC-SVM | FAIL |

## Fixed budget view: % of targets caught (seed mean)

| model | budget | img1 | img2 | img3 | >= 90% on all 3 |
|---|---|---|---|---|---|
| IF | 15% | 85.71 | 94.74 | 82.94 | FAIL |
| IF | 20% | 85.71 | 94.74 | 90.59 | FAIL |
| LOF | 15% | 71.43 | 42.11 | 23.53 | FAIL |
| LOF | 20% | 85.71 | 42.11 | 35.29 | FAIL |
| OC-SVM | 15% | 85.71 | 100.0 | 67.06 | FAIL |
| OC-SVM | 20% | 97.14 | 100.0 | 70.59 | FAIL |
