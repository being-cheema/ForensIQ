import { useMemo } from 'react'
import { D, MODELS, SHORT, MVAR, IMGS, short, fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import LogStrip from './LogStrip'

export default function Hero(p) {
  const info = useMemo(() => {
    const tot = IMGS.reduce((a, t) => a + D.images[t].files, 0), best = [0, 0, 0]
    const biggest = Math.max.apply(null, IMGS.map((t) => D.images[t].files))
    IMGS.forEach((t) => { MODELS.forEach((m, i) => { best[i] += parseFloat(D.images[t].metrics[m].target_recall) }) })
    const mean = best.map((b) => b / IMGS.length)
    return { tot, biggest, mean, top: mean.indexOf(Math.max.apply(null, mean)) }
  }, [])
  const top = info.top, im = D.images[p.img]
  const date = new Date().toISOString().slice(0, 10)
  return (
    <header className="wrap">
      <div className="casehdr">
        <div className="cf"><span>Case</span><b>Disk triage</b></div>
        <div className="cf"><span>Image</span><b title={im.label}>{im.label}</b></div>
        <div className="cf"><span>Examiner</span><b>ForensIQ</b></div>
        <div className="cf"><span>Date</span><b>{date}</b></div>
        <button type="button" onClick={p.toggleTheme} aria-pressed={p.dark} title="Switch between paper and lightbox">Lightbox: <u>{p.dark ? 'on' : 'off'}</u></button>
      </div>
      <div className="hero">
        <h1>Three seized disks. {fmt(info.tot)} files. Which model finds the <em>evidence?</em></h1>
        <div className="hero-grid">
          <p className="lede">A forensic examiner can't read every file on a disk: the largest here holds {fmt(info.biggest)}. Each model ranks every file on 23 forensic features, and the examiner reads only the top slice. Pick a disk image, pick a model, and watch it triage the real files.</p>
          <div className="summary">
            <div><b><Num value={info.tot} fmt={fmt} intro={true} delay={300} /></b><span>files across {IMGS.length} real disk images</span></div>
            <div><b>5%</b><span>of files an examiner reads per disk in the simulation below</span></div>
            <div><b style={{ color: 'var(' + MVAR[top] + ')' }}><Num value={info.mean[top]} fmt={(v) => pc(v, 0)} intro={true} delay={400} /></b><span>mean evidence recall for {SHORT[top]} at a strict 5% budget. The best model changes with the budget: see the verdict.</span></div>
          </div>
        </div>
        <LogStrip />
      </div>
    </header>
  )
}
