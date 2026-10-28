import { useEffect, useLayoutEffect, useRef } from 'react'
import { AN, canAnim } from './motion'

/* Number that tweens to its new value. */
export default function Num(props) {
  const ref = useRef(), cur = useRef({ v: null }), fr = useRef(props.fmt), anim = useRef(null)
  fr.current = props.fmt || String
  useLayoutEffect(() => {
    const el = ref.current, o = cur.current, v = props.value, intro = props.intro
    if (anim.current && AN) AN.remove(o)
    if (!canAnim() || (o.v === null && !intro)) { o.v = v; el.textContent = fr.current(v); return }
    if (o.v === null) o.v = 0
    el.textContent = fr.current(o.v)
    anim.current = AN({ targets: o, v, duration: intro ? 1400 : 650, delay: intro ? (props.delay || 0) : 0, easing: 'easeOutCubic',
      update: () => { el.textContent = fr.current(o.v) }, complete: () => { el.textContent = fr.current(v) } })
  }, [props.value])
  useEffect(() => () => { if (AN) AN.remove(cur.current) }, [])
  return <span ref={ref} className="num"></span>
}
