import { useState } from 'react'
import R from '../data/remediation.json'
import { fmt } from '../lib/data'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'
import { imgName } from './Plateau'
import { C1, DISKS, f2 } from '../lib/study'
import { Flag } from '../lib/Prose'

const BUDS = ['20', '15']
const CONF = { low: 1, medium: 2, high: 3 }

const Conf = ({ c }) => (
  <span className={'rm-conf c-' + c} role="img" aria-label={'confidence ' + c}>
    <span className="rm-bars" aria-hidden="true"><i></i><i></i><i></i></span>{c}
  </span>
)

function Rec({ r, n }) {
  const reads = r.commands.filter((c) => c.kind === 'read').length
  const chg = r.commands.length - reads
  return (
    <li className={'rm-ent conf-' + r.confidence}>
      <span className="rm-no" aria-hidden="true">{n}</span>
      <div className="rm-body">
        <h3 className="rm-t">{r.title}</h3>
        <p className="rm-meta">
          {r.mitre ? <span className="ctag" title={r.mitreName || ''}>{r.mitre}</span> : <span className="ctag rm-nomitre">no technique claimed</span>}
          {r.mitreAlso && r.mitreAlso.length ? r.mitreAlso.map((x) => <span key={x} className="ctag">{x}</span>) : null}
          <Conf c={r.confidence} />
          {r.requiresApproval ? <span className="rm-appr">needs approval</span> : <span className="rm-appr ro">no system change offered</span>}
        </p>
        <p className="rm-why">{r.confidenceWhy}</p>
        <p className="small rm-trig"><b>Trigger.</b> {r.trigger.detail} <span className="rm-op">{r.trigger.operatingPoint}</span></p>

        <details className="rm-files">
          <summary>{r.trigger.files.length} supporting flagged files, with ranks</summary>
          <div className="tbl"><table className="rm-ft">
            <thead><tr><th className="n">Rank</th><th>Path</th></tr></thead>
            <tbody>{r.trigger.files.map((f) => (
              <tr key={f.rank + f.path}><td className="n">{fmt(f.rank)}</td><td className="rm-p">{f.path}{f.generic ? <small> generic OS file</small> : null}</td></tr>))}</tbody>
          </table></div>
        </details>

        <h4 className="rm-h">What to do</h4>
        <ol className="rm-act">{r.actions.map((a, i) => <li key={i}>{a}</li>)}</ol>

        <h4 className="rm-h">Commands <small>{reads} read-only{chg ? ', ' + chg + ' change the system' : ''}</small></h4>
        <ul className="rm-cmds">{r.commands.map((c, i) => (
          <li key={i} className={'rm-c ' + c.kind}>
            <p className="rm-cd"><span className={'rm-k ' + c.kind}>{c.kind === 'read' ? 'read-only' : 'changes system, needs approval'}</span>{c.desc}</p>
            <pre className="rm-code" tabIndex={0}><code>{(c.kind === 'change' ? (r._xp ? 'REM ' : '# ') + '[CHANGES SYSTEM] ' : '') + c.cmd}</code></pre>
            {c.note ? <p className="small rm-note">{c.note}</p> : null}
          </li>))}</ul>

        {r.notApplicable.length ? (
          <details className="rm-na">
            <summary>{r.notApplicable.length} left out because this OS lacks {r.notApplicable.length === 1 ? 'it' : 'them'}</summary>
            <ul>{r.notApplicable.map((x, i) => <li key={i}><b>{x.desc}</b><span className="small"> {x.reason}</span><pre className="rm-code dim"><code>{x.wouldBe.replace(/^PS:/, '')}</code></pre></li>)}</ul>
          </details>) : null}
      </div>
    </li>
  )
}

