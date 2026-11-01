# ForensIQ

ForensIQ ranks the files on a Windows disk image so an examiner can review the most unusual ones first. It reads the image without mounting it, extracts file-system, event-log, prefetch and registry metadata, builds one feature row per file, and scores each file with unsupervised anomaly detectors. Isolation Forest is the main model. SHAP shows which features pushed each file up the ranking. The output is an ordered list, not a verdict.

ForensIQ was evaluated on three public disk images: NIST CFReDS Hacking Case (Windows XP), NIST CFReDS Data Leakage (Windows 7), and Digital Corpora Lone Wolf (Windows 10). Results site: https://forensiq-triage-lab.vercel.app. The evaluation was pre-registered; see [reports/study_v3/PROTOCOL.md](reports/study_v3/PROTOCOL.md).

## Main result

Isolation Forest, 19 features (17 clean features plus 2 burst features). A "budget" is the top share of files by score that an examiner reviews. A target counts as caught if any of its files is inside the budget.

| Disk | Targets | Caught at 20%, all 5 seeds | Caught at 15%, mean of 5 seeds | Knee (90% of targets), mean |
|---|---|---|---|---|
| img1: XP hacking (SCHARDT.001) | 7 | 7 of 7 | 7.0 | 12.4% of disk |
| img2: Win7 data leakage | 19 | 19 of 19 | 19.0 | 9.9% of disk |
| img3: Win10 Lone Wolf | 34 | 34 of 34 | 32.4 | 13.2% of disk |

The knee is the smallest budget that reaches 90% of targets. Seeds are 42, 1337, 9999, 7 and 2024.

## What was tested

Each test has a pass rule written in [PROTOCOL.md](reports/study_v3/PROTOCOL.md) before the results were computed. Results below are for the final feature set unless noted. IF is Isolation Forest, LOF is Local Outlier Factor, and OC-SVM is One-Class SVM.

- **A1 Feature groups.** Does the result depend on one group of features? **FAIL.** Removing the temporal group leaves IF's recall unchanged or higher on all three disks. Removing the path/file or execution/activity group lowers recall. See [A1](reports/study_v3/final/A1/summary.md).
- **A2 Threshold and seed stability.** Are the knee and the headline recall stable across seeds? **FAIL.** IF catches every target in every seed at 20%, but its knee moves 3.9 to 5.2 points across seeds against a 2-point limit. LOF has a stable knee but misses targets at both budgets. OC-SVM fails both parts. See [A2](reports/study_v3/final/A2/summary.md).
- **A3 Feature sets.** Which features are kept? The drop-one rule was **FAILED** as written: applied to all failing features at once, it removed 16 of 17 clean features, which is degenerate. The final set was chosen by the burst rule, which **PASSED**: burst features raise IF recall on all three disks and lower it on none. See [AMENDMENT.md](reports/study_v3/AMENDMENT.md) and [A3](reports/study_v3/A3/summary.md).
- **A4 Models versus plain rules.** Does the model beat the best rule that uses no ground truth and no learning? **PASS for IF at 15%, FAIL at 20%.** At 15%, IF beats the best rule on img1 and img2 but ties it on img3 (34 of 34). At 20%, it wins only on img2. LOF and OC-SVM fail at both budgets. See [A4](reports/study_v3/final/A4/summary.md).
- **A5 Hyperparameters.** Does headline recall stay within one target across tested settings? **FAIL.** IF changes by at most 0.6, 0.4 and 1.6 targets at 15% (0 at 20%); the rule allows 1. LOF and OC-SVM change by much more. See [A5](reports/study_v3/final/A5/summary.md).
- **A6 Cross-disk transfer.** Does a budget tuned on one disk work on the other two? **FAIL.** A knee learned on img2 catches 75.9% of targets on img3 for IF. A fixed 20% budget catches all targets on each disk for IF, but that is not the pre-registered test. See [A6](reports/study_v3/final/A6/summary.md).
- **A7 Robustness.** **FAIL overall.** Dropping a random 10% of non-target files passes. Adding 1-hour Gaussian noise to timestamps fails: recall falls by 10 to 14% (relative) on img1 and img3. See [A7](reports/study_v3/final/A7/summary.md).
- **B1 Explanation faithfulness.** Does removing the SHAP top-3 features push a flagged file down more than removing 3 random features? **FAIL at 20%** (6 of 9 disk-model cells pass). IF and OC-SVM pass on all three disks; LOF fails on all three. See [B](reports/study_v3/final/B/summary.md).
- **B2 Explanation stability.** Do the top-3 reasons agree across seeds and under 1% input noise? **FAIL at 20%** (6 of 9 cells). IF and OC-SVM pass; LOF fails on all three disks under noise.
- **B3 Planted attacks.** Does SHAP name the planted cause for planted files that get flagged? **FAIL at 20%** (8 of 9 cells). The one failing cell is LOF on img3, which names the planted cause for 34% of detected files against an 80% rule.
- **C1 Remediation.** Does every recommendation cite at least one flagged file? **PASS** (22 of 22 recommendations). No generated command targets the disk image. Against the known scenario, the new trigger logic (v2) has pooled precision 0.54 and recall 0.88 at 20%, versus 0.25 and 0.38 for the old logic (v1). The sample is small: 12 to 13 expected indicators in total. See [C1](reports/study_v3/final/C1/summary.md).

