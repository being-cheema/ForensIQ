import { useEffect, useLayoutEffect, useRef } from 'react'
import { AN, canAnim, EASE } from './motion'

/* Number that tweens to its new value. A timer writes the final value if the tween stalls, so it never stays at zero. */
export default function Num(props) {
  const ref = useRef(), cur = useRef({ v: null }), fr = useRef(props.fmt), anim = useRef(null), timer = useRef(0)
  fr.current = props.fmt || String
  useLayoutEffect(() => {
    const el = ref.current, o = cur.current, v = props.value, intro = props.intro
    clearTimeout(timer.current)
    if (anim.current && AN) AN.remove(o)
    if (!canAnim() || (o.v === null && !intro)) { o.v = v; el.textContent = fr.current(v); return }
    if (o.v === null) o.v = 0
    el.textContent = fr.current(o.v)
    const dur = intro ? 900 : (props.dur || 500), delay = intro ? (props.delay || 0) : 0
    anim.current = AN({ targets: o, v, duration: dur, delay, easing: EASE,
      update: () => { el.textContent = fr.current(o.v) }, complete: () => { el.textContent = fr.current(v) } })
    timer.current = setTimeout(() => { o.v = v; el.textContent = fr.current(v) }, dur + delay + 1200)
  }, [props.value])
  useEffect(() => () => { clearTimeout(timer.current); if (AN) AN.remove(cur.current) }, [])
  return <span ref={ref} className="num"></span>
}
