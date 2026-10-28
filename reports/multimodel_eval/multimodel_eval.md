# ForensIQ Multi-Model Benchmark (Isolation Forest vs. LOF vs. One-Class SVM, 23-feature baseline)

All numbers are produced by `multimodel_eval.py` and `robustness_check.py` from artifacts extracted directly from the raw disk images.

## 1. Scope and limits

- Images evaluated: Image 1, Image 2, Image 3.
- Every image was re-extracted from its raw disk image (NIST CFReDS Hacking Case, NIST CFReDS Data Leakage Case, Digital Corpora 2018 Lone Wolf), with `$FILE_NAME` timestamps read from the MFT so that `delta_si_fn` is computed.
- Targets: Image 1: 7 target families (15 files) reconstructed from the SCHARDT case notes | Image 2: 19 targets (38 files) from the repository's CFReDS ground-truth list | Image 3: 34 files (125 copies) that the scenario author's own examiner tagged Evidence / Of interest / Bookmark (published openly by Digital Corpora), plus the Chrome Login Data database; the teacher's guide answer key was not available.
- A target counts as caught when any of its files is in the flagged set. Same review budget for every model: the top 5% of files.
- One-Class SVM is trained on a 10,000-file random subsample (RBF kernel is O(n^2)) and scores every file; LOF uses 20 neighbours; Isolation Forest 200 trees.
- `after_hours_touch` uses UTC hours 08:00-18:00; the image's own time zone is not applied.
- Constant features: Image 1: 8 of 23 features constant (future_m, is_deleted, credential_tool, sniffer_tool, powershell_exec, cmd_exec, script_host, usb_present); Image 2: 8 of 23 features constant (future_m, is_deleted, credential_tool, sniffer_tool, powershell_exec, cmd_exec, script_host, usb_present); Image 3: 8 of 23 features constant (future_m, is_deleted, credential_tool, sniffer_tool, powershell_exec, cmd_exec, script_host, usb_present). The model therefore works with fewer than 23 active features per image.

## 2. Results at the 5% review budget

| Image | Model | Targets caught | Target recall | File recall | Accuracy | Precision | F1 |
|:---|:---|:---|:---|:---|:---|:---|:---|
| Image 1: XP Hacking (SCHARDT.001) (11,773 files, K=589) | Isolation Forest | 5/7 | 71.4% | 46.7% | 94.99% | 1.19% | 2.32% |
|  | Local Outlier Factor | 1/7 | 14.3% | 13.3% | 94.90% | 0.34% | 0.66% |
|  | One-Class SVM | 5/7 | 71.4% | 46.7% | 94.99% | 1.19% | 2.32% |
| Image 2: Win7 Data Leakage (85,017 files, K=4,251) | Isolation Forest | 17/19 | 89.5% | 71.1% | 95.02% | 0.64% | 1.26% |
|  | Local Outlier Factor | 2/19 | 10.5% | 5.3% | 94.96% | 0.05% | 0.09% |
|  | One-Class SVM | 19/19 | 100.0% | 89.5% | 95.04% | 0.80% | 1.59% |
| Image 3: Win10 Lone Wolf (166,110 files, K=8,306) | Isolation Forest | 8/34 | 23.5% | 18.8% | 94.97% | 0.19% | 0.38% |
|  | Local Outlier Factor | 2/34 | 5.9% | 5.9% | 94.95% | 0.06% | 0.12% |
|  | One-Class SVM | 25/34 | 73.5% | 76.5% | 95.03% | 0.78% | 1.55% |

Accuracy is about 95% for every model because the budget is fixed at 5% and targets are rare; recall, precision and F1 are the discriminating metrics.

Mean target recall across images: OC-SVM 81.7%, IF 61.5%, LOF 10.2%.

## 3. Recall at larger budgets

| Image | Model | 5% | 5.5% | 10% |
|:---|:---|:---|:---|:---|
| Image 1 | Isolation Forest | 71.4% | 71.4% | 100.0% |
| Image 1 | Local Outlier Factor | 14.3% | 14.3% | 57.1% |
| Image 1 | One-Class SVM | 71.4% | 71.4% | 85.7% |
| Image 2 | Isolation Forest | 89.5% | 89.5% | 89.5% |
| Image 2 | Local Outlier Factor | 10.5% | 10.5% | 15.8% |
| Image 2 | One-Class SVM | 100.0% | 100.0% | 100.0% |
| Image 3 | Isolation Forest | 23.5% | 26.5% | 82.4% |
| Image 3 | Local Outlier Factor | 5.9% | 5.9% | 8.8% |
| Image 3 | One-Class SVM | 73.5% | 73.5% | 73.5% |

