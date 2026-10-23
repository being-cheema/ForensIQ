"""
confidence_tiers.py
===================
ForensIQ Anomaly Confidence Tier Calibration
Ranks flagged anomalies into CRITICAL, HIGH, MEDIUM, and LOW confidence tiers
based on quartile score distribution, outputting a prioritized investigation queue.
"""

import os
import pandas as pd
from config import FEAT_DIR, REPORT_DIR


def calibrate_confidence_tiers():
    v2_path = os.path.join(FEAT_DIR, "flagged_anomalies_v2.csv")
    v1_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")

    source_path = v2_path if os.path.exists(v2_path) else v1_path
    score_col = "anomaly_score_v2" if os.path.exists(v2_path) else "anomaly_score"
    flag_col = "is_anomaly_v2" if os.path.exists(v2_path) else "is_anomaly"

    if not os.path.exists(source_path):
        print(f"[!] Flagged anomalies file not found at {source_path}. Skipping confidence tiers.")
        return False

    df = pd.read_csv(source_path)
    if flag_col not in df.columns or score_col not in df.columns:
        print(f"[!] Expected columns ({flag_col}, {score_col}) not found. Skipping confidence tiers.")
        return False

    flagged = df[df[flag_col] == 1].copy()
    if flagged.empty:
        print("[i] Zero flagged anomalies to tier. Writing empty queue.")
        empty_queue = pd.DataFrame(columns=["path", score_col, "confidence_tier"])
        empty_queue.to_csv(os.path.join(FEAT_DIR, "investigation_queue.csv"), index=False)
        return True

    p25 = flagged[score_col].quantile(0.25)
    p50 = flagged[score_col].quantile(0.50)
    p75 = flagged[score_col].quantile(0.75)

    print("\n[+] Calibrating Investigation Confidence Tiers:")
    print(f"    • CRITICAL threshold (Q25): {p25:.4f}")
    print(f"    • HIGH threshold     (Q50): {p50:.4f}")
    print(f"    • MEDIUM threshold   (Q75): {p75:.4f}")

    def assign_tier(score):
        if score <= p25:
            return "CRITICAL"
        elif score <= p50:
            return "HIGH"
        elif score <= p75:
            return "MEDIUM"
        else:
            return "LOW"

    flagged["confidence_tier"] = flagged[score_col].apply(assign_tier)
    tier_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    flagged["tier_rank"] = flagged["confidence_tier"].map(tier_order)
    flagged = flagged.sort_values(["tier_rank", score_col])

    counts = flagged["confidence_tier"].value_counts()
    for t in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        print(f"    • {t:10s}: {counts.get(t, 0):4d} files")

    queue_path = os.path.join(FEAT_DIR, "investigation_queue.csv")
    flagged[["path", score_col, "confidence_tier"]].to_csv(queue_path, index=False)
    print(f"[+] Investigation queue generated: {queue_path}")
    return True


if __name__ == "__main__":
    calibrate_confidence_tiers()