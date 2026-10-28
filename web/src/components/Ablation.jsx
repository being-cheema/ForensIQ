import { useRef } from 'react'
import { MODELS, SHORT, MVAR, frac } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'

export default function Ablation(p) {
  const ref = useRef()
  useGrow(ref, [p.img])
  return (
    <Section id="ablation">
      <div className="sec-head rv"><div className="eyebrow">Ablation</div><h2>Which features carry the result?</h2><p>Targets caught at the 5% budget with feature groups removed or kept alone, for the selected disk.</p></div>
      <div className="panel scroll-x rv" ref={ref}><table><thead><tr><th>Feature set</th><th className="n">Features</th>{SHORT.map((n, i) => <th key={n}><i className="dotkey" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{n}</th>)}</tr></thead><tbody>{p.im.ablation.map((r) => {
        const strong = /^Full \(/.test(r.config) || /^Legacy/.test(r.config)
        return <tr key={r.config} style={strong ? { background: 'var(--surface2)' } : undefined}><td>{r.config}</td><td className="n">{r.n}</td>{MODELS.map((m, i) => (
          <td key={m}><div className="abc"><span className="num mono">{r[m]}</span><div className="bar"><i data-grow="1" data-w={frac(r[m]) * 100} style={{ width: (frac(r[m]) * 100) + '%', background: 'var(' + MVAR[i] + ')' }}></i></div></div></td>
        ))}</tr>
      })}</tbody></table></div>
    </Section>
  )
}
