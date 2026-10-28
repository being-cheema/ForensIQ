import { useEffect, useMemo, useRef, useState } from 'react'
import { AN, RM, EASE } from '../lib/motion'
import { MODELS, SHORT, MVAR, css, fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'

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
/* Timeline phases (ms): reveal, score, triage, evidence. PH_END[i] is the time at which step i is complete. */
const DUR = [3300, 2750, 2200, 2750]
const PH_END = [3300, 6050, 8250, 11000]

export default function Simulation(p) {
  const im = p.im, cvRef = useRef(), scrubRef = useRef(), tl = useRef(null), stepsRef = useRef(), seekObj = useRef(null)
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
    colors.current = { dot: css('--dot'), ok: css('--accent'), miss: css('--ink2'), bg: css('--sheet'), ink: css('--ink'), grid: css('--grid'), m: MVAR.map(css) }
  }
  function draw() {
    const cv = cvRef.current; if (!cv) return
    if (!colors.current) refreshColors()
    const ctx = cv.getContext('2d'), L = live.current, s = sim.current, c = colors.current, dpr = dprRef.current
    const w = cv.width, h = cv.height, k = L.K, N = L.N, m = L.m, pad = 22 * dpr, P = L.P
    ctx.clearRect(0, 0, w, h)
    /* graph paper */
    ctx.strokeStyle = c.grid; ctx.lineWidth = dpr; ctx.beginPath()
    const gs = 28 * dpr
    for (let gx = gs; gx < w; gx += gs) { ctx.moveTo(Math.round(gx) + .5, 0); ctx.lineTo(Math.round(gx) + .5, h) }
    for (let gy = gs; gy < h; gy += gs) { ctx.moveTo(0, Math.round(gy) + .5); ctx.lineTo(w, Math.round(gy) + .5) }
    ctx.stroke()
    const reveal = s.reveal, score = s.score, tri = s.tri, ev = s.ev, mc = c.m[m]
    let i, q, x, y, flagged, heat, col, rad, a
    for (i = 0; i < P.length; i++) {
      q = P[i]; if (q.o > reveal * 1.02 && reveal < 1) continue
      x = pad + q.nx * (w - 2 * pad); y = pad + q.ny * (h - 2 * pad)
      flagged = q.r[m] <= k
      heat = Math.max(0, 1 - (q.r[m] / N) / 0.15) * score
      col = mixc(c.dot, mc, Math.max(heat, flagged ? tri : 0)); a = flagged ? 1 : 1 - 0.8 * tri
      rad = (1.5 + heat * 1.3 + (flagged ? tri * 1.1 : 0)) * dpr
      ctx.globalAlpha = Math.min(1, a * (reveal < 1 ? 0.35 + 0.65 * reveal : .82))
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(x, y, rad, 0, 6.2832); ctx.fill()
    }
    ctx.globalAlpha = 1
    if (ev > 0) {
      const labelled = {}
      for (i = 0; i < P.length; i++) {
        q = P[i]; if (!q.t) continue
        const tg = L.tmap[q.t]; if (!tg) continue
        x = pad + q.nx * (w - 2 * pad); y = pad + q.ny * (h - 2 * pad)
        const ok = tg.ranks[MODELS[m]] <= k, r = (4.5 + 5.5 * ev) * dpr * (L.sel === q.t ? 1.35 : 1)
        ctx.lineWidth = 2 * dpr; ctx.globalAlpha = ev
        ctx.fillStyle = c.bg; ctx.beginPath(); ctx.arc(x, y, r + 1.5 * dpr, 0, 6.2832); ctx.fill()
        ctx.strokeStyle = ok ? c.ok : c.miss; ctx.fillStyle = ok ? c.ok : c.miss
        ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.stroke()
        if (ok) { ctx.beginPath(); ctx.arc(x, y, r * 0.38, 0, 6.2832); ctx.fill() }
        else { ctx.lineWidth = 1.5 * dpr; ctx.beginPath(); ctx.moveTo(x - r * .5, y - r * .5); ctx.lineTo(x + r * .5, y + r * .5); ctx.moveTo(x + r * .5, y - r * .5); ctx.lineTo(x - r * .5, y + r * .5); ctx.stroke() }
        if ((L.sel === q.t && !labelled[q.t]) || i === hover.current) {
          labelled[q.t] = 1
          ctx.globalAlpha = 1; ctx.font = (12 * dpr) + 'px "JetBrains Mono", monospace'; ctx.fillStyle = c.ink
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
  /* A step scrolled into view: ease the timeline to the end of that phase. */
  function goPhase(i) {
    const t = tl.current; if (!t) return
    t.pause(); setPlaying(false)
    if (seekObj.current) AN.remove(seekObj.current)
    const o = { v: t.currentTime }; seekObj.current = o
    AN({ targets: o, v: PH_END[i], duration: 600, easing: EASE, update: () => { t.seek(o.v); onTick() }, complete: () => { t.seek(PH_END[i]); onTick(); setAtEnd(i === 3) } })
  }

  /* mount: canvas size, theme tracking, the anime timeline and the step observer */
  useEffect(() => {
    const cv = cvRef.current
    function size() { dprRef.current = Math.min(2, window.devicePixelRatio || 1); cv.width = Math.round(cv.clientWidth * dprRef.current); cv.height = Math.round(cv.clientHeight * dprRef.current); draw() }
    refreshColors(); size()
    const ro = window.ResizeObserver ? new ResizeObserver(size) : null; if (ro) ro.observe(cv); else addEventListener('resize', size)
    const repaint = () => { refreshColors(); draw() }
    const mo = new MutationObserver(repaint); mo.observe(document.documentElement, { attributes: true })
    const mq = matchMedia('(prefers-color-scheme: dark)'); if (mq.addEventListener) mq.addEventListener('change', repaint)
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw)
    let io = null
    if (AN && !RM()) {
      const s = sim.current
      const phaseOpt = (key, d) => { const o = { targets: s, duration: d, easing: 'easeInOutSine' }; o[key] = [0, 1]; return o }
      const t = AN.timeline({ autoplay: false, easing: 'linear', update: onTick, complete: () => { setPlaying(false); setAtEnd(true) } })
      const keys = ['reveal', 'score', 'tri', 'ev']
      /* the finished picture is the default: only rewind to 0 once the timeline exists, then jump back to the end */
      s.reveal = s.score = s.tri = s.ev = 0
      keys.forEach((k, i) => t.add(phaseOpt(k, DUR[i])))
      tl.current = t; t.seek(t.duration); onTick()
      if (window.IntersectionObserver && matchMedia('(min-width: 960px)').matches && stepsRef.current) {
        io = new IntersectionObserver((es) => {
          es.forEach((e) => { if (e.isIntersecting) goPhase(+e.target.getAttribute('data-i')) })
        }, { rootMargin: '-38% 0px -52% 0px' })
        stepsRef.current.querySelectorAll('.step').forEach((el) => io.observe(el))
      }
    }
    return () => {
      if (io) io.disconnect()
      if (ro) ro.disconnect(); else removeEventListener('resize', size)
      mo.disconnect(); if (mq.removeEventListener) mq.removeEventListener('change', repaint)
      if (seekObj.current) AN.remove(seekObj.current)
      if (tl.current) { tl.current.pause(); AN.remove(sim.current); tl.current = null }
    }
  }, [])
  useEffect(() => { draw() }, [p.m, p.K, p.sel, p.img])

  function toggle() {
    const t = tl.current
    if (!t) { setT(1); draw(); if (scrubRef.current) scrubRef.current.value = 1000; return }
    if (seekObj.current) AN.remove(seekObj.current)
    if (playing) { t.pause(); setPlaying(false); return }
    if (t.progress >= 99.9) t.seek(0)
    setAtEnd(false); setPlaying(true); t.play()
  }
  function scrub(e) {
    const v = e.target.value / 1000, t = tl.current
    if (seekObj.current) AN.remove(seekObj.current)
    setPlaying(false); setAtEnd(v >= 1)
    if (t) { t.pause(); t.seek(t.duration * v) } else setT(v)
    draw()
  }
  function move(e) {
    const cv = cvRef.current, r = cv.getBoundingClientRect(), mx = (e.clientX - r.left) / r.width, my = (e.clientY - r.top) / r.height, L = live.current, m = L.m
    let best = -1, bd = 1e9
    const pad = 22 / r.width, padY = 22 / r.height
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
      tip.style.left = Math.max(8, Math.min(innerWidth - 330, e.clientX + 14)) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; tip.style.opacity = 1
    } else { tip.style.opacity = 0; hover.current = -1 }
    draw()
  }
  function leave() { p.tipRef.current.style.opacity = 0; hover.current = -1; draw() }

  const rnd = Math.round(p.K / im.files * targets.length * 10) / 10
  const STEPS = [
    ['Index', 'The tool reads the disk\'s file table and lists every file. Each dot is a real file from the selected disk, placed by how similar its 23 features are.'],
    ['Score', SHORT[p.m] + ' scores every file on those 23 forensic features. Dots take on the model\'s colour as their anomaly score rises.'],
    ['Triage', 'Only the top ' + fmt(p.K) + ' files (' + pc(p.K / im.files, 2) + ') fit the review budget. The rest fall away, unread.'],
    ['Evidence', 'The evidence the case investigators care about is marked: ringed in red when it was caught, crossed out when missed. ' + caught + ' of ' + targets.length + ' caught here.']
  ]
  return (
    <Section id="simulation" letter="A" title="Watch a model triage a disk">
      <Pr><p>Each dot is a real file from the selected disk, placed by how similar its 23 features are. Scroll, or press play: files are indexed, scored, cut to the review budget, and the evidence the case investigators care about is marked as caught or missed.</p></Pr>
      <div className="scrolly">
        <div className="stage">
          <div className="fig"><canvas ref={cvRef} role="img" aria-label="Scatter of files scored by the selected model; flagged files and evidence targets are highlighted" onPointerMove={move} onPointerLeave={leave}></canvas></div>
          <div className="transport"><button className="btn" type="button" onClick={toggle}>{playing ? 'Pause' : atEnd ? 'Replay' : 'Play'}</button>
            <input ref={scrubRef} type="range" min="0" max="1000" defaultValue="1000" aria-label="Simulation progress" onInput={scrub} /></div>
          <div className="readout" aria-live="polite">
            <div className="hot"><b><Num value={caught} fmt={String} /><small>/ {targets.length}</small></b><span className="l">Evidence caught</span></div>
            <div><b><Num value={p.K} fmt={fmt} /></b><span className="l">Files to read</span></div>
            <div><b><Num value={p.K / im.files} fmt={(v) => pc(v, 2)} /></b><span className="l">Share of disk</span></div>
            <div><b><Num value={im.files - p.K} fmt={fmt} /></b><span className="l">Files skipped</span></div>
            <div><b><Num value={caught / targets.length} fmt={(v) => pc(v)} /></b><span className="l">Evidence recall</span></div>
          </div>
          <div className="legend"><span><i className="dotkey" style={{ background: 'var(--dot)' }}></i>file</span>
            <span><i className="dotkey" style={{ background: 'var(' + MVAR[p.m] + ')' }}></i>flagged for review</span>
            <span><i className="dotkey ring"></i>evidence caught</span>
            <span><i className="dotkey x"></i>evidence missed</span></div>
          <p className="small" style={{ marginTop: 10 }}>Reading files at random would catch about {rnd} of {targets.length} targets at this budget.</p>
        </div>
        <div className="steps" ref={stepsRef}>{STEPS.map((s, i) => (
          <div key={i} data-i={i} className={'step' + (phase === i ? ' on' : '')}><h3><span>Step {i + 1}</span>{s[0]}</h3><p>{s[1]}</p></div>
        ))}</div>
      </div>
    </Section>
  )
}
