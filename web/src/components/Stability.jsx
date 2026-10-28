import { useRef } from 'react'
import { SW } from '../lib/data'
import { useDraw } from '../lib/hooks'
import Section from '../lib/Section'

const CFG = [['IF-23', '--m0', '', 'IF · 23'], ['LOF-23', '--m1', '', 'LOF · 23'], ['OCSVM-23', '--m2', '', 'OC-SVM · 23'], ['IF-17', '--ink2', '5 4', 'IF · 17']]

export default function Stability(p) {
  const sw = SW[p.img], ref = useRef()
  useDraw(ref, [p.img])
  const head = (
    <div className="sec-head rv"><div className="eyebrow">Threshold stability</div><h2>Is there a review budget that holds up?</h2>
      <p>Each model was rerun five times with 10% of ordinary files dropped at random, in three separate randomizations. The lines show mean evidence recall from a 5% to a 100% budget; the bands show the spread across runs. The legacy XP disk is excluded.</p></div>
  )
  if (!sw) return <Section id="stability">{head}<div className="two rv"><div className="panel"><p className="note">The legacy XP disk is excluded from this study. Pick Image 2 or Image 3.</p></div></div></Section>
  const W = 560, H = 320, L = 44, R = 150, T = 14, B = 34, pw = W - L - R, ph = H - T - B
  const Xs = (v) => L + (v / 100) * pw, Ys = (v) => T + (1 - v / 100) * ph
  const ends = []
  CFG.forEach((c) => {
    const d = sw[c[0]]; if (!d) return
    let j = d.pct.findIndex((v) => v >= 20); if (j < 0) j = d.pct.length - 1
    ends.push({ c, y: Ys(d.recall[j]) })
  })
  ends.sort((a, b) => a.y - b.y)
  for (let j = 1; j < ends.length; j++) if (ends[j].y - ends[j - 1].y < 15) ends[j].y = ends[j - 1].y + 15
  const cx = Xs(p.pct * 100), i5 = (d) => d.pct.indexOf(5), a = sw['IF-23'], o = sw['OCSVM-23']
  return (
    <Section id="stability">{head}
      <div className="two rv">
        <div className="panel" ref={ref}><svg viewBox={'0 0 ' + W + ' ' + H} width="100%" role="img" aria-label="Mean recall versus review budget across randomized runs">
          {[0, 25, 50, 75, 100].map((v) => <g key={v}><line className="gl" x1={L} x2={W - R} y1={Ys(v)} y2={Ys(v)} /><text x={L - 8} y={Ys(v) + 4} textAnchor="end">{v}%</text><text x={Xs(v)} y={H - 12} textAnchor="middle">{v}%</text></g>)}
          <text x={L + pw / 2} y={H} textAnchor="middle">review budget</text>
          {CFG.map((c) => {
            const d = sw[c[0]]; if (!d) return null
            const up = d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(Math.min(100, d.recall[i] + d.std[i])).toFixed(1))
            const dn = d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(Math.max(0, d.recall[i] - d.std[i])).toFixed(1)).reverse()
            return (
              <g key={c[0]}><polygon className="fadein" data-op="0.12" points={up.concat(dn).join(' ')} fill={'var(' + c[1] + ')'} opacity="0.12" />
                <polyline className="draw" data-dash={c[2]} fill="none" stroke={'var(' + c[1] + ')'} strokeWidth="2.2" strokeDasharray={c[2] || undefined} points={d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(d.recall[i]).toFixed(1)).join(' ')} /></g>
            )
          })}
          {ends.map((e) => <text key={e.c[0]} className="fadein" x={W - R + 8} y={Math.min(H - B, e.y) + 4} style={{ fill: 'var(' + e.c[1] + ')', fontWeight: 500 }}>{e.c[3]}</text>)}
          <line x1={cx} x2={cx} y1={T} y2={H - B} stroke="var(--ink)" strokeDasharray="4 4" />
        </svg></div>
        <div className="panel"><h3 style={{ marginBottom: 10 }}>Smallest budget reaching 90% recall</h3>
          <div className="scroll-x"><table><thead><tr><th>Model (features)</th><th className="n">Run set 1</th><th className="n">Run set 2</th><th className="n">Run set 3</th><th>Agree?</th><th className="n">Thresholds agreeing</th></tr></thead><tbody>{CFG.map((c) => {
            const d = sw[c[0]]; if (!d) return null
            const g = d.ge90 || {}, cellv = (k) => (g[k] == null ? 'never' : g[k] + '%')
            return <tr key={c[0]}><td><i className="dotkey" style={{ background: 'var(' + c[1] + ')' }}></i>{d.label}</td><td className="n">{cellv('R1')}</td><td className="n">{cellv('R2')}</td><td className="n">{cellv('R3')}</td><td><span className={'chip ' + (d.agree90 ? 'ok' : 'warn')}>{d.agree90 ? 'yes' : 'no'}</span></td><td className="n">{d.agreement || '–'}</td></tr>
          })}</tbody></table></div>
          <p className="note" style={{ marginTop: 10 }}>{a && o ? 'At 5% Isolation Forest catches ' + a.hits[i5(a)] + ' of ' + a.targets + ' targets on average and One-Class SVM ' + o.hits[i5(o)] + '. Full recall at a 5.5% budget is not a general result: only One-Class SVM on Image 2 reaches it.' : ''}</p></div>
      </div>
    </Section>
  )
}
