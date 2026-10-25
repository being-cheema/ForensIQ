# ForensIQ: AI-Powered Autonomous Digital Forensics & Incident Response

[![Python Version](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Machine Learning](https://img.shields.io/badge/ML-Isolation%20Forest%20%7C%20k--NN-orange)](https://scikit-learn.org/)
[![Explainable AI](https://img.shields.io/badge/XAI-TreeSHAP%20(Game%20Theory)-green)](https://github.com/shap/shap)
[![Taxonomy](https://img.shields.io/badge/Taxonomy-MITRE%20ATT%26CK%20v14-red)](https://attack.mitre.org/)
[![Forensics Core](https://img.shields.io/badge/Engine-pytsk3%20%7C%20The%20Sleuth%20Kit-purple)](https://www.sleuthkit.org/)
[![Integrity](https://img.shields.io/badge/Integrity-Dual%20SHA--256%20%2F%20MD5-teal)](#-evidentiary-integrity-manifest)

**ForensIQ** is an autonomous, publication-grade **Digital Forensics & Incident Response (DFIR)** platform. It parses raw disk images non-invasively (`$MFT`, Event Logs, Prefetch, Registry), engineers a 17-dimensional forensic feature space, flags suspicious insider threats using unsupervised ML (**Isolation Forest & k-NN**), explains anomalies via **TreeSHAP**, maps findings to **MITRE ATT&CK®**, and benchmarks performance against standard forensic baselines.

---

## ⚡ Quick Start

### 1. Installation
```bash
git clone https://github.com/juveenasnowlyn-jpg/ForensIQ.git
cd ForensIQ
pip install -r requirements.txt
```

### 2. Execution Commands
```bash
# Run the complete 12-stage forensic pipeline
py -3.12 run_pipeline.py

# Skip disk extraction (use existing extracted artifacts)
py -3.12 run_pipeline.py --skip-extraction

# Start at feature engineering & ML training (Stages 3–12)
py -3.12 run_pipeline.py --start-at 3

# Run the Milestone 5 Scientific Baseline Benchmark
py -3.12 evaluate_baselines.py

# Convert an E01 image container to raw DD with hash sidecars
py -3.12 convert_e01.py --image path/to/image.E01
```

---

## 🔬 The 12-Stage Pipeline

```
Raw Disk Image (.raw / .dd / .E01)
 ├── 1. Data Extraction (MFT, EVT/EVTX, Registry, Prefetch)
 ├── 2. Cryptographic Manifest (Streaming Dual SHA-256 / MD5)
 ├── 3. Feature Engineering (17-feature space with zero-timestamp masking)
 ├── 4. Anomaly Detection (Unsupervised Isolation Forest, top 5% queue)
 ├── 5. Temporal Burst Detection (Rapid staging & wipe burst windows)
 ├── 6. Confidence Calibration (CRITICAL / HIGH / MEDIUM / LOW tiers)
 ├── 7. MITRE ATT&CK® Mapping (T1070.006, T1052.001, T1036.005, etc.)
 ├── 8. Explainable AI (TreeSHAP attributions & waterfall charts)
 ├── 9. Interactive Timeline (Unified MFT + EVTX security timeline)
 ├── 10. Remediation Scripts (Automated containment PowerShell playbooks)
 ├── 11. Master Forensic Report (Executive HTML dashboard & case state)
 └── 12. Scientific Baseline Benchmark (Matched-budget evaluation vs 11 methods)
```

---

## 📊 17-Feature Forensic Space

| Feature | Category | Source | Formula / Signal | Forensic Rationale |
|---|---|---|---|---|
| `delta_mc` | MACB | NTFS `$MFT` | $\|m\_time - c\_time\|$ (if $>0$, else $0.0$) | Detects timestomping metadata manipulation |
| `delta_mb` | MACB | NTFS `$MFT` | $\|m\_time - cr\_time\|$ (if $>0$, else $0.0$) | Detects backdating prior to creation on volume |
| `delta_ab` | MACB | NTFS `$MFT` | $\|a\_time - cr\_time\|$ (if $>0$, else $0.0$) | Flags access anomalies relative to birth |
| `future_m` | MACB | NTFS `$MFT` | $m\_time > now\_ts$ | Flags timestamps set into future |
| `zero_size_recent` | Size | NTFS `$MFT` | $size == 0 \land recent$ | Detects wiper touch artifacts & zero-byte drops |
| `size` | Size | NTFS `$MFT` | Record file size in bytes | Catches massive exfil dumps or micro-stagers |
| `is_deleted` | File System | NTFS `$MFT` | `bool(flags & TSK_FS_META_FLAG_UNALLOC)` | Identifies deleted records in free space |
| `is_exe` / `is_archive` | File Type | Path | `.exe`, `.dll`, `.sys` / `.zip`, `.rar`, `.7z` | Flags executables and compressed archives |
| `temp_path` / `user_path` | Location | Path | In `/temp/` or `/users/` | Distinguishes user activity from OS background |
| `credential_tool` | Prefetch | `.pf` | `pwdump`, `cain`, `mimikatz`, `123wasp` | Direct indicator of credential dumping |
| `sniffer_tool` | Prefetch | `.pf` | `wireshark`, `ethereal`, `tcpdump`, `winpcap` | Network sniffing / reconnaissance tools |
| `powershell_exec` / `cmd_exec` | Prefetch | `.pf` | `powershell.exe` / `cmd.exe` | Living-off-the-land script interpreter runs |
| `script_host` | Prefetch | `.pf` | `wscript.exe`, `cscript.exe` | Windows Scripting Host background execution |
| `usb_present` | Hardware | Registry | `SYSTEM\CurrentControlSet\Enum\USBSTOR` | Reconstructs external storage connection |

---

## 📈 Scientific Benchmark: Multi-Method Evaluation

Evaluated across **85,017 file records** on the NIST CFReDS Data Leakage PC against all **19 ground-truth target artifacts** across 7 matched review budgets ($K$):

| Method | K=25 | K=50 | K=100 | K=250 | K=500 | K=1000 | K=4250 (5% Triage) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Random Baseline** (10 Seeds) | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.1 \pm 0.3$ | $1.3 \pm 1.2$ |
| **Rule: .exe under /Program Files** | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $1/19$ | $1/19$ |
| **Rule: Suspicious Paths (User/Temp)** | $0/19$ | $0/19$ | $1/19$ | **$12/19$** | **$12/19$** | **$12/19$** | **$13/19$** |
| **Univariate: File Size** | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $1/19$ | $6/19$ |
| **Isolation Forest (17 Feats, Seed 42)** | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $0/19$ | **$7/19$** |
| **Isolation Forest Multi-Seed (0–9)** | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | $0.0 \pm 0.0$ | **$6.6 \pm 1.6$** |
| **k-NN Distance Outlier ($k=5$)** | $0/19$ | $0/19$ | $0/19$ | $0/19$ | $3/19$ | $4/19$ | **$12/19$** |

### Key Benchmark Insights
1. **Domain Heuristics Win at Small Budgets ($K \le 250$)**: Path filters (`\Users\` and `\Temp\`) capture 12/19 targets quickly because insider attacks congregate in user folders.
2. **ML Uncovers Multi-Modal Non-Executable Targets ($K = 4,250$)**: Narrow rules (`.exe`) miss 16 of the 19 targets because modern threats involve shortcuts (`.lnk`), databases, and archives. At 5% triage budget ($K=4,250$), **Isolation Forest uncovers 7 targets** and **k-NN uncovers 12 targets**.

---

## 🛡️ Explainable AI & ATT&CK Evidence Cards

* **TreeSHAP Attributions**: Computes game-theoretic Shapley attributions ($\phi_i$) for all flagged anomalies, generating per-file waterfall PNG charts in `reports/shap/` and global feature beeswarm plots (`reports/shap/shap_summary_beeswarm.png`).
* **ATT&CK Evidence Cards**: Maps findings to MITRE ATT&CK techniques with scientific rigor, identifying hypotheses and required corroboration:
  - `T1070.006 Timestomping`: Divergence between `$SI` and `$FN` timestamps.
  - `T1070.001 Log Clearing`: Hourly event log gap verified against Event ID 1102/104.
  - `T1052.001 USB Exfiltration`: Registry `USBSTOR` connection corroborated with file copy activity.
  - `T1003.002 SAM Dumping`: Prefetch execution of `pwdump` or `cain` linked to process logs.
  - `T1036.005 Masquerading`: Header magic byte mismatch against file extension.

---

## 🔒 Evidentiary Integrity Manifest

ForensIQ maintains forensic integrity through streaming dual cryptographic hashing:
* **Dual Hashes (SHA-256 & MD5)**: Automatically computed for all extracted artifacts at ingestion.
* **Audit Manifest**: Serialized into `reports/chain_of_custody.json` and cross-verified during report generation (`reports/coc_verification.csv`).

---

## 📚 Technical Handbooks

Complete documentation and step-by-step guides are available in the repository root:
* [**ForensIQ Complete Technical Handbook (PDF)**](ForensIQ_Complete_Technical_Handbook.pdf): 12-stage architecture, 17-feature mathematical derivations, TreeSHAP theory, and baseline benchmark findings.
* [**ForensIQ Researcher Action Guide (PDF)**](ForensIQ_Researcher_Action_Guide.pdf): Step-by-step audit protocol, cross-image partition offsets, and manual verification checklists.

---

## 📁 Repository Structure

```
ForensIQ/
├── artifacts/                  # Raw extracted forensic artifacts (EVT, EVTX, MFT, Prefetch, Registry)
├── features/                   # Engineered matrices, scaler.pkl, and flagged queue CSVs
├── models/                     # Serialized models (iforest.pkl, iforest_bundle.pkl, scaler.pkl)
├── reports/                    # HTML report, SHAP charts, baseline benchmarks, and timeline
│   ├── forensiq_report.html    # Interactive master forensic dashboard
│   ├── baseline_budget_comparison.png # Milestone 5 benchmark comparison plot
│   └── shap/                   # SHAP beeswarm and per-file waterfall charts
├── convert_e01.py              # E01 to raw DD stream converter with hash verification
├── evaluate_baselines.py       # Milestone 5 Scientific Baseline Benchmark engine
├── run_pipeline.py             # 12-stage automated pipeline orchestrator
├── ForensIQ_Complete_Technical_Handbook.pdf # Architecture & mathematical derivations
└── ForensIQ_Researcher_Action_Guide.pdf     # Audit protocol & examiner guide
```
