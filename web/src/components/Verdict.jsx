import { useEffect, useRef, useState } from 'react'
import { D, SHORT, MVAR, fmt, short } from '../lib/data'
import { useGrow } from '../lib/hooks'
import { AN, canAnim, EASE4 } from '../lib/motion'
import Num from '../lib/Num'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'
import Integrity from './Integrity'
import { MK, DISKS, A2, statAt, f1, rangeTxt } from '../lib/study'

const TICKS = [5, 10, 15, 20, 25]
const COLS = [10, 15, 20]
const dn = (t) => short(D.images[t].label)

export default function Verdict() {
  const [budget, setBudget] = useState(20)
  const barsRef = useRef(), whyRef = useRef(), stampRef = useRef()
  useGrow(barsRef, [budget])
  useGrow(whyRef, [])
  const rows = []
  DISKS.forEach((t) => MK.forEach((k, i) => { const s = statAt(t, k, budget); rows.push({ t, k, i, s, rec: k === 'IF' && budget === 20 }) }))
  const if20 = DISKS.map((t) => statAt(t, 'IF', 20)), if15 = DISKS.map((t) => statAt(t, 'IF', 15))
  const worst15 = if15[2]

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
    <Section id="verdict-budget" letter="B" title="The final answer: which model, which budget" band>
      <Pr><p>An examiner cannot read every file, so the question is how many to read. The model ranks the files, the examiner reads from the top, and the <b>budget</b> is the share of files read. The pre-registered study tested three models on three disks, five times each with different random seeds. Here is where it ended up.</p></Pr>
      <div className="spread">
        <div className="finding l">
          <div className="k">The answer</div>
          <div className="disp" style={{ color: 'var(--m0)' }}>Isolation Forest</div>
          <div className="sub">19 features · 20% budget</div>
          <div className="stamprow"><span className="stamp" ref={stampRef}>Recommended</span></div>
          <p>At a 20% budget it caught <b>{if20[0].mean} of {if20[0].n}</b>, <b>{if20[1].mean} of {if20[1].n}</b> and <b>{if20[2].mean} of {if20[2].n}</b> evidence targets on the three disks, in <b>all 5 seeds</b>. At 15% it caught {f1(if15[0].mean)}, {f1(if15[1].mean)} and {f1(if15[2].mean)} of the same targets, and its weakest seed on Image 3 caught {worst15.min} of {worst15.n}.</p>
        </div>
        <div className="finding r">
          <div className="k">The other two</div>
          <div className="disp" style={{ color: 'var(--ink2)' }}>Behind it</div>
          <div className="sub">same 20% budget</div>
          <p>One-Class SVM caught {DISKS.map((t) => f1(statAt(t, 'OC-SVM', 20).mean) + '/' + statAt(t, 'OC-SVM', 20).n).join(', ')}. LOF caught {DISKS.map((t) => f1(statAt(t, 'LOF', 20).mean) + '/' + statAt(t, 'LOF', 20).n).join(', ')}. LOF also fails the explainability tests in Exhibit G.</p>
        </div>
      </div>
      <Integrity />
    </Section>
    <section className="ex cont"><div className="wrap">
      <div className="chartgrid" style={{ marginTop: 0 }}>
        <div>
          <div className="vtop"><h3 className="cap" style={{ margin: 0 }}>Targets caught at a chosen budget</h3>
            <div className="fld"><span className="lab">Budget</span>
              <Seg label="Review budget" items={TICKS.map((t) => t + '%')} value={TICKS.indexOf(budget)} onPick={(i) => setBudget(TICKS[i])} /></div></div>
          <p className="small" style={{ marginBottom: 6 }}>Mean share of targets caught over 5 seeds. The dashed line marks 90%. {budget === 20 ? 'At 20% the recommended setting, Isolation Forest, is outlined.' : 'Pick 20% to see the recommended setting.'}</p>
          <div className="vchart" ref={barsRef}>
            <div className="ninety" aria-hidden="true"><span>90%</span></div>
            {rows.map((r) => {
              const val = r.s.mean / r.s.n * 100
              return (
                <div key={r.t + r.k} className={'vrow' + (r.rec ? ' rec' : '')}>
                  <div className="vl">{dn(r.t)} · {SHORT[r.i]}{r.rec ? <em>recommended</em> : null}</div>
                  <div className="vt"><i data-grow="1" data-w={val} style={{ width: val + '%', background: 'var(' + MVAR[r.i] + ')' }}></i></div>
                  <div className="vv"><Num value={val} fmt={(v) => v.toFixed(1) + '%'} /></div></div>
              )
            })}
          </div>
        </div>
        <aside className="side" ref={whyRef} style={{ marginTop: 0 }}>
          <b>Why 20% and not 15%</b>
          <p>The pre-registered rule asks for at least 90% of the targets in every seed on every disk. At 15% Isolation Forest misses it: on Image 3 the weakest seed caught {worst15.min} of {worst15.n}, which is {f1(worst15.min / worst15.n * 100)}%. At 20% it passes.</p>
          <p><b>Files read at 20%</b></p>
          {DISKS.map((t) => <div key={t} className="mrow"><span className="mn">{dn(t)}</span><div className="bar1"><i data-grow="1" data-w={20 / 25 * 100} style={{ width: (20 / 25 * 100) + '%', background: 'var(--m0)' }}></i></div><span className="num">{fmt(Math.round(0.2 * A2.disks[t].N))}</span></div>)}
        </aside>
      </div>
      <p className="big-rule"><b style={{ fontWeight: 500 }}>The simple rule:</b> read the top 20% of files with Isolation Forest on the 19 features. On these three disks that found every target, every time.</p>
      <Pr>
        <h3 className="cap" style={{ marginTop: 40 }}>What this answer does not claim</h3>
        <ul className="plain">
          <li><b>The budget is not free.</b> 20% of Image 3 is {fmt(Math.round(0.2 * A2.disks.img3.N))} files. Most of what the examiner reads is not evidence (Exhibit D).</li>
          <li><b>The exact budget moves.</b> The point where 90% of targets are reached shifts by several percentage points between seeds, and the pre-registered test of that failed (Exhibit F, A2).</li>
          <li><b>A plain rule is nearly as good on one disk.</b> On Image 3 the targets are the examiner-tagged files in the suspect’s home folder, so simply reading the user folder also finds 34 of 34 (Exhibit F, A4).</li>
          <li><b>Three disks are three disks.</b> Nothing here shows the same budget works on a disk from another case.</li>
        </ul>
      </Pr>
      <div style={{ marginTop: 48 }}>
        <h3 className="cap">Targets caught, by budget</h3>
        <div className="tbl"><table><thead><tr><th>Disk · model</th>{COLS.map((c) => <th key={c} className={'n' + (c === 20 ? ' star' : '')}>{c}%</th>)}</tr></thead><tbody>{DISKS.map((t) => MK.map((k, i) => (
          <tr key={t + k}><td><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{dn(t)} · {SHORT[i]}</td>{COLS.map((c) => {
            const x = statAt(t, k, c), r = x.mean / x.n * 100
            return <td key={c} className={'n' + (c === 20 ? ' star' : '')}><div>{f1(x.mean)}/{x.n}</div><div className={'sub' + (r >= 90 ? ' hi' : '')}>{r.toFixed(1)}%{x.max > x.min ? ' · seeds ' + rangeTxt(x.min, x.max) : ''}</div></td>
          })}</tr>
        )))}</tbody></table></div>
        <Pr><p className="small" style={{ marginTop: 10 }}>Means over 5 seeds, with the lowest to highest seed where they differ. Red percentages are at or above 90%. The shaded column is the recommended 20% budget. Source: pre-registered study A2.</p></Pr>
      </div>
    </div></section>
    </>
  )
}
