import D from '../data/data.json'

export { D }
export const MODELS = D.models
export const SHORT = ['Isolation Forest', 'LOF', 'One-Class SVM']
export const MVAR = ['--m0', '--m1', '--m2']
export const IMGS = Object.keys(D.images)

export const fmt = (n) => Number(n).toLocaleString('en-US')
export const pc = (x, d) => (x * 100).toFixed(d == null ? 1 : d) + '%'
export const short = (l) => l.split(':')[0]
export const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim()
