# Threshold stability study (4th ablation, fresh runs)

Question: is the 'everything caught at 5.5%' result a fluke, and what review threshold is stable?

Method: images img2 (85017 files, 19 targets) and img3 (166110 files, 34 targets); IF, LOF, OC-SVM on 23 features plus IF on the 17 legacy features. Each run drops a random 10% of non-target rows, refits with the seed, and ranks all remaining rows; every threshold is read off that one ranking (K = round(pct x rows kept)). A target is caught if any of its rows is in the top K. Precision = targets caught / K. Seeds: R1 = 0-4, R2 = 100-104, R3 = 200-204; sections 1, 2 and 4 use R1. Reproduce with `.venv/bin/python threshold_sweep.py`.

## 1. Fine sweep (seeds 0-4, mean +/- std over 5 runs)

### img2 / IF-23 (19 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 3826.0 | 17.0 +/- 0.00 | 89.5 +/- 0.0 | 0.4443 |
| 7 | 5356.0 | 17.0 +/- 0.00 | 89.5 +/- 0.0 | 0.3174 |
| 9 | 6887.0 | 17.0 +/- 0.00 | 89.5 +/- 0.0 | 0.2468 |
| 11 | 8417.0 | 17.4 +/- 0.49 | 91.6 +/- 2.6 | 0.2067 |
| 13 | 9947.0 | 17.8 +/- 0.40 | 93.7 +/- 2.1 | 0.1789 |
| 15 | 11478.0 | 18.0 +/- 0.00 | 94.7 +/- 0.0 | 0.1568 |

### img2 / LOF-23 (19 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 3826.0 | 2.0 +/- 0.00 | 10.5 +/- 0.0 | 0.0523 |
| 7 | 5356.0 | 3.0 +/- 0.00 | 15.8 +/- 0.0 | 0.056 |
| 9 | 6887.0 | 3.0 +/- 0.00 | 15.8 +/- 0.0 | 0.0436 |
| 11 | 8417.0 | 3.0 +/- 0.00 | 15.8 +/- 0.0 | 0.0356 |
| 13 | 9947.0 | 3.4 +/- 0.80 | 17.9 +/- 4.2 | 0.0342 |
| 15 | 11478.0 | 3.8 +/- 0.75 | 20.0 +/- 3.9 | 0.0331 |

### img2 / OCSVM-23 (19 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 3826.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.4966 |
| 7 | 5356.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.3547 |
| 9 | 6887.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.2759 |
| 11 | 8417.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.2257 |
| 13 | 9947.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.191 |
| 15 | 11478.0 | 19.0 +/- 0.00 | 100.0 +/- 0.0 | 0.1655 |

### img2 / IF-17 (19 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 3826.0 | 7.6 +/- 0.49 | 40.0 +/- 2.6 | 0.1986 |
| 7 | 5356.0 | 8.0 +/- 0.00 | 42.1 +/- 0.0 | 0.1494 |
| 9 | 6887.0 | 9.4 +/- 1.02 | 49.5 +/- 5.4 | 0.1365 |
| 11 | 8417.0 | 10.6 +/- 1.20 | 55.8 +/- 6.3 | 0.1259 |
| 13 | 9947.0 | 12.0 +/- 0.00 | 63.2 +/- 0.0 | 0.1206 |
| 15 | 11478.0 | 13.2 +/- 0.98 | 69.5 +/- 5.2 | 0.115 |

### img3 / IF-23 (34 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 7475.0 | 11.8 +/- 3.60 | 34.7 +/- 10.6 | 0.1579 |
| 7 | 10466.0 | 24.4 +/- 2.06 | 71.8 +/- 6.1 | 0.2331 |
| 9 | 13456.0 | 28.0 +/- 2.00 | 82.4 +/- 5.9 | 0.2081 |
| 11 | 16446.0 | 29.0 +/- 0.63 | 85.3 +/- 1.9 | 0.1763 |
| 13 | 19436.0 | 31.2 +/- 1.72 | 91.8 +/- 5.1 | 0.1605 |
| 15 | 22426.0 | 33.8 +/- 0.40 | 99.4 +/- 1.2 | 0.1507 |

