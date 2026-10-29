"""study_v3_paper_stats.py: evidence gaps for the article (error rates with uncertainty, rank metrics,
model comparison tests, runtime). Final feature set only.

    FORENSIQ_FEATURE_SET=final .venv/bin/python study_v3_paper_stats.py

Writes reports/study_v3/final/P/stats.json and stats.md. Ground truth is used only to score rankings.
Definitions
  * K = round(budget/100 * N) files reviewed (same rule as study_v3_common.curve).
  * Target-level recall = targets with any file in the top K / targets (n = 7 / 19 / 34; 60 pooled).
    Seed-mean recall uses the mean caught over the 5 seeds with a Wilson 95% interval (n = targets);
    worst seed uses the minimum caught over seeds.
  * File-level precision = target files in the top K / K ("target files" = every file matching any target pattern).
    False alarms = K - target files caught; false-alarm rate = false alarms / non-target files; miss rate = 1 - recall.
  * AUC-ROC / average precision / R-precision are file-level, positives = all target files, per seed.
"""
import os, sys, json, time, subprocess, platform, warnings
import numpy as np

import multimodel_eval as M
import study_v3_common as C

warnings.filterwarnings("ignore")
assert M.FEATURE_SET == "final", "run with FORENSIQ_FEATURE_SET=final"
from scipy.stats import wilcoxon
from sklearn.metrics import roc_auc_score, average_precision_score

OUTD = os.path.join(C.OUT, "P")
MODELS = M.MODELS
SHORT = {"Isolation Forest": "IF", "Local Outlier Factor": "LOF", "One-Class SVM": "OC-SVM"}
BUD = [15, 20]
RNG_SEED = 20260101


def wilson(k, n, z=1.959964):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [float(max(0.0, c - h)), float(min(1.0, c + h))]


def ms(x):
    x = np.asarray(x, float)
    return {"mean": float(x.mean()), "sd": float(x.std(ddof=1)) if len(x) > 1 else 0.0}


def sysq(*a):
    try:
        return subprocess.check_output(["sysctl", "-n", *a], text=True).strip()
    except Exception:
        return None


def artifact_counts(tag):
    art = os.path.join(M.BASE_DIR, "runs", tag, "artifacts")
    out = {}
    recs = json.load(open(os.path.join(art, "mft", "mft_records.json"), encoding="utf-8"))
    out["mft_records_total"] = len(recs)
    out["mft_records_files"] = sum(1 for r in recs if r.get("type") == "file")
    pf = [f for f in os.listdir(os.path.join(art, "prefetch")) if f.lower().endswith(".pf")]
    out["prefetch_pf_files"] = len(pf)
    ev = [f for f in os.listdir(os.path.join(art, "evtx")) if f.lower().endswith((".evtx", ".evt"))]
    out["evtx_log_files"] = len(ev)
    pe = os.path.join(art, "evtx", "parsed_events.json")
    if os.path.exists(pe):
        d = json.load(open(pe, encoding="utf-8"))
        out["parsed_events"] = len(d) if hasattr(d, "__len__") else None
    reg = os.path.join(art, "registry")
    out["registry_hives"] = len([f for f in os.listdir(reg) if os.path.isfile(os.path.join(reg, f)) and not f.startswith(".")])
    out["registry_hive_names"] = sorted(f for f in os.listdir(reg) if os.path.isfile(os.path.join(reg, f)))
    return out


