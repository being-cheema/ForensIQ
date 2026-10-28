"""
make_multimodel_pdf.py
======================
Builds reports/multimodel_eval/multimodel_eval.md and
reports/ForensIQ_MultiModel_Verified_Evaluation.pdf from the output of
multimodel_eval.py and robustness_check.py (results_main.csv, results_ablation.csv,
results.json, robustness.json, *_tool_output.txt, shap/*.png). Renders HTML through
headless Chrome.

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
rob_path = os.path.join(D, "robustness.json")
rob = json.load(open(rob_path)) if os.path.exists(rob_path) else {}
MODELS = ["Isolation Forest", "Local Outlier Factor", "One-Class SVM"]
SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OC-SVM"}
TAGS = {v["label"].split(":")[0]: t for t, v in res["results"].items()}  # "Image 1" -> "img1"

TARGET_SOURCES = {
    "img1": "7 target families (15 files) reconstructed from the SCHARDT case notes",
    "img2": "19 targets (38 files) from the repository's CFReDS ground-truth list",
    "img3": "12 targets (558 files, all copies counted) taken from a published third-party "
            "analysis of the case; the official answer key is access-restricted, so treat these as unofficial",
}


def pct(x, d=1):
    return f"{float(x) * 100 + 1e-9:.{d}f}%"


def constant_features():
    out = {}
    for tag in res["results"]:
        p = os.path.join(BASE, "runs", tag, "features", "macb_features.csv")
        if os.path.exists(p):
            df = pd.read_csv(p)
            out[tag] = [c for c in df.columns if c != "path" and df[c].nunique() <= 1]
    return out


CONST = constant_features()
n_feat = {t: len(v["features"]) for t, v in res["results"].items()}


# ---------------------------------------------------------------- tables (as row lists)
def main_rows():
    rows = []
    for img, g in main.groupby("image", sort=False):
        recs = g.to_dict("records")
        top = max(float(r["target_recall"]) for r in recs)
        for i, r in enumerate(recs):
            rows.append([f"{img} ({int(r['files']):,} files, K={int(r['K']):,})" if i == 0 else "",
                         r["model"], r["targets"], pct(r["target_recall"]), pct(r["file_recall"]),
                         pct(r["accuracy"], 2), pct(r["precision"], 2), pct(r["f1"], 2),
                         float(r["target_recall"]) == top])
    return rows


def budget_rows():
    return [[r["image"].split(":")[0], r["model"], pct(r["target_recall"]), pct(r["recall_at_5.5pct"]),
             pct(r["recall_at_10pct"])] for r in main.to_dict("records")]


def verdict_rows():
    rows = []
    for t, v in res["results"].items():
        for m in MODELS:
            x = v["models"][m]["verdicts"]
            si = x.get("si_fn_mismatch_flagged")
            rows.append([v["label"].split(":")[0], m, x["timestomp"], x["known_ts_hit"] and ", ".join(x["known_ts_hit"]) or "-",
                         si if si is not None else "-", x["insider"]])
    return rows


def abl_rows(img_key):
    a = abl[abl["image"].str.startswith(img_key)]
    out = []
    for c in dict.fromkeys(a["config"]):
        s = a[a["config"] == c]
        cells = [c, int(s["n_features"].iloc[0])]
        for m in MODELS:
            x = s[s["model"] == m]
            cells.append(x["targets"].iloc[0] if len(x) else "-")
        out.append(cells)
    return out


def shap_rows():
    rows = []
    for t, v in res["results"].items():
        for m in MODELS:
            s = v["models"][m]["shap"]
            if s:
                top = sorted(s["mean_abs"].items(), key=lambda a: -a[1])[:3]
                rows.append([v["label"].split(":")[0], m, f"{s['active_features']} / {s['n_features']}",
                             ", ".join(f"{k} {x:.2f}" for k, x in top)])
    return rows


def robust_rows():
    rows = []
    for t, r in rob.items():
        lab = res["results"][t]["label"].split(":")[0]
        lof = ", ".join(f"k={k}: {v}" for k, v in r["lof"].items())
        svm = "; ".join(f"n={n}: {min(v)}-{max(v)}" for n, v in r["ocsvm"].items())
        rows.append([lab, f"{r['targets']}", lof, svm, f"{min(r['iforest_seeds'])}-{max(r['iforest_seeds'])}",
                     f"{r['unique_rows']:,} / {r['rows']:,}"])
    return rows


# ---------------------------------------------------------------- renderers
def md_table(header, rows):
    esc = lambda c: str(c).replace("|", "\\|")
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(":---" for _ in header) + "|"]
    out += ["| " + " | ".join(esc(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def html_table(header, rows, bold_last=False):
    h = "".join(f"<th>{html.escape(str(c))}</th>" for c in header)
    b = ""
    for r in rows:
        bold = bold_last and r[-1] is True
        cells = r[:-1] if bold_last else r
        tds = "".join(f"<td>{('<b>' + html.escape(str(c)) + '</b>') if bold else html.escape(str(c))}</td>" for c in cells)
        b += f"<tr>{tds}</tr>"
    return f"<table><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"


MAIN_H = ["Image", "Model", "Targets caught", "Target recall", "File recall", "Accuracy", "Precision", "F1"]
BUD_H = ["Image", "Model", "5%", "5.5%", "10%"]
VERD_H = ["Image", "Model", "Timestomping", "Known timestomped file flagged", "SI/FN mismatches in flagged set", "Insider attack"]
ABL_H = ["Feature set", "n", "Isolation Forest", "LOF", "One-Class SVM"]
SHAP_H = ["Image", "Model", "Features with non-zero SHAP", "Top mean |SHAP|"]
ROB_H = ["Image", "Targets", "LOF by neighbours (targets caught)", "One-Class SVM by subsample (min-max over 5 seeds)",
         "Isolation Forest (5 seeds)", "Unique rows"]

# overall winner by mean target recall across evaluated images
mean_rec = main.assign(r=main["target_recall"].astype(float)).groupby("model")["r"].mean().reindex(MODELS)
ranking = ", ".join(f"{SHORT[m]} {pct(mean_rec[m])}" for m in mean_rec.sort_values(ascending=False).index)
evaluated = ", ".join(res["results"][t]["label"].split(":")[0] for t in res["results"])
const_note = "; ".join(f"{res['results'][t]['label'].split(':')[0]}: {len(c)} of {n_feat[t]} features constant ({', '.join(c)})"
                       for t, c in CONST.items())
skipped = list(res.get("skipped", {}))

scope_items = [
    f"Images evaluated: {evaluated}.",
    "Every image was re-extracted from its raw disk image (NIST CFReDS Hacking Case, NIST CFReDS Data Leakage Case, "
    "Digital Corpora 2018 Lone Wolf), with `$FILE_NAME` timestamps read from the MFT so that `delta_si_fn` is computed.",
    "Targets: " + " | ".join(f"{res['results'][t]['label'].split(':')[0]}: {TARGET_SOURCES.get(t, '')}" for t in res["results"]) + ".",
    "A target counts as caught when any of its files is in the flagged set. Same review budget for every model: the top 5% of files.",
    "One-Class SVM is trained on a 10,000-file random subsample (RBF kernel is O(n^2)) and scores every file; LOF uses 20 neighbours; Isolation Forest 200 trees.",
    "`after_hours_touch` uses UTC hours 08:00-18:00; the image's own time zone is not applied.",
    f"Constant features: {const_note}. The model therefore works with fewer than 23 active features per image.",
]
if skipped:
    scope_items.append("Not evaluated: " + ", ".join(skipped) + ".")


# ---------------------------------------------------------------- markdown
def write_md():
    L = ["# ForensIQ Multi-Model Benchmark (Isolation Forest vs. LOF vs. One-Class SVM, 23-feature baseline)", "",
         "All numbers are produced by `multimodel_eval.py` and `robustness_check.py` from artifacts extracted "
         "directly from the raw disk images.", "", "## 1. Scope and limits", ""]
    L += [f"- {s}" for s in scope_items]
    L += ["", "## 2. Results at the 5% review budget", "",
          md_table(MAIN_H, [r[:-1] for r in main_rows()]), "",
          "Accuracy is about 95% for every model because the budget is fixed at 5% and targets are rare; "
          "recall, precision and F1 are the discriminating metrics.", "",
          f"Mean target recall across images: {ranking}.", "",
          "## 3. Recall at larger budgets", "", md_table(BUD_H, budget_rows()), "",
          "## 4. Timestomping and insider attack", "", md_table(VERD_H, verdict_rows()), "",
          "Timestomping is YES when a ground-truth timestomped file is in the flagged set (Image 1: NMEM/NGETTIME; "
          "Image 2: Eraser.exe), otherwise UNVERIFIED because no ground-truth timestomped file is defined. "
          "The `$STANDARD_INFORMATION` vs `$FILE_NAME` mismatch count is a hint, not proof, because ordinary file operations also cause mismatches. "
          "`future_m` is always zero because its reference time is the newest timestamp in the image. "
          "Insider attack is CONFIRMED when at least half of the targets are flagged, PARTIAL at 25-50%; "
          "it is not applicable to the external intrusion in Image 1.", ""]
    for img in TAGS:
        L += [f"## 5. Ablation, {img} (targets caught)", "", md_table(ABL_H, abl_rows(img)), ""]
    L += ["## 6. SHAP", "", md_table(SHAP_H, shap_rows()), "",
          "Isolation Forest: TreeSHAP over a 20,000-file sample plus caught targets. LOF and One-Class SVM: KernelSHAP "
          "on caught targets only, so their importances are not directly comparable. SHAP explains why a file ranked high; "
          "it does not by itself establish intent.", ""]
    if rob:
        L += ["## 7. Robustness", "", md_table(ROB_H, robust_rows()), "",
              "LOF is the weakest model at every neighbour setting tried and is very sensitive to it; duplicate rows distort it.", ""]
    L += ["## 8. Which model performs best", "",
          f"Mean target recall: {ranking}. The ranking is the same on every evaluated image where the targets are defined from the case record; "
          "Image 3 uses unofficial targets, so its figures are indicative only.", "",
          "## Tool output", "", "CLI-style detections per image: " + ", ".join(f"`{t}_tool_output.txt`" for t in res["results"]) + "."]
    with open(os.path.join(D, "multimodel_eval.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ---------------------------------------------------------------- pdf
def img(path, cap):
    p = os.path.join(D, "shap", path)
    return f"<figure><img src='file://{p}'><figcaption>{cap}</figcaption></figure>" if os.path.exists(p) else ""


def tool_excerpt(tag, n):
    p = os.path.join(D, f"{tag}_tool_output.txt")
    return "<pre>" + html.escape("\n".join(open(p, encoding="utf-8").read().splitlines()[:n])) + "</pre>"


def write_pdf():
    scope_html = "".join(f"<li>{html.escape(s).replace('`', '')}</li>" for s in scope_items)
    abl_html = "".join(f"<h2>{5 + i}. Ablation, {img_} (targets caught)</h2>{html_table(ABL_H, abl_rows(img_))}"
                       for i, img_ in enumerate(TAGS))
    n0 = 5 + len(TAGS)
    rob_html = f"<h2>{n0 + 1}. Robustness</h2>{html_table(ROB_H, robust_rows())}" if rob else ""
    tool_html = "".join(f"<h2>Tool output - {res['results'][t]['label']}</h2>{tool_excerpt(t, 62)}" for t in res["results"])
    figs = "".join([img(f"{t}_{m.replace(' ', '_')}_shap_bar.png", f"{res['results'][t]['label'].split(':')[0]} - {m}")
                    for t in res["results"] for m in ("Isolation Forest", "One-Class SVM")])
    doc = f"""<!doctype html><html><head><meta charset='utf-8'><style>
