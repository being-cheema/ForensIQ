import { useRef } from 'react'
import { X } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'

function ChipFor(p) {
  const st = p.st
  if (!st) return <span className="note">–</span>
  const cls = st.status === 'fired' ? 'ok' : st.status === 'not fired' ? 'bad' : 'warn'
  return <span><span className={'chip ' + cls}>{st.status}</span> <span className="mono num note">{st.shap.toFixed(3)}</span></span>
}

export default function Firing(p) {
  const f = (X.firing || {})[p.img], ref = useRef()
  useGrow(ref, [p.img])
  const rows = f ? f.features.slice().sort((a, b) => ((b.s23 || {}).shap || 0) - ((a.s23 || {}).shap || 0)) : []
  return (
    <Section id="firing">
      <div className="sec-head rv"><div className="eyebrow">SHAP feature firing</div><h2>Which features does the model actually use?</h2>
        <p>A feature "fires" when its mean SHAP value is above zero. Features that never vary across files can never fire, whatever happened on the disk.</p></div>
      <div className="panel rv" style={{ display: 'grid', gap: 14 }} ref={ref}>
        {f ? <><div className="fcounts">{f.counts.map((c, i) => (
          <span key={i} className="chip fchip"><span>{c.set} features · {c.model}: <b>{c.fired}</b> of {c.of} fired</span><span className="bar mini"><i data-grow="1" data-w={c.fired / c.of * 100} style={{ width: (c.fired / c.of * 100) + '%', background: 'var(--m0)' }}></i></span></span>
        ))}</div>
        <div className="scroll-x"><table><thead><tr><th>Feature</th><th>Original 17</th><th>23-feature set</th><th className="n">Files non-zero</th><th>Why</th></tr></thead><tbody>{rows.map((r) => {
          const cause = (r.s23 || r.s17 || {}).cause || ''
          return <tr key={r.feature}><td className="mono">{r.feature}{r.constant ? <> <span className="chip bad">constant</span></> : null}</td><td><ChipFor st={r.s17} /></td><td><ChipFor st={r.s23} /></td><td className="n">{r.nonzero_pct}%</td><td style={{ fontSize: '12.5px', color: 'var(--ink2)', minWidth: 280 }}>{cause.length > 230 ? cause.slice(0, 227) + '…' : cause}</td></tr>
        })}</tbody></table></div></> : null}
      </div>
    </Section>
  )
}
