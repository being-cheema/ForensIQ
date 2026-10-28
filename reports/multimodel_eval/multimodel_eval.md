# ForensIQ Multi-Model Benchmark (Isolation Forest vs. LOF vs. One-Class SVM)

All numbers below are produced by `multimodel_eval.py` from the extracted MFT / Prefetch artifacts
(`results_main.csv`, `results_ablation.csv`, `results.json`). Same review budget for every model:
the top 5% most suspicious files. Features are standardised; ranking score is the model's anomaly score.

## Scope and limits (read first)

| Item | Status |
|:---|:---|
| Image 1 (XP Hacking, 11,773 files) | Run |
| Image 2 (Win7 Data Leakage, 85,017 files) | Run |
| Image 3 (Win10 Lone Wolf) | **Not run** - no extracted artifacts on this machine (needs the E01 set) |
| Feature count | **22 of 23**. `delta_si_fn` needs `$FILE_NAME` timestamps, which the saved MFT json does not contain. `extractor.py` now saves them (`fn_m_time`, `fn_cr_time`); untested until the image is re-extracted. |
| Image 1 targets | 7 families reconstructed from case notes (15 file records); a family counts as caught if any of its files is flagged |
| Image 2 targets | 19 targets from `evaluate_baselines.py` (38 file records) |
| `after_hours_touch` | Uses UTC hours 08:00-18:00; image time zone not applied |
| One-Class SVM | Trained on a 10,000-file random subsample (RBF kernel is O(n^2)), then scores every file |
| LOF | `n_neighbors=20`; see sensitivity below |

## 1. Main results (5% budget)

| Image | Model | Targets caught | Target recall | File recall | Accuracy | Precision | F1 |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Image 1 (K=589) | Isolation Forest | 5 / 7 | 71.4% | 46.7% | 94.99% | 1.19% | 2.32% |
| | Local Outlier Factor | 1 / 7 | 14.3% | 13.3% | 94.90% | 0.34% | 0.66% |
| | One-Class SVM | 5 / 7 | 71.4% | 46.7% | 94.99% | 1.19% | 2.32% |
| Image 2 (K=4,251) | Isolation Forest | 17 / 19 | 89.5% | 71.1% | 95.02% | 0.64% | 1.26% |
| | Local Outlier Factor | 1 / 19 | 5.3% | 2.6% | 94.96% | 0.02% | 0.05% |
| | One-Class SVM | **19 / 19** | **100.0%** | 89.5% | 95.04% | 0.80% | 1.59% |

Accuracy is about 95% for every model by construction (a fixed 5% budget on a rare-target problem), so it does not separate the models; recall, precision and F1 do.

Recall at larger budgets (target recall):

| Image | Model | 5.5% | 10% |
|:---|:---|:---:|:---:|
| Image 1 | Isolation Forest | 71.4% | 100.0% |
| | LOF | 14.3% | 57.1% |
| | One-Class SVM | 85.7% | 85.7% |
| Image 2 | Isolation Forest | 89.5% | 89.5% |
| | LOF | 5.3% | 10.5% |
| | One-Class SVM | 100.0% | 100.0% |

Isolation Forest over 5 seeds: identical recall every time (Image 1: 71.4%, Image 2: 89.5%, std 0.0).

### Robustness checks
- **One-Class SVM (5 subsample seeds):** Image 2 caught 18-19 / 19 (5k subsample) and 19 / 19 (10k, 20k). Image 1 caught 5-6 / 7.
- **LOF is very sensitive to `n_neighbors`:** Image 1: k=20 -> 1/7, 50 -> 2/7, 100 -> 3/7, 300 -> 5/7. Image 2: k=20 -> 1/19, 50 -> 3/19, 100 -> 4/19, 300 -> 0/19. 13% of Image 2 rows are exact duplicates, which distorts LOF. LOF is the weakest model at every setting tried.

## 2. Timestomping and insider attack

