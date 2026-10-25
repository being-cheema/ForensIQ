"""
anomaly_detection.py
====================
ForensIQ Machine Learning Anomaly Detection Engine
Trains an Isolation Forest model over standardized forensic feature space (17 features)
to identify anomalous and suspicious files (timestomping, credential dumpers, covert exfil).
"""

import os
import pickle
import numpy as np
import pandas as pd

# Headless matplotlib configuration
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from sklearn.ensemble import IsolationForest
from config import FEAT_DIR, MODEL_DIR, CONTAMINATION, REPORT_DIR
from feature_engineering import FEATURE_COLUMNS


def train_and_report(contamination=CONTAMINATION):
    """
    Trains the Isolation Forest model and outputs flagged anomalies,
    detailed triage summaries, and score distribution visualizations.
    Guards against empty feature matrices (M-5) and calibrates decision thresholds (H-3).
    """
    x_matrix_path = os.path.join(FEAT_DIR, "X_matrix.npy")
    x_raw_path = os.path.join(FEAT_DIR, "X_raw.npy")
    file_index_path = os.path.join(FEAT_DIR, "file_index.csv")

    if not os.path.exists(x_matrix_path) or not os.path.exists(file_index_path):
        raise FileNotFoundError(f"[!] Feature matrix or file index missing in {FEAT_DIR}. Run feature_engineering first.")

    X = np.load(x_matrix_path)
    file_paths = pd.read_csv(file_index_path)["path"].values

    if X.shape[0] == 0 or len(file_paths) == 0:
        print("[!] Feature matrix is empty. Skipping Isolation Forest model training.")
        return None, None

    print(f"[*] Training Isolation Forest on {X.shape[0]:,} files across {X.shape[1]} features...")

    # Train Isolation Forest
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples="auto",
        random_state=42
    )
    model.fit(X)

    # decision_function: continuous score where < 0 indicates anomaly, >= 0 normal
    scores = model.decision_function(X)
    labels = model.predict(X)  # -1 = anomaly, +1 = normal

    # Save trained model and full bundle (Milestone 3 Task 5, Milestone 6)
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_DIR, "iforest.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    scaler_path = os.path.join(FEAT_DIR, "scaler.pkl")
    scaler = None
    if os.path.exists(scaler_path):
        with open(scaler_path, "rb") as sf:
            scaler = pickle.load(sf)

    bundle_path = os.path.join(MODEL_DIR, "iforest_bundle.pkl")
    cols = FEATURE_COLUMNS[:X.shape[1]]
    with open(bundle_path, "wb") as f:
        pickle.dump({"model": model, "scaler": scaler, "features": cols}, f)

    flagged_count = int((labels == -1).sum())
    print(f"[+] Model saved to {model_path}")
    print(f"[+] Flagged anomalies: {flagged_count:,} of {len(labels):,} files ({flagged_count / len(labels) * 100:.1f}%)")

    # Load raw feature values for reporting
    X_raw = np.load(x_raw_path) if os.path.exists(x_raw_path) else X

    cols = FEATURE_COLUMNS[:X_raw.shape[1]]
    results = pd.DataFrame(X_raw, columns=cols)
    results.insert(0, "path", file_paths)
    results["anomaly_score"] = scores
    results["is_anomaly"] = (labels == -1).astype(int)

    flagged = results[results["is_anomaly"] == 1].sort_values("anomaly_score")

    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    flagged.to_csv(flagged_path, index=False)
    print(f"[+] Saved flagged anomalies to {flagged_path}")

    # Decision threshold calibration (H-3):
    # In scikit-learn, decision_function = score_samples - offset_.
    # The true classification boundary is exactly 0.0 (or scores corresponding to -offset_).
    actual_decision_threshold = 0.0

    # Terminal Reporting & Verification
    print("\n" + "=" * 75)
    print("   FORENSIQ ANOMALY DETECTION — TRIAGE SUMMARY")
    print("=" * 75)
    print(f"\n[1] SCORE DISTRIBUTION STATISTICS:")
    print(f"    • Total Analyzed Files   : {len(scores):,}")
    print(f"    • Total Flagged Anomaly  : {flagged_count:,}")
    print(f"    • Score Range            : [{scores.min():.4f} .. {scores.max():.4f}]")
    print(f"    • Decision Boundary (0.0): {actual_decision_threshold:.4f} (scores < 0 are anomalous)")

    if len(flagged) > 0:
        q25, q50, q75 = np.percentile(flagged["anomaly_score"], [25, 50, 75])
        print(f"    • Flagged Score Q25 (CRITICAL) : <= {q25:.4f}")
        print(f"    • Flagged Score Q50 (HIGH)     : <= {q50:.4f}")
        print(f"    • Flagged Score Q75 (MEDIUM)   : <= {q75:.4f}")

    print(f"\n[2] NIST CFREDS GROUND-TRUTH ARTIFACT MATCHES:")
    gt_keywords = {
        "Cain & Abel (Credential Dumper)": r"cain",
        "DEFRAG (Anti-Forensic Cover)"   : r"defrag",
        "NetStumbler (Wireless Scanner)" : r"stumbler|netstumbler",
        "Ethereal / WinPcap (Sniffer)"   : r"ethereal|winpcap|wpcap",
        "Anonymizer (Covert Channel)"    : r"anonymizer",
        "123 Write Stored Passwords"     : r"123.?write|stored.?passwords",
    }
    for name, pat in gt_keywords.items():
        hits = flagged[flagged["path"].str.contains(pat, case=False, regex=True, na=False)]
        if len(hits):
            example_name = os.path.basename(str(hits.iloc[0]["path"]))
            print(f"    • [MATCH] {name:<32} -> {len(hits):>2} hits (e.g., {example_name})")
        else:
            print(f"    • [none]  {name:<32} ->  0 hits")

    print(f"\n[3] TOP 15 MOST ANOMALOUS FILES (RANKED WORKLIST):")
    print(f"    {'Rank':<6} {'Anomaly Score':<16} {'File Path'}")
    print("    " + "-" * 68)
    for idx, row in enumerate(flagged.head(15).itertuples(), 1):
        short_path = str(row.path)
        if len(short_path) > 48:
            short_path = "..." + short_path[-45:]
        print(f"    #{idx:<5} {row.anomaly_score:<16.4f} {short_path}")
    print("=" * 75 + "\n")

    # Generate Visualization Plot
    try:
        generate_score_chart(scores, actual_decision_threshold, contamination)
    except Exception as e:
        print(f"[!] Warning: Could not generate score chart: {e}")

    return results, flagged


