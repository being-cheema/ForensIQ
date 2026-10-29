# A5: hyperparameter sensitivity

Final features (17 clean + 2 burst). Isolation Forest (sklearn IsolationForest called directly; 5 seeds, mean±sd) over n_estimators x max_samples; LOF over k; One-Class SVM over nu with gamma="scale" (10,000-row fit sample). **LOF and One-Class SVM: seed 42 only.** Default = IF (200 trees, sample 256), LOF k=20, OCSVM nu=0.05; the defaults were checked to reproduce the pipeline's final-set results exactly. max_samples "auto" equals min(256, n) = 256 in sklearn, so it is expected to match the 256 column.

Cells are targets caught at 15% / 20% of the disk. Targets: img1 = 7, img2 = 19, img3 = 34.

## Image 1: XP Hacking (SCHARDT.001)

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 6.8±0.4 | 7.0±0.0 | 11.3±3.4 | 11.3±3.4 |
| IF n=50, max_samples=512 | 6.4±0.5 | 7.0±0.0 | 14.4±1.9 | 14.4±1.9 |
| IF n=50, max_samples=1024 | 6.4±0.5 | 7.0±0.0 | 14.9±1.8 | 14.9±1.8 |
| IF n=50, max_samples=auto | 6.8±0.4 | 7.0±0.0 | 11.3±3.4 | 11.3±3.4 |
| IF n=100, max_samples=256 | 7.0±0.0 | 7.0±0.0 | 12.1±1.9 | 12.1±1.9 |
| IF n=100, max_samples=512 | 6.6±0.5 | 7.0±0.0 | 14.8±1.6 | 14.8±1.6 |
| IF n=100, max_samples=1024 | 6.8±0.4 | 7.0±0.0 | 14.1±0.9 | 14.1±0.9 |
| IF n=100, max_samples=auto | 7.0±0.0 | 7.0±0.0 | 12.1±1.9 | 12.1±1.9 |
| IF n=200, max_samples=256 | 7.0±0.0 | 7.0±0.0 | 12.4±1.6 | 12.4±1.6 |
| IF n=200, max_samples=512 | 6.4±0.5 | 7.0±0.0 | 14.7±0.8 | 14.7±0.8 |
| IF n=200, max_samples=1024 | 6.8±0.4 | 7.0±0.0 | 14.2±0.6 | 14.2±0.6 |
| IF n=200, max_samples=auto | 7.0±0.0 | 7.0±0.0 | 12.4±1.6 | 12.4±1.6 |
| IF n=500, max_samples=256 | 7.0±0.0 | 7.0±0.0 | 12.6±1.0 | 12.6±1.0 |
| IF n=500, max_samples=512 | 6.8±0.4 | 7.0±0.0 | 14.4±0.7 | 14.4±0.7 |
| IF n=500, max_samples=1024 | 7.0±0.0 | 7.0±0.0 | 14.0±0.4 | 14.0±0.4 |
| IF n=500, max_samples=auto | 7.0±0.0 | 7.0±0.0 | 12.6±1.0 | 12.6±1.0 |
| LOF k=10 | 2.0 | 2.0 | 76.33 | 76.33 |
| LOF k=20 | 4.0 | 5.0 | 35.72 | 35.72 |
| LOF k=35 | 4.0 | 5.0 | 54.24 | 54.24 |
| LOF k=50 | 1.0 | 2.0 | 40.09 | 40.09 |
| OCSVM nu=0.01 | 5.0 | 6.0 | 62.47 | 62.47 |
| OCSVM nu=0.05 | 6.0 | 6.0 | 29.44 | 29.44 |
| OCSVM nu=0.1 | 6.0 | 6.0 | 20.78 | 20.78 |

## Image 2: Win7 Data Leakage

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 18.6±0.5 | 19.0±0.0 | 8.7±2.7 | 13.3±3.9 |
| IF n=50, max_samples=512 | 19.0±0.0 | 19.0±0.0 | 4.9±1.6 | 10.6±3.0 |
| IF n=50, max_samples=1024 | 19.0±0.0 | 19.0±0.0 | 5.8±2.5 | 10.1±1.9 |
| IF n=50, max_samples=auto | 18.6±0.5 | 19.0±0.0 | 8.7±2.7 | 13.3±3.9 |
| IF n=100, max_samples=256 | 18.6±0.5 | 19.0±0.0 | 9.3±2.2 | 13.5±3.1 |
| IF n=100, max_samples=512 | 19.0±0.0 | 19.0±0.0 | 5.2±1.3 | 10.4±1.8 |
| IF n=100, max_samples=1024 | 19.0±0.0 | 19.0±0.0 | 5.1±1.8 | 10.7±0.8 |
| IF n=100, max_samples=auto | 18.6±0.5 | 19.0±0.0 | 9.3±2.2 | 13.5±3.1 |
| IF n=200, max_samples=256 | 19.0±0.0 | 19.0±0.0 | 9.8±2.5 | 12.9±0.7 |
| IF n=200, max_samples=512 | 19.0±0.0 | 19.0±0.0 | 5.6±1.4 | 11.4±1.5 |
| IF n=200, max_samples=1024 | 19.0±0.0 | 19.0±0.0 | 4.3±0.3 | 11.3±0.9 |
| IF n=200, max_samples=auto | 19.0±0.0 | 19.0±0.0 | 9.8±2.5 | 12.9±0.7 |
| IF n=500, max_samples=256 | 19.0±0.0 | 19.0±0.0 | 10.4±1.8 | 12.6±0.4 |
| IF n=500, max_samples=512 | 19.0±0.0 | 19.0±0.0 | 6.2±0.7 | 11.9±0.9 |
| IF n=500, max_samples=1024 | 19.0±0.0 | 19.0±0.0 | 4.9±0.5 | 11.7±0.8 |
| IF n=500, max_samples=auto | 19.0±0.0 | 19.0±0.0 | 10.4±1.8 | 12.6±0.4 |
| LOF k=10 | 4.0 | 4.0 | 86.54 | 93.8 |
| LOF k=20 | 5.0 | 8.0 | 88.25 | 93.18 |
| LOF k=35 | 5.0 | 6.0 | 90.22 | 94.46 |
| LOF k=50 | 8.0 | 8.0 | 81.3 | 89.48 |
| OCSVM nu=0.01 | 19.0 | 19.0 | 4.45 | 9.74 |
| OCSVM nu=0.05 | 19.0 | 19.0 | 2.04 | 2.67 |
| OCSVM nu=0.1 | 19.0 | 19.0 | 3.96 | 4.56 |

