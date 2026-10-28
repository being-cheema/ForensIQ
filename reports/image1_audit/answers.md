# Image 1 (SCHARDT / Hacking Case) audit of the fresh run

Source: `runs/img1/` (11,773 MFT file records, 11,619 unique paths). Baseline Isolation Forest reproduced from `X_raw.npy`: exact match with the stored flagged set and scores.

Model: IsolationForest(n_estimators=200, max_samples='auto', contamination=0.05, random_state=42) on 17 standardised features. Constant columns on this image (zero information): future_m, is_deleted, credential_tool, sniffer_tool, powershell_exec, cmd_exec, script_host, usb_present. 9 non-constant features: delta_mc, delta_mb, delta_ab, zero_size_recent, size, is_exe, is_archive, temp_path, user_path.

## A1. Are the known malicious artefacts flagged?

Flag rule: score < 0 (5% budget, K = 589 rows).

| Key file | Rank (of 11773) | Score | Flagged |
|---|---|---|---|
| Cain.exe | 136 | -0.1096 | yes |
| ethereal.exe | 148 | -0.0983 | yes |
| NetStumbler.exe | 322 | -0.0471 | yes |
| defrag.exe | 2260 | +0.1088 | no |
| UNWISE.EXE | 1823 | +0.0902 | no |
| 123wasp.exe | 2270 | +0.1091 | no |
| uninst-anonymizer.exe | 1289 | +0.0653 | no |
| biglist_990218.zip | 1 | -0.1673 | yes |
| 250MB_WORDLIST.ZIP | 4 | -0.1547 | yes |
| NMEM.EXE | 81 | -0.1192 | yes |
| NGETTIME.EXE | 80 | -0.1192 | yes |

Family and file level (GT = 302 unique files in 8 families):

| Family | GT files | Flagged files | Family caught |
|---|---|---|---|
| Cain & Abel | 37 | 4 | yes |
| Ethereal/WinPcap | 174 | 43 | yes |
| NetStumbler | 13 | 1 | yes |
| 123WASP | 7 | 0 | no |
| Anonymizer | 66 | 0 | no |
| defrag.exe | 1 | 0 | no |
| Timestomped Novell | 2 | 2 | yes |
| Wordlists | 2 | 2 | yes |

Family recall 5/8 = 62.5%; file recall 52/302 = 17.2%. Missed families: 123WASP, Anonymizer, defrag.exe.

## A2. Dominant SHAP feature versus the forensically expected signal

xai_shap.py: `shap.TreeExplainer(model, data=X_scaled, feature_perturbation='interventional')` on standardised rows; `dominant_feature` = argmax of |SHAP| over the 17 features. Because credential_tool, sniffer_tool, cmd_exec and usb_present are constant (set from global prefetch/USB presence), SHAP can never point at tool identity; the only meaningful per-file signals are executable type, MACB deltas, size, archive type. 'Expected' therefore means: executables/tools -> is_exe, a MACB delta or size; timestomped Novell -> a MACB delta; wordlists -> is_archive, size or a MACB delta.

| Family | Flagged | Dominant = expected | Dominant feature counts |
|---|---|---|---|
| Cain & Abel | 4 | 4/4 | {'size': 2, 'delta_mc': 1, 'delta_mb': 1} |
| Ethereal/WinPcap | 43 | 43/43 | {'delta_mc': 35, 'size': 6, 'delta_ab': 2} |
| NetStumbler | 1 | 1/1 | {'delta_ab': 1} |
| 123WASP | 0 | n/a | - |
| Anonymizer | 0 | n/a | - |
| defrag.exe | 0 | n/a | - |
| Timestomped Novell | 2 | 2/2 | {'delta_mb': 2} |
| Wordlists | 2 | 2/2 | {'size': 2} |

Per key flagged file:

