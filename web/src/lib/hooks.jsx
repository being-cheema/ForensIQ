import { useEffect, useLayoutEffect, useRef } from 'react'
import { AN, canAnim, EASE } from './motion'

/* Calls fn once, the first time ref's element scrolls into view. fn may return a cleanup. Never fires when motion is reduced. */
export function useOnceInView(ref, fn) {
  const f = useRef(fn); f.current = fn
  const stop = useRef(null)
  useEffect(() => {
    if (!canAnim() || !window.IntersectionObserver || !ref.current) return
    const io = new IntersectionObserver((es) => {
      if (es.some((e) => e.isIntersecting)) { io.disconnect(); stop.current = f.current() }
    }, { rootMargin: '0px 0px -6% 0px' })
    io.observe(ref.current)
    return () => { io.disconnect(); if (typeof stop.current === 'function') stop.current() }
  }, [])
}

/* Bars marked [data-grow] with data-w=<percent> grow from the baseline, on first view and whenever deps change. The final width is always the inline style, restored by a timer if the animation stalls. */
export function useGrow(ref, deps) {
  const seen = useRef(false), timer = useRef(0)
  const run = () => {
    const root = ref.current; if (!root || !canAnim()) return
    const els = root.querySelectorAll('[data-grow]'); if (!els.length) return
    const settle = () => { els.forEach((e) => { e.style.width = e.dataset.w + '%' }) }
    clearTimeout(timer.current)
    AN.remove(els); AN.set(els, { width: '0%' })
    AN({ targets: els, width: (el) => el.dataset.w + '%', duration: 560, delay: AN.stagger(24, { start: 60 }), easing: EASE, complete: settle })
    timer.current = setTimeout(settle, 560 + els.length * 24 + 900)
  }
  useOnceInView(ref, () => { seen.current = true; run(); return () => { clearTimeout(timer.current); if (ref.current && AN) AN.remove(ref.current.querySelectorAll('[data-grow]')) } })
  useLayoutEffect(() => { if (seen.current) run() }, deps)
}

/* SVG polylines with class "draw" draw in with strokeDashoffset; ".fadein" elements fade in after. Everything is restored by a timer if the animation stalls. */
export function useDraw(ref, deps) {
  const seen = useRef(false), timer = useRef(0)
  const run = () => {
    const root = ref.current; if (!root || !canAnim()) return
    const ps = root.querySelectorAll('.draw'); if (!ps.length) return
    const fades = root.querySelectorAll('.fadein')
    const settle = () => {
      ps.forEach((p) => { p.removeAttribute('stroke-dashoffset'); const d = p.getAttribute('data-dash'); if (d) p.setAttribute('stroke-dasharray', d); else p.removeAttribute('stroke-dasharray') })
      fades.forEach((e) => { e.style.opacity = e.getAttribute('data-op') || '' })
    }
    clearTimeout(timer.current)
    AN.remove(ps); AN.remove(fades)
    AN.set(fades, { opacity: 0 })
    AN({ targets: ps, strokeDashoffset: [AN.setDashoffset, 0], duration: 800, delay: AN.stagger(90), easing: EASE, complete: settle })
    if (fades.length) AN({ targets: fades, opacity: (el) => [0, +(el.getAttribute('data-op') || 1)], duration: 400, delay: 700, easing: EASE })
    timer.current = setTimeout(settle, 2600)
  }
  useOnceInView(ref, () => { seen.current = true; run(); return () => { clearTimeout(timer.current); if (ref.current && AN) AN.remove(ref.current.querySelectorAll('.draw, .fadein')) } })
  useLayoutEffect(() => { if (seen.current) run() }, deps)
}