| Image | Model | Timestomping | Insider attack |
|:---|:---|:---|:---|
| Image 1 | Isolation Forest | YES (NMEM/NGETTIME flagged) | N/A (external intrusion) |
| | LOF | NO (NMEM/NGETTIME missed) | N/A |
| | One-Class SVM | YES | N/A |
| Image 2 | Isolation Forest | YES (Eraser.exe flagged) | CONFIRMED (17/19) |
| | LOF | NO | NOT DETECTED (1/19) |
| | One-Class SVM | YES | CONFIRMED (19/19) |

Rules: timestomping is YES when a ground-truth timestomped file is in the flagged set (Image 1: NMEM/NGETTIME; Image 2: Eraser.exe). That is one file per image, so treat it as supporting evidence, not proof of a general timestomping detector. Insider attack is CONFIRMED when at least half of the insider targets are flagged, PARTIAL at 25-50%.
`future_m` flagged 0 files in both images. The count of flagged files with a backdated-modified-time signature is in `results.json`.

## 3. Ablation (Image 2, target recall at 5% budget, 22 features)

| Feature set | n | Isolation Forest | LOF | One-Class SVM |
|:---|:--:|:---:|:---:|:---:|
| Full | 22 | 17/19 | 1/19 | 19/19 |
| Legacy 17 only | 17 | 7/19 | 8/19 | 9/19 |
| Only Temporal | 6 | 1/19 | 5/19 | 0/19 |
| Without Temporal | 16 | 18/19 | 3/19 | 19/19 |
| Only Path/File | 9 | 17/19 | 3/19 | 18/19 |
| Without Path/File | 13 | 2/19 | 7/19 | 4/19 |
| Only Execution/Tool | 7 | 4/19 | 2/19 | 4/19 |
| Without Execution/Tool | 15 | 16/19 | 4/19 | 18/19 |
| Full minus `is_shortcut_or_trace` | 21 | 6/19 | 2/19 | 10/19 |
| Full minus `per_file_prefetch_hit` | 21 | 17/19 | 4/19 | 18/19 |
| Full minus `after_hours_touch` | 21 | 17/19 | 1/19 | 19/19 |
| Full minus `filename_entropy` | 21 | 17/19 | 5/19 | 19/19 |
| Full minus `path_depth` | 21 | 17/19 | 0/19 | 17/19 |

Reading it: going from the legacy 17 features to the new set lifts Isolation Forest from 7/19 to 17/19 and One-Class SVM from 9/19 to 19/19. The gain comes from the Path/File group, mainly `is_shortcut_or_trace` (removing it drops IF from 17 to 6 and OC-SVM from 19 to 10). The Temporal group on its own is weak (IF 1/19). Image 1 ablations are in `results_ablation.csv`.

## 4. SHAP

SHAP was computed for all three models on both images (`shap/`). Isolation Forest uses TreeSHAP on a 20,000-file sample plus caught targets; LOF and OC-SVM use KernelSHAP (50 background rows, 300 samples) on the caught targets only, so their importances are not directly comparable to Isolation Forest's. For LOF, the explainer uses a novelty-mode refit.

Active features (mean |SHAP| > 0): Isolation Forest 14/22 (Image 1) and 13/22 (Image 2). Top Isolation Forest features on Image 2: `is_exe` 0.54, `after_hours_touch` 0.51, `path_depth` 0.50, `delta_ab` 0.44, `delta_mc` 0.32.

## 5. Which model performs best

On the 22 features available, **One-Class SVM is best on Image 2 (19/19) and ties Isolation Forest on Image 1 (5/7)**; Isolation Forest is a close, stable second (it never varied across seeds); **LOF is clearly worst**. Image 3 is untested, so this is a two-image result. The ranking does not match the earlier draft (which put Isolation Forest first, LOF second and One-Class SVM last).

## Tool output

CLI-style detections per image: `img1_tool_output.txt`, `img2_tool_output.txt`.