def generate_score_chart(scores, decision_threshold, contamination):
    """Generates the dark-themed anomaly score distribution histogram (H-7)."""
    fig, ax = plt.subplots(figsize=(15, 8))

    counts, bins, patches = ax.hist(
        scores,
        bins=30,
        color="#00C8FF",
        edgecolor="white",
        linewidth=1.2,
        alpha=0.9
    )

    # True decision boundary line (H-3)
    ax.axvline(
        decision_threshold,
        color="red",
        linewidth=3,
        linestyle="--",
        label=f"Decision Boundary (Score = {decision_threshold:.1f})"
    )

    max_count = max(counts) if len(counts) > 0 else 1
    for count, patch in zip(counts, patches):
        if count > 0:
            ax.text(
                patch.get_x() + patch.get_width() / 2,
                count + max_count * 0.02,
                str(int(count)),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
                color="white"
            )

    fig.patch.set_facecolor("#0a0c14")
    ax.set_facecolor("#13151f")

    ax.set_title("Isolation Forest Anomaly Score Distribution", fontsize=18, color="white", fontweight="bold", pad=15)
    ax.set_xlabel("Anomaly Score (Lower / Negative = More Suspicious)", fontsize=14, color="white")
    ax.set_ylabel("Number of Files", fontsize=14, color="white")

    xmin = np.floor(scores.min() * 20) / 20
    xmax = np.ceil(scores.max() * 20) / 20
    ax.set_xlim(xmin, xmax)
    ax.xaxis.set_major_locator(MultipleLocator(0.05))
    ax.xaxis.set_minor_locator(MultipleLocator(0.01))

    step = 100
    if max_count < 500:
        step = 50
    if max_count < 200:
        step = 20
    if max_count < 100:
        step = 10

    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_minor_locator(MultipleLocator(step / 2))

    ax.tick_params(axis="both", which="major", colors="white", labelsize=12, width=1.5, length=8)
    ax.tick_params(axis="both", which="minor", colors="white", width=1, length=4)

    ax.grid(which="major", color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
    ax.grid(which="minor", color="gray", linestyle=":", linewidth=0.5, alpha=0.3)

    for spine in ax.spines.values():
        spine.set_color("white")
        spine.set_linewidth(1.2)

    legend = ax.legend(facecolor="#111521", edgecolor="white", fontsize=12)
    for text in legend.get_texts():
        text.set_color("white")

    plt.tight_layout()
    os.makedirs(REPORT_DIR, exist_ok=True)
    chart_path = os.path.join(REPORT_DIR, "anomaly_scores.png")
    plt.savefig(chart_path, dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[+] Saved anomaly score distribution chart to {chart_path}")


if __name__ == "__main__":
    train_and_report()