import { memo, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { D, IMGS, fmt, short } from '../lib/data'
import { AN, canAnim } from '../lib/motion'
import { useDraw, useOnceInView } from '../lib/hooks'
import { CFGS, JOIN, curve, curveSet, fb, fn1 } from '../lib/curves'
import { exportSvg } from '../lib/svgexport'
import Num from '../lib/Num'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr } from '../lib/Prose'

const TW = (s, fs) => s.length * fs * 0.56
const clamp = (v, a, b) => Math.min(b, Math.max(a, v))
const imgName = (img) => short(D.images[img].label)

/* width of an element, kept current with a ResizeObserver */
function useBox(ref) {
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

const xAxis = (log, L, pw) => ({
  x: log ? (b) => L + (Math.log10(Math.max(0.1, b)) + 1) / 3 * pw : (b) => L + b / 100 * pw,
  inv: log ? (x) => Math.pow(10, (x - L) / pw * 3 - 1) : (x) => (x - L) / pw * 100
})

function AxisX({ X, log, y, L, pw, narrow }) {
  const ticks = log ? [0.1, 1, 10, 100] : narrow ? [0, 25, 50, 75, 100] : [0, 20, 40, 60, 80, 100]
  return (
    <g>
      <line className="ax" x1={L} x2={L + pw} y1={y} y2={y} />
      {ticks.map((t) => <g key={t}><line className="ax" x1={X(t)} x2={X(t)} y1={y} y2={y + 4} /><text x={X(t)} y={y + 17} textAnchor="middle">{t + '%'}</text></g>)}
      <text className="axt" x={L + pw / 2} y={y + 34} textAnchor="middle">review budget, % of files read{log ? ' (log scale)' : ''}</text>
    </g>
  )
}

/* spread labels vertically so they never overlap */
function dodge(items, gap, lo, hi) {
  const s = items.slice().sort((a, b) => a.y - b.y)
  for (let i = 0; i < s.length; i++) s[i].y = Math.max(s[i].y, i ? s[i - 1].y + gap : lo)
  for (let i = s.length - 1; i >= 0; i--) { const mx = i === s.length - 1 ? hi : s[i + 1].y - gap; if (s[i].y > mx) s[i].y = mx }
  return s
}

function Rule({ x, y1, y2, pct, anchor, top }) {
  return (
    <g className="rule">
      <line x1={x} x2={x} y1={y1} y2={y2} />
      <text x={x + (anchor === 'end' ? -5 : 5)} y={top ? y1 + 10 : y2 - 6} textAnchor={anchor || 'start'}>{'your budget ' + fb(pct * 100)}</text>
    </g>
  )
}

/* ---------------- Figure 1: recall against budget ---------------- */
function RecallPanel({ img, log, pct, m, hov, setHov, compact, narrowHead }) {
  const box = useRef(), svg = useRef()
  const w = useBox(box)
  const cs = useMemo(() => curveSet(img), [img])
  const wide = w >= 700 && !compact
  const L = 44, R = wide ? 150 : compact ? 62 : 72, T = 14 + cs.length * 13 + 6, B = 44
  const H = compact ? 300 : w >= 640 ? 420 : 340
  const pw = Math.max(40, w - L - R), ph = H - T - B
  const { x: X, inv } = xAxis(log, L, pw)
  const Y = (v) => T + (1 - v / 100) * ph
  const narrow = w < 520
  const hasSw = !!cs.find((c) => c.sw && c.ranks)
  const selId = CFGS[m] ? CFGS[m].id : 'IF-23'
  const hb = hov ? hov.b : null

  const lanes = cs.map((c) => c).sort((a, b) => b.plateau.b - a.plateau.b)   // top lane: furthest plateau
  const laneOf = (c) => lanes.indexOf(c)
  const ends = dodge(cs.map((c) => ({ c, y: Y(c.at(100).recall) + 4 })), 14, T + 4, T + ph)
  const sel = cs.find((c) => c.cfg.id === selId) || cs[0]

  const move = (e) => {
    if (!svg.current) return
    const r = svg.current.getBoundingClientRect(), x = e.clientX - r.left
    if (x < L - 2 || x > L + pw + 2) return
    setHov({ img, b: clamp(inv(x), log ? 0.1 : 0, 100), touch: e.pointerType === 'touch' })
  }
  const leave = (e) => { if (e.pointerType !== 'touch') setHov(null) }

  return (
    <div ref={box} className="fpanel">
      {narrowHead ? <h4 className="fph">{imgName(img)}</h4> : null}
      {w > 0 ? (
        <svg ref={svg} className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Evidence recall against review budget on ' + imgName(img) + ': ' + cs.map((c) => c.cfg.lab + ' reaches 90% at ' + (c.knee == null ? 'never' : fb(c.knee)) + ' and its last evidence at ' + fb(c.plateau.b)).join('; ')}>
          {[0, 25, 50, 75, 100].map((v) => <line key={v} className="gl" x1={L} x2={L + pw} y1={Y(v)} y2={Y(v)} />)}
          <line className="ref" x1={L} x2={L + pw} y1={Y(90)} y2={Y(90)} />
          {[0, 25, 50, 75, 90, 100].map((v) => <text key={v} className={v === 90 ? 'hi' : ''} x={L - 7} y={Y(v) + 4} textAnchor="end">{v}</text>)}
          <text className="axt" transform={'translate(11 ' + (T + ph / 2) + ') rotate(-90)'} textAnchor="middle">evidence recall, %</text>
          {cs.map((c) => <rect key={'dz' + c.cfg.id} className="fadein dz" data-op="0.05" x={X(c.plateau.b)} y={T} width={Math.max(0, X(100) - X(c.plateau.b))} height={ph} fill={'var(' + c.cfg.v + ')'} opacity="0.05" />)}
          {hasSw ? (() => { const jx = X(JOIN); return (
            <g className="join"><line x1={jx} x2={jx} y1={T} y2={T + ph} />
              {jx - L > 76 ? <text x={jx - 4} y={T + ph - 5} textAnchor="end">exact ranks</text> : null}
              <text x={jx + 4} y={T + ph - 5}>sweep means</text></g>) })() : null}
          {cs.map((c) => {
            if (!c.sw) return null
            const up = c.sw.pct.map((p, i) => X(p).toFixed(1) + ',' + Y(Math.min(100, c.sw.recall[i] + c.sw.std[i])).toFixed(1))
            const dn = c.sw.pct.map((p, i) => X(p).toFixed(1) + ',' + Y(Math.max(0, c.sw.recall[i] - c.sw.std[i])).toFixed(1)).reverse()
            return <polygon key={'bd' + c.cfg.id} className="fadein band" data-op="0.15" points={up.concat(dn).join(' ')} fill={'var(' + c.cfg.v + ')'} opacity="0.15" />
          })}
          {cs.map((c) => {
            let d = ''
            if (c.ranks) d = c.steps().map((p, i) => (i ? 'L' : 'M') + X(p[0]).toFixed(1) + ' ' + Y(p[1]).toFixed(1)).join('')
            if (c.sw) d += c.sw.pct.map((p, i) => ((d || i) ? 'L' : 'M') + X(p).toFixed(1) + ' ' + Y(c.sw.recall[i]).toFixed(1)).join('')
            return <path key={'ln' + c.cfg.id} className="draw" data-dash={c.cfg.dash} fill="none" stroke={'var(' + c.cfg.v + ')'} strokeWidth={c.cfg.id === selId ? 2.4 : 1.7} strokeLinejoin="round" strokeDasharray={c.cfg.dash || undefined} d={d} />
          })}
          {sel && !narrow && X(100) - Math.max(X(sel.plateau.b) + 10, X(40)) > 200 ? (() => { const tx = Math.max(X(sel.plateau.b) + 10, X(log ? 30 : 40)); return (
            <text className="fadein dzt" data-op="1" x={tx} y={Y(14)}>
              <tspan x={tx}>Dead zone. Every file read past</tspan><tspan x={tx} dy="15">here finds no new evidence.</tspan>
            </text>) })() : null}
          {cs.map((c) => {
            const col = 'var(' + c.cfg.v + ')'
            const out = []
            if (c.knee != null) {
              const kx = X(c.knee), ky = Y(c.at(c.knee).recall), ly = Y(90) + 20 + cs.indexOf(c) * 13, t = '90% at ' + fb(c.knee), end = kx + 6 + TW(t, 11) > L + pw - 2
              out.push(<g key={'kn' + c.cfg.id} className="fadein ann" data-op="1">
                <line className="lead" x1={kx} x2={kx} y1={ky} y2={ly - 4} stroke={col} />
                <circle cx={kx} cy={ky} r="4" fill={col} stroke="var(--paper)" strokeWidth="1.5" />
                <text className="kt" x={kx + (end ? -6 : 6)} y={ly} textAnchor={end ? 'end' : 'start'} fill={col}>{t}</text></g>)
            }
            const p = c.plateau, px = X(p.b), py = Y(p.fm), ly = 13 + laneOf(c) * 13
            const t = p.partial ? 'tops out at ' + fn1(p.fm) + '%' : p.b >= 90 ? 'last target only at ' + fb(p.b) : (compact ? 'plateau ' : 'last evidence ') + fb(p.b)
            const end = px + 6 + TW(t, 11) > L + pw - 2
            out.push(<g key={'pl' + c.cfg.id} className="fadein ann" data-op="1">
              <line className="lead" x1={px} x2={px} y1={ly + 3} y2={py - 4} stroke={col} />
              <circle cx={px} cy={py} r="4.2" fill="var(--paper)" stroke={col} strokeWidth="2" />
              <text className="kt" x={px + (end ? -6 : 6)} y={ly} textAnchor={end ? 'end' : 'start'} fill={col}>{t}</text></g>)
            return out
          })}
          {ends.map((e) => <text key={'el' + e.c.cfg.id} className="fadein lbl" data-op="1" x={L + pw + 9} y={e.y} fill={'var(' + e.c.cfg.v + ')'}>{wide ? e.c.cfg.lab : e.c.cfg.lab2}</text>)}
          <line className="ax" x1={L} x2={L} y1={T} y2={T + ph} />
          <AxisX X={X} log={log} y={T + ph} L={L} pw={pw} narrow={narrow} />
          <Rule x={X(clamp(pct * 100, log ? 0.1 : 0, 100))} y1={T} y2={T + ph - 16} pct={pct} />
          {hb != null ? (
            <g className="hov no-export" pointerEvents="none">
              <line x1={X(hb)} x2={X(hb)} y1={T} y2={T + ph} />
              {cs.map((c) => { const a = c.at(hb); return a ? <circle key={c.cfg.id} cx={X(hb)} cy={Y(a.recall)} r="3.6" fill={'var(' + c.cfg.v + ')'} stroke="var(--paper)" strokeWidth="1.2" /> : null })}
            </g>
          ) : null}
          <rect className="hit no-export" x={L} y={T} width={pw} height={ph} fill="transparent" onPointerMove={move} onPointerDown={move} onPointerLeave={leave} />
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- Figure 2: false alarms and precision ---------------- */
function logAxisY(Y, lmin, lmax, L, pw, fmtT) {
  const out = []
  for (let e = lmin; e <= lmax; e++) out.push(<g key={e}><line className="gl" x1={L} x2={L + pw} y1={Y(Math.pow(10, e))} y2={Y(Math.pow(10, e))} /><text x={L - 7} y={Y(Math.pow(10, e)) + 4} textAnchor="end">{fmtT(e)}</text></g>)
  return out
}
const faT = (e) => (e >= 3 ? Math.pow(10, e - 3) + 'k' : String(Math.pow(10, e)))
const prT = (e) => (e >= 0 ? Math.pow(10, e) + '%' : +Math.pow(10, e).toFixed(2) + '%')

function ErrPanel({ img, log, pct, hov, kind, title }) {
  const box = useRef()
  const w = useBox(box)
  const cs = useMemo(() => curveSet(img), [img])
  const isFa = kind === 'fa'
  const compact = w < 520
  const L = isFa ? 46 : 46, R = isFa ? (w >= 700 ? 112 : 78) : (w >= 520 ? 76 : 70), T = 12, B = 44, H = compact ? 250 : 290
  const pw = Math.max(40, w - L - R), ph = H - T - B
  const { x: X } = xAxis(log, L, pw)
  const val = (a) => (isFa ? a.fa : a.prec)
  const series = useMemo(() => cs.map((c) => ({ c, pts: c.bs.filter((b) => b >= 0.1).map((b) => c.at(b)).filter((a) => a && val(a) != null && val(a) > 0) })), [cs, kind])
  let vmin = Infinity, vmax = 0
  series.forEach((s) => s.pts.forEach((a) => { vmin = Math.min(vmin, val(a)); vmax = Math.max(vmax, val(a)) }))
  const lmin = isFa ? Math.max(0, Math.floor(Math.log10(vmin))) : Math.floor(Math.log10(vmin)), lmax = isFa ? Math.ceil(Math.log10(vmax)) : 2
  const Y = (v) => T + (1 - (Math.log10(Math.max(v, Math.pow(10, lmin))) - lmin) / (lmax - lmin)) * ph
  const ends = dodge(series.map((s) => { const a = s.pts[s.pts.length - 1]; return { s, a, y: Y(val(a)) + 4 } }), isFa ? 27 : 14, T + 4, T + ph)
  const hb = hov ? hov.b : null
  return (
    <div ref={box} className="fpanel">
      <h4 className="fph">{title}</h4>
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img" aria-label={title + ' against review budget on ' + imgName(img)}>
          {logAxisY(Y, lmin, lmax, L, pw, isFa ? faT : prT)}
          <text className="axt" transform={'translate(11 ' + (T + ph / 2) + ') rotate(-90)'} textAnchor="middle">{isFa ? 'false alarms (files)' : 'precision'}</text>
          {series.map((s) => (
            <path key={s.c.cfg.id} className="draw" data-dash={s.c.cfg.dash} fill="none" stroke={'var(' + s.c.cfg.v + ')'} strokeWidth="1.8" strokeLinejoin="round" strokeDasharray={s.c.cfg.dash || undefined}
              d={s.pts.map((a, i) => (i ? 'L' : 'M') + X(a.b).toFixed(1) + ' ' + Y(val(a)).toFixed(1)).join('')} />
          ))}
          {series.map((s) => {
            const a = s.c.at(s.c.plateau.b); if (!a || val(a) == null || val(a) <= 0) return null
            return <circle key={'pd' + s.c.cfg.id} className="fadein" data-op="1" cx={X(a.b)} cy={Y(val(a))} r="4.2" fill="var(--paper)" stroke={'var(' + s.c.cfg.v + ')'} strokeWidth="2" />
          })}
          {ends.map((e) => (
            <text key={'e' + e.s.c.cfg.id} className="fadein lbl" data-op="1" x={L + pw + 8} y={e.y} fill={'var(' + e.s.c.cfg.v + ')'}>
              {isFa || w >= 520 ? e.s.c.cfg.lab2 : e.s.c.cfg.lab2.replace(' · ', '')}
              {isFa ? <tspan className="num2" x={L + pw + 8} dy="12">{fmt(Math.round(val(e.a)))}</tspan> : null}
            </text>
          ))}
          <line className="ax" x1={L} x2={L} y1={T} y2={T + ph} />
          <AxisX X={X} log={log} y={T + ph} L={L} pw={pw} narrow={w < 520} />
          <Rule x={X(clamp(pct * 100, log ? 0.1 : 0, 100))} y1={T} y2={T + ph - 16} pct={pct} anchor={w < 520 ? 'start' : 'start'} />
          {hb != null ? <line className="hovl no-export" x1={X(hb)} x2={X(hb)} y1={T} y2={T + ph} /> : null}
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- Figure 3: marginal yield ---------------- */
function useBarsSvg(ref, deps) {
  const seen = useRef(false), timer = useRef(0)
  const run = () => {
    const root = ref.current; if (!root || !canAnim()) return
    const els = root.querySelectorAll('rect.bar'); if (!els.length) return
    const settle = () => els.forEach((e) => { e.setAttribute('y', e.dataset.y); e.setAttribute('height', e.dataset.h) })
    clearTimeout(timer.current); AN.remove(els)
    AN.set(els, { height: 0 })
    AN({ targets: els, y: (e) => [+e.dataset.base, +e.dataset.y], height: (e) => [0, +e.dataset.h], duration: 520, delay: AN.stagger(9, { start: 60 }), easing: 'easeOutCubic', complete: settle })
    timer.current = setTimeout(settle, 1600 + els.length * 9)
  }
  useOnceInView(ref, () => { seen.current = true; run(); return () => { clearTimeout(timer.current); if (ref.current) AN.remove(ref.current.querySelectorAll('rect.bar')) } })
  useLayoutEffect(() => { if (seen.current) run() }, deps)
}

const YieldFig = memo(function YieldFig({ img, pct }) {
  const box = useRef()
  const w = useBox(box)
  const cs = useMemo(() => curveSet(img), [img])
  const bins = useMemo(() => cs.map((c) => Array.from({ length: 50 }, (_, i) => c.gain(i * 2, i * 2 + 2))), [cs])
  useBarsSvg(box, [img, w > 0])
  const top0 = Math.max.apply(null, bins.map((b) => Math.max.apply(null, b.map((v) => v || 0))))
  const mx = top0 > 6 ? 3 : Math.max(1, Math.ceil(top0))
  const L = 44, R = 12, sh = w < 560 ? 58 : 66, gap = 14, top = 8, B = 44
  const H = top + cs.length * (sh + gap) - gap + B
  const pw = Math.max(40, w - L - R), bw = pw / 50
  const X = (b) => L + b / 100 * pw
  const xend = top + cs.length * (sh + gap) - gap
  return (
    <div ref={box} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img" aria-label={'New evidence files found per extra 2% of review budget on ' + imgName(img)}>
          {cs.map((c, ci) => {
            const y0 = top + ci * (sh + gap) + sh, col = 'var(' + c.cfg.v + ')', p = c.plateau.b, px = X(p), pt = w < 520 ? 'plateau begins' : 'plateau begins at ' + fb(p)
            const endA = px > L + pw - 150
            let best = -1; bins[ci].forEach((v, i) => { if (v != null && (best < 0 || v > bins[ci][best])) best = i })
            return (
              <g key={c.cfg.id}>
                <text className="lbl" x={L + pw - 4} y={y0 - sh + 10} textAnchor="end" fill={col}>{w < 520 ? c.cfg.lab2 : c.cfg.lab}</text>
                <text x={L - 7} y={y0 + 4} textAnchor="end">0</text>
                <text x={L - 7} y={y0 - sh + 14} textAnchor="end">{mx + (top0 > 6 ? '+' : '')}</text>
                <line className="ax" x1={L} x2={L + pw} y1={y0} y2={y0} />
                {bins[ci].map((v, i) => {
                  if (v == null) return null
                  const h = Math.min(sh - 4, v / mx * (sh - 4)), y = y0 - h
                  return <rect key={i} className="bar" x={L + i * bw + 0.8} width={Math.max(0.5, bw - 1.6)} y={y} height={h} data-y={y} data-h={h} data-base={y0} fill={col} />
                })}
                {v0(bins[ci], best) ? <text className="bv" x={L + best * bw + bw / 2} y={y0 - Math.min(sh - 4, bins[ci][best] / mx * (sh - 4)) - 4} textAnchor={best * bw > pw - 40 ? 'end' : 'middle'} fill={col}>{'+' + fn1(bins[ci][best])}</text> : null}
                <g className="fadein" data-op="1">
                  <line className="plh" x1={px} x2={px} y1={y0 - sh + 16} y2={y0 + 1} stroke={col} />
                  <text className="kt" x={px + (endA ? -5 : 5)} y={y0 - 10} textAnchor={endA ? 'end' : 'start'} fill={col}>{pt}</text>
                </g>
              </g>
            )
          })}
          <line className="ax" x1={L} x2={L} y1={top} y2={xend} />
          <text className="axt" transform={'translate(11 ' + ((top + xend) / 2) + ') rotate(-90)'} textAnchor="middle">new evidence files per 2% of budget</text>
          <AxisX X={X} log={false} y={xend} L={L} pw={pw} narrow={w < 520} />
          <Rule x={X(pct * 100)} y1={top} y2={xend} pct={pct} top />
        </svg>
      ) : null}
    </div>
  )
})
const v0 = (arr, i) => i >= 0 && arr[i] > 0.05

/* ---------------- figure frame ---------------- */
function Fig({ n, name, caption, children }) {
  const ref = useRef()
  const dl = () => exportSvg(ref.current, 'forensiq-figure-' + n + '-' + name)
  return (
    <figure className="fgr">
      <div ref={ref} className="fgr-body">{children}</div>
      <figcaption><span className="fgn">Figure {n}.</span> {caption} <button type="button" className="lnk svgdl" onClick={dl} aria-label={'Download Figure ' + n + ' as SVG'}>SVG</button></figcaption>
    </figure>
  )
}

/* ---------------- readout ---------------- */
function Readout({ img, b, hovering }) {
  const cs = curveSet(img)
  return (
    <div className="rdo">
      <p className="small rdo-h" aria-live="polite">{hovering ? 'At the cursor' : 'At your budget'}: reading <b className="mono">{b < 1 ? b.toFixed(2) : b.toFixed(1)}%</b> of {imgName(img)}</p>
      <div className="tbl"><table><thead><tr><th>Model</th><th className="n">Files read</th><th className="n">Evidence found</th><th className="n">Recall</th><th className="n">Precision</th><th className="n">Dead reads</th></tr></thead>
        <tbody>{cs.map((c) => {
          const a = c.at(b)
          return (
            <tr key={c.cfg.id}><td><i className="key" style={{ background: 'var(' + c.cfg.v + ')' }}></i>{c.cfg.lab}</td>
              {a ? <>
                <td className="n"><Num dur={160} value={a.K} fmt={(v) => fmt(Math.round(v))} /></td>
                <td className="n"><Num dur={160} value={a.found} fmt={(v) => fn1(v) + ' / ' + c.nT} /></td>
                <td className="n"><Num dur={160} value={a.recall} fmt={(v) => v.toFixed(1) + '%'} /></td>
                <td className="n">{a.prec == null ? '–' : <Num dur={160} value={a.prec} fmt={(v) => (v < 10 ? v.toFixed(2) : v.toFixed(1)) + '%'} />}</td>
                <td className="n"><Num dur={160} value={c.dead(b)} fmt={(v) => fmt(Math.round(v))} /></td></> : <td className="n" colSpan="5">not measured below 5%</td>}
            </tr>)
        })}</tbody></table></div>
    </div>
  )
}

/* ---------------- ledger ---------------- */
const budgetCell = (b) => (b == null ? 'never' : fb(b))
function Ledger({ img }) {
  const rows = []
  IMGS.forEach((im) => curveSet(im).forEach((c, i) => {
    const a5 = c.at(5), a15 = c.at(15)
    rows.push({ im, first: i === 0, c, k90: c.knee, pl: c.plateau, dead15: c.dead(15), fa5: a5.fa, fa15: a15.fa, pr15: a15.prec })
  }))
  return (
    <div className="tbl ledger"><table>
      <thead><tr><th>Disk</th><th>Model</th><th className="n">Budget for 90%</th><th className="n">Budget for last evidence</th><th className="n">Dead reads at 15%</th><th className="n">False alarms at 5%</th><th className="n">False alarms at 15%</th><th className="n">Precision at 15%</th></tr></thead>
      <tbody>{rows.map((r) => (
        <tr key={r.im + r.c.cfg.id} className={(r.first ? 'grp' : '') + (r.im === img ? ' cur' : '')}>
          <td>{r.first ? imgName(r.im) : ''}</td>
          <td><i className="key" style={{ background: 'var(' + r.c.cfg.v + ')' }}></i>{r.c.cfg.lab}</td>
          <td className="n">{budgetCell(r.k90)}</td>
          <td className="n">{r.pl.partial ? 'tops out at ' + fn1(r.pl.fm) + '%' : fb(r.pl.b)}</td>
          <td className="n">{r.dead15 > 0 ? fmt(Math.round(r.dead15)) : 'none'}</td>
          <td className="n">{fmt(Math.round(r.fa5))}</td>
          <td className="n">{fmt(Math.round(r.fa15))}</td>
          <td className="n">{r.pr15 == null ? '–' : r.pr15.toFixed(2) + '%'}</td>
        </tr>))}</tbody></table></div>
  )
}

/* ---------------- the exhibit ---------------- */
export default function Plateau({ img, m, pct }) {
  const [log, setLog] = useState(false)
  const [all, setAll] = useState(false)
  const [hov, setHov] = useState(null)
  const body = useRef()
  const hasSw = img !== 'img1'
  const sel = curve(img, CFGS[m].id)
  const budget = pct * 100
  useDraw(body, [img, log, all])
  const hb = hov ? hov.b : budget, hImg = hov ? hov.img : img

  const stop = sel.plateau.b >= 99.5 ? null : sel.plateau.b
  const modelWords = ['Isolation Forest on 23 features', 'LOF on 23 features', 'One-Class SVM on 23 features'][m]
  const take = sel.plateau.partial
    ? modelWords + ' never finds every target on ' + imgName(img) + ': it tops out at ' + fn1(sel.plateau.fm) + '% recall, and the rest of the disk adds only false alarms.'
    : stop == null || sel.plateau.b >= 90
      ? modelWords + ' finds its last evidence only at ' + fb(sel.plateau.b) + ' on ' + imgName(img) + '. Nothing short of reading nearly the whole disk completes the set.'
      : modelWords + ' stops finding new evidence at ' + fb(sel.plateau.b) + ' on ' + imgName(img) + '; reading the other ' + fb(100 - sel.plateau.b) + ' of the disk adds only ' + fmt(Math.round(sel.at(100).fa - sel.at(sel.plateau.b).fa)) + ' false alarms.'
  const deadAt = sel.dead(budget), kAt = sel.at(budget)
  const deadSentence = budget <= sel.plateau.b
    ? 'At your ' + fb(budget) + ' budget, ' + sel.cfg.name + ' is still finding evidence: its last target turns up at ' + fb(sel.plateau.b) + '.'
    : 'At your ' + fb(budget) + ' budget, ' + fmt(Math.round(deadAt)) + ' of the ' + fmt(Math.round(kAt.K)) + ' files ' + sel.cfg.name + ' reads come after its last evidence was found.'

  const f1cap = hasSw
    ? ' Below 5% the lines are the exact full-disk ranks of one run (seed 42); from 5% up they are the mean of 5 seeds in 3 randomizations, with a band of one standard deviation, joined at the dotted rule. The sweep drops 10% of ordinary files at random, so file counts above 5% are those of the thinned disk.'
    : ' Image 1 was not part of the randomized sweep, so every line here is the exact rank curve of one run (seed 42).'
  const imgs = all ? IMGS : [img]

  return (
    <Section id="plateau" letter="C" title="How much reading until nothing new turns up?">
      <Pr note={<><b>{take}</b></>}>
        <p>Recall always rises with the review budget, but it does not rise forever. Past some point the last piece of evidence has been found and every further file is a false alarm. The figures below follow the budget out to 100% of the disk to show where that point sits for each model, and what reading beyond it costs.</p>
      </Pr>
      <div className="fgctl">
        <div className="fld"><span className="lab">Horizontal axis</span>
          <Seg label="Horizontal axis" items={['Linear, 0 to 100%', 'Log, 0.1 to 100%']} value={log ? 1 : 0} onPick={(i) => setLog(i === 1)} /></div>
        <div className="fld"><span className="lab">Figure 1 shows</span>
          <Seg label="Disks shown in Figure 1" items={['This disk', 'All three disks']} value={all ? 1 : 0} onPick={(i) => setAll(i === 1)} /></div>
      </div>
      <div ref={body}>
        <Fig n="1" name={'recall-' + (all ? 'all' : img)} caption={<>Evidence recall against review budget from 0 to 100% of files, {all ? 'one panel per disk' : imgName(img)}. Dots mark the first budget that reaches 90% recall; rings mark the plateau, the first budget at which a line reaches its final maximum. The shaded area to the right of each ring is that model’s dead zone. The dashed line is the original 17-feature Isolation Forest.{f1cap}</>}>
          <div className={all ? 'fgrid' : ''}>
            {imgs.map((im) => <RecallPanel key={im} img={im} log={log} pct={pct} m={m} hov={hov} setHov={setHov} compact={all} narrowHead={all} />)}
          </div>
        </Fig>
        <Readout img={hImg} b={hb} hovering={!!hov} />
        <Pr><p className="deadline">{deadSentence}</p></Pr>
        <Fig n="2" name={'false-alarms-' + img} caption={<>(a) Files read that are not evidence, on a log axis, and (b) precision, the share of files read that are evidence. For {imgName(img)}{hasSw ? ' these are file counts from the sweep above 5% (precision times files read gives the evidence found) and files read minus targets found below 5%' : ' they are files read minus targets found, from the exact ranks'}. Rings mark each model’s plateau. A straight rise on this scale is steady growth: false alarms keep growing with the budget while recall stays flat.</>}>
          <div className="fgrid two">
            <ErrPanel img={img} log={log} pct={pct} hov={hov} kind="fa" title="Files read that are not evidence" />
            <ErrPanel img={img} log={log} pct={pct} hov={hov} kind="pr" title="Precision" />
          </div>
        </Fig>
        <Fig n="3" name={'yield-' + img} caption={<>New evidence files found for each extra 2% of budget on {imgName(img)}, one strip per model on a shared vertical scale. Every bar to the right of “plateau begins” is empty: past that point the budget buys nothing. Bars taller than the scale are cut at the top and labelled with their value. The horizontal axis is linear in this figure.</>}>
          <YieldFig img={img} pct={pct} />
        </Fig>
      </div>
      <div className="ledgerwrap">
        <h3 className="cap">Where each model stops finding evidence</h3>
        <Ledger img={img} />
        <Pr><p className="small" style={{ marginTop: 10 }}>Dead reads are the files read after a model’s last evidence was found. False alarms are files read that are not evidence. Image 1 rows use the exact ranks of one run; Images 2 and 3 use sweep means from 5% upward.</p></Pr>
      </div>
    </Section>
  )
}
