import { useRef } from 'react'
import { D } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'

export default function Pipeline(p) {
  const tm = p.im.stage_times, ref = useRef(), mx = Math.sqrt(Math.max.apply(null, D.pipeline.map((s) => tm[s.script] || 0)) || 1)
  let tot = 0
  useGrow(ref, [p.img])
  const rows = D.pipeline.map((s, i) => {
    const v = tm[s.script] || 0; tot += v
    return <div key={s.script} className="stp"><span className="ix">{String(i + 1).padStart(2, '0')}</span><div><b>{s.title}</b><span>{s.desc}</span></div><div className="bar"><i data-grow="1" data-w={Math.sqrt(v) / mx * 100} style={{ width: (Math.sqrt(v) / mx * 100) + '%', background: 'var(--m0)' }}></i></div><span className="num mono">{v.toFixed(1)}s</span></div>
  })
  return (
    <Section id="pipeline">
      <div className="sec-head rv"><div className="eyebrow">Pipeline</div><h2>The 12 stages behind every result</h2><p>Measured run times for the selected disk, from the raw image to the report.</p></div>
      <div className="panel pipe rv" ref={ref}>{rows}<div className="stp" style={{ borderBottom: 0 }}><span></span><b>Total</b><span></span><span className="num mono">{tot.toFixed(0)}s</span></div></div>
    </Section>
  )
}
