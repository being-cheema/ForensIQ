import { useState } from 'react'
import { D, short } from '../lib/data'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr, Flag } from '../lib/Prose'
import { A1, A2, A3, A4, A5, A6, A7, DISKS, NT, MNAME, f1, rangeTxt } from '../lib/study'
import { Fig } from './Plateau'
import HBars from './HBars'

const dn = (t) => short(D.images[t].label)
const PF = ({ ok }) => <Flag kind={ok ? 'ok' : 'err'}>{ok ? 'pass' : 'fail'}</Flag>
const MX = ({ n }) => <Flag kind="warn">{n}</Flag>

/* One pre-registered rule: its verdict, the rule as written in advance, and what the numbers showed. */
function Rule({ ok, rule, found, tag }) {
  return (
    <div className="prule">
      <div className="prule-v">{tag || <PF ok={ok} />}</div>
      <div><p className="prule-t"><b>Rule.</b> {rule}</p>{found ? <p className="small prule-f">{found}</p> : null}</div>
    </div>
  )
}
function Head({ q, children }) {
  return <div className="pq"><p className="pq-q">{q}</p>{children}</div>
}

/* ------------------------------------------------------------------ A1 */
const A1ROWS = [['full clean set', 'All 19 features'], ['only Temporal', 'Only timestamp features'], ['all except Temporal', 'Everything but timestamps'], ['only Path/File', 'Only path and file features'], ['all except Path/File', 'Everything but path and file'], ['only Execution/Activity', 'Only activity features'], ['all except Execution/Activity', 'Everything but activity']]
function PanelA1() {
  const r1 = A1.rule1
  const groups = DISKS.map((t) => ({ label: dn(t), rows: A1ROWS.map(([k, lab], i) => { const a = A1.results[k][t].IF; return { label: lab, v: a.at15 / NT[t] * 100, text: f1(a.at15) + ' / ' + NT[t], color: 'var(--m0)', hi: i === 0 } }) }))
  const lowers = (g) => (r1[g].length ? r1[g].map(dn).join(', ') : 'nowhere')
  return (
    <>
      <Head q="Does the result depend on all three groups of features, or only on one?">
        The 19 features fall into three groups: timestamps (7), path and file (9), and activity (3: prefetch and the two burst counts). Each group was used alone and then removed, on all three disks.
      </Head>
      <Rule ok={A1.pass.rule1} rule="Removing any single group lowers recall at the headline budget on at least one disk." found={'Removing timestamps lowers recall ' + lowers('Temporal') + '. Removing path and file features lowers it on ' + lowers('Path/File') + ', and removing activity features lowers it on ' + lowers('Execution/Activity') + '. On Image 3, dropping the timestamps actually raised recall slightly at 15%.'} />
      <Rule ok={A1.pass.rule2} rule="No single group alone matches the full set on all disks." found="No group matches alone on every disk. Path and file features alone match on Images 2 and 3 but not on Image 1." />
      <Fig n="5" name="feature-groups" caption={<>Targets caught at a 15% budget by Isolation Forest with groups of features kept alone or removed, as a share of all targets. Means over 5 seeds. The outlined bar is the full set of 19.</>}>
        <HBars groups={groups} refAt={90} refLabel="90%" aria="Targets caught at 15% for each group of features on each disk" />
      </Fig>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Features used</th><th className="n">IF at 15%</th><th className="n">IF at 20%</th><th className="n">LOF at 20%</th><th className="n">OC-SVM at 20%</th></tr></thead>
        <tbody>{DISKS.map((t) => A1ROWS.map(([k, lab], i) => {
          const r = A1.results[k][t]
          return <tr key={t + k} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? dn(t) : ''}</td><td>{lab}</td>
            <td className="n">{f1(r.IF.at15)} ± {f1(r.IF.at15_sd)}</td><td className="n">{f1(r.IF.at20)} ± {f1(r.IF.at20_sd)}</td><td className="n">{r.LOF.at20}</td><td className="n">{r.OCSVM.at20}</td></tr>
        }))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Targets caught, of {DISKS.map((t) => NT[t]).join(', ')}. Isolation Forest is the mean ± standard deviation over 5 seeds. LOF and One-Class SVM were run with one seed (42) only.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A2 */
function PanelA2() {
  const spread = (k) => DISKS.map((t) => A2.disks[t].models[k].summary.knee_spread_pp)
  const names = { 'IF@15': 'Isolation Forest', 'IF@20': 'Isolation Forest', 'LOF@15': 'LOF', 'LOF@20': 'LOF', 'OC-SVM@15': 'One-Class SVM', 'OC-SVM@20': 'One-Class SVM' }
  return (
    <>
      <Head q="If the random seed changes, does the model give the same answer?">
        Isolation Forest and One-Class SVM involve chance. Each was run with five seeds. The “90% point” is the budget at which 90% of the targets have been found. The charts for this test are Figures 1 and 2 in Exhibit C.
      </Head>
      <Rule ok={false} tag={<PF ok={false} />} rule="The 90% point moves by at most 2 percentage points between seeds, and the headline budget catches at least 90% of targets in every seed on every disk." found="Every model fails as written. Isolation Forest passes the second half at 20% but not the first." />
      <div className="tbl ledger"><table>
        <thead><tr><th>Model</th><th className="n">Budget</th><th className="n">90% point moves by (Image 1 / 2 / 3)</th><th>At most 2 points?</th><th>90% caught in every seed?</th><th>Rule</th></tr></thead>
        <tbody>{Object.keys(A2.pass).map((k, i) => {
          const p = A2.pass[k], mk = k.split('@')[0], bud = k.split('@')[1]
          return <tr key={k} className={i % 2 === 0 ? 'grp' : ''}><td>{i % 2 === 0 ? names[k] : ''}</td><td className="n">{bud}%</td>
            <td className="n">{spread(mk).map((v) => f1(v)).join(' / ')} points</td><td><PF ok={p.knee_spread_ok} /></td><td><PF ok={p.recall_ok} /></td><td><PF ok={p.pass} /></td></tr>
        })}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>LOF has no random component, so its spread is zero by construction and its failure is about recall: it does not catch 90% of targets at either budget. In plain terms, the recommended budget works in every seed at 20%, but the point where it first works is not stable.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A3 */
function PanelA3() {
  const drop = A3.b_drop_one, feats = Object.keys(drop)
  const arms = ['v1 (legacy23 IF)', 'v2 (8 feat + burst IF)', 'clean IF', 'clean+burst IF']
  const armName = { 'v1 (legacy23 IF)': 'v1: old 23 features', 'v2 (8 feat + burst IF)': 'v2: 8 chosen features + burst', 'clean IF': 'Cleaned 17', 'clean+burst IF': 'Final 19' }
  const an = A3.e_anonymizer.img1, miss = an.v1_missed_v2_caught_seed42
  const cs = ['img1', 'img2', 'img3']
  return (
    <>
      <Head q="Which features should stay, and was the cleaning worth it?">
        Two pre-registered rules decide this. The first removes each feature in turn; the second asks whether the two burst features help. The comparison of the old 23 features with the cleaned set is in Exhibit E.
      </Head>
      <Rule ok={false} rule="Keep a feature only if removing it does not raise recall on any disk at 15% or 20%." found="Applied as written, this removed 16 of the 17 features and left three. That set falls from 6 targets to 0 on Image 1 at 15%, so it is degenerate. Removing features one at a time is not additive, and most of the “raises” were inside seed noise (for example +0.2 of a target). The rule is reported as failed, and it was not used to pick the final set." />
      <Rule ok={A3.c_burst.passes} rule="The burst features enter the set only if they raise recall on at least one disk and lower it on none." found={'They raised Isolation Forest recall on all three disks (+' + A3.c_burst.delta.img1.map((v) => v).join('/') + ' targets on Image 1, +' + A3.c_burst.delta.img2.join('/') + ' on Image 2, +' + A3.c_burst.delta.img3.join('/') + ' on Image 3, at 15%/20%) and lowered it on none. This is the rule that chose the final 19 features (Amendment 1).'} />
      <h4 className="rel-h"><span>1</span>Removing one feature at a time</h4>
      <Pr><p>Change in targets caught by Isolation Forest, averaged over 5 seeds, when one feature is left out of the cleaned 17. Positive means recall went up without it. Each cell shows the change at 15% and at 20%.</p></Pr>
      <div className="tbl ledger"><table>
        <thead><tr><th>Feature removed</th>{cs.map((t) => <th key={t} className="n">{dn(t)}</th>)}<th>Recall went up on</th></tr></thead>
        <tbody>{feats.map((f) => (
          <tr key={f}><td className="mono">{f}</td>{cs.map((t) => <td key={t} className="n">{drop[f].IF_delta[t].map((v) => (v > 0 ? '+' : '') + f1(v)).join(' / ')}</td>)}<td>{drop[f].raises_on.length ? drop[f].raises_on.map(dn).join(', ') : 'none'}</td></tr>))}</tbody></table></div>

      <h4 className="rel-h"><span>2</span>The earlier “v2” against “v1”, for the record</h4>
      <Pr note={<><b>This is not a fair comparison.</b> v2’s feature list was picked after seeing results on these disks, it has 8 features against 23, it includes burst information v1 lacks, and it ran with one seed on one model.</>}>
        <p>An earlier version of this project claimed a “v2” feature set beat the original “v1”. The table repeats that comparison exactly as it was defined. It is kept so the claim can be checked, not as evidence.</p>
      </Pr>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Arm</th><th className="n">At 5%</th><th className="n">At 15%</th><th className="n">At 20%</th></tr></thead>
        <tbody>{cs.map((t) => ['v1', 'v2'].map((a, i) => { const r = A3.d_v1_v2[a][t]; return <tr key={t + a} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? dn(t) : ''}</td><td>{a === 'v1' ? 'v1: old 23 features' : 'v2: 8 features + burst'}</td><td className="n">{r.at5} / {r.targets}</td><td className="n">{r.at15} / {r.targets}</td><td className="n">{r.at20} / {r.targets}</td></tr> }))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Seed 42, Isolation Forest. v2 looked better only at 5% on Image 1. On Images 2 and 3 it was worse at every budget, so the claim does not hold up.</p></Pr>

      <h4 className="rel-h"><span>3</span>Fact-check: the Anonymizer files on Image 1</h4>
      <Pr><p>The earlier claim was that v2 “caught 65 of 70 Anonymizer files that v1 missed”. Counting every file with “anonymizer” in its path on Image 1 gives <b>{an.n_files} files</b>. At a 5% budget v1 flagged only {an.arms['v1 (legacy23 IF)']['5%'].seed42} of them, so it missed {miss['5%'].v1_missed}, and v2 caught <b>{miss['5%'].v2_caught_of_those} of those {miss['5%'].v1_missed}</b>. The claim holds in substance, with the wrong denominator. It is also a 5% result: with a bigger budget the gap closes.</p></Pr>
      <div className="tbl ledger"><table>
        <thead><tr><th>Arm</th><th className="n">Flagged at 5%</th><th className="n">At 15%</th><th className="n">At 20%</th></tr></thead>
        <tbody>{arms.map((a) => <tr key={a}><td>{armName[a]}</td>{['5%', '15%', '20%'].map((b) => <td key={b} className="n">{an.arms[a][b].seed42} of {an.n_files}<small className="small"> (5-seed mean {f1(an.arms[a][b].mean5)})</small></td>)}</tr>)}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Of the files v1 missed, v2 caught {miss['5%'].v2_caught_of_those} of {miss['5%'].v1_missed} at 5%, {miss['15%'].v2_caught_of_those} of {miss['15%'].v1_missed} at 15% and {miss['20%'].v2_caught_of_those} of {miss['20%'].v1_missed} at 20%. The other two disks have no Anonymizer files.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A4 */
const A4N = { IF: 'Isolation Forest', LOF: 'LOF', 'OC-SVM': 'One-Class SVM', 'R1 timestamp mismatch (delta_si_fn)': 'Rule 1: timestamp mismatch', 'R2 modified before created': 'Rule 2: modified before created', 'R3 location (temp+user+exe+script+archive)': 'Rule 3: location and file type', 'R4 recency (latest m_time first)': 'Rule 4: newest first', 'R5 random order (mean of 5 seeds)': 'Rule 5: random order' }
function PanelA4() {
  const cols = ['var(--m0)', 'var(--m1)', 'var(--m2)', 'var(--ink2)', 'var(--ink2)', 'var(--ink2)', 'var(--ink2)', 'var(--rule)']
  const groups = DISKS.map((t) => ({ label: dn(t), rows: A4.disks[t].rows.map((r, i) => ({ label: A4N[r.method], v: r.at20 / NT[t] * 100, text: f1(r.at20) + ' / ' + NT[t], color: cols[i], hi: i === 0 })) }))
  const win = (k) => A4.pass[k]
  return (
    <>
      <Head q="Does the model beat simple rules that need no machine learning?">
        Five plain rules rank the files with no learning at all, for example “read files in user folders, temp folders, or that are programs, scripts or archives first”. A useful model should do better.
      </Head>
      <Rule ok={win('IF@15')} rule="The model beats the best plain rule at the headline budget on at least two of the three disks." found="Isolation Forest passes at 15% (it wins on Images 1 and 2) and fails at 20%, where it only ties the location rule on Images 1 and 3. LOF and One-Class SVM fail at both budgets." tag={<MX n="pass at 15%, fail at 20%" />} />
      <Fig n="6" name="models-vs-rules" caption={<>Targets caught at a 20% budget by the three models (seed means) and by five plain rules, as a share of all targets. The outlined bar is Isolation Forest. The grey bars are the plain rules. Source: A4.</>}>
        <HBars groups={groups} refAt={90} refLabel="90%" aria="Targets caught at 20% by each model and each plain rule on each disk" labW={220} />
      </Fig>
      <Pr><p><b>Why a plain rule does so well on Image 3.</b> The targets on Image 3 are the files an examiner tagged in the suspect’s home folder. A rule that reads user folders first therefore finds 34 of 34 almost by definition. This says something about how the targets were chosen, not only about the model, and it limits what Image 3 can prove. On Image 2 the same rule finds 16 of 19, and Isolation Forest finds all 19.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A5 */
function PanelA5() {
  const mc = A5.max_change
  const fam = [['IF', 'Isolation Forest', 'trees (50 to 500) and sample size (256 to 1,024 and auto), 16 settings, 5 seeds each'], ['LOF', 'LOF', 'number of neighbours, 10 to 50'], ['OCSVM', 'One-Class SVM', 'share of files allowed outside the boundary, 1% to 10%']]
  const row = (k) => A5[k]
  const ifRange = (t, b) => { const v = Object.keys(row('IF')).map((s) => row('IF')[s][t][b]); return rangeTxt(Math.min.apply(null, v), Math.max.apply(null, v)) }
  return (
    <>
      <Head q="Do the model settings matter?">
        Every model has dials. The study moved each one over a wide range and checked how many targets were caught at the headline budget.
      </Head>
      <Rule ok={A5.pass} rule="Headline recall changes by at most 1 target across the tested settings." found="All three fail as written. Isolation Forest is the steadiest: at 20% it changes by 0 targets on every disk, but at 15% it moves by up to 1.6 targets on Image 3. LOF and One-Class SVM swing by many targets." />
      <div className="tbl ledger"><table>
        <thead><tr><th>Model</th><th>Settings tried</th><th>Disk</th><th className="n">Largest change at 15%</th><th className="n">Largest change at 20%</th><th>Rule</th></tr></thead>
        <tbody>{fam.map(([k, name, what]) => DISKS.map((t, i) => (
          <tr key={k + t} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? name : ''}</td><td style={{ whiteSpace: 'normal', minWidth: 220 }}>{i === 0 ? what : ''}</td><td>{dn(t)}</td>
            <td className="n">{f1(mc[k][t].at15)} targets</td><td className="n">{f1(mc[k][t].at20)} targets</td><td>{i === 0 ? <PF ok={A5.family_pass[k]} /> : ''}</td></tr>)))}</tbody></table></div>
      <h4 className="rel-h"><span>1</span>Targets caught at each setting, 20% budget</h4>
      <div className="tbl ledger"><table>
        <thead><tr><th>Setting</th>{DISKS.map((t) => <th key={t} className="n">{dn(t)} of {NT[t]}</th>)}</tr></thead>
        <tbody>
          <tr className="grp"><td><i className="key" style={{ background: 'var(--m0)' }}></i>Isolation Forest, all 16 settings</td>{DISKS.map((t) => <td key={t} className="n">{ifRange(t, 'at20')}</td>)}</tr>
          {Object.keys(row('LOF')).map((k) => <tr key={'l' + k}><td><i className="key" style={{ background: 'var(--m1)' }}></i>LOF, {k} neighbours</td>{DISKS.map((t) => <td key={t} className="n">{row('LOF')[k][t].at20}</td>)}</tr>)}
          {Object.keys(row('OCSVM')).map((k) => <tr key={'o' + k}><td><i className="key" style={{ background: 'var(--m2)' }}></i>One-Class SVM, {Math.round(k * 100)}% outside the boundary</td>{DISKS.map((t) => <td key={t} className="n">{row('OCSVM')[k][t].at20}</td>)}</tr>)}
        </tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Isolation Forest figures are means over 5 seeds, shown as the lowest to highest across its 16 settings. LOF and One-Class SVM used one seed (42). The defaults are 200 trees with a sample of 256 for Isolation Forest, 20 neighbours for LOF and 5% for One-Class SVM.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A6 */
function PanelA6() {
  const fx = A6.fixed_budget_pct
  return (
    <>
      <Head q="If you choose the budget on one disk, does it work on another?">
        This mimics real use. Find the budget that reaches 90% on one disk, then apply that budget to a different disk and see how much it catches there.
      </Head>
      <Rule ok={false} rule="A budget tuned on any one disk catches at least 90% of targets on the other two." found="All three models fail. For Isolation Forest, the 90% point from Image 2 (9.9%) catches only 75.9% of the targets on Image 3. A fixed 20% budget behaves much better than a tuned one (see below)." />
      <div className="tbl ledger"><table>
        <thead><tr><th>Model</th><th>Tuned on</th><th>Applied to</th><th className="n">Budget</th><th className="n">Targets caught</th><th className="n">Weakest seed</th><th>Caught 90% or more?</th></tr></thead>
        <tbody>{A6.matrix.map((r, i) => (
          <tr key={i} className={i % 6 === 0 ? 'grp' : ''}><td>{i % 6 === 0 ? MNAME[r.model] : ''}</td><td>{dn(r.learned_on)}</td><td>{dn(r.applied_to)}</td><td className="n">{f1(r.knee_from)}%</td><td className="n">{f1(r.pct)}%</td><td className="n">{f1(r.pct_min_seed)}%</td><td><PF ok={r.pct >= 90} /></td></tr>))}</tbody></table></div>
      <h4 className="rel-h"><span>1</span>A fixed budget, with no tuning</h4>
      <div className="tbl ledger"><table>
        <thead><tr><th>Model</th><th className="n">Budget</th>{DISKS.map((t) => <th key={t} className="n">{dn(t)}</th>)}<th>At least 90% on all three?</th></tr></thead>
        <tbody>{Object.keys(fx).map((k, i) => { const v = fx[k]; return <tr key={k} className={i % 2 === 0 ? 'grp' : ''}><td>{i % 2 === 0 ? MNAME[k.split('@')[0]] : ''}</td><td className="n">{k.split('@')[1]}%</td>{DISKS.map((t) => <td key={t} className="n">{f1(v[t])}%</td>)}<td><PF ok={DISKS.every((t) => v[t] >= 90)} /></td></tr> })}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>This second table is not part of the pass rule, which asks about a tuned budget. It shows why the headline is a fixed 20%: Isolation Forest clears 90% on all three disks at 20% and also at 15%, as a mean.</p></Pr>
    </>
  )
}

/* ------------------------------------------------------------------ A7 */
const A7V = [['drop10_nontarget', 'Drop a random 10% of ordinary files', 'Evidence files are kept.'], ['drop10_all', 'Drop a random 10% of all files', 'Evidence files can be dropped too. Judged separately.'], ['noise3600', 'Shift every timestamp by random noise of about one hour', 'Every time feature is recomputed from the noisy times.']]
function PanelA7() {
  return (
    <>
      <Head q="Does it survive messy data?">
        Real images are incomplete and clocks are wrong. Isolation Forest was re-run on disks with files removed, and on disks where every timestamp was jittered by about an hour.
      </Head>
      <Rule ok={A7.verdict.drop10_nontarget && A7.verdict.noise3600} rule="With 10% of files dropped, or with one hour of timestamp noise, recall at the headline budget falls by at most 10%." found="Dropping files passes. One hour of timestamp noise fails: recall falls 14% on Image 1 and 12% on Image 3 at 15%. The two burst features count files that share a modified time, and jitter probably breaks that matching." />
      {A7V.map(([k, title, note]) => (
        <div key={k}>
          <h4 className="rel-h"><span><PF ok={A7.verdict[k]} /></span>{title}</h4>
          <Pr><p className="small">{note}</p></Pr>
          <div className="tbl ledger"><table>
            <thead><tr><th>Disk</th><th className="n">Budget</th><th className="n">Before</th><th className="n">After</th><th className="n">Fall</th><th className="n">Each seed after</th></tr></thead>
            <tbody>{DISKS.map((t) => ['at15', 'at20'].map((b, i) => { const r = A7.results[k][t][b]; return (
              <tr key={t + b} className={(i === 0 ? 'grp' : '')}><td>{i === 0 ? dn(t) : ''}</td><td className="n">{b === 'at15' ? '15%' : '20%'}</td><td className="n">{f1(r.base_mean)} / {NT[t]}</td><td className="n">{f1(r.pert_mean)} / {NT[t]}</td>
                <td className="n">{r.rel_drop_pct <= 0 ? 'none' : f1(r.rel_drop_pct) + '%'}{r.rel_drop_pct > 10 ? ' ' : ''}{r.rel_drop_pct > 10 ? <Flag kind="err">over 10%</Flag> : null}</td><td className="n">{r.pert_per_seed.join(', ')}</td></tr>) }))}</tbody></table></div>
        </div>))}
      <Pr><p className="small" style={{ marginTop: 10 }}>Isolation Forest, 5 seeds, means. “Fall” is the relative drop in targets caught against the unperturbed run with the same seeds.</p></Pr>
    </>
  )
}

const TABS = [
  ['A1 Groups', PanelA1, 'fail'], ['A2 Seeds', PanelA2, 'fail'], ['A3 Features', PanelA3, 'mixed'], ['A4 Plain rules', PanelA4, 'mixed'], ['A5 Settings', PanelA5, 'fail'], ['A6 Other disks', PanelA6, 'fail'], ['A7 Messy data', PanelA7, 'fail']
]

export default function Ablations() {
  const [t, setT] = useState(0)
  const P = TABS[t][1], st = TABS[t][2]
  return (
    <Section id="reliability" letter="F" title="Reliability: seven ablations">
      <Pr note={<>Seven tests were written down with their pass rules before any result was computed, and they are shown here as run. Strictly, <b>no test passes every one of its rules</b>. Some individual rules do pass: the burst features (A3), the plain-rule comparison at 15% (A4) and dropping files (A7).</>}>
        <p>An ablation changes one thing and watches what happens. Each tab below asks a plain question, states the pass rule that was fixed in advance, and shows the evidence. Failures are reported as failures, and nothing was re-tuned after seeing a result.</p>
        <p>All of it uses the final 19 features. Choose a test.</p>
      </Pr>
      <div className="auditbar"><Seg label="Ablation" items={TABS.map((x) => x[0])} value={t} onPick={setT} />
        <span className="small">Overall: {st === 'fail' ? <PF ok={false} /> : <MX n="mixed" />}</span></div>
      <div className="abl" key={t}><P /></div>
    </Section>
  )
}
