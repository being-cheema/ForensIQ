"""
make_multimodel_pdf.py
======================
Builds reports/ForensIQ_MultiModel_Verified_Evaluation.pdf from the output of
multimodel_eval.py (results_main.csv, results_ablation.csv, results.json,
*_tool_output.txt, shap/*.png). Renders HTML through headless Chrome.

Usage:  python make_multimodel_pdf.py
"""

import os
import json
import html
import subprocess
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, "reports", "multimodel_eval")
PDF = os.path.join(BASE, "reports", "ForensIQ_MultiModel_Verified_Evaluation.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

main = pd.read_csv(os.path.join(D, "results_main.csv"))
abl = pd.read_csv(os.path.join(D, "results_ablation.csv"))
res = json.load(open(os.path.join(D, "results.json")))
MODELS = ["Isolation Forest", "Local Outlier Factor", "One-Class SVM"]


def pct(x, d=1):
    return f"{float(x) * 100 + 1e-9:.{d}f}%"


def table(header, rows, cls=""):
    h = "".join(f"<th>{html.escape(str(c))}</th>" for c in header)
    b = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table class='{cls}'><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


def best(rows_for_image):
    top = max(float(r["target_recall"]) for r in rows_for_image)
    return top


# ---- main table
rows = []
for img, g in main.groupby("image", sort=False):
    top = best(g.to_dict("records"))
    for i, r in enumerate(g.to_dict("records")):
        m = f"<b>{r['model']}</b>" if float(r["target_recall"]) == top else r["model"]
        rows.append([f"<b>{img}</b><br><small>{int(r['files']):,} files, K={int(r['K']):,}</small>" if i == 0 else "",
                     m, r["targets"], pct(r["target_recall"]), pct(r["file_recall"]),
                     pct(r["accuracy"], 2), pct(r["precision"], 2), pct(r["f1"], 2)])
t_main = table(["Image", "Model", "Targets caught", "Target recall", "File recall",
                "Accuracy", "Precision", "F1"], rows)

# ---- budgets
rows = [[r["image"].split(":")[0], r["model"], pct(r["target_recall"]), pct(r["recall_at_5.5pct"]), pct(r["recall_at_10pct"])]
        for r in main.to_dict("records")]
t_budget = table(["Image", "Model", "5%", "5.5%", "10%"], rows)

# ---- verdicts
rows = []
for r in main.to_dict("records"):
    rows.append([r["image"].split(":")[0], r["model"], r["timestomping"], r["insider"]])
t_verd = table(["Image", "Model", "Timestomping", "Insider attack"], rows)


# ---- ablation
def abl_table(img_key):
    a = abl[abl["image"].str.startswith(img_key)]
    cfgs = list(dict.fromkeys(a["config"]))
    out = []
    for c in cfgs:
        s = a[a["config"] == c]
        cells = [c, int(s["n_features"].iloc[0])]
        for m in MODELS:
            x = s[s["model"] == m]
            cells.append(x["targets"].iloc[0] if len(x) else "-")
        out.append(cells)
    return table(["Feature set", "n", "Isolation Forest", "LOF", "One-Class SVM"], out)


def shap_active():
    rows = []
    for tag, v in res["results"].items():
        for m in MODELS:
            s = v["models"][m]["shap"]
            if s:
                rows.append([v["label"].split(":")[0], m, f"{s['active_features']} / {s['n_features']}"])
    return table(["Image", "Model", "Features with non-zero SHAP"], rows)


def img(path, cap):
    p = os.path.join(D, "shap", path)
    return f"<figure><img src='file://{p}'><figcaption>{cap}</figcaption></figure>" if os.path.exists(p) else ""


def tool_excerpt(tag, n=62):
    p = os.path.join(D, f"{tag}_tool_output.txt")
    return "<pre>" + html.escape("\n".join(open(p, encoding="utf-8").read().splitlines()[:n])) + "</pre>"


skipped = "".join(f"<li><b>{html.escape(k)}</b>: extracted artifacts not available for this image</li>"
                  for k in res.get("skipped", {}))
feat_n = {v["label"].split(":")[0]: len(v["features"]) for v in res["results"].values()}

doc = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page {{ size: A4; margin: 16mm 14mm; }}
body {{ font: 10.5pt/1.45 -apple-system, Helvetica, Arial, sans-serif; color:#111; }}
h1 {{ font-size: 20pt; margin: 0 0 4px; }} h2 {{ font-size: 13.5pt; margin: 20px 0 6px; border-bottom:1px solid #ccc; padding-bottom:3px; }}
table {{ border-collapse: collapse; width:100%; font-size: 9pt; margin: 6px 0 10px; }}
th,td {{ border:1px solid #bbb; padding:3px 6px; text-align:left; vertical-align:top; }}
th {{ background:#eef2f7; }} small {{ color:#555; }}
pre {{ background:#0e1116; color:#d6e2f0; font: 7.4pt/1.3 Menlo, monospace; padding:8px; border-radius:4px; white-space:pre-wrap; }}
figure {{ margin:6px 0; page-break-inside:avoid; }} img {{ width:100%; max-width:430px; }} figcaption {{ font-size:8.5pt; color:#444; }}
.row {{ display:flex; gap:10px; }} .row figure {{ flex:1; }} .pb {{ page-break-before: always; }}
</style></head><body>
<h1>ForensIQ Multi-Model Evaluation</h1>
<div><small>Isolation Forest vs. Local Outlier Factor vs. One-Class SVM, equal review budget (top 5% of files).
All values computed by <code>multimodel_eval.py</code> from the extracted artifacts.</small></div>

<h2>1. Scope</h2>
<ul>
<li>Images evaluated: Image 1 (XP Hacking, 11,773 files) and Image 2 (Win7 Data Leakage, 85,017 files).</li>
<li>Features per file: {', '.join(f'{k}: {v}' for k, v in feat_n.items())} of the 23-feature design. <code>delta_si_fn</code> requires $FILE_NAME timestamps that the stored MFT data does not contain, so it is excluded.</li>
{skipped and '<li>Not evaluated:</li><ul>' + skipped + '</ul>'}
<li>One-Class SVM is trained on a 10,000-file random subsample and scores every file; LOF uses 20 neighbours.</li>
<li>A target is "caught" when any of its files is in the flagged set. Image 1 has 7 target families (15 files); Image 2 has 19 targets (38 files).</li>
</ul>

<h2>2. Results at the 5% review budget</h2>
{t_main}
<p><small>Accuracy is about 95% for every model because the budget is fixed at 5% and targets are rare; recall, precision and F1 are the discriminating metrics.</small></p>
<h2>3. Recall at larger budgets</h2>
{t_budget}

<h2>4. Timestomping and insider attack</h2>
{t_verd}
<p><small>Timestomping = a ground-truth timestomped file is flagged (Image 1: NMEM/NGETTIME; Image 2: Eraser.exe). Insider attack = at least half of the insider targets flagged (partial at 25-50%); not applicable to the external intrusion in Image 1.</small></p>

<div class='pb'></div>
<h2>5. Ablation, Image 2 (targets caught of 19)</h2>
{abl_table('Image 2')}
<h2>6. Ablation, Image 1 (targets caught of 7)</h2>
{abl_table('Image 1')}

<div class='pb'></div>
<h2>7. SHAP explanations</h2>
{shap_active()}
<p><small>Isolation Forest: TreeSHAP over a 20,000-file sample plus caught targets. LOF and One-Class SVM: KernelSHAP on caught targets only (not directly comparable).</small></p>
<div class='row'>{img('img2_Isolation_Forest_shap_bar.png', 'Image 2 - Isolation Forest')}{img('img2_One-Class_SVM_shap_bar.png', 'Image 2 - One-Class SVM')}</div>
<div class='row'>{img('img1_Isolation_Forest_shap_bar.png', 'Image 1 - Isolation Forest')}{img('img2_Local_Outlier_Factor_shap_bar.png', 'Image 2 - LOF')}</div>

<div class='pb'></div>
<h2>8. Tool output - Image 2 (Win7 Data Leakage)</h2>
{tool_excerpt('img2', 70)}
<h2>9. Tool output - Image 1 (XP Hacking)</h2>
{tool_excerpt('img1', 70)}
</body></html>"""

html_path = os.path.join(D, "report.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(doc)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={PDF}", f"file://{html_path}"], check=True, capture_output=True)
print("[+] wrote", PDF)
