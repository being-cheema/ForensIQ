import { D, SHORT, IMGS, short, fmt, pc } from '../lib/data'
import Seg from '../lib/Seg'

const MIN = 0.2, MAX = 20
const pos = (v) => ((v - MIN) / (MAX - MIN)) * 100

export default function ControlStrip(p) {
  return (
    <div className="bar"><div className="wrap"><div className="bar-in">
      <div className="fld"><span className="lab">Disk</span>
        <Seg label="Disk" items={IMGS.map((t) => short(D.images[t].label))} value={IMGS.indexOf(p.img)} onPick={(i) => p.setImg(IMGS[i])} /></div>
      <div className="fld"><span className="lab">Model</span>
        <Seg label="Model" colored={true} items={SHORT} value={p.m} onPick={p.setM} /></div>
      <div className="fld ruler"><label htmlFor="bud">Budget</label>
        <div className="ruler-in">
          <input id="bud" type="range" min={MIN} max={MAX} step="0.1" value={p.pct * 100} onChange={(e) => p.setPct(parseFloat(e.target.value) / 100)} aria-valuetext={pc(p.pct) + ' of files'} />
          <div className="ticks" aria-hidden="true">{[[5, '5% strict', '5%: the strict equal-budget comparison point'], [10, '10', ''], [15, '15% recommended', '15%: the recommended budget'], [20, '20', '']].map(([v, t, ttl]) => <i key={v} title={ttl || undefined} className={v === 15 ? 'rec' : v === 5 ? 'strict' : ''} style={{ left: pos(v) + '%' }}><span>{t}</span></i>)}</div>
        </div>
        <output htmlFor="bud">{pc(p.pct)} · {fmt(p.K)} files</output></div>
    </div></div></div>
  )
}