export default function Remediation({ img }) {
  const [bi, setBi] = useState(0)
  const [cf, setCf] = useState(0)
  const d = R.images[img], bud = BUDS[bi], op = d.ops[bud], o = d.os, old = d.oldVsNew.old
  const xp = o.family === 'xp'
  const recs = op.recs.filter((r) => cf === 0 || CONF[r.confidence] >= 2)
  const hidden = op.recs.length - recs.length
  return (
    <Section id="remediation" letter="H" title="What should be done about it?">
      <Pr note={<>The earlier stage emitted scripts from rules that fire on every disk and could not run on the source OS. This one turns only the fair indicators described in Exhibit D into advice, each tied to named files and ranks, with commands written for the version of Windows the disk actually came from.</>}>
        <p>A flagged file is a lead, not a verdict. For each indicator that fired, this exhibit says what to look at and what, with approval, to change in the <b>live environment the disk came from</b>. Anything that would change a system is commented out and marked.</p>
      </Pr>

      <div className="rm-strip" role="region" aria-label={'Context for ' + imgName(img)}>
        <dl className="rm-dl">
          <div><dt>Disk</dt><dd>{d.label}</dd></div>
          <div><dt>Operating system</dt><dd><b>{o.product}</b> · version {o.version}, build {o.build}{o.servicePack ? ', ' + o.servicePack : ''}</dd></div>
          <div><dt>How it was detected</dt><dd>{o.method}. Path check: {o.pathCheck}.</dd></div>
          <div><dt>Commands written for</dt><dd>{o.shell}; scripts are <span className="mono">.{o.scriptExt}</span></dd></div>
          <div><dt>Operating point</dt><dd>Isolation Forest, {R.meta.operatingPoint.features} features, {bud}% budget ({fmt(op.K)} files){bud === '20' ? ', the headline one' : ''}</dd></div>
        </dl>
        <p className="rm-warn"><b>Live environment only.</b> Every step needs human approval. Never run any of it against seized evidence (ISO/IEC 27037).</p>
      </div>

      <div className="auditbar rm-bar">
        <Seg label="Review budget" items={['20% (headline)', '15%']} value={bi} onPick={setBi} />
        <Seg label="Show" items={['All recommendations', 'Medium and high only']} value={cf} onPick={setCf} />
      </div>

      <h3 className="rel-h"><span>1</span>Recommendations ({op.recs.length})</h3>
      {recs.length ? <ol className="rm-led">{recs.map((r, i) => <Rec key={bud + r.id} r={{ ...r, _xp: xp }} n={i + 1} />)}</ol> : <p className="small">No recommendation reaches this confidence.</p>}
      {hidden > 0 ? <p className="small">{hidden} low-confidence {hidden === 1 ? 'entry is' : 'entries are'} hidden by the filter.</p> : null}

      <h3 className="rel-h"><span>2</span>Not triggered</h3>
      <Pr><p>These indicators did not fire at this budget, so nothing is recommended for them.</p></Pr>
      <ul className="rm-nt">{op.notTriggered.length ? op.notTriggered.map((n) => <li key={n.id}><b>{n.title}</b><span className="small"> {n.reason}</span></li>) : <li><span className="small">Every indicator fired.</span></li>}</ul>

      <h3 className="rel-h"><span>3</span>Old against new, {imgName(img)}</h3>
      <Pr><p>The old stage wrote {old.length} scripts for this disk. Each rule is struck through in red and the reason it was wrong is written beside it. The new advice for the same disk follows.</p></Pr>
      <div className="doc rm-old">{old.map((e) => (
        <div key={e.breach} className="cl bad">
          <div><span className="mk"><svg viewBox="0 0 20 20" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" aria-hidden="true"><path d="M4.5 4.5l11 11M15.5 4.5l-11 11" /></svg></span>
            <p className="cl-text"><span className="mono">{e.script}</span> · {e.rule}</p>
            <small>{e.value}{e.replacedBy ? ' · replaced by ' + e.replacedBy : ' · no fair indicator, dropped'}</small></div>
          <div className="fix"><b>faulty</b>{e.fault}</div>
        </div>))}
      </div>
      <div className="tbl ledger rm-new"><table>
        <thead><tr><th>New recommendation</th><th>Confidence</th><th>Needs approval</th></tr></thead>
        <tbody>{d.ops['20'].recs.map((r) => <tr key={r.id}><td>{r.title}</td><td><Conf c={r.confidence} /></td><td>{r.requiresApproval ? 'yes, for the change commands' : 'no change offered'}</td></tr>)}</tbody>
      </table></div>

      <h3 className="rel-h"><span>4</span>What the old scripts claimed, against what the code does</h3>
      <div className="rm-claims" role="table" aria-label="Claimed behaviour against actual code">
        <div className="rm-cr rm-ch" role="row"><span role="columnheader">Script</span><span role="columnheader">The earlier description said</span><span role="columnheader">What the code does</span><span role="columnheader">Problem</span></div>
        {R.meta.claims.map((c, i) => (
          <div key={i} className="rm-cr" role="row">
            <span className="mono rm-cs" role="cell">{c.script}</span>
            <span className="rm-cl" role="cell"><em>Said</em>{c.claimed}</span>
            <span role="cell"><em>Does</em>{c.actual}</span>
            <span role="cell"><em>Problem</em>{c.problem}</span>
          </div>))}
      </div>
      <Eval bud={bud} />
    </Section>
  )
}

const SYS = [['v1', 'Old rules (v1)'], ['v2_all', 'New, all recommendations'], ['v2_medium+', 'New, medium and high confidence only']]
const PFlag = ({ ok }) => <Flag kind={ok ? 'ok' : 'err'}>{ok ? 'pass' : 'fail'}</Flag>

