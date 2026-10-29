import { useEffect, useMemo, useRef, useState } from 'react'
import { AN, canAnim } from '../lib/motion'
import { fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import { GROUPS, GROUP_NAMES, PRESETS, sameMask, recallAt } from './data'
import { MODEL_COL, Part, pal, showTip, hideTip, useCanvas, useThemeTick } from './ui'

const NCOL = 10
const yOf = (rank, n) => Math.sqrt((rank - 1) / Math.max(1, n - 1))
const ELL = (ctx, s, w) => { if (ctx.measureText(s).width <= w) return s; while (s.length > 3 && ctx.measureText(s + '…').width > w) s = s.slice(0, -1); return s + '…' }

export default function A1({ d, fit, cfg, setCfg, pct, tipRef, history, planted }) {
  const cv = useRef(), hover = useRef(-1)
  const dots = useRef(null)           // [{y}] animated
  const jit = useMemo(() => Array.from({ length: d.n }, (_, i) => { const h = Math.sin(i * 12.9898 + 78.233) * 43758.5453; return (h - Math.floor(h)) - 0.5 }), [d])
  const tick = useThemeTick()
  const [hint, setHint] = useState('Hover or focus a feature to read what it measures.')
  const ranks = fit.ranks, n = d.n
  const res = recallAt(ranks, d.isT, pct)
  const mkey = MODEL_COL[cfg.model]

  // animated y positions (FLIP-style: current -> new, staggered by new rank)
  if (!dots.current || dots.current.length !== n) dots.current = Array.from({ length: n }, (_, i) => ({ y: yOf(ranks[i], n) }))
  const live = useRef({})
  live.current = { d, ranks, res, pct, planted, cfg }

  const draw = (ctx, w, h) => {
    const P = pal(), L = live.current, D = L.d, R = dots.current
    const gut = w < 560 ? Math.min(118, w * 0.34) : 190
    const px0 = 40, px1 = w - gut - 6, top = 14, bot = h - 26, ph = bot - top
    const colW = (px1 - px0) / NCOL
    ctx.font = '500 11px "Inter Tight", sans-serif'
    // axis
    ctx.strokeStyle = P.ink; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(px0 - 6.5, top); ctx.lineTo(px0 - 6.5, bot); ctx.stroke()
    ctx.fillStyle = P.ink2; ctx.textAlign = 'right'; ctx.textBaseline = 'middle'
    const kk = Math.max(1, Math.round(L.pct * n))
    const ticks = [[1, '1'], [Math.round(n * 0.1), '10%'], [Math.round(n * 0.25), '25%'], [Math.round(n * 0.5), '50%'], [n, '100%']]
    ticks.forEach(([r, s]) => { const y = top + yOf(r, n) * ph; ctx.fillText(s, px0 - 12, Math.min(bot - 4, Math.max(top + 4, y))); ctx.fillRect(px0 - 9, Math.round(y), 3, 1) })
    // column labels
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = P.ink2
    for (let c = 0; c < NCOL; c++) ctx.fillText(c === NCOL - 1 ? NCOL + '+' : String(c + 1), px0 + (c + 0.5) * colW, h - 8)
    ctx.textAlign = 'left'; ctx.fillText('depth', 2, h - 8)
    // budget line
    const yb = top + yOf(kk, n) * ph
    ctx.save(); ctx.strokeStyle = P.accent; ctx.lineWidth = 1; ctx.setLineDash([4, 3]); ctx.beginPath(); ctx.moveTo(px0 - 6, yb + .5); ctx.lineTo(px1 + 4, yb + .5); ctx.stroke(); ctx.restore()
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle'
    const bl = 'budget \u00b7 ' + fmt(kk) + ' files', bw = ctx.measureText(bl).width
    ctx.fillStyle = P.sheet; ctx.globalAlpha = 0.85; ctx.fillRect(px0 - 2, yb + 3, bw + 8, 15); ctx.globalAlpha = 1
    ctx.fillStyle = P.accentInk; ctx.fillText(bl, px0 + 2, yb + 10.5)
    // ordinary dots
    const mc = P[MODEL_COL[L.cfg.model]]
    const pos = (i) => ({ x: px0 + (Math.min(NCOL, D.depth[i]) - 1 + 0.5 + jit[i] * 0.86) * colW, y: top + R[i].y * ph })
    ctx.globalAlpha = 0.4; ctx.fillStyle = P.dot
    ctx.beginPath()
    for (let i = 0; i < n; i++) { if (D.isT[i] || L.ranks[i] <= kk) continue; const q = pos(i); ctx.rect(q.x - 1, q.y - 1, 2, 2) }
    ctx.fill()
    ctx.globalAlpha = 0.85; ctx.fillStyle = mc; ctx.beginPath()
    for (let i = 0; i < n; i++) { if (D.isT[i] || L.ranks[i] > kk) continue; const q = pos(i); ctx.rect(q.x - 1.25, q.y - 1.25, 2.5, 2.5) }
    ctx.fill(); ctx.globalAlpha = 1
    // evidence
    const tl = []
    for (const i of D.targetIdx) {
      const q = pos(i), caught = L.ranks[i] <= kk
      ctx.beginPath(); ctx.arc(q.x, q.y, 4.2, 0, 6.2832)
      ctx.fillStyle = caught ? P.accent : P.sheet; ctx.fill()
      ctx.lineWidth = 1.6; ctx.strokeStyle = caught ? P.accent : P.accent; ctx.globalAlpha = caught ? 1 : 0.75; ctx.stroke(); ctx.globalAlpha = 1
      tl.push({ i, x: q.x, y: q.y })
    }
    if (hover.current >= 0) { const q = pos(hover.current); ctx.strokeStyle = P.ink; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(q.x, q.y, 7, 0, 6.2832); ctx.stroke() }
    // labels for the best-ranked evidence, stacked in the gutter
    const best = tl.slice().sort((a, b) => L.ranks[a.i] - L.ranks[b.i]).slice(0, w < 560 ? 4 : 6).sort((a, b) => a.y - b.y)
    let last = -99; const lx = px1 + 8
    ctx.font = '500 11.5px "Inter Tight", sans-serif'; ctx.textBaseline = 'middle'
    best.forEach((t) => {
      let ly = Math.max(t.y, last + 14); if (ly > bot) ly = bot; last = ly
      ctx.strokeStyle = P.accent; ctx.globalAlpha = 0.45; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(t.x + 5, t.y); ctx.lineTo(lx - 3, ly); ctx.stroke(); ctx.globalAlpha = 1
      ctx.fillStyle = P.ink; ctx.textAlign = 'left'
      ctx.fillText(ELL(ctx, D.name[t.i], gut - 44), lx, ly)
      ctx.fillStyle = P.accentInk; ctx.textAlign = 'right'; ctx.fillText('#' + L.ranks[t.i], w - 2, ly)
    })
    // planted file from the "plant your own" part
    if (L.planted && L.cfg.model === 'if') {
      const y = top + yOf(L.planted.sampleRank, n) * ph, x = px0 + NCOL * colW + 0, s = 6
      ctx.fillStyle = P.accent; ctx.beginPath(); ctx.moveTo(x - 2, y); ctx.lineTo(x - 2 - s, y - s); ctx.lineTo(x - 2 - 2 * s, y); ctx.lineTo(x - 2 - s, y + s); ctx.closePath(); ctx.fill()
      ctx.strokeStyle = P.accent; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(px0 - 6, y + .5); ctx.lineTo(x - 2 - 2 * s, y + .5); ctx.stroke()
      ctx.fillStyle = P.accentInk; ctx.textAlign = 'right'; ctx.font = '600 11px "Inter Tight", sans-serif'; ctx.fillText('your file (planted below)', x - 2 - 2 * s - 6, y - 8)
    }
  }
  const redraw = useCanvas(cv, draw, tick)

  // animate when ranks change
  const first = useRef(true)
  useEffect(() => {
    const R = dots.current
    AN.remove(R)
    const target = ranks.map((r) => yOf(r, n))
    if (first.current || !canAnim()) { first.current = false; R.forEach((o, i) => { o.y = target[i] }); redraw(); return }
    // evidence moves first so the eye follows it
    AN({ targets: R, y: (el, i) => target[i], duration: 640, easing: 'easeOutQuart',
      delay: (el, i) => (d.isT[i] ? 0 : 40 + Math.min(260, ranks[i] / n * 320)), update: redraw, complete: redraw })
    const t = setTimeout(() => { R.forEach((o, i) => { o.y = target[i] }); redraw() }, 1200)
    return () => { clearTimeout(t); AN.remove(R) }
  }, [fit])
  useEffect(() => { redraw() }, [pct, planted])

  function hit(e) {
    const c = cv.current, r = c.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top
    const w = r.width, h = r.height, gut = w < 560 ? Math.min(118, w * 0.34) : 190, px0 = 40, px1 = w - gut - 6, top = 14, ph = h - 26 - top, colW = (px1 - px0) / NCOL
    let best = -1, bd = 1e9
    for (let i = 0; i < n; i++) {
      const x = px0 + (Math.min(NCOL, d.depth[i]) - 1 + 0.5 + jit[i] * 0.86) * colW, y = top + dots.current[i].y * ph
      const dx = x - mx, dy = y - my, dd = (dx * dx + dy * dy) * (d.isT[i] ? 0.35 : 1)
      if (dd < bd) { bd = dd; best = i }
    }
    return bd < 12 * 12 ? best : -1
  }
  function move(e) {
    const i = hit(e); hover.current = i
    if (i < 0) hideTip(tipRef.current)
    else showTip(tipRef.current, [d.isT[i] ? { b: d.rows[i].t } : null, d.rows[i].p.trim(), 'rank ' + ranks[i] + ' of ' + fmt(n) + ' in this sample · full-disk rank ' + fmt(d.rows[i].rk.if) + ' (saved IF)'].filter(Boolean), e.clientX, e.clientY)
    redraw()
  }
  const leave = () => { hover.current = -1; hideTip(tipRef.current); redraw() }

  // controls
  const flip = (j) => setCfg((c) => { const m = c.mask.slice(); m[j] = !m[j]; return { ...c, mask: m } })
  const flipGroup = (g) => setCfg((c) => {
    const idx = GROUPS[g].map((f) => d.features.indexOf(f)).filter((j) => j >= 0)
    const all = idx.every((j) => c.mask[j]); const m = c.mask.slice(); idx.forEach((j) => { m[j] = !all }); return { ...c, mask: m }
  })
  const nOn = cfg.mask.filter(Boolean).length
  const spark = useMemo(() => history.map((h) => recallAt(h.ranks, d.isT, pct).recall), [history, pct, d])

  return (
    <Part n="A1" title="Run the model yourself"
      intro="Every dot is a real file from the sample, placed by how suspicious the model finds it: the most suspicious files sit at the top. Switch features off, change the model or reroll its randomness, and watch the evidence (the red rings) rise or sink."
      note={<>Each change <b>refits the model from scratch</b> in your browser, on the sample, in a few milliseconds. The vertical axis stretches the top of the ranking so the files near the budget line stay readable.</>}>
      <div className="a1-grid">
      <div className="lab-ctl a1-ctl">
        <div className="lab-row">
          <div className="fld"><span className="lab" id="a1-pre">Preset</span>
            <div className="tabs" role="group" aria-labelledby="a1-pre">
              {PRESETS.map(([name, fn]) => <button key={name} type="button" aria-pressed={sameMask(cfg.mask, fn(d))} onClick={() => setCfg((c) => ({ ...c, mask: fn(d) }))}>{name}</button>)}
            </div></div>
          <div className="fld"><span className="lab" id="a1-mod">Model</span>
            <div className="tabs" role="group" aria-labelledby="a1-mod">
              {[['if', 'Isolation Forest'], ['lof', 'LOF'], ['svm', 'One-Class SVM (saved)']].map(([k, t]) => <button key={k} type="button" aria-pressed={cfg.model === k} style={{ '--c': 'var(--' + MODEL_COL[k] + ')' }} onClick={() => setCfg((c) => ({ ...c, model: k }))}>{t}</button>)}
            </div></div>
        </div>
        <div className="lab-row">
          <div className="lrange"><label htmlFor="a1-trees">Trees</label>
            <input id="a1-trees" type="range" min="25" max="400" step="25" value={cfg.nTrees} disabled={cfg.model === 'svm' ? false : false} onChange={(e) => setCfg((c) => ({ ...c, nTrees: +e.target.value }))} aria-valuetext={cfg.nTrees + ' trees'} />
            <output htmlFor="a1-trees">{cfg.nTrees}</output></div>
          <div className="lrange"><label htmlFor="a1-k">LOF neighbours (k)</label>
            <input id="a1-k" type="range" min="5" max="100" step="5" value={cfg.k} onChange={(e) => setCfg((c) => ({ ...c, k: +e.target.value }))} aria-valuetext={cfg.k + ' neighbours'} />
            <output htmlFor="a1-k">{cfg.k}</output></div>
          <button type="button" className="btn lab-btn" onClick={() => setCfg((c) => ({ ...c, seed: (Math.random() * 1e6) | 0 }))}>Reroll seed <span className="mono">{cfg.seed}</span></button>
        </div>
        {cfg.model === 'svm' ? <p className="small">One-Class SVM is not run live. These are its saved full-disk ranks for the sample files, so the feature toggles do not move them. Trees and the seed still drive the Isolation Forest used in A2 and A3.</p> : null}
        {cfg.model === 'if' ? <p className="small">LOF neighbours has no effect while the Isolation Forest is selected.</p> : cfg.model === 'lof' ? <p className="small">Trees and the seed do not change LOF; they still drive the Isolation Forest used in A2 and A3.</p> : null}
        <div className="lab-feats" role="group" aria-label="Features used by the model">
          {GROUP_NAMES.map((g) => {
            const idx = GROUPS[g].map((f) => d.features.indexOf(f)).filter((j) => j >= 0)
            const on = idx.filter((j) => cfg.mask[j]).length
            return (
              <fieldset key={g} className="lf-g">
                <legend><button type="button" className="lnk" onClick={() => flipGroup(g)} aria-label={'Toggle all ' + g + ' features'}>{g}</button> <small>{on}/{idx.length}</small></legend>
                <div className="lf-wrap">{idx.map((j) => {
                  const f = d.features[j]
                  return (
                    <label key={f} className="lf" title={d.info[f]} onMouseEnter={() => setHint(f + ': ' + d.info[f])} onFocus={() => setHint(f + ': ' + d.info[f])}>
                      <input type="checkbox" checked={cfg.mask[j]} onChange={() => flip(j)} /><span className="mono">{f}</span>
                    </label>
                  )
                })}</div>
              </fieldset>
            )
          })}
        </div>
        <p className="small lab-hint" aria-live="polite">{hint}</p>
        {nOn === 0 ? <p className="small warnline">Switch at least one feature on; the model needs something to look at.</p> : null}
      </div>
      <div className="a1-out">
      <div className="fig lab-fig">
        <canvas ref={cv} className="lab-cv" onPointerMove={move} onPointerDown={move} onPointerLeave={leave} role="img"
          aria-label={'Rank chart of ' + fmt(n) + ' sample files; ' + res.hit + ' of ' + res.tot + ' evidence files are inside the top ' + pc(pct) + '.'}></canvas>
      </div>
      <div className="legend"><span><i className="dotkey" style={{ background: 'var(--dot)' }}></i>file</span>
        <span><i className="dotkey" style={{ background: 'var(--' + mkey + ')' }}></i>inside the budget</span>
        <span><i className="dotkey ring" style={{ background: 'var(--accent)' }}></i>evidence caught</span>
        <span><i className="dotkey ring"></i>evidence missed</span></div>
      <div className="readout lab-read" aria-live="polite" aria-atomic="true">
        <div className="hot"><b><Num value={res.hit} fmt={String} /><small>/ {res.tot}</small></b><span className="l">evidence in the top {pc(pct)}</span></div>
        <div><b><Num value={res.recall} fmt={(v) => pc(v, 0)} /></b><span className="l">of the sample's evidence caught</span></div>
        <div><b><Num value={res.k} fmt={fmt} /></b><span className="l">files the examiner reads</span></div>
        <div><b><Num value={medianTarget(d, ranks)} fmt={fmt} /></b><span className="l">median evidence rank</span></div>
        <div><b>{fit.ms < 10 ? fit.ms.toFixed(1) : Math.round(fit.ms)}<small>ms</small></b><span className="l">to refit {cfg.model === 'lof' ? 'LOF' : cfg.model === 'svm' ? 'the forest' : 'the forest'}</span></div>
      </div>
      <Spark vals={spark} />
      </div>
      </div>
    </Part>
  )
}

function medianTarget(d, ranks) {
  const r = d.targetIdx.map((i) => ranks[i]).sort((a, b) => a - b)
  return r.length ? r[(r.length - 1) >> 1] : 0
}

function Spark({ vals }) {
  const ref = useRef()
  const W = 300, H = 46, n = vals.length
  const pts = vals.map((v, i) => [n > 1 ? 6 + (i / (n - 1)) * (W - 12) : W / 2, H - 6 - v * (H - 12)])
  useEffect(() => {
    const el = ref.current && ref.current.querySelector('.sp-last'); if (!el || !canAnim()) return
    AN.remove(el); AN({ targets: el, r: [1, 4.5, 3.2], duration: 560, easing: 'easeOutQuart' })
  }, [vals.length, vals[vals.length - 1]])
  return (
    <div className="spark" ref={ref}>
      <span className="small">Recall over your last {Math.min(10, n)} configuration{n === 1 ? '' : 's'}</span>
      <svg viewBox={'0 0 ' + W + ' ' + H} role="img" aria-label={'Recall history: ' + vals.map((v) => Math.round(v * 100) + '%').join(', ')}>
        <line x1="0" x2={W} y1={H - 6} y2={H - 6} stroke="var(--rule)" />
        {n > 1 ? <polyline points={pts.map((p) => p.join(',')).join(' ')} fill="none" stroke="var(--ink)" strokeWidth="1.25" /> : null}
        {pts.map((p, i) => i < n - 1 ? <circle key={i} cx={p[0]} cy={p[1]} r="2" fill="var(--ink)" /> : <circle key={i} className="sp-last" cx={p[0]} cy={p[1]} r="3.2" fill="var(--accent)" />)}
      </svg>
      <span className="mono sp-val">{n ? Math.round(vals[n - 1] * 100) + '%' : ''}</span>
    </div>
  )
}
