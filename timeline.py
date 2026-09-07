# Merge artifact sources into a unified event list

import json
import os
import pandas as pd
from datetime import datetime, timezone
from config import OUT_DIR, FEAT_DIR, REPORT_DIR

events = []

# 1. Flagged MFT anomalies
flagged = pd.read_csv(f"{FEAT_DIR}/flagged_anomalies.csv")

with open(f"{OUT_DIR}/mft/mft_records.json") as f:
    mft = {r["path"]: r for r in json.load(f)}

for _, row in flagged.iterrows():
    rec = mft.get(row["path"], {})
    ts = rec.get("m_time", 0)

    if ts:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)

        events.append({
            "timestamp": dt,
            "source": "MFT",
            "event_id": "ANOMALY",
            "description": f"Suspicious file: {row['path']}",
            "score": row["anomaly_score"]
        })

# 2. Windows Event Log entries
with open(f"{OUT_DIR}/evtx/parsed_events.json") as f:
    evtx = json.load(f)

for ev in evtx:
    try:
        dt = datetime.fromisoformat(
            ev["timestamp"].replace("Z", "+00:00")
        )

        events.append({
            "timestamp": dt,
            "source": ev["source"],
            "event_id": ev["event_id"],
            "description": f"EventID {ev['event_id']}",
            "score": 0
        })

    except Exception:
        pass

# Build timeline
timeline = pd.DataFrame(events)

if not timeline.empty:
    timeline = timeline.sort_values("timestamp")

os.makedirs(f"{REPORT_DIR}/timeline", exist_ok=True)

timeline.to_csv(
    f"{REPORT_DIR}/timeline/timeline.csv",
    index=False
)

print(f"[+] Timeline: {len(timeline)} events")


# Export a self-contained HTML timeline report
def export_html_timeline(timeline):
    rows = ""

    for _, ev in timeline.iterrows():
        is_anom = ev["event_id"] == "ANOMALY"
        cls = 'class="anomaly"' if is_anom else ""

        rows += (
            f'<tr {cls}>'
            f'<td>{ev["timestamp"]}</td>'
            f'<td>{ev["source"]}</td>'
            f'<td>{ev["event_id"]}</td>'
            f'<td>{ev["description"]}</td>'
            f'<td>{ev["score"]:.4f}</td>'
            f'</tr>\n'
        )

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>ForensIQ Timeline</title>
    <style>
        body {{
            background: #0a0c14;
            color: #c4cde0;
            font-family: monospace;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 8px;
            border: 1px solid #1e2538;
        }}
        th {{
            background: #111521;
        }}
        tr.anomaly {{
            background: #2a060a;
            color: #f87171;
        }}
    </style>
</head>
<body>
    <h2>ForensIQ Attack Timeline</h2>
    <table>
        <thead>
            <tr>
                <th>Timestamp</th>
                <th>Source</th>
                <th>EventID</th>
                <th>Description</th>
                <th>Score</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>
"""

    path = f"{REPORT_DIR}/timeline/timeline.html"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)

    print(f"[+] HTML timeline file: {path}")


export_html_timeline(timeline)