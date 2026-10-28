import { useState } from 'react'
import { X } from '../lib/data'
import Section from '../lib/Section'
import Seg from '../lib/Seg'

export default function Audit() {
  const [af, setAf] = useState(0), all = X.claims || []
  const list = all.filter((c) => af === 0 || (af === 1 ? c.verdict === 'FALSE' : c.verdict === 'TRUE'))
  const nf = all.filter((c) => c.verdict === 'FALSE').length
  return (
    <Section id="audit">
      <div className="sec-head rv"><div className="eyebrow">Earlier claims checked</div><h2>What the earlier results got right and wrong</h2>
        <p>Each claim from the earlier results was re-tested against this run. Many earlier Image 1 numbers matched an older, buggier version of the pipeline; others were not produced by any code.</p></div>
      <div className="rv" style={{ display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center', marginBottom: 12 }}>
        <Seg label="Filter claims" items={['All', 'Wrong', 'Correct']} value={af} onPick={setAf} /><span className="note">{nf} of {all.length} checked claims did not hold up.</span></div>
      <div className="rows rv" style={{ maxHeight: 620 }}>{list.map((c, i) => {
        const ok = c.verdict === 'TRUE', cls = ok ? 'ok' : c.verdict === 'FALSE' ? 'bad' : 'warn'
        return <details key={c.claim + i} className="row" style={{ display: 'block', cursor: 'default' }}><summary className="csum"><span className={'chip ' + cls}>{ok ? 'correct' : c.verdict === 'FALSE' ? 'wrong' : c.verdict.toLowerCase()}</span><span>{c.claim}<small>{c.area}</small></span></summary><p className="note cev">{c.evidence}</p></details>
      })}</div>
    </Section>
  )
}
