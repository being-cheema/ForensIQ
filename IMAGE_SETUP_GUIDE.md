# ForensIQ: Universal Forensic Image Setup & Execution Guide

ForensIQ supports non-invasive ingestion and analysis of all major digital forensic disk image container formats:
* **Expert Witness Compression Format (`.E01` / `.Exx`)**: Native direct streaming across multi-segment files with **zero raw disk conversion** and **zero extra disk space usage**.
* **Raw / Consolidated Bitstream Images (`.raw`, `.dd`, `.001`)**: Direct partition-table inspection and sector mapping.

---

## 🚀 Quick Execution by Image Type

### 1. Lone Wolf (Windows 10 — Multi-Segment E01)

ForensIQ reads `.E01` images directly in memory. You **do not** need to convert or unpack the 476 GB virtual volume to disk.

* **Disk Format**: Expert Witness Format (E01) across 9 segments (`LoneWolf.E01`–`LoneWolf.E09`).
* **Partition Table**: GPT (GUID Partition Table).
* **OS Partition Offset**: Sector `1259520` (Auto-detected).
* **Artifacts**: Windows 10 EVTX logs, MAM compressed Prefetch, NTFS `$MFT`.

#### Execution Command:
```bash
# Direct execution (ForensIQ automatically globs all 9 segments and mounts GPT sector 1259520)
py -3.12 run_pipeline.py --image "Lone Wolf/LoneWolf.E01"

# Or if you run without arguments, ForensIQ auto-discovers Lone Wolf in the workspace:
py -3.12 run_pipeline.py
```

---

### 2. NIST CFReDS Data Leakage PC (Windows 7 — Raw DD)

* **Disk Format**: Raw Bitstream (`.dd` / `.raw`).
* **Partition Table**: MBR (Master Boot Record).
* **OS Partition Offset**: Sector `206848` (Auto-detected).
* **Artifacts**: Windows 7 EVTX logs, uncompressed Prefetch, USB registry traces (`setupapi.dev.log`, `USBSTOR`).

#### Execution Command:
```bash
py -3.12 run_pipeline.py --image path/to/cfreds_2015_data_leakage_pc.dd
```

---

### 3. SCHARDT Hacking Case (Windows XP — Raw 001)

* **Disk Format**: Raw Split / Bitstream (`.001` / `.raw`).
* **Partition Table**: MBR (Legacy).
* **OS Partition Offset**: Sector `63` (Auto-detected).
* **Artifacts**: Legacy Windows `.evt` logs (`SysEvent.Evt`, `SecEvent.Evt`), XP Prefetch.

#### Execution Command:
```bash
py -3.12 run_pipeline.py --image path/to/SCHARDT.001
```

---

### 4. Fast Analysis Mode (Pre-Extracted Artifacts)

If artifacts are already present in the `artifacts/` directory, you can run all machine learning, burst detection, SHAP attributions, and baseline benchmarks instantly without needing any disk image:

```bash
py -3.12 run_pipeline.py --skip-extraction
```

Or start directly from a specific pipeline stage:
```bash
py -3.12 run_pipeline.py --start-at feature_engineering.py
```

---

## ⚙️ Environment Prerequisites

ForensIQ runs on Windows, Linux, and macOS. Ensure the required Python libraries are installed:

```bash
pip install -r requirements.txt
```

### Direct E01 Support
Direct streaming of `.E01` containers relies on `libewf-python`:
```bash
pip install libewf-python
```

---

## 🧭 Partition Offset Reference & Auto-Detection

ForensIQ automatically inspects partition tables and searches the root directory for Windows markers (`Windows`, `Winnt`, `Users`, or `Documents and Settings`).

| Case / OS | Partition Type | Common Sector Offset | Byte Offset | Detection Mechanism |
|:---|:---:|:---:|:---:|:---|
| **Windows 10 (Lone Wolf)** | GPT Basic Data | `1259520` | 644,874,240 | Auto-detected from GPT partition entry |
| **Windows 7 (NIST CFReDS)** | MBR Partition 2 | `206848` | 105,906,176 | Auto-detected from MBR table |
| **Windows XP (SCHARDT)** | MBR Partition 1 | `63` | 32,256 | Auto-detected from MBR table |
| **Single-Partition MBR** | MBR Standard | `2048` | 1,048,576 | Auto-detected |

If an unusual partition layout is used, you can manually specify the offset:
```bash
py -3.12 run_pipeline.py --image path/to/image.dd --offset 1259520
```
