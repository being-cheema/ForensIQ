import { useState } from 'react'
import { X } from '../lib/data'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'

const Check = () => <svg viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M3.5 10.5l4.2 4.3L16.5 5.2" /></svg>
const Cross = () => <svg viewBox="0 0 20 20" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M4.5 4.5l11 11M15.5 4.5l-11 11" /></svg>

export default function Audit() {
  const [af, setAf] = useState(0), all = X.claims || []
  const list = all.filter((c) => af === 0 || (af === 1 ? c.verdict === 'FALSE' : c.verdict === 'TRUE'))
  const nf = all.filter((c) => c.verdict === 'FALSE').length
  return (
    <Section id="audit" letter="K" title="Earlier claims, checked">
      <Pr><p>Each claim from the earlier results was re-tested against the pipeline run from the raw images. Many earlier Image 1 numbers matched an older, buggier version of the pipeline; others were not produced by any code. These checks were made on the earlier 23-feature set, so some figures they mention are superseded by the clean-up in Exhibit E.</p></Pr>
      <div className="auditbar">
        <Seg label="Filter claims" items={['All', 'Wrong', 'Correct']} value={af} onPick={setAf} /><span className="small">{nf} of {all.length} checked claims did not hold up.</span></div>
      <div className="doc">{list.map((c, i) => {
        const ok = c.verdict === 'TRUE', bad = c.verdict === 'FALSE', cls = ok ? 'ok' : bad ? 'bad' : 'warn'
        return (
          <div key={c.claim + i} className={'cl ' + cls}>
            <div><span className="mk">{ok ? <Check /> : bad ? <Cross /> : null}</span>
              <p className="cl-text">{c.claim}</p><small>{c.area}</small>
              {ok ? <details><summary>evidence</summary><p>{c.evidence}</p></details> : null}</div>
            {ok ? <div></div> : <div className="fix"><b>{bad ? 'wrong' : c.verdict.toLowerCase()}</b>{c.evidence}</div>}
          </div>
        )
      })}</div>
    </Section>
  )
}
