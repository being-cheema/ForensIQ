import { useLayoutEffect, useMemo, useRef } from 'react'
import { AN, canAnim } from '../lib/motion'
import { D, MODELS, SHORT, MVAR, IMGS, fmt, pc } from '../lib/data'
import Num from '../lib/Num'

export default function Hero() {
  const ref = useRef()
  const info = useMemo(() => {
    const tot = IMGS.reduce((a, t) => a + D.images[t].files, 0), best = [0, 0, 0]
    IMGS.forEach((t) => { MODELS.forEach((m, i) => { best[i] += parseFloat(D.images[t].metrics[m].target_recall) }) })
    const mean = best.map((b) => b / IMGS.length)
    return { tot, mean, top: mean.indexOf(Math.max.apply(null, mean)) }
  }, [])
  useLayoutEffect(() => {
    if (!canAnim()) return
    const q = (s) => ref.current.querySelectorAll(s)
    AN.set(q('.eyebrow, h1, .lede, .hstat'), { opacity: 0 })
    AN.set(q('.hero-rule'), { scaleX: 0 })
    const tl = AN.timeline({ easing: 'easeOutExpo', duration: 800 })
      .add({ targets: q('.eyebrow'), opacity: [0, 1], translateY: [10, 0] })
      .add({ targets: q('h1'), opacity: [0, 1], translateY: [26, 0], duration: 1000 }, '-=600')
      .add({ targets: q('.hero-rule'), scaleX: [0, 1], duration: 900 }, '-=700')
      .add({ targets: q('.lede'), opacity: [0, 1], translateY: [14, 0] }, '-=700')
      .add({ targets: q('.hstat'), opacity: [0, 1], translateY: [18, 0], delay: AN.stagger(110) }, '-=500')
    return () => { tl.pause(); AN.remove(q('.eyebrow, h1, .lede, .hstat, .hero-rule')) }
  }, [])
  const top = info.top
  return (
    <div className="wrap"><header className="hero" ref={ref}>
      <div className="eyebrow">ForensIQ · explainable disk triage · three real disk images</div>
      <h1>Which model finds the evidence in the first 5% of files?</h1>
      <div className="hero-rule"></div>
      <p className="lede">A forensic examiner can't read 166,000 files. Each model ranks every file on 23 forensic features, and the examiner reads only the top slice. Pick a disk image, pick a model, and watch it triage the real files.</p>
      <div className="hero-stats">
        <div className="hstat"><b><Num value={info.tot} fmt={fmt} intro={true} delay={500} /></b><span>files across {IMGS.length} real disk images</span></div>
        <div className="hstat"><b>5%</b><span>of files an examiner reads per disk in the simulation below</span></div>
        <div className="hstat"><b style={{ color: 'var(' + MVAR[top] + ')' }}><Num value={info.mean[top]} fmt={(v) => pc(v, 0)} intro={true} delay={650} /></b><span>mean evidence recall for {SHORT[top]} at a strict 5% budget. The best model changes with the budget: see the verdict.</span></div>
      </div></header></div>
  )
}