## Known limits

- **Knee position.** For IF, the knee moves 3.9 to 5.2 points across seeds on these disks. Treat it as an approximate budget, roughly 10 to 15% of the disk, not a fixed cut-off.
- **Lone Wolf is easy for simple rules.** Its evidence list is examiner-tagged files in the user's home folder, so a plain user-folder rule also scores 34 of 34. The plain location rule in A4 also catches all 34 at both budgets. These results do not show that the model finds anything a simple rule misses on this disk.
- **Timestamp features add little for IF.** A1 shows the temporal group contributes nothing measurable to IF's recall.
- **Timestamp noise.** One-hour timestamp noise lowers recall by 10 to 14% (A7). The burst features count files that share a modified second or minute, so they depend on the same timestamps; the A7 noise test rebuilds them from the noisy times, and they lose most of their signal. Real disk timestamps are recorded to the second, so this is a stress test rather than a typical condition.
- **LOF does not give usable explanations.** Its SHAP reasons fail the faithfulness and stability tests on all three disks, and fail the planted-cause test on img3. Only IF and OC-SVM pass B1 to B3 on every disk.
- **Planted attacks.** At 20%, IF flags 46 to 54% of planted files, depending on the disk. For those it flags, it names the planted cause in 92 to 100% of cases.
- **Small ground truth.** There are 7, 19 and 34 targets, taken from the public case descriptions and the target lists in `multimodel_eval.py`. One target is 3 to 14 percentage points of recall, so small differences are noise.
- **Remediation output is advice for live systems only.** The generated steps are meant for a live Windows system, and system-changing commands are commented out. The remediation scripts were never run on evidence images.

## Reproduce

### Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### Disk images and artifacts

Disk images are not in this repository. See [IMAGE_SETUP_GUIDE.md](IMAGE_SETUP_GUIDE.md) for file names, formats and partition offsets. Extracted artifacts are read from `runs/img1/artifacts`, `runs/img2/artifacts` and `runs/img3/artifacts`; `runs/` is git-ignored.

```bash
.venv/bin/python run_pipeline.py --image path/to/image.dd    # extract artifacts and run the pipeline
.venv/bin/python run_pipeline.py --skip-extraction           # reuse existing artifacts
.venv/bin/python convert_e01.py --image path/to/image.E01    # optional: convert E01 to raw .dd
.venv/bin/python evaluate_baselines.py                       # plain-rule baseline comparison
```

### Study v3

The v3 scripts must run with the final feature set (19 features). Without `FORENSIQ_FEATURE_SET=final`, the shared code falls back to the 17-feature clean set.

```bash
export FORENSIQ_FEATURE_SET=final
.venv/bin/python study_v3_feature_audit.py --set clean    # writes reports/study_v3/feature_audit_clean.md
.venv/bin/python study_v3_reliability_a.py               # A2, A4, A6
.venv/bin/python study_v3_reliability_b.py               # A1, A3, A5, A7
.venv/bin/python study_v3_explain.py                     # B1-B3, all three disks in parallel
.venv/bin/python study_v3_remediation_eval.py            # C1
```

Results are written to `reports/study_v3/final/`. `study_v3_explain.py` also accepts `--disk img1` (one disk) and `--merge` (rebuild the summary from saved per-disk results). Per-disk runtime for the explainability study was 145 to 261 seconds.

### Results website

```bash
cd web
npm install
npm run dev
```

The site reads `site/data.json`, copied into `web/src/data/` by `npm run sync-data`.

## Repository layout

- `run_pipeline.py`: end-to-end entry point.
- `extractor.py`, `extractor_for_evt.py`, `extractor_for_evtx.py`, `convert_e01.py`, `image_utils.py`: image access and artifact extraction.
- `feature_engineering.py`, `burst_detection.py`: per-file features, including the burst features.
- `anomaly_detection.py`: unsupervised models. `xai_shap.py`: SHAP explanations.
- `forensiq_report.py`, `timeline.py`, `chain_of_custody.py`: reports, timelines and custody records.
- `remediation.py` (v1), `remediation_v2.py` (current): remediation playbooks.
- `multimodel_eval.py`: ground-truth target lists, model definitions and shared evaluation code. `evaluate_baselines.py`: plain-rule baselines.
- `study_v3_common.py` and `study_v3_*.py`: the pre-registered v3 study.
- `reports/study_v3/`: protocol, amendment, feature audit, and per-test results (`final/` holds the final feature set).
- `web/`: results site (React and Vite). `site/`: exported site data. `export_site_data.py`: export.
- `features/`, `models/`, `features_dataleak/`, `models_dataleak/`, `reports_dataleak/`: outputs from earlier runs.
- `runs/`, `images/`, `.cache/`: generated or local data, git-ignored.
