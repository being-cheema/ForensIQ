# Train the Isolation Forest Model

import numpy as np
import pandas as pd
import pickle
import os

from sklearn.ensemble import IsolationForest
from config import FEAT_DIR, MODEL_DIR, CONTAMINATION, REPORT_DIR

# Load features
X = np.load(f"{FEAT_DIR}/X_matrix.npy")
file_paths = pd.read_csv(f"{FEAT_DIR}/file_index.csv")["path"].values

# Train model
model = IsolationForest(
    n_estimators=200,  # more trees = more stable scores
    contamination=CONTAMINATION,
    max_samples="auto",
    random_state=42,
)

model.fit(X)

# Generate scores and labels
scores = model.decision_function(X)  # continuous: lower = more suspicious
labels = model.predict(X)            # -1 = anomaly, +1 = normal

# Save model
os.makedirs(MODEL_DIR, exist_ok=True)

with open(f"{MODEL_DIR}/iforest.pkl", "wb") as f:
    pickle.dump(model, f)

print(f"[+] Model saved to {MODEL_DIR}/iforest.pkl")
print(f"[+] Flagged: {(labels == -1).sum()} of {len(labels)} files")


# --------------------------------------------------
# Generate the flagged anomaly CSV
# --------------------------------------------------

X_raw = np.load(f"{FEAT_DIR}/X_raw.npy")

cols = [
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

results = pd.DataFrame(X_raw, columns=cols)

results.insert(0, "path", file_paths)
results["anomaly_score"] = scores
results["is_anomaly"] = (labels == -1).astype(int)

flagged = (
    results[results["is_anomaly"] == 1]
    .sort_values("anomaly_score")
)

flagged.to_csv(
    f"{FEAT_DIR}/flagged_anomalies.csv",
    index=False
)

# --------------------------------------------------
# Detailed Terminal Reporting & Verification
# --------------------------------------------------

print("\n" + "="*75)
print("   FORENSIQ ANOMALY DETECTION — TRIAGE SUMMARY")
print("="*75)

print(f"\n[1] SCORE DISTRIBUTION STATISTICS:")
print(f"    • Total Analyzed Files   : {len(scores):,}")
print(f"    • Total Flagged (5%)     : {(labels == -1).sum():,}")
print(f"    • Score Range            : [{scores.min():.4f}  ..  {scores.max():.4f}]")

threshold_val = np.percentile(scores, CONTAMINATION * 100)
print(f"    • Decision Threshold (0%): {threshold_val:.4f}")

if len(flagged):
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
    "123 Write All Stored Passwords" : r"123.?write|stored.?passwords",
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
print("    " + "-"*68)
for idx, row in enumerate(flagged.head(15).itertuples(), 1):
    short_path = str(row.path)
    if len(short_path) > 48:
        short_path = "..." + short_path[-45:]
    print(f"    #{idx:<5} {row.anomaly_score:<16.4f} {short_path}")

print("="*75 + "\n")


# --------------------------------------------------
# Visualize anomaly score distribution
# --------------------------------------------------

import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

# Create larger figure
fig, ax = plt.subplots(figsize=(15, 8))

# Plot histogram
counts, bins, patches = ax.hist(
    scores,
    bins=30,                  # Wider bars for better visibility
    color="#00C8FF",
    edgecolor="white",
    linewidth=1.2,
    alpha=0.9
)

# Threshold line
threshold = np.percentile(
    scores,
    CONTAMINATION * 100
)

ax.axvline(
    threshold,
    color="red",
    linewidth=3,
    linestyle="--",
    label=f"Anomaly Threshold ({CONTAMINATION*100:.0f}%)"
)

# --------------------------------------------------
# Display file count on top of every bar
# --------------------------------------------------

max_count = max(counts)

for count, patch in zip(counts, patches):

    if count > 0:

        ax.text(
            patch.get_x() + patch.get_width()/2,
            count + max_count*0.02,
            str(int(count)),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="white"
        )

# --------------------------------------------------
# Styling
# --------------------------------------------------

fig.patch.set_facecolor("#0a0c14")
ax.set_facecolor("#13151f")

ax.set_title(
    "Isolation Forest Anomaly Score Distribution",
    fontsize=18,
    color="white",
    fontweight="bold",
    pad=15
)

ax.set_xlabel(
    "Anomaly Score (Lower = More Suspicious)",
    fontsize=14,
    color="white"
)

ax.set_ylabel(
    "Number of Files",
    fontsize=14,
    color="white"
)

# --------------------------------------------------
# Clear axis divisions
# --------------------------------------------------

# X-axis ticks
xmin = np.floor(scores.min() * 20) / 20
xmax = np.ceil(scores.max() * 20) / 20

ax.set_xlim(xmin, xmax)
ax.xaxis.set_major_locator(MultipleLocator(0.05))
ax.xaxis.set_minor_locator(MultipleLocator(0.01))

# Y-axis ticks
step = 100

if max_count < 500:
    step = 50

if max_count < 200:
    step = 20

if max_count < 100:
    step = 10

ax.yaxis.set_major_locator(MultipleLocator(step))
ax.yaxis.set_minor_locator(MultipleLocator(step/2))

# Tick appearance
ax.tick_params(
    axis="both",
    which="major",
    colors="white",
    labelsize=12,
    width=1.5,
    length=8
)

ax.tick_params(
    axis="both",
    which="minor",
    colors="white",
    width=1,
    length=4
)

# Grid lines
ax.grid(
    which="major",
    color="gray",
    linestyle="--",
    linewidth=0.8,
    alpha=0.6
)

ax.grid(
    which="minor",
    color="gray",
    linestyle=":",
    linewidth=0.5,
    alpha=0.3
)

# White border
for spine in ax.spines.values():
    spine.set_color("white")
    spine.set_linewidth(1.2)

# Legend
legend = ax.legend(
    facecolor="#111521",
    edgecolor="white",
    fontsize=12
)

for text in legend.get_texts():
    text.set_color("white")

plt.tight_layout()

os.makedirs(REPORT_DIR, exist_ok=True)

plt.savefig(
    f"{REPORT_DIR}/anomaly_scores.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

print(f"[+] Saved anomaly score distribution to {REPORT_DIR}/anomaly_scores.png")