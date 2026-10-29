import { D, X, short } from '../lib/data'
import Section from '../lib/Section'
import { Pr, Flag } from '../lib/Prose'
import { A3, DISKS, NT, f1 } from '../lib/study'
import { Fig } from './Plateau'
import HBars from './HBars'

const AU = X.audit
const dn = (t) => short(D.images[t].label)
const IFK = 'Isolation Forest'
const SETS = [
  { k: 'legacy', name: 'Old 23 features', color: 'var(--ink2)', get: (t) => A3.a_legacy_vs_clean.legacy23[t][IFK] },
  { k: 'clean', name: 'Cleaned 17', color: 'var(--m1)', get: (t) => A3.a_legacy_vs_clean.clean[t][IFK] },
  { k: 'final', name: 'Final 19 (clean + burst)', color: 'var(--m0)', get: (t) => A3.c_burst.clean_plus_burst[t][IFK], hi: true }
]
const WHY = {
  credential_tool: 'Set once for the whole disk, so every file gets the same value. It also tested names taken from Image 1’s own answer key (Cain, Ethereal, NetStumbler), which leaks the answer.',
  sniffer_tool: 'Same as above: one value for the whole disk, built from Image 1’s own answer-key tool names.',
  powershell_exec: 'Never fires on any file on any disk.',
  cmd_exec: 'One value for the whole disk. It also matched MPCMDRUN, Windows Defender’s own program.',
  script_host: 'Never fires on any file on any disk.',
  usb_present: 'Says a USB device was seen somewhere on the disk, so every file gets 1. It cannot tell which files relate to it.',
  future_m: 'Compares each file with the newest timestamp on the same disk, so no file can ever be later. Always 0 by construction.',
  is_deleted: 'The MFT export holds no deleted records, so the flag is always 0.'
}
const KIND = { credential_tool: 'disk-level flag', sniffer_tool: 'disk-level flag', powershell_exec: 'disk-level flag', cmd_exec: 'disk-level flag', script_host: 'disk-level flag', usb_present: 'disk-level flag', future_m: 'built never to fire', is_deleted: 'never set' }
const TZ = { img1: 'UTC−5', img2: 'UTC−4', img3: 'UTC−4' }

export default function Cleanup() {
  const groups = DISKS.map((t) => ({ label: dn(t), rows: SETS.map((s) => { const a = s.get(t); return { label: s.name, v: a.at20 / NT[t] * 100, text: f1(a.at20) + ' / ' + NT[t], color: s.color, hi: s.hi } }) }))
  const fx = (f) => AU.fixed.find((r) => r.feature === f)
  const ah = fx('after_hours_touch'), pf = fx('per_file_prefetch_hit')
  return (
    <Section id="cleanup" letter="E" title="The feature clean-up: what was broken and what it changed">
      <Pr note={<>The clean-up was done <b>before</b> any of the numbers in this page were produced, and ground truth was not used to decide which features to drop.</>}>
        <p>Every model ranks files using <b>features</b>: numbers worked out for each file, such as how far its timestamps disagree or how deep its folder is. The earlier results used 23 of them. Before running the study, each one was checked on all three disks, and several turned out to be broken.</p>
        <p>Eight of the 23 were dead: they never changed from file to file, so they could not help a model rank anything. Two more were measuring the wrong thing and were repaired. Two new ones were added. The result is 17 clean features. A pre-registered test then added two burst features, which gives the final 19.</p>
      </Pr>

      <h3 className="rel-h"><span>1</span>Eight features that could not tell files apart</h3>
      <div className="tbl ledger issues"><table>
        <thead><tr><th>Feature</th><th>Kind</th><th className="n">Files set on Image 1</th><th className="n">Image 2</th><th className="n">Image 3</th><th>What was wrong</th></tr></thead>
        <tbody>{AU.dead.map((r) => (
          <tr key={r.feature}><td className="mono">{r.feature}</td><td><Flag kind="warn">{KIND[r.feature]}</Flag></td>
            {DISKS.map((t) => <td key={t} className="n">{r.nonzero[t] >= 99.995 ? 'all' : r.nonzero[t] === 0 ? 'none' : r.nonzero[t] + '%'}</td>)}
            <td style={{ whiteSpace: 'normal', minWidth: 260 }}>{WHY[r.feature]}</td></tr>))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>“All” means every file on the disk has the value 1, “none” means every file has 0. Either way the column is flat. Source: the feature audit, <span className="mono">reports/study_v3/feature_audit.md</span>.</p></Pr>

      <h3 className="rel-h"><span>2</span>Two features repaired, two added</h3>
      <div className="tbl ledger issues"><table>
        <thead><tr><th>Feature</th><th>Change</th><th className="n">Image 1, before → after</th><th className="n">Image 2</th><th className="n">Image 3</th></tr></thead>
        <tbody>
          <tr><td className="mono">after_hours_touch</td><td style={{ whiteSpace: 'normal', minWidth: 260 }}>Working hours were counted on the UTC clock. They are now counted in the disk’s own time zone, read from its registry ({DISKS.map((t) => dn(t) + ': ' + TZ[t]).join(', ')}).</td>
            {DISKS.map((t) => <td key={t} className="n">{ah.before[t]}% → {ah.after[t]}%</td>)}</tr>
          <tr><td className="mono">per_file_prefetch_hit</td><td style={{ whiteSpace: 'normal', minWidth: 260 }}>Prefetch records are matched by program name. The old matching also flagged the prefetch files themselves; that was fixed.</td>
            {DISKS.map((t) => <td key={t} className="n">{pf.before[t]}% → {pf.after[t]}%</td>)}</tr>
          {AU.added.map((r) => (
            <tr key={r.feature}><td className="mono">{r.feature}</td><td style={{ whiteSpace: 'normal', minWidth: 260 }}>{r.feature === 'm_before_cr' ? 'New. Set when a file was modified before it was created, a common sign of a copy or of backdating.' : 'New. Set for script file types such as .ps1, .bat, .cmd, .vbs and .js.'}</td>
              {DISKS.map((t) => <td key={t} className="n">{r.nonzero[t]}% of files</td>)}</tr>))}
        </tbody></table></div>

      <h3 className="rel-h"><span>3</span>What it changed in the results</h3>
      <Pr><p>Cleaning did not improve the headline. At a 20% budget the old 23 features and the final 19 find the same targets. What changed is that the numbers no longer rest on flags that leak the answer or never vary. The first cleaned set of 17 was actually a little weaker, and adding the two burst features brought it back and then some. A burst feature counts how many files share the same modified second or minute. A bulk copy or a wipe stamps many files at once.</p></Pr>
      <Fig n="4" name="feature-sets" caption={<>Targets caught at a 20% budget by Isolation Forest, as a share of all targets, for the old 23 features, the cleaned 17 and the final 19. Means over 5 seeds. Labels give targets caught of targets. Source: A3 of the pre-registered study.</>}>
        <HBars groups={groups} refAt={90} refLabel="90%" aria={'Targets caught at a 20% budget for three feature sets on three disks'} />
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
      <Pr><p className="small" style={{ marginTop: 10 }}>Isolation Forest, mean ± standard deviation over 5 seeds. The burst features raised recall on all three disks and lowered it on none, which is the pre-registered rule for keeping them (A3, burst test: pass). A second rule, “drop any feature whose removal does not hurt”, was applied as written and removed 16 of the 17 features, leaving a set that falls to 0 of 7 on Image 1 at 15%. That result was judged degenerate, reported as a failure, and not used. The reasoning is in the amendment linked in Exhibit L.</p></Pr>
    </Section>
  )
}
