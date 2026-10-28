import { useEffect, useMemo, useRef, useState } from 'react'
import { D, MODELS, IMGS, SW, pc, hitsFmt, frac } from '../lib/data'
import { useGrow } from '../lib/hooks'
import { AN, canAnim, EASE4 } from '../lib/motion'
import Num from '../lib/Num'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'

const FB_N = { img2: 19, img3: 34 }
const FB = {
  img2: { 'IF-23': { 5: [17, 89.5], 11: [17.4, 91.6], 15: [18, 94.7], 21: [19, 100] }, 'OCSVM-23': { 5: [19, 100], 11: [19, 100], 15: [19, 100], 21: [19, 100] },
    'IF-17': { 5: [7.6, 40], 11: [10.6, 55.8], 15: [13.2, 69.5], 21: [17.8, 93.7], 25: [18, 94.7] } },
  img3: { 'IF-23': { 5: [11.8, 34.7, 10.6], 11: [29, 85.3], 15: [33.8, 99.4], 21: [34, 100] }, 'OCSVM-23': { 5: [24.8, 72.9], 11: [25.6, 75.3], 15: [27.4, 80.6, 5.1], 21: [30.4, 89.4], 23: [30.8, 90.6] } }
}
function cell(img, cfg, pct) {
  const d = (SW[img] || {})[cfg], i = d ? d.pct.indexOf(pct) : -1
  if (d && i >= 0) return { h: d.hits[i], r: d.recall[i], s: d.std[i] || 0, n: d.targets }
  const f = ((FB[img] || {})[cfg] || {})[pct]
  return f ? { h: f[0], r: f[1], s: f[2] || 0, n: FB_N[img] } : null
}
function reach(img, cfg, thr) {
  const d = (SW[img] || {})[cfg]; if (!d) return null
  for (let i = 0; i < d.pct.length; i++) if (d.recall[i] >= thr - 1e-9) return d.pct[i]
  return null
}
const VROWS = [
  { img: 'img2', cfg: 'IF-23', name: 'Image 2 · Isolation Forest, 23 features', v: '--m0', table: true },
  { img: 'img2', cfg: 'OCSVM-23', name: 'Image 2 · One-Class SVM, 23 features', v: '--m2', table: true },
  { img: 'img2', cfg: 'IF-17', name: 'Image 2 · Isolation Forest, original 17', v: '--ink2', table: true },
  { img: 'img2', cfg: 'LOF-23', name: 'Image 2 · LOF, 23 features', v: '--m1' },
  { img: 'img3', cfg: 'IF-23', name: 'Image 3 · Isolation Forest, 23 features', v: '--m0', table: true },
  { img: 'img3', cfg: 'OCSVM-23', name: 'Image 3 · One-Class SVM, 23 features', v: '--m2', table: true },
  { img: 'img3', cfg: 'LOF-23', name: 'Image 3 · LOF, 23 features', v: '--m1' }
]
const TICKS = [5, 11, 15, 21, 25], COLS = [5, 11, 15, 21, 23, 25]