## 4. Timestomping and insider attack

| Image | Model | Timestomping | Known timestomped file flagged | SI/FN mismatches in flagged set | Insider attack |
|:---|:---|:---|:---|:---|:---|
| Image 1 | Isolation Forest | YES | NMEM/NGETTIME (timestomped Novell tools) | 373 | N/A (external intrusion) |
| Image 1 | Local Outlier Factor | NO | - | 93 | N/A (external intrusion) |
| Image 1 | One-Class SVM | YES | NMEM/NGETTIME (timestomped Novell tools) | 292 | N/A (external intrusion) |
| Image 2 | Isolation Forest | YES | Eraser.exe (Installed Wiping Tool) | 2614 | CONFIRMED |
| Image 2 | Local Outlier Factor | NO | - | 3144 | NOT DETECTED |
| Image 2 | One-Class SVM | YES | Eraser.exe (Installed Wiping Tool) | 2862 | CONFIRMED |
| Image 3 | Isolation Forest | UNVERIFIED | - | 3282 | NOT DETECTED |
| Image 3 | Local Outlier Factor | UNVERIFIED | - | 4214 | NOT DETECTED |
| Image 3 | One-Class SVM | UNVERIFIED | - | 3333 | CONFIRMED |

Timestomping is YES when a ground-truth timestomped file is in the flagged set (Image 1: NMEM/NGETTIME; Image 2: Eraser.exe), otherwise UNVERIFIED because no ground-truth timestomped file is defined. The `$STANDARD_INFORMATION` vs `$FILE_NAME` mismatch count is a hint, not proof, because ordinary file operations also cause mismatches. `future_m` is always zero because its reference time is the newest timestamp in the image. Insider attack is CONFIRMED when at least half of the targets are flagged, PARTIAL at 25-50%; it is not applicable to the external intrusion in Image 1.

## 5. Ablation, Image 1 (targets caught)

| Feature set | n | Isolation Forest | LOF | One-Class SVM |
|:---|:---|:---|:---|:---|
| Full (all available) | 23 | 5/7 | 1/7 | 5/7 |
| Legacy 17 only | 17 | 5/7 | 5/7 | 3/7 |
| Only Temporal | 7 | 3/7 | 6/7 | 2/7 |
| Without Temporal | 16 | 5/7 | 1/7 | 5/7 |
| Only Path/File | 9 | 3/7 | 1/7 | 2/7 |
| Without Path/File | 14 | 6/7 | 5/7 | 3/7 |
| Only Execution/Tool | 7 | 4/7 | 0/7 | 4/7 |
| Without Execution/Tool | 16 | 3/7 | 1/7 | 3/7 |
| Full minus is_shortcut_or_trace | 22 | 5/7 | 1/7 | 5/7 |
| Full minus per_file_prefetch_hit | 22 | 3/7 | 1/7 | 3/7 |
| Full minus after_hours_touch | 22 | 5/7 | 2/7 | 5/7 |
| Full minus delta_si_fn | 22 | 5/7 | 1/7 | 5/7 |
| Full minus filename_entropy | 22 | 5/7 | 2/7 | 5/7 |
| Full minus path_depth | 22 | 5/7 | 3/7 | 5/7 |

## 5. Ablation, Image 2 (targets caught)

| Feature set | n | Isolation Forest | LOF | One-Class SVM |
|:---|:---|:---|:---|:---|
| Full (all available) | 23 | 17/19 | 2/19 | 19/19 |
| Legacy 17 only | 17 | 7/19 | 8/19 | 9/19 |
| Only Temporal | 7 | 0/19 | 5/19 | 0/19 |
| Without Temporal | 16 | 18/19 | 3/19 | 19/19 |
| Only Path/File | 9 | 17/19 | 3/19 | 18/19 |
| Without Path/File | 14 | 1/19 | 5/19 | 4/19 |
| Only Execution/Tool | 7 | 4/19 | 2/19 | 4/19 |
| Without Execution/Tool | 16 | 17/19 | 4/19 | 19/19 |
| Full minus is_shortcut_or_trace | 22 | 5/19 | 2/19 | 10/19 |
| Full minus per_file_prefetch_hit | 22 | 17/19 | 4/19 | 19/19 |
| Full minus after_hours_touch | 22 | 17/19 | 1/19 | 19/19 |
| Full minus delta_si_fn | 22 | 17/19 | 2/19 | 19/19 |
| Full minus filename_entropy | 22 | 17/19 | 4/19 | 19/19 |
| Full minus path_depth | 22 | 17/19 | 1/19 | 18/19 |

## 5. Ablation, Image 3 (targets caught)

