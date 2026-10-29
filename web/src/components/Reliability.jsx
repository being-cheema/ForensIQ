import { useMemo, useRef } from 'react'
import { D, MODELS, SHORT, MVAR, IMGS, SW, fmt, pc, short } from '../lib/data'
import { CFGS, curve, fb, fn1 } from '../lib/curves'
import { useDraw } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr, Flag } from '../lib/Prose'
import { Fig, useBox, imgName } from './Plateau'

const SWEEP_IMGS = IMGS.filter((t) => SW[t])
const GROUPS = [5, 11, 15, 21]
const groupNote = (b) => (b === 5 ? 'strict comparison' : b === 15 ? 'recommended' : '')
const kOf = (x, pct) => Math.max(1, Math.round(pct * x.files))
const caught = (x, m, K) => x.targets.filter((t) => t.ranks[m] <= K).length
const ratio = (s) => { const p = String(s || '').split('/'); return p.length === 2 ? parseInt(p[0], 10) / parseInt(p[1], 10) : null }
const rng = (a) => (Math.min.apply(null, a) === Math.max.apply(null, a) ? String(a[0]) : Math.min.apply(null, a) + '–' + Math.max.apply(null, a))

/* ---------- Figure 4: seed spread, dot and whisker ---------- */
function SpreadPanel({ img }) {
  const box = useRef(), w = useBox(box), sw = SW[img]
  const L = 78, R = 14, T = 8, PITCH = 19, HEAD = 22, GAP = 8, B = 38
  const cfgs = CFGS.filter((c) => sw[c.id])
  const gh = HEAD + cfgs.length * PITCH
  const H = T + GROUPS.length * (gh + GAP) + B
  const pw = Math.max(60, w - L - R), X = (v) => L + (v / 100) * pw
  const col = (c) => 'var(' + c.v + ')'
  return (
    <div ref={box} className="fpanel">
      <h4 className="fph">{imgName(img)}</h4>
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Mean evidence recall with one standard deviation across 5 seeds and 3 randomizations on ' + imgName(img) + ', at budgets of ' + GROUPS.join(', ') + '%'}>
          {[0, 25, 50, 75, 100].map((v) => <line key={v} className="gl" x1={X(v)} x2={X(v)} y1={T} y2={H - B} />)}
          <line className="ref" x1={X(90)} x2={X(90)} y1={T} y2={H - B} />
          {GROUPS.map((b, gi) => {
            const y0 = T + gi * (gh + GAP)
            return (
              <g key={b}>
                <text className="lbl" x={L - 70} y={y0 + 13} style={{ fill: 'var(--ink)' }}>{b}%{groupNote(b) ? ' · ' + groupNote(b) : ''}</text>
                <line className="ax" x1={L - 70} x2={L + pw} y1={y0 + 18} y2={y0 + 18} />
                {cfgs.map((c, ci) => {
                  const d = sw[c.id], j = d.pct.indexOf(b); if (j < 0) return null
                  const y = y0 + HEAD + ci * PITCH + PITCH / 2, r = d.recall[j], s = d.std[j], lo = Math.max(0, r - s), hi = Math.min(100, r + s)
                  return (
                    <g key={c.id}>
                      <text x={L - 8} y={y + 4} textAnchor="end" style={{ fill: col(c) }}>{c.lab2}</text>
                      {s > 0 ? <g stroke={col(c)} strokeWidth="1.6" fill="none">
                        <line className="draw" x1={X(lo)} x2={X(hi)} y1={y} y2={y} />
                        <line x1={X(lo)} x2={X(lo)} y1={y - 4} y2={y + 4} /><line x1={X(hi)} x2={X(hi)} y1={y - 4} y2={y + 4} /></g> : null}
                      <circle className="fadein" data-op="1" cx={X(r)} cy={y} r="4" fill={col(c)} stroke="var(--paper)" strokeWidth="1.2" />
                      <title>{c.lab + ' at ' + b + '%: ' + r.toFixed(1) + '% recall, standard deviation ' + s.toFixed(1)}</title>
                    </g>
                  )
                })}
              </g>
            )
          })}
          {[0, 25, 50, 75, 90, 100].map((v) => <text key={v} className={v === 90 ? 'hi' : ''} x={X(v)} y={H - B + 14} textAnchor="middle">{v}</text>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">evidence recall, %</text>
        </svg>
      ) : null}
    </div>
  )
}