### img3 / LOF-23 (34 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 7475.0 | 0.6 +/- 0.49 | 1.8 +/- 1.4 | 0.008 |
| 7 | 10466.0 | 2.0 +/- 0.00 | 5.9 +/- 0.0 | 0.0191 |
| 9 | 13456.0 | 2.2 +/- 0.40 | 6.5 +/- 1.2 | 0.0163 |
| 11 | 16446.0 | 3.0 +/- 0.00 | 8.8 +/- 0.0 | 0.0182 |
| 13 | 19436.0 | 3.2 +/- 0.40 | 9.4 +/- 1.2 | 0.0165 |
| 15 | 22426.0 | 4.4 +/- 0.49 | 12.9 +/- 1.4 | 0.0196 |

### img3 / OCSVM-23 (34 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 7475.0 | 24.8 +/- 0.40 | 72.9 +/- 1.2 | 0.3318 |
| 7 | 10466.0 | 24.8 +/- 0.40 | 72.9 +/- 1.2 | 0.237 |
| 9 | 13456.0 | 25.4 +/- 0.49 | 74.7 +/- 1.4 | 0.1888 |
| 11 | 16446.0 | 25.6 +/- 0.49 | 75.3 +/- 1.4 | 0.1557 |
| 13 | 19436.0 | 25.8 +/- 0.40 | 75.9 +/- 1.2 | 0.1327 |
| 15 | 22426.0 | 27.4 +/- 1.74 | 80.6 +/- 5.1 | 0.1222 |

### img3 / IF-17 (34 targets)

| Threshold % | K (files) | Targets caught | Recall % | Precision % |
|---|---|---|---|---|
| 5 | 7475.0 | 21.4 +/- 1.62 | 62.9 +/- 4.8 | 0.2863 |
| 7 | 10466.0 | 26.0 +/- 1.55 | 76.5 +/- 4.6 | 0.2484 |
| 9 | 13456.0 | 29.6 +/- 0.49 | 87.1 +/- 1.4 | 0.22 |
| 11 | 16446.0 | 31.2 +/- 0.98 | 91.8 +/- 2.9 | 0.1897 |
| 13 | 19436.0 | 32.6 +/- 0.49 | 95.9 +/- 1.4 | 0.1677 |
| 15 | 22426.0 | 33.4 +/- 0.49 | 98.2 +/- 1.4 | 0.1489 |

## 2. Targets caught at exactly 5.0% and 5.5% (seeds 0-4)

| Image | Config | Threshold % | K | Targets caught | Recall % |
|---|---|---|---|---|---|
| img2 | IF-23 | 5.0 | 3826.0 | 17.0 +/- 0.00 | 89.5 |
| img2 | IF-23 | 5.5 | 4209.0 | 17.0 +/- 0.00 | 89.5 |
| img2 | LOF-23 | 5.0 | 3826.0 | 2.0 +/- 0.00 | 10.5 |
| img2 | LOF-23 | 5.5 | 4209.0 | 2.4 +/- 0.49 | 12.6 |
| img2 | OCSVM-23 | 5.0 | 3826.0 | 19.0 +/- 0.00 | 100.0 |
| img2 | OCSVM-23 | 5.5 | 4209.0 | 19.0 +/- 0.00 | 100.0 |
| img2 | IF-17 | 5.0 | 3826.0 | 7.6 +/- 0.49 | 40.0 |
| img2 | IF-17 | 5.5 | 4209.0 | 8.0 +/- 0.00 | 42.1 |
| img3 | IF-23 | 5.0 | 7475.0 | 11.8 +/- 3.60 | 34.7 |
| img3 | IF-23 | 5.5 | 8223.0 | 17.4 +/- 3.26 | 51.2 |
| img3 | LOF-23 | 5.0 | 7475.0 | 0.6 +/- 0.49 | 1.8 |
| img3 | LOF-23 | 5.5 | 8223.0 | 1.0 +/- 0.63 | 2.9 |
| img3 | OCSVM-23 | 5.0 | 7475.0 | 24.8 +/- 0.40 | 72.9 |
| img3 | OCSVM-23 | 5.5 | 8223.0 | 24.8 +/- 0.40 | 72.9 |
| img3 | IF-17 | 5.0 | 7475.0 | 21.4 +/- 1.62 | 62.9 |
| img3 | IF-17 | 5.5 | 8223.0 | 22.8 +/- 2.04 | 67.1 |

