# Audit of the earlier ForensIQ results

Every claim below was checked against a fresh run from the raw disk images (NIST CFReDS Hacking Case, NIST CFReDS Data Leakage PC, Digital Corpora 2018 Lone Wolf) and, where relevant, against the old outputs saved in git commit `0b6f08d`. Detailed evidence is in:

- `reports/image1_audit/` (Image 1 questions, retrained ablations, v1 vs v2) — `image1_audit.py`
- `reports/shap_feature_firing/` (which features fire and why, all 3 images) — `shap_feature_firing.py`
- `reports/threshold_sweep/` (5–15% and 5–100% sweeps, 3 randomizations) — `threshold_sweep.py`
- `reports/multimodel_eval/` (3 models × 3 images × 23 features) — `multimodel_eval.py`

Claims fall into three groups.

## 1. Stale: correct for the old code, wrong for the current pipeline

These numbers do match the old Image 1 outputs in commit `0b6f08d`, which were produced by `feature_eng2.py` before the path and reference-time fixes. They no longer describe the pipeline as it runs today.

| Claim | Old outputs (`0b6f08d`) | Fresh run |
|:---|:---|:---|
| Cain.exe rank #4, score −0.1562 | #4, −0.1562 | #136, −0.110 |
| ethereal.exe #60 / NetStumbler.exe #191 | #60 / #191 | #148 / #322 |
| defrag.exe #580, UNWISE.EXE #525 (flagged) | #580 / #526 | #2,260 / #1,823 (not flagged) |
| 123wasp.exe #603, uninst-anonymizer.exe #647 | #603 / #647 | #2,270 / #1,289 |
| Score range [−0.1649, +0.2412] | same | [−0.1673, +0.2099] |
| "5.5% gives 100% category recall" | holds on old ranks | 5 of 8 families at 5.5%; all 8 only at 19.2% |
| 6 of 17 features fire on Image 1 (is_exe 1.81 …) | old SHAP file | 8 of 17 fire, different values |
| Image 2: 6/17 fired, delta_ab 2.589 … | matches old `features/shap_values.npy` | 7/17 fired, different values |

## 2. Wrong: not supported by any data or code