@page {{ size: A4; margin: 16mm 14mm; }}
body {{ font: 10.5pt/1.45 -apple-system, Helvetica, Arial, sans-serif; color:#111; }}
h1 {{ font-size: 20pt; margin: 0 0 4px; }} h2 {{ font-size: 13.5pt; margin: 20px 0 6px; border-bottom:1px solid #ccc; padding-bottom:3px; }}
table {{ border-collapse: collapse; width:100%; font-size: 8.6pt; margin: 6px 0 10px; }}
th,td {{ border:1px solid #bbb; padding:3px 6px; text-align:left; vertical-align:top; }}
th {{ background:#eef2f7; }} small {{ color:#555; }}
pre {{ background:#0e1116; color:#d6e2f0; font: 7.2pt/1.3 Menlo, monospace; padding:8px; border-radius:4px; white-space:pre-wrap; }}
figure {{ margin:6px 0; page-break-inside:avoid; }} img {{ width:100%; max-width:380px; }} figcaption {{ font-size:8.5pt; color:#444; }}
.grid {{ display:grid; grid-template-columns: 1fr 1fr; gap:6px; }} .pb {{ page-break-before: always; }}
</style></head><body>
<h1>ForensIQ Multi-Model Evaluation</h1>
<div><small>Isolation Forest vs. Local Outlier Factor vs. One-Class SVM on the 23-feature baseline, equal review budget (top 5% of files).
All values computed by <code>multimodel_eval.py</code> from artifacts extracted from the raw disk images.</small></div>
<h2>1. Scope and limits</h2><ul>{scope_html}</ul>
<h2>2. Results at the 5% review budget</h2>{html_table(MAIN_H + [''], main_rows(), bold_last=True).replace('<th></th>', '')}
<p><small>Accuracy is about 95% for every model because the budget is fixed at 5% and targets are rare; recall, precision and F1 separate the models. Mean target recall: {html.escape(ranking)}.</small></p>
<h2>3. Recall at larger budgets</h2>{html_table(BUD_H, budget_rows())}
<h2>4. Timestomping and insider attack</h2>{html_table(VERD_H, verdict_rows())}
<p><small>Timestomping is YES when a ground-truth timestomped file is flagged (Image 1: NMEM/NGETTIME; Image 2: Eraser.exe), otherwise UNVERIFIED. The SI/FN mismatch count is a hint, not proof. Insider attack: at least half of the targets flagged (partial at 25-50%); not applicable to the external intrusion in Image 1.</small></p>
<div class='pb'></div>{abl_html}{rob_html}
<div class='pb'></div><h2>SHAP explanations</h2>{html_table(SHAP_H, shap_rows())}
<p><small>Isolation Forest: TreeSHAP over a 20,000-file sample plus caught targets. LOF and One-Class SVM: KernelSHAP on caught targets only (not directly comparable). SHAP explains why a file ranked high; it does not by itself establish intent.</small></p>
<div class='grid'>{figs}</div>
<div class='pb'></div>{tool_html}
</body></html>"""
    path = os.path.join(D, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={PDF}", f"file://{path}"], check=True, capture_output=True)


write_md()
write_pdf()
print("[+] wrote", os.path.join(D, "multimodel_eval.md"), "and", PDF)
