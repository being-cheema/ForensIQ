import { useRef } from 'react'
import { D } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'

export default function Pipeline(p) {
  const tm = p.im.stage_times, ref = useRef(), mx = Math.sqrt(Math.max.apply(null, D.pipeline.map((s) => tm[s.script] || 0)) || 1)
  let tot = 0
  useGrow(ref, [p.img])
  const rows = D.pipeline.map((s, i) => {
    const v = tm[s.script] || 0; tot += v
    return <li key={s.script} className="stp"><span className="ix">{i + 1}</span><div><b>{s.title}</b><span className="d">{s.desc}</span></div><div className="b1"><i data-grow="1" data-w={Math.sqrt(v) / mx * 100} style={{ width: (Math.sqrt(v) / mx * 100) + '%' }}></i></div><span className="num">{v.toFixed(1)}s</span></li>
  })
  return (
    <Section id="pipeline" letter="F" title="The 12 stages behind every result">
      <Pr><p>Measured run times for the selected disk, from the raw image to the report.</p></Pr>
      <ol className="pipe" ref={ref}>{rows}<li className="stp total"><span></span><b>Total</b><span></span><span className="num">{tot.toFixed(0)}s</span></li></ol>
    </Section>
  )
}