| File | Dominant | Top-3 (SHAP) | Expected? |
|---|---|---|---|
| Cain.exe | size | size(-3.61), delta_mc(-1.22), delta_mb(-1.08) | yes |
| ethereal.exe | size | size(-3.67), delta_mc(-1.46), delta_ab(-1.26) | yes |
| NetStumbler.exe | delta_ab | delta_ab(-1.85), delta_mc(-1.78), size(-1.62) | yes |
| biglist_990218.zip | size | size(-3.89), is_archive(-2.16), delta_mb(-1.53) | yes |
| 250MB_WORDLIST.ZIP | size | size(-4.52), is_archive(-2.29), delta_mb(-1.11) | yes |
| NMEM.EXE | delta_mb | delta_mb(-3.61), delta_mc(-3.58), is_exe(-0.72) | yes |
| NGETTIME.EXE | delta_mb | delta_mb(-3.61), delta_mc(-3.58), is_exe(-0.72) | yes |

Overall 52/52 flagged GT files have a dominant feature in the expected set. Mismatches: none.

## A3. Counts, SHAP magnitude, custody, determinism

* Flagged: 589 rows = 589 unique paths (no flagged path is duplicated). SHAP table / shap_values.npy have 593 rows: xai_shap.py picks every row whose *path* is flagged, adding 4 unflagged twin rows (NDELFILE.EXE, NOPNFILE.EXE, TXTVIEW.OCX, msoeres.dll). Image-wide: 11773 rows, 11619 unique paths, 154 paths appear twice.
* Score range [-0.1673, 0.2099]; largest flagged -0.000201, smallest unflagged 0.000134.
* Mean |SHAP| per feature (all 593 SHAP rows as the pipeline prints it; 589 flagged-only in the last column):

| Feature | mean abs SHAP (593) | mean abs SHAP (589) |
|---|---|---|
| delta_mc | 1.8437 | 1.8474 |
| size | 1.5958 | 1.6046 |
| delta_mb | 1.3752 | 1.3840 |
| delta_ab | 1.2229 | 1.2300 |
| user_path | 0.4673 | 0.4697 |
| is_exe | 0.4250 | 0.4174 |
| is_archive | 0.2697 | 0.2711 |
| temp_path | 0.0024 | 0.0024 |
| is_deleted | 0.0000 | 0.0000 |
| zero_size_recent | 0.0000 | 0.0000 |
| future_m | 0.0000 | 0.0000 |
| credential_tool | 0.0000 | 0.0000 |
| sniffer_tool | 0.0000 | 0.0000 |
| powershell_exec | 0.0000 | 0.0000 |
| cmd_exec | 0.0000 | 0.0000 |
| script_host | 0.0000 | 0.0000 |
| usb_present | 0.0000 | 0.0000 |

Dominant-feature counts over the 593 SHAP rows: {'size': 184, 'delta_mb': 174, 'delta_ab': 86, 'user_path': 54, 'delta_mc': 54, 'is_archive': 37, 'is_exe': 4}.

* Chain of custody: 96/96 artefacts PASS in coc_verification.csv (0 non-PASS); independent re-hash mismatches: 0. Verdict: PASS.
* random_state audit (AST scan of every pipeline-stage script):

| Script | Line | Call | random_state |
|---|---|---|---|
| anomaly_detection.py | 48 | IsolationForest | 42 |
| burst_detection.py | 92 | IsolationForest | 42 |
| evaluate_baselines.py | 309 | IsolationForest | 42 |
| evaluate_baselines.py | 356 | IsolationForest | 42 |
| evaluate_baselines.py | 368 | IsolationForest | 42 |
| evaluate_baselines.py | 247 | np.random.RandomState | (positional) |
| evaluate_baselines.py | 321 | IsolationForest | seed |

Unseeded calls: 0. The model fits that drive the pipeline output (anomaly_detection.py, burst_detection.py, evaluate_baselines.py) all pass an explicit seed; SHAP's TreeExplainer with an interventional background is deterministic (no sampling). Seed is fixed at 42 for both v1 and v2, but it is a literal in each file, not read from config.py.

## A4. Recall at the 5% budget