| Claim | What the data shows |
|:---|:---|
| All three images were "already extracted and evaluated" in the repo | Only Image 2 artifacts and 8,306 flagged Image 3 rows existed; no full Image 3 data |
| 3-model, 23-feature table (IF 7/7, 18/19, 22/24; LOF 6/7, 16/19, 19/24; OC-SVM 5/7, 9/19, 13/24) and "Isolation Forest wins" | No LOF/OC-SVM code existed. Fresh result: OC-SVM best at a 5% budget (5/7, 19/19, 25/34), IF second (5/7, 17/19, 8/34), LOF last (1/7, 2/19, 2/34); at a 15% budget IF on 23 features is best overall |
| Timestomping "125 / 512 / 5,396 files", "13 future_m files" | `future_m` can never be 1 (compared to the image's own newest time); counts not produced by any code |
| "591 /Windows/Temp/INS_*.TMP files" on Image 3 | 4 such files on the disk |
| Image 1: "9 of 17 fired including sniffer_tool and credential_tool" | Both are constant on every row; constants never fire |
| 23-feature SHAP magnitudes (sniffer_tool 2.84, filename_entropy 2.14 …) and coverage counts for the 6 new features | Do not match the fresh run; 4 of 6 coverage counts are wrong |
| Feature ablation "Active-6 retains 589/589, drop is_exe 374/589, drop MACB 107/589" | Computed by subtracting SHAP values, which is not an ablation. Retrained: 558, 514, 238 (seed noise alone moves the set by ±20) |
| v1→v2 "Ethereal 16→25", "timestomped 219→300", Jaccard 0.5756 | v1 flags 43 Ethereal files; 226→301; Jaccard 0.5855 (v2 Anonymizer 65/70 and NetStumbler 1→11 are correct) |
| Chain of custody 102/102, 182 event-log records | 96/96 on the fresh run; 0 event records parsed on Image 1 (old file is empty too) |
| MITRE T1070.001 "78 work-hour log gaps" | Not present in the mapping |
| Remediation filename mismatch in `forensiq_report.py` | Both files use `remediate_credentials.ps1` |
| Threshold sweep: "11% knee", 3 randomizations agree on 44/49 steps | No script produced the old files; the old randomization file has 15/20 rows identical. Fresh IF-17 curve keeps climbing to ~21%. The earlier 25% figure matches the 17-feature IF (fresh run: about 21%) |
| "delta_si_fn mismatch is 100% proof of tampering" | Mismatch is normal on these disks (non-zero on 84% of Image 2 files) |
| "MFT parsing takes under 30 seconds" | 0.5 s, 13 s and 110 s for Images 1, 2, 3 |

## 3. Wrong reasoning

- Silent features were explained by attacker behaviour ("PowerShell did not exist on XP", "the insider did not use sniffers"). The real cause is the code: `credential_tool`, `sniffer_tool`, `powershell_exec`, `cmd_exec`, `script_host` and `usb_present` are one per-disk value copied onto every file, so they are constant and can never fire. On Image 1 `credential_tool` and `sniffer_tool` are 1 for every file and are still silent.
- Accuracy was reported as a model score. With a fixed 5% budget and rare targets, every model scores about 95% by construction; it does not separate models.

## 4. What is actually true (fresh run)

**Three models, 23 features, 5% budget (targets caught)**

| Image | Isolation Forest | LOF | One-Class SVM |
|:---|:---:|:---:|:---:|
| 1 · XP Hacking (7 families) | 5/7 | 1/7 | 5/7 |
| 2 · Win7 Data Leakage (19) | 17/19 | 2/19 | 19/19 |
| 3 · Lone Wolf (34, examiner-tagged) | 8/34 | 2/34 | 25/34 |

**Real setup bugs found**

1. Six tool/USB features are disk-level constants (always zero SHAP).
2. `future_m` compares against the image's own newest timestamp, so it is always 0.
3. `is_deleted` is always 0: the extractor reads `meta.flags`, but most deleted entries have no metadata (365 / 6,287 / 15,717 deleted names on the three disks are missed).
4. `usb_present` is 1 on every disk because the extractor always writes `usb_devices.txt`.
5. The `cmd` prefetch keyword also matches `MPCMDRUN` (Defender).
6. `after_hours_touch` uses UTC, so 85% of Image 2 files count as after-hours.
7. Fewer prefetch files are extracted than the MFT lists (98 of 130 on Image 2, 172 of 233 on Image 3).

**Threshold (4th ablation, Images 2 and 3, 5 runs × 3 randomizations)**

- "100% at 5.5%" is not general. It holds only for One-Class SVM on Image 2.
- Threshold for ≥ 90% recall, agreeing across all three randomizations: IF-23 11% (Image 2) and 13–15% (Image 3); IF-17 21% (Image 2); OC-SVM 5% (Image 2) but 21–23% (Image 3); LOF never below ~50%.
- Isolation Forest randomizations agree on 90–98% of thresholds; LOF and Image 3 OC-SVM do not.

### Which model and budget to use

- At a strict 5% review budget, One-Class SVM catches the most targets (5/7, 19/19, 25/34; mean target recall 81.7% vs IF 61.5%, LOF 10.2%).
- Best overall is Isolation Forest on all 23 features at a 15% budget: 94.7% on Image 2 and 99.4% on Image 3, and its 3 randomizations agree on 90–98% of thresholds.
- OC-SVM on Image 3 reaches only 80.6% at 15% and needs about 23% to reach 90%. LOF never reaches 90% below about 50%.
- The earlier "25%" threshold came from the original 17-feature Isolation Forest on Image 2. A fresh rerun of that model reaches 90% at about 21% (93.7% at 21%, 94.7% at 25%, 100% only at 39%). With 23 features the same model needs 15%.
