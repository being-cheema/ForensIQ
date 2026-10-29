// ForensIQ Lab engine: pure JS Isolation Forest, trace, contributions, LOF, rank helpers. No deps.

export function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const EULER = 0.5772156649015329;
/** average path length of unsuccessful BST search (Liu et al.) */
export function cFactor(n) {
  if (n <= 1) return 0;
  if (n === 2) return 1;
  return 2 * (Math.log(n - 1) + EULER) - (2 * (n - 1)) / n;
}

function buildTree(X, idx, depth, maxDepth, rng, feats) {
  const n = idx.length;
  if (depth >= maxDepth || n <= 1) return { f: -1, thr: 0, left: null, right: null, size: n, depth };
  // pick random feature among those with spread; retry like sklearn (constant features are skipped)
  const cand = feats.slice();
  while (cand.length) {
    const ci = (rng() * cand.length) | 0;
    const f = cand[ci];
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < n; i++) { const v = X[idx[i]][f]; if (v < lo) lo = v; if (v > hi) hi = v; }
    if (hi > lo) {
      const thr = lo + rng() * (hi - lo);
      const L = [], R = [];
      for (let i = 0; i < n; i++) (X[idx[i]][f] < thr ? L : R).push(idx[i]);
      if (!L.length || !R.length) { cand[ci] = cand[cand.length - 1]; cand.pop(); continue; }
      return { f, thr, size: n, depth,
        left: buildTree(X, L, depth + 1, maxDepth, rng, feats),
        right: buildTree(X, R, depth + 1, maxDepth, rng, feats) };
    }
    cand[ci] = cand[cand.length - 1]; cand.pop();
  }
  return { f: -1, thr: 0, left: null, right: null, size: n, depth };
}

function treePath(node, x) {
  let h = 0;
  while (node.f >= 0) { node = x[node.f] < node.thr ? node.left : node.right; h++; }
  return h + cFactor(node.size);
}

export function fitIsolationForest(X, { nTrees = 200, sampleSize = 256, seed = 42, featureMask = null } = {}) {
  const n = X.length, d = n ? X[0].length : 0;
  const psi = Math.min(sampleSize, n);
  const maxDepth = Math.ceil(Math.log2(Math.max(psi, 2)));
  const feats = [];
  for (let j = 0; j < d; j++) if (!featureMask || featureMask[j]) feats.push(j);
  const rng = mulberry32(seed);
  const trees = [];
  // per-feature data bounds of the training data (for trace cell bounds)
  const lo = new Array(d).fill(Infinity), hi = new Array(d).fill(-Infinity);
  for (let i = 0; i < n; i++) for (let j = 0; j < d; j++) { const v = X[i][j]; if (v < lo[j]) lo[j] = v; if (v > hi[j]) hi[j] = v; }
  const pool = new Int32Array(n);
  for (let t = 0; t < nTrees; t++) {
    for (let i = 0; i < n; i++) pool[i] = i;
    for (let i = 0; i < psi; i++) { const j = i + ((rng() * (n - i)) | 0); const tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp; }
    trees.push(buildTree(X, Array.from(pool.subarray(0, psi)), 0, maxDepth, rng, feats));
  }
  const c = cFactor(psi);
  const forest = { trees, c, nTrees, psi, lo, hi, featureMask, d };
  forest.pathLength = (x) => { let s = 0; for (let t = 0; t < trees.length; t++) s += treePath(trees[t], x); return s / trees.length; };
  forest.score = (x) => Math.pow(2, -forest.pathLength(x) / c);
  return forest;
}

/** Path of x through one tree: [{f, thr, side:'left'|'right', depth, nodeSize, lo:[], hi:[]}]; lo/hi = cell bounds before the cut. */
export function isolationTrace(forest, x, treeIndex = 0) {
  let node = forest.trees[treeIndex];
  const lo = forest.lo.slice(), hi = forest.hi.slice();
  const out = [];
  while (node.f >= 0) {
    const goLeft = x[node.f] < node.thr;
    out.push({ f: node.f, thr: node.thr, side: goLeft ? "left" : "right", depth: node.depth, nodeSize: node.size,
               lo: lo.slice(), hi: hi.slice() });
    if (goLeft) hi[node.f] = node.thr; else lo[node.f] = node.thr;
    node = goLeft ? node.left : node.right;
  }
  return out;
}

/** depth-weighted split counts per feature over all trees (weight 1/(depth+1)), normalized to sum 1. */
export function featureContributions(forest, x) {
  const w = new Float64Array(forest.d);
  for (const root of forest.trees) {
    let node = root;
    while (node.f >= 0) { w[node.f] += 1 / (node.depth + 1); node = x[node.f] < node.thr ? node.left : node.right; }
  }
  let s = 0; for (let j = 0; j < w.length; j++) s += w[j];
  return Array.from(w, (v) => (s > 0 ? v / s : 0));
}