* Family level: 5/8 = 62.5%.
* File level: 52/302 = 17.2% (tool families only: 48/298).
* For comparison, random selection of 589/11773 rows would catch about 5.0% of GT files.

## B1. Feature-group ablation (retrained, StandardScaler + same IF params)

Overlap = rows also flagged by the full-17 seed-42 baseline (out of 589). 5-seed values use seeds [42, 1, 2, 3, 4] (mean +/- std, overlap always against the seed-42 baseline).

| Variant | #feat | K | Overlap/589 (s42) | Overlap 5-seed | Fam. recall s42 | Fam. recall 5-seed | File recall s42 | File recall 5-seed | Tool files s42 |
|---|---|---|---|---|---|---|---|---|---|
| full_17 | 17 | 589 | 589 | 549.0 +/- 20.5 | 5/8 | 0.625 +/- 0.000 | 52/302 (0.172) | 0.144 +/- 0.042 | 48 |
| nonconstant_only (9) | 9 | 589 | 558 | 545.2 +/- 9.9 | 5/8 | 0.625 +/- 0.000 | 65/302 (0.215) | 0.154 +/- 0.073 | 61 |
| assumed_active6 (3 MACB+size+is_exe+is_archive) | 6 | 589 | 535 | 527.0 +/- 10.0 | 5/8 | 0.625 +/- 0.000 | 58/302 (0.192) | 0.217 +/- 0.056 | 54 |
| drop_is_exe | 16 | 589 | 514 | 513.8 +/- 2.1 | 5/8 | 0.625 +/- 0.000 | 15/302 (0.050) | 0.050 +/- 0.002 | 11 |
| drop_size | 16 | 586 | 477 | 474.8 +/- 3.1 | 5/8 | 0.625 +/- 0.000 | 84/302 (0.278) | 0.291 +/- 0.022 | 80 |
| drop_is_archive | 16 | 589 | 527 | 520.4 +/- 6.8 | 5/8 | 0.625 +/- 0.000 | 25/302 (0.083) | 0.103 +/- 0.035 | 21 |
| drop_all_MACB_deltas | 14 | 589 | 238 | 242.6 +/- 5.6 | 3/8 | 0.375 +/- 0.000 | 10/302 (0.033) | 0.030 +/- 0.001 | 8 |
| only_MACB_deltas | 3 | 564 | 350 | 355.8 +/- 9.6 | 5/8 | 0.625 +/- 0.000 | 72/302 (0.238) | 0.336 +/- 0.129 | 70 |

Families missed per variant (seed 42): full_17: 123WASP; Anonymizer; defrag.exe; nonconstant_only (9): 123WASP; Anonymizer; defrag.exe; assumed_active6 (3 MACB+size+is_exe+is_archive): 123WASP; Anonymizer; defrag.exe; drop_is_exe: 123WASP; Anonymizer; defrag.exe; drop_size: 123WASP; Anonymizer; defrag.exe; drop_is_archive: 123WASP; Anonymizer; defrag.exe; drop_all_MACB_deltas: NetStumbler; 123WASP; Anonymizer; defrag.exe; Timestomped Novell; only_MACB_deltas: 123WASP; defrag.exe; Wordlists.

## B2. Contamination sweep (full 17 features, seed 42)

| % | K | Families | GT files | Newly entering families | Still missing |
|---|---|---|---|---|---|
| 1 | 113 | 3/8 | 6/302 | Ethereal/WinPcap; Timestomped Novell; Wordlists | Cain & Abel; NetStumbler; 123WASP; Anonymizer; defrag.exe |
| 2 | 236 | 4/8 | 8/302 | Cain & Abel | NetStumbler; 123WASP; Anonymizer; defrag.exe |
| 2.5 | 295 | 4/8 | 8/302 | - | NetStumbler; 123WASP; Anonymizer; defrag.exe |
| 3 | 354 | 5/8 | 13/302 | NetStumbler | 123WASP; Anonymizer; defrag.exe |
| 4 | 471 | 5/8 | 20/302 | - | 123WASP; Anonymizer; defrag.exe |
| 5 | 589 | 5/8 | 52/302 | - | 123WASP; Anonymizer; defrag.exe |
| 5.12 | 603 | 5/8 | 57/302 | - | 123WASP; Anonymizer; defrag.exe |
| 5.5 | 648 | 5/8 | 68/302 | - | 123WASP; Anonymizer; defrag.exe |
| 7.5 | 883 | 5/8 | 91/302 | - | 123WASP; Anonymizer; defrag.exe |
| 10 | 1177 | 6/8 | 106/302 | Anonymizer | 123WASP; defrag.exe |

