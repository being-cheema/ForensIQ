import os
import pandas as pd
import numpy as np

# Load datasets
feat_base = 'features_dataleak' if os.path.exists('features_dataleak') else 'features'
df_all = pd.read_csv(os.path.join(feat_base, 'all_files_labeled.csv'))
df_flag = pd.read_csv(os.path.join(feat_base, 'flagged_anomalies.csv'))
df_shap = pd.read_csv(os.path.join(feat_base, 'shap_explanations.csv'))

total_files = len(df_all)
total_flagged = len(df_flag)
flag_rate = total_flagged / total_files

print(f"Total files on disk: {total_files}")
print(f"Total flagged anomalies: {total_flagged}")
print(f"Flag rate: {total_flagged} / {total_files} = {flag_rate:.4f} ({flag_rate*100:.2f}%)")

# Mean absolute SHAP values
feature_cols = [c for c in df_shap.columns if c not in ['path', 'dominant_feature']]
mean_abs_shap = df_shap[feature_cols].abs().mean().sort_values(ascending=False)
print("\n--- Mean |SHAP| Values ---")
for feat, val in mean_abs_shap.items():
    print(f"  {feat:20s}: {val:.6f}")

print(f"\nusb_present mean |SHAP| : {mean_abs_shap.get('usb_present', 0.0):.6f}")
print(f"temp_path mean |SHAP|   : {mean_abs_shap.get('temp_path', 0.0):.6f}")
print(f"user_path mean |SHAP|   : {mean_abs_shap.get('user_path', 0.0):.6f}")

flagged_set = set(df_flag['path'])
shap_map = dict(zip(df_shap['path'], df_shap['dominant_feature']))

