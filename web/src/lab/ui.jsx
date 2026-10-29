import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { css } from '../lib/data'

/* ---------- palette read from the design tokens; refreshed when the theme flips ---------- */
let PAL = null
const subs = new Set()
function reset() { PAL = null; subs.forEach((f) => f()) }
if (typeof window !== 'undefined') {
  new MutationObserver(reset).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  if (window.matchMedia) matchMedia('(prefers-color-scheme: dark)').addEventListener('change', reset)
}
export function pal() {
  if (!PAL) PAL = { dot: css('--dot'), accent: css('--accent'), accentInk: css('--accent-ink'), ink: css('--ink'), ink2: css('--ink2'), rule: css('--rule'), sheet: css('--sheet'), paper: css('--paper'), grid: css('--grid'), tagbg: css('--tagbg'), m0: css('--m0'), m1: css('--m1'), m2: css('--m2') }
  return PAL
}
export function useThemeTick() {
  const [t, setT] = useState(0)
  useEffect(() => { const f = () => setT((v) => v + 1); subs.add(f); return () => { subs.delete(f) } }, [])
  return t
}
export const MODEL_COL = { if: 'm0', lof: 'm1', svm: 'm2' }

/* ---------- a crisp, resizable canvas. draw(ctx, w, h) works in CSS pixels. ---------- */
export function useCanvas(ref, draw, tick) {
  const dr = useRef(draw); dr.current = draw
  const size = useRef({ w: 0, h: 0, dpr: 1 })
  const redraw = useCallback(() => {
    const cv = ref.current; if (!cv) return
    const { w, h, dpr } = size.current; if (!w) return
    const ctx = cv.getContext('2d')
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, w, h)
    dr.current(ctx, w, h)
  }, [])
  useLayoutEffect(() => {
    const cv = ref.current; if (!cv) return
    const fit = () => {
      const r = cv.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1)
      if (!r.width) return
      size.current = { w: r.width, h: r.height, dpr }
      cv.width = Math.round(r.width * dpr); cv.height = Math.round(r.height * dpr)
      redraw()
    }
    fit()
    const ro = new ResizeObserver(fit); ro.observe(cv)
    return () => ro.disconnect()
  }, [])
  useEffect(() => { redraw() }, [tick, draw])
  return redraw
}

/* ---------- tooltip (the page-wide .tip element) ---------- */
export function showTip(tip, lines, x, y) {
  if (!tip) return
  tip.innerHTML = ''
  lines.forEach((l, i) => {
    if (i) tip.appendChild(document.createElement('br'))
    if (l && l.b) { const b = document.createElement('b'); b.textContent = l.b; tip.appendChild(b) } else tip.appendChild(document.createTextNode(l))
  })
  tip.style.left = Math.max(8, Math.min(window.innerWidth - 330, x + 14)) + 'px'
  tip.style.top = Math.min(window.innerHeight - 80, y + 14) + 'px'
  tip.style.opacity = 1
}
export const hideTip = (tip) => { if (tip) tip.style.opacity = 0 }

/* ---------- searchable file picker ---------- */
export function FilePicker({ d, value, onPick, label, quicks, id }) {
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(false)
  const [hi, setHi] = useState(0)
  const box = useRef()
  const list = (() => {
    const s = q.trim().toLowerCase()
    const out = []
    for (let i = 0; i < d.n && out.length < 40; i++) {
      if (!s || d.rows[i].p.toLowerCase().includes(s) || (d.isT[i] && d.rows[i].t.toLowerCase().includes(s))) out.push(i)
    }
    // evidence files first when browsing
    if (!s) out.sort((a, b) => (d.isT[b] ? 1 : 0) - (d.isT[a] ? 1 : 0))
    return out
  })()
  useEffect(() => { setHi(0) }, [q])
  useEffect(() => {
    if (!open) return
    const f = (e) => { if (box.current && !box.current.contains(e.target)) setOpen(false) }
    document.addEventListener('pointerdown', f); return () => document.removeEventListener('pointerdown', f)
  }, [open])
  const pick = (i) => { onPick(i); setOpen(false); setQ('') }
  const key = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setHi((h) => Math.min(list.length - 1, h + 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setHi((h) => Math.max(0, h - 1)) }
    else if (e.key === 'Enter' && open && list[hi] != null) { e.preventDefault(); pick(list[hi]) }
    else if (e.key === 'Escape') setOpen(false)
  }
  return (
    <div className="fpick" ref={box}>
      <label htmlFor={id}>{label}</label>
      <div className="fp-cur"><span className={d.isT[value] ? 'tg' : ''}>{d.name[value]}</span><small>{d.isT[value] ? 'evidence' : 'ordinary file'} · rank {d.rows[value].rk.if.toLocaleString('en-US')} of {d.N.toLocaleString('en-US')} (full disk)</small></div>
      <div className="fp-in">
        <input id={id} type="search" role="combobox" aria-expanded={open} aria-controls={id + '-l'} aria-autocomplete="list" autoComplete="off" placeholder="Search the sample by path"
          value={q} onChange={(e) => { setQ(e.target.value); setOpen(true) }} onFocus={() => setOpen(true)} onKeyDown={key} />
        {open ? (
          <ul id={id + '-l'} role="listbox" className="fp-list">
            {list.length ? list.map((i, k) => (
              <li key={i} role="option" aria-selected={k === hi} className={(k === hi ? 'on ' : '') + (d.isT[i] ? 't' : '')} onPointerDown={(e) => { e.preventDefault(); pick(i) }} onMouseEnter={() => setHi(k)}>
                <b>{d.name[i]}</b><span>{d.folder[i]}</span></li>
            )) : <li className="none">No file in the sample matches.</li>}
          </ul>
        ) : null}
      </div>
      <div className="fp-q">{quicks.map((qk) => <button key={qk.label} type="button" className="lnk" onClick={qk.fn}>{qk.label}</button>)}</div>
    </div>
  )
}

/* ---------- small pieces ---------- */
export function Part({ n, title, intro, note, children }) {
  return (
    <div className="lab-part" id={'lab-' + n.toLowerCase()}>
      <h3 className="lab-h"><span>{n}</span>{title}</h3>
      <div className="pr">
        <div className="pr-main"><p>{intro}</p></div>
        {note ? <aside className="side">{note}</aside> : null}
      </div>
      {children}
    </div>
  )
}
export const sr = (s) => <span className="sr">{s}</span>

/** Debounced live-region text, so sliders do not make a screen reader chatter. */
export function useSettled(text, ms = 600) {
  const [s, setS] = useState(text)
  useEffect(() => { const t = setTimeout(() => setS(text), ms); return () => clearTimeout(t) }, [text])
  return s
}
