import { useRef } from 'react'
import { MODELS, SHORT, MVAR, frac } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'

export default function Ablation(p) {
  const ref = useRef()
  useGrow(ref, [p.img])
  return (
    <Section id="ablation" letter="K" title="Which features carry the result?">
      <Pr><p>Targets caught with feature groups removed or kept alone, for the selected disk. The ablation was run only at the 5% equal-budget comparison point, so these counts are fixed there and do not move with the budget control.</p></Pr>
      <div className="tbl" ref={ref}><table><thead><tr><th>Feature set</th><th className="n">Features</th>{SHORT.map((n, i) => <th key={n}><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{n}</th>)}</tr></thead><tbody>{p.im.ablation.map((r) => {
        const strong = /^Full \(/.test(r.config) || /^Legacy/.test(r.config)
        return <tr key={r.config} className={strong ? 'strong' : ''}><td>{r.config}</td><td className="n">{r.n}</td>{MODELS.map((m, i) => (
          <td key={m}><div className="abc"><span className="num">{r[m]}</span><div className="b1"><i data-grow="1" data-w={frac(r[m]) * 100} style={{ width: (frac(r[m]) * 100) + '%', background: 'var(' + MVAR[i] + ')' }}></i></div></div></td>
        ))}</tr>
      })}</tbody></table></div>
    </Section>
  )
}
