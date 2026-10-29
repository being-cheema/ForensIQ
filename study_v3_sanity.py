"""Phase 1 sanity: ground-truth target matching and a plain Isolation Forest (seed 42) at 15% / 20% budget,
clean vs legacy23. Report only; nothing is tuned."""
import os
os.environ.setdefault("FORENSIQ_FEATURE_SET", "clean")
import multimodel_eval as M

for tag in ["img1", "img2", "img3"]:
    spec = M.IMAGES[tag]
    for name, fn in [("legacy23", M.build_features_legacy23), ("clean", M.build_features_clean)]:
        df, raw, feats = fn(spec["art_dir"], tag)
        tg = spec["targets"](df["path"]) if callable(spec["targets"]) else spec["targets"]
        active, all_idx = M.match_targets(df["path"], tg)
        Xs = M.standardize(df[feats].values.astype(float))
        s, _ = M.fit_score("Isolation Forest", Xs, 42)
        row = [f"{name}: {len(feats)} feats, targets matched {len(active)} ({len(all_idx)} files)"]
        for pct in (0.15, 0.20):
            mk, _ = M.top_k_mask(s, int(round(pct * len(df))))
            m = M.metrics(mk, active, all_idx)
            row.append(f"{int(pct*100)}%: {m['targets_hit']}/{m['targets_total']}")
        print(tag, " | ".join(row))
