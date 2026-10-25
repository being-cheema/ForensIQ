"""
xai_shap.py
===========
ForensIQ Explainable AI (SHAP) Attribution Engine
Computes TreeExplainer SHAP values across the 17-feature space for flagged anomalies,
generating per-file waterfall attribution charts and global beeswarm/summary plots.
"""

import os
import pickle
import numpy as np
import pandas as pd

# Headless matplotlib configuration
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    import shap
    HAVE_SHAP = True
except ImportError:
    HAVE_SHAP = False

from config import FEAT_DIR, MODEL_DIR, REPORT_DIR
from feature_engineering import FEATURE_COLUMNS


def plot_waterfall(explainer, shap_values, X_flagged_raw, idx, file_path, out_dir):
    """Generate SHAP waterfall plot for a single flagged file."""
    base_value = explainer.expected_value
    if isinstance(base_value, (list, np.ndarray)):
        base_value = float(np.array(base_value).flatten()[0])

    exp = shap.Explanation(
        values=shap_values[idx],
        base_values=base_value,
        data=X_flagged_raw[idx],
        feature_names=FEATURE_COLUMNS,
    )

    fig = plt.figure(figsize=(10, 5), facecolor="white")
    shap.plots.waterfall(exp, show=False, max_display=10)
    plt.title(
        f"SHAP Feature Attribution — {os.path.basename(file_path)}",
        fontsize=13,
        fontweight="bold",
        pad=15,
        color="#111827"
    )
    plt.tight_layout()

    safe_name = file_path.replace("/", "_").replace("\\", "_")[:70]
    out_path = os.path.join(out_dir, f"waterfall_{safe_name}.png")
    plt.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out_path


def compute_shap_explanations():
    if not HAVE_SHAP:
        print("[!] shap package is not installed. Skipping XAI analysis.")
        return False

    model_path = os.path.join(MODEL_DIR, "iforest.pkl")
    x_raw_path = os.path.join(FEAT_DIR, "X_raw.npy")
    x_scaled_path = os.path.join(FEAT_DIR, "X_matrix.npy")
    file_index_path = os.path.join(FEAT_DIR, "file_index.csv")
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")

    for p in [model_path, x_raw_path, x_scaled_path, file_index_path, flagged_path]:
        if not os.path.exists(p):
            print(f"[!] Required file {p} not found. Skipping SHAP computation.")
            return False

    with open(model_path, "rb") as f:
        loaded = pickle.load(f)
        if isinstance(loaded, dict) and "model" in loaded:
            model = loaded["model"]
        elif isinstance(loaded, tuple):
            model = loaded[0]
        else:
            model = loaded

    X_raw = np.load(x_raw_path)
    X_scaled = np.load(x_scaled_path)
    file_paths = pd.read_csv(file_index_path)["path"].values
    flagged = pd.read_csv(flagged_path)

    if flagged.empty or len(flagged) == 0:
        print("[i] Zero flagged anomalies. Skipping SHAP.")
        return False

    flagged_paths = set(flagged["path"].values)
    flagged_idx = [i for i, p in enumerate(file_paths) if p in flagged_paths]

    if not flagged_idx:
        print("[!] No flagged files matched in index.")
        return False

    X_flagged = X_scaled[flagged_idx]
    X_flagged_raw = X_raw[flagged_idx]

    shap_dir = os.path.join(REPORT_DIR, "shap")
    os.makedirs(shap_dir, exist_ok=True)

    print(f"[*] Computing TreeExplainer SHAP values for {len(flagged_idx):,} flagged files...")
    explainer = shap.TreeExplainer(model, data=X_scaled, feature_perturbation="interventional")
    shap_values = explainer.shap_values(X_flagged)

    np.save(os.path.join(FEAT_DIR, "shap_values.npy"), shap_values)

    shap_df = pd.DataFrame(shap_values, columns=FEATURE_COLUMNS[:shap_values.shape[1]])
    shap_df.insert(0, "path", [file_paths[i] for i in flagged_idx])
    shap_df["dominant_feature"] = shap_df[FEATURE_COLUMNS[:shap_values.shape[1]]].abs().idxmax(axis=1)

    shap_csv = os.path.join(FEAT_DIR, "shap_explanations.csv")
    shap_df.to_csv(shap_csv, index=False)
    print(f"[+] SHAP explanations saved to {shap_csv}")

    # Generate waterfall plots for top 10 most anomalous files
    path_to_shap_idx = {file_paths[i]: pos for pos, i in enumerate(flagged_idx)}
    top10 = flagged.sort_values("anomaly_score").head(10)

    print("[+] Generating SHAP waterfall plots for top anomalies:")
    for rank, (_, row) in enumerate(top10.iterrows(), start=1):
        fpath = row["path"]
        if fpath in path_to_shap_idx:
            s_idx = path_to_shap_idx[fpath]
            plot_waterfall(explainer, shap_values, X_flagged_raw, s_idx, fpath, shap_dir)
            print(f"    [{rank:02d}] {os.path.basename(fpath)}")

    # Generate beeswarm summary plot
    fig = plt.figure(figsize=(10, 6), facecolor="white")
    shap.summary_plot(
        shap_values,
        X_flagged_raw,
        feature_names=FEATURE_COLUMNS[:shap_values.shape[1]],
        show=False,
        plot_type="dot",
        max_display=10
    )
    plt.title("SHAP Global Feature Importance & Anomaly Impact", fontsize=14, fontweight="bold", pad=20, color="#111827")
    plt.tight_layout()
    plt.savefig(os.path.join(shap_dir, "shap_summary_beeswarm.png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Generate bar summary plot
    fig = plt.figure(figsize=(10, 6), facecolor="white")
    shap.summary_plot(
        shap_values,
        X_flagged_raw,
        feature_names=FEATURE_COLUMNS[:shap_values.shape[1]],
        show=False,
        plot_type="bar",
        max_display=10
    )
    plt.title("SHAP Mean Absolute Feature Importance (Top 10)", fontsize=14, fontweight="bold", pad=20, color="#111827")
    plt.tight_layout()
    plt.savefig(os.path.join(shap_dir, "shap_summary_bar.png"), dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    mean_abs = pd.Series(np.abs(shap_values).mean(axis=0), index=FEATURE_COLUMNS[:shap_values.shape[1]]).sort_values(ascending=False)
    print("\n[+] Mean |SHAP| per feature:")
    print(mean_abs.head(8).to_string())
    return True


if __name__ == "__main__":
    compute_shap_explanations()