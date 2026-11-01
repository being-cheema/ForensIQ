# Hyperparameter sensitivity (final 19 features)

Cells: targets caught at 15% / 20% (seed mean). Default IF n=200, max_samples=256.

## img1 (7 targets)

| setting | at15 | at20 | knee % |
|---|---|---|---|
| IF n=50, max_samples=256 | 6.8 | 7.0 | 11.3 |
| IF n=50, max_samples=512 | 6.4 | 7.0 | 14.4 |
| IF n=50, max_samples=1024 | 6.4 | 7.0 | 14.9 |
| IF n=100, max_samples=256 | 7.0 | 7.0 | 12.1 |
| IF n=100, max_samples=512 | 6.6 | 7.0 | 14.8 |
| IF n=100, max_samples=1024 | 6.8 | 7.0 | 14.1 |
| IF n=200, max_samples=256 | 7.0 | 7.0 | 12.4 |
| IF n=200, max_samples=512 | 6.4 | 7.0 | 14.7 |
| IF n=200, max_samples=1024 | 6.8 | 7.0 | 14.2 |
| IF n=500, max_samples=256 | 7.0 | 7.0 | 12.6 |
| IF n=500, max_samples=512 | 6.8 | 7.0 | 14.4 |
| IF n=500, max_samples=1024 | 7.0 | 7.0 | 14.0 |
| LOF k=10 | 2.0 | 2.0 | 76.3 |
| LOF k=20 | 4.0 | 5.0 | 35.7 |
| LOF k=35 | 4.0 | 5.0 | 54.2 |
| LOF k=50 | 1.0 | 2.0 | 40.1 |
| OC-SVM nu=0.01 | 5.0 | 5.6 | 67.1 |
| OC-SVM nu=0.05 | 6.0 | 6.0 | 32.5 |
| OC-SVM nu=0.1 | 6.0 | 6.0 | 21.0 |

## img2 (19 targets)

| setting | at15 | at20 | knee % |
|---|---|---|---|
| IF n=50, max_samples=256 | 18.6 | 19.0 | 8.7 |
| IF n=50, max_samples=512 | 19.0 | 19.0 | 4.9 |
| IF n=50, max_samples=1024 | 19.0 | 19.0 | 5.8 |
| IF n=100, max_samples=256 | 18.6 | 19.0 | 9.3 |
| IF n=100, max_samples=512 | 19.0 | 19.0 | 5.2 |
| IF n=100, max_samples=1024 | 19.0 | 19.0 | 5.1 |
| IF n=200, max_samples=256 | 19.0 | 19.0 | 9.8 |
| IF n=200, max_samples=512 | 19.0 | 19.0 | 5.6 |
| IF n=200, max_samples=1024 | 19.0 | 19.0 | 4.3 |
| IF n=500, max_samples=256 | 19.0 | 19.0 | 10.4 |
| IF n=500, max_samples=512 | 19.0 | 19.0 | 6.2 |
| IF n=500, max_samples=1024 | 19.0 | 19.0 | 4.9 |
| LOF k=10 | 4.0 | 4.0 | 86.5 |
| LOF k=20 | 5.0 | 8.0 | 88.2 |
| LOF k=35 | 5.0 | 6.0 | 90.2 |
| LOF k=50 | 8.0 | 8.0 | 81.3 |
| OC-SVM nu=0.01 | 18.8 | 19.0 | 7.3 |
| OC-SVM nu=0.05 | 19.0 | 19.0 | 2.3 |
| OC-SVM nu=0.1 | 19.0 | 19.0 | 3.3 |

## img3 (34 targets)

| setting | at15 | at20 | knee % |
|---|---|---|---|
| IF n=50, max_samples=256 | 32.4 | 34.0 | 12.5 |
| IF n=50, max_samples=512 | 33.8 | 34.0 | 10.5 |
| IF n=50, max_samples=1024 | 33.0 | 34.0 | 12.0 |
| IF n=100, max_samples=256 | 32.8 | 34.0 | 13.2 |
| IF n=100, max_samples=512 | 32.6 | 34.0 | 12.5 |
| IF n=100, max_samples=1024 | 33.4 | 34.0 | 12.8 |
| IF n=200, max_samples=256 | 32.4 | 34.0 | 13.2 |
| IF n=200, max_samples=512 | 33.4 | 34.0 | 12.3 |
| IF n=200, max_samples=1024 | 34.0 | 34.0 | 12.4 |
| IF n=500, max_samples=256 | 32.2 | 34.0 | 14.1 |
| IF n=500, max_samples=512 | 33.4 | 34.0 | 12.3 |
| IF n=500, max_samples=1024 | 33.8 | 34.0 | 12.8 |
| LOF k=10 | 7.0 | 8.0 | 77.7 |
| LOF k=20 | 15.0 | 19.0 | 43.3 |
| LOF k=35 | 17.0 | 17.0 | 61.7 |
| LOF k=50 | 17.0 | 18.0 | 62.0 |
| OC-SVM nu=0.01 | 18.2 | 19.6 | 65.6 |
| OC-SVM nu=0.05 | 22.0 | 23.4 | 46.9 |
| OC-SVM nu=0.1 | 26.8 | 28.8 | 24.9 |

## Rule
```
{
 "img1": {
  "default_at15": 7.0,
  "default_at20": 7.0,
  "range15": [
   6.4,
   7.0
  ],
  "range20": [
   7.0,
   7.0
  ],
  "max_change15": 0.5999999999999996,
  "max_change20": 0.0
 },
 "img2": {
  "default_at15": 19.0,
  "default_at20": 19.0,
  "range15": [
   18.6,
   19.0
  ],
  "range20": [
   19.0,
   19.0
  ],
  "max_change15": 0.3999999999999986,
  "max_change20": 0.0
 },
 "img3": {
  "default_at15": 32.4,
  "default_at20": 34.0,
  "range15": [
   32.2,
   34.0
  ],
  "range20": [
   34.0,
   34.0
  ],
  "max_change15": 1.6000000000000014,
  "max_change20": 0.0
 },
 "pass_20": true,
 "pass_15": false
}
```