## 3. Full sweep 5-100% (seeds 0-4; mean targets caught, std in brackets)

Full per-threshold data (recall, precision) is in `full_sweep.csv`.

| Threshold % | img2/IF-23 | img2/LOF-23 | img2/OCSVM-23 | img2/IF-17 | img3/IF-23 | img3/LOF-23 | img3/OCSVM-23 | img3/IF-17 |
|---|---|---|---|---|---|---|---|---|
| 5 | 17.0 (0.00) | 2.0 (0.00) | 19.0 (0.00) | 7.6 (0.49) | 11.8 (3.60) | 0.6 (0.49) | 24.8 (0.40) | 21.4 (1.62) |
| 7 | 17.0 (0.00) | 3.0 (0.00) | 19.0 (0.00) | 8.0 (0.00) | 24.4 (2.06) | 2.0 (0.00) | 24.8 (0.40) | 26.0 (1.55) |
| 9 | 17.0 (0.00) | 3.0 (0.00) | 19.0 (0.00) | 9.4 (1.02) | 28.0 (2.00) | 2.2 (0.40) | 25.4 (0.49) | 29.6 (0.49) |
| 11 | 17.4 (0.49) | 3.0 (0.00) | 19.0 (0.00) | 10.6 (1.20) | 29.0 (0.63) | 3.0 (0.00) | 25.6 (0.49) | 31.2 (0.98) |
| 13 | 17.8 (0.40) | 3.4 (0.80) | 19.0 (0.00) | 12.0 (0.00) | 31.2 (1.72) | 3.2 (0.40) | 25.8 (0.40) | 32.6 (0.49) |
| 15 | 18.0 (0.00) | 3.8 (0.75) | 19.0 (0.00) | 13.2 (0.98) | 33.8 (0.40) | 4.4 (0.49) | 27.4 (1.74) | 33.4 (0.49) |
| 17 | 18.0 (0.00) | 4.4 (1.36) | 19.0 (0.00) | 15.0 (0.00) | 34.0 (0.00) | 8.0 (1.90) | 29.0 (2.76) | 34.0 (0.00) |
| 19 | 18.4 (0.49) | 5.8 (0.75) | 19.0 (0.00) | 15.8 (0.75) | 34.0 (0.00) | 10.4 (2.42) | 30.2 (2.64) | 34.0 (0.00) |
| 21 | 19.0 (0.00) | 6.0 (1.10) | 19.0 (0.00) | 17.8 (0.40) | 34.0 (0.00) | 12.8 (2.32) | 30.4 (2.65) | 34.0 (0.00) |
| 23 | 19.0 (0.00) | 6.8 (0.75) | 19.0 (0.00) | 18.0 (0.00) | 34.0 (0.00) | 16.2 (1.47) | 30.8 (2.56) | 34.0 (0.00) |
| 25 | 19.0 (0.00) | 7.8 (0.98) | 19.0 (0.00) | 18.0 (0.00) | 34.0 (0.00) | 18.0 (1.67) | 31.2 (2.71) | 34.0 (0.00) |
| 27 | 19.0 (0.00) | 7.8 (0.98) | 19.0 (0.00) | 18.0 (0.00) | 34.0 (0.00) | 19.4 (1.02) | 32.4 (1.20) | 34.0 (0.00) |
| 29 | 19.0 (0.00) | 7.8 (0.98) | 19.0 (0.00) | 18.0 (0.00) | 34.0 (0.00) | 19.8 (0.98) | 32.8 (0.40) | 34.0 (0.00) |
| 31 | 19.0 (0.00) | 8.0 (0.89) | 19.0 (0.00) | 18.4 (0.49) | 34.0 (0.00) | 20.6 (0.80) | 33.0 (0.00) | 34.0 (0.00) |
| 33 | 19.0 (0.00) | 8.2 (0.98) | 19.0 (0.00) | 18.8 (0.40) | 34.0 (0.00) | 21.6 (1.62) | 33.0 (0.00) | 34.0 (0.00) |
| 35 | 19.0 (0.00) | 8.2 (0.98) | 19.0 (0.00) | 18.8 (0.40) | 34.0 (0.00) | 23.2 (0.98) | 33.0 (0.00) | 34.0 (0.00) |
| 37 | 19.0 (0.00) | 8.8 (0.40) | 19.0 (0.00) | 18.8 (0.40) | 34.0 (0.00) | 25.0 (0.63) | 33.0 (0.00) | 34.0 (0.00) |
| 39 | 19.0 (0.00) | 9.2 (0.75) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 27.0 (1.41) | 33.0 (0.00) | 34.0 (0.00) |
| 41 | 19.0 (0.00) | 9.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 27.4 (1.36) | 33.0 (0.00) | 34.0 (0.00) |
| 43 | 19.0 (0.00) | 9.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 27.8 (0.98) | 33.0 (0.00) | 34.0 (0.00) |
| 45 | 19.0 (0.00) | 10.0 (0.63) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 28.2 (1.17) | 33.0 (0.00) | 34.0 (0.00) |
| 47 | 19.0 (0.00) | 11.2 (1.17) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 28.8 (0.98) | 33.0 (0.00) | 34.0 (0.00) |
| 49 | 19.0 (0.00) | 11.2 (1.17) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 29.2 (1.60) | 33.0 (0.00) | 34.0 (0.00) |
| 51 | 19.0 (0.00) | 11.8 (1.17) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 29.6 (1.85) | 33.2 (0.40) | 34.0 (0.00) |
| 53 | 19.0 (0.00) | 12.0 (0.89) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 30.6 (1.62) | 33.4 (0.49) | 34.0 (0.00) |
| 55 | 19.0 (0.00) | 12.0 (0.89) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 30.6 (1.62) | 33.4 (0.49) | 34.0 (0.00) |
| 57 | 19.0 (0.00) | 12.0 (0.89) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 30.6 (1.62) | 33.8 (0.40) | 34.0 (0.00) |
| 59 | 19.0 (0.00) | 12.0 (0.89) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.0 (1.26) | 34.0 (0.00) | 34.0 (0.00) |
| 61 | 19.0 (0.00) | 12.2 (0.75) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 63 | 19.0 (0.00) | 12.4 (0.49) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 65 | 19.0 (0.00) | 13.4 (1.50) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 67 | 19.0 (0.00) | 13.6 (1.62) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 69 | 19.0 (0.00) | 13.6 (1.62) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 71 | 19.0 (0.00) | 14.0 (1.26) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.2 (1.17) | 34.0 (0.00) | 34.0 (0.00) |
| 73 | 19.0 (0.00) | 14.8 (0.98) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 31.8 (0.98) | 34.0 (0.00) | 34.0 (0.00) |
| 75 | 19.0 (0.00) | 15.0 (0.89) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.0 (0.63) | 34.0 (0.00) | 34.0 (0.00) |
| 77 | 19.0 (0.00) | 15.2 (0.75) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.2 (0.40) | 34.0 (0.00) | 34.0 (0.00) |
| 79 | 19.0 (0.00) | 15.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.4 (0.49) | 34.0 (0.00) | 34.0 (0.00) |
| 81 | 19.0 (0.00) | 16.6 (0.49) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.8 (0.40) | 34.0 (0.00) | 34.0 (0.00) |
| 83 | 19.0 (0.00) | 16.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.8 (0.40) | 34.0 (0.00) | 34.0 (0.00) |
| 85 | 19.0 (0.00) | 17.4 (0.49) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.8 (0.40) | 34.0 (0.00) | 34.0 (0.00) |
| 87 | 19.0 (0.00) | 17.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 32.8 (0.40) | 34.0 (0.00) | 34.0 (0.00) |
| 89 | 19.0 (0.00) | 18.4 (0.49) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 33.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 91 | 19.0 (0.00) | 18.6 (0.49) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 33.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 93 | 19.0 (0.00) | 18.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 33.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 95 | 19.0 (0.00) | 18.8 (0.40) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 33.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 97 | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 33.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 99 | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |
| 100 | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 19.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) | 34.0 (0.00) |

