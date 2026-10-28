import { useRef } from 'react'
import { D, MODELS, SHORT, MVAR, IMGS, short, fmt, pc } from '../lib/data'
import { useDraw, useGrow } from '../lib/hooks'
import Section from '../lib/Section'

function Curve(p) {
  const im = p.im, ref = useRef(), W = 560, H = 320, L = 44, R = 118, T = 14, B = 34, pw = W - L - R, ph = H - T - B
  const Xs = (v) => L + (v / 0.2) * pw, Ys = (v) => T + (1 - v) * ph
  useDraw(ref, [p.img])
  const ends = MODELS.map((m, i) => ({ i, y: Ys(im.curves[m][im.curves[m].length - 1]) })).sort((a, b) => a.y - b.y)
  for (let j = 1; j < ends.length; j++) if (ends[j].y - ends[j - 1].y < 15) ends[j].y = ends[j - 1].y + 15
  const cx = Xs(p.pct); let jj = 0; while (jj < D.pcts.length - 1 && D.pcts[jj + 1] <= p.pct + 1e-9) jj++
  return (
    <div ref={ref}><svg viewBox={'0 0 ' + W + ' ' + H} width="100%" role="img" aria-label="Recall versus review budget for three models">
      {[0, .25, .5, .75, 1].map((v) => <g key={v}><line className="gl" x1={L} x2={W - R} y1={Ys(v)} y2={Ys(v)} /><text x={L - 8} y={Ys(v) + 4} textAnchor="end">{Math.round(v * 100)}%</text></g>)}
      {[0, .05, .1, .15, .2].map((v) => <text key={v} x={Xs(v)} y={H - 12} textAnchor="middle">{Math.round(v * 100)}%</text>)}
      <text x={L + pw / 2} y={H} textAnchor="middle">review budget (share of files read)</text>
      {MODELS.map((m, i) => {
        const pts = D.pcts.map((v, k) => Xs(v).toFixed(1) + ',' + Ys(im.curves[m][k]).toFixed(1)).join(' ')
        return <polyline key={m} className="draw" fill="none" stroke={'var(' + MVAR[i] + ')'} strokeWidth={i === p.m ? 3.2 : 1.8} opacity={i === p.m ? 1 : .75} points={pts} />
      })}
      {ends.map((e) => <text key={e.i} className="fadein" x={W - R + 8} y={e.y + 4} style={{ fill: 'var(' + MVAR[e.i] + ')', fontWeight: 500 }}>{SHORT[e.i]}</text>)}
      <line x1={cx} x2={cx} y1={T} y2={H - B} stroke="var(--ink)" strokeDasharray="4 4" />
      {MODELS.map((m, i) => <circle key={m} cx={cx} cy={Ys(im.curves[m][jj])} r="4.5" fill={'var(' + MVAR[i] + ')'} stroke="var(--surface)" strokeWidth="1.5" />)}
    </svg></div>
  )
}

export default function Results(p) {
  const im = p.im, allRef = useRef()
  useGrow(allRef, [])
  return (
    <Section id="recall">
      <div className="sec-head rv"><div className="eyebrow">Results</div><h2>How much evidence for how much reading?</h2>
        <p>Recall of the evidence targets as the examiner is allowed to read more files. The dashed line is the budget you chose above.</p></div>
      <div className="two rv">
        <div className="panel"><Curve im={im} img={p.img} m={p.m} pct={p.pct} /></div>
        <div className="panel"><h3 style={{ marginBottom: 10 }}>{short(im.label)} at the 5% budget ({fmt(im.K5)} of {fmt(im.files)} files)</h3>
          <div className="scroll-x"><table><thead><tr><th>Model</th><th className="n">Targets</th><th className="n">Recall</th><th className="n">Precision</th><th className="n">F1</th><th className="n">Accuracy</th></tr></thead><tbody>{MODELS.map((m, i) => {
            const x = im.metrics[m]
            return <tr key={m}><td><i className="dotkey" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{SHORT[i]}</td><td className="n">{x.targets}</td><td className="n">{pc(x.target_recall)}</td><td className="n">{pc(x.precision, 2)}</td><td className="n">{pc(x.f1, 2)}</td><td className="n">{pc(x.accuracy, 2)}</td></tr>
          })}</tbody></table></div>
          <p className="note" style={{ marginTop: 10 }}>Accuracy sits near 95% for every model by construction: a fixed 5% budget on rare evidence. Recall, precision and F1 are the numbers that separate the models.</p></div>
      </div>
      <h3 className="rv" style={{ margin: '26px 0 12px' }}>All three disks at the 5% budget</h3>
      <div className="three rv" ref={allRef}>{IMGS.map((t) => {
        const x = D.images[t], best = Math.max.apply(null, MODELS.map((m) => parseFloat(x.metrics[m].target_recall)))
        return (
          <div key={t} className="panel cardimg"><h3>{short(x.label)}</h3><div className="meta">{x.label.split(': ')[1] || ''} · {fmt(x.files)} files · {x.targets.length} targets</div>
            {MODELS.map((m, i) => {
              const r = parseFloat(x.metrics[m].target_recall)
              return <div key={m} className={'mrow' + (r === best ? ' best' : '')}><span className="mn">{SHORT[i]}</span><div className="bar"><i data-grow="1" data-w={r * 100} style={{ width: (r * 100) + '%', background: 'var(' + MVAR[i] + ')' }}></i></div><span className="num mono">{x.metrics[m].targets}</span></div>
            })}</div>
        )
      })}</div>
    </Section>
  )
}
