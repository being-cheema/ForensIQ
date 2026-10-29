# Study v3, explainability ablations B1-B3 (final feature set)

Feature set: 19 features (17 clean + log_burst_count, log_burst_60s). Headline flagging budget: top 20% of the disk by suspicion score (15% reported alongside). Models are fitted once per seed on the standardized matrix; every number below comes from `study_v3_explain.py`. Pass rules are the ones fixed in PROTOCOL.md; a rule passes only if **every** disk x model cell passes.

## Verdict

| Rule | What it asks | Result at 20% |
|---|---|---|
| B1 faithfulness | removing the SHAP top-3 moves a flagged file down the ranking more than removing 3 random features (one-sided Wilcoxon p < 0.01) | **FAIL (6/9 disk x model cells pass)** |
| B2 stability | top-3 reasons agree across seeds (Jaccard >= 0.7) and under 1% noise (>= 0.6) | **FAIL (6/9 disk x model cells pass)** |
| B3 planted attacks | SHAP top-3 names the planted cause in >= 80% of detected planted files | **FAIL (8/9 disk x model cells pass)** |

Cells that fail at 20% (disk model):

- B1: img1 LOF, img2 LOF, img3 LOF
- B2: img1 LOF, img2 LOF, img3 LOF
- B3: img3 LOF

Cells are listed in the tables below. Failures are reported as failures; nothing was re-tuned. Counting only Isolation Forest (TreeSHAP) and OC-SVM, the pattern in the tables is that their reasons are faithful and stable, while LOF's KernelSHAP reasons are not: LOF is a local density method, so editing a few features can move a file to another sparse region instead of a dense one (the ranking does not fall), and a 1% jitter reshuffles its nearest neighbours.

## How each test works (plain English)

