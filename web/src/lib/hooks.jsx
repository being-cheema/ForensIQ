import { useEffect, useLayoutEffect, useRef } from 'react'
import { AN, canAnim } from './motion'

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

/* Bars marked [data-grow] with data-w=<percent> grow from 0 with a stagger: on first view and whenever deps change. */
export function useGrow(ref, deps) {
  const seen = useRef(false)
  const run = () => {
    const root = ref.current; if (!root || !canAnim()) return
    const els = root.querySelectorAll('[data-grow]'); if (!els.length) return
    AN.remove(els); AN.set(els, { width: '0%' })
    AN({ targets: els, width: (el) => el.dataset.w + '%', duration: 800, delay: AN.stagger(28, { start: 120 }), easing: 'easeOutCubic' })
  }
  useOnceInView(ref, () => { seen.current = true; run(); return () => { if (ref.current && AN) AN.remove(ref.current.querySelectorAll('[data-grow]')) } })
  useLayoutEffect(() => { if (seen.current) run() }, deps)
}

/* SVG polylines with class "draw" draw in with strokeDashoffset; dashed lines get their dash pattern back afterwards. */
export function useDraw(ref, deps) {
  const seen = useRef(false)
  const run = () => {
    const root = ref.current; if (!root || !canAnim()) return
    const ps = root.querySelectorAll('.draw'); if (!ps.length) return
    const fades = root.querySelectorAll('.fadein')
    AN.remove(ps)
    AN.set(fades, { opacity: 0 })
    AN({ targets: ps, strokeDashoffset: [AN.setDashoffset, 0], duration: 1300, delay: AN.stagger(140), easing: 'easeInOutSine',
      complete: () => { ps.forEach((p) => { p.removeAttribute('stroke-dashoffset'); const d = p.getAttribute('data-dash'); if (d) p.setAttribute('stroke-dasharray', d); else p.removeAttribute('stroke-dasharray') }) } })
    if (fades.length) AN({ targets: fades, opacity: (el) => [0, +(el.getAttribute('data-op') || 1)], duration: 700, delay: 900, easing: 'easeOutQuad' })
  }
  useOnceInView(ref, () => { seen.current = true; run(); return () => { if (ref.current && AN) AN.remove(ref.current.querySelectorAll('.draw, .fadein')) } })
  useLayoutEffect(() => { if (seen.current) run() }, deps)
}
