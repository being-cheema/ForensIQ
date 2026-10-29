import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { AN, canAnim } from '../lib/motion'
import { fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import { featureContributions, rankWithin } from './engine.js'
import { fmtRaw } from './data'
import { Part, pal, useCanvas, useThemeTick, useSettled } from './ui'

const HEAVY = ['delta_mc', 'delta_mb', 'delta_ab', 'delta_si_fn', 'size']
const MAIN = ['delta_si_fn', 'delta_mc', 'delta_mb', 'delta_ab', 'filename_entropy', 'path_depth', 'size']
const MAIN_FLAGS = ['after_hours_touch', 'per_file_prefetch_hit', 'is_exe', 'is_shortcut_or_trace']
const slog = (v) => Math.sign(v) * Math.log1p(Math.abs(v))
const sexp = (u) => Math.sign(u) * Math.expm1(Math.abs(u))

export default function A3({ d, fit, pct, setPlanted }) {
  const tick = useThemeTick()
  const j = (f) => d.features.indexOf(f)
  // range of each feature: p1..p99 from the full disk
  const spec = useMemo(() => {
    const o = {}
    d.features.forEach((f, i) => {
      const [lo, med, hi] = d.ranges[f]
      o[f] = { lo, med, hi, bin: d.uniq[i] <= 2 || (lo === 0 && hi <= 1), flat: hi === lo && lo === d.ranges[f][1] }
    })
    return o
  }, [d])
  const base = useMemo(() => { const v = {}; d.features.forEach((f) => { v[f] = spec[f].bin ? Math.round(spec[f].med) : spec[f].med }); return v }, [d, spec])
  const [vals, setVals] = useState(base)
  const [preset, setPreset] = useState(null)
  useEffect(() => { setVals(base); setPreset(null) }, [base])

  const PRE = useMemo(() => {
    const P = (name, over) => [name, () => {
      const v = { ...base }
      Object.keys(over).forEach((f) => { if (f in v) { const s = spec[f]; const o = over[f]; v[f] = o === 'hi' ? s.hi : o === 'lo' ? s.lo : o === 'med' ? s.med : o } })
      return v
    }]
    return [
      P('Timestomped tool', { is_exe: 1, delta_si_fn: 'hi', delta_mc: 'hi', delta_mb: 'hi', delta_ab: 'hi', future_m: 1, m_before_cr: 1, per_file_prefetch_hit: 1, user_path: 1, filename_entropy: 'hi', is_shortcut_or_trace: 0 }),
      P('Normal Word doc', { is_exe: 0, user_path: 1, is_shortcut_or_trace: 0, after_hours_touch: 0, per_file_prefetch_hit: 0 }),
      P('Hidden after-hours script', { is_script: 1, script_host: 1, powershell_exec: 1, after_hours_touch: 1, temp_path: 1, is_exe: 0, filename_entropy: 'hi', path_depth: 'hi', is_deleted: 1, delta_si_fn: 'hi' }),
    ]
  }, [base, spec])

  const z = useMemo(() => d.features.map((f, i) => (d.std[i] ? (vals[f] - d.mean[i]) / d.std[i] : 0)), [vals, d])
  const sc = fit.forest.score(z)
  const sampleRank = useMemo(() => { let h = 0; for (let i = 0; i < d.n; i++) if (fit.ifScores[i] > sc) h++; return h + 1 }, [sc, fit])
  const full = rankWithin(sc, fit.ifScores, d.N, d.isT)
  const K = Math.max(1, Math.round(pct * d.N))
  const caught = full <= K
  const contrib = useMemo(() => featureContributions(fit.forest, z), [fit, z])
  useEffect(() => { setPlanted({ sampleRank, full }) }, [sampleRank, full])
  useEffect(() => () => setPlanted(null), [])
  const live = useSettled(`Your file ranks ${full} of ${d.N}, ${caught ? 'caught' : 'missed'} at a ${pc(pct)} budget.`)

  const set = (f, v) => { setPreset(null); setVals((o) => ({ ...o, [f]: v })) }
  const apply = (name, fn) => { setPreset(name); setVals(fn()) }

  const sliders = MAIN.filter((f) => j(f) >= 0 && !spec[f].flat)
  const flags = MAIN_FLAGS.filter((f) => j(f) >= 0)
  const otherFlags = d.features.filter((f) => !MAIN.includes(f) && !MAIN_FLAGS.includes(f) && !spec[f].flat)

  const slider = (f) => {
    const s = spec[f], heavy = HEAVY.includes(f)
    const a = heavy ? slog(s.lo) : s.lo, b = heavy ? slog(s.hi) : s.hi
    const pos = heavy ? slog(vals[f]) : vals[f]
    return (
      <div key={f} className="lrange wide" title={d.info[f]}>
        <label htmlFor={'a3-' + f}>{f}</label>
        <input id={'a3-' + f} type="range" min={a} max={b} step={(b - a) / 400 || 1} value={Math.min(b, Math.max(a, pos))}
          onChange={(e) => { const v = +e.target.value; set(f, heavy ? sexp(v) : f === 'path_depth' ? Math.round(v * 2) / 2 : v) }} aria-valuetext={fmtRaw(f, vals[f])} />
        <output htmlFor={'a3-' + f}>{fmtRaw(f, vals[f])}</output>
      </div>
    )
  }
  const toggle = (f) => (
    <label key={f} className="lf" title={d.info[f]}><input type="checkbox" checked={!!vals[f]} onChange={(e) => set(f, e.target.checked ? 1 : 0)} /><span className="mono">{f}</span></label>
  )

  return (
    <Part n="A3" title="Plant your own attack"
      intro="Describe a file you could imagine on a seized disk: set its timestamps, name and where it lives. The forest from A1 scores it, as if it were a file nobody had seen, and tells you where it would land among every file on the real disk."
      note={<>The planted file is <b>never added to the training data</b>; it is only scored. The full-disk rank is estimated by comparing its score with the sample's ordinary files, scaled to the disk's {fmt(d.N)} files. It uses the Isolation Forest from A1 (same features, trees and seed).</>}>
      <div className="lab-row">
        <div className="fld"><span className="lab" id="a3-pre">Start from</span>
          <div className="tabs" role="group" aria-labelledby="a3-pre">
            {PRE.map(([name, fn]) => <button key={name} type="button" aria-pressed={preset === name} onClick={() => apply(name, fn)}>{name}</button>)}
            <button type="button" aria-pressed={false} onClick={() => apply(null, () => base)}>Disk median</button>
          </div></div>
      </div>
      <div className="a3-grid">
        <div className="a3-ctl">
          <h4 className="lab-sub">Timestamps, name and size</h4>
          {sliders.map(slider)}
          <h4 className="lab-sub">Traits</h4>
          <div className="lf-wrap">{flags.map(toggle)}</div>
          <details className="a3-more"><summary>More flags</summary>
            <div className="lf-wrap">{otherFlags.map(toggle)}</div></details>
        </div>
        <div className="a3-out">
          <div className="a3-big" aria-hidden="true">
            <span className="k">Your file ranks</span>
            <div className="disp">#<Num value={full} fmt={fmt} /> <small>of {fmt(d.N)}</small></div>
            <div className={'verd ' + (caught ? 'ok' : 'no')}>{caught ? <span className="flag ok">Caught</span> : <span className="flag bad">Missed</span>}
              <span> at a {pc(pct)} budget ({fmt(K)} files read)</span></div>
          </div>
          <span className="sr" aria-live="polite">{live}</span>
          <Strip d={d} fit={fit} pct={pct} sampleRank={sampleRank} caught={caught} tick={tick} />
          <Contrib d={d} contrib={contrib} mask={fit.cfg.mask} />
        </div>
      </div>
    </Part>
  )
}

function Strip({ d, fit, pct, sampleRank, caught, tick }) {
  const cv = useRef(), mk = useRef(), first = useRef(true), n = d.n
  const xOf = (rank, w) => 8 + Math.sqrt((rank - 1) / (n - 1)) * (w - 16)
  const L = useRef({}); L.current = { fit, pct }
  const draw = (ctx, w, h) => {
    const P = pal(), { fit: f, pct: p } = L.current
    const order = f.ranks.map((r, i) => i).sort((a, b) => f.ifScores[b] - f.ifScores[a])
    // ordinary files as thin ticks, evidence as taller red ticks
    ctx.fillStyle = P.ink2; ctx.globalAlpha = 0.5
    ctx.beginPath()
    order.forEach((i, r) => { if (!d.isT[i]) ctx.rect(Math.round(xOf(r + 1, w)), h - 36, 1, 14) })
    ctx.fill(); ctx.globalAlpha = 1
    ctx.fillStyle = P.accent; ctx.beginPath()
    order.forEach((i, r) => { if (d.isT[i]) ctx.rect(Math.round(xOf(r + 1, w)) - 0.5, h - 44, 2, 22) })
    ctx.fill()
    const kk = Math.max(1, Math.round(p * n)), xb = xOf(kk, w)
    ctx.strokeStyle = P.accent; ctx.setLineDash([4, 3]); ctx.beginPath(); ctx.moveTo(Math.round(xb) + .5, 22); ctx.lineTo(Math.round(xb) + .5, h - 14); ctx.stroke(); ctx.setLineDash([])
    ctx.font = '500 11px "Inter Tight", sans-serif'; ctx.fillStyle = P.accentInk; ctx.textAlign = xb > w - 120 ? 'right' : 'left'
    ctx.fillText('budget', xb + (xb > w - 120 ? -5 : 5), h - 3 - 0)
    ctx.fillStyle = P.ink2; ctx.textAlign = 'left'; ctx.fillText('most suspicious', 8, h - 3)
    ctx.textAlign = 'right'; ctx.fillText('least', w - 8, h - 3)
  }
  const redraw = useCanvas(cv, draw, tick)
  useEffect(() => { redraw() }, [fit, pct])
  // the marker drops in, then follows the rank
  useLayoutEffect(() => {
    const m = mk.current, c = cv.current; if (!m || !c) return
    const w = c.getBoundingClientRect().width, x = xOf(sampleRank, w)
    if (!canAnim()) { m.style.left = x + 'px'; m.style.opacity = 1; m.style.transform = 'none'; first.current = false; return }
    if (first.current) { first.current = false; m.style.left = x + 'px'; AN.remove(m); AN({ targets: m, translateY: [-46, 0], opacity: [0, 1], duration: 620, easing: 'easeOutBounce' }) }
    else { AN.remove(m); m.style.opacity = 1; AN({ targets: m, left: x, translateY: 0, duration: 240, easing: 'easeOutQuart' }) }
  }, [sampleRank, fit])
  return (
    <figure className="a3-strip">
      <figcaption className="small">Where it falls among the sample (the sample holds every evidence file, so its top looks busier than the real disk)</figcaption>
      <div className="strip-box"><canvas ref={cv} className="strip-cv" aria-hidden="true"></canvas>
        <div className={'pmark' + (caught ? ' ok' : '')} ref={mk} aria-hidden="true"><i></i></div></div>
    </figure>
  )
}

function Contrib({ d, contrib, mask }) {
  const root = useRef()
  const rows = useMemo(() => d.features.map((f, i) => ({ f, i, g: d.gidx[i] })).sort((a, b) => a.g - b.g || a.i - b.i), [d])
  const mx = Math.max(0.0001, ...contrib)
  useEffect(() => {
    const els = root.current.querySelectorAll('[data-w]'); const vals = Array.from(els, (e) => +e.dataset.w)
    if (!canAnim()) { els.forEach((e, k) => { e.style.width = vals[k] + '%' }); return }
    AN.remove(els); AN({ targets: els, width: (e, k) => vals[k] + '%', duration: 300, easing: 'easeOutQuart' })
    const t = setTimeout(() => els.forEach((e, k) => { e.style.width = vals[k] + '%' }), 600)
    return () => clearTimeout(t)
  }, [contrib])
  return (
    <div className="a3-con" ref={root}>
      <div className="cap">What gave it away</div>
      <p className="small">Share of the forest's cuts, weighted towards early cuts, that were made on each feature along this file's path.</p>
      {rows.map(({ f, i }) => (
        <div key={f} className={'cbar' + (mask[i] ? '' : ' off')} title={d.info[f]}>
          <span className="mono">{f}</span>
          <span className="t"><i data-w={(contrib[i] / mx) * 100} style={{ width: (contrib[i] / mx) * 100 + '%' }}></i></span>
          <span className="num">{mask[i] ? (contrib[i] * 100).toFixed(0) + '%' : 'off'}</span>
        </div>
      ))}
    </div>
  )
}
