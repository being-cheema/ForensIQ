import A1 from '../data/study/A1.json'
import A2 from '../data/study/A2.json'
import A3 from '../data/study/A3.json'
import A4 from '../data/study/A4.json'
import A5 from '../data/study/A5.json'
import A6 from '../data/study/A6.json'
import A7 from '../data/study/A7.json'
import B from '../data/study/B.json'
import C1 from '../data/study/C1.json'

/* The pre-registered study (reports/study_v3). Every number in the new exhibits comes from these files. */
export { A1, A2, A3, A4, A5, A6, A7, B, C1 }
export const REPO = 'https://github.com/being-cheema/ForensIQ'
export const PROTOCOL_URL = REPO + '/blob/main/reports/study_v3/PROTOCOL.md'
export const AMENDMENT_URL = REPO + '/blob/main/reports/study_v3/AMENDMENT.md'

export const DISKS = ['img1', 'img2', 'img3']
export const MK = ['IF', 'LOF', 'OC-SVM']          // same order as the site's MODELS
export const MNAME = { IF: 'Isolation Forest', LOF: 'LOF', 'OC-SVM': 'One-Class SVM' }
export const MCOL = { IF: '--m0', LOF: '--m1', 'OC-SVM': '--m2' }
export const NT = { img1: 7, img2: 19, img3: 34 }

export const f1 = (v) => (Math.round(v * 10) / 10).toString()
export const f2 = (v) => (Math.round(v * 100) / 100).toString()
export const pct1 = (v) => (Math.round(v * 10) / 10) + '%'
export const rangeTxt = (lo, hi, f) => { const g = f || f1; return g(lo) === g(hi) ? g(lo) : g(lo) + '–' + g(hi) }

/* Targets caught against budget, from A2: per seed counts at 0, 1, ... 100 percent of the disk. */
const cache = {}
export function seedCurve(img, mk) {
  const k = img + '/' + mk
  if (cache[k]) return cache[k]
  const d = A2.disks[img], mod = d.models[mk], nT = d.targets, seeds = Object.keys(mod.seeds)
  const n = A2.budgets.length, mean = [], lo = [], hi = []
  for (let i = 0; i < n; i++) {
    let s = 0, a = Infinity, b = -Infinity
    seeds.forEach((sd) => { const v = mod.seeds[sd][i]; s += v; a = Math.min(a, v); b = Math.max(b, v) })
    mean.push(s / seeds.length); lo.push(a); hi.push(b)
  }
  return (cache[k] = { img, mk, nT, N: d.N, mean, lo, hi, sum: mod.summary, seeds: seeds.length })
}
/* linear interpolation of a per-percent array at budget b (percent) */
export function at(arr, b) {
  const x = Math.min(100, Math.max(0, b)), i = Math.floor(x), j = Math.min(100, i + 1)
  return arr[i] + (arr[j] - arr[i]) * (x - i)
}

/* mean, lowest, highest and spread of targets caught at an integer budget, over the 5 seeds */
export function statAt(img, mk, b) {
  const d = A2.disks[img], arr = Object.keys(d.models[mk].seeds).map((sd) => d.models[mk].seeds[sd][b])
  const mean = arr.reduce((a, v) => a + v, 0) / arr.length
  const sd = Math.sqrt(arr.reduce((a, v) => a + (v - mean) * (v - mean), 0) / Math.max(1, arr.length - 1))
  return { mean, sd, min: Math.min.apply(null, arr), max: Math.max.apply(null, arr), n: d.targets, per: arr }
}
