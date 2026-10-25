"""
generate_forensiq_handbook_pdf.py
=================================
Generates the comprehensive, publication-quality technical handbook:
'ForensIQ_Complete_Technical_Handbook.pdf'
Updated with:
- 12-Stage Automated Pipeline Architecture
- 17-Feature Forensic Extraction Space
- Milestone 5 Scientific Evaluation & Baseline Benchmark (Equal-Budget Comparisons)
- ATT&CK Evidence Cards & Scientific Standards
- Complete Verified Forensic Bug Fixes (Bitmask, Timestamps, Scaler Persistence)
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        if self._pageNumber > 1:
            self.drawString(54, 750, "ForensIQ — Complete Technical Mastery Handbook")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

            self.line(54, 45, 558, 45)
            self.drawString(54, 32, "Confidential — ForensIQ AI DFIR Framework")
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(558, 32, page_text)
        self.restoreState()


def build_handbook_pdf(output_filename="ForensIQ_Complete_Technical_Handbook.pdf"):
    pdf_path = os.path.abspath(output_filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=13,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#0369A1"),
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5
    )

    term_title = ParagraphStyle(
        'TermTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A")
    )

    term_desc = ParagraphStyle(
        'TermDesc',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#334155")
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E40AF")
    )

    story = []

    # ================= COVER / TITLE BLOCK =================
    story.append(Paragraph("FORENSIQ: AI-POWERED DIGITAL FORENSICS", title_style))
    story.append(Paragraph("Comprehensive Technical Reference, Architecture, Baselines & Operational Handbook", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2563EB"), spaceAfter=12))

    meta_text = (
        "<b>Framework:</b> Autonomous Digital Forensics & Incident Response (DFIR) with Machine Learning & XAI<br/>"
        "<b>Canonical Pipeline:</b> 12-Stage Automated Triage Engine | 17-Feature Forensic Space<br/>"
        "<b>Evaluated Evidence:</b> NIST CFReDS Data Leakage Scenario (Windows 7 SP1 x64, 85,017 Files)<br/>"
        "<b>Compliance:</b> NIST SP 800-86 / ISO/IEC 27042 / MITRE ATT&CK v14 Standards"
    )
    story.append(Paragraph(meta_text, body_style))
    story.append(Spacer(1, 10))

    # ================= SECTION 1: ARCHITECTURE OVERVIEW =================
    story.append(Paragraph("1. System Architecture: The 12-Stage ForensIQ Pipeline", h1_style))
    story.append(Paragraph(
        "ForensIQ orchestrates end-to-end evidence ingestion, artifact parsing, feature engineering, "
        "unsupervised anomaly scoring, temporal burst detection, confidence tiering, ATT&CK mapping, "
        "Explainable AI attributions, interactive timeline synthesis, and scientific baseline benchmarking:",
        body_style
    ))

    pipeline_stages = [
        ("Stage 1: Evidence Ingestion & Partition Probing", "extractor.py", "Parses raw disk images (.raw/.dd) and E01 files without partition mounting. Extracts MFT filesystem metadata, EVT/EVTX logs, Prefetch, and Registry hives."),
        ("Stage 2: Cryptographic Manifest Verification", "chain_of_custody.py", "Computes streaming dual hashes (SHA-256 and MD5) across all 102 extracted artifacts, establishing a verifiable baseline manifest."),
        ("Stage 3: 17-Feature Forensic Engineering", "feature_engineering.py", "Extracts 17 numerical features per file: MACB deltas with zero-timestamp masking, size, deleted bitmask flags, executable/archive extensions, user/temp paths, and prefetch execution indicators."),
        ("Stage 4: Isolation Forest Anomaly Detection (v1)", "anomaly_detection.py", "Trains Isolation Forest on the standardized 17-feature matrix. Flags the top anomalous records into flagged_anomalies.csv and bundles (model, scaler, cols)."),
        ("Stage 5: Sliding-Window Temporal Burst Detection (v2)", "burst_detection.py", "Performs moving-window aggregation across MFT modification and EVTX event timestamps to detect rapid staging, wiping, or encryption bursts."),
        ("Stage 6: Multi-Artifact Confidence Calibration", "confidence_tiers.py", "Classifies anomalous candidates into CRITICAL, HIGH, MEDIUM, and LOW risk tiers based on decision boundary quartiles."),
        ("Stage 7: MITRE ATT&CK Technique Mapping", "mitre_mapper.py", "Maps anomaly signatures to MITRE ATT&CK Enterprise techniques (T1070.006 Timestomping, T1052.001 USB Exfiltration, T1036.005 Masquerading)."),
        ("Stage 8: Explainable AI Attribution (TreeSHAP)", "xai_shap.py", "Computes game-theoretic Shapley attributions (TreeExplainer) on raw feature data (data=X_flagged_raw), generating individual waterfall charts and global beeswarm plots."),
        ("Stage 9: Unified Chronological Timeline", "timeline.py", "Fuses MFT filesystem events and EVTX security logs into a timezone-normalized UTC timeline with client-side search and 50-event pagination."),
        ("Stage 10: Automated Incident Remediation", "remediation.py", "Synthesizes actionable containment PowerShell scripts tailored to the detected threat class (account lockout, timestamp reset, malware quarantine)."),
        ("Stage 11: Master Report & Audit Assembly", "forensiq_report.py", "Compiles executive breach classification, CoC hash verification, verifiable ground-truth scoring, and an interactive HTML dashboard."),
        ("Stage 12: Scientific Baseline Benchmark", "evaluate_baselines.py", "Executes equal-budget comparisons (K=25, 50, 100, 250, 500, 1000, 4250) against Random, Heuristic Rules, Univariate, Isolation Forest, and k-NN.")
    ]

    p_table_data = [
        [Paragraph("<b>Pipeline Stage & Core Script</b>", term_title), Paragraph("<b>Forensic Operation & Technical Deliverables</b>", term_title)]
    ]
    for stage_name, script, desc in pipeline_stages:
        p_table_data.append([
            Paragraph(f"<b>{stage_name}</b><br/><code>{script}</code>", term_desc),
            Paragraph(desc, term_desc)
        ])

    p_table = Table(p_table_data, colWidths=[160, 344])
    p_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(p_table)
    story.append(Spacer(1, 10))

    # ================= SECTION 2: 17-FEATURE SPACE =================
    story.append(Paragraph("2. The Canonical 17-Feature Forensic Feature Space", h1_style))
    story.append(Paragraph(
        "Every feature possesses a rigorous forensic definition, unit, and calculation formula, "
        "designed to differentiate malicious actions from benign OS operations:",
        body_style
    ))

    feat_data = [
        [Paragraph("<b>Feature</b>", term_title), Paragraph("<b>Unit / Source</b>", term_title), Paragraph("<b>Exact Formula</b>", term_title), Paragraph("<b>Forensic Purpose</b>", term_title)],
        [Paragraph("<code>delta_mc</code>", term_desc), Paragraph("Seconds / MFT", term_desc), Paragraph("|m_time - c_time| if both > 0 else 0", term_desc), Paragraph("Detects timestomping metadata manipulation.", term_desc)],
        [Paragraph("<code>delta_mb</code>", term_desc), Paragraph("Seconds / MFT", term_desc), Paragraph("|m_time - cr_time| if both > 0 else 0", term_desc), Paragraph("Detects file backdating prior to creation.", term_desc)],
        [Paragraph("<code>delta_ab</code>", term_desc), Paragraph("Seconds / MFT", term_desc), Paragraph("|a_time - cr_time| if both > 0 else 0", term_desc), Paragraph("Detects anomalous access vs birth latency.", term_desc)],
        [Paragraph("<code>future_m</code>", term_desc), Paragraph("Binary / MFT", term_desc), Paragraph("1 if m_time > now_ts else 0", term_desc), Paragraph("Flags timestamps set into the future.", term_desc)],
        [Paragraph("<code>zero_size_recent</code>", term_desc), Paragraph("Binary / MFT", term_desc), Paragraph("1 if size==0 and age < 24h else 0", term_desc), Paragraph("Flags zero-byte touch/wiper artifacts.", term_desc)],
        [Paragraph("<code>size</code>", term_desc), Paragraph("Bytes / MFT", term_desc), Paragraph("meta.size", term_desc), Paragraph("Detects massive data archives or tiny binaries.", term_desc)],
        [Paragraph("<code>is_deleted</code>", term_desc), Paragraph("Binary / MFT", term_desc), Paragraph("bool(flags & UNALLOC)", term_desc), Paragraph("Flags shift-deleted records in free space.", term_desc)],
        [Paragraph("<code>is_exe</code>", term_desc), Paragraph("Binary / Path", term_desc), Paragraph(".exe, .dll, .sys, .scr", term_desc), Paragraph("Isolates executable machine code.", term_desc)],
        [Paragraph("<code>is_archive</code>", term_desc), Paragraph("Binary / Path", term_desc), Paragraph(".zip, .rar, .7z, .tar, .gz", term_desc), Paragraph("Flags data compression staging files.", term_desc)],
        [Paragraph("<code>temp_path</code>", term_desc), Paragraph("Binary / Path", term_desc), Paragraph("contains /temp/ or /tmp/", term_desc), Paragraph("Detects malware staging in temporary folders.", term_desc)],
        [Paragraph("<code>user_path</code>", term_desc), Paragraph("Binary / Path", term_desc), Paragraph("contains /users/ or /docs & settings/", term_desc), Paragraph("Separates user activity from core OS activity.", term_desc)],
        [Paragraph("<code>credential_tool</code>", term_desc), Paragraph("Binary / Prefetch", term_desc), Paragraph("mimikatz, pwdump, cain, 123wasp", term_desc), Paragraph("Flags credential-dumping utility execution.", term_desc)],
        [Paragraph("<code>sniffer_tool</code>", term_desc), Paragraph("Binary / Prefetch", term_desc), Paragraph("wireshark, ethereal, tcpdump, winpcap", term_desc), Paragraph("Flags network packet sniffing execution.", term_desc)],
        [Paragraph("<code>powershell_exec</code>", term_desc), Paragraph("Binary / Prefetch", term_desc), Paragraph("powershell.exe in prefetch", term_desc), Paragraph("Flags script-based living-off-the-land attacks.", term_desc)],
        [Paragraph("<code>cmd_exec</code>", term_desc), Paragraph("Binary / Prefetch", term_desc), Paragraph("cmd.exe in prefetch", term_desc), Paragraph("Flags command shell execution for manual staging.", term_desc)],
        [Paragraph("<code>script_host</code>", term_desc), Paragraph("Binary / Prefetch", term_desc), Paragraph("wscript or cscript in prefetch", term_desc), Paragraph("Flags Windows Script Host execution.", term_desc)],
        [Paragraph("<code>usb_present</code>", term_desc), Paragraph("Binary / Registry", term_desc), Paragraph("SYSTEM USBSTOR non-empty", term_desc), Paragraph("Corroborates physical external storage presence.", term_desc)],
    ]

    t_feat = Table(feat_data, colWidths=[90, 75, 175, 164])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 10))

    # ================= SECTION 3: BASELINE BENCHMARK =================
    story.append(Paragraph("3. Scientific Evaluation & Baseline Benchmark (Milestone 5)", h1_style))
    story.append(Paragraph(
        "To establish whether machine learning adds measurable value compared to simpler approaches, "
        "ForensIQ evaluates 11 ranking methods across 7 matched investigation budgets ($K$) on the 85,017 files of NIST CFReDS:",
        body_style
    ))

    bench_data = [
        [
            Paragraph("<b>Ranking Method</b>", term_title),
            Paragraph("<b>K=25</b>", term_title),
            Paragraph("<b>K=50</b>", term_title),
            Paragraph("<b>K=100</b>", term_title),
            Paragraph("<b>K=250</b>", term_title),
            Paragraph("<b>K=500</b>", term_title),
            Paragraph("<b>K=1000</b>", term_title),
            Paragraph("<b>K=4250 (5%)</b>", term_title)
        ],
        [
            Paragraph("Random Baseline (10 seeds)", term_desc),
            Paragraph("0.0", term_desc), Paragraph("0.0", term_desc), Paragraph("0.0", term_desc),
            Paragraph("0.0", term_desc), Paragraph("0.0", term_desc), Paragraph("0.1", term_desc), Paragraph("1.3±1.2", term_desc)
        ],
        [
            Paragraph("Rule: .exe under /Program Files", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("1/19", term_desc), Paragraph("1/19", term_desc)
        ],
        [
            Paragraph("<b>Rule: Suspicious Paths (User/Temp)</b>", term_title),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("1/19", term_desc),
            Paragraph("<b>12/19</b>", term_title), Paragraph("<b>12/19</b>", term_title), Paragraph("<b>12/19</b>", term_title), Paragraph("<b>13/19</b>", term_title)
        ],
        [
            Paragraph("Univariate: delta_mc", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc)
        ],
        [
            Paragraph("Univariate: File Size", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("1/19", term_desc), Paragraph("6/19", term_desc)
        ],
        [
            Paragraph("<b>Isolation Forest (17 Feats)</b>", term_title),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("<b>7/19</b>", term_title)
        ],
        [
            Paragraph("Isolation Forest Multi-Seed (0–9)", term_desc),
            Paragraph("0.0", term_desc), Paragraph("0.0", term_desc), Paragraph("0.0", term_desc),
            Paragraph("0.0", term_desc), Paragraph("0.0", term_desc), Paragraph("0.0", term_desc), Paragraph("6.6±1.6", term_desc)
        ],
        [
            Paragraph("<b>k-NN Distance Outlier (k=5)</b>", term_title),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("3/19", term_desc), Paragraph("4/19", term_desc), Paragraph("<b>12/19</b>", term_title)
        ],
        [
            Paragraph("Ablation: MACB Deltas Only", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc)
        ],
        [
            Paragraph("Ablation: Path Heuristics Only", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc),
            Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("0/19", term_desc), Paragraph("2/19", term_desc)
        ],
    ]

    t_b = Table(bench_data, colWidths=[134, 46, 46, 46, 46, 46, 50, 60])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
    ]))
    story.append(t_b)
    story.append(Spacer(1, 8))

    # ================= SECTION 4: EVIDENCE CARDS =================
    story.append(Paragraph("4. MITRE ATT&CK Evidence Cards & Corroboration Protocols", h1_style))
    story.append(Paragraph(
        "In accordance with forensic science standards, ForensIQ replaces aggressive heuristic leaps "
        "with evidence-linked observation cards that identify required corroborating artifacts:",
        body_style
    ))

    cards = [
        ("T1070.006 Timestomping", "Divergence between $SI Modified and Record Changed times (delta_mc > 86400s).", "Archive extraction; software installers unpacking older legacy DLLs.", "Compare $STANDARD_INFORMATION ($SI) with kernel-protected $FILE_NAME ($FN) timestamps and USN Journal.", "HYPOTHESIS / SUSPICIOUS DELTA"),
        ("T1070.001 Log Clearing", "Hourly continuity gap in event logs during business hours (event_count == 0).", "Workstation powered off, suspended, or disconnected from network.", "Event ID 1102 (Security cleared) or Event ID 104 (System cleared); power state uptime verification.", "OBSERVED GAP / NEEDS POWER CORROB."),
        ("T1052.001 USB Exfiltration", "Registry key SYSTEM\\CurrentControlSet\\Enum\\USBSTOR contains connected drive.", "Authorized business thumb drive; connection without data copy.", "LNK shortcut files or Shellbags proving navigation of removable drive letter; MFT unallocated file copy traces.", "POSSIBLE CONNECTION / REQUIRES FILE-COPY"),
        ("T1486 Ransomware", "Multiple archive files (.zip, .rar, .7z) flagged in user folders.", "Normal user compression; backup archives; downloaded installers.", "Presence of ransom notes; Shannon entropy > 7.8 across document extensions; dropped locker binaries.", "UNVERIFIED / DATA COMPRESSION ONLY"),
        ("T1003.002 SAM Dumping", "Prefetch execution record matching pwdump, cain, or mimikatz.", "Antivirus scanning SAM hive; Volume Shadow Copy (VSS) routine backups.", "Prefetch execution count > 0; Event ID 4688 process execution logs; output hash dump text files.", "HIGH RISK / PENDING RUNTIME PROOF"),
        ("T1036.005 Masquerading", "File extension conflicts with binary magic header (e.g. .jpg containing Excel XML).", "Software bug or inadvertent user file extension naming.", "Magic byte file header confirmation; LNK shortcuts showing file opened in conflicting host application.", "CONFIRMED MASQUERADING")
    ]

    c_table_data = [
        [Paragraph("<b>ATT&CK Technique</b>", term_title), Paragraph("<b>Observed Forensic Signal</b>", term_title), Paragraph("<b>Alternative Explanations</b>", term_title), Paragraph("<b>Required Corroboration</b>", term_title), Paragraph("<b>Scientific Status</b>", term_title)]
    ]
    for name, obs, alt, cor, stat in cards:
        c_table_data.append([
            Paragraph(f"<b>{name}</b>", term_desc),
            Paragraph(obs, term_desc),
            Paragraph(alt, term_desc),
            Paragraph(cor, term_desc),
            Paragraph(f"<b>{stat}</b>", term_desc)
        ])

    c_table = Table(c_table_data, colWidths=[90, 110, 100, 110, 94])
    c_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(c_table)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated Technical Handbook at: {pdf_path}")
    return pdf_path


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else "ForensIQ_Complete_Technical_Handbook.pdf"
    build_handbook_pdf(out)
