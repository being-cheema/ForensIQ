import { D, short } from '../lib/data'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'
import { A3, DISKS, NT, f1 } from '../lib/study'
import { Fig } from './Plateau'
import HBars from './HBars'

const dn = (t) => short(D.images[t].label)
const IFK = 'Isolation Forest'
const SETS = [
  { k: 'clean', name: 'Base 17', color: 'var(--m1)', get: (t) => A3.c_burst.clean[t][IFK] },
  { k: 'final', name: 'Final 19 (base + burst)', color: 'var(--m0)', get: (t) => A3.c_burst.clean_plus_burst[t][IFK], hi: true }
]
const TZ = { img1: 'UTC−5', img2: 'UTC−4', img3: 'UTC−4' }

export default function Cleanup() {
  const groups = DISKS.map((t) => ({ label: dn(t), rows: SETS.map((s) => { const a = s.get(t); return { label: s.name, v: a.at20 / NT[t] * 100, text: f1(a.at20) + ' / ' + NT[t], color: s.color, hi: s.hi } }) }))
  return (
    <Section id="cleanup" letter="E" title="The feature set: what goes into the ranking">
      <Pr note={<>The feature set was fixed <b>before</b> any of the numbers in this page were produced, and ground truth was not used to decide which features to keep.</>}>
        <p>Every model ranks files using <b>features</b>: numbers worked out for each file, such as how far its timestamps disagree or how deep its folder is. Each feature was checked on all three disks before the study. Features that did not vary from file to file were left out, because they cannot help a model rank anything.</p>
        <p>The result is 17 base features. Working hours are counted in each disk’s own time zone, read from its registry ({DISKS.map((t) => dn(t) + ': ' + TZ[t]).join(', ')}). A pre-registered test then added two burst features, which gives the final 19.</p>
      </Pr>

      <h3 className="rel-h"><span>1</span>What the burst features add</h3>
      <Pr><p>A burst feature counts how many files share the same modified second or minute. A bulk copy or a wipe stamps many files at once.</p></Pr>
      <Fig n="4" name="feature-sets" caption={<>Targets caught at a 20% budget by Isolation Forest, as a share of all targets, for the base 17 and the final 19 features. Means over 5 seeds. Labels give targets caught of targets. Source: A3 of the pre-registered study.</>}>
        <HBars groups={groups} refAt={90} refLabel="90%" aria={'Targets caught at a 20% budget for two feature sets on three disks'} />
      </Fig>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Feature set</th><th className="n">Caught at 15%</th><th className="n">Caught at 20%</th><th className="n">Budget for 90%</th><th className="n">Budget for last target</th></tr></thead>
        <tbody>{DISKS.map((t) => SETS.map((s, i) => {
          const a = s.get(t)
          return (
            <tr key={t + s.k} className={i === 0 ? 'grp' : ''}>
              <td>{i === 0 ? dn(t) : ''}</td><td>{s.name}</td>
              <td className="n">{f1(a.at15)}{a.at15_sd ? ' ± ' + f1(a.at15_sd) : ''} / {NT[t]}</td>
              <td className="n">{f1(a.at20)}{a.at20_sd ? ' ± ' + f1(a.at20_sd) : ''} / {NT[t]}</td>
              <td className="n">{f1(a.knee_pct)}%</td><td className="n">{f1(a.plateau_pct)}%</td></tr>)
        }))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Isolation Forest, mean ± standard deviation over 5 seeds. The burst features raised recall on all three disks and lowered it on none, which is the pre-registered rule for keeping them (A3, burst test: pass). A second rule, “drop any feature whose removal does not hurt”, was applied as written and removed 16 of the 17 features, leaving a set that falls to 0 of 7 on Image 1 at 15%. That result was judged degenerate, reported as a failure, and not used. The reasoning is in the amendment linked in Exhibit K.</p></Pr>
    </Section>
  )
}
