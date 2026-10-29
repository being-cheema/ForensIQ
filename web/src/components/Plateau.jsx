import { useMemo, useRef, useState } from 'react'
import { D, MODELS, SHORT, MVAR, fmt, short } from '../lib/data'
import { useDraw } from '../lib/hooks'
import { exportSvg } from '../lib/svgexport'
import { seedCurve, at, MK, f1, rangeTxt, A2, DISKS } from '../lib/study'
import { useLayoutEffect } from 'react'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'

const TW = (s, fs) => s.length * fs * 0.56
const clamp = (v, a, b) => Math.min(b, Math.max(a, v))
export const imgName = (img) => short(D.images[img].label)
const col = (i) => 'var(' + MVAR[i] + ')'

/* width of an element, kept current with a ResizeObserver */
export function useBox(ref) {
  const [w, setW] = useState(0)
  useLayoutEffect(() => {
    const el = ref.current; if (!el) return
    const f = () => setW(Math.round(el.getBoundingClientRect().width))
    f()
    if (!window.ResizeObserver) { window.addEventListener('resize', f); return () => window.removeEventListener('resize', f) }
    const ro = new ResizeObserver(f); ro.observe(el); return () => ro.disconnect()
  }, [])
  return w
}

/* spread labels vertically so they never overlap */
function dodge(items, gap, lo, hi) {
  const s = items.slice().sort((a, b) => a.y - b.y)
  for (let i = 0; i < s.length; i++) s[i].y = Math.max(s[i].y, i ? s[i - 1].y + gap : lo)
  for (let i = s.length - 1; i >= 0; i--) { const mx = i === s.length - 1 ? hi : s[i + 1].y - gap; if (s[i].y > mx) s[i].y = mx }
  return s
}