## 4. Three independent randomizations: do stable thresholds agree?

Stable-threshold definitions (on the 5,7,...,99,100 grid, using the mean over the 5 seeds of each randomization): (i) smallest threshold where mean recall reaches its maximum; (ii) smallest threshold with mean recall >= 90%; (iii) knee = smallest threshold after which every further +2% step adds < 1 target on average ('sustained'); the first-step variant (first +2% step adding < 1 target) is in the JSON. 'Agree rate' = share of thresholds where the three randomization means lie within 0.5 targets of each other.

| Image/Config | (i) first at max recall R1/R2/R3 | (ii) first recall>=90% R1/R2/R3 | (iii) knee R1/R2/R3 | Agree rate | Pooled 15 seeds: >=90% / knee |
|---|---|---|---|---|---|
| img2/IF-23 | 21 / 21 / 21 (yes) | 11 / 11 / 11 (yes) | 5 / 5 / 5 (yes) | 48/49 (98%) | 11 / 5 |
| img2/LOF-23 | 97 / 93 / 95 (NO) | 85 / 83 / 83 (NO) | 65 / 79 / 87 (NO) | 29/49 (59%) | 83 / 25 |
| img2/OCSVM-23 | 5 / 5 / 5 (yes) | 5 / 5 / 5 (yes) | 5 / 5 / 5 (yes) | 49/49 (100%) | 5 / 5 |
| img2/IF-17 | 39 / 35 / 33 (NO) | 21 / 21 / 21 (yes) | 21 / 21 / 21 (yes) | 47/49 (96%) | 21 / 21 |
| img3/IF-23 | 17 / 17 / 19 (NO) | 13 / 13 / 15 (NO) | 15 / 17 / 15 (NO) | 44/49 (90%) | 13 / 15 |
| img3/LOF-23 | 99 / 99 / 100 (NO) | 53 / 51 / 53 (NO) | 99 / 99 / 39 (NO) | 19/49 (39%) | 53 / 39 |
| img3/OCSVM-23 | 59 / 59 / 61 (NO) | 23 / 21 / 21 (NO) | 27 / 21 / 21 (NO) | 36/49 (74%) | 21 / 21 |
| img3/IF-17 | 17 / 17 / 17 (yes) | 11 / 11 / 11 (yes) | 13 / 15 / 15 (NO) | 45/49 (92%) | 11 / 15 |