## Image 3: Win10 Lone Wolf

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 32.4±1.7 | 34.0±0.0 | 12.5±2.7 | 15.8±2.1 |
| IF n=50, max_samples=512 | 33.8±0.4 | 34.0±0.0 | 10.5±2.2 | 13.1±2.0 |
| IF n=50, max_samples=1024 | 33.0±1.4 | 34.0±0.0 | 12.0±1.4 | 14.7±2.7 |
| IF n=50, max_samples=auto | 32.4±1.7 | 34.0±0.0 | 12.5±2.7 | 15.8±2.1 |
| IF n=100, max_samples=256 | 32.8±1.1 | 34.0±0.0 | 13.2±1.2 | 16.5±2.2 |
| IF n=100, max_samples=512 | 32.6±1.9 | 34.0±0.0 | 12.5±2.5 | 14.9±1.8 |
| IF n=100, max_samples=1024 | 33.4±1.3 | 34.0±0.0 | 12.8±1.1 | 14.5±1.2 |
| IF n=100, max_samples=auto | 32.8±1.1 | 34.0±0.0 | 13.2±1.2 | 16.5±2.2 |
| IF n=200, max_samples=256 | 32.4±1.9 | 34.0±0.0 | 13.2±1.7 | 16.2±1.5 |
| IF n=200, max_samples=512 | 33.4±0.5 | 34.0±0.0 | 12.3±1.7 | 14.9±2.0 |
| IF n=200, max_samples=1024 | 34.0±0.0 | 34.0±0.0 | 12.4±0.4 | 14.0±0.8 |
| IF n=200, max_samples=auto | 32.4±1.9 | 34.0±0.0 | 13.2±1.7 | 16.2±1.5 |
| IF n=500, max_samples=256 | 32.2±0.8 | 34.0±0.0 | 14.1±0.6 | 17.6±1.0 |
| IF n=500, max_samples=512 | 33.4±0.5 | 34.0±0.0 | 12.3±0.7 | 15.0±1.0 |
| IF n=500, max_samples=1024 | 33.8±0.4 | 34.0±0.0 | 12.8±0.4 | 14.8±0.6 |
| IF n=500, max_samples=auto | 32.2±0.8 | 34.0±0.0 | 14.1±0.6 | 17.6±1.0 |
| LOF k=10 | 7.0 | 8.0 | 77.68 | 91.44 |
| LOF k=20 | 15.0 | 19.0 | 43.32 | 84.03 |
| LOF k=35 | 17.0 | 17.0 | 61.73 | 85.29 |
| LOF k=50 | 17.0 | 18.0 | 61.97 | 99.5 |
| OCSVM nu=0.01 | 17.0 | 17.0 | 75.69 | 88.39 |
| OCSVM nu=0.05 | 24.0 | 25.0 | 39.42 | 79.3 |
| OCSVM nu=0.1 | 29.0 | 31.0 | 17.2 | 69.04 |

## Pass rule (PROTOCOL A5): headline recall changes by <= 1 target across the tested settings

Measured as the largest absolute difference of targets caught (IF: seed mean) between any tested setting and the default, at 15% and at 20%, per disk. The spread (max minus min over settings) is also given.

| model | disk | max change at15 | max change at20 | spread at15 | spread at20 |
|---|---|---|---|---|---|
| IF | img1 | 0.6 | 0.0 | 0.6 | 0.0 |
| IF | img2 | 0.4 | 0.0 | 0.4 | 0.0 |
| IF | img3 | 1.6 | 0.0 | 1.8 | 0.0 |
| LOF | img1 | 3.0 | 3.0 | 3.0 | 3.0 |
| LOF | img2 | 3.0 | 4.0 | 4.0 | 4.0 |
| LOF | img3 | 8.0 | 11.0 | 10.0 | 11.0 |
| OCSVM | img1 | 1.0 | 0.0 | 1.0 | 0.0 |
| OCSVM | img2 | 0.0 | 0.0 | 0.0 | 0.0 |
| OCSVM | img3 | 7.0 | 8.0 | 12.0 | 14.0 |

- IF: **FAIL**
- LOF: **FAIL**
- OCSVM: **FAIL**
- A5 overall (all three families within 1 target on every disk): **FAIL**
