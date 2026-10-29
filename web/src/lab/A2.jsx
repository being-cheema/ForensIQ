import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { AN, canAnim } from '../lib/motion'
import { useOnceInView } from '../lib/hooks'
import { fmt } from '../lib/data'
import Num from '../lib/Num'
import { fitIsolationForest, isolationTrace, cFactor } from './engine.js'
import { fmtRaw, rawOf } from './data'
import { Part, FilePicker, pal, useCanvas, useThemeTick } from './ui'

const NTREES = 200
function pathInfo(forest, x, ti) {
  let node = forest.trees[ti], h = 0
  while (node.f >= 0) { node = x[node.f] < node.thr ? node.left : node.right; h++ }
  return { h, size: node.size, adj: h + cFactor(node.size) }
}

function pickDefaults(d) {
  const byName = (re) => d.rows.findIndex((r) => re.test(r.p))
  let a = byName(/\/Cain\/Cain\.exe$/i); if (a < 0) a = byName(/\/Eraser\/Eraser\.exe$/i)
  if (a < 0) { let bi = d.targetIdx[0]; d.targetIdx.forEach((i) => { if (d.rows[i].rk.if < d.rows[bi].rk.if) bi = i }); a = bi }
  let b = byName(/\/ntdll\.dll$/i)
  if (b < 0) {
    const dl = []; d.rows.forEach((r, i) => { if (!d.isT[i] && /\.dll$/i.test(r.p)) dl.push(i) })
    const pool = dl.length ? dl : d.rows.map((r, i) => i).filter((i) => !d.isT[i])
    pool.sort((x, y) => Math.abs(d.rows[x].rk.if - d.N * 0.6) - Math.abs(d.rows[y].rk.if - d.N * 0.6)); b = pool[0]
  }
  return [a, b]
}