| Feature set | n | Isolation Forest | LOF | One-Class SVM |
|:---|:---|:---|:---|:---|
| Full (all available) | 23 | 8/34 | 2/34 | 25/34 |
| Legacy 17 only | 17 | 22/34 | 5/34 | 5/34 |
| Only Temporal | 7 | 0/34 | 5/34 | 0/34 |
| Without Temporal | 16 | 23/34 | 5/34 | 33/34 |
| Only Path/File | 9 | 24/34 | 5/34 | 33/34 |
| Without Path/File | 14 | 0/34 | 5/34 | 0/34 |
| Only Execution/Tool | 7 | 0/34 | 0/34 | 0/34 |
| Without Execution/Tool | 16 | 7/34 | 2/34 | 25/34 |
| Full minus is_shortcut_or_trace | 22 | 3/34 | 2/34 | 25/34 |
| Full minus per_file_prefetch_hit | 22 | 6/34 | 2/34 | 25/34 |
| Full minus after_hours_touch | 22 | 6/34 | 2/34 | 25/34 |
| Full minus delta_si_fn | 22 | 8/34 | 2/34 | 25/34 |
| Full minus filename_entropy | 22 | 9/34 | 15/34 | 30/34 |
| Full minus path_depth | 22 | 12/34 | 6/34 | 6/34 |

## 6. SHAP

| Image | Model | Features with non-zero SHAP | Top mean |SHAP| |
|:---|:---|:---|:---|
| Image 1 | Isolation Forest | 15 / 23 | after_hours_touch 0.49, user_path 0.38, delta_mb 0.31 |
| Image 1 | Local Outlier Factor | 12 / 23 | path_depth 34224648.82, user_path 29108522.78, after_hours_touch 26174535.99 |
| Image 1 | One-Class SVM | 13 / 23 | size 5.64, per_file_prefetch_hit 5.58, is_archive 4.07 |
| Image 2 | Isolation Forest | 14 / 23 | is_exe 0.55, path_depth 0.41, delta_si_fn 0.37 |
| Image 2 | Local Outlier Factor | 10 / 23 | path_depth 455356.80, user_path 455025.73, delta_mc 438996.10 |
| Image 2 | One-Class SVM | 12 / 23 | is_shortcut_or_trace 30.39, per_file_prefetch_hit 23.02, user_path 6.81 |
| Image 3 | Isolation Forest | 15 / 23 | is_exe 0.58, after_hours_touch 0.53, delta_ab 0.35 |
| Image 3 | Local Outlier Factor | 11 / 23 | after_hours_touch 3414943.10, delta_ab 1607238.79, filename_entropy 1307470.27 |
| Image 3 | One-Class SVM | 12 / 23 | user_path 15.44, is_shortcut_or_trace 5.42, filename_entropy 2.74 |

Isolation Forest: TreeSHAP over a 20,000-file sample plus caught targets. LOF and One-Class SVM: KernelSHAP on caught targets only, so their importances are not directly comparable. SHAP explains why a file ranked high; it does not by itself establish intent.

## 7. Robustness

| Image | Targets | LOF by neighbours (targets caught) | One-Class SVM by subsample (min-max over 5 seeds) | Isolation Forest (5 seeds) | Unique rows |
|:---|:---|:---|:---|:---|:---|
| Image 1 | 7 | k=20: 1, k=50: 2, k=100: 3, k=300: 5 | n=5000: 5-6; n=10000: 5-6; n=20000: 5-5 | 5-5 | 11,125 / 11,773 |
| Image 2 | 19 | k=20: 2, k=50: 1, k=100: 5, k=300: 4 | n=5000: 19-19; n=10000: 19-19; n=20000: 19-19 | 17-17 | 73,771 / 85,017 |
| Image 3 | 34 | k=20: 2, k=50: 0, k=100: 1, k=300: 2 | n=5000: 24-26; n=10000: 24-25; n=20000: 25-25 | 7-18 | 140,438 / 166,110 |

LOF is the weakest model at every neighbour setting tried and is very sensitive to it; duplicate rows distort it.

## 8. Which model performs best, and at what budget

At the strict 5% review budget, One-Class SVM catches the most targets. Mean target recall at 5%: OC-SVM 81.7%, IF 61.5%, LOF 10.2%. At 5% the ranking is the same on every evaluated image where the targets are defined from the case record; Image 3 uses unofficial targets, so its figures are indicative only.

At a 15% budget, Isolation Forest on all 23 features is the best overall (94.7% on Image 2, 99.4% on Image 3). See reports/gemini_audit/GEMINI_AUDIT.md section 4.

## Tool output

CLI-style detections per image: `img1_tool_output.txt`, `img2_tool_output.txt`, `img3_tool_output.txt`.
