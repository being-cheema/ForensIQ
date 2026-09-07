import pandas as pd
import os
from config import FEAT_DIR, REPORT_DIR

flagged = pd.read_csv(f"{FEAT_DIR}/flagged_anomalies_v2.csv")
flagged = flagged[flagged["is_anomaly_v2"] == 1].copy()

p25 = flagged["anomaly_score_v2"].quantile(0.25)
p50 = flagged["anomaly_score_v2"].quantile(0.50)
p75 = flagged["anomaly_score_v2"].quantile(0.75)

print(f"CRITICAL threshold: {p25:.4f}")
print(f"HIGH threshold:     {p50:.4f}")
print(f"MEDIUM threshold:   {p75:.4f}")

def assign_tier(score):
    if score <= p25:
        return "CRITICAL"
    elif score <= p50:
        return "HIGH"
    elif score <= p75:
        return "MEDIUM"
    else:
        return "LOW"

flagged["confidence_tier"] = flagged["anomaly_score_v2"].apply(assign_tier)

tier_order = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3
}

flagged["tier_rank"] = flagged["confidence_tier"].map(tier_order)

flagged = flagged.sort_values(
    ["tier_rank", "anomaly_score_v2"]
)

counts = flagged["confidence_tier"].value_counts()

for t in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
    print(f"{t:10s}: {counts.get(t, 0):4d} files")

flagged[
    ["path", "anomaly_score_v2", "confidence_tier"]
].to_csv(
    f"{FEAT_DIR}/investigation_queue.csv",
    index=False
)

print(f"[+] Queue in {FEAT_DIR}/investigation_queue.csv")