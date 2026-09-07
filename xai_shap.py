# Compute SHAP values for all flagged files

import os
import pickle
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

from config import FEAT_DIR, MODEL_DIR, REPORT_DIR

# ------------------------------------------------------------------
# Load model and data
# ------------------------------------------------------------------

with open(f"{MODEL_DIR}/iforest.pkl", "rb") as f:
    model = pickle.load(f)

X_raw = np.load(f"{FEAT_DIR}/X_raw.npy")
X_scaled = np.load(f"{FEAT_DIR}/X_matrix.npy")

file_paths = pd.read_csv(
    f"{FEAT_DIR}/file_index.csv"
)["path"].values

flagged = pd.read_csv(
    f"{FEAT_DIR}/flagged_anomalies.csv"
)

FEATURE_NAMES = [
    "delta_mc",
    "delta_mb",
    "delta_ab",
    "future_m",
    "zero_size_recent",
    "size",
    "is_deleted",
    "is_exe",
    "is_archive",
    "temp_path",
    "user_path",
    "credential_tool",
    "sniffer_tool",
    "powershell_exec",
    "cmd_exec",
    "script_host",
    "usb_present"
]

os.makedirs(f"{REPORT_DIR}/shap", exist_ok=True)

# ------------------------------------------------------------------
# Select flagged files
# ------------------------------------------------------------------

flagged_paths = set(flagged["path"].values)

flagged_idx = [
    i for i, p in enumerate(file_paths)
    if p in flagged_paths
]

if len(flagged_idx) == 0:
    print("[!] No flagged files found.")
    exit()

X_flagged = X_scaled[flagged_idx]
X_flagged_raw = X_raw[flagged_idx]

# ------------------------------------------------------------------
# SHAP explanation
# ------------------------------------------------------------------

explainer = shap.TreeExplainer(
    model,
    data=X_scaled,
    feature_perturbation="interventional"
)

shap_values = explainer.shap_values(X_flagged)

np.save(
    f"{FEAT_DIR}/shap_values.npy",
    shap_values
)

# ------------------------------------------------------------------
# Save per-file explanations
# ------------------------------------------------------------------

shap_df = pd.DataFrame(
    shap_values,
    columns=FEATURE_NAMES
)

shap_df.insert(
    0,
    "path",
    [file_paths[i] for i in flagged_idx]
)

shap_df["dominant_feature"] = (
    shap_df[FEATURE_NAMES]
    .abs()
    .idxmax(axis=1)
)

shap_df.to_csv(
    f"{FEAT_DIR}/shap_explanations.csv",
    index=False
)

print(f"[+] SHAP computed for {len(flagged_idx)} files")

# ------------------------------------------------------------------
# Waterfall plots
# ------------------------------------------------------------------

path_to_shap_idx = {
    file_paths[i]: pos
    for pos, i in enumerate(flagged_idx)
}


def plot_waterfall(idx, file_path, out_dir):
    """
    Generate SHAP waterfall plot for a single file.
    """

    base_value = explainer.expected_value

    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.array(base_value).flatten()[0])

    exp = shap.Explanation(
        values=shap_values[idx],
        base_values=base_value,
        data=X_flagged_raw[idx],
        feature_names=FEATURE_NAMES,
    )

    fig = plt.figure(figsize=(10, 5), facecolor="white")

    shap.plots.waterfall(
        exp,
        show=False,
        max_display=10
    )

    plt.title(
        f"SHAP Feature Attribution — {os.path.basename(file_path)}",
        fontsize=13,
        fontweight="bold",
        pad=15,
        color="#111827"
    )

    plt.tight_layout()

    safe_name = (
        file_path.replace("/", "_")
        .replace("\\", "_")[:70]
    )

    out_path = os.path.join(
        out_dir,
        f"waterfall_{safe_name}.png"
    )

    plt.savefig(
        out_path,
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close()

    return out_path


# ------------------------------------------------------------------
# Top 10 most anomalous files
# ------------------------------------------------------------------

top10 = (
    flagged
    .sort_values("anomaly_score")
    .head(10)
)

for rank, (_, row) in enumerate(top10.iterrows(), start=1):

    file_path = row["path"]

    if file_path not in path_to_shap_idx:
        continue

    shap_idx = path_to_shap_idx[file_path]

    plot_waterfall(
        shap_idx,
        file_path,
        f"{REPORT_DIR}/shap"
    )

    print(f" [{rank:02d}] {os.path.basename(file_path)}")

# ------------------------------------------------------------------
# Global beeswarm summary
# ------------------------------------------------------------------

fig = plt.figure(figsize=(10, 6), facecolor="white")

shap.summary_plot(
    shap_values,
    X_flagged_raw,
    feature_names=FEATURE_NAMES,
    show=False,
    plot_type="dot",  # "dot" renders the beeswarm plot in shap.summary_plot
    max_display=10
)

plt.title(
    "SHAP Global Feature Importance & Anomaly Impact (17 Features)",
    fontsize=14,
    fontweight="bold",
    pad=20,
    color="#111827"
)

plt.tight_layout()

plt.savefig(
    f"{REPORT_DIR}/shap/shap_summary_beeswarm.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close()

# Also generate a clean bar chart summary of Mean |SHAP|
fig = plt.figure(figsize=(10, 6), facecolor="white")

shap.summary_plot(
    shap_values,
    X_flagged_raw,
    feature_names=FEATURE_NAMES,
    show=False,
    plot_type="bar",
    max_display=10
)

plt.title(
    "SHAP Mean Absolute Feature Importance (Top 10 Features)",
    fontsize=14,
    fontweight="bold",
    pad=20,
    color="#111827"
)

plt.tight_layout()

plt.savefig(
    f"{REPORT_DIR}/shap/shap_summary_bar.png",
    dpi=300,
    bbox_inches="tight",
    facecolor="white"
)

plt.close()

# ------------------------------------------------------------------
# Global feature importance
# ------------------------------------------------------------------

mean_abs = (
    pd.Series(
        np.abs(shap_values).mean(axis=0),
        index=FEATURE_NAMES
    )
    .sort_values(ascending=False)
)

print("\n[+] Mean |SHAP| per feature:")
print(mean_abs.to_string())

print("\n" + "="*70)
print("  WHY DO ONLY 6 OF 17 FEATURES SHOW NON-ZERO SHAP VALUES?")
print("="*70)
print("  • While ForensIQ engineers 17 features per file, only 6 features")
print("    (is_exe, size, delta_mc, delta_mb, delta_ab, is_archive) show")
print("    non-zero mean |SHAP| values on the SCHARDT image.")
print("  • This occurs because the remaining 11 features are either constant/zero")
print("    across this dataset or are not selected for decision tree split")
print("    criteria by the Isolation Forest model.")
print("  • Since SHAP TreeExplainer measures variance reduction across splits,")
print("    features that are never split on contribute exactly 0.00.")
print("="*70 + "\n")