function Eval({ bud }) {
  const rows = (t, b) => C1.disks[t].rows.filter((r) => r.budget === b)
  const pooled = (sys) => {
    let tp = 0, fp = 0, fn = 0
    DISKS.forEach((t) => rows(t, bud).filter((r) => r.system === sys).forEach((r) => { tp += r.tp; fp += r.fp; fn += r.fn }))
    return { tp, fp, fn, p: tp / (tp + fp), r: tp / (tp + fn) }
  }
  const ind = Object.fromEntries(C1.reference.indicators)
  const nm = (s) => (s ? s.split('|').map((x) => ind[x] || x).join(', ') : 'none')
  const allCite = DISKS.flatMap((t) => C1.disks[t].checks.cite), cites = allCite.filter((c) => c.pass).length
  const allChg = DISKS.flatMap((t) => C1.disks[t].checks.changesCommented), chg = allChg.filter((c) => c.pass).length
  const evFail = DISKS.reduce((a, t) => a + C1.disks[t].checks.evidenceCmdFails.length, 0)
  const osFail = DISKS.reduce((a, t) => a + C1.disks[t].checks.osViolations.length, 0)
  const stab = DISKS.every((t) => Object.values(C1.disks[t].stability).every((v) => v === 1))
  return (
    <>
      <h3 className="rel-h"><span>5</span>Does the new advice work? Old rules against new, scored on the known cases</h3>
      <Pr note={<>This is a small test: three disks and nine possible indicators. A score of 3 of 4 on one disk is a count, not a rate. The case descriptions are public, and the expected indicators were written down before the comparison.</>}>
        <p>Each disk comes from a documented case, so we know roughly what happened on it. For each of nine indicators (timestomping, wiping tools, USB use, cloud sync, hacking tools, document traces, browser activity, log clearing, malware), the case description says yes or no. <b>Precision</b> is the share of triggered indicators that really happened. <b>Recall</b> is the share of real indicators that were triggered. Results for the {bud}% budget.</p>
      </Pr>
      <div className="tbl ledger"><table>
        <thead><tr><th>Disk</th><th>Case description</th><th>Old rules triggered</th><th className="n">Precision, recall</th><th>New advice triggered</th><th className="n">Precision, recall</th></tr></thead>
        <tbody>{DISKS.map((t) => { const o = rows(t, bud).find((r) => r.system === 'v1'), n = rows(t, bud).find((r) => r.system === 'v2_all'); return (
          <tr key={t}><td>{imgName(t)}</td><td style={{ whiteSpace: 'normal', minWidth: 200 }}>{C1.reference.case[t]}</td>
            <td style={{ whiteSpace: 'normal', minWidth: 180 }}>{nm(o.triggered)}</td><td className="n">{f2(o.precision)}, {f2(o.recall)}</td>
            <td style={{ whiteSpace: 'normal', minWidth: 180 }}>{nm(n.triggered)}</td><td className="n">{f2(n.precision)}, {f2(n.recall)}</td></tr>) })}</tbody></table></div>
      <div className="tbl ledger"><table>
        <thead><tr><th>All three disks pooled</th><th className="n">Real indicators found</th><th className="n">False alarms</th><th className="n">Precision</th><th className="n">Recall</th></tr></thead>
        <tbody>{SYS.map(([k, lab]) => { const x = pooled(k); return <tr key={k} className={k === 'v1' ? '' : 'cur'}><td>{lab}</td><td className="n">{x.tp} of {x.tp + x.fn}</td><td className="n">{x.fp}</td><td className="n">{f2(x.p)}</td><td className="n">{f2(x.r)}</td></tr> })}</tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>The old rules fire nearly the same set on every disk whatever it contains: timestamp tampering, USB use and malware on all three, and log clearing on two. The case descriptions do not list malware or log clearing for any disk. The new advice finds most of what the cases describe, but it still raises false alarms (6 of its 13 triggers). Keeping only medium and high confidence entries cuts those to 2 of 8, at the cost of some recall. The budget makes no difference: 15% and 20% give identical results. One limit: the new advice has no browser indicator, so Image 3’s browser use can never be found.</p></Pr>

      <h4 className="rm-h">Checks on the new advice <small>all disks, both budgets</small></h4>
      <div className="tbl ledger"><table>
        <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
        <tbody>
          <tr><td>Every recommendation cites at least one flagged file</td><td><PFlag ok={cites === allCite.length} /></td><td>{cites} of {allCite.length} recommendations; every cited file is inside the flagged set at its stated rank</td></tr>
          <tr><td>No command targets the evidence image</td><td><PFlag ok={evFail === 0} /></td><td>{evFail} commands name a disk-image file, a raw device or an imaging tool; all paths are live-system paths</td></tr>
          <tr><td>Every system-changing command is commented out</td><td><PFlag ok={chg === allChg.length} /></td><td>{chg} of {allChg.length} generated script files</td></tr>
          <tr><td>No command uses a tool the operating system lacks</td><td><PFlag ok={osFail === 0} /></td><td>{osFail} violations. This is a pattern scan, not an execution: it cannot prove a command works</td></tr>
          <tr><td>Same advice at 15% and 20%, and across 5 seeds</td><td><PFlag ok={stab} /></td><td>The set of recommendations is identical in every case (overlap 1.00)</td></tr>
        </tbody></table></div>
      <Pr><p className="small" style={{ marginTop: 10 }}>The pre-registered rule for this step (C1) was that every recommendation cites a flagged file and that old and new precision are reported. Both are done. Nothing here says the commands are safe to run on a real machine: that still needs a person.</p></Pr>
    </>
  )
}