/* ---------------- Figure 1: targets caught against budget, mean and range of 5 seeds ---------------- */
function RecallPanel({ img, pct, m, compact, head }) {
  const box = useRef()
  const w = useBox(box)
  const cs = useMemo(() => MK.map((k) => seedCurve(img, k)), [img])
  const wide = w >= 700 && !compact
  const L = 44, R = wide ? 126 : compact ? 20 : 20, T = 16 + 3 * 13 + 6, B = 44
  const H = compact ? 300 : w >= 640 ? 400 : 330
  const pw = Math.max(40, w - L - R), ph = H - T - B
  const X = (b) => L + b / 100 * pw
  const Y = (v) => T + (1 - v / 100) * ph
  const narrow = w < 520
  const ends = dodge(cs.map((c, i) => ({ i, y: Y(100) + 4 })), 15, T + 4, T + ph)
  const sel = cs[m]
  const lanes = cs.map((c, i) => i).sort((a, b) => cs[b].sum.plateau_pct_mean - cs[a].sum.plateau_pct_mean)
  return (
    <div ref={box} className="fpanel">
      {head ? <h4 className="fph">{imgName(img)}</h4> : null}
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Share of evidence targets caught against review budget on ' + imgName(img) + ', mean of 5 seeds with the lowest and highest seed as a band: ' + cs.map((c, i) => SHORT[i] + ' reaches 90% at ' + f1(c.sum.knee_pct_mean) + '% of files and its last target at ' + f1(c.sum.plateau_pct_mean) + '%').join('; ')}>
          {[0, 25, 50, 75, 100].map((v) => <line key={v} className="gl" x1={L} x2={L + pw} y1={Y(v)} y2={Y(v)} />)}
          <line className="ref" x1={L} x2={L + pw} y1={Y(90)} y2={Y(90)} />
          {[0, 25, 50, 75, 90, 100].map((v) => <text key={v} className={v === 90 ? 'hi' : ''} x={L - 7} y={Y(v) + 4} textAnchor="end">{v}</text>)}
          <text className="axt" transform={'translate(11 ' + (T + ph / 2) + ') rotate(-90)'} textAnchor="middle">targets caught, %</text>
          <rect className="fadein dz" data-op="0.06" x={X(sel.sum.plateau_pct_mean)} y={T} width={Math.max(0, X(100) - X(sel.sum.plateau_pct_mean))} height={ph} fill={col(m)} opacity="0.06" />
          {cs.map((c, i) => {
            const up = A2.budgets.map((b, j) => X(b).toFixed(1) + ',' + Y(c.hi[j] / c.nT * 100).toFixed(1))
            const dn = A2.budgets.map((b, j) => X(b).toFixed(1) + ',' + Y(c.lo[j] / c.nT * 100).toFixed(1)).reverse()
            return <polygon key={'bd' + i} className="fadein band" data-op="0.16" points={up.concat(dn).join(' ')} fill={col(i)} opacity="0.16" />
          })}
          {cs.map((c, i) => (
            <path key={'ln' + i} className="draw" fill="none" stroke={col(i)} strokeWidth={i === m ? 2.4 : 1.7} strokeLinejoin="round"
              d={A2.budgets.map((b, j) => (j ? 'L' : 'M') + X(b).toFixed(1) + ' ' + Y(c.mean[j] / c.nT * 100).toFixed(1)).join('')} />
          ))}
          {sel && !narrow && X(100) - Math.max(X(sel.sum.plateau_pct_mean) + 10, X(40)) > 200 ? (() => { const tx = Math.max(X(sel.sum.plateau_pct_mean) + 10, X(40)); return (
            <text className="fadein dzt" data-op="1" x={tx} y={Y(14)}>
              <tspan x={tx}>Dead zone. Every file read past</tspan><tspan x={tx} dy="15">here finds no new evidence.</tspan>
            </text>) })() : null}
          {cs.map((c, i) => {
            const out = [], s = c.sum
            const kx = X(s.knee_pct_mean), ky = Y(at(c.mean, s.knee_pct_mean) / c.nT * 100), ly = Y(90) + 20 + i * 13, t = '90% at ' + f1(s.knee_pct_mean) + '%', end = kx + 6 + TW(t, 11) > L + pw - 2
            out.push(<g key={'kn' + i} className="fadein ann" data-op="1">
              <line className="lead" x1={kx} x2={kx} y1={ky} y2={ly - 4} stroke={col(i)} />
              <circle cx={kx} cy={ky} r="4" fill={col(i)} stroke="var(--paper)" strokeWidth="1.5" />
              <text className="kt" x={kx + (end ? -6 : 6)} y={ly} textAnchor={end ? 'end' : 'start'} fill={col(i)}>{t}</text></g>)
            const px = X(s.plateau_pct_mean), py = Y(100), pl = 13 + lanes.indexOf(i) * 13
            const t2 = (compact ? 'last ' : 'last target ') + f1(s.plateau_pct_mean) + '%', end2 = px + 6 + TW(t2, 11) > L + pw - 2
            out.push(<g key={'pl' + i} className="fadein ann" data-op="1">
              <line className="lead" x1={px} x2={px} y1={pl + 3} y2={py - 4} stroke={col(i)} />
              <circle cx={px} cy={py} r="4.2" fill="var(--paper)" stroke={col(i)} strokeWidth="2" />
              <text className="kt" x={px + (end2 ? -6 : 6)} y={pl} textAnchor={end2 ? 'end' : 'start'} fill={col(i)}>{t2}</text></g>)
            return out
          })}
          {wide ? ends.map((e) => <text key={'el' + e.i} className="fadein lbl" data-op="1" x={L + pw + 9} y={e.y} fill={col(e.i)}>{SHORT[e.i]}</text>) : null}
          <line className="ax" x1={L} x2={L} y1={T} y2={T + ph} />
          <g>
            <line className="ax" x1={L} x2={L + pw} y1={T + ph} y2={T + ph} />
            {(narrow ? [0, 25, 50, 75, 100] : [0, 20, 40, 60, 80, 100]).map((t) => <g key={t}><line className="ax" x1={X(t)} x2={X(t)} y1={T + ph} y2={T + ph + 4} /><text x={X(t)} y={T + ph + 17} textAnchor="middle">{t + '%'}</text></g>)}
            <text className="axt" x={L + pw / 2} y={T + ph + 34} textAnchor="middle">review budget, % of files read</text>
          </g>
          <g className="rule">
            <line x1={X(clamp(pct * 100, 0, 100))} x2={X(clamp(pct * 100, 0, 100))} y1={T} y2={T + ph - 16} />
            <text x={X(clamp(pct * 100, 0, 100)) + 5} y={T + ph - 22} textAnchor="start">{'your budget ' + f1(pct * 100) + '%'}</text>
          </g>
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- Figure 2: how far the 90% point moves between seeds ---------------- */
function KneePanel({ img }) {
  const box = useRef(), w = useBox(box)
  const L = 70, R = 14, T = 8, PITCH = 22, B = 38
  const H = T + MK.length * PITCH + B
  const pw = Math.max(60, w - L - R), X = (v) => L + (v / 100) * pw
  return (
    <div ref={box} className="fpanel">
      <h4 className="fph">{imgName(img)}</h4>
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Budget needed to reach 90% of targets on ' + imgName(img) + ', lowest to highest of 5 seeds: ' + MK.map((k, i) => { const s = A2.disks[img].models[k].summary; return SHORT[i] + ' ' + f1(s.knee_pct_min) + ' to ' + f1(s.knee_pct_max) + '%' }).join('; ')}>
          {[0, 25, 50, 75, 100].map((v) => <line key={v} className="gl" x1={X(v)} x2={X(v)} y1={T} y2={H - B} />)}
          {MK.map((k, i) => {
            const s = A2.disks[img].models[k].summary, y = T + i * PITCH + PITCH / 2
            return (
              <g key={k}>
                <text x={L - 8} y={y + 4} textAnchor="end" style={{ fill: col(i) }}>{SHORT[i].replace('Isolation Forest', 'IF').replace('One-Class SVM', 'OC-SVM')}</text>
                {s.knee_pct_max > s.knee_pct_min ? <g stroke={col(i)} strokeWidth="1.6" fill="none">
                  <line className="draw" x1={X(s.knee_pct_min)} x2={X(s.knee_pct_max)} y1={y} y2={y} />
                  <line x1={X(s.knee_pct_min)} x2={X(s.knee_pct_min)} y1={y - 4} y2={y + 4} /><line x1={X(s.knee_pct_max)} x2={X(s.knee_pct_max)} y1={y - 4} y2={y + 4} /></g> : null}
                <circle className="fadein" data-op="1" cx={X(s.knee_pct_mean)} cy={y} r="4" fill={col(i)} stroke="var(--paper)" strokeWidth="1.2" />
                <text className="bv" x={X(s.knee_pct_max) + 8 > L + pw - 60 ? X(s.knee_pct_min) - 8 : X(s.knee_pct_max) + 8} y={y + 4} textAnchor={X(s.knee_pct_max) + 8 > L + pw - 60 ? 'end' : 'start'}>{rangeTxt(s.knee_pct_min, s.knee_pct_max)}%</text>
                <title>{SHORT[i] + ': 90% of targets reached at ' + f1(s.knee_pct_mean) + '% of files on average; lowest seed ' + f1(s.knee_pct_min) + '%, highest ' + f1(s.knee_pct_max) + '%'}</title>
              </g>
            )
          })}
          {[0, 25, 50, 75, 100].map((v) => <text key={v} x={X(v)} y={H - B + 14} textAnchor="middle">{v}</text>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">files read to reach 90% of targets, %</text>
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- figure frame ---------------- */
export function Fig({ n, name, caption, children }) {
  const ref = useRef()
  const dl = () => exportSvg(ref.current, 'forensiq-figure-' + n + '-' + name)
  return (
    <figure className="fgr">
      <div ref={ref} className="fgr-body">{children}</div>
      <figcaption><span className="fgn">Figure {n}.</span> {caption} <button type="button" className="lnk svgdl" onClick={dl} aria-label={'Download Figure ' + n + ' as SVG'}>SVG</button></figcaption>
    </figure>
  )
}

/* ---------------- readout and ledger ---------------- */
function Readout({ img, pct }) {
  const im = D.images[img], K = Math.max(1, Math.round(pct * im.files)), b = pct * 100
  return (
    <div className="rdo">
      <p className="small rdo-h" aria-live="polite">At your budget: reading <b className="mono">{f1(b)}%</b> of {imgName(img)}, which is {fmt(K)} of {fmt(im.files)} files</p>
      <div className="tbl"><table><thead><tr><th>Model</th><th className="n">Targets caught, run seed 42</th><th className="n">Mean of 5 seeds</th><th className="n">Lowest to highest seed</th></tr></thead>
        <tbody>{MK.map((k, i) => {
          const c = seedCurve(img, k), exact = im.targets.filter((t) => t.ranks[MODELS[i]] <= K).length
          const ok = b >= 1
          return (
            <tr key={k}><td><i className="key" style={{ background: col(i) }}></i>{SHORT[i]}</td>
              <td className="n">{exact} / {c.nT}</td>
              <td className="n">{ok ? f1(at(c.mean, b)) + ' / ' + c.nT : 'n/a'}</td>
              <td className="n">{ok ? rangeTxt(at(c.lo, b), at(c.hi, b)) : 'n/a'}</td></tr>)
        })}</tbody></table></div>
      {b < 1 ? <p className="small">The five-seed curves are sampled every 1% of the disk, so they are not read below 1%.</p> : null}
    </div>
  )
}

function Ledger({ img }) {
  return (
    <div className="tbl ledger"><table>
      <thead><tr><th>Disk</th><th>Model</th><th className="n">Caught at 15%</th><th className="n">Caught at 20%</th><th className="n">Budget for 90% (mean)</th><th className="n">Lowest to highest seed</th><th className="n">Budget for last target</th><th className="n">Dead zone</th></tr></thead>
      <tbody>{DISKS.map((t) => MK.map((k, i) => {
        const s = A2.disks[t].models[k].summary, n = s.targets
        return (
          <tr key={t + k} className={(i === 0 ? 'grp' : '') + (t === img ? ' cur' : '')}>
            <td>{i === 0 ? imgName(t) : ''}</td><td><i className="key" style={{ background: col(i) }}></i>{SHORT[i]}</td>
            <td className="n">{f1(s.at15_mean)} / {n}</td><td className="n">{f1(s.at20_mean)} / {n}</td>
            <td className="n">{f1(s.knee_pct_mean)}%</td><td className="n">{rangeTxt(s.knee_pct_min, s.knee_pct_max)}%</td>
            <td className="n">{f1(s.plateau_pct_mean)}%</td><td className="n">{f1(s.dead_zone_pct)}% of the disk</td>
          </tr>)
      }))}</tbody></table></div>
  )
}

/* ---------------- the exhibit ---------------- */
export default function Plateau({ img, m, pct }) {
  const [all, setAll] = useState(false)
  const body = useRef()
  useDraw(body, [img, all])
  const sel = seedCurve(img, MK[m]).sum
  const take = MK[m] === 'IF'
    ? 'Isolation Forest reaches 90% of the targets on ' + imgName(img) + ' after ' + f1(sel.knee_pct_mean) + '% of the files on average, and its last target after ' + f1(sel.plateau_pct_mean) + '%. The remaining ' + f1(sel.dead_zone_pct) + '% of the disk adds only false alarms.'
    : SHORT[m] + ' reaches 90% of the targets on ' + imgName(img) + ' after ' + f1(sel.knee_pct_mean) + '% of the files on average, and its last target after ' + f1(sel.plateau_pct_mean) + '%. The rest of the disk, ' + f1(sel.dead_zone_pct) + '%, adds only false alarms.'
  const imgs = all ? DISKS : [img]
  return (
    <Section id="plateau" letter="C" title="How much reading until nothing new turns up?">
      <Pr note={<><b>{take}</b> The 90% point moves by {f1(sel.knee_spread_pp)} percentage points between the five seeds on this disk, so the exact budget is not a fixed number.</>}>
        <p>Reading more files always finds more evidence, but not forever. After some point the last target has been found and every further file is a false alarm. This chart follows each model from 0% to 100% of the disk.</p>
        <p>Each line is the average of five runs with different random seeds. The shaded band runs from the weakest to the strongest of those five runs. A dot marks the <b>90% point</b>, the first budget where 90% of the targets are found. A ring marks the <b>last target</b>. Everything to the right of it is the dead zone.</p>
      </Pr>
      <div className="fgctl">
        <div className="fld"><span className="lab">Figure 1 shows</span>
          <Seg label="Disks shown in Figure 1" items={['This disk', 'All three disks']} value={all ? 1 : 0} onPick={(i) => setAll(i === 1)} /></div>
      </div>
      <div ref={body}>
        <Fig n="1" name={'recall-' + (all ? 'all' : img)} caption={<>Share of evidence targets caught against review budget, 0 to 100% of the files, {all ? 'one panel per disk' : imgName(img)}. Lines are the mean of 5 seeds; the band is the weakest to the strongest seed. A target counts as caught when any of its files is in the top of the ranking. Dots mark where each model reaches 90%; rings mark its last target. The shaded dead zone follows the model chosen in the control bar. The red rule is your budget.</>}>
          <div className={all ? 'fgrid' : ''}>
            {imgs.map((t) => <RecallPanel key={t} img={t} pct={pct} m={m} compact={all} head={all} />)}
          </div>
        </Fig>
        <Readout img={img} pct={pct} />
        <Fig n="2" name="ninety-percent-spread" caption={<>The budget needed to reach 90% of the targets, per disk and model. The dot is the mean of the 5 seeds and the line runs from the lowest to the highest seed. A long line means the answer depends on the random draw. Isolation Forest is not tight: its 90% point moves by several percentage points between seeds.</>}>
          <div className="fgrid">{DISKS.map((t) => <KneePanel key={t} img={t} />)}</div>
        </Fig>
      </div>
      <div className="ledgerwrap">
        <h3 className="cap">Where each model stops finding evidence</h3>
        <Ledger img={img} />
        <Pr><p className="small" style={{ marginTop: 10 }}>Targets caught are means over 5 seeds. The dead zone is the share of the disk after the model’s last target. Whether the 90% point is stable enough is a pre-registered test, A2 in Exhibit F. It fails.</p></Pr>
      </div>
    </Section>
  )
}