Exact ranks (rank is independent of contamination; the flag threshold moves):

| File | Rank | Score |
|---|---|---|
| 123wasp.exe | 2270 | +0.1091 |
| uninst-anonymizer.exe | 1289 | +0.0653 |
| defrag.exe | 2260 | +0.1088 |
| UNWISE.EXE | 1823 | +0.0902 |
| Cain.exe | 136 | -0.1096 |
| ethereal.exe | 148 | -0.0983 |
| NetStumbler.exe | 322 | -0.0471 |
| biglist_990218.zip | 1 | -0.1673 |

Smallest contamination (0.1% grid) at which all 8 families are caught: 19.2% (K=2261).

## B3. Component ablation: v1 (17 static) vs v2 (burst model)

v2 features (burst_detection.py): delta_mc, delta_mb, delta_ab, future_m, zero_size_recent, size, log_burst_count, log_burst_60s. v2 omits is_exe: yes. v2 refit from MFT JSON reproduces stored flags: exact. Top 1-s modification bursts: [('2001-08-23T18:00:00Z', 7033), ('2004-08-19T22:34:25Z', 210), ('1999-04-23T22:22:00Z', 131)].

| Family | GT files | v1 | v2 | union | both | v1 only | v2 only |
|---|---|---|---|---|---|---|---|
| Cain & Abel | 37 | 4 | 3 | 4 | 3 | 1 | 0 |
| Ethereal/WinPcap | 174 | 43 | 25 | 61 | 7 | 36 | 18 |
| NetStumbler | 13 | 1 | 11 | 11 | 1 | 0 | 10 |
| 123WASP | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| Anonymizer | 66 | 0 | 65 | 65 | 0 | 0 | 65 |
| defrag.exe | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Timestomped Novell | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| Wordlists | 2 | 2 | 2 | 2 | 2 | 0 | 0 |
| ALL GT FILES | 302 | 52 | 108 | 145 | 15 | 37 | 93 |
| FLAGGED SET (unique paths) |  | 589 | 589 | 743 | 435 | 154 | 154 |

Flagged-set Jaccard: unique paths 0.5855, rows 0.5855. Family recall v1 5/8, v2 6/8, union 6/8.

