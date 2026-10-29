import { useRef } from 'react'
import { D, MODELS, SHORT, MVAR, IMGS, short, fmt, pc } from '../lib/data'
import { useDraw, useGrow } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'

function Curve(p) {
  const im = p.im, ref = useRef(), W = 900, H = 380, L = 48, R = 170, T = 16, B = 44, pw = W - L - R, ph = H - T - B
  const Xs = (v) => L + (v / 0.2) * pw, Ys = (v) => T + (1 - v) * ph
  useDraw(ref, [p.img])
  const ends = MODELS.map((m, i) => ({ i, y: Ys(im.curves[m][im.curves[m].length - 1]) })).sort((a, b) => a.y - b.y)
  for (let j = 1; j < ends.length; j++) if (ends[j].y - ends[j - 1].y < 17) ends[j].y = ends[j - 1].y + 17
  const cx = Xs(p.pct); let jj = 0; while (jj < D.pcts.length - 1 && D.pcts[jj + 1] <= p.pct + 1e-9) jj++
  return (
    <div ref={ref}><svg className="ch" viewBox={'0 0 ' + W + ' ' + H} role="img" aria-label="Recall versus review budget for three models">
      <line className="axis" x1={L} x2={L} y1={T} y2={H - B} /><line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
      {[0, .5, 1].map((v) => <g key={v}><line className="tickl" x1={L - 5} x2={L} y1={Ys(v)} y2={Ys(v)} /><text x={L - 9} y={Ys(v) + 4} textAnchor="end">{Math.round(v * 100)}%</text></g>)}
      {[0, .05, .1, .15, .2].map((v) => <g key={v}><line className="tickl" x1={Xs(v)} x2={Xs(v)} y1={H - B} y2={H - B + 5} /><text x={Xs(v)} y={H - B + 20} textAnchor="middle">{Math.round(v * 100)}%</text></g>)}
      <text x={L + pw / 2} y={H - 6} textAnchor="middle">review budget (share of files read)</text>
      <text x={L} y={T - 4} textAnchor="start">evidence recall</text>
      {MODELS.map((m, i) => {
        const pts = D.pcts.map((v, k) => Xs(v).toFixed(1) + ',' + Ys(im.curves[m][k]).toFixed(1)).join(' ')
        return <polyline key={m} className="draw" fill="none" stroke={'var(' + MVAR[i] + ')'} strokeWidth={i === p.m ? 3 : 1.6} strokeLinejoin="round" opacity={i === p.m ? 1 : .8} points={pts} />
      })}
      {ends.map((e) => <text key={e.i} className="fadein lbl" x={W - R + 10} y={e.y + 4} style={{ fill: 'var(' + MVAR[e.i] + ')' }}>{SHORT[e.i]}</text>)}
      <line className="mark" x1={cx} x2={cx} y1={T} y2={H - B} />
      <text className="mk" x={Math.min(cx + 6, W - R - 70)} y={T + 10}>budget {pc(p.pct)}</text>
      {MODELS.map((m, i) => <circle key={m} cx={cx} cy={Ys(im.curves[m][jj])} r="4.5" fill={'var(' + MVAR[i] + ')'} stroke="var(--paper)" strokeWidth="1.5" />)}
    </svg></div>
  )
}

const kOf = (x, pct) => Math.max(1, Math.round(pct * x.files))
const caught = (x, m, K) => x.targets.filter((t) => t.ranks[m] <= K).length

export default function Results(p) {
  const im = p.im, allRef = useRef(), K = kOf(im, p.pct)
  useGrow(allRef, [p.pct])
  return (
    <Section id="recall" letter="G" title="How much evidence for how much reading?">
      <Pr note={<>The 5% tables further down are the equal-budget comparison. Accuracy sits near 95% for every model there by construction, because 95% of files are left unflagged. Recall, precision and F1 are the numbers that separate the models.</>}>
        <p>Recall of the evidence targets as the examiner is allowed to read more files, up to 20% of the disk. The dashed line is the budget you chose above, {pc(p.pct)}. The Plateau exhibit above follows the same curves out to 100%.</p>
      </Pr>
      <div className="chartwrap"><Curve im={im} img={p.img} m={p.m} pct={p.pct} /></div>
      <div className="split">
        <div>
          <h3 className="cap">{short(im.label)} at your {pc(p.pct)} budget ({fmt(K)} of {fmt(im.files)} files)</h3>
          <div className="tbl"><table><thead><tr><th>Model</th><th className="n">Targets caught</th><th className="n">Recall</th><th className="n">Files read</th><th className="n">False alarms</th></tr></thead><tbody>{MODELS.map((m, i) => {
            const c = caught(im, m, K), n = im.targets.length
            return <tr key={m}><td><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{SHORT[i]}</td><td className="n">{c}/{n}</td><td className="n">{pc(c / n)}</td><td className="n">{fmt(K)}</td><td className="n">{fmt(K - c)}</td></tr>
          })}</tbody></table></div>
          <p className="small" style={{ marginTop: 8 }}>Counted from the full-disk ranks of one run (seed 42). A false alarm is a file read that is not a target.</p>
        </div>
        <div ref={allRef}>
          <h3 className="cap">All three disks at your {pc(p.pct)} budget</h3>
          <div style={{ display: 'grid', gap: 22 }}>{IMGS.map((t) => {
            const x = D.images[t], Kx = kOf(x, p.pct), n = x.targets.length, cs = MODELS.map((m) => caught(x, m, Kx)), best = Math.max.apply(null, cs)
            return (
              <div key={t}><div style={{ font: '500 16px var(--serif)' }}>{short(x.label)} <span className="small">{x.label.split(': ')[1] || ''} · {fmt(x.files)} files · {n} targets</span></div>
                {MODELS.map((m, i) => {
                  const r = cs[i] / n
                  return <div key={m} className={'mrow' + (cs[i] === best ? ' best' : '')}><span className="mn">{SHORT[i]}</span><div className="bar1"><i data-grow="1" data-w={r * 100} style={{ width: (r * 100) + '%', background: 'var(' + MVAR[i] + ')' }}></i></div><span className="num">{cs[i]}/{n}</span></div>
                })}</div>
            )
          })}</div>
        </div>
      </div>
      <div className="ledgerwrap">
        <h3 className="cap">Equal-budget comparison at a strict 5%</h3>
        <div className="tbl ledger"><table><thead><tr><th>Disk</th><th>Model</th><th className="n">Targets</th><th className="n">Recall</th><th className="n">Precision</th><th className="n">F1</th><th className="n">Accuracy</th></tr></thead><tbody>{IMGS.map((t) => MODELS.map((m, i) => {
          const x = D.images[t], y = x.metrics[m]
          return <tr key={t + m} className={i === 0 ? 'grp' : ''}><td>{i === 0 ? short(x.label) + ' · ' + fmt(x.K5) + ' of ' + fmt(x.files) + ' files' : ''}</td><td><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{SHORT[i]}</td><td className="n">{y.targets}</td><td className="n">{pc(y.target_recall)}</td><td className="n">{pc(y.precision, 2)}</td><td className="n">{pc(y.f1, 2)}</td><td className="n">{pc(y.accuracy, 2)}</td></tr>
        }))}</tbody></table></div>
        <p className="small" style={{ marginTop: 10 }}>This table is fixed at 5% on purpose: it is the one budget at which all three models were scored on the same footing, and it does not move with the slider. Precision, F1 and accuracy are file-level and were only computed at 5%.</p>
      </div>
    </Section>
  )
}
