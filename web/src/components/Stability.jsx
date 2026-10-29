import { useRef } from 'react'
import { SW, pc } from '../lib/data'
import { curve, fn1 } from '../lib/curves'
import { useDraw } from '../lib/hooks'
import Section from '../lib/Section'
import { Pr, Flag } from '../lib/Prose'

const CFG = [['IF-23', '--m0', '', 'IF · 23'], ['LOF-23', '--m1', '', 'LOF · 23'], ['OCSVM-23', '--m2', '', 'OC-SVM · 23'], ['IF-17', '--ink2', '5 4', 'IF · 17']]

export default function Stability(p) {
  const sw = SW[p.img], ref = useRef()
  useDraw(ref, [p.img])
  const intro = <p>Each model was rerun five times with 10% of ordinary files dropped at random, in three separate randomizations. The lines show mean evidence recall from a 5% to a 100% budget; the bands show the spread across runs. The legacy XP disk is excluded.</p>
  if (!sw) return <Section id="stability" letter="M" title="Is there a review budget that holds up?"><Pr>{intro}</Pr><Pr><p className="small">The legacy XP disk is excluded from this study. Pick Image 2 or Image 3.</p></Pr></Section>
  const W = 900, H = 380, L = 48, R = 130, T = 16, B = 44, pw = W - L - R, ph = H - T - B
  const Xs = (v) => L + (v / 100) * pw, Ys = (v) => T + (1 - v / 100) * ph
  const ends = []
  CFG.forEach((c) => {
    const d = sw[c[0]]; if (!d) return
    let j = d.pct.findIndex((v) => v >= 20); if (j < 0) j = d.pct.length - 1
    ends.push({ c, y: Ys(d.recall[j]) })
  })
  ends.sort((a, b) => a.y - b.y)
  for (let j = 1; j < ends.length; j++) if (ends[j].y - ends[j - 1].y < 17) ends[j].y = ends[j - 1].y + 17
  const cx = Xs(p.pct * 100), a = sw['IF-23'], o = sw['OCSVM-23']
  const ca = curve(p.img, 'IF-23').at(p.pct * 100), co = curve(p.img, 'OCSVM-23').at(p.pct * 100)
  const note = a && o ? 'At a ' + pc(p.pct) + ' budget Isolation Forest catches ' + fn1(ca.found) + ' of ' + a.targets + ' targets on average and One-Class SVM ' + fn1(co.found) + '. The full-recall points differ by disk and model: see the table below.' : ''
  return (
    <Section id="stability" letter="M" title="Is there a review budget that holds up?">
      <Pr note={note || null}>{intro}</Pr>
      <div ref={ref}><svg className="ch" viewBox={'0 0 ' + W + ' ' + H} role="img" aria-label="Mean recall versus review budget across randomized runs">
        <line className="axis" x1={L} x2={L} y1={T} y2={H - B} /><line className="axis" x1={L} x2={W - R} y1={H - B} y2={H - B} />
        {[0, 50, 100].map((v) => <g key={'y' + v}><line className="tickl" x1={L - 5} x2={L} y1={Ys(v)} y2={Ys(v)} /><text x={L - 9} y={Ys(v) + 4} textAnchor="end">{v}%</text></g>)}
        {[0, 25, 50, 75, 100].map((v) => <g key={'x' + v}><line className="tickl" x1={Xs(v)} x2={Xs(v)} y1={H - B} y2={H - B + 5} /><text x={Xs(v)} y={H - B + 20} textAnchor="middle">{v}%</text></g>)}
        <text x={L + pw / 2} y={H - 6} textAnchor="middle">review budget</text>
        {CFG.map((c) => {
          const d = sw[c[0]]; if (!d) return null
          const up = d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(Math.min(100, d.recall[i] + d.std[i])).toFixed(1))
          const dn = d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(Math.max(0, d.recall[i] - d.std[i])).toFixed(1)).reverse()
          return (
            <g key={c[0]}><polygon className="fadein" data-op="0.14" points={up.concat(dn).join(' ')} fill={'var(' + c[1] + ')'} opacity="0.14" />
              <polyline className="draw" data-dash={c[2]} fill="none" stroke={'var(' + c[1] + ')'} strokeWidth="2" strokeLinejoin="round" strokeDasharray={c[2] || undefined} points={d.pct.map((v, i) => Xs(v).toFixed(1) + ',' + Ys(d.recall[i]).toFixed(1)).join(' ')} /></g>
          )
        })}
        {ends.map((e) => <text key={e.c[0]} className="fadein lbl" x={W - R + 10} y={Math.min(H - B, e.y) + 4} style={{ fill: 'var(' + e.c[1] + ')' }}>{e.c[3]}</text>)}
        <line className="mark" x1={cx} x2={cx} y1={T} y2={H - B} />
        <text className="mk" x={cx + 6} y={T + 10}>budget {(p.pct * 100).toFixed(1)}%</text>
      </svg></div>
      <div style={{ marginTop: 40 }}>
        <h3 className="cap">Smallest budget reaching 90% recall</h3>
        <div className="tbl"><table><thead><tr><th>Model (features)</th><th className="n">Run set 1</th><th className="n">Run set 2</th><th className="n">Run set 3</th><th>Agree?</th><th className="n">Thresholds agreeing</th></tr></thead><tbody>{CFG.map((c) => {
          const d = sw[c[0]]; if (!d) return null
          const g = d.ge90 || {}, cellv = (k) => (g[k] == null ? 'never' : g[k] + '%')
          return <tr key={c[0]}><td><i className="key" style={{ background: 'var(' + c[1] + ')' }}></i>{d.label}</td><td className="n">{cellv('R1')}</td><td className="n">{cellv('R2')}</td><td className="n">{cellv('R3')}</td><td><Flag kind={d.agree90 ? 'ok' : 'warn'}>{d.agree90 ? 'yes' : 'no'}</Flag></td><td className="n">{d.agreement || '–'}</td></tr>
        })}</tbody></table></div>
      </div>
    </Section>
  )
}