def main():
    t_start = time.time()
    R = {"feature_set": M.FEATURE_SET, "seeds": C.SEEDS, "budgets_pct": BUD}
    Ds = {t: C.load(t) for t in C.DISKS}
    cols = {t: Ds[t]["feats"] for t in C.DISKS}
    R["n_features"] = len(cols["img1"])
    R["features"] = cols["img1"]

    # ---------------- scores: disk x model x seed -> first rank per target, file-level rank metrics
    fr = {}       # (disk, model) -> array seeds x targets (best rank, 1-based)
    rank_m = {}   # (disk, model) -> list over seeds of {auc, ap, rprec}
    tgt_files = {}
    for t in C.DISKS:
        D = Ds[t]
        y = np.zeros(D["N"], dtype=bool)
        y[list(D["all_idx"])] = True
        tgt_files[t] = y
        for m in MODELS:
            seeds = [42] if m == "Local Outlier Factor" else C.SEEDS     # LOF has no random component
            rows, rm = [], []
            for sd in C.SEEDS if m != "Local Outlier Factor" else [42]:
                s = C.score(D, m, cols[t], sd)
                rows.append(C.first_rank(D, s))
                order = np.argsort(-s, kind="stable")
                R_ = int(y.sum())
                rm.append({"auc": float(roc_auc_score(y, s)), "ap": float(average_precision_score(y, s)),
                           "rprec": float(y[order[:R_]].sum() / R_),
                           "tgt_file_top": {str(b): int(y[order[:int(round(b / 100 * D['N']))]].sum()) for b in BUD}})
            if m == "Local Outlier Factor":   # deterministic: replicate over the 5 seeds for uniform tables
                rows, rm = rows * len(C.SEEDS), rm * len(C.SEEDS)
            fr[(t, m)] = np.array(rows)
            rank_m[(t, m)] = rm
            print(t, SHORT[m], "done", f"{time.time() - t_start:.0f}s", flush=True)

    # ---------------- (a) error rates
    A = {}
    pooled = {SHORT[m]: {str(b): {"caught_per_seed": np.zeros(len(C.SEEDS)), "tf": np.zeros(len(C.SEEDS)),
                                  "K": 0, "T": 0, "nontarget": 0} for b in BUD} for m in MODELS}
    for t in C.DISKS:
        D = Ds[t]
        N, T, GT = D["N"], len(D["active"]), int(tgt_files[t].sum())
        for m in MODELS:
            e = {}
            for b in BUD:
                K = int(round(b / 100 * N))
                F = fr[(t, m)]
                caught = (F <= K).sum(1)                       # per seed
                tf = np.array([x["tgt_file_top"][str(b)] for x in rank_m[(t, m)]], float)
                fa = K - tf
                e[str(b)] = {
                    "K": K, "targets": T, "target_files": GT,
                    "caught_per_seed": caught.tolist(),
                    "recall_seedmean": float(caught.mean() / T),
                    "recall_seedmean_wilson95": wilson(float(caught.mean()), T),
                    "recall_worst": float(caught.min() / T),
                    "recall_worst_wilson95": wilson(int(caught.min()), T),
                    "miss_rate_seedmean": float(1 - caught.mean() / T),
                    "file_precision": ms(tf / K), "target_files_caught": ms(tf),
                    "false_alarms": ms(fa), "false_alarm_rate": ms(fa / (N - GT)),
                }
                P = pooled[SHORT[m]][str(b)]
                P["caught_per_seed"] += caught
                P["tf"] += tf
                P["K"] += K
                P["T"] += T
                P["nontarget"] += N - GT
            A.setdefault(t, {})[SHORT[m]] = e
    Ap = {}
    for m in MODELS:
        Ap[SHORT[m]] = {}
        for b in BUD:
            P = pooled[SHORT[m]][str(b)]
            c, T = P["caught_per_seed"], P["T"]
            fa = P["K"] - P["tf"]
            Ap[SHORT[m]][str(b)] = {
                "targets": T, "K_total": P["K"],
                "recall_seedmean": float(c.mean() / T), "recall_seedmean_wilson95": wilson(float(c.mean()), T),
                "recall_worst": float(c.min() / T), "recall_worst_wilson95": wilson(int(c.min()), T),
                "miss_rate_seedmean": float(1 - c.mean() / T),
                "file_precision": ms(P["tf"] / P["K"]), "false_alarms": ms(fa),
                "false_alarm_rate": ms(fa / P["nontarget"]),
                "note": "pooled over the 3 disks (micro): sums of counts; Wilson treats the 60 targets as independent",
            }
    R["error_rates"] = {"per_disk": A, "pooled": Ap}

    # per-target table, IF seed-mean best rank
    pt = {}
    for t in C.DISKS:
        D, F = Ds[t], fr[(t, "Isolation Forest")]
        mean_r, N = F.mean(0), D["N"]
        rows = []
        for j, tg in enumerate(D["active"]):
            rows.append({"target": tg["name"], "n_files": len(tg["idx"]), "best_rank_mean": float(mean_r[j]),
                         "best_rank_sd": float(F[:, j].std(ddof=1)), "best_rank_worst_seed": int(F[:, j].max()),
                         "percentile_mean": float(100 * mean_r[j] / N),
                         "percentile_worst_seed": float(100 * F[:, j].max() / N),
                         "outside_15pct": bool(mean_r[j] > round(0.15 * N)),
                         "outside_20pct": bool(mean_r[j] > round(0.20 * N))})
        rk = sorted(range(len(rows)), key=lambda i: -rows[i]["percentile_mean"])
        for rank, i in enumerate(rk, 1):
            rows[i]["hardness_rank_in_disk"] = rank
        pt[t] = rows
    allrows = [dict(r, disk=t) for t in C.DISKS for r in pt[t]]
    hardest = sorted(allrows, key=lambda r: -r["percentile_mean"])[:10]
    R["per_target_IF"] = {"disks": pt, "hardest10_pooled": hardest,
                          "flag_rule": "hardest = the 10 largest seed-mean rank percentiles over the 60 targets; outside_15/20pct = seed-mean best rank beyond the budget"}

    # ---------------- (b) rank metrics
    B = {}
    for t in C.DISKS:
        B[t] = {}
        for m in MODELS:
            rm = rank_m[(t, m)]
            B[t][SHORT[m]] = {k: ms([x[k] for x in rm]) for k in ("auc", "ap", "rprec")}
            B[t][SHORT[m]]["positives_files"] = int(tgt_files[t].sum())
            B[t][SHORT[m]]["prevalence"] = float(tgt_files[t].mean())
    R["rank_metrics"] = {"per_disk": B, "note": "file-level; positives = all files matching a target pattern; "
                         "LOF is deterministic so its sd is 0; R-precision = share of positives in the top R (R = #positives)"}

    # ---------------- (c) model comparison and bootstrap
    pct = {}
    for m in MODELS:
        pct[m] = np.concatenate([100 * fr[(t, m)].mean(0) / Ds[t]["N"] for t in C.DISKS])   # seed-mean best-rank percentile
    cmp_ = {}
    for other in ("One-Class SVM", "Local Outlier Factor"):
        a, b_ = pct["Isolation Forest"], pct[other]
        d = a - b_
        nz = int((d != 0).sum())
        w = wilcoxon(a, b_, alternative="less", zero_method="wilcox")
        cmp_[f"IF_vs_{SHORT[other]}"] = {
            "test": "one-sided Wilcoxon signed-rank, H1: IF best-rank percentile < other (IF ranks the target higher)",
            "n_targets": int(len(a)), "n_nonzero_pairs": nz, "statistic_W": float(w.statistic), "p_value": float(w.pvalue),
            "median_percentile_IF": float(np.median(a)), f"median_percentile_{SHORT[other]}": float(np.median(b_)),
            "median_paired_diff_pct_points": float(np.median(d)),
            "targets_IF_better": int((d < 0).sum()), "targets_other_better": int((d > 0).sum()), "ties": int((d == 0).sum()),
            "per_disk": {}}
        off = 0
        for t in C.DISKS:
            n_t = len(Ds[t]["active"])
            aa, bb = a[off:off + n_t], b_[off:off + n_t]
            off += n_t
            try:
                ww = wilcoxon(aa, bb, alternative="less", zero_method="wilcox")
                cmp_[f"IF_vs_{SHORT[other]}"]["per_disk"][t] = {"n": n_t, "W": float(ww.statistic), "p": float(ww.pvalue)}
            except Exception as ex:
                cmp_[f"IF_vs_{SHORT[other]}"]["per_disk"][t] = {"n": n_t, "error": str(ex)}
    rng = np.random.RandomState(RNG_SEED)
    boot = {}
    for m in MODELS:
        # per-target hit indicator at 20%, averaged over seeds, then resample targets
        ind = np.concatenate([(fr[(t, m)] <= int(round(0.20 * Ds[t]["N"]))).mean(0) for t in C.DISKS])
        bs = np.array([ind[rng.randint(0, len(ind), len(ind))].mean() for _ in range(2000)])
        boot[SHORT[m]] = {"pooled": {"recall20": float(ind.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]},
                          "per_disk": {}}
        off = 0
        for t in C.DISKS:
            n_t = len(Ds[t]["active"])
            x = ind[off:off + n_t]
            off += n_t
            bs = np.array([x[rng.randint(0, n_t, n_t)].mean() for _ in range(2000)])
            boot[SHORT[m]]["per_disk"][t] = {"recall20": float(x.mean()), "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    R["model_comparison"] = {"wilcoxon": cmp_, "bootstrap_recall20": boot,
                             "bootstrap_spec": {"resamples": 2000, "unit": "target", "rng_seed": RNG_SEED,
                                                "statistic": "mean over targets of (fraction of seeds in which the target is in the top 20%)"},
                             "note": "percentile = seed-mean best rank / N; the 60 targets are pooled across disks, so disk difficulty is shared; "
                                     "targets within a disk are not independent of each other (same model fit)"}

    # ---------------- (d) runtime and counts
    import shap
    from sklearn.ensemble import IsolationForest
    RT = {"machine": {"cpu": sysq("machdep.cpu.brand_string"), "ram_bytes": int(sysq("hw.memsize")),
                      "ram_gb": round(int(sysq("hw.memsize")) / 2 ** 30, 1), "logical_cpus": sysq("hw.logicalcpu"),
                      "os": platform.platform(), "python": sys.version.split()[0]}}
    import sklearn
    RT["machine"]["sklearn"], RT["machine"]["shap"] = sklearn.__version__, shap.__version__
    RT["runs"] = 3
    RT["per_disk"] = {}
    for t in C.DISKS:
        spec = M.IMAGES[t]
        tb, tf_, tsh = [], [], []
        for _ in range(3):
            t0 = time.perf_counter()
            df, raw, feats = M.build_features(spec["art_dir"], t)
            tb.append(time.perf_counter() - t0)
        D = Ds[t]
        for _ in range(3):
            t0 = time.perf_counter()
            Xs = C.matrix(D, cols[t])
            s, fm = M.fit_score("Isolation Forest", Xs, 42)
            tf_.append(time.perf_counter() - t0)
        K = int(round(0.20 * D["N"]))
        flagged = np.argsort(-s, kind="stable")[:K]
        samp = np.random.RandomState(0).choice(flagged, min(1000, K), replace=False)
        expl = shap.TreeExplainer(fm)
        for _ in range(3):
            t0 = time.perf_counter()
            expl.shap_values(Xs[samp])
            tsh.append(time.perf_counter() - t0)
        RT["per_disk"][t] = {
            "files": int(D["N"]), "flagged_20pct": K, "build_features_s": ms(tb), "build_features_runs": tb,
            "if_fit_score_s": ms(tf_), "if_fit_score_runs": tf_,
            "shap_s_per_1000_flagged": ms(tsh), "shap_sample_rows": int(len(samp)),
            "shap_s_for_all_flagged_est": float(np.mean(tsh) / len(samp) * K),
            "artifacts": artifact_counts(t)}
        print(t, "runtime done", f"{time.time() - t_start:.0f}s", flush=True)
    RT["note"] = "feature building = multimodel_eval.build_features (final set incl. burst) from runs/imgN/artifacts, JSON already extracted; " \
                 "IF = standardise + fit (200 trees, sample 256, n_jobs=-1) + score all rows; SHAP = TreeSHAP on 1000 random flagged files (top 20%)"
    R["runtime"] = RT
    R["total_script_s"] = time.time() - t_start

    os.makedirs(OUTD, exist_ok=True)
    json.dump(R, open(os.path.join(OUTD, "stats.json"), "w"), indent=1)
    write_md(R)
    print("written", OUTD)


