import { useRef } from 'react'
import { X } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr, Flag } from '../lib/Prose'

function StatusFor(p) {
  const st = p.st
  if (!st) return <span className="small">–</span>
  return <span><span className={'stt' + (st.status === 'fired' ? ' f' : '')}>{st.status}</span> <span className="mono small">{st.shap.toFixed(3)}</span></span>
}

export default function Firing(p) {
  const f = (X.firing || {})[p.img], ref = useRef()
  useGrow(ref, [p.img])
  const rows = f ? f.features.slice().sort((a, b) => ((b.s23 || {}).shap || 0) - ((a.s23 || {}).shap || 0)) : []
  return (
    <Section id="firing" letter="J" title="Which features does the model actually use?">
      <Pr><p>A feature "fires" when its mean SHAP value is above zero. Features that never vary across files can never fire, whatever happened on the disk.</p></Pr>
      <div ref={ref}>
        {f ? <><div className="fcounts">{f.counts.map((c, i) => (
          <div key={i}><b>{c.fired}<small> of {c.of}</small></b><span>{c.set} features · {c.model}: {c.fired} of {c.of} fired</span><div className="b1"><i data-grow="1" data-w={c.fired / c.of * 100} style={{ width: (c.fired / c.of * 100) + '%' }}></i></div></div>
        ))}</div>
        <div className="tbl"><table><thead><tr><th>Feature</th><th>Original 17</th><th>23-feature set</th><th className="n">Files non-zero</th><th>Why</th></tr></thead><tbody>{rows.map((r) => {
          const cause = (r.s23 || r.s17 || {}).cause || ''
          return <tr key={r.feature}><td className="mono" style={{ whiteSpace: 'nowrap' }}>{r.feature}{r.constant ? <> <Flag kind="bad">constant</Flag></> : null}</td><td><StatusFor st={r.s17} /></td><td><StatusFor st={r.s23} /></td><td className="n">{r.nonzero_pct}%</td><td className="cause">{cause.length > 230 ? cause.slice(0, 227) + '…' : cause}</td></tr>
        })}</tbody></table></div></> : null}
      </div>
    </Section>
  )
}
