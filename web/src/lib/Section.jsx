import { useEffect, useRef } from 'react'
import { AN, canAnim, EASE } from './motion'

/* An exhibit. Content is visible by default; the heading eases in only once it is in view, and a timer restores it if animation stalls. */
export default function Section(props) {
  const head = useRef()
  useEffect(() => {
    const h = head.current
    if (!h || !canAnim() || !window.IntersectionObserver) return
    let t = 0
    const clear = () => { Array.prototype.forEach.call(h.children, (e) => { e.style.opacity = ''; e.style.transform = '' }) }
    const io = new IntersectionObserver((es) => {
      if (!es.some((e) => e.isIntersecting)) return
      io.disconnect()
      AN({ targets: h.children, opacity: [0, 1], translateY: [10, 0], duration: 520, delay: AN.stagger(70), easing: EASE, complete: clear })
      t = setTimeout(clear, 1600)
    }, { rootMargin: '0px 0px -8% 0px' })
    io.observe(h)
    return () => { io.disconnect(); clearTimeout(t); AN.remove(h.children); clear() }
  }, [])
  return (
    <section id={props.id} className={'ex' + (props.band ? ' band' : '')}>
      <div className="wrap">
        <header className="exh" ref={head}>
          <span className="exl">Exhibit {props.letter}</span>
          <h2>{props.title}</h2>
        </header>
        {props.children}
      </div>
    </section>
  )
}