/* ---------- Figure 5: hyperparameter dot plot ---------- */
function ParamPanel({ img }) {
  const box = useRef(), w = useBox(box), rb = D.images[img].robustness, N = rb.targets
  const L = 88, R = 16, T = 8, PITCH = 20, B = 38
  const rows = [{ k: 'IF · seeds', v: rb.iforest_seeds, c: 0 }]
    .concat(Object.keys(rb.ocsvm).map((n) => ({ k: 'OC-SVM · n=' + (+n >= 1000 ? +n / 1000 + 'k' : n), v: rb.ocsvm[n], c: 2 })))
    .concat(Object.keys(rb.lof).map((k) => ({ k: 'LOF · k=' + k, v: [rb.lof[k]], c: 1 })))
  const H = T + rows.length * PITCH + B
  const pw = Math.max(60, w - L - R), X = (v) => L + (v / N) * pw
  const ticks = [0, Math.round(N / 2), N]
  return (
    <div ref={box} className="fpanel">
      <h4 className="fph">{imgName(img)} <span className="small">· {N} targets</span></h4>
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Targets caught at 5% on ' + imgName(img) + ' for each hyperparameter setting: ' + rows.map((r) => r.k + ' ' + rng(r.v)).join('; ')}>
          {ticks.map((v) => <line key={v} className="gl" x1={X(v)} x2={X(v)} y1={T} y2={H - B} />)}
          {rows.map((r, i) => {
            const y = T + i * PITCH + PITCH / 2, col = 'var(' + MVAR[r.c] + ')', mn = Math.min.apply(null, r.v), mx = Math.max.apply(null, r.v)
            return (
              <g key={r.k}>
                <text x={L - 8} y={y + 4} textAnchor="end" style={{ fill: col }}>{r.k}</text>
                {mx > mn ? <line className="draw" x1={X(mn)} x2={X(mx)} y1={y} y2={y} stroke={col} strokeWidth="1.6" /> : null}
                {r.v.map((v, j) => {
                  const same = r.v.filter((u) => u === v), idx = r.v.slice(0, j).filter((u) => u === v).length, off = same.length > 1 ? (idx - (same.length - 1) / 2) * 3.4 : 0
                  return <circle key={j} className="fadein" data-op="0.9" cx={X(v)} cy={y + off} r="3.2" fill={col} opacity="0.9" stroke="var(--paper)" strokeWidth="0.8" />
                })}
                <title>{r.k + ': ' + r.v.join(', ') + ' of ' + N + ' targets'}</title>
              </g>
            )
          })}
          {ticks.map((v) => <text key={v} x={X(v)} y={H - B + 14} textAnchor="middle">{v}</text>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">targets caught of {N}</text>
        </svg>
      ) : null}
    </div>
  )
}

/* ---------- Figure 6: same model, three disks ---------- */
function DisksFig({ pct }) {
  const box = useRef(), w = useBox(box)
  const L = 98, R = 46, T = 6, PITCH = 19, GH = 10, B = 36
  const H = T + MODELS.length * (IMGS.length * PITCH + GH) + B
  const pw = Math.max(60, w - L - R), X = (v) => L + v * pw
  return (
    <div ref={box} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Share of targets caught at a ' + pc(pct) + ' budget by each model on each of the three disks'}>
          {[0, 0.25, 0.5, 0.75, 1].map((v) => <line key={v} className="gl" x1={X(v)} x2={X(v)} y1={T} y2={H - B} />)}
          {MODELS.map((m, mi) => {
            const y0 = T + mi * (IMGS.length * PITCH + GH), col = 'var(' + MVAR[mi] + ')'
            return (
              <g key={m}>
                {IMGS.map((t, ti) => {
                  const x = D.images[t], n = x.targets.length, c = caught(x, m, kOf(x, pct)), y = y0 + ti * PITCH + PITCH / 2
                  return (
                    <g key={t}>
                      <text x={L - 8} y={y + 4} textAnchor="end" style={ti === 0 ? { fill: col, fontWeight: 600 } : undefined}>{ti === 0 ? SHORT[mi].replace('Isolation Forest', 'IF').replace('One-Class SVM', 'OC-SVM') + ' · ' : ''}{'Im ' + (ti + 1)}</text>
                      <rect x={L} y={y - 5} width={Math.max(1.5, (c / n) * pw)} height="10" fill={col} opacity={c ? 0.9 : 0.25} />
                      <text className="bv" x={L + (c / n) * pw + 5} y={y + 4}>{c}/{n}</text>
                    </g>
                  )
                })}
              </g>
            )
          })}
          {[0, 25, 50, 75, 100].map((v) => <text key={v} x={X(v / 100)} y={H - B + 14} textAnchor="middle">{v}</text>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">evidence targets caught, %</text>
        </svg>
      ) : null}
    </div>
  )
}

