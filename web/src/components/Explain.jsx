import { useState } from 'react'
import { D, short } from '../lib/data'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr, Flag } from '../lib/Prose'
import { B, DISKS, MK, MCOL, f1, f2 } from '../lib/study'
import { Fig } from './Plateau'
import HBars from './HBars'

const dn = (t) => short(D.images[t].label)
const PF = ({ ok }) => <Flag kind={ok ? 'ok' : 'err'}>{ok ? 'pass' : 'fail'}</Flag>
const SHORTM = { IF: 'Isolation Forest', LOF: 'LOF', 'OC-SVM': 'One-Class SVM' }
const BUDS = ['20', '15']

const cellB1 = (t, k, b) => B.disks[t][k].B1[b]
const cellB2 = (t, k, b) => {
  const x = B.disks[t][k].B2, sd = x.seeds ? x.seeds[b].mean_jaccard : null, nz = x.noise[b].mean_jaccard
  return { sd, nz, top1: x.noise[b].top1_same, ok: (sd == null || sd >= B.thresholds.B2_seed) && nz >= B.thresholds.B2_noise }
}
const cellB3 = (t, k, b) => B.disks[t][k].B3.ALL[b]
const b3ok = (c) => c.attr_hit_detected_pct >= B.thresholds.B3_attr * 100
const ratioTxt = (c) => (c.ratio == null || c.median_drop_shap <= 0 || c.median_drop_random <= 0 ? 'n/a' : c.ratio >= 100 ? Math.round(c.ratio) + '×' : f1(c.ratio) + '×')
const pTxt = (p) => (p == null ? 'n/a' : p < 1e-4 ? '< 0.0001' : p.toFixed(3))
const ATK = ['P1 timestamp forgery', 'P2 hidden executable in temp', 'P3 bulk-wipe burst']

function Rules({ b }) {
  const all = (fn) => DISKS.every((t) => MK.every((k) => fn(t, k)))
  return (
    <div className="tbl ledger"><table>
      <thead><tr><th>Test</th><th>What it asks, fixed in advance</th><th>Result</th><th>Cells that fail, of 9 (3 disks × 3 models)</th></tr></thead>
      <tbody>
        {[['B1 Faithfulness', 'Overwriting the three features SHAP names should push a file down the ranking much further than overwriting three random features (one-sided Wilcoxon test, p below 0.01).', (t, k) => cellB1(t, k, b).pass],
          ['B2 Stability', 'The three named features should overlap by at least 0.7 across seeds and by at least 0.6 when the input is jittered by 1%.', (t, k) => cellB2(t, k, b).ok],
          ['B3 Planted attacks', 'For planted attacks the model detects, SHAP’s top three should name the planted cause at least 80% of the time.', (t, k) => b3ok(cellB3(t, k, b))]].map(([n, what, fn]) => {
          const bad = []
          DISKS.forEach((t) => MK.forEach((k) => { if (!fn(t, k)) bad.push(dn(t) + ' ' + SHORTM[k]) }))
          return <tr key={n}><td><b>{n}</b></td><td style={{ whiteSpace: 'normal', minWidth: 300 }}>{what}</td><td><PF ok={all(fn)} /></td><td style={{ whiteSpace: 'normal' }}>{bad.length ? bad.join('; ') : 'none'}</td></tr>
        })}
      </tbody></table></div>
  )
}

