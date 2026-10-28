import { D, SHORT, IMGS, short, fmt, pc } from '../lib/data'
import Seg from '../lib/Seg'

export default function ControlStrip(p) {
  return (
    <div className="strip"><div className="strip-in">
      <div className="grp"><span className="lab">Disk</span>
        <Seg label="Disk" items={IMGS.map((t) => short(D.images[t].label))} value={IMGS.indexOf(p.img)} onPick={(i) => p.setImg(IMGS[i])} /></div>
      <div className="grp"><span className="lab">Model</span>
        <Seg label="Model" colored={true} items={SHORT} value={p.m} onPick={p.setM} /></div>
      <div className="grp budget"><label htmlFor="bud">Budget</label>
        <input id="bud" type="range" min="0.2" max="20" step="0.1" value={p.pct * 100} onChange={(e) => p.setPct(parseFloat(e.target.value) / 100)} />
        <output htmlFor="bud">{pc(p.pct)} · {fmt(p.K)} files</output></div>
    </div></div>
  )
}
