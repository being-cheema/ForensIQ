# A5: hyperparameter sensitivity

Clean features. Isolation Forest (sklearn IsolationForest called directly; 5 seeds, mean±sd) over n_estimators x max_samples; LOF over k; One-Class SVM over nu with gamma="scale" (10,000-row fit sample). **LOF and One-Class SVM: seed 42 only.** Default = IF (200 trees, sample 256), LOF k=20, OCSVM nu=0.05; the defaults were checked to reproduce the pipeline's clean results exactly. max_samples "auto" equals min(256, n) = 256 in sklearn, so it is expected to match the 256 column.

Cells are targets caught at 15% / 20% of the disk. Targets: img1 = 7, img2 = 19, img3 = 34.

## Image 1: XP Hacking (SCHARDT.001)

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 6.0±0.0 | 6.0±0.0 | 27.6±7.1 | 27.6±7.1 |
| IF n=50, max_samples=512 | 6.0±0.0 | 6.0±0.0 | 25.9±3.3 | 25.9±3.3 |
| IF n=50, max_samples=1024 | 6.0±0.0 | 6.0±0.0 | 26.4±5.4 | 26.4±5.4 |
| IF n=50, max_samples=auto | 6.0±0.0 | 6.0±0.0 | 27.6±7.1 | 27.6±7.1 |
| IF n=100, max_samples=256 | 6.0±0.0 | 6.0±0.0 | 26.3±5.3 | 26.3±5.3 |
| IF n=100, max_samples=512 | 6.0±0.0 | 6.0±0.0 | 27.8±2.8 | 27.8±2.8 |
| IF n=100, max_samples=1024 | 6.0±0.0 | 6.0±0.0 | 26.0±1.6 | 26.0±1.6 |
| IF n=100, max_samples=auto | 6.0±0.0 | 6.0±0.0 | 26.3±5.3 | 26.3±5.3 |
| IF n=200, max_samples=256 | 6.0±0.0 | 6.0±0.0 | 24.6±3.5 | 24.6±3.5 |
| IF n=200, max_samples=512 | 6.0±0.0 | 6.0±0.0 | 26.6±2.7 | 26.6±2.7 |
| IF n=200, max_samples=1024 | 6.0±0.0 | 6.0±0.0 | 25.3±2.2 | 25.3±2.2 |
| IF n=200, max_samples=auto | 6.0±0.0 | 6.0±0.0 | 24.6±3.5 | 24.6±3.5 |
| IF n=500, max_samples=256 | 6.0±0.0 | 6.0±0.0 | 24.2±1.3 | 24.2±1.3 |
| IF n=500, max_samples=512 | 6.0±0.0 | 6.0±0.0 | 25.3±1.8 | 25.3±1.8 |
| IF n=500, max_samples=1024 | 6.0±0.0 | 6.0±0.0 | 24.3±0.6 | 24.3±0.6 |
| IF n=500, max_samples=auto | 6.0±0.0 | 6.0±0.0 | 24.2±1.3 | 24.2±1.3 |
| LOF k=10 | 3.0 | 3.0 | 50.34 | 50.34 |
| LOF k=20 | 5.0 | 6.0 | 37.17 | 37.17 |
| LOF k=35 | 3.0 | 5.0 | 45.07 | 45.07 |
| LOF k=50 | 0.0 | 2.0 | 45.02 | 45.02 |
| OCSVM nu=0.01 | 6.0 | 6.0 | 25.45 | 25.45 |
| OCSVM nu=0.05 | 6.0 | 7.0 | 18.94 | 18.94 |
| OCSVM nu=0.1 | 6.0 | 7.0 | 18.35 | 18.35 |

## Image 2: Win7 Data Leakage

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 17.8±0.4 | 18.0±0.0 | 12.8±3.4 | 22.7±2.6 |
| IF n=50, max_samples=512 | 18.0±0.0 | 18.4±0.5 | 8.2±2.3 | 20.6±2.0 |
| IF n=50, max_samples=1024 | 18.0±0.0 | 18.4±0.5 | 7.5±3.5 | 21.5±4.3 |
| IF n=50, max_samples=auto | 17.8±0.4 | 18.0±0.0 | 12.8±3.4 | 22.7±2.6 |
| IF n=100, max_samples=256 | 18.0±0.0 | 18.2±0.4 | 9.8±1.6 | 21.5±2.3 |
| IF n=100, max_samples=512 | 18.0±0.0 | 18.8±0.4 | 6.2±0.9 | 19.3±1.1 |
| IF n=100, max_samples=1024 | 18.0±0.0 | 18.4±0.5 | 5.2±1.5 | 20.0±1.6 |
| IF n=100, max_samples=auto | 18.0±0.0 | 18.2±0.4 | 9.8±1.6 | 21.5±2.3 |
| IF n=200, max_samples=256 | 18.0±0.0 | 18.0±0.0 | 9.3±2.0 | 21.9±1.3 |
| IF n=200, max_samples=512 | 18.0±0.0 | 18.6±0.5 | 6.8±0.7 | 20.2±0.8 |
| IF n=200, max_samples=1024 | 18.0±0.0 | 18.6±0.5 | 5.0±0.4 | 20.1±2.0 |
| IF n=200, max_samples=auto | 18.0±0.0 | 18.0±0.0 | 9.3±2.0 | 21.9±1.3 |
| IF n=500, max_samples=256 | 18.0±0.0 | 18.0±0.0 | 9.0±0.6 | 21.4±1.3 |
| IF n=500, max_samples=512 | 18.0±0.0 | 18.4±0.5 | 6.5±0.8 | 20.4±1.2 |
| IF n=500, max_samples=1024 | 18.0±0.0 | 18.8±0.4 | 4.3±0.5 | 19.4±0.9 |
| IF n=500, max_samples=auto | 18.0±0.0 | 18.0±0.0 | 9.0±0.6 | 21.4±1.3 |
| LOF k=10 | 6.0 | 9.0 | 75.69 | 84.11 |
| LOF k=20 | 8.0 | 8.0 | 52.92 | 62.42 |
| LOF k=35 | 2.0 | 3.0 | 91.76 | 99.84 |
| LOF k=50 | 3.0 | 4.0 | 71.26 | 99.49 |
| OCSVM nu=0.01 | 19.0 | 19.0 | 4.8 | 13.21 |
| OCSVM nu=0.05 | 19.0 | 19.0 | 1.89 | 4.6 |
| OCSVM nu=0.1 | 19.0 | 19.0 | 3.87 | 5.79 |

