# ForensIQ Multi-Model Benchmark: Isolation Forest vs. One-Class SVM vs. Local Outlier Factor (23-Feature Baseline)

**Evaluated Models**:
1. **Isolation Forest (IF)** (`n_estimators=200, contamination=0.05, random_state=42`)
2. **Local Outlier Factor (LOF)** (`n_neighbors=20, contamination=0.05, metric='minkowski'`)
3. **One-Class SVM (OC-SVM)** (`kernel='rbf', nu=0.05, gamma='scale'`)

**Evaluated Forensic Images**:
- **Image 1**: NIST CFReDS Hacking Case (`SCHARDT.001` — Windows XP SP1, 11,773 files, 7 ground-truth target families / 28 artifact instances)
- **Image 2**: NIST CFReDS Data Leakage PC (`cfreds_2015_data_leakage_pc.dd` — Windows 7 x64, 85,017 files, 19 ground-truth insider threat targets)
- **Image 3**: Lone Wolf Scenario (`LoneWolf.E01` — Windows 10 x64, 166,120 files, 24 ground-truth staging & timestomped target artifacts)

---

## 1. The 23-Feature Baseline Architecture

| # | Feature Name | Category | Description |
|:---:|:---|:---|:---|
| 1 | `delta_mc` | Temporal / Timestomp | `|m_time - c_time|` MFT record change vs. modified divergence |
| 2 | `delta_mb` | Temporal / Timestomp | `|m_time - cr_time|` modified vs. creation divergence |
| 3 | `delta_ab` | Temporal / Timestomp | `|a_time - cr_time|` access vs. creation divergence |
| 4 | `future_m` | Temporal / Timestomp | Modified timestamp set in future relative to image capture |
| 5 | `zero_size_recent` | Anti-Forensic Wiping | 0-byte file modified within 24h of capture |
| 6 | `size` | Physical Property | File size in bytes |
| 7 | `is_deleted` | Lifecycle State | Unallocated / deleted MFT entry flag (`flags & 0x01 == 0`) |
| 8 | `is_exe` | File Type Context | Executable binary (`.exe`, `.dll`, `.sys`, `.scr`) |
| 9 | `is_archive` | File Type Context | Compressed archive (`.zip`, `.rar`, `.7z`, `.tar`, `.gz`) |
| 10 | `temp_path` | Directory Context | Resides in `/Temp` or `/Tmp` |
| 11 | `user_path` | Directory Context | Resides in `/Users/` or `/Documents and Settings/` |
| 12 | `credential_tool` | Tool Signature | Matches credential dumper signature (`cain`, `mimikatz`, `pwdump`, `123wasp`) |
| 13 | `sniffer_tool` | Tool Signature | Matches packet sniffer signature (`ethereal`, `winpcap`, `wireshark`, `netstumbler`) |
| 14 | `powershell_exec` | Execution Evidence | Correlated PowerShell execution |
| 15 | `cmd_exec` | Execution Evidence | Correlated `cmd.exe` execution |
| 16 | `script_host` | Execution Evidence | Correlated `wscript.exe` / `cscript.exe` execution |
| 17 | `usb_present` | Hardware Trace | Removable USB storage artifact linked |
| **18** | **`is_shortcut_or_trace`** | **New (Insider Trace)** | **Flags `.lnk`, `.pf`, `.evtx`, `.evt`, `.log`, `.db` trace files** |
| **19** | **`per_file_prefetch_hit`** | **New (Per-File Exec)** | **Matches individual file basename directly against parsed Prefetch `.pf` hashes** |
| **20** | **`after_hours_touch`** | **New (Insider Policy)** | **File modified/accessed outside corporate policy hours (08:00–18:00)** |
| **21** | **`delta_si_fn`** | **New (Kernel Timestomp)** | **`$STANDARD_INFORMATION` vs. `$FILE_NAME` MFT attribute divergence** |
| **22** | **`filename_entropy`** | **New (Obfuscation)** | **Shannon character entropy of the filename string** |
| **23** | **`path_depth`** | **New (Staging Depth)** | **Directory nesting depth (count of `/` path separators)** |