/** Optional/slow: refit without each enabled feature; returns per-feature rank change of x among Xtrain scores (positive = x looks less anomalous without it). */
export function ablationContribution(Xtrain, x, { nTrees = 60, sampleSize = 256, seed = 42, featureMask = null } = {}) {
  const d = x.length;
  const mask = Array.from({ length: d }, (_, j) => (featureMask ? !!featureMask[j] : true));
  const rankIn = (m) => {
    const f = fitIsolationForest(Xtrain, { nTrees, sampleSize, seed, featureMask: m });
    const sx = f.score(x); let higher = 0;
    for (let i = 0; i < Xtrain.length; i++) if (f.score(Xtrain[i]) > sx) higher++;
    return higher + 1;
  };
  const base = rankIn(mask);
  const out = new Array(d).fill(0);
  for (let j = 0; j < d; j++) { if (!mask[j]) continue; const m = mask.slice(); m[j] = false; out[j] = rankIn(m) - base; }
  return { baseRank: base, rankChange: out };
}

/** exact LOF; higher = more anomalous (sklearn -negative_outlier_factor_). */
export function lofScores(X, k = 20, featureMask = null) {
  const n = X.length, dAll = n ? X[0].length : 0;
  const cols = []; for (let j = 0; j < dAll; j++) if (!featureMask || featureMask[j]) cols.push(j);
  const d = cols.length;
  k = Math.min(k, n - 1);
  const P = new Float32Array(n * d);
  for (let i = 0; i < n; i++) for (let a = 0; a < d; a++) P[i * d + a] = X[i][cols[a]];
  const kd = new Float32Array(n * k), ki = new Int32Array(n * k), kdist = new Float64Array(n);
  const bd = new Float32Array(k), bi = new Int32Array(k);
  for (let i = 0; i < n; i++) {
    let cnt = 0, worst = Infinity, wpos = 0;
    const oi = i * d;
    for (let j = 0; j < n; j++) {
      if (j === i) continue;
      const oj = j * d; let s = 0;
      for (let a = 0; a < d; a++) { const t = P[oi + a] - P[oj + a]; s += t * t; }
      if (cnt < k) {
        bd[cnt] = s; bi[cnt] = j; cnt++;
        if (cnt === k) { worst = -1; for (let q = 0; q < k; q++) if (bd[q] > worst) { worst = bd[q]; wpos = q; } }
      } else if (s < worst) {
        bd[wpos] = s; bi[wpos] = j; worst = -1;
        for (let q = 0; q < k; q++) if (bd[q] > worst) { worst = bd[q]; wpos = q; }
      }
    }
    let mx = 0;
    for (let q = 0; q < k; q++) { const dd = Math.sqrt(bd[q]); kd[i * k + q] = dd; ki[i * k + q] = bi[q]; if (dd > mx) mx = dd; }
    kdist[i] = mx;
  }
  const lrd = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0;
    for (let q = 0; q < k; q++) { const o = ki[i * k + q]; s += Math.max(kdist[o], kd[i * k + q]); }
    lrd[i] = 1 / (s / k + 1e-10);
  }
  const out = new Float64Array(n);
  for (let i = 0; i < n; i++) {
    let s = 0; for (let q = 0; q < k; q++) s += lrd[ki[i * k + q]];
    out[i] = s / k / lrd[i];
  }
  return Array.from(out);
}

/** ranks starting at 1, highest score = rank 1 (stable on ties). */
export function rankOf(scores) {
  const n = scores.length, order = Array.from({ length: n }, (_, i) => i);
  order.sort((a, b) => scores[b] - scores[a] || a - b);
  const r = new Array(n);
  for (let i = 0; i < n; i++) r[order[i]] = i + 1;
  return r;
}

/** share of target rows whose rank is within the top budgetFrac * n. */
export function recallAtBudget(ranks, isTarget, budgetFrac) {
  const k = Math.round(budgetFrac * ranks.length);
  let t = 0, hit = 0;
  for (let i = 0; i < ranks.length; i++) if (isTarget[i]) { t++; if (ranks[i] <= k) hit++; }
  return t ? hit / t : 0;
}

/** Estimate full-disk rank: ceil(frac of sample scoring higher * N_full) + 1. Pass isTarget to use non-target sample rows only. */
export function rankWithin(score, sampleScores, Nfull, isTarget = null) {
  let higher = 0, tot = 0;
  for (let i = 0; i < sampleScores.length; i++) {
    if (isTarget && isTarget[i]) continue;
    tot++; if (sampleScores[i] > score) higher++;
  }
  return Math.ceil((tot ? higher / tot : 0) * Nfull) + 1;
}