## 5. Comparison with the earlier claims (IF on 17 features, img2)

No script that produced `reports/ablation_4_threshold_sweep.md/.json`, `ablation_4_full_sweep_5_to_100.csv` or `ablation_4_three_randomizations.csv` exists in the repository, so those numbers cannot be traced to code; this study re-derives them from scratch.

| Threshold % | Claimed targets | Fresh mean | Fresh std | Reproduces (within 0.5) |
|---|---|---|---|---|
| 5 | 7.0 | 7.6 | 0.49 | False |
| 11 | 10.4 | 10.6 | 1.2 | True |
| 15 | 12.0 | 13.2 | 0.98 | False |
| 25 | 18.0 | 18.0 | 0.0 | True |
| 43 | 19.0 | 19.0 | 0.0 | True |

- Full-sweep points where fresh IF-17 mean is within 0.5 of the earlier file: 42/49.
- Earlier three-randomization file: 15/20 rows marked identical (it covers 5-43% only, seeds 42/1337/9999). Fresh IF-17 img2 agreement within 0.5 targets: 47/49 thresholds.

## 6. Findings in plain English

Mean targets caught (seeds 0-4), with the threshold at which every target is caught:

| Image/Config | 5% | 5.5% | 11% | 15% | 25% | 43% | 100% of targets first reached at |
|---|---|---|---|---|---|---|---|
| img2 / IF-23 (19) | 17.0 | 17.0 | 17.4 | 18.0 | 19.0 | 19.0 | 21% |
| img2 / LOF-23 | 2.0 | 2.4 | 3.0 | 3.8 | 7.8 | 9.8 | 97% |
| img2 / OC-SVM-23 | 19.0 | 19.0 | 19.0 | 19.0 | 19.0 | 19.0 | 5% |
| img2 / IF-17 | 7.6 | 8.0 | 10.6 | 13.2 | 18.0 | 19.0 | 39% |
| img3 / IF-23 (34) | 11.8 | 17.4 | 29.0 | 33.8 | 34.0 | 34.0 | 17% |
| img3 / LOF-23 | 0.6 | 1.0 | 3.0 | 4.4 | 18.0 | 27.8 | 99% |
| img3 / OC-SVM-23 | 24.8 | 24.8 | 25.6 | 27.4 | 31.2 | 33.0 | 59% |
| img3 / IF-17 | 21.4 | 22.8 | 31.2 | 33.4 | 34.0 | 34.0 | 17% |

