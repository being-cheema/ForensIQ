import { useEffect, useMemo, useRef } from 'react'
import { AN, canAnim } from '../lib/motion'
import { D, IMGS, short } from '../lib/data'
import { Tag } from '../lib/Prose'

/* A scrolling log of real file paths from the three images; evidence targets in red. */
export default function LogStrip() {
  const rows = useMemo(() => {
    const per = IMGS.map((t) => {
      const s = D.images[t].sample, tg = s.filter((q) => q.t), rest = s.filter((q) => !q.t)
      const step = Math.max(1, Math.floor(rest.length / 34)), out = []
      for (let i = 0, k = 0; i < rest.length && out.length < 34; i += step, k++) {
        out.push(rest[i])
        if (k % 4 === 3 && tg.length) out.push(tg[(k >> 2) % tg.length])
      }
      return out.map((q) => ({ id: short(D.images[t].label).replace('Image ', 'img'), p: q.p.trim().replace(/^\/?/, '/'), t: q.t }))
    })
    const all = [], n = Math.max.apply(null, per.map((a) => a.length))
    for (let i = 0; i < n; i++) per.forEach((a) => { if (a[i]) all.push(a[i]) })
    return all
  }, [])
  const ref = useRef()
  useEffect(() => {
    if (!canAnim() || !ref.current) return
    const el = ref.current, h = el.scrollHeight / 2
    const a = AN({ targets: el, translateY: [0, -h], duration: rows.length * 1100, easing: 'linear', loop: true })
    return () => { a.pause(); AN.remove(el); el.style.transform = '' }
  }, [])
  const list = (k) => rows.map((r, i) => (
    <div key={k + i} className={'lg' + (r.t ? ' t' : '')}><span className="li">{r.id}</span><span className="lp">{r.p}</span>{r.t ? <Tag>{r.t}</Tag> : null}</div>
  ))
  return (
    <div className="logwrap">
      <div className="logcap"><span>A sample of real file paths from the three images</span><span>Evidence in <b>red</b></span></div>
      <div className="log" aria-hidden="true"><div className="log-in" ref={ref}>{list('a')}{list('b')}</div></div>
    </div>
  )
}
