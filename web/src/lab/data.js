import { useEffect, useState } from 'react'
import { fitIsolationForest, lofScores, rankOf } from './engine.js'

/* ---------- loading and preparing a disk's 2,000-file sample ---------- */
const loaders = {
  img1: () => import('../data/lab/img1.json'),
  img2: () => import('../data/lab/img2.json'),
  img3: () => import('../data/lab/img3.json'),
}
const cache = {}

export const GROUPS = {
  Temporal: ['delta_mc', 'delta_mb', 'delta_ab', 'future_m', 'zero_size_recent', 'delta_si_fn', 'after_hours_touch'],
  'Path / file': ['size', 'is_deleted', 'is_exe', 'is_archive', 'temp_path', 'user_path', 'path_depth', 'filename_entropy', 'is_shortcut_or_trace'],
  'Execution / tool': ['credential_tool', 'sniffer_tool', 'powershell_exec', 'cmd_exec', 'script_host', 'usb_present', 'per_file_prefetch_hit'],
}
export const GROUP_NAMES = Object.keys(GROUPS)
const NEW_6 = ['is_shortcut_or_trace', 'per_file_prefetch_hit', 'after_hours_touch', 'delta_si_fn', 'filename_entropy', 'path_depth']

function prep(raw) {
  const rows = raw.rows, n = rows.length, nf = raw.features.length
  const X = rows.map((r) => r.x)
  const isT = rows.map((r) => !!r.t)
  const name = [], folder = [], depth = []
  rows.forEach((r) => {
    const segs = r.p.trim().split('/').filter(Boolean)
    name.push(segs[segs.length - 1] || r.p)
    folder.push('/' + segs.slice(0, -1).join('/'))
    depth.push(Math.max(1, segs.length))
  })
  const mtime = rows.map((r) => (r.ts && r.ts.m ? r.ts.m : null))
  // distinct values per feature in the sample (used to find binary / discrete features)
  const uniq = new Array(nf).fill(0)
  for (let j = 0; j < nf; j++) {
    const s = new Set()
    for (let i = 0; i < n; i++) { s.add(Math.round(X[i][j] * 1000)); if (s.size > 8) break }
    uniq[j] = s.size
  }
  const gidx = raw.features.map((f) => GROUP_NAMES.findIndex((g) => GROUPS[g].includes(f)))
  const targetIdx = []
  for (let i = 0; i < n; i++) if (isT[i]) targetIdx.push(i)
  return { raw, rows, n, nf, X, isT, name, folder, depth, mtime, uniq, gidx, targetIdx, features: raw.features, N: raw.N, mean: raw.mean, std: raw.std,
    ranges: raw.rawRanges, info: raw.featureInfo, timeline: raw.timeline, svmRank: rows.map((r) => r.rk.svm) }
}

export function useDisk(img) {
  const [st, setSt] = useState(() => (cache[img] ? { img, d: cache[img] } : { img, d: null }))
  useEffect(() => {
    let live = true
    if (cache[img]) { setSt({ img, d: cache[img] }); return }
    setSt({ img, d: null })
    loaders[img]().then((m) => { cache[img] = prep(m.default || m); if (live) setSt({ img, d: cache[img] }) }).catch(() => { if (live) setSt({ img, d: null, err: true }) })
    return () => { live = false }
  }, [img])
  return st.img === img ? st : { img, d: null }
}

/* ---------- feature masks and presets ---------- */
export const maskOf = (d, pred) => d.features.map((f) => pred(f))
export const PRESETS = [
  ['All 23', (d) => maskOf(d, () => true)],
  ['Original 17', (d) => maskOf(d, (f) => !NEW_6.includes(f))],
  ['Drop timestamps', (d) => maskOf(d, (f) => !GROUPS.Temporal.includes(f))],
  ['Only path features', (d) => maskOf(d, (f) => GROUPS['Path / file'].includes(f))],
]
export const sameMask = (a, b) => a.length === b.length && a.every((v, i) => v === b[i])

/* ---------- fitting ---------- */
export const DEFAULT_CFG = { model: 'if', nTrees: 200, k: 20, seed: 42 }

/** Fit the chosen model on the sample; always also returns an Isolation Forest (used by the probe, the planted file and the game). */
export function fitModel(d, cfg) {
  const t0 = performance.now()
  const mask = cfg.mask
  const forest = fitIsolationForest(d.X, { nTrees: cfg.nTrees, sampleSize: 256, seed: cfg.seed, featureMask: mask })
  const ifScores = d.X.map((x) => forest.score(x))
  let scores
  if (cfg.model === 'lof') scores = lofScores(d.X, cfg.k, mask)
  else if (cfg.model === 'svm') scores = d.svmRank.map((r) => -r)
  else scores = ifScores
  const ranks = rankOf(scores)
  return { cfg, forest, ifScores, scores, ranks, ms: performance.now() - t0 }
}

export function recallAt(ranks, isT, frac) {
  const k = Math.max(1, Math.round(frac * ranks.length))
  let hit = 0, tot = 0
  for (let i = 0; i < ranks.length; i++) if (isT[i]) { tot++; if (ranks[i] <= k) hit++ }
  return { hit, tot, k, recall: tot ? hit / tot : 0 }
}

/* ---------- small formatters ---------- */
export const utcDay = (s) => new Date(s * 1000).toISOString().slice(0, 10)
export const utcTime = (s) => new Date(s * 1000).toISOString().slice(11, 19)
export const rawOf = (d, j, z) => z * (d.std[j] || 1) + d.mean[j]
export function human(sec) {
  const a = Math.abs(sec)
  if (a < 90) return Math.round(sec) + ' s'
  if (a < 5400) return Math.round(sec / 60) + ' min'
  if (a < 129600) return (sec / 3600).toFixed(1) + ' h'
  if (a < 86400 * 400) return Math.round(sec / 86400) + ' days'
  return (sec / 31557600).toFixed(1) + ' years'
}
export const SECONDS = ['delta_mc', 'delta_mb', 'delta_ab', 'delta_si_fn']
export function fmtRaw(f, v) {
  if (SECONDS.includes(f)) return human(v)
  if (f === 'size') return v < 1024 ? Math.round(v) + ' B' : v < 1048576 ? (v / 1024).toFixed(1) + ' KB' : (v / 1048576).toFixed(1) + ' MB'
  if (f === 'filename_entropy') return v.toFixed(2) + ' bits'
  if (f === 'path_depth') return v.toFixed(1)
  return Math.abs(v) < 10 ? v.toFixed(2) : Math.round(v).toLocaleString('en-US')
}
export const shortPath = (p, n) => (p.length > n ? '…' + p.slice(p.length - n + 1) : p)

/** deterministic shuffle */
export function shuffled(n, seed) {
  const a = Array.from({ length: n }, (_, i) => i)
  let s = seed >>> 0
  const rnd = () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296 }
  for (let i = n - 1; i > 0; i--) { const j = (rnd() * (i + 1)) | 0; const t = a[i]; a[i] = a[j]; a[j] = t }
  return a
}