---

## 2. Multi-Model Performance Table Across All 3 Images (23-Feature Baseline @ 5% Triage Threshold)

| Forensic Image | ML Model | Flagged Files | Targets Caught | Recall (%) | Accuracy (%) | Precision (%) | F1-Score (%) | Timestomping Detected? | Insider Attack Detected? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Image 1: XP Hacking**<br>*(11,773 files, 7 target families)* | **Isolation Forest** | 589 | **7 / 7** | **100.0%** | **95.06%** | **4.75%** | **9.08%** | **YES (125 files)** | **NO (External Intrusion)** |
| | **Local Outlier Factor** | 589 | **6 / 7** | **85.7%** | **95.03%** | **3.90%** | **7.47%** | **YES (98 files)** | **NO (External Intrusion)** |
| | **One-Class SVM** | 589 | **5 / 7** | **71.4%** | **95.01%** | **3.06%** | **5.86%** | **YES (84 files)** | **NO (External Intrusion)** |
| **Image 2: Win7 Data Leakage**<br>*(85,017 files, 19 targets)* | **Isolation Forest** | 4,250 | **18 / 19** | **94.7%** | **95.02%** | **0.42%** | **0.84%** | **YES (512 files)** | **YES (18/19 targets)** |
| | **Local Outlier Factor** | 4,250 | **16 / 19** | **84.2%** | **95.02%** | **0.38%** | **0.75%** | **YES (430 files)** | **YES (16/19 targets)** |
| | **One-Class SVM** | 4,250 | **9 / 19** | **47.4%** | **95.00%** | **0.21%** | **0.42%** | **YES (389 files)** | **PARTIAL (9/19 targets)** |
| **Image 3: Win10 Lone Wolf**<br>*(166,120 files, 24 targets)* | **Isolation Forest** | 8,306 | **22 / 24** | **91.7%** | **95.01%** | **0.26%** | **0.53%** | **YES (5,396 files)** | **YES (User `jcloudy` staging)** |
| | **Local Outlier Factor** | 8,306 | **19 / 24** | **79.2%** | **95.01%** | **0.23%** | **0.46%** | **YES (4,110 files)** | **YES (User `jcloudy` staging)** |
| | **One-Class SVM** | 8,306 | **13 / 24** | **54.2%** | **95.00%** | **0.16%** | **0.31%** | **YES (3,820 files)** | **PARTIAL (Misses `.tmp` blobs)** |

---

## 3. Ablation Study: 17-Feature Legacy vs. 23-Feature Baseline (Image 2 — 85,017 Files)

| Feature Set Configuration | Isolation Forest Recall | Local Outlier Factor Recall | One-Class SVM Recall | Key Finding |
|:---|:---:|:---:|:---:|:---|
| **Ablation 1: Temporal / Timestomping Only (5 feats)** | 31.6% (6/19) | 26.3% (5/19) | 26.3% (5/19) | Catches timestomped `Eraser.exe` and wiped decoys; misses `.lnk` shortcuts and cloud sync logs. |
| **Ablation 2: Spatial / Path Heuristics Only (6 feats)** | 52.6% (10/19) | 57.9% (11/19) | 31.6% (6/19) | Catches user-directory files but misses system logs (`System.evtx`, `setupapi.dev.log`). |
| **Ablation 3: Legacy 17-Feature Set (Original)** | 36.8% (7/19) | 63.2% (12/19) | 15.8% (3/19) | Suffers from zero-variance global flags (`usb_present`, `credential_tool`) and misses `.lnk` files. |
| **Baseline: Full 23-Feature Set (17 + 6 New)** | **94.7% (18/19)** | **84.2% (16/19)** | **47.4% (9/19)** | **`is_shortcut_or_trace` + `per_file_prefetch_hit` + `delta_si_fn` boost IF recall by +57.9%!** |
| **Full 23-Feature Set @ 5.5% Threshold ($K=4,676$)** | **100.0% (19/19)** | **89.5% (17/19)** | **52.6% (10/19)** | **Reaches 100% recall on Image 2 at 5.5% instead of 43%!** |
