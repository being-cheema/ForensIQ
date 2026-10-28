import { useLayoutEffect, useRef } from 'react'
import { AN, canAnim } from './motion'

/* Section: .rv children fade/slide in once when the section first scrolls into view. */
export default function Section(props) {
  const ref = useRef()
  useLayoutEffect(() => {
    if (!canAnim() || !window.IntersectionObserver) return
    const els = ref.current.querySelectorAll('.rv'); if (!els.length) return
    AN.set(els, { opacity: 0, translateY: 18 })
    const io = new IntersectionObserver((es) => {
      if (!es.some((e) => e.isIntersecting)) return
      io.disconnect()
      AN({ targets: els, opacity: 1, translateY: 0, delay: AN.stagger(90), duration: 700, easing: 'easeOutCubic',
        complete: () => { els.forEach((e) => { e.style.transform = '' }) } })
    }, { rootMargin: '0px 0px -6% 0px' })
    io.observe(ref.current)
    return () => { io.disconnect(); AN.remove(els); els.forEach((e) => { e.style.opacity = ''; e.style.transform = '' }) }
  }, [])
  return <section id={props.id} ref={ref}>{props.children}</section>
}