## Image 3: Win10 Lone Wolf

| setting | at15 | at20 | knee % | plateau % |
|---|---|---|---|---|
| IF n=50, max_samples=256 | 27.0±4.6 | 31.0±2.1 | 19.7±5.1 | 22.0±4.7 |
| IF n=50, max_samples=512 | 28.6±2.5 | 32.4±2.3 | 17.8±4.4 | 20.8±5.0 |
| IF n=50, max_samples=1024 | 29.2±1.8 | 33.0±1.4 | 16.2±1.6 | 19.9±1.4 |
| IF n=50, max_samples=auto | 27.0±4.6 | 31.0±2.1 | 19.7±5.1 | 22.0±4.7 |
| IF n=100, max_samples=256 | 28.6±2.5 | 31.4±1.9 | 19.5±4.9 | 22.0±4.8 |
| IF n=100, max_samples=512 | 28.6±2.1 | 32.4±2.2 | 17.6±3.9 | 20.2±3.5 |
| IF n=100, max_samples=1024 | 29.2±1.6 | 33.0±1.4 | 14.9±2.4 | 18.4±2.3 |
| IF n=100, max_samples=auto | 28.6±2.5 | 31.4±1.9 | 19.5±4.9 | 22.0±4.8 |
| IF n=200, max_samples=256 | 28.2±1.5 | 30.8±2.2 | 19.9±2.9 | 21.6±3.2 |
| IF n=200, max_samples=512 | 28.0±1.9 | 32.6±1.3 | 18.0±2.9 | 20.5±3.2 |
| IF n=200, max_samples=1024 | 29.6±1.5 | 34.0±0.0 | 15.6±1.2 | 18.5±1.1 |
| IF n=200, max_samples=auto | 28.2±1.5 | 30.8±2.2 | 19.9±2.9 | 21.6±3.2 |
| IF n=500, max_samples=256 | 28.8±0.4 | 32.6±1.7 | 18.4±1.4 | 20.0±1.7 |
| IF n=500, max_samples=512 | 28.4±1.7 | 32.6±1.3 | 16.9±1.8 | 19.6±2.2 |
| IF n=500, max_samples=1024 | 29.0±1.9 | 33.4±1.3 | 15.6±1.3 | 19.1±2.2 |
| IF n=500, max_samples=auto | 28.8±0.4 | 32.6±1.7 | 18.4±1.4 | 20.0±1.7 |
| LOF k=10 | 11.0 | 14.0 | 90.53 | 96.78 |
| LOF k=20 | 8.0 | 12.0 | 76.65 | 82.65 |
| LOF k=35 | 17.0 | 17.0 | 97.45 | 97.7 |
| LOF k=50 | 17.0 | 17.0 | 75.85 | 88.1 |
| OCSVM nu=0.01 | 18.0 | 18.0 | 68.76 | 87.0 |
| OCSVM nu=0.05 | 24.0 | 24.0 | 52.02 | 74.8 |
| OCSVM nu=0.1 | 33.0 | 33.0 | 8.94 | 53.73 |

## Pass rule (PROTOCOL A5): headline recall changes by <= 1 target across the tested settings

Measured as the largest absolute difference of targets caught (IF: seed mean) between any tested setting and the default, at 15% and at 20%, per disk. The spread (max minus min over settings) is also given.

| model | disk | max change at15 | max change at20 | spread at15 | spread at20 |
|---|---|---|---|---|---|
| IF | img1 | 0.0 | 0.0 | 0.0 | 0.0 |
| IF | img2 | 0.2 | 0.8 | 0.2 | 0.8 |
| IF | img3 | 1.4 | 3.2 | 2.6 | 3.2 |
| LOF | img1 | 5.0 | 4.0 | 5.0 | 4.0 |
| LOF | img2 | 6.0 | 5.0 | 6.0 | 6.0 |
| LOF | img3 | 9.0 | 5.0 | 9.0 | 5.0 |
| OCSVM | img1 | 0.0 | 1.0 | 0.0 | 1.0 |
| OCSVM | img2 | 0.0 | 0.0 | 0.0 | 0.0 |
| OCSVM | img3 | 9.0 | 9.0 | 15.0 | 15.0 |

- IF: **FAIL**
- LOF: **FAIL**
- OCSVM: **FAIL**
- A5 overall (all three families within 1 target on every disk): **FAIL**
