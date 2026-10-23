"""
timeline.py
===========
ForensIQ Unified Forensic Timeline & Executive Dashboard Generator
Fuses MFT filesystem activity, Isolation Forest anomalies, and multi-source
Windows Event Logs (EVT/EVTX) into a cohesive chronological event sequence.
Generates CSV export, interactive HTML timeline, and executive dashboard HTML.
"""

import os
import json
import base64
import html
from datetime import datetime, timezone
import pandas as pd

from config import OUT_DIR, FEAT_DIR, REPORT_DIR

TIMELINE_COLUMNS = [
    "timestamp", "source", "event_id", "description", "score", "kind", "severity"
]


def ts_to_dt(unix_ts):
    """Safely convert Unix timestamp to UTC datetime (M-6)."""
    if unix_ts is None or unix_ts == "" or unix_ts == 0:
        return None
    try:
        return datetime.fromtimestamp(float(unix_ts), tz=timezone.utc)
    except Exception:
        return None


def parse_dt(value):
    """Parses ISO timestamp string or datetime object to UTC datetime."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        cleaned = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def read_json(path, default=None):
    """Safely reads JSON file."""
    if default is None:
        default = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def load_all_parsed_events():
    """
    Multi-source event log aggregator (Report 3 Step 4):
    Aggregates events from both modern EVTX and legacy EVT parsed event files.
    """
    events = []
    for candidate in [
        os.path.join(OUT_DIR, "evtx", "parsed_events.json"),
        os.path.join(OUT_DIR, "evt", "parsed_events.json"),
    ]:
        loaded = read_json(candidate, [])
        if loaded:
            events.extend(loaded)
    return events


def detect_category(path_str):
    """Categorizes flagged file path for modern and legacy threats."""
    low = path_str.lower()
    if any(k in low for k in ["onedrive", "dropbox", "box.com", "googledrive"]):
        return "Cloud Storage Sync"
    if any(k in low for k in ["mega", "tor", "anonymizer"]):
        return "Exfiltration / Anonymizer"
    if any(k in low for k in ["cain", "mimikatz", "pwdump", "123wasp", "stored"]):
        return "Credential Harvesting"
    if any(k in low for k in ["wireshark", "ethereal", "tcpdump", "netstumbler"]):
        return "Network Sniffing"
    if any(k in low for k in ["temp", "tmp"]) and low.endswith(".exe"):
        return "Staged Malware / Dropper"
    if low.endswith((".zip", ".rar", ".7z")):
        return "Data Archive / Staging"
    return "Filesystem Anomaly"


def collect_anomaly_events():
    """Extracts flagged anomalies as timeline events."""
    events = []
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    mft_path = os.path.join(OUT_DIR, "mft", "mft_records.json")

    if not os.path.exists(flagged_path):
        return events

    flagged = pd.read_csv(flagged_path)
    mft_records = read_json(mft_path, [])
    mft_lookup = {r["path"]: r for r in mft_records if "path" in r}

    for _, row in flagged.iterrows():
        fpath = str(row["path"])
        rec = mft_lookup.get(fpath, {})
        ts = rec.get("m_time", 0)
        dt = ts_to_dt(ts)
        category = detect_category(fpath)

        if dt:
            events.append({
                "timestamp": dt,
                "source": "MFT",
                "event_id": "ANOMALY",
                "description": f"[{category}] Suspicious file: {fpath}",
                "score": float(row.get("anomaly_score", 0.0)),
                "kind": "anomaly",
                "severity": "critical" if float(row.get("anomaly_score", 0.0)) < -0.1 else "high"
            })
    return events


def collect_log_events():
    """Extracts parsed Windows Event Log entries as timeline events."""
    events = []
    log_entries = load_all_parsed_events()

    for ev in log_entries:
        dt = parse_dt(ev.get("timestamp"))
        if not dt:
            continue

        eid = str(ev.get("event_id", ""))
        source = ev.get("source", "Security")
        computer = ev.get("computer", "")
        msg = ev.get("message", "")
        desc = f"EventID {eid} on {computer}: {msg}" if msg else f"{source} EventID {eid}"

        events.append({
            "timestamp": dt,
            "source": source,
            "event_id": eid,
            "description": desc,
            "score": 0.0,
            "kind": "eventlog",
            "severity": "medium" if eid in ["1102", "4625", "6005", "6006"] else "info"
        })
    return events


def build_timeline():
    """Combines anomalies and event logs into a sorted timeline DataFrame."""
    anomalies = collect_anomaly_events()
    logs = collect_log_events()
    all_events = anomalies + logs

    if not all_events:
        return pd.DataFrame(columns=TIMELINE_COLUMNS)

    df = pd.DataFrame(all_events)
    df = df.sort_values("timestamp").reset_index(drop=True)

    os.makedirs(os.path.join(REPORT_DIR, "timeline"), exist_ok=True)
    csv_path = os.path.join(REPORT_DIR, "timeline", "timeline.csv")
    df.to_csv(csv_path, index=False)
    print(f"[+] Consolidated timeline: {len(df):,} events ({len(anomalies)} anomalies, {len(logs)} log events)")
    return df


def export_html_timeline(timeline):
    """Generates an interactive, styled HTML timeline page."""
    rows = ""
    for _, ev in timeline.iterrows():
        is_anom = ev["kind"] == "anomaly"
        row_cls = 'class="anomaly-row"' if is_anom else ""
        badge_cls = 'badge-anomaly' if is_anom else 'badge-log'
        ts_str = ev["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(ev["timestamp"], datetime) else str(ev["timestamp"])

        rows += f"""
        <tr {row_cls} data-kind="{ev['kind']}" data-text="{html.escape(ev['description'].lower())}">
            <td><code>{ts_str}</code></td>
            <td><span class="badge {badge_cls}">{html.escape(str(ev['source']))}</span></td>
            <td><code>{html.escape(str(ev['event_id']))}</code></td>
            <td>{html.escape(str(ev['description']))}</td>
            <td><code>{ev['score']:.4f}</code></td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>ForensIQ — Forensic Timeline</title>
    <style>
        body {{
            background: #06080e;
            color: #dce4e4;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace;
            margin: 0;
            padding: 24px;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #1e2638;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        h1 {{
            margin: 0;
            font-size: 24px;
            color: #00f2ff;
            letter-spacing: -0.02em;
        }}
        .toolbar {{
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            align-items: center;
        }}
        input[type="text"] {{
            background: #0e1422;
            border: 1px solid #1e293b;
            color: white;
            padding: 8px 14px;
            border-radius: 6px;
            width: 320px;
            font-size: 14px;
        }}
        button {{
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            padding: 8px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
        }}
        button.active {{
            background: #00f2ff;
            color: #000;
            font-weight: 600;
            border-color: #00f2ff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid #161f30;
            text-align: left;
        }}
        th {{
            background: #0d121f;
            color: #7dd3fc;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        tr:hover td {{
            background: #111827;
        }}
        tr.anomaly-row td {{
            background: rgba(239, 68, 68, 0.08);
            border-bottom-color: rgba(239, 68, 68, 0.2);
        }}
        tr.anomaly-row:hover td {{
            background: rgba(239, 68, 68, 0.16);
        }}
        .badge {{
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .badge-anomaly {{
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
            border: 1px solid #ef4444;
        }}
        .badge-log {{
            background: rgba(0, 242, 255, 0.15);
            color: #38bdf8;
            border: 1px solid #0284c7;
        }}
        code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: #0f172a;
            padding: 2px 5px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ForensIQ Forensic Investigation Timeline</h1>
        <div style="font-size: 13px; color: #64748b;">Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>
    </div>
    <div class="toolbar">
        <input type="text" id="searchInput" placeholder="Search event description, path, or ID..." onkeyup="filterTable()">
        <button class="active" onclick="setKind('all', this)">All Events ({len(timeline)})</button>
        <button onclick="setKind('anomaly', this)">Anomalies Only</button>
        <button onclick="setKind('eventlog', this)">Windows Logs Only</button>
    </div>
    <table>
        <thead>
            <tr>
                <th style="width: 200px;">Timestamp (UTC)</th>
                <th style="width: 140px;">Source</th>
                <th style="width: 120px;">Event ID</th>
                <th>Description</th>
                <th style="width: 100px;">Score</th>
            </tr>
        </thead>
        <tbody id="timelineBody">
            {rows}
        </tbody>
    </table>
    <script>
        let currentKind = 'all';
        function setKind(kind, btn) {{
            currentKind = kind;
            document.querySelectorAll('.toolbar button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            filterTable();
        }}
        function filterTable() {{
            const query = document.getElementById('searchInput').value.toLowerCase();
            const rows = document.querySelectorAll('#timelineBody tr');
            rows.forEach(r => {{
                const text = r.getAttribute('data-text') || '';
                const kind = r.getAttribute('data-kind') || '';
                const matchText = text.includes(query);
                const matchKind = currentKind === 'all' || kind === currentKind;
                r.style.display = (matchText && matchKind) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""

    out_html = os.path.join(REPORT_DIR, "timeline", "timeline.html")
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"[+] Saved HTML timeline to {out_html}")


def export_dashboard(timeline):
    """
    Generates the Executive Case Dashboard HTML report (H-7)
    with top suspicious files, anomaly scores, and system metrics.
    """
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    flagged = pd.read_csv(flagged_path) if os.path.exists(flagged_path) else pd.DataFrame()

    total_events = len(timeline)
    anomaly_events = (timeline["kind"] == "anomaly").sum() if not timeline.empty else 0
    log_events = (timeline["kind"] == "eventlog").sum() if not timeline.empty else 0

    # Top suspicious files table
    suspicious_rows = ""
    if not flagged.empty:
        for idx, row in enumerate(flagged.head(10).itertuples(), 1):
            short_path = str(row.path)
            score_val = float(getattr(row, "anomaly_score", 0.0))
            suspicious_rows += f"""
            <tr>
                <td>#{idx}</td>
                <td><code>{html.escape(short_path)}</code></td>
                <td><span style="color: #f87171; font-weight: bold;">{score_val:.4f}</span></td>
                <td>{detect_category(short_path)}</td>
            </tr>"""

    # Embed chart as base64 data URI if exists for 100% portable offline reporting (H-7)
    chart_path = os.path.join(REPORT_DIR, "anomaly_scores.png")
    chart_elem = "<p style='color:#64748b;'>Score chart not generated.</p>"
    if os.path.exists(chart_path):
        try:
            with open(chart_path, "rb") as cf:
                b64_chart = base64.b64encode(cf.read()).decode("utf-8")
                chart_elem = f'<img src="data:image/png;base64,{b64_chart}" style="max-width:100%; border-radius:8px; border:1px solid #1e293b;">'
        except Exception:
            chart_elem = '<img src="anomaly_scores.png" style="max-width:100%;">'

    dash_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>ForensIQ — Investigation Dashboard</title>
    <style>
        body {{
            background: #04060a;
            color: #dce4e4;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 32px;
        }}
        h1 {{
            color: #00f2ff;
            margin: 0 0 8px;
            font-size: 26px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin: 24px 0;
        }}
        .metric-card {{
            background: #0c121e;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 16px 20px;
        }}
        .metric-card .val {{
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 4px;
        }}
        .metric-card .lbl {{
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .panel {{
            background: #0c121e;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 24px;
        }}
        h2 {{
            color: #7dd3fc;
            font-size: 16px;
            margin: 0 0 16px;
            border-bottom: 1px solid #1e293b;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 9px 12px;
            border-bottom: 1px solid #161f30;
            text-align: left;
        }}
        th {{
            color: #94a3b8;
            background: #080c14;
        }}
        code {{
            color: #38bdf8;
            background: #080c14;
            padding: 2px 5px;
            border-radius: 4px;
        }}
        a.btn {{
            display: inline-block;
            background: #00f2ff;
            color: #000;
            text-decoration: none;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            margin-right: 12px;
        }}
    </style>
</head>
<body>
    <h1>ForensIQ Threat Intelligence Dashboard</h1>
    <div style="color: #64748b; font-size: 13px; margin-bottom: 20px;">Automated Forensic Anomaly & Timeline Analysis</div>

    <div class="metrics-grid">
        <div class="metric-card"><div class="val">{len(flagged):,}</div><div class="lbl">Flagged Anomalies</div></div>
        <div class="metric-card"><div class="val">{log_events:,}</div><div class="lbl">Windows Event Logs</div></div>
        <div class="metric-card"><div class="val">{total_events:,}</div><div class="lbl">Total Timeline Events</div></div>
        <div class="metric-card"><div class="val" style="color:#f87171;">HIGH</div><div class="lbl">Threat Severity</div></div>
    </div>

    <div class="panel">
        <h2>Top Suspicious Files (Isolation Forest Anomaly Rank)</h2>
        <table>
            <thead>
                <tr>
                    <th style="width: 60px;">Rank</th>
                    <th>File Path</th>
                    <th style="width: 120px;">Score</th>
                    <th style="width: 200px;">Assessed Category</th>
                </tr>
            </thead>
            <tbody>
                {suspicious_rows}
            </tbody>
        </table>
    </div>

    <div class="panel">
        <h2>Anomaly Score Distribution</h2>
        {chart_elem}
    </div>

    <div style="margin-top: 24px;">
        <a class="btn" href="timeline/timeline.html">Open Interactive Timeline</a>
        <a class="btn" style="background:#1e293b; color:#fff;" href="forensiq_report.html">View Technical Verification Report</a>
    </div>
</body>
</html>"""

    dash_path = os.path.join(REPORT_DIR, "dashboard.html")
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write(dash_html)
    print(f"[+] Saved Executive Dashboard to {dash_path}")


def export_ui_state(timeline):
    """
    Exports case JSON data (mockState.json) matching the React frontend data contract (Report 3 Step 4).
    """
    flagged_path = os.path.join(FEAT_DIR, "flagged_anomalies.csv")
    flagged = pd.read_csv(flagged_path) if os.path.exists(flagged_path) else pd.DataFrame()

    anomalies_list = []
    if not flagged.empty:
        for idx, row in enumerate(flagged.head(10).itertuples(), 1):
            fpath = str(row.path)
            score_val = float(getattr(row, "anomaly_score", 0.0))
            anomalies_list.append({
                "id": f"ANM-{idx:03d}",
                "path": fpath,
                "score": score_val,
                "size_kb": int(getattr(row, "size", 0) / 1024),
                "severity": "critical" if score_val < -0.1 else "warn",
                "category": detect_category(fpath),
                "description": f"Anomalous file with ML score {score_val:.4f}"
            })

    timeline_list = []
    if not timeline.empty:
        for idx, row in enumerate(timeline.head(15).itertuples(), 1):
            ts = row.timestamp
            ts_str = ts.isoformat() if isinstance(ts, datetime) else str(ts)
            disp_str = ts.strftime("%H:%M:%S UTC") if isinstance(ts, datetime) else ts_str

            timeline_list.append({
                "id": f"EVT-{idx:03d}",
                "timestamp": ts_str,
                "display_time": disp_str,
                "type": "critical" if row.kind == "anomaly" else "info",
                "title": f"[{row.source}] {row.event_id}",
                "description": str(row.description),
                "metadata": {
                    "source": str(row.source),
                    "event_id": str(row.event_id),
                    "score": f"{row.score:.4f}"
                }
            })

    ui_state = {
        "case_id": "FRQ-CASE-2026",
        "analyst": "FORENSIQ-AUTOMATED-SOC",
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": {
            "total_extracted_gb": 4.2,
            "anomalies_flagged": len(flagged),
            "logs_parsed": f"{len(load_all_parsed_events()):,}",
            "scan_duration_sec": 42,
            "risk_score": 85 if len(flagged) > 10 else 40
        },
        "anomalies": anomalies_list,
        "timeline": timeline_list
    }

    ui_state_path = os.path.join(REPORT_DIR, "mockState.json")
    with open(ui_state_path, "w", encoding="utf-8") as f:
        json.dump(ui_state, f, indent=2)
    print(f"[+] Exported UI state contract to {ui_state_path}")


def main():
    print("=" * 65)
    print("      ForensIQ Timeline & Dashboard Generation Engine")
    print("=" * 65)
    timeline = build_timeline()
    if not timeline.empty:
        export_html_timeline(timeline)
        export_dashboard(timeline)
        export_ui_state(timeline)
    print("=" * 65)
    print("      Timeline Generation Complete")
    print("=" * 65)


if __name__ == "__main__":
    main()