export default function A2({ d, cfg, tipRef }) {
  const [files, setFiles] = useState(() => pickDefaults(d))
  const [watch, setWatch] = useState(0)
  const [ti, setTi] = useState(0)
  const [cuts, setCuts] = useState(0)        // cuts shown so far
  const [alive, setAlive] = useState(d.n)
  const [playing, setPlaying] = useState(false)
  const [mode, setMode] = useState('tree')   // 'tree' | 'all'
  const tick = useThemeTick()
  const cv = useRef(), st = useRef({ k: 0, sweep: 1, fade: 1, done: true, pulse: 0 }), token = useRef(0)

  // a 200-tree forest on the sample, honouring the feature choices made in A1 and its seed
  const maskKey = cfg.mask.join('')
  const forest = useMemo(() => fitIsolationForest(d.X, { nTrees: NTREES, sampleSize: 256, seed: cfg.seed, featureMask: cfg.mask }), [d, maskKey, cfg.seed])

  const fa = files[watch], fb = files[1 - watch]
  const xa = d.X[fa]
  const trace = useMemo(() => isolationTrace(forest, xa, ti), [forest, fa, ti])
  const infoA = useMemo(() => pathInfo(forest, d.X[files[0]], ti), [forest, files, ti])
  const infoB = useMemo(() => pathInfo(forest, d.X[files[1]], ti), [forest, files, ti])

  // which two features does this tree cut on most along this file's path?
  const plane = useMemo(() => {
    const cnt = {}; trace.forEach((c) => { cnt[c.f] = (cnt[c.f] || 0) + 1 })
    const used = Object.keys(cnt).map(Number).sort((a, b) => cnt[b] - cnt[a] || a - b)
    const out = used.slice(0, 2)
    if (out.length < 2) {
      // fall back to the highest-variance enabled features
      const cand = d.features.map((f, j) => j).filter((j) => cfg.mask[j] && !out.includes(j)).sort((a, b) => d.uniq[b] - d.uniq[a] || a - b)
      while (out.length < 2 && cand.length) out.push(cand.shift())
      while (out.length < 2) out.push((out[0] + 1) % d.nf)
    }
    return out
  }, [trace, d])
  // each feature's sample values in order: the 2-D view plots rank order, so every dot has room
  const sorted = useMemo(() => d.features.map((f, j) => Float64Array.from(d.X, (x) => x[j]).sort()), [d])
  // the step on which each sample dot leaves the file's cell
  const death = useMemo(() => {
    const out = new Int16Array(d.n).fill(99)
    for (let i = 0; i < d.n; i++) {
      const x = d.X[i]
      for (let c = 0; c < trace.length; c++) {
        const left = x[trace[c].f] < trace[c].thr
        if ((left ? 'left' : 'right') !== trace[c].side) { out[i] = c; break }
      }
    }
    return out
  }, [trace, d])
  const aliveAfter = useMemo(() => {
    const a = [d.n]; for (let c = 0; c < trace.length; c++) { let s = 0; for (let i = 0; i < d.n; i++) if (death[i] > c) s++; a.push(s) } return a
  }, [death, trace])
  const jit = useMemo(() => Array.from({ length: d.n }, (_, i) => { const f = (v) => v - Math.floor(v); return [f(Math.sin(i * 12.9898) * 43758.5453), f(Math.sin(i * 78.233) * 12345.678)] }), [d])
  const L = useRef({}); L.current = { d, trace, plane, sorted, death, xa, jit, fa }

  const draw = (ctx, w, h) => {
    const P = pal(), S = st.current, Q = L.current
    const m = { l: 44, r: 12, t: 12, b: 34 }, pw = w - m.l - m.r, ph = h - m.t - m.b, n = Q.d.n
    const [ja, jb] = Q.plane, sa = Q.sorted[ja], sb = Q.sorted[jb]
    const lb = (arr, v) => { let lo = 0, hi = arr.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] < v) lo = mid + 1; else hi = mid } return lo }
    const ub = (arr, v) => { let lo = 0, hi = arr.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] <= v) lo = mid + 1; else hi = mid } return lo }
    const X = (f) => m.l + f * pw, Y = (f) => m.t + (1 - f) * ph
    const bx = (v) => X(lb(sa, v) / n), by = (v) => Y(lb(sb, v) / n)       // a cut or cell edge
    const dx = (v, u) => { const a = lb(sa, v), b = ub(sa, v); return X((a + (b - a) * u) / n) }
    const dy = (v, u) => { const a = lb(sb, v), b = ub(sb, v); return Y((a + (b - a) * u) / n) }
    ctx.strokeStyle = P.ink; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(m.l - .5, m.t); ctx.lineTo(m.l - .5, m.t + ph + .5); ctx.lineTo(m.l + pw, m.t + ph + .5); ctx.stroke()
    ctx.font = '500 11.5px "Inter Tight", sans-serif'; ctx.fillStyle = P.ink2
    ctx.textAlign = 'left'; ctx.textBaseline = 'alphabetic'
    ctx.fillText(Q.d.features[ja] + '  \u2192  (files spread out in rank order, low to high)', m.l, h - 8)
    ctx.save(); ctx.translate(13, m.t + ph); ctx.rotate(-Math.PI / 2); ctx.fillText(Q.d.features[jb] + '  \u2192', 0, 0); ctx.restore()
    const k = Math.min(S.k, Q.trace.length), nT = Q.trace.length
    const cell = k < nT ? Q.trace[k] : null
    let lo = null, hi = null
    if (cell) { lo = cell.lo; hi = cell.hi } else if (nT) { const c = Q.trace[nT - 1]; lo = c.lo.slice(); hi = c.hi.slice(); if (c.side === 'left') hi[c.f] = c.thr; else lo[c.f] = c.thr }
    // dots: still in the file's cell, then the ones already cut away (faint)
    for (let pass = 0; pass < 2; pass++) {
      ctx.beginPath()
      for (let i = 0; i < n; i++) {
        const dth = Q.death[i], dead = dth < k, cur = dth === k && k < nT
        if ((pass === 0) === (dead || cur)) continue
        const x = dx(Q.d.X[i][ja], Q.jit[i][0]), y = dy(Q.d.X[i][jb], Q.jit[i][1])
        ctx.rect(x - 1.1, y - 1.1, 2.2, 2.2)
      }
      ctx.globalAlpha = pass === 0 ? 0.55 : 0.07; ctx.fillStyle = P.dot; ctx.fill(); ctx.globalAlpha = 1
    }
    // the side being cut away fades out
    if (cell && S.fade > 0) {
      ctx.beginPath()
      for (let i = 0; i < n; i++) { if (Q.death[i] !== k) continue; ctx.rect(dx(Q.d.X[i][ja], Q.jit[i][0]) - 1.1, dy(Q.d.X[i][jb], Q.jit[i][1]) - 1.1, 2.2, 2.2) }
      ctx.globalAlpha = 0.55 * (1 - S.fade); ctx.fillStyle = P.dot; ctx.fill(); ctx.globalAlpha = 1
    }
    // earlier cuts
    for (let c = 0; c < Math.min(k, nT); c++) {
      const t = Q.trace[c]; if (t.f !== ja && t.f !== jb) continue
      ctx.strokeStyle = P.ink2; ctx.globalAlpha = 0.6; ctx.lineWidth = 1; ctx.beginPath()
      if (t.f === ja) { const x = Math.round(bx(t.thr)) + .5; ctx.moveTo(x, by(t.hi[jb])); ctx.lineTo(x, by(t.lo[jb])) }
      else { const y = Math.round(by(t.thr)) + .5; ctx.moveTo(bx(t.lo[ja]), y); ctx.lineTo(bx(t.hi[ja]), y) }
      ctx.stroke(); ctx.globalAlpha = 1
    }
    // the cell the file still lives in
    if (lo) {
      const x0 = bx(lo[ja]), x1 = hi[ja] >= sa[n - 1] ? X(1) : bx(hi[ja]), y1 = by(lo[jb]), y0 = hi[jb] >= sb[n - 1] ? Y(1) : by(hi[jb])
      ctx.strokeStyle = P.accent; ctx.lineWidth = 1.5; ctx.setLineDash([5, 3]); ctx.strokeRect(x0 + .5, y0 + .5, x1 - x0, y1 - y0); ctx.setLineDash([])
    }
    // the cut being drawn now sweeps across its cell
    if (cell && S.sweep > 0 && (cell.f === ja || cell.f === jb)) {
      const t = cell; ctx.strokeStyle = P.accent; ctx.lineWidth = 2.4; ctx.beginPath()
      if (t.f === ja) { const x0 = bx(t.lo[ja]), x1 = bx(t.thr), x = x0 + (x1 - x0) * S.sweep; ctx.moveTo(x, t.hi[jb] >= sb[n - 1] ? Y(1) : by(t.hi[jb])); ctx.lineTo(x, by(t.lo[jb])) }
      else { const y0 = t.hi[jb] >= sb[n - 1] ? Y(1) : by(t.hi[jb]), y1 = by(t.thr), y = y0 + (y1 - y0) * S.sweep; ctx.moveTo(bx(t.lo[ja]), y); ctx.lineTo(t.hi[ja] >= sa[n - 1] ? X(1) : bx(t.hi[ja]), y) }
      ctx.stroke()
    } else if (cell && S.sweep > 0) {
      ctx.font = 'italic 450 14px Newsreader, Georgia, serif'; ctx.fillStyle = P.accentInk; ctx.textAlign = 'right'; ctx.textBaseline = 'top'
      ctx.globalAlpha = Math.min(1, S.sweep * 2) * (1 - S.fade * 0.6)
      ctx.fillText('cut on ' + Q.d.features[cell.f] + ' (not in this view)', m.l + pw - 8, m.t + 8); ctx.globalAlpha = 1
    }
    // the file
    const fx = dx(Q.xa[ja], 0.5), fy = dy(Q.xa[jb], 0.5)
    if (S.done && S.pulse > 0) { ctx.strokeStyle = P.accent; ctx.globalAlpha = 1 - S.pulse; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(fx, fy, 6 + S.pulse * 22, 0, 6.2832); ctx.stroke(); ctx.globalAlpha = 1 }
    ctx.fillStyle = P.accent; ctx.beginPath(); ctx.arc(fx, fy, 5, 0, 6.2832); ctx.fill()
    ctx.strokeStyle = P.paper; ctx.lineWidth = 1.5; ctx.stroke()
    ctx.font = '600 12px "Inter Tight", sans-serif'; ctx.fillStyle = P.accentInk
    const nm = Q.d.name[Q.fa]; ctx.textAlign = fx > m.l + pw * 0.6 ? 'right' : 'left'; ctx.textBaseline = 'bottom'
    ctx.fillText(nm.length > 34 ? nm.slice(0, 33) + '\u2026' : nm, fx + (ctx.textAlign === 'right' ? -9 : 9), fy - 6)
  }
  const redraw = useCanvas(cv, draw, tick)

  // ---------- the animation: one cut at a time ----------
  const stop = () => { token.current++; AN.remove(st.current) }
  function run(fast) {
    stop(); const my = token.current, S = st.current
    const n = trace.length
    if (fast || !canAnim()) { S.k = n; S.sweep = 1; S.fade = 1; S.done = true; S.pulse = 0; setCuts(n); setAlive(aliveAfter[n]); setPlaying(false); redraw(); return }
    S.k = 0; S.sweep = 0; S.fade = 0; S.done = false; S.pulse = 0; setCuts(0); setAlive(d.n); setPlaying(true); redraw()
    let c = 0
    const step = () => {
      if (my !== token.current) return
      if (c >= n) {
        S.k = n; S.done = true; S.pulse = 0; redraw()
        AN({ targets: S, pulse: [0, 1], duration: 700, easing: 'easeOutQuart', update: redraw, complete: () => { if (my === token.current) { S.pulse = 0; redraw(); setPlaying(false) } } })
        return
      }
      S.k = c; S.sweep = 0; S.fade = 0
      AN({ targets: S, sweep: 1, duration: 300, easing: 'easeInOutQuad', update: redraw }).finished.then(() => {
        if (my !== token.current) return
        setCuts(c + 1)
        AN({ targets: S, fade: 1, duration: 240, easing: 'easeOutQuad', update: redraw }).finished.then(() => {
          if (my !== token.current) return
          setAlive(aliveAfter[c + 1]); c++; S.k = c; S.sweep = 0; S.fade = 0; step()
        })
      })
    }
    step()
  }
  const started = useRef(false)
  const wrap = useRef()
  useOnceInView(wrap, () => { started.current = true; run(); return null })
  useEffect(() => { if (started.current || !canAnim()) run(!started.current && !canAnim()); }, [fa, ti, forest, watch])
  useEffect(() => () => stop(), [])

  // ---------- histogram of path lengths over all trees ----------
  const [hist, setHist] = useState({ n: 0, a: null, b: null })
  const paths = useMemo(() => {
    const pa = new Float32Array(NTREES), pb = new Float32Array(NTREES)
    for (let t = 0; t < NTREES; t++) { pa[t] = pathInfo(forest, d.X[files[0]], t).adj; pb[t] = pathInfo(forest, d.X[files[1]], t).adj }
    return { pa, pb }
  }, [forest, files])
  const BINS = 18
  const binsAt = (cnt) => {
    const a = new Array(BINS).fill(0), b = new Array(BINS).fill(0)
    for (let t = 0; t < cnt; t++) { a[Math.min(BINS - 1, Math.max(0, Math.round(paths.pa[t]) - 1))]++; b[Math.min(BINS - 1, Math.max(0, Math.round(paths.pb[t]) - 1))]++ }
    return [a, b]
  }
  const finalBins = useMemo(() => binsAt(NTREES), [paths])
  const hmax = Math.max(1, ...finalBins[0], ...finalBins[1])
  const barsA = useRef([]), barsB = useRef([]), hdrv = useRef({ n: NTREES })
  const [ran, setRan] = useState(0)
  const hRun = useRef(0)
  function setBars(cnt) {
    const [a, b] = binsAt(Math.round(cnt))
    for (let i = 0; i < BINS; i++) {
      const ea = barsA.current[i], eb = barsB.current[i]
      if (ea) { const hh = (a[i] / hmax) * 150; ea.setAttribute('height', hh); ea.setAttribute('y', 160 - hh) }
      if (eb) { const hh = (b[i] / hmax) * 150; eb.setAttribute('height', hh); eb.setAttribute('y', 160 - hh) }
    }
  }
  function runAll() {
    setMode('all'); const my = ++hRun.current
    AN.remove(hdrv.current)
    const o = hdrv.current; o.n = 0; setBars(0); setRan(0)
    if (!canAnim()) { o.n = NTREES; setBars(NTREES); setRan(NTREES); return }
    let lastN = -1
    AN({ targets: o, n: NTREES, duration: 2600, easing: 'easeInOutQuad', update: () => { setBars(o.n); const r = Math.round(o.n); if (r !== lastN) { lastN = r; setRan(r) } },
      complete: () => { if (my === hRun.current) { setBars(NTREES); setRan(NTREES) } } })
  }
  useEffect(() => { // keep the histogram in step with the current files/forest
    AN.remove(hdrv.current); hdrv.current.n = mode === 'all' ? NTREES : 0
    setBars(mode === 'all' ? NTREES : 0); setRan(mode === 'all' ? NTREES : 0)
  }, [paths])
  useEffect(() => () => { AN.remove(hdrv.current) }, [])
  const meanAt = (arr, c) => { let s = 0; for (let t = 0; t < c; t++) s += arr[t]; return c ? s / c : 0 }

  // ---------- helpers ----------
  const quicks = (slot) => [
    { label: 'An evidence file', fn: () => pickT(slot) },
    { label: 'A system DLL', fn: () => pickDll(slot) },
  ]
  const tcur = useRef(0), dcur = useRef(0)
  const dlls = useMemo(() => { const o = []; d.rows.forEach((r, i) => { if (!d.isT[i] && /\.dll$/i.test(r.p)) o.push(i) }); if (!o.length) d.rows.forEach((r, i) => { if (!d.isT[i] && /\.(sys|exe)$/i.test(r.p)) o.push(i) }); return o }, [d])
  const setSlot = (slot, i) => setFiles((f) => { const g = f.slice(); g[slot] = i; return g })
  const pickT = (slot) => { const ts = d.targetIdx.filter((i) => i !== files[1 - slot]); tcur.current = (tcur.current + 1 + ((Math.random() * 3) | 0)) % ts.length; setSlot(slot, ts[tcur.current]) }
  const pickDll = (slot) => { dcur.current = (dcur.current + 1 + ((Math.random() * 5) | 0)) % dlls.length; setSlot(slot, dlls[dcur.current]) }

  const nameA = d.name[files[0]], nameB = d.name[files[1]]
  const lastCut = trace.length
  const cutRows = trace.slice(0, cuts)
  const verdictLine = infoA.h === infoB.h ? nameA + ' and ' + nameB + ' both took ' + infoA.h + ' cuts in this tree.'
    : (infoA.h < infoB.h ? nameA + ' isolated in ' + infoA.h + ' cuts; ' + nameB + ' needed ' + infoB.h + '.' : nameB + ' isolated in ' + infoB.h + ' cuts; ' + nameA + ' needed ' + infoA.h + '.')
  const mA = meanAt(paths.pa, ran), mB = meanAt(paths.pb, ran)
  const dFeat = (c) => d.features[c.f]

  return (
    <Part n="A2" title="Watch one tree isolate a file"
      intro="An Isolation Forest asks one question: how few random cuts does it take to fence this file off from everything else? Pick a file and watch a single tree cut the sample, one random line at a time, until only the file is left in its cell."
      note={<><b>Fewer cuts means stranger, which means more suspicious.</b> Ordinary files sit in crowds and need many cuts to separate. The animation uses every file in the sample for the dots; the tree itself was grown on 256 of them.</>}>
      <div ref={wrap}>
        <div className="lab-two">
          <FilePicker id="a2-a" d={d} value={files[0]} label="File 1" onPick={(i) => setSlot(0, i)} quicks={quicks(0)} />
          <FilePicker id="a2-b" d={d} value={files[1]} label="File 2 (to compare)" onPick={(i) => setSlot(1, i)} quicks={quicks(1)} />
        </div>
        <div className="lab-row lab-tools">
          <div className="fld"><span className="lab" id="a2-w">Watching</span>
            <div className="tabs" role="group" aria-labelledby="a2-w">
              {[0, 1].map((s) => <button key={s} type="button" aria-pressed={watch === s} onClick={() => setWatch(s)}>{d.name[files[s]].length > 24 ? d.name[files[s]].slice(0, 23) + '…' : d.name[files[s]]}</button>)}
            </div></div>
          <button type="button" className="btn lab-btn" onClick={() => run()}>{playing ? 'Restart' : 'Replay this tree'}</button>
          <button type="button" className="btn lab-btn" onClick={() => { setTi((t) => (t + 1) % NTREES) }}>Next tree <span className="mono">{ti + 1}/{NTREES}</span></button>
          <button type="button" className="btn lab-btn" onClick={runAll}>Run all {NTREES} trees</button>
        </div>
        <div className="lab-treegrid">
          <div className="fig lab-fig"><canvas ref={cv} className="lab-cv sq" role="img" aria-label={'Two-dimensional view of the sample showing the random cuts a tree makes around ' + d.name[fa]}></canvas></div>
          <div className="lab-cuts">
            <div className="depthc" aria-live="polite" aria-atomic="true">
              <b><Num value={cuts} fmt={String} /></b><span>cut{cuts === 1 ? '' : 's'}{cuts === lastCut && !playing ? ' — isolated' : ''}</span>
            </div>
            <div className="small">In this cell: <b className="mono"><Num value={alive} fmt={fmt} /></b> of {fmt(d.n)} sample files</div>
            <ol className="cutlog">
              {cutRows.map((c, i) => <CutRow key={ti + '-' + fa + '-' + i} i={i} text={<><b>{dFeat(c)}</b> {'< '}{fmtRaw(dFeat(c), rawOf(d, c.f, c.thr))} <em>{c.side === 'left' ? 'file is below' : 'file is above'}</em> <span className="mono">{fmt(aliveAfter[i + 1])} left</span></>} />)}
              {!cutRows.length ? <li className="idle">Cuts appear here.</li> : null}
            </ol>
          </div>
        </div>
        <p className="lab-verdict" aria-live="polite">{verdictLine} <span>Tree {ti + 1} of {NTREES}.</span>
          {(infoA.size > 1 || infoB.size > 1) ? <small> A cell that still holds several files is counted as if it had been cut further, so the path is slightly longer than the cut count.</small> : null}</p>
        <div className="lab-hist">
          <div className="lh-h"><span className="cap">All {NTREES} trees</span>
            <span className="small" aria-live="polite">{mode === 'all' ? ran + ' trees run · average path ' : 'Press “Run all ' + NTREES + ' trees” to fill the histogram. '}{mode === 'all' ? <><b className="a">{nameA} {mA.toFixed(1)}</b> vs <b>{nameB} {mB.toFixed(1)}</b> cuts</> : null}</span></div>
          <svg className="ch lab-hsvg" viewBox="0 0 420 200" role="img" aria-label={'Histogram of path lengths over ' + NTREES + ' trees for ' + nameA + ' and ' + nameB}>
            <line className="axis" x1="20" x2="410" y1="160.5" y2="160.5" />
            {Array.from({ length: BINS }, (_, i) => (
              <g key={i}>
                <rect ref={(e) => { barsA.current[i] = e }} x={22 + i * 21.6} width="9.5" y="160" height="0" fill="var(--accent)" />
                <rect ref={(e) => { barsB.current[i] = e }} x={22 + i * 21.6 + 10} width="9.5" y="160" height="0" fill="var(--ink)" opacity=".75" />
                <text x={22 + i * 21.6 + 9.75} y="177" textAnchor="middle">{i + 1}</text>
              </g>
            ))}
            <text x="215" y="196" textAnchor="middle">path length (cuts) → shorter means more isolated</text>
          </svg>
          <div className="legend"><span><i className="dotkey" style={{ background: 'var(--accent)' }}></i>{nameA}</span><span><i className="dotkey" style={{ background: 'var(--ink)' }}></i>{nameB}</span></div>
        </div>
      </div>
    </Part>
  )
}

function CutRow({ text, i }) {
  const r = useRef()
  useLayoutEffect(() => { if (r.current && canAnim()) AN({ targets: r.current, opacity: [0, 1], translateX: [-10, 0], duration: 320, easing: 'easeOutQuart' }) }, [])
  return <li ref={r}><span className="ix">{i + 1}</span><span>{text}</span></li>
}