1. **'100% at 5.5%' is not a general property.** It was a small-image effect on the old XP image (not re-tested here). On the two larger images no model other than OC-SVM on img2 catches every target at 5-5.5%, and on img3 even the best 23-feature model is at 51% (IF) or 73% (OC-SVM) at 5.5%. The jump between 5% and 5.5% is real but modest and, on img3, noisy (IF-23: 11.8 +/- 3.6 at 5%, 17.4 +/- 3.3 at 5.5%).
2. **Isolation Forest is the only model with a usable, stable threshold.** On both images the 23-feature IF reaches >= 90% recall at 11-15% (img2: 11%; img3: 13-15%) and everything by 17-21%. A budget of about 15% (img2: ~12.8k files, img3: ~25k files) is the smallest round figure that gives >= 90% on both images for IF-23 in all three randomizations.
3. **OC-SVM on img2 is a ceiling artefact.** It catches all 19 at 5% in every run, but on img3 it stalls at 25 of 34 until about 11% and needs ~59% for full recall. Its result does not transfer between images, so 5% cannot be recommended on the strength of img2 alone.
4. **LOF is not usable at any practical budget.** It catches 2-3 targets at 5-11% and needs ~100% review on both images; its randomizations also disagree most (agreement 59% and 39% of thresholds).
5. **Do the three randomizations agree?** For IF-23 and IF-17 the curves agree within 0.5 targets at 90-98% of thresholds on img2 and 90-92% on img3, and the first >= 90% recall threshold is identical across R1/R2/R3 on img2 (11 and 21) and within one grid step on img3 (13/13/15 for IF-23; 11/11/11 for IF-17). The 'first at max recall' and knee thresholds are less stable (differences of 2-4 points on img3, and for img2 IF-17 the first-at-max moves between 33 and 39), because the last target to be caught is a single hard file whose rank shifts with the random drop. LOF and img3 OC-SVM do not agree. The knee is degenerate for img2 IF-23 and OC-SVM (already at 5%) because their curves are nearly flat from the start.
6. **Recommended thresholds (smallest threshold reaching >= 90% mean recall in all three randomizations, or the nearest pooled value):** img2 IF-23 11%, img3 IF-23 15%, img2 IF-17 21%, img3 IF-17 13-15% (pooled 11%), img2 OC-SVM 5%, img3 OC-SVM 23%, LOF none below ~50%. If a single figure is needed for the 23-feature IF, 15% is stable on both images.

### Earlier claims (IF on 17 features, img2)

No script that produced the earlier files exists in the repository, so these cannot be traced to code. Against the fresh runs:

- 7/19 at 5%: close but not exact (fresh 7.6 +/- 0.5; some seeds give 8). The earlier std of 0.00 does not reproduce.
- 10.4 at 11%: reproduces (fresh 10.6 +/- 1.2).
- 12 at 15%: fresh 13.2 +/- 1.0, higher than claimed (not within 0.5).
- 18/19 at 25%: reproduces exactly (18.0 +/- 0.0).
- 19/19 at 43%: reproduces (full recall is in fact reached at 39%).
- Overall the fresh IF-17 curve is within 0.5 targets of the earlier full-sweep file at 42 of 49 thresholds, so the overall shape reproduces while the zero-variance plateaus at 5-7% and 13-15% do not (fresh runs show seed-to-seed variation there).
- The earlier randomization file has 15 of 20 rows marked identical and covers 5-43% only; the '44 of 49 steps' agreement was not found in the repository files. Fresh IF-17 agreement is 47 of 49 thresholds.
- The earlier takeaway of a '11% knee' is not supported as a knee: the curve keeps rising by more than 1 target per 2% step until about 21%.
