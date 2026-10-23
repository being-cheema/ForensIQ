import os
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable

def generate_pdf():
    pdf_path = "reports/ForensIQ_Data_Leakage_Ground_Truth_Scoring.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=14
    )
    
    section_h2 = ParagraphStyle(
        'SecH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=10,
        spaceAfter=8
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1E293B')
    )
    
    cell_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )
    
    stat_label = ParagraphStyle(
        'StatLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#334155')
    )
    
    stat_val = ParagraphStyle(
        'StatVal',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0F172A')
    )

    story = []
    
    # Header
    story.append(Paragraph("ForensIQ — NIST CFReDS Data Leakage Scenario Evaluation", title_style))
    story.append(Paragraph("Ground Truth Validation & Explainable AI (SHAP) Attribution Report | Case: Iaman Informant / OOO Corp", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2563EB'), spaceAfter=12))
    
    # Summary Cards Table
    stats_data = [
        [
            Paragraph("Total Disk Files Extracted:", stat_label), Paragraph("85,017 files", stat_val),
            Paragraph("Target Contamination Rate:", stat_label), Paragraph("5.00%", stat_val)
        ],
        [
            Paragraph("Total Flagged Anomalies:", stat_label), Paragraph("4,227 files", stat_val),
            Paragraph("Measured Flag Rate:", stat_label), Paragraph("4.97% (0.0497)", stat_val)
        ],
        [
            Paragraph("Top Temporal SHAP Delta:", stat_label), Paragraph("delta_ab (2.589362)", stat_val),
            Paragraph("user_path Mean |SHAP|:", stat_label), Paragraph("0.934824 (Active)", stat_val)
        ],
        [
            Paragraph("File Size Mean |SHAP|:", stat_label), Paragraph("size (1.693254)", stat_val),
            Paragraph("temp_path Mean |SHAP|:", stat_label), Paragraph("0.042036 (Active)", stat_val)
        ]
    ]
    
    stats_table = Table(stats_data, colWidths=[150, 200, 150, 240])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 14))
    
    # Main Validation Table
    story.append(Paragraph("Ground Truth Scoring & Artifact Cross-Reference", section_h2))
    
    headers = [
        Paragraph("Artifact (Answer Key)", cell_header),
        Paragraph("On Disk?", cell_header),
        Paragraph("Flagged?", cell_header),
        Paragraph("Dominant SHAP Feat.", cell_header),
        Paragraph("Expected Signal / Forensic Rationale", cell_header),
        Paragraph("Agree?", cell_header)
    ]
    
    val_df = pd.read_csv("features_dataleak/ground_truth_validation.csv")
    
    table_rows = [headers]
    for idx, r in val_df.iterrows():
        # Formatting
        flagged_text = f"<b>{r['Flagged?']}</b>" if r['Flagged?'] == 'Yes' else r['Flagged?']
        agree_text = f"<b>{r['Agree?']}</b>" if r['Agree?'] == 'Yes' else r['Agree?']
        
        row = [
            Paragraph(str(r['Artifact (answer key)']), cell_style),
            Paragraph(str(r['On disk?']), cell_style),
            Paragraph(flagged_text, cell_style),
            Paragraph(f"<code>{r['Dominant SHAP feat.']}</code>", cell_style),
            Paragraph(str(r['Expected signal']), cell_style),
            Paragraph(agree_text, cell_style)
        ]
        table_rows.append(row)
        
    main_table = Table(table_rows, colWidths=[170, 75, 55, 95, 270, 75])
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F1F5F9')]),
    ]))
    story.append(main_table)
    
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "<b>Key Takeaways for Publication:</b> The Isolation Forest model achieved clean alignment with the 5% target contamination threshold (4.97% flag rate). Explainability analysis proves non-zero attribution for <code>user_path</code> (0.9348) and <code>temp_path</code> (0.0420), effectively capturing user-space staging, anti-forensics tools (<code>Eraser.exe</code>), cloud exfiltration remnants (<code>sync_log.log</code>), and optical disc staging decoys.",
        subtitle_style
    ))
    
    doc.build(story)
    print("PDF generated successfully at:", pdf_path)

if __name__ == "__main__":
    generate_pdf()
