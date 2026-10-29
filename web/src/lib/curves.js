import { D, MODELS, SW } from './data'

/* Recall, files read and false alarms as a function of review budget (percent of files).
   0 to JOIN percent: exact full-disk ranks of one run (seed 42): recall(K) is the share of targets whose best copy ranks within K.
   JOIN to 100 percent: means of 5 seeds x 3 randomizations from the threshold sweep (Images 2 and 3). Image 1 has no sweep, so it is exact throughout. */
export const JOIN = 5
export const CFGS = [
  { id: 'IF-23', model: 0, v: '--m0', dash: '', name: 'Isolation Forest', lab: 'Isolation Forest · 23', lab2: 'IF · 23' },
  { id: 'LOF-23', model: 1, v: '--m1', dash: '', name: 'LOF', lab: 'LOF · 23', lab2: 'LOF · 23' },
  { id: 'OCSVM-23', model: 2, v: '--m2', dash: '', name: 'One-Class SVM', lab: 'OC-SVM · 23', lab2: 'OC-SVM' },
  { id: 'IF-17', model: null, v: '--ink2', dash: '5 4', name: 'Isolation Forest, original 17', lab: 'IF · original 17', lab2: 'IF · 17' }
]
const cache = {}
export const curve = (img, id) => { const k = img + '/' + id; return k in cache ? cache[k] : (cache[k] = build(img, CFGS.find((c) => c.id === id))) }
export const curveSet = (img) => CFGS.map((c) => curve(img, c.id)).filter(Boolean)

function build(img, cfg) {
  const im = D.images[img], N = im.files
  const sw = (SW[img] || {})[cfg.id] || null
  const ranks = cfg.model != null ? im.targets.map((t) => t.ranks[MODELS[cfg.model]]).sort((a, b) => a - b) : null
  if (!ranks && !sw) return null
  const nT = ranks ? ranks.length : sw.targets
  const P = sw ? sw.pct : null
  const ev = sw ? sw.precision.map((p, i) => p * sw.K[i] / 100) : null     // evidence files read = precision x K
  const cntLE = (K) => { let c = 0; for (const r of ranks) if (r <= K) c++; return c }
  const exactAt = (b) => { const K = Math.round(b / 100 * N), f = cntLE(K); return { K, found: f, recall: f / nT * 100, std: 0 } }
  const sweepAt = (b) => {
    let j = P.findIndex((p) => p >= b); if (j < 0) j = P.length - 1
    const j0 = Math.max(0, j - 1), t = P[j] === P[j0] ? 0 : (b - P[j0]) / (P[j] - P[j0]), L = (a) => a[j0] + (a[j] - a[j0]) * t
    return { K: L(sw.K), found: L(ev), recall: L(sw.recall), std: L(sw.std) }
  }
  const at = (b) => {
    b = Math.min(100, Math.max(0, b))
    let o
    if (ranks && (b < JOIN || !sw)) o = exactAt(b)
    else if (sw && b >= P[0]) o = sweepAt(b)
    else return null
    o.b = b; o.prec = o.K > 0 ? o.found / o.K * 100 : null; o.fa = Math.max(0, o.K - o.found)
    return o
  }
  const fm = at(100).recall
  let pb = null
  if (ranks) { const bm = ranks[nT - 1] / N * 100; if (!sw || (bm < JOIN && sw.recall[0] >= fm - 0.005)) pb = bm }
  if (pb == null) pb = P[sw.recall.findIndex((r) => r >= fm - 0.005)]
  const plateau = { b: pb, K: at(pb).K, fm, partial: fm < 99.95 }
  let knee = null
  if (ranks) { const need = Math.ceil(0.9 * nT - 1e-9), bk = ranks[need - 1] / N * 100; if (!sw || bk < JOIN) knee = bk }
  if (knee == null && sw) { const j = sw.recall.findIndex((r) => r >= 90 - 0.005); if (j >= 0) knee = P[j] }
  const scale = ranks && sw ? sw.K[0] / (JOIN / 100 * N) : 1
  const dead = (b) => { if (b <= pb) return 0; let kp = plateau.K; if (ranks && sw && pb < JOIN && b >= JOIN) kp *= scale; return Math.max(0, at(b).K - kp) }
  const steps = () => {
    const lim = sw ? JOIN : 100, pts = [[0, 0]]; let f = 0
    ranks.forEach((r, i) => { const b = r / N * 100; if (b > lim) return; pts.push([b, i / nT * 100], [b, (i + 1) / nT * 100]); f = i + 1 })
    pts.push([lim, f / nT * 100]); return pts
  }
  let bs
  if (!ranks) bs = P.slice()
  else {
    const g = [], hi = sw ? JOIN : 100, G = sw ? 40 : 110
    for (let i = 0; i <= G; i++) g.push(0.1 * Math.pow(hi / 0.1, i / G))
    if (sw) g.push.apply(g, P); else for (let b = 1; b <= 100; b++) g.push(b)
    bs = Array.from(new Set(g.map((x) => +x.toFixed(4)))).sort((a, b) => a - b)
  }
  const gain = (a, b) => {
    if (ranks && sw && a < JOIN && b > JOIN) return gain(a, JOIN) + gain(JOIN, b)
    if (!ranks && a < JOIN) a = JOIN
    if (b <= a) return null
    const A = at(a), B = at(b); return A && B ? Math.max(0, B.found - A.found) : null
  }
  return { cfg, img, N, nT, ranks, sw, at, plateau, knee, dead, steps, bs, gain }
}

/* formatters */
export const fb = (b) => (b < 1 ? +b.toFixed(2) : b < 10 ? +b.toFixed(1) : Math.round(b)) + '%'
export const fn1 = (v) => (Math.abs(v - Math.round(v)) < 0.05 ? String(Math.round(v)) : v.toFixed(1))
