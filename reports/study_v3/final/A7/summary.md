# A7: robustness

Isolation Forest, clean features, 200 trees, all five seeds (mean over seeds). Baseline = the unperturbed clean run with the same seeds. Budgets 15% and 20% of the (possibly reduced) disk. Targets: img1 = 7, img2 = 19, img3 = 34.

What was done exactly:

- Drop variants: for each seed, a random 10% of the non-target files (variant i) or of all files (variant i-b) is removed before the model is fitted; features are recomputed over the remaining rows (standardisation on the remaining rows); the budget is a percentage of the remaining file count. "Target files" are all files matching any target pattern. In variant i-b a target whose files are all removed counts as missed.
- Noise variant: no deltas were patched. Instead every clean time feature (delta_mc, delta_mb, delta_ab, zero_size_recent, delta_si_fn, m_before_cr, after_hours_touch) was recomputed from the raw timestamps after adding independent Gaussian noise (sd 3600 s, rounded to whole seconds) to each positive m, a, c and cr time and the $FILE_NAME modified time (zero = missing timestamps stay zero). Noise seed = model seed. The rebuild was verified to reproduce the stored columns exactly at zero noise on all three disks.
- Pass rule: headline recall (targets caught / targets) falls by <= 10% relative to the baseline seed mean, at both 15% and 20%, on every disk. Absolute drop in percentage points is shown too. Verdict (overall) uses variants (i) and (ii); (i-b) is judged separately.

## (i) drop a random 10% of non-target files (all target files kept)

| disk | budget | targets | baseline mean caught | perturbed mean caught | relative drop % | drop (pp) | perturbed per seed |
|---|---|---|---|---|---|---|---|
| Image 1: XP Hacking (SCHARDT.001) | at15 | 7 | 7.0 | 6.8 | 2.86 | 2.86 | [7, 7, 7, 6, 7] |
| Image 1: XP Hacking (SCHARDT.001) | at20 | 7 | 7.0 | 7.0 | 0.0 | 0.0 | [7, 7, 7, 7, 7] |
| Image 2: Win7 Data Leakage | at15 | 19 | 19.0 | 18.8 | 1.05 | 1.05 | [19, 19, 19, 18, 19] |
| Image 2: Win7 Data Leakage | at20 | 19 | 19.0 | 19.0 | 0.0 | 0.0 | [19, 19, 19, 19, 19] |
| Image 3: Win10 Lone Wolf | at15 | 34 | 32.4 | 33.2 | -2.47 | -2.35 | [33, 33, 33, 33, 34] |
| Image 3: Win10 Lone Wolf | at20 | 34 | 34.0 | 34.0 | 0.0 | 0.0 | [34, 34, 34, 34, 34] |

Verdict: **PASS**

## (i-b) drop a random 10% of ALL files, including target files (reported separately)

| disk | budget | targets | baseline mean caught | perturbed mean caught | relative drop % | drop (pp) | perturbed per seed |
|---|---|---|---|---|---|---|---|
| Image 1: XP Hacking (SCHARDT.001) | at15 | 7 | 7.0 | 7.0 | 0.0 | 0.0 | [7, 7, 7, 7, 7] |
| Image 1: XP Hacking (SCHARDT.001) | at20 | 7 | 7.0 | 7.0 | 0.0 | 0.0 | [7, 7, 7, 7, 7] |
| Image 2: Win7 Data Leakage | at15 | 19 | 19.0 | 17.6 | 7.37 | 7.37 | [19, 15, 19, 18, 17] |
| Image 2: Win7 Data Leakage | at20 | 19 | 19.0 | 17.6 | 7.37 | 7.37 | [19, 15, 19, 18, 17] |
| Image 3: Win10 Lone Wolf | at15 | 34 | 32.4 | 31.0 | 4.32 | 4.12 | [31, 29, 33, 32, 30] |
| Image 3: Win10 Lone Wolf | at20 | 34 | 34.0 | 32.4 | 4.71 | 4.71 | [34, 32, 33, 33, 30] |

Verdict: **PASS**

## (ii) Gaussian noise, sd 3600 s, on timestamps

| disk | budget | targets | baseline mean caught | perturbed mean caught | relative drop % | drop (pp) | perturbed per seed |
|---|---|---|---|---|---|---|---|
| Image 1: XP Hacking (SCHARDT.001) | at15 | 7 | 7.0 | 6.0 | 14.29 | 14.29 | [6, 6, 6, 6, 6] |
| Image 1: XP Hacking (SCHARDT.001) | at20 | 7 | 7.0 | 6.0 | 14.29 | 14.29 | [6, 6, 6, 6, 6] |
| Image 2: Win7 Data Leakage | at15 | 19 | 19.0 | 18.4 | 3.16 | 3.16 | [19, 18, 19, 18, 18] |
| Image 2: Win7 Data Leakage | at20 | 19 | 19.0 | 19.0 | 0.0 | 0.0 | [19, 19, 19, 19, 19] |
| Image 3: Win10 Lone Wolf | at15 | 34 | 32.4 | 28.4 | 12.35 | 11.76 | [30, 23, 27, 30, 32] |
| Image 3: Win10 Lone Wolf | at20 | 34 | 34.0 | 30.6 | 10.0 | 10.0 | [31, 29, 29, 31, 33] |

Verdict: **FAIL**

## Overall (PROTOCOL A7)

- Drop 10% of non-target files: **PASS**
- Timestamp noise 1 h: **FAIL**
- Drop 10% of all files (separate): **PASS**
- A7 overall (variants i and ii): **FAIL**