const Sub = ({ n, children }) => <h3 className="rel-h"><span>{n}</span>{children}</h3>

export default function Reliability({ img, m, pct }) {
  const b = pct * 100, body = useRef()
  useDraw(body, [img])
  const bb = Math.max(5, b)

  /* Seed stability readout at the chosen budget */
  const rows = useMemo(() => {
    const out = []
    SWEEP_IMGS.forEach((t) => CFGS.forEach((c, i) => { if (SW[t][c.id]) { const a = curve(t, c.id).at(bb); out.push({ t, c, a, first: i === 0, n: SW[t][c.id].targets }) } }))
    return out
  }, [bb])
  const ifAgree = SWEEP_IMGS.map((t) => SW[t]['IF-23'] ? ratio(SW[t]['IF-23'].agreement) : null).filter((v) => v != null)
  const ifAgreeTxt = ifAgree.length ? Math.round(Math.min.apply(null, ifAgree) * 100) + '–' + Math.round(Math.max.apply(null, ifAgree) * 100) + '%' : ''

  /* cross-disk numbers at the chosen budget */
  const cross = IMGS.map((t) => { const x = D.images[t], K = kOf(x, pct), n = x.targets.length; return { t, x, K, n, c: MODELS.map((mm) => caught(x, mm, K)) } })
  const lead = cross.map((r) => { const mx = Math.max.apply(null, r.c), who = r.c.map((v, i) => v === mx ? i : -1).filter((i) => i >= 0); return who.length === 1 ? SHORT[who[0]] : who.map((i) => SHORT[i]).join(' / ') + ' (tied)' })
  const sameLead = lead.every((l) => l === lead[0])
  const ifRob = IMGS.map((t) => { const r = D.images[t].robustness; return { t, v: r.iforest_seeds, n: r.targets } })
  const widest = ifRob.slice().sort((a, c) => (Math.max.apply(null, c.v) - Math.min.apply(null, c.v)) - (Math.max.apply(null, a.v) - Math.min.apply(null, a.v)))[0]

  /* flags that are constant on every disk */
  const constAll = D.images[IMGS[0]].constant.filter((f) => IMGS.every((t) => D.images[t].constant.indexOf(f) >= 0))
  const toolFlags = constAll.filter((f) => f !== 'future_m' && f !== 'is_deleted')

  const note1 = SWEEP_IMGS.length ? <>Across the three randomizations of the sweep, Isolation Forest on 23 features agrees on the 90% threshold at {ifAgreeTxt} of the budget points tested. That is agreement between randomizations. Between seeds the picture is weaker: see the hyperparameter runs below.</> : null

  return (
    <Section id="reliability" letter="E" title="How reliable is this?">
      <Pr note={note1}>
        <p>A single run of a randomized model can look better or worse than it is. This exhibit separates what survives repetition from what does not. It starts with what holds, and ends with what does not hold yet and the known defects in the features. Numbers follow the budget control where the data allows it.</p>
      </Pr>

      <div ref={body}>
        <h3 className="rel-top">What holds</h3>

        <Sub n="1">Seed stability: how far recall moves between reruns</Sub>
        <Pr><p>Each dot is the mean evidence recall of 5 seeds in 3 randomizations; the whisker is one standard deviation. The dotted line marks 90%. Image 1 was not part of the randomized sweep.</p></Pr>
        <Fig n="5" name="seed-spread" caption={<>Mean evidence recall and spread across 5 seeds × 3 randomizations, at four budgets: 5% is the strict equal-budget comparison and 15% is the recommended budget. A short whisker means reruns agree. A long one means the result depends on the draw: see Isolation Forest at 5% on Image 3.</>}>
          <div className="fgrid d2">{SWEEP_IMGS.map((t) => <SpreadPanel key={t} img={t} />)}</div>
        </Fig>

        <div className="ledgerwrap tight">
          <h3 className="cap">At your {fb(bb)} budget{b < 5 ? ' (the sweep starts at 5%)' : ''}</h3>
          <div className="tbl ledger"><table><thead><tr><th>Disk</th><th>Model</th><th className="n">Targets caught (mean)</th><th className="n">Recall</th><th className="n">Std. dev.</th></tr></thead>
            <tbody>{rows.map((r) => (
              <tr key={r.t + r.c.id} className={(r.first ? 'grp' : '') + (r.t === img ? ' cur' : '')}>
                <td>{r.first ? imgName(r.t) : ''}</td><td><i className="key" style={{ background: 'var(' + r.c.v + ')' }}></i>{r.c.lab}</td>
                <td className="n">{fn1(r.a.found)} / {r.n}</td><td className="n">{r.a.recall.toFixed(1)}%</td><td className="n">{r.a.std.toFixed(1)} pts</td>
              </tr>))}</tbody></table></div>
        </div>

        <div className="ledgerwrap tight">
          <h3 className="cap">Do the three randomizations agree on the 90% threshold?</h3>
          <div className="tbl ledger"><table><thead><tr><th>Disk</th><th>Model</th><th className="n">Run set 1</th><th className="n">Run set 2</th><th className="n">Run set 3</th><th>Agree?</th><th className="n">Budget points agreeing</th></tr></thead>
            <tbody>{SWEEP_IMGS.map((t) => CFGS.map((c, i) => {
              const d = SW[t][c.id]; if (!d) return null
              const g = d.ge90 || {}, cv = (k) => (g[k] == null ? 'never' : g[k] + '%'), r = ratio(d.agreement)
              return (
                <tr key={t + c.id} className={(i === 0 ? 'grp' : '') + (t === img ? ' cur' : '')}>
                  <td>{i === 0 ? imgName(t) : ''}</td><td><i className="key" style={{ background: 'var(' + c.v + ')' }}></i>{c.lab}</td>
                  <td className="n">{cv('R1')}</td><td className="n">{cv('R2')}</td><td className="n">{cv('R3')}</td>
                  <td><Flag kind={d.agree90 ? 'ok' : 'warn'}>{d.agree90 ? 'yes' : 'no'}</Flag></td>
                  <td className="n">{d.agreement}{r != null ? ' · ' + Math.round(r * 100) + '%' : ''}</td>
                </tr>)
            }))}</tbody></table></div>
          <Pr><p className="small" style={{ marginTop: 10 }}>The first columns show the smallest swept budget at which each randomization reaches 90% mean recall. Isolation Forest on 23 features agrees on {ifAgreeTxt} of the budget points tested;</p></Pr>
        </div>

        <Sub n="2">Hyperparameter sensitivity: how much the settings matter</Sub>
        <Pr note={<>These runs score targets caught at the <b>5% equal-budget comparison</b>, which is the only budget at which the sensitivity runs were done.</>}>
          <p>Local Outlier Factor was run with four neighbour counts, One-Class SVM with three training-subsample sizes and five seeds each, and Isolation Forest with five seeds. Each dot is one run.</p>
        </Pr>
        <Fig n="6" name="hyperparameters" caption={<>Targets caught at a 5% budget for every setting tried. Dots in the same row are repeat runs; stacked dots are identical results. Isolation Forest moves with its seed, One-Class SVM barely moves with either seed or sample size, and Local Outlier Factor stays low at every neighbour count.</>}>
          <div className="fgrid">{IMGS.map((t) => <ParamPanel key={t} img={t} />)}</div>
        </Fig>
        <div className="tbl ledger"><table><thead><tr><th>Setting (targets caught at 5%)</th>{IMGS.map((t) => <th key={t} className="n">{short(D.images[t].label)} · {D.images[t].robustness.targets} targets</th>)}</tr></thead>
          <tbody>
            <tr><td><i className="key" style={{ background: 'var(--m0)' }}></i>Isolation Forest · 5 seeds</td>{IMGS.map((t) => <td key={t} className="n">{rng(D.images[t].robustness.iforest_seeds)}</td>)}</tr>
            {Object.keys(D.images[IMGS[0]].robustness.ocsvm).map((n) => <tr key={n}><td><i className="key" style={{ background: 'var(--m2)' }}></i>One-Class SVM · n = {fmt(n)} · 5 seeds</td>{IMGS.map((t) => <td key={t} className="n">{rng(D.images[t].robustness.ocsvm[n])}</td>)}</tr>)}
            {Object.keys(D.images[IMGS[0]].robustness.lof).map((k) => <tr key={k}><td><i className="key" style={{ background: 'var(--m1)' }}></i>LOF · k = {k}</td>{IMGS.map((t) => <td key={t} className="n">{D.images[t].robustness.lof[k]}</td>)}</tr>)}
          </tbody></table></div>

        <h3 className="rel-top rel-no">What does not hold (yet)</h3>

        <Sub n="3">Cross-disk consistency: three disks, three different answers</Sub>
        <Pr note={<>On {short(D.images[widest.t].label)} the headline run of Isolation Forest catches {D.images[widest.t].metrics[MODELS[0]].targets} at 5%, while its five reruns catch {rng(widest.v)} of {widest.n}. One seed can mislead.</>}>
          <p>The same model, scored on the same budget on each disk, gives very different recall. At a {pc(pct)} budget the leading model is {sameLead ? lead[0] + ' on all three disks' : lead.map((l, i) => l + ' on ' + short(D.images[IMGS[i]].label)).join(', ')}.</p>
        </Pr>
        <Fig n="7" name="cross-disk" caption={<>Share of evidence targets caught at your {pc(pct)} budget, one row per disk and model, counted from the full-disk ranks of the headline run (seed 42). Change the budget above to see the picture move.</>}>
          <DisksFig pct={pct} />
        </Fig>
        <div className="tbl ledger"><table><thead><tr><th>Disk</th><th className="n">Files read</th>{SHORT.map((s, i) => <th key={s} className="n"><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{s}</th>)}<th>Where the targets come from</th></tr></thead>
          <tbody>{cross.map((r, i) => (
            <tr key={r.t} className={r.t === img ? 'cur' : ''}><td>{short(r.x.label)}</td><td className="n">{fmt(r.K)}</td>
              {r.c.map((c, mi) => <td key={mi} className={'n' + (mi === m ? ' sel' : '')}>{c}/{r.n} · {pc(c / r.n, 0)}</td>)}
              <td>{['case notes', 'repository CFReDS list', 'scenario author’s examiner tags'][i]}{i === 2 ? <> <Flag kind="warn">weaker truth</Flag></> : null}</td></tr>))}</tbody></table></div>
        <Pr><p style={{ marginTop: 14 }}><b>Three disks are not enough to claim this generalises.</b> The best model changes with the disk and with the budget, and each disk has a different scenario: an outside intrusion, an insider data leak and a lone-wolf case. Image 3’s targets are the tags of one examiner, not an official answer key, so recall on it is measured against a weaker ground truth than on the other two. Treat every number here as evidence about these three disks, not about disks in general.</p></Pr>

        <Sub n="4">Known feature issues, still in the 23 features</Sub>
        <Pr><p>These defects remain in the current 23 features, so every number on this page includes them. Fixing them will change the results, in either direction.</p></Pr>
        <div className="tbl ledger issues"><table><thead><tr><th>Issue</th><th>What goes wrong</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td><b>{toolFlags.length} disk-level tool and USB flags are constant</b><div className="small mono">{toolFlags.join(', ')}</div></td><td>Each is set once for the whole disk, not per file, so every file gets the same value. A constant column cannot rank anything; it only adds a fixed offset.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td><b className="mono">future_m</b> is always 0</td><td>Its reference time is the newest timestamp on the same disk, so no file can be later than it. The feature can never fire.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td><b className="mono">is_deleted</b> is always 0</td><td>No file ever carries the flag, so deletion is invisible to the models.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td><b className="mono">usb_present</b> is always 1</td><td>It reports that a USB device was seen anywhere on the disk, not which files relate to it.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td>The <span className="mono">cmd</span> keyword also matches <span className="mono">MPCMDRUN</span></td><td>The command-prompt flag matches the name of Windows Defender’s own executable, so it can fire for activity that has nothing to do with a command prompt.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td><span className="mono">after_hours</span> is measured in UTC</td><td>Working hours are fixed at 08:00 to 18:00 UTC. The disk’s own time zone is not applied, so activity can be filed as after-hours or office-hours wrongly.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
            <tr><td>Prefetch files are under-extracted</td><td>Many execution records are missed, so <span className="mono">per_file_prefetch_hit</span> understates what was run.</td><td><Flag kind="warn">in the 23</Flag></td></tr>
          </tbody></table></div>
        <Pr><p className="small" style={{ marginTop: 10 }}>{constAll.length} of the 23 features are constant on all three disks ({constAll.join(', ')}), which leaves {23 - constAll.length} that can vary.</p></Pr>
      </div>
    </Section>
  )
}
