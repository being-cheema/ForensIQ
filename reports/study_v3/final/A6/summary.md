# A6: cross-disk transfer

For each model, the knee budget (seed-mean % of disk needed for 90% of targets) is learned on one disk and applied to each other disk. Reported: % of targets caught there (mean over seeds).

| model | learned on | applied to | knee % | files reviewed | targets caught (mean) | % caught | % caught, worst seed |
|---|---|---|---|---|---|---|---|
| IF | img1 | img2 | 12.42 | 10559 | 18.0 | 94.74 | 89.47 |
| IF | img1 | img3 | 12.42 | 20631 | 30.0 | 88.24 | 85.29 |
| IF | img2 | img1 | 9.85 | 1160 | 6.0 | 85.71 | 85.71 |
| IF | img2 | img3 | 9.85 | 16362 | 25.8 | 75.88 | 70.59 |
| IF | img3 | img1 | 13.21 | 1555 | 6.6 | 94.29 | 85.71 |
| IF | img3 | img2 | 13.21 | 11231 | 18.8 | 98.95 | 94.74 |
| LOF | img1 | img2 | 35.72 | 30368 | 8.0 | 42.11 | 42.11 |
| LOF | img1 | img3 | 35.72 | 59334 | 24.0 | 70.59 | 70.59 |
| LOF | img2 | img1 | 88.25 | 10390 | 7.0 | 100.0 | 100.0 |
| LOF | img2 | img3 | 88.25 | 146592 | 34.0 | 100.0 | 100.0 |
| LOF | img3 | img1 | 43.32 | 5100 | 7.0 | 100.0 | 100.0 |
| LOF | img3 | img2 | 43.32 | 36829 | 10.0 | 52.63 | 52.63 |
| OC-SVM | img1 | img2 | 32.53 | 27656 | 19.0 | 100.0 | 100.0 |
| OC-SVM | img1 | img3 | 32.53 | 54036 | 25.8 | 75.88 | 70.59 |
| OC-SVM | img2 | img1 | 2.32 | 273 | 5.0 | 71.43 | 71.43 |
| OC-SVM | img2 | img3 | 2.32 | 3854 | 3.4 | 10.0 | 8.82 |
| OC-SVM | img3 | img1 | 46.93 | 5525 | 7.0 | 100.0 | 100.0 |
| OC-SVM | img3 | img2 | 46.93 | 39898 | 19.0 | 100.0 | 100.0 |

## Pass rule (a budget tuned on any one disk catches >= 90% on the other two)

| model | result |
|---|---|
| IF | FAIL |
| LOF | FAIL |
| OC-SVM | FAIL |

## Fixed budget view: % of targets caught (seed mean)

| model | budget | img1 | img2 | img3 | >= 90% on all 3 |
|---|---|---|---|---|---|
| IF | 15% | 100.0 | 100.0 | 95.29 | PASS |
| IF | 20% | 100.0 | 100.0 | 100.0 | PASS |
| LOF | 15% | 57.14 | 26.32 | 44.12 | FAIL |
| LOF | 20% | 71.43 | 42.11 | 55.88 | FAIL |
| OC-SVM | 15% | 85.71 | 100.0 | 64.71 | FAIL |
| OC-SVM | 20% | 85.71 | 100.0 | 68.82 | FAIL |
