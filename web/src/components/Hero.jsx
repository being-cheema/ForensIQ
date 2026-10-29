import { useMemo } from 'react'
import { D, MODELS, SHORT, MVAR, IMGS, fmt, pc } from '../lib/data'
import Num from '../lib/Num'
import LogStrip from './LogStrip'

export default function Hero(p) {
  const info = useMemo(() => {
    const tot = IMGS.reduce((a, t) => a + D.images[t].files, 0)
    const biggest = Math.max.apply(null, IMGS.map((t) => D.images[t].files))
    return { tot, biggest }
  }, [])
  /* mean share of targets caught over the three disks at the selected budget, per model (full-disk ranks of the seed-42 run) */
  const mean = useMemo(() => MODELS.map((m) => IMGS.reduce((a, t) => { const x = D.images[t], K = Math.max(1, Math.round(p.pct * x.files)); return a + x.targets.filter((g) => g.ranks[m] <= K).length / x.targets.length }, 0) / IMGS.length), [p.pct])
  const top = mean.indexOf(Math.max.apply(null, mean)), im = D.images[p.img]
  const date = new Date().toISOString().slice(0, 10)
  return (
    <header className="wrap">
      <div className="casehdr">
        <div className="cf"><span>Case</span><b>Disk triage</b></div>
        <div className="cf"><span>Image</span><b title={im.label}>{im.label}</b></div>
        <div className="cf"><span>Examiner</span><b>ForensIQ</b></div>
        <div className="cf"><span>Date</span><b>{date}</b></div>
        <button type="button" onClick={p.toggleTheme} aria-pressed={p.dark} title="Switch between light and dark display">Lightbox: <u>{p.dark ? 'on' : 'off'}</u></button>
      </div>
      <div className="hero">
        <h1>Three seized disks. {fmt(info.tot)} files. Which model finds the <em>evidence?</em></h1>
        <div className="hero-grid">
          <p className="lede">A forensic examiner can't read every file on a disk: the largest here holds {fmt(info.biggest)}. Each model ranks every file on 19 forensic features, and the examiner reads only the top slice. Pick a disk image, pick a model, and watch it triage the real files.</p>
          <div className="summary">
            <div><b><Num value={info.tot} fmt={fmt} intro={true} delay={300} /></b><span>files across {IMGS.length} real disk images</span></div>
            <div><b><Num value={p.pct * 100} fmt={(v) => v.toFixed(1) + '%'} /></b><span>of files an examiner reads per disk, set by the budget control below. 20% is the recommended setting.</span></div>
            <div><b style={{ color: 'var(' + MVAR[top] + ')' }}><Num value={mean[top]} fmt={(v) => pc(v, 0)} intro={true} delay={400} /></b><span>mean share of targets caught by {SHORT[top]} across the three disks at a {pc(p.pct)} budget, in one run. The final answer and its limits are in Exhibits B and L.</span></div>
          </div>
        </div>
        <LogStrip />
      </div>
    </header>
  )
}
