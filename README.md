# ForensIQ 🔍

Autonomous, AI-powered Digital Forensics & Incident Response (DFIR) platform.

ForensIQ triages raw disk images non-invasively, extracts forensic artifacts ($MFT, Event Logs, Prefetch, Registry), detects insider threat anomalies using unsupervised machine learning, and provides explainable AI (XAI) attributions mapped to MITRE ATT&CK®.

---

## Key Features

- **Non-Invasive Extraction**: Parses raw disk images (`.raw`, `.dd`) and Expert Witness (`.E01`) files without mounting.
- **Unsupervised ML Detection**: Flags anomalous file system and execution activity using Isolation Forest and k-NN.
- **Explainable AI (SHAP)**: Generates game-theoretic feature attribution charts explaining why each file was flagged.
- **MITRE ATT&CK® Mapping**: Maps detected indicators directly to relevant adversarial techniques.
- **Automated Reporting**: Produces interactive HTML reports, unified timelines, and containment scripts.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/juveenasnowlyn-jpg/ForensIQ.git
cd ForensIQ
pip install -r requirements.txt
```

### 2. Usage

```bash
# Run the complete automated pipeline
py -3.12 run_pipeline.py

# Skip extraction and run analysis on existing artifacts
py -3.12 run_pipeline.py --skip-extraction

# Run baseline benchmark evaluation
py -3.12 evaluate_baselines.py

# Convert E01 image to raw DD
py -3.12 convert_e01.py --image path/to/image.E01
```

---

## Documentation

Comprehensive technical documentation is included in the repository:
- [**ForensIQ Complete Technical Handbook**](ForensIQ_Complete_Technical_Handbook.pdf) — Architecture, ML formulas, and benchmark results.
- [**ForensIQ Researcher Action Guide**](ForensIQ_Researcher_Action_Guide.pdf) — Step-by-step triage protocols and checklists.