## C. Claim check (TRUE / FALSE / UNVERIFIABLE)

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| 1 | 589 files flagged by v1 and by v2 | **TRUE** | v1 flagged rows=589, v2 flagged rows=589; v1 unique flagged paths=589, v2=589. |
| 2 | 593 rows downstream because 4 duplicated paths (NDELFILE.EXE, NOPNFILE.EXE, TXTVIEW.OCX, msoeres.dll) | **TRUE** | SHAP table has 593 rows for 589 paths: xai_shap.py selects every row whose path is in the flagged-path set, so 4 unflagged twin rows are added; their basenames are ['NDELFILE.EXE', 'NOPNFILE.EXE', 'TXTVIEW.OCX', 'msoeres.dll']. Note the 589 flagged rows themselves are all unique paths, so 'flagged' stays 589; the 593 only affects the SHAP/ explanation tables. Image-wide the MFT has 154 paths occurring twice (11773 rows vs 11619 unique paths). |
| 3 | Score range [-0.1649, +0.2412] | **FALSE** | Fresh run range is [-0.1673, 0.2099] (stored flagged_anomalies.csv min -0.1673). |
| 4 | Decision cutoff ~ -0.0000 | **TRUE** | Largest flagged score -0.000201, smallest unflagged 0.000134; sklearn offset_ for contamination 0.05 puts the boundary at 0 by construction of decision_function. |
| 5 | Cain.exe rank #4, score -0.1562 | **FALSE** | Fresh run: rank #136, score -0.1096, flagged=True. |
| 6 | ethereal.exe rank #60, score -0.1352 | **FALSE** | Fresh run: rank #148, score -0.0983, flagged=True. |
| 7 | NetStumbler.exe rank #191, score -0.0999 | **FALSE** | Fresh run: rank #322, score -0.0471, flagged=True. |
| 8 | defrag.exe rank #580, score -0.0008 | **FALSE** | Fresh run: rank #2260, score +0.1088, flagged=False. |
| 9 | UNWISE.EXE rank #525, score -0.0134 | **FALSE** | Fresh run: rank #1823, score +0.0902, flagged=False. |
| 10 | 123wasp.exe rank #603, score +0.0032 | **FALSE** | Fresh run: rank #2270, score +0.1091, flagged=False. |
| 11 | uninst-anonymizer.exe rank #647, score +0.0133 | **FALSE** | Fresh run: rank #1289, score +0.0653, flagged=False. |
| 12 | biglist_990218.zip rank #1, score -0.1649 | **FALSE** | Fresh run: rank #1, score -0.1673, flagged=True. |
| 13 | Bumping 5% to 5.5% (648 files) gives 100% (7/7) category recall | **FALSE** | At 5.5%: K=648 rows; families caught 5/8 (missing: 123WASP, Anonymizer, defrag.exe); file recall 68/302. Smallest contamination on a 0.1% grid reaching all 8 families: 19.2% (K=2261). |
| 14 | Active-6 retains 589/589 | **FALSE** | 'Active-6' is not defined anywhere in the repo. Retrained: all 9 non-constant features -> 558/589 overlap; assumed 6 (3 MACB deltas+size+is_exe+is_archive) -> 535/589. Removing the 8 constant columns is not a no-op because IsolationForest draws split features at random, so the RNG path changes. |
| 15 | Ablation: drop is_exe 374/589 | **FALSE** | Retrained (seed 42): overlap 514/589; 5-seed mean+/-std 513.8 +/- 2.1. |
| 16 | Ablation: drop size 323/589 | **FALSE** | Retrained (seed 42): overlap 477/589; 5-seed mean+/-std 474.8 +/- 3.1. |
| 17 | Ablation: drop all MACB deltas 107/589 | **FALSE** | Retrained (seed 42): overlap 238/589; 5-seed mean+/-std 242.6 +/- 5.6. |
| 18 | Ablation: MACB-only 198/589 with 0 tool files | **FALSE** | Retrained (seed 42): overlap 350/589; tool-family files caught 70 (all-GT files 72); 5-seed overlap 355.8 +/- 9.6. |
| 19 | v2 catches 65/70 Anonymizer files | **TRUE** | Substring 'anonymizer' anywhere: 70 rows on disk, v1 flagged 0, v2 flagged 65. Under the /Program Files/Anonymizer/ family definition: 66 files, v1 0, v2 65. |
| 20 | Ethereal v1->v2: 16 -> 25 | **FALSE** | Ethereal/WinPcap rows flagged: v1 44, v2 25 (regex); family definition 43 -> 25 of 174. |
| 21 | NetStumbler v1->v2: 1 -> 11 | **TRUE** | NetStumbler rows flagged (regex 'stumbler'): v1 1, v2 11; family definition 1 -> 11 of 13. |
| 22 | Timestomped files v1->v2: 219 -> 300 | **FALSE** | 'Timestomped' as defined in mitre_mapper.py (flagged and delta_mb < 60 s): v1 226, v2 301. Claimed 219/300 are close but not equal; the claim's own definition is not in the repo, so under any other definition it is UNVERIFIABLE. |
| 23 | Jaccard(v1, v2) = 0.5756 | **FALSE** | Jaccard on unique paths 0.5855; on rows 0.5855; /v1 & v2/ rows=435, /union/=743. |
| 24 | v2 omits is_exe | **TRUE** | burst_detection.py feat_v2 = ['delta_mc', 'delta_mb', 'delta_ab', 'future_m', 'zero_size_recent', 'size', 'log_burst_count', 'log_burst_60s']; (also omits is_archive, user_path, temp_path and every prefetch/USB flag). |
| 25 | 210-file burst at 2004-08-19T22:34:25Z | **TRUE** | Top 1-second m_time buckets (file records): [('2001-08-23T18:00:00Z', 7033), ('2004-08-19T22:34:25Z', 210), ('1999-04-23T22:22:00Z', 131), ('2004-08-19T22:35:22Z', 45), ('2004-08-19T22:34:59Z', 44)]. |
| 26 | 7,033-file burst at 2001-08-23T18:00:00Z | **TRUE** | Top 1-second m_time buckets: [('2001-08-23T18:00:00Z', 7033), ('2004-08-19T22:34:25Z', 210), ('1999-04-23T22:22:00Z', 131)]. Top 60-second buckets: [('2001-08-23T18:00Z', 7033), ('2004-08-19T22:35Z', 546), ('2004-08-19T22:34Z', 371)]. |
| 27 | Chain of custody 102/102 PASS | **FALSE** | chain_of_custody.json lists 96 artefacts; coc_verification.csv: 96 PASS, 0 not-PASS; independent SHA-256 re-hash mismatches: 0. So the integrity result is a full pass, but on 96 artefacts, not 102. |
| 28 | 182 event log records parsed | **FALSE** | parsed_events.json holds 0 events (pipeline.log: 'Parsed 0 EVT events'); 3 .Evt files extracted (AppEvent, SecEvent, SysEvent) but none parsed. log_gap_features.csv is empty. |
| 29 | 81 prefetch files | **TRUE** | 81 .pf files in artifacts/prefetch (prefetch_list.json entries: 81). |
| 30 | MITRE T1070.006 = 215 timestomped files | **FALSE** | mitre_mapping.json T1070.006 count = 226. |
| 31 | MITRE T1070.001 = 78 work-hour log gaps | **FALSE** | T1070.001 present in mitre_mapping.json: False; techniques detected: ['T1003.002', 'T1040', 'T1052.001', 'T1070.006', 'T1486']. With 0 parsed events there are no hourly bins, so no gap can be computed. |
| 32 | forensiq_report.py looks for remediate_credential_dumping.ps1 but remediation.py writes remediate_credentials.ps1 | **FALSE** | Filenames referenced by forensiq_report.py: ['remediate_credentials.ps1', 'remediate_log_clearing.ps1', 'remediate_malware.ps1', 'remediate_network.ps1', 'remediate_ransomware.ps1', 'remediate_timestamp.ps1', 'remediate_usb.ps1']; written by remediation.py: ['remediate_credentials.ps1', 'remediate_log_clearing.ps1', 'remediate_malware.ps1', 'remediate_network.ps1', 'remediate_ransomware.ps1', 'remediate_timestamp.ps1', 'remediate_usb.ps1']; 'remediate_credential_dumping.ps1' appears in neither. Names referenced but never written: none ('remediate_log_clearing.ps1' is written only when a log_clearing pattern is detected, so it is absent on this run by design). On disk: ['remediate_credentials.ps1', 'remediate_malware.ps1', 'remediate_network.ps1', 'remediate_ransomware.ps1', 'remediate_timestamp.ps1', 'remediate_usb.ps1']. |

Full text of every claim, verdict and evidence is also in `claims_check.csv`.

Notes on method: the pipeline's own `ground_truth_metrics.json` and the baseline-benchmark stage report different on-disk counts (e.g. Anonymizer 70, Ethereal 188) because they use unrestricted case-insensitive regexes ('anonymizer', 'ethereal|winpcap|wpcap'); this audit uses the path-anchored family definitions given in the task. Regex-based counts are quoted where a claim used them.