export default function Verdict() {
  const [budget, setBudget] = useState(15)
  const barsRef = useRef(), whyRef = useRef(), stampRef = useRef()
  const s5 = useMemo(() => MODELS.map((m) => IMGS.reduce((a, t) => a + parseFloat(D.images[t].metrics[m].target_recall), 0) / IMGS.length), [])
  const ocHits = IMGS.map((t) => D.images[t].metrics[MODELS[2]].targets).join(', ')
  const agr = ['img2', 'img3'].map((i) => { const a = (SW[i] || {})['IF-23']; return a ? frac(a.agreement) * 100 : null }).filter((v) => v != null)
  const agrTxt = agr.length ? Math.round(Math.min.apply(null, agr)) + '–' + Math.round(Math.max.apply(null, agr)) + '%' : '90–98%'
  const rows = VROWS.map((r) => Object.assign({ c: cell(r.img, r.cfg, budget) }, r))
  useGrow(barsRef, [budget])
  const r17 = reach('img2', 'IF-17', 90) || 21, r17f = reach('img2', 'IF-17', 100) || 39, r23a = reach('img2', 'IF-23', 90) || 11, r23b = reach('img3', 'IF-23', 90) || 15
  const oc3 = reach('img3', 'OCSVM-23', 90) || 23, lofMin = Math.min.apply(null, ['img2', 'img3'].map((i) => reach(i, 'LOF-23', 90) || 100))
  const rb = [{ n: 'Original 17 features', w: r17, v: '--ink2' }, { n: '23 features, Image 2', w: r23a, v: '--m0' }, { n: '23 features, Image 3', w: r23b, v: '--m0' }]
  useGrow(whyRef, [])
  const c17 = cell('img2', 'IF-17', 21), c17b = cell('img2', 'IF-17', 25)

  /* the stamp lands once, when the finding scrolls into view; it is visible unless this effect hides it itself */
  useEffect(() => {
    const el = stampRef.current
    if (!el || !canAnim() || !window.IntersectionObserver) return
    let t = 0
    const done = () => { el.style.opacity = ''; el.style.transform = '' }
    const io = new IntersectionObserver((es) => {
      if (!es.some((e) => e.isIntersecting)) return
      io.disconnect()
      AN({ targets: el, scale: [1.3, 1], rotate: [-9, -4], opacity: [0, 0.94], duration: 380, delay: 250, easing: EASE4, complete: done })
      t = setTimeout(done, 1500)
    }, { threshold: 0.8 })
    io.observe(el)
    return () => { io.disconnect(); clearTimeout(t); AN.remove(el); done() }
  }, [])

  return (
    <>
    <Section id="verdict-budget" letter="B" title="Which model, which budget" band>
      <Pr><p>The best model depends on the review budget, which is the share of files an examiner agrees to review. A very tight budget favours one model. A slightly larger budget favours another.</p></Pr>
      <div className="spread">
        <div className="finding l">
          <div className="k">At a strict 5% budget</div>
          <div className="disp">One-Class SVM</div>
          <p>At 5% of files, One-Class SVM catches the most: {ocHits} targets on the three disks. Its mean target recall is <b>{pc(s5[2])}</b>, against {pc(s5[0])} for Isolation Forest and {pc(s5[1])} for LOF.</p>
        </div>
        <div className="finding r">
          <div className="k">Best overall</div>
          <div className="disp">Isolation Forest</div>
          <div className="sub">23 features · 15% budget</div>
          <div className="stamprow"><span className="stamp" ref={stampRef}>Recommended</span></div>
          <p>At a 15% budget it reaches <b>{pc((cell('img2', 'IF-23', 15) || { r: 94.7 }).r / 100)}</b> on Image 2 and <b>{pc((cell('img3', 'IF-23', 15) || { r: 99.4 }).r / 100)}</b> on Image 3. It is also stable: the 3 randomizations agree on {agrTxt} of thresholds.</p>
        </div>
      </div>
    </Section>
    <section className="ex cont"><div className="wrap">
      <div className="chartgrid" style={{ marginTop: 0 }}>
        <div>
          <div className="vtop"><h3 className="cap" style={{ margin: 0 }}>Recall at a chosen budget</h3>
            <div className="fld"><span className="lab">Budget</span>
              <Seg label="Review budget" items={TICKS.map((t) => t + '%')} value={TICKS.indexOf(budget)} onPick={(i) => setBudget(TICKS[i])} /></div></div>
          <p className="small" style={{ marginBottom: 6 }}>Mean evidence recall over 5 randomized runs. The dashed line marks 90%. {budget === 15 ? 'At 15% the recommended setting, Isolation Forest on 23 features, is outlined.' : 'Pick 15% to see the recommended setting.'}</p>
          <div className="vchart" ref={barsRef}>
            <div className="ninety" aria-hidden="true"><span>90% recall</span></div>
            {rows.map((r) => {
              const rec = r.cfg === 'IF-23' && budget === 15, val = r.c ? r.c.r : 0
              return (
                <div key={r.img + r.cfg} className={'vrow' + (rec ? ' rec' : '')}>
                  <div className="vl">{r.name}{rec ? <em>recommended</em> : null}</div>
                  <div className="vt"><i data-grow="1" data-w={val} style={{ width: val + '%', background: 'var(' + r.v + ')' }}></i></div>
                  <div className="vv"><Num value={val} fmt={(v) => v.toFixed(1) + '%'} /></div></div>
              )
            })}
          </div>
        </div>
        <aside className="side" ref={whyRef} style={{ marginTop: 0 }}>
          <b>Why the earlier 25% figure</b>
          <p>It came from the original 17-feature Isolation Forest on Image 2. A fresh rerun of that same model reaches 90% at about {r17}%: {c17 ? c17.r.toFixed(1) : '93.7'}% at 21%, {c17b ? c17b.r.toFixed(1) : '94.7'}% at 25%, and 100% only at {r17f}%. With 23 features the same model needs only 15%. The 6 new features are what cut the budget.</p>
          <p><b>Smallest budget reaching 90% recall</b></p>
          {rb.map((b) => <div key={b.n} className="mrow"><span className="mn">{b.n}</span><div className="bar1"><i data-grow="1" data-w={b.w / 30 * 100} style={{ width: (b.w / 30 * 100) + '%', background: 'var(' + b.v + ')' }}></i></div><span className="num">{b.w}%</span></div>)}
        </aside>
      </div>
      <p className="big-rule"><b style={{ fontWeight: 500 }}>The simple rule:</b> if you can read only 5% of files, use One-Class SVM. If you can read 15%, use Isolation Forest on all 23 features.</p>
      <Pr className="" >
        <h3 className="cap" style={{ marginTop: 40 }}>The other two models</h3>
        <ul className="plain">
          <li><b>One-Class SVM on Image 3</b> reaches only {(cell('img3', 'OCSVM-23', 15) || { r: 80.6 }).r.toFixed(1)}% at 15% and needs about {oc3}% to reach 90%. On Image 2 it is perfect at every budget.</li>
          <li><b>LOF</b> never reaches 90% below about {Math.round(lofMin / 10) * 10}%, so it is not a practical choice at any budget an examiner would accept.</li>
        </ul>
      </Pr>
      <div style={{ marginTop: 48 }}>
        <h3 className="cap">Recall at budget</h3>
        <div className="tbl"><table><thead><tr><th>Disk · model</th>{COLS.map((c) => <th key={c} className={'n' + (c === 15 ? ' star' : '')}>{c}%</th>)}</tr></thead><tbody>{VROWS.filter((r) => r.table).map((r) => (
          <tr key={r.img + r.cfg}><td><i className="key" style={{ background: 'var(' + r.v + ')' }}></i>{r.name}</td>{COLS.map((c) => {
            const x = cell(r.img, r.cfg, c)
            if (!x) return <td key={c} className="n">–</td>
            return <td key={c} className={'n' + (c === 15 ? ' star' : '')}><div>{hitsFmt(x.h)}/{x.n}</div><div className={'sub' + (x.r >= 90 ? ' hi' : '')}>{x.r.toFixed(1)}%{x.s >= 1 ? ' ±' + x.s.toFixed(1) : ''}</div></td>
          })}</tr>
        ))}</tbody></table></div>
        <Pr><p className="small" style={{ marginTop: 10 }}>Hits are the mean number of evidence targets found over 5 runs, each with 10% of ordinary files dropped at random. Red percentages are at or above 90%. The shaded column is the recommended 15% budget.</p></Pr>
      </div>
    </div></section>
    </>
  )
}
