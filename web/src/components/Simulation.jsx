import { useEffect, useMemo, useRef, useState } from 'react'
import { AN, RM } from '../lib/motion'
import { MODELS, MVAR, css, fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import Section from '../lib/Section'

const smooth = (a, b, t) => { const x = Math.min(1, Math.max(0, (t - a) / (b - a))); return x * x * (3 - 2 * x) }
function mixc(c1, c2, f) {
  function h(c) { c = c.replace('#', ''); if (c.length === 3) c = c.split('').map((z) => z + z).join(''); return [0, 2, 4].map((i) => parseInt(c.substr(i, 2), 16)) }
  const a = h(c1), b = h(c2); return 'rgb(' + a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(',') + ')'
}
function layoutPts(im) {
  const s = im.sample, xs = s.map((p) => p.x).sort((a, b) => a - b), ys = s.map((p) => p.y).sort((a, b) => a - b)
  const q = (a, f) => a[Math.floor(f * (a.length - 1))]
  const x0 = q(xs, .01), x1 = q(xs, .99), y0 = q(ys, .01), y1 = q(ys, .99)
  let seed = 11
  return s.map((p, i) => {
    seed = (seed * 9301 + 49297) % 233280
    return { nx: Math.min(1, Math.max(0, (p.x - x0) / (x1 - x0 || 1))), ny: Math.min(1, Math.max(0, (p.y - y0) / (y1 - y0 || 1))), r: p.r, t: p.t, p: p.p, o: seed / 233280, i }
  })
}
const PHASES = [['1 Index', 'read the MFT'], ['2 Score', 'model ranks files'], ['3 Triage', 'cut to budget'], ['4 Evidence', 'caught or missed']]

export default function Simulation(p) {
  const im = p.im, cvRef = useRef(), scrubRef = useRef(), tl = useRef(null)
  const sim = useRef({ reveal: 1, score: 1, tri: 1, ev: 1 }), live = useRef({}), colors = useRef(null), dprRef = useRef(1), hover = useRef(-1)
  const [phase, setPhase] = useState(3)
  const [playing, setPlaying] = useState(false)
  const [atEnd, setAtEnd] = useState(true)
  const P = useMemo(() => layoutPts(im), [p.img])
  const tmap = useMemo(() => { const o = {}; im.targets.forEach((t) => { o[t.name] = t }); return o }, [p.img])
  live.current = { P, tmap, K: p.K, N: im.files, m: p.m, sel: p.sel, files: im.files }
  const targets = im.targets, mname = MODELS[p.m]
  const caught = targets.filter((t) => t.ranks[mname] <= p.K).length

  function refreshColors() {
    colors.current = { dot: css('--dot'), ok: css('--ok'), bad: css('--bad'), bg: css('--surface'), ink: css('--ink'), m: MVAR.map(css) }
  }
  function draw() {
    const cv = cvRef.current; if (!cv) return
    if (!colors.current) refreshColors()
    const ctx = cv.getContext('2d'), L = live.current, s = sim.current, c = colors.current, dpr = dprRef.current
    const w = cv.width, h = cv.height, k = L.K, N = L.N, m = L.m, pad = 18 * dpr, P = L.P
    ctx.clearRect(0, 0, w, h)
    const reveal = s.reveal, score = s.score, tri = s.tri, ev = s.ev, mc = c.m[m]
    let i, q, x, y, flagged, heat, col, rad, a
    for (i = 0; i < P.length; i++) {
      q = P[i]; if (q.o > reveal * 1.02 && reveal < 1) continue
      x = pad + q.nx * (w - 2 * pad); y = pad + q.ny * (h - 2 * pad)
      flagged = q.r[m] <= k
      heat = Math.max(0, 1 - (q.r[m] / N) / 0.15) * score
      col = mixc(c.dot, mc, Math.max(heat, flagged ? tri : 0)); a = flagged ? 1 : 1 - 0.78 * tri
      rad = (2.1 + heat * 1.3 + (flagged ? tri * 1.2 : 0)) * dpr
      ctx.globalAlpha = Math.min(1, a * (reveal < 1 ? 0.35 + 0.65 * reveal : 1))
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, rad, 0, 6.2832); ctx.fill()
    }
    ctx.globalAlpha = 1
    if (ev > 0) {
      for (i = 0; i < P.length; i++) {
        q = P[i]; if (!q.t) continue
        const tg = L.tmap[q.t]; if (!tg) continue
        x = pad + q.nx * (w - 2 * pad); y = pad + q.ny * (h - 2 * pad)
        const ok = tg.ranks[MODELS[m]] <= k, r = (5 + 6 * ev) * dpr * (L.sel === q.t ? 1.35 : 1)
        ctx.lineWidth = 2.2 * dpr; ctx.globalAlpha = ev
        ctx.fillStyle = c.bg; ctx.beginPath(); ctx.arc(x, y, r + 1.5 * dpr, 0, 6.2832); ctx.fill()
        ctx.strokeStyle = ok ? c.ok : c.bad; ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.stroke()
        if (ok) { ctx.fillStyle = c.ok; ctx.beginPath(); ctx.arc(x, y, r * 0.45, 0, 6.2832); ctx.fill() }
        else { ctx.beginPath(); ctx.moveTo(x - r * .5, y - r * .5); ctx.lineTo(x + r * .5, y + r * .5); ctx.moveTo(x + r * .5, y - r * .5); ctx.lineTo(x - r * .5, y + r * .5); ctx.stroke() }
        if (L.sel === q.t || i === hover.current) {
          ctx.globalAlpha = 1; ctx.font = (12 * dpr) + 'px "IBM Plex Mono", monospace'; ctx.fillStyle = c.ink
          const tw = ctx.measureText(q.t).width, lx = Math.min(w - tw - 8 * dpr, Math.max(8 * dpr, x - tw / 2))
          ctx.fillText(q.t, lx, y - r - 7 * dpr)
        }
      }
      ctx.globalAlpha = 1
    }
    setPhase(ev > 0 ? 3 : tri > 0 ? 2 : score > 0 ? 1 : 0)
  }
  function setT(t) { /* fallback (reduced motion): map progress straight onto the phase values */
    const s = sim.current; s.reveal = smooth(0, .3, t); s.score = smooth(.3, .55, t); s.tri = smooth(.55, .75, t); s.ev = smooth(.75, 1, t)
  }
  function onTick() {
    draw()
    if (scrubRef.current && tl.current) scrubRef.current.value = Math.round(tl.current.progress * 10)
  }

  /* mount: canvas size, theme tracking, and the anime timeline */
  useEffect(() => {
    const cv = cvRef.current
    function size() { dprRef.current = Math.min(2, window.devicePixelRatio || 1); cv.width = Math.round(cv.clientWidth * dprRef.current); cv.height = Math.round(cv.clientHeight * dprRef.current); draw() }
    refreshColors(); size()
    const ro = window.ResizeObserver ? new ResizeObserver(size) : null; if (ro) ro.observe(cv); else addEventListener('resize', size)
    const repaint = () => { refreshColors(); draw() }
    const mo = new MutationObserver(repaint); mo.observe(document.documentElement, { attributes: true })
    const mq = matchMedia('(prefers-color-scheme: dark)'); if (mq.addEventListener) mq.addEventListener('change', repaint)
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw)
    if (AN && !RM()) {
      const s = sim.current; s.reveal = s.score = s.tri = s.ev = 0
      const phaseOpt = (key, d) => { const o = { targets: s, duration: d, easing: 'easeInOutSine' }; o[key] = [0, 1]; return o }
      const t = AN.timeline({ autoplay: false, easing: 'linear', update: onTick, complete: () => { setPlaying(false); setAtEnd(true) } })
      t.add(phaseOpt('reveal', 3300)).add(phaseOpt('score', 2750)).add(phaseOpt('tri', 2200)).add(phaseOpt('ev', 2750))
      tl.current = t; t.seek(t.duration); onTick()
    }
    return () => {
      if (ro) ro.disconnect(); else removeEventListener('resize', size)
      mo.disconnect(); if (mq.removeEventListener) mq.removeEventListener('change', repaint)
      if (tl.current) { tl.current.pause(); AN.remove(sim.current); tl.current = null }
    }
  }, [])
  useEffect(() => { draw() }, [p.m, p.K, p.sel, p.img])

  function toggle() {
    const t = tl.current
    if (!t) { setT(1); draw(); if (scrubRef.current) scrubRef.current.value = 1000; return }
    if (playing) { t.pause(); setPlaying(false); return }
    if (t.progress >= 99.9) t.seek(0)
    setAtEnd(false); setPlaying(true); t.play()
  }
  function scrub(e) {
    const v = e.target.value / 1000, t = tl.current
    setPlaying(false); setAtEnd(v >= 1)
    if (t) { t.pause(); t.seek(t.duration * v) } else setT(v)
    draw()
  }
  function move(e) {
    const cv = cvRef.current, r = cv.getBoundingClientRect(), mx = (e.clientX - r.left) / r.width, my = (e.clientY - r.top) / r.height, L = live.current, m = L.m
    let best = -1, bd = 1e9
    const pad = 18 / r.width, padY = 18 / r.height
    L.P.forEach((q, i) => {
      const dx = (pad + q.nx * (1 - 2 * pad) - mx) * r.width, dy = (padY + q.ny * (1 - 2 * padY) - my) * r.height, d = dx * dx + dy * dy, want = q.t ? 0.4 : 1
      if (d * want < bd) { bd = d * want; best = i }
    })
    const tip = p.tipRef.current
    if (best >= 0 && bd < 18 * 18) {
      const q = L.P[best]; hover.current = q.t ? best : -1
      tip.innerHTML = ''
      if (q.t) { const b = document.createElement('b'); b.textContent = q.t; tip.appendChild(b); tip.appendChild(document.createElement('br')) }
      tip.appendChild(document.createTextNode(q.p)); tip.appendChild(document.createElement('br'))
      tip.appendChild(document.createTextNode('rank ' + fmt(q.r[m]) + ' of ' + fmt(L.files) + (q.r[m] <= L.K ? ' · flagged' : ' · not flagged')))
      tip.style.left = Math.min(innerWidth - 330, e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; tip.style.opacity = 1
    } else { tip.style.opacity = 0; hover.current = -1 }
    draw()
  }
  function leave() { p.tipRef.current.style.opacity = 0; hover.current = -1; draw() }

  const tickerText = useMemo(() => { let t = ''; im.sample.slice(0, 60).forEach((q) => { t += q.p + '   ·   ' }); return t + t }, [p.img])
  const rnd = Math.round(p.K / im.files * targets.length * 10) / 10
  return (
    <Section id="simulation">
      <div className="sec-head rv"><div className="eyebrow">Simulation</div><h2>Watch a model triage a disk</h2>
        <p>Each dot is a real file from the selected disk, placed by how similar its 23 features are. Press play: files are indexed, scored, cut to the review budget, and the evidence the case investigators care about is marked as caught or missed.</p></div>
      <div className="sim rv">
        <div className="stage">
          <div className="ticker" aria-hidden="true"><div>{tickerText}</div></div>
          <canvas ref={cvRef} role="img" aria-label="Scatter of files scored by the selected model; flagged files and evidence targets are highlighted" onPointerMove={move} onPointerLeave={leave}></canvas>
          <div className="phases">{PHASES.map((ph, i) => <div key={i} className={phase === i ? 'on' : ''}><b>{ph[0]}</b>{ph[1]}</div>)}</div>
          <div className="transport"><button className="btn" type="button" onClick={toggle}>{playing ? 'Pause' : atEnd ? 'Replay' : 'Play'}</button>
            <input ref={scrubRef} type="range" min="0" max="1000" defaultValue="1000" aria-label="Simulation progress" onInput={scrub} /></div>
          <div className="legend"><span><i className="dotkey" style={{ background: 'var(--dot)' }}></i>file</span>
            <span><i className="dotkey" style={{ background: 'var(' + MVAR[p.m] + ')' }}></i>flagged for review</span>
            <span><i className="dotkey" style={{ background: 'var(--ok)' }}></i>evidence caught</span>
            <span><i className="dotkey" style={{ background: 'transparent', border: '2px solid var(--bad)' }}></i>evidence missed</span></div>
        </div>
        <aside className="readout" aria-live="polite">
          <div><div className="eyebrow">Evidence caught</div><div className="big"><Num value={caught} fmt={String} /><small>/ {targets.length}</small></div></div>
          <dl className="kv">
            <dt>Files to read</dt><dd><Num value={p.K} fmt={fmt} /></dd>
            <dt>Share of disk</dt><dd><Num value={p.K / im.files} fmt={(v) => pc(v, 2)} /></dd>
            <dt>Files skipped</dt><dd><Num value={im.files - p.K} fmt={fmt} /></dd>
            <dt>Evidence recall</dt><dd><Num value={caught / targets.length} fmt={(v) => pc(v)} /></dd>
          </dl>
          <p className="note">Reading files at random would catch about {rnd} of {targets.length} targets at this budget.</p>
        </aside>
      </div>
    </Section>
  )
}