def pc(x):
    return f"{100 * x:.1f}"


def write_md(R):
    L = ["# Paper statistics (final feature set, 19 features)", "",
         "Produced by `study_v3_paper_stats.py`. Seeds 42, 1337, 9999, 7, 2024 (LOF is deterministic: one fit). "
         "K = round(budget x N). Recall is target-level; precision, false alarms are file-level (target files = every file matching a target pattern). "
         "Wilson 95% intervals use n = number of targets (7 / 19 / 34 / 60 pooled); for the seed-mean the mean caught count is used as k.", ""]
    L += ["## (a) Error rates", ""]
    for b in ("15", "20"):
        L += [f"### Budget {b}%", "",
              "| disk | model | K | recall (seed-mean) | Wilson 95% | recall (worst seed) | Wilson 95% | miss rate | file precision | false alarms | false-alarm rate |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for t in C.DISKS:
            for m in ("IF", "LOF", "OC-SVM"):
                e = R["error_rates"]["per_disk"][t][m][b]
                L.append(f"| {t} | {m} | {e['K']} | {pc(e['recall_seedmean'])}% ({e['recall_seedmean'] * e['targets']:.1f}/{e['targets']}) | "
                         f"{pc(e['recall_seedmean_wilson95'][0])}-{pc(e['recall_seedmean_wilson95'][1])} | {pc(e['recall_worst'])}% | "
                         f"{pc(e['recall_worst_wilson95'][0])}-{pc(e['recall_worst_wilson95'][1])} | {pc(e['miss_rate_seedmean'])}% | "
                         f"{e['file_precision']['mean'] * 100:.2f}% | {e['false_alarms']['mean']:.0f} | {e['false_alarm_rate']['mean'] * 100:.2f}% |")
        for m in ("IF", "LOF", "OC-SVM"):
            e = R["error_rates"]["pooled"][m][b]
            L.append(f"| pooled (60) | {m} | {e['K_total']} | {pc(e['recall_seedmean'])}% | "
                     f"{pc(e['recall_seedmean_wilson95'][0])}-{pc(e['recall_seedmean_wilson95'][1])} | {pc(e['recall_worst'])}% | "
                     f"{pc(e['recall_worst_wilson95'][0])}-{pc(e['recall_worst_wilson95'][1])} | {pc(e['miss_rate_seedmean'])}% | "
                     f"{e['file_precision']['mean'] * 100:.2f}% | {e['false_alarms']['mean']:.0f} | {e['false_alarm_rate']['mean'] * 100:.2f}% |")
        L.append("")
    L += ["### Per-target best rank, Isolation Forest (seed-mean over 5 seeds)", "",
          "Percentile = best rank / N. `outside 20%` marks targets whose seed-mean best rank is beyond the 20% review budget; "
          "`hard` = one of the 10 largest percentiles of the 60 targets.", "",
          "| disk | target | files | best rank (mean) | sd | worst seed | percentile (mean) | percentile (worst seed) | outside 15% | outside 20% | hard |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    hard = {(r["disk"], r["target"]) for r in R["per_target_IF"]["hardest10_pooled"]}
    for t in C.DISKS:
        for r in sorted(R["per_target_IF"]["disks"][t], key=lambda r: -r["percentile_mean"]):
            L.append(f"| {t} | {r['target']} | {r['n_files']} | {r['best_rank_mean']:.1f} | {r['best_rank_sd']:.1f} | {r['best_rank_worst_seed']} | "
                     f"{r['percentile_mean']:.2f}% | {r['percentile_worst_seed']:.2f}% | {'yes' if r['outside_15pct'] else ''} | "
                     f"{'yes' if r['outside_20pct'] else ''} | {'hard' if (t, r['target']) in hard else ''} |")
    L += ["", "## (b) Rank-based metrics (file level, mean ± sd over seeds)", "",
          "| disk | model | target files | AUC-ROC | average precision | R-precision |", "|---|---|---|---|---|---|"]
    for t in C.DISKS:
        for m in ("IF", "LOF", "OC-SVM"):
            x = R["rank_metrics"]["per_disk"][t][m]
            f = lambda k, d=4: f"{x[k]['mean']:.{d}f} ± {x[k]['sd']:.{d}f}"
            L.append(f"| {t} | {m} | {x['positives_files']} | {f('auc')} | {f('ap')} | {f('rprec')} |")
    L += ["", R["rank_metrics"]["note"] + ".", "", "## (c) Model comparison", "",
          "Target-level paired test, 60 targets pooled over disks. For each target the seed-mean best-rank percentile is compared.", "",
          "| comparison | n | non-zero pairs | W | one-sided p | median pct IF | median pct other | IF better / other better / ties |", "|---|---|---|---|---|---|---|---|"]
    for k, v in R["model_comparison"]["wilcoxon"].items():
        o = k.split("_vs_")[1]
        L.append(f"| {k.replace('_', ' ')} | {v['n_targets']} | {v['n_nonzero_pairs']} | {v['statistic_W']:.1f} | {v['p_value']:.3g} | "
                 f"{v['median_percentile_IF']:.2f} | {v['median_percentile_' + o]:.2f} | {v['targets_IF_better']} / {v['targets_other_better']} / {v['ties']} |")
    L += ["", "Per disk (same test):", "", "| comparison | disk | n | W | p |", "|---|---|---|---|---|"]
    for k, v in R["model_comparison"]["wilcoxon"].items():
        for t, x in v["per_disk"].items():
            L.append(f"| {k.replace('_', ' ')} | {t} | {x['n']} | {x.get('W', float('nan')):.1f} | {x.get('p', float('nan')):.3g} |")
    L += ["", "Bootstrap (2,000 resamples of targets) 95% CI of recall at 20%:", "",
          "| model | pooled | img1 | img2 | img3 |", "|---|---|---|---|---|"]
    for m, v in R["model_comparison"]["bootstrap_recall20"].items():
        cell = lambda x: f"{pc(x['recall20'])}% [{pc(x['ci95'][0])}, {pc(x['ci95'][1])}]"
        L.append(f"| {m} | {cell(v['pooled'])} | " + " | ".join(cell(v['per_disk'][t]) for t in C.DISKS) + " |")
    L += ["", R["model_comparison"]["note"] + ".", ""]
    rt = R["runtime"]
    L += ["## (d) Runtime and data volume", "",
          f"Machine: {rt['machine']['cpu']}, {rt['machine']['logical_cpus']} logical CPUs, {rt['machine']['ram_gb']} GB RAM, {rt['machine']['os']}, "
          f"Python {rt['machine']['python']}, scikit-learn {rt['machine']['sklearn']}, shap {rt['machine']['shap']}. Mean of {rt['runs']} runs.", "",
          "| disk | files | flagged (20%) | feature build (s) | IF fit+score (s) | TreeSHAP per 1,000 flagged (s) | MFT records (files / all) | prefetch .pf | event logs | registry hives |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for t in C.DISKS:
        x = rt["per_disk"][t]
        a = x["artifacts"]
        L.append(f"| {t} | {x['files']} | {x['flagged_20pct']} | {x['build_features_s']['mean']:.1f} ± {x['build_features_s']['sd']:.1f} | "
                 f"{x['if_fit_score_s']['mean']:.2f} ± {x['if_fit_score_s']['sd']:.2f} | {x['shap_s_per_1000_flagged']['mean']:.2f} ± {x['shap_s_per_1000_flagged']['sd']:.2f} | "
                 f"{a['mft_records_files']} / {a['mft_records_total']} | {a['prefetch_pf_files']} | {a['evtx_log_files']} | {a['registry_hives']} |")
    L += ["", rt["note"] + ".", "", f"Parsed event records: " + ", ".join(f"{t} {rt['per_disk'][t]['artifacts'].get('parsed_events')}" for t in C.DISKS) + ".", ""]
    open(os.path.join(OUTD, "stats.md"), "w").write("\n".join(L))


if __name__ == "__main__":
    main()