export default function Explain() {
  const [bi, setBi] = useState(0)
  const b = BUDS[bi]
  const g1 = DISKS.map((t) => ({ label: dn(t), rows: MK.map((k) => { const c = cellB1(t, k, b); return { label: SHORTM[k], v: c.share_shap_beats_random * 100, text: f1(c.share_shap_beats_random * 100) + '% · ' + ratioTxt(c), color: 'var(' + MCOL[k] + ')' } }) }))
  const g2 = DISKS.map((t) => ({ label: dn(t), rows: MK.map((k) => { const c = cellB2(t, k, b); return { label: SHORTM[k], v: c.nz * 100, text: f2(c.nz), color: 'var(' + MCOL[k] + ')' } }) }))
  const g3 = DISKS.map((t) => ({ label: dn(t), rows: MK.flatMap((k) => { const c = cellB3(t, k, b); return [
    { label: SHORTM[k] + ': detected', v: c.detect_pct, text: f1(c.detect_pct) + '%', color: 'var(' + MCOL[k] + ')', dim: true },
    { label: SHORTM[k] + ': cause named', v: c.attr_hit_detected_pct, text: f1(c.attr_hit_detected_pct) + '%', color: 'var(' + MCOL[k] + ')' }] }) }))
  const ifDet = DISKS.map((t) => cellB3(t, 'IF', b).detect_pct), ifAtt = DISKS.map((t) => cellB3(t, 'IF', b).attr_hit_detected_pct)
  return (
    <Section id="explain" letter="G" title="Explainability: can you trust the explanation?">
      <Pr note={<>For Isolation Forest and One-Class SVM, all three tests pass on all three disks. <b>LOF is the one that fails</b>, and because the study required every cell to pass, each test is reported as failed overall.</>}>
        <p>An examiner is shown not only a ranked list but a <b>reason</b> for each file: the three features that pushed its score up the most. This is only useful if the reason is real. Three tests, again fixed before running, check that.</p>
        <p>The reasons come from SHAP, a method that splits a model’s score into a contribution per feature. All numbers use the final 19 features and the files in the top {b}% of the disk.</p>
      </Pr>
      <div className="auditbar"><Seg label="Flagged share" items={['Top 20% (headline)', 'Top 15%']} value={bi} onPick={setBi} /></div>
      <Rules b={b} />

      <h3 className="rel-h"><span>1</span>Faithfulness: does removing the reason hurt?</h3>
      <Pr><p>For flagged files, the three features SHAP names are overwritten with typical values, the same model scores the file again, and we see how far it falls in the ranking. As a control, three random features are overwritten instead. If the reason is real, the first fall should be much larger.</p></Pr>
      <Fig n="8" name="faithfulness" caption={<>Share of flagged files that fall further when SHAP’s three features are removed than when three random features are removed, for each disk and model. The label also gives how many times larger the typical fall was. Isolation Forest and One-Class SVM are close to 100%. LOF is below 50%, which is no better than chance.</>}>
        <HBars groups={g1} refAt={50} refLabel="chance" aria="Share of flagged files where removing the SHAP reason moves the file down more than removing random features" />
      </Fig>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Model</th><th className="n">Files tested</th><th className="n">Typical fall, SHAP features</th><th className="n">Typical fall, random</th><th className="n">Wilcoxon p</th><th>Result</th></tr></thead>
        <tbody>{DISKS.map((t) => MK.map((k, i) => { const c = cellB1(t, k, b); return (
          <tr key={t + k} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? dn(t) : ''}</td><td><i className="key" style={{ background: 'var(' + MCOL[k] + ')' }}></i>{SHORTM[k]}</td>
            <td className="n">{c.n}</td><td className="n">{Math.round(c.median_drop_shap).toLocaleString('en-US')} places</td><td className="n">{Math.round(c.median_drop_random).toLocaleString('en-US')} places</td><td className="n">{pTxt(c.wilcoxon_p)}</td><td><PF ok={c.pass} /></td></tr>) }))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>LOF is a local density method. Overwriting a few features can move a file to a different sparse corner instead of a dense one, so the rank does not fall, and its negative falls mean files moved <i>up</i>. That makes LOF’s SHAP reasons unreliable here.</p></Pr>

      <h3 className="rel-h"><span>2</span>Stability: does the reason stay the same?</h3>
      <Pr><p>An explanation that changes every time you rerun is not an explanation. We refit with five seeds and compare the top-three lists, and we add 1% jitter to every input and compare again. The score is the <b>Jaccard overlap</b>: 1 means the same three features, 0 means nothing in common.</p></Pr>
      <Fig n="9" name="stability" caption={<>Overlap of the three named features after refitting on inputs jittered by 1%, for each disk and model (1 is identical). The pass line is 0.6. LOF is deterministic, so it has no seed test, and its noise result is far below the line.</>}>
        <HBars groups={g2} max={100} ticks={[0, 25, 50, 75, 100]} refAt={60} refLabel="0.6" unit="overlap × 100" aria="Overlap of the top three SHAP features under 1% input noise" />
      </Fig>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Model</th><th className="n">Across 5 seeds (need 0.7)</th><th className="n">Under 1% noise (need 0.6)</th><th className="n">Same top reason under noise</th><th>Result</th></tr></thead>
        <tbody>{DISKS.map((t) => MK.map((k, i) => { const c = cellB2(t, k, b); return (
          <tr key={t + k} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? dn(t) : ''}</td><td><i className="key" style={{ background: 'var(' + MCOL[k] + ')' }}></i>{SHORTM[k]}</td>
            <td className="n">{c.sd == null ? 'no seed test' : f2(c.sd)}</td><td className="n">{f2(c.nz)}</td><td className="n">{Math.round(c.top1 * 100)}%</td><td><PF ok={c.ok} /></td></tr>) }))}</tbody></table></div>

      <h3 className="rel-h"><span>3</span>Planted attacks: does the explanation name the real cause?</h3>
      <Pr note={<>Detecting is the model’s job and explaining is SHAP’s. Isolation Forest detects only about half of the planted attacks at {b}% ({f1(Math.min.apply(null, ifDet))}% to {f1(Math.max.apply(null, ifDet))}%), but when it does detect one it names the right cause {f1(Math.min.apply(null, ifAtt))}% to {f1(Math.max.apply(null, ifAtt))}% of the time.</>}>
        <p>Here the cause is known because we put it there. On each disk, 60 ordinary files were copied and one attack was planted in each copy: a forged timestamp, a hidden program in a temp folder, or a burst of files sharing one modified time. We then checked whether the model flagged the copy and whether SHAP’s top three included the planted feature.</p>
      </Pr>
      <Fig n="10" name="planted-attacks" caption={<>For each disk and model, the share of the 60 planted attacks the model flagged (pale bar), and, of those it flagged, the share where SHAP’s top three named the planted cause (solid bar). The pass line is 80% for the solid bar.</>}>
        <HBars groups={g3} refAt={80} refLabel="80%" aria="Detection rate and correct-cause rate for planted attacks" labW={190} />
      </Fig>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Model</th><th>Attack</th><th className="n">Detected</th><th className="n">Cause named, of detected</th></tr></thead>
        <tbody>{DISKS.map((t) => MK.map((k) => ATK.concat(['ALL']).map((a, i) => { const c = B.disks[t][k].B3[a][b]; return (
          <tr key={t + k + a} className={(k === 'IF' && i === 0 ? 'grp' : i === 0 ? 'grp2' : '') + (a === 'ALL' ? ' cur' : '')}><td>{k === 'IF' && i === 0 ? dn(t) : ''}</td><td>{i === 0 ? SHORTM[k] : ''}</td><td>{a === 'ALL' ? 'All three attack types' : a.replace(/^P\d /, '')}</td>
            <td className="n">{f1(c.detect_pct)}%</td><td className="n">{f1(c.attr_hit_detected_pct)}%{a === 'ALL' ? <> <PF ok={c.attr_hit_detected_pct >= 80} /></> : null}</td></tr>) })))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>Isolation Forest figures are means over 5 seeds. Bulk-wipe bursts are the hardest for Isolation Forest to detect (7% to 34% at 20%).</p></Pr>

      <h3 className="rel-h"><span>4</span>Do the reasons make forensic sense?</h3>
      <Pr><p>This one has no pass rule. For the real evidence targets that each model caught, we looked at how often the single strongest reason was something other than file name randomness, folder depth or file size alone, and how often the top three included a feature an examiner would expect for that kind of file.</p></Pr>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Model</th><th className="n">Targets caught</th><th className="n">Top reason is a forensic feature</th><th className="n">Top three include an expected one</th></tr></thead>
        <tbody>{DISKS.map((t) => MK.map((k, i) => { const s = B.disks[t][k].sense; return (
          <tr key={t + k} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? dn(t) : ''}</td><td><i className="key" style={{ background: 'var(' + MCOL[k] + ')' }}></i>{SHORTM[k]}</td>
            <td className="n">{s.n}</td><td className="n">{Math.round(s.top1_sensible * 100)}%</td><td className="n">{Math.round(s.match_expected * 100)}%</td></tr>) }))}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>A high share shows the reason is not an obvious artefact. It does not prove the reason is right. The “expected” lists were written by hand.</p></Pr>
    </Section>
  )
}