- **Reason** = the three features that push a file's suspicion score up the most (largest positive SHAP values). Isolation Forest uses TreeSHAP; One-Class SVM and LOF use KernelSHAP (20 background rows, 200 samples per file).
- **B1 deletion test.** For flagged files (every target caught, plus a seeded random sample of other flagged files: 300 for Isolation Forest, 100 for OC-SVM and LOF) we overwrite the three reason features with the disk's **median** value (not a permutation), score the file again with the **same fitted model**, and see how far it falls in the ranking. The control overwrites 3 random features of the same file the same way (5 draws, averaged). A faithful explanation should cause a bigger drop than the random control.
- **B2 stability.** (i) Seeds: Isolation Forest and OC-SVM are refitted with the 5 study seeds; for files flagged under all 5 seeds we take the mean pairwise Jaccard overlap of their top-3 reasons. LOF has no random component, so only the noise test applies. (ii) Noise: Gaussian noise with sd = 1% of each column's std is added to the standardized matrix, the model is refitted (seed 42) and the top-3 reasons are compared with the clean ones. KernelSHAP's own sampling noise is removed by reusing the same random stream, so differences come from the model, not the explainer's dice.
- **B3 planted attacks.** Per disk, 60 random ordinary files (non-target, not flagged by Isolation Forest seed 42) are copied and one cause is planted in each copy, 20 per attack type: P1 timestamp forgery (delta_si_fn at the disk's 99.5th percentile, m_before_cr = 1; cause features delta_si_fn, m_before_cr, delta_mb, delta_mc), P2 hidden executable in temp (is_exe = 1, temp_path = 1, path_depth at the 95th percentile), P3 bulk-wipe burst (both burst features at the disk maximum). Planted rows are standardized with the original disk mean/std, scored by models fitted on the original rows only, and explained. *Detected* = lands in the flagged top 20%; *attribution hit* = top-3 reasons include at least one cause feature. Isolation Forest is repeated over all 5 seeds (values are 5-seed means).
- **LOF caveat.** LOF is transductive: a row in its own training set counts as its own neighbour. Every explained or edited training row is therefore queried with itself removed from its neighbour list (the original and the edited version alike), and ranked against the ordinary LOF scores. The other points' densities still include the row, a second-order effect that is the same for the SHAP and control arms.

## B1 Faithfulness (deletion test)

### Flagged = top 20%

| Disk | Model | Files (targets) | Median rank drop, SHAP top-3 | Median rank drop, random 3 | Ratio | SHAP > random share | Wilcoxon p | Result |
|---|---|---|---|---|---|---|---|---|
| img1 | IF | 307 (7) | 2142 | 199.4 | 10.7 | 1.00 | <1e-4 | PASS |
| img1 | LOF | 105 (5) | 0 | 296.4 | 0.0 | 0.48 | 0.0692 | FAIL |
| img1 | OC-SVM | 106 (6) | 7683 | 59.7 | 128.7 | 0.97 | <1e-4 | PASS |
| img2 | IF | 319 (19) | 28574 | 2354.0 | 12.1 | 1.00 | <1e-4 | PASS |
| img2 | LOF | 108 (8) | -2542 | -53.4 | n/a | 0.26 | 1.0000 | FAIL |
| img2 | OC-SVM | 119 (19) | 71934 | 7702.4 | 9.3 | 1.00 | <1e-4 | PASS |
| img3 | IF | 334 (34) | 58878 | 3491.6 | 16.9 | 1.00 | <1e-4 | PASS |
| img3 | LOF | 119 (19) | -3522 | -1110.6 | n/a | 0.29 | 0.9997 | FAIL |
| img3 | OC-SVM | 125 (25) | 133243 | 19198.4 | 6.9 | 0.95 | <1e-4 | PASS |

### Flagged = top 15%

| Disk | Model | Files (targets) | Median rank drop, SHAP top-3 | Median rank drop, random 3 | Ratio | SHAP > random share | Wilcoxon p | Result |
|---|---|---|---|---|---|---|---|---|
| img1 | IF | 238 (7) | 2022 | 203.8 | 9.9 | 1.00 | <1e-4 | PASS |
| img1 | LOF | 81 (4) | 42 | 469.6 | 0.1 | 0.53 | 0.0172 | FAIL |
| img1 | OC-SVM | 78 (6) | 8221 | 0.8 | 10276.2 | 0.99 | <1e-4 | PASS |
| img2 | IF | 254 (19) | 28022 | 2543.6 | 11.0 | 1.00 | <1e-4 | PASS |
| img2 | LOF | 76 (5) | -1237 | 893.6 | -1.4 | 0.25 | 1.0000 | FAIL |
| img2 | OC-SVM | 97 (19) | 73498 | 5634.8 | 13.0 | 1.00 | <1e-4 | PASS |
| img3 | IF | 253 (33) | 63501 | 4649.6 | 13.7 | 1.00 | <1e-4 | PASS |
| img3 | LOF | 86 (15) | -822 | 2436.7 | -0.3 | 0.34 | 0.9884 | FAIL |
| img3 | OC-SVM | 101 (24) | 135908 | 19971.6 | 6.8 | 0.98 | <1e-4 | PASS |

Rank drop = how many places lower the file ranks after the edit (higher means the removed features mattered more).

## B2 Stability of reasons

### Flagged = top 20%

| Disk | Model | Files in all 5 seeds | Jaccard across seeds (>= 0.7) | Files (noise) | Jaccard under 1% noise (>= 0.6) | Same top reason under noise | Result |
|---|---|---|---|---|---|---|---|
| img1 | IF | 282 | 0.89 | 307 | 0.72 | 0.91 | PASS |
| img1 | LOF | n/a (deterministic) | n/a | 105 | 0.23 | 0.13 | FAIL |
| img1 | OC-SVM | 101 | 0.96 | 106 | 0.92 | 0.99 | PASS |
| img2 | IF | 279 | 0.80 | 319 | 0.71 | 0.91 | PASS |
| img2 | LOF | n/a (deterministic) | n/a | 108 | 0.33 | 0.31 | FAIL |
| img2 | OC-SVM | 100 | 0.90 | 119 | 0.86 | 0.97 | PASS |
| img3 | IF | 303 | 0.85 | 334 | 0.73 | 0.90 | PASS |
| img3 | LOF | n/a (deterministic) | n/a | 119 | 0.17 | 0.08 | FAIL |
| img3 | OC-SVM | 109 | 0.95 | 125 | 0.94 | 0.97 | PASS |

### Flagged = top 15%

| Disk | Model | Files in all 5 seeds | Jaccard across seeds (>= 0.7) | Files (noise) | Jaccard under 1% noise (>= 0.6) | Same top reason under noise | Result |
|---|---|---|---|---|---|---|---|
| img1 | IF | 209 | 0.90 | 238 | 0.74 | 0.90 | PASS |
| img1 | LOF | n/a (deterministic) | n/a | 81 | 0.23 | 0.14 | FAIL |
| img1 | OC-SVM | 73 | 0.95 | 78 | 0.91 | 1.00 | PASS |
| img2 | IF | 210 | 0.80 | 254 | 0.74 | 0.91 | PASS |
| img2 | LOF | n/a (deterministic) | n/a | 76 | 0.30 | 0.32 | FAIL |
| img2 | OC-SVM | 84 | 0.90 | 97 | 0.84 | 0.97 | PASS |
| img3 | IF | 212 | 0.87 | 253 | 0.75 | 0.91 | PASS |
| img3 | LOF | n/a (deterministic) | n/a | 86 | 0.17 | 0.07 | FAIL |
| img3 | OC-SVM | 80 | 0.96 | 101 | 0.95 | 0.97 | PASS |

For LOF the seed test does not exist, so its result rests on the noise test alone.

## B3 Planted attacks (known cause)

### Detection and attribution, flagged = top 20%

| Disk | Model | Attack | Detected (%) | Attribution hit, of detected (%) | Attribution hit, of all planted (%) | Result (all types, of detected >= 80) |
|---|---|---|---|---|---|---|
| img1 | IF | P1 timestamp forgery | 100.0 | 100.0 | 100.0 |  |
| img1 | IF | P2 hidden executable in temp | 42.0 | 100.0 | 100.0 |  |
| img1 | IF | P3 bulk-wipe burst | 20.0 | 30.0 | 37.0 |  |
| img1 | IF | ALL | 54.0 | 91.5 | 79.0 | PASS |
| img1 | LOF | P1 timestamp forgery | 100.0 | 70.0 | 70.0 |  |
| img1 | LOF | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img1 | LOF | P3 bulk-wipe burst | 60.0 | 66.7 | 75.0 |  |
| img1 | LOF | ALL | 86.7 | 80.8 | 81.7 | PASS |
| img1 | OC-SVM | P1 timestamp forgery | 100.0 | 100.0 | 100.0 |  |
| img1 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img1 | OC-SVM | P3 bulk-wipe burst | 35.0 | 71.4 | 90.0 |  |
| img1 | OC-SVM | ALL | 78.3 | 95.7 | 96.7 | PASS |
| img2 | IF | P1 timestamp forgery | 9.0 | 100.0 | 100.0 |  |
| img2 | IF | P2 hidden executable in temp | 94.0 | 100.0 | 100.0 |  |
| img2 | IF | P3 bulk-wipe burst | 34.0 | 100.0 | 100.0 |  |
| img2 | IF | ALL | 45.7 | 100.0 | 100.0 | PASS |
| img2 | LOF | P1 timestamp forgery | 55.0 | 100.0 | 100.0 |  |
| img2 | LOF | P2 hidden executable in temp | 80.0 | 100.0 | 100.0 |  |
| img2 | LOF | P3 bulk-wipe burst | 95.0 | 63.2 | 60.0 |  |
| img2 | LOF | ALL | 76.7 | 84.8 | 86.7 | PASS |
| img2 | OC-SVM | P1 timestamp forgery | 40.0 | 87.5 | 95.0 |  |
| img2 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img2 | OC-SVM | P3 bulk-wipe burst | 100.0 | 100.0 | 100.0 |  |
| img2 | OC-SVM | ALL | 80.0 | 97.9 | 98.3 | PASS |
| img3 | IF | P1 timestamp forgery | 44.0 | 100.0 | 100.0 |  |
| img3 | IF | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img3 | IF | P3 bulk-wipe burst | 7.0 | 100.0 | 99.0 |  |
| img3 | IF | ALL | 50.3 | 100.0 | 99.7 | PASS |
| img3 | LOF | P1 timestamp forgery | 95.0 | 63.2 | 65.0 |  |
| img3 | LOF | P2 hidden executable in temp | 100.0 | 15.0 | 15.0 |  |
| img3 | LOF | P3 bulk-wipe burst | 100.0 | 25.0 | 25.0 |  |
| img3 | LOF | ALL | 98.3 | 33.9 | 35.0 | FAIL |
| img3 | OC-SVM | P1 timestamp forgery | 55.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | P3 bulk-wipe burst | 75.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | ALL | 76.7 | 100.0 | 100.0 | PASS |

### Detection and attribution, flagged = top 15%

| Disk | Model | Attack | Detected (%) | Attribution hit, of detected (%) | Attribution hit, of all planted (%) | Result (all types, of detected >= 80) |
|---|---|---|---|---|---|---|
| img1 | IF | P1 timestamp forgery | 88.0 | 100.0 | 100.0 |  |
| img1 | IF | P2 hidden executable in temp | 17.0 | 100.0 | 100.0 |  |
| img1 | IF | P3 bulk-wipe burst | 2.0 | 50.0 | 37.0 |  |
| img1 | IF | ALL | 35.7 | 99.1 | 79.0 | PASS |
| img1 | LOF | P1 timestamp forgery | 100.0 | 70.0 | 70.0 |  |
| img1 | LOF | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img1 | LOF | P3 bulk-wipe burst | 55.0 | 63.6 | 75.0 |  |
| img1 | LOF | ALL | 85.0 | 80.4 | 81.7 | PASS |
| img1 | OC-SVM | P1 timestamp forgery | 100.0 | 100.0 | 100.0 |  |
| img1 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img1 | OC-SVM | P3 bulk-wipe burst | 25.0 | 60.0 | 90.0 |  |
| img1 | OC-SVM | ALL | 75.0 | 95.6 | 96.7 | PASS |
| img2 | IF | P1 timestamp forgery | 6.0 | 100.0 | 100.0 |  |
| img2 | IF | P2 hidden executable in temp | 81.0 | 100.0 | 100.0 |  |
| img2 | IF | P3 bulk-wipe burst | 12.0 | 100.0 | 100.0 |  |
| img2 | IF | ALL | 33.0 | 100.0 | 100.0 | PASS |
| img2 | LOF | P1 timestamp forgery | 50.0 | 100.0 | 100.0 |  |
| img2 | LOF | P2 hidden executable in temp | 15.0 | 100.0 | 100.0 |  |
| img2 | LOF | P3 bulk-wipe burst | 95.0 | 63.2 | 60.0 |  |
| img2 | LOF | ALL | 53.3 | 78.1 | 86.7 | FAIL |
| img2 | OC-SVM | P1 timestamp forgery | 35.0 | 85.7 | 95.0 |  |
| img2 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img2 | OC-SVM | P3 bulk-wipe burst | 95.0 | 100.0 | 100.0 |  |
| img2 | OC-SVM | ALL | 76.7 | 97.8 | 98.3 | PASS |
| img3 | IF | P1 timestamp forgery | 32.0 | 100.0 | 100.0 |  |
| img3 | IF | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img3 | IF | P3 bulk-wipe burst | 1.0 | 100.0 | 99.0 |  |
| img3 | IF | ALL | 44.3 | 100.0 | 99.7 | PASS |
| img3 | LOF | P1 timestamp forgery | 95.0 | 63.2 | 65.0 |  |
| img3 | LOF | P2 hidden executable in temp | 100.0 | 15.0 | 15.0 |  |
| img3 | LOF | P3 bulk-wipe burst | 100.0 | 25.0 | 25.0 |  |
| img3 | LOF | ALL | 98.3 | 33.9 | 35.0 | FAIL |
| img3 | OC-SVM | P1 timestamp forgery | 50.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | P2 hidden executable in temp | 100.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | P3 bulk-wipe burst | 75.0 | 100.0 | 100.0 |  |
| img3 | OC-SVM | ALL | 75.0 | 100.0 | 100.0 | PASS |

Planted values for Isolation Forest are means over the 5 seeds (per-seed values are in results.json).

## Forensic sense (descriptive, no pass rule)

Among the real targets caught in the top 20% (best copy of each target), the share whose single strongest reason is not filename_entropy, path_depth or size alone, and the share whose top-3 includes a feature a forensic examiner would expect for that kind of target (hand-written list carried over from the earlier trust study).

| Disk | Model | Targets caught | Top reason is a forensic feature | Top-3 includes an expected feature |
|---|---|---|---|---|
| img1 | IF | 7 | 0.86 | 0.71 |
| img1 | LOF | 5 | 0.80 | 0.20 |
| img1 | OC-SVM | 6 | 0.83 | 1.00 |
| img2 | IF | 19 | 0.95 | 0.95 |
| img2 | LOF | 8 | 0.88 | 0.75 |
| img2 | OC-SVM | 19 | 1.00 | 0.95 |
| img3 | IF | 34 | 0.82 | 1.00 |
| img3 | LOF | 19 | 0.95 | 0.47 |
| img3 | OC-SVM | 25 | 1.00 | 1.00 |

_Reading it honestly: see the per-target detail in site.json; a high share here does not prove the reason is right, only that it is not an obvious artefact._

## Runtime

Per-disk seconds: img1 144.8, img2 217.3, img3 260.8 (disks ran in parallel).