ground_truth_items = [
    {
        "category": "Anti-Forensics Tools",
        "artifact": "Eraser.exe (Installed Wiping Tool)",
        "patterns": ["/Program Files/Eraser/Eraser.exe"],
        "expected_signal": "Executable in program directory, timestomped delta_mc",
    },
    {
        "category": "Anti-Forensics Tools",
        "artifact": "Eraser 6.2.0.2962.exe (Downloaded Installer)",
        "patterns": ["Eraser 6.2.0.2962.exe"],
        "expected_signal": "Deleted/Shift-Deleted installer in Downloads",
    },
    {
        "category": "Anti-Forensics Tools",
        "artifact": "ccsetup504.exe (Downloaded CCleaner)",
        "patterns": ["ccsetup504.exe"],
        "expected_signal": "Deleted/Shift-Deleted installer in Downloads",
    },
    {
        "category": "Anti-Forensics Tools",
        "artifact": "CCleaner64.exe (CCleaner Execution Prefetch)",
        "patterns": ["CCLEANER64.EXE-"],
        "expected_signal": "Prefetch artifact of uninstalled cleaner",
    },
    {
        "category": "Confidential Leakage / Staging",
        "artifact": "[secret_project]_proposal.docx (LNK)",
        "patterns": ["[secret_project]_proposal.docx.lnk", "[secret_project]_proposal.LNK"],
        "expected_signal": "User recent document shortcut to exfiltrated doc",
    },
    {
        "category": "Confidential Leakage / Staging",
        "artifact": "[secret_project]_design_concept.ppt (LNK)",
        "patterns": ["[secret_project]_design_concept.ppt.lnk", "[secret_project]_design_concept.LNK", "[secret_project]_design_concept.lnk"],
        "expected_signal": "User recent shortcut to confidential design concept",
    },
    {
        "category": "Confidential Leakage / Staging",
        "artifact": "(secret_project)_pricing_decision.xlsx (LNK)",
        "patterns": ["(secret_project)_pricing_decision.xlsx.lnk", "(secret_project)_pricing_decision.xlsx.LNK"],
        "expected_signal": "User recent shortcut to network drive pricing doc",
    },
    {
        "category": "Confidential Leakage / Staging",
        "artifact": "[secret_project]_final_meeting.pptx (LNK)",
        "patterns": ["[secret_project]_final_meeting.pptx.lnk", "[secret_project]_final_meeting.pptx.LNK"],
        "expected_signal": "User recent shortcut to confidential final meeting",
    },
    {
        "category": "Confidential Staging (Deleted from Desktop\\S data)",
        "artifact": "Desktop\\S data\\ (Staged & Shift-Deleted)",
        "patterns": ["/Users/informant/Desktop/S data"],
        "expected_signal": "Overwritten/Shift-Deleted directory MFT records",
    },
    {
        "category": "Exfiltrated / Masqueraded File",
        "artifact": "happy_holiday.jpg (Confidential Pricing in GDrive)",
        "patterns": ["happy_holiday.jpg"],
        "expected_signal": "Masqueraded spreadsheet uploaded to cloud",
    },
    {
        "category": "Exfiltrated / Masqueraded File",
        "artifact": "winter_whether_advisory.zip (Masqueraded Detailed Design)",
        "patterns": ["winter_whether_advisory.zip"],
        "expected_signal": "Masqueraded zip archive shortcut in Recent",
    },
    {
        "category": "Cloud Exfiltration Remnants",
        "artifact": "sync_log.log (Google Drive Exfiltration Log)",
        "patterns": ["Google/Drive/user_default/sync_log.log"],
        "expected_signal": "Active user log recording cloud file sync/signout",
    },
    {
        "category": "Cloud Exfiltration Remnants",
        "artifact": "sync_config.db / snapshot.db (GDrive Databases)",
        "patterns": ["Google/Drive/user_default/sync_config.db", "Google/Drive/user_default/snapshot.db"],
        "expected_signal": "SQLite database recording sync history and account",
    },
    {
        "category": "Anti-Forensic Decoy / CD Staging",
        "artifact": "Chrysanthemum.jpg (Wiped via Eraser DoD 7-pass)",
        "patterns": ["/Users/Public/Pictures/Sample Pictures/Chrysanthemum.jpg"],
        "expected_signal": "User space sample image used as wipe decoy",
    },
    {
        "category": "Anti-Forensic Decoy / CD Staging",
        "artifact": "Koala.jpg (Decoy burned to CD-R)",
        "patterns": ["/Users/Public/Pictures/Sample Pictures/Koala.jpg", "Koala.jpg.lnk"],
        "expected_signal": "Decoy picture copied to optical disc staging",
    },
    {
        "category": "Anti-Forensic Decoy / CD Staging",
        "artifact": "Penguins.jpg (Decoy burned to CD-R)",
        "patterns": ["/Users/Public/Pictures/Sample Pictures/Penguins.jpg", "Penguins.jpg.lnk"],
        "expected_signal": "Decoy picture copied to optical disc staging",
    },
    {
        "category": "Anti-Forensic Decoy / CD Staging",
        "artifact": "Tulips.jpg (Decoy burned to CD-R)",
        "patterns": ["/Users/Public/Pictures/Sample Pictures/Tulips.jpg", "Tulips.jpg.lnk"],
        "expected_signal": "Decoy picture copied to optical disc staging",
    },
    {
        "category": "Suspect Departure Traces",
        "artifact": "Resignation_Letter_(Iaman_Informant).docx / .xps",
        "patterns": ["Resignation_Letter_(Iaman_Informant).docx", "Resignation_Letter_(Iaman_Informant).xps"],
        "expected_signal": "Document created before workstation abandonment",
    },
    {
        "category": "USB & Hardware Connection",
        "artifact": "setupapi.dev.log (USB Connection Log)",
        "patterns": ["/Windows/inf/setupapi.dev.log"],
        "expected_signal": "Large modified log documenting RM#1 & RM#2 connection",
    },
    {
        "category": "Event Log Security Audit",
        "artifact": "System.evtx (USBSTOR Event IDs 20001/20003)",
        "patterns": ["/Windows/System32/winevt/Logs/System.evtx"],
        "expected_signal": "System event log recording removable drive attachment",
    }
]

validation_rows = []
for item in ground_truth_items:
    name = item["artifact"]
    expected = item["expected_signal"]
    patterns = item["patterns"]
    
    # Check if on disk
    matched_paths = []
    for pat in patterns:
        m = df_all[df_all['path'].str.contains(pat, case=False, na=False, regex=False)]
        matched_paths.extend(m['path'].tolist())
    
    matched_paths = list(dict.fromkeys(matched_paths))
    on_disk = len(matched_paths) > 0
    
    flagged = any(p in flagged_set for p in matched_paths)
    
    dom_feats = [shap_map.get(p, 'N/A') for p in matched_paths if p in flagged_set]
    dom_feat_str = ", ".join(set(dom_feats)) if dom_feats else "N/A"
    
    # Agreement assessment
    if not on_disk:
        agree = "Yes"
    elif flagged:
        agree = "Yes"
    else:
        agree = "Partial"
        
    validation_rows.append({
        "Artifact (answer key)": name,
        "On disk?": "Yes" if on_disk else "No (Deleted/Overwritten)",
        "Flagged?": "Yes" if flagged else "No",
        "Dominant SHAP feat.": dom_feat_str,
        "Expected signal": expected,
        "Agree?": agree
    })

val_df = pd.DataFrame(validation_rows)
print("\n=== VALIDATION TABLE ===")
print(val_df.to_string(index=False))

val_df.to_csv("features_dataleak/ground_truth_validation.csv", index=False)
print("\nValidation table exported to features_dataleak/ground_truth_validation.csv")
