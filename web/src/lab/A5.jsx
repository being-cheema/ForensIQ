import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AN, canAnim } from '../lib/motion'
import { fmt } from '../lib/data'
import { Part, pal, useCanvas, useThemeTick, hideTip, showTip } from './ui'
import { utcDay, utcTime } from './data'

const DUR = 12000
const mlOf = (w) => (w < 520 ? 40 : 58)

export default function A5({ d, fit, tipRef }) {
  const tl = d.timeline, nb = tl.counts.length, T0 = tl.start, T1 = tl.start + nb * tl.binSec, SP = T1 - T0
  const tick = useThemeTick()
  const cv = useRef(), logRef = useRef(), anim = useRef(null), drv = useRef({ p: 1 }), selRef = useRef(null), dragRef = useRef(null)
  const refs = { sample: useRef(), ev: useRef(), full: useRef(), date: useRef() }
  const [playing, setPlaying] = useState(false)
  const [sel, setSel] = useState(null)
  const [done, setDone] = useState('')

  // sample files placed on the axis
  const items = useMemo(() => {
    const o = []
    for (let i = 0; i < d.n; i++) if (d.mtime[i] != null) o.push({ i, t: Math.min(T1 - 1, Math.max(T0, d.mtime[i])), raw: d.mtime[i], tg: d.isT[i] })
    o.sort((a, b) => a.t - b.t); return o
  }, [d])
  const before = useMemo(() => items.filter((x) => x.raw < T0), [items])
  // the busiest week for evidence, then the busiest day inside it
  const { peak, weekN } = useMemo(() => {
    const c = tl.targets.counts, W = 7; let best = -1, bs = 0, run = 0
    for (let i = 0; i < c.length; i++) { run += c[i]; if (i >= W) run -= c[i - W]; if (run > best) { best = run; bs = Math.max(0, i - W + 1) } }
    let bi = bs; for (let i = bs; i < Math.min(c.length, bs + W); i++) if (c[i] > c[bi]) bi = i
    return { peak: bi, weekN: best }
  }, [tl])
  const peakT = T0 + peak * tl.binSec, peakN = tl.targets.counts[peak]
  const cum = useMemo(() => { const c = new Float64Array(nb + 1); for (let i = 0; i < nb; i++) c[i + 1] = c[i] + tl.counts[i]; return c }, [tl])
  const totTargets = items.filter((x) => x.tg).length

  const L = useRef({}); L.current = { items, peak, nb, tl, d }
  const draw = (ctx, w, h) => {
    const P = pal(), Q = L.current, p = drv.current.p, play = anim.current && p < 1 && p > 0
    const ml = mlOf(w), mr = 10, pw = w - ml - mr, top = 14, laneH = 22, axisH = 22, mainH = h - top - laneH - axisH - 10
    const NC = Math.max(20, Math.min(Q.nb, Math.floor(pw / 2.5))), cw = pw / NC
    const colv = new Float64Array(NC), colt = new Float64Array(NC)
    for (let b = 0; b < Q.nb; b++) { const c = Math.min(NC - 1, Math.floor((b / Q.nb) * NC)); colv[c] += Q.tl.counts[b]; colt[c] += Q.tl.targets.counts[b] }
    let mx = 1; for (let c = 0; c < NC; c++) if (colv[c] > mx) mx = colv[c]
    const xp = ml + p * pw
    // histogram (square-root scale so quiet years stay visible)
    for (let c = 0; c < NC; c++) {
      const hh = Math.sqrt(colv[c] / mx) * mainH, x = ml + c * cw
      ctx.fillStyle = P.ink2; ctx.globalAlpha = (play && x > xp) ? 0.22 : 0.62
      ctx.fillRect(x, top + mainH - hh, Math.max(1, cw - 0.4), hh)
    }
    ctx.globalAlpha = 1
    // evidence lane
    const ly = top + mainH + 8
    ctx.fillStyle = P.rule; ctx.fillRect(ml, ly + laneH, pw, 1)
    for (let c = 0; c < NC; c++) {
      if (!colt[c]) continue
      const x = ml + c * cw, hh = Math.min(laneH, 7 + colt[c] * 5)
      ctx.fillStyle = P.accent; ctx.globalAlpha = (play && x > xp) ? 0.25 : 1; ctx.fillRect(x, ly + laneH - hh, Math.max(2, cw), hh)
    }
    ctx.globalAlpha = 1
    // axis ticks
    ctx.font = '500 11.5px "Inter Tight", sans-serif'; ctx.fillStyle = P.ink2; ctx.textBaseline = 'alphabetic'
    const yrs = SP > 86400 * 365 * 3
    const d0 = new Date(T0 * 1000), maxLab = Math.max(2, Math.floor(pw / 52)), step = yrs ? Math.max(1, Math.ceil(SP / (86400 * 365) / maxLab)) : Math.max(1, Math.ceil(SP / (86400 * 30.5) / maxLab))
    ctx.textAlign = 'center'
    let y = d0.getUTCFullYear(), m = yrs ? 0 : d0.getUTCMonth() + 1
    for (let guard = 0; guard < 80; guard++) {
      const t = Date.UTC(y, m, 1) / 1000
      if (t > T1) break
      if (t >= T0) { const x = ml + ((t - T0) / SP) * pw; ctx.fillRect(Math.round(x), ly + laneH, 1, 4); const lab = yrs ? String(y) : y + '-' + String(m + 1).padStart(2, '0'); if (x > ml + 14 && x < w - 16) ctx.fillText(lab, x, h - 4) }
      if (yrs) y += step; else { m += step; while (m > 11) { m -= 12; y++ } }
    }
    ctx.textAlign = 'left'; ctx.fillText('UTC', 2, h - 4)
    ctx.textAlign = 'right'; ctx.fillStyle = P.accentInk; ctx.fillText(ml > 50 ? 'evidence' : 'evid.', ml - 4, ly + laneH - 6); ctx.fillStyle = P.ink2; if (w > 520) ctx.fillText('files', ml - 4, top + 10)
    // brush
    const s = selRef.current
    if (s) {
      const xa = ml + ((Math.min(s.a, s.b) - T0) / SP) * pw, xb = ml + ((Math.max(s.a, s.b) - T0) / SP) * pw
      ctx.fillStyle = P.ink; ctx.globalAlpha = 0.09; ctx.fillRect(xa, top, Math.max(1, xb - xa), mainH + laneH + 8); ctx.globalAlpha = 1
      ctx.fillStyle = P.ink; ctx.fillRect(Math.round(xa), top, 1, mainH + laneH + 8); ctx.fillRect(Math.round(xb), top, 1, mainH + laneH + 8)
    }
    // annotation for the biggest evidence burst
    const px = ml + ((Q.peak + 0.5) / Q.nb) * pw
    ctx.strokeStyle = P.accent; ctx.lineWidth = 1; ctx.setLineDash([2, 3]); ctx.beginPath(); ctx.moveTo(Math.round(px) + .5, top + 14); ctx.lineTo(Math.round(px) + .5, ly + 2); ctx.stroke(); ctx.setLineDash([])
    const note = 'Most evidence touched on ' + utcDay(peakT)
    ctx.font = 'italic 450 14px Newsreader, Georgia, serif'; ctx.fillStyle = P.accentInk
    const tw = ctx.measureText(note).width, right = px + tw + 10 > w - 4
    ctx.textAlign = right ? 'right' : 'left'; ctx.fillText(note, right ? px - 6 : px + 6, top + 12)
    // passed marks while playing
    if (play) {
      const now = T0 + p * SP
      ctx.fillStyle = P.accent
      for (const it of Q.items) { if (!it.tg) continue; if (it.t > now) break; const x = ml + ((it.t - T0) / SP) * pw; ctx.beginPath(); ctx.arc(x, ly + laneH + 10, 2.4, 0, 6.2832); ctx.fill() }
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(xp, top - 4); ctx.lineTo(xp, ly + laneH + 4); ctx.stroke()
      ctx.fillStyle = P.accent; ctx.beginPath(); ctx.moveTo(xp - 5, top - 6); ctx.lineTo(xp + 5, top - 6); ctx.lineTo(xp, top + 2); ctx.closePath(); ctx.fill()
    }
  }
  const redraw = useCanvas(cv, draw, tick)

  // ---------- playback ----------
  const state = useRef({ ptr: 0, nS: 0, nT: 0, queue: [], tq: [] })
  function paint(p) {
    const S = state.current, now = T0 + p * SP
    while (S.ptr < items.length && items[S.ptr].t <= now) { const it = items[S.ptr++]; S.nS++; if (it.tg) { S.nT++; S.tq.push(it) } else S.queue.push(it) }
    const bpos = Math.min(nb, (now - T0) / tl.binSec), bi = Math.min(nb - 1, Math.floor(bpos))
    const full = cum[bi] + (bpos - bi) * tl.counts[bi]
    refs.sample.current.textContent = fmt(S.nS); refs.ev.current.textContent = String(S.nT); refs.full.current.textContent = fmt(Math.round(p >= 1 ? cum[nb] : full)); refs.date.current.textContent = p >= 1 ? '' : utcDay(now)
    // ticker: evidence always, ordinary files a few per frame
    let k = 0
    while (S.tq.length) addLine(S.tq.shift(), true)
    while (S.queue.length && k < 2) { addLine(S.queue.shift(), false); k++ }
    if (S.queue.length > 40) S.queue.splice(0, S.queue.length - 6)
    redraw()
  }
  function addLine(it, tg) {
    const box = logRef.current; if (!box) return
    const row = document.createElement('div'); row.className = 'lg' + (tg ? ' t' : '')
    const a = document.createElement('span'); a.className = 'li'; a.textContent = utcDay(it.raw)
    const b = document.createElement('span'); b.className = 'lp'; b.textContent = d.rows[it.i].p.trim()
    row.appendChild(a); row.appendChild(b)
    if (tg) { const t = document.createElement('span'); t.className = 'tag'; const i = document.createElement('i'); t.appendChild(i); t.appendChild(document.createTextNode('Evidence')); row.appendChild(t) }
    box.insertBefore(row, box.firstChild)
    while (box.children.length > 9) box.removeChild(box.lastChild)
    if (canAnim()) AN({ targets: row, opacity: [0, 1], translateY: [-14, 0], duration: tg ? 380 : 220, easing: 'easeOutQuart' })
  }
  function showTotals() {
    refs.sample.current.textContent = fmt(items.length); refs.ev.current.textContent = String(totTargets); refs.full.current.textContent = fmt(cum[nb]); refs.date.current.textContent = ''
  }
  function play() {
    if (anim.current && playing) { anim.current.pause(); setPlaying(false); return }
    if (anim.current && drv.current.p > 0 && drv.current.p < 1) { anim.current.play(); setPlaying(true); return }
    // fresh run
    AN.remove(drv.current); const S = state.current
    S.ptr = 0; S.nS = 0; S.nT = 0; S.queue = []; S.tq = []; if (logRef.current) logRef.current.innerHTML = ''
    drv.current.p = 0; setDone(''); setPlaying(true)
    if (!canAnim()) { drv.current.p = 1; S.ptr = items.length; S.nS = items.length; S.nT = totTargets; showTotals(); redraw(); setPlaying(false); setDone(summary()); return }
    paint(0)
    anim.current = AN({ targets: drv.current, p: 1, duration: DUR, easing: 'linear', update: () => paint(drv.current.p),
      complete: () => { drv.current.p = 1; S.queue = []; S.tq = []; showTotals(); redraw(); setPlaying(false); anim.current = null; setDone(summary()) } })
  }
  const summary = () => 'Replay finished: ' + fmt(items.length) + ' sample files touched, ' + totTargets + ' of them evidence.'
  useEffect(() => { showTotals(); return () => { if (anim.current) anim.current.pause(); AN.remove(drv.current) } }, [])
  useEffect(() => { // disk changed: reset
    if (anim.current) { anim.current.pause(); anim.current = null }
    AN.remove(drv.current); drv.current.p = 1; setPlaying(false); setDone(''); selRef.current = null; setSel(null)
    if (logRef.current) logRef.current.innerHTML = ''
    showTotals(); redraw()
  }, [d])

  // ---------- brushing ----------
  const tOf = (e) => { const r = cv.current.getBoundingClientRect(), ml = mlOf(r.width), pw = r.width - ml - 10; return T0 + Math.max(0, Math.min(1, (e.clientX - r.left - ml) / pw)) * SP }
  const commit = useRef(0)
  function down(e) { cv.current.setPointerCapture && cv.current.setPointerCapture(e.pointerId); const t = tOf(e); dragRef.current = { a: t, x: e.clientX, moved: false } }
  function move(e) {
    const g = dragRef.current
    if (!g) {
      const r = cv.current.getBoundingClientRect(), t = tOf(e)
      const bi = Math.min(nb - 1, Math.floor((t - T0) / tl.binSec))
      if (e.clientY - r.top < r.height - 28 && bi >= 0) showTip(tipRef.current, [{ b: utcDay(T0 + bi * tl.binSec) }, fmt(tl.counts[bi]) + ' files modified that day (full disk)', tl.targets.counts[bi] ? tl.targets.counts[bi] + ' of them evidence' : 'no evidence'], e.clientX, e.clientY)
      else hideTip(tipRef.current)
      return
    }
    if (!g.moved && Math.abs(e.clientX - g.x) < 4) return
    g.moved = true; hideTip(tipRef.current)
    selRef.current = { a: g.a, b: tOf(e) }; redraw()
    const now = performance.now(); if (now - commit.current > 110) { commit.current = now; setSel({ ...selRef.current }) }
  }
  function up() {
    const g = dragRef.current; dragRef.current = null; if (!g) return
    if (!g.moved) { selRef.current = null; setSel(null); redraw(); return }
    setSel(selRef.current ? { ...selRef.current } : null)
  }
  function key(e) {
    const step = SP * 0.03
    if (e.key === 'Escape') { selRef.current = null; setSel(null); redraw(); return }
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const s = selRef.current ? { ...selRef.current } : { a: T0 + SP * 0.48, b: T0 + SP * 0.52 }
    const dir = e.key === 'ArrowLeft' ? -1 : 1
    if (e.shiftKey) s.b = Math.max(T0, Math.min(T1, s.b + dir * step)); else { s.a = Math.max(T0, Math.min(T1, s.a + dir * step)); s.b = Math.max(T0, Math.min(T1, s.b + dir * step)) }
    selRef.current = s; setSel(s); redraw()
  }
  function jump() { const s = { a: peakT - 3 * tl.binSec, b: peakT + 4 * tl.binSec }; selRef.current = s; setSel(s); redraw() }
  function clear() { selRef.current = null; setSel(null); redraw() }
  useEffect(() => { selRef.current = sel; redraw() }, [sel])

  const inSel = useMemo(() => {
    if (!sel) return null
    const a = Math.min(sel.a, sel.b), b = Math.max(sel.a, sel.b)
    return items.filter((x) => x.raw >= a && x.raw <= b).sort((p, q) => fit.ranks[p.i] - fit.ranks[q.i])
  }, [sel, items, fit])
  const selEv = inSel ? inSel.filter((x) => x.tg).length : 0
  const modelName = { if: 'Isolation Forest', lof: 'LOF', svm: 'One-Class SVM (saved ranks)' }[fit.cfg.model]

  return (
    <Part n="A5" title="Replay the disk's timeline"
      intro="Every file carries the date it was last modified. Press play and a playhead sweeps across the years the disk covers; files from the sample flash past as it reaches them, and the evidence lights up in red. Drag across the plot to hold a stretch of time still and see what the model made of it."
      note={<><b>All dates and times are UTC.</b> The bars count every file on the full disk (square-root scale); the live log and the model ranks come from the 2,000-file sample. {before.length ? <>{before.length} sample file{before.length === 1 ? '' : 's'} ({before.filter((x) => x.tg).length} evidence) carry modified dates before the plotted window and appear at its left edge. </> : null}The red marker shows <b>{utcDay(peakT)}</b>, the busiest day in the week with the most evidence ({weekN} evidence files on the full disk).</>}>
      <div className="a5-bar">
        <button type="button" className="btn lab-btn pri" onClick={play}>{playing ? 'Pause' : (drv.current.p > 0 && drv.current.p < 1) ? 'Resume' : 'Play the timeline'}</button>
        <button type="button" className="btn lab-btn" onClick={jump}>Jump to the evidence burst</button>
        {sel ? <button type="button" className="btn lab-btn" onClick={clear}>Clear selection</button> : null}
        <div className="a5-cnt" aria-hidden="true">
          <span><b className="num" ref={refs.sample}></b> sample files touched</span>
          <span className="hot"><b className="num" ref={refs.ev}></b> evidence</span>
          <span><b className="num" ref={refs.full}></b> on the full disk</span>
          <span className="mono" ref={refs.date}></span>
        </div>
      </div>
      <div className="fig lab-fig">
        <canvas ref={cv} className="lab-cv tl" tabIndex={0} role="application" aria-label="Timeline of file modification dates. Drag, or use the left and right arrow keys, to select a range; shift with the arrows resizes it; Escape clears it."
          onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} onPointerLeave={() => hideTip(tipRef.current)} onKeyDown={key}></canvas>
      </div>
      <span className="sr" aria-live="polite">{done}</span>
      <div className="a5-two">
        <div>
          <h4 className="cap">Live log</h4>
          <div className="lab-log" ref={logRef} aria-hidden="true"></div>
          <p className="small">Files from the sample, in modified-time order, as the playhead passes them.</p>
        </div>
        <div>
          <h4 className="cap">Held range</h4>
          {!inSel ? <p className="small">Drag across the plot above, or use the arrow keys when it has focus. The files inside the range are listed here with the rank {modelName} gives them in the sample (set in A1).</p> : (
            <>
              <p className="small" aria-live="polite"><b>{fmt(inSel.length)}</b> sample files from {utcDay(Math.min(sel.a, sel.b))} to {utcDay(Math.max(sel.a, sel.b))} (UTC), <b className={selEv ? 'hi' : ''}>{selEv}</b> evidence. Best rank in range: {inSel.length ? '#' + fit.ranks[inSel[0].i] : 'none'}.</p>
              <ol className="a5-sel">
                {inSel.slice(0, 80).map((x) => (
                  <li key={x.i} className={x.tg ? 't' : ''}><span className="rk mono">#{fit.ranks[x.i]}</span><span className="nm"><b>{d.name[x.i]}</b><small className="mono">{utcDay(x.raw)} {utcTime(x.raw)}</small></span>{x.tg ? <span className="tag"><i></i>Evidence</span> : null}</li>
                ))}
                {!inSel.length ? <li className="idle small">No sample file was modified in this range.</li> : null}
              </ol>
              {inSel.length > 80 ? <p className="small">Showing the 80 best-ranked of {fmt(inSel.length)}.</p> : null}
            </>
          )}
        </div>
      </div>
    </Part>
  )
}
