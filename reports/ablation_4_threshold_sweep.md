# Ablation Study 4: Threshold Rate Sensitivity & Workload Calibration

**Dataset**: NIST CFReDS Data Leakage PC (`cfreds_2015_data_leakage_pc.dd`)  
**Operating System**: Windows 7 x64 Enterprise  
**Scale**: 85,017 total indexed files  
**Ground-Truth Targets**: 19 on-disk verified evidentiary targets  
**Evaluation Methodology**: Multi-seed stochastic evaluation (5 runs per threshold rate, reporting Mean ± Std)

---

## 1. Experimental Results Table

| Threshold Rate | Review Budget ($K$ files) | Targets Detected (Hits / 19) | Recall (%) | Precision (%) | Forensic Yield per 1k Files |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **5.0%** | 4,250 files | **7.0 ± 0.00** | **36.8% ± 0.0%** | 0.165% | 1.65 targets / 1k |
| **7.0%** | 5,951 files | **7.0 ± 0.00** | **36.8% ± 0.0%** | 0.118% | 1.18 targets / 1k |
| **9.0%** | 7,651 files | **8.2 ± 0.40** | **43.2% ± 2.1%** | 0.107% | 1.07 targets / 1k |
| **11.0%** | 9,351 files | **10.4 ± 0.49** | **54.7% ± 2.6%** | 0.111% | 1.11 targets / 1k |
| **13.0%** | 11,052 files | **11.8 ± 0.40** | **62.1% ± 2.1%** | 0.107% | 1.07 targets / 1k |
| **15.0%** | 12,752 files | **12.0 ± 0.00** | **63.2% ± 0.0%** | 0.094% | 0.94 targets / 1k |

---

## 2. Key Forensic Takeaways

1. **Confirmation of the "Fluke" Hypothesis**:
   - The 100% detection jump from 5% to 5.5% observed on the legacy Windows XP image (`SCHARDT.001`, 11,773 files) was indeed an artifact of a small toy dataset where all 7 targets clustered in the top 600 files.
   - In a modern enterprise Windows 7 system with 85,017 files, detection scales progressively from 36.8% to 63.2%.

2. **The 5% to 7% Plateau**:
   - Bumping the threshold from 5% to 7% forces an examiner to inspect 1,701 additional files with zero new evidence discovered.

3. **The 11% Operational Knee (Sweet Spot)**:
   - At 11% (9,351 files), the model captures 10.4 targets (54.7% recall), including wiping installers, masqueraded exfiltration archives, and the resignation letter.
   - Beyond 11%, diminishing returns set in: expanding review by 3,401 more files (to 15%) only uncovers 1.6 additional targets.
