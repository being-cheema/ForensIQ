import { useRef } from 'react'
import { useBox } from './Plateau'

/* Grouped horizontal bars as an SVG, for the exhibits' figures.
   groups: [{ label, rows: [{ label, v, text, color, hi }] }]. v is on a 0..max scale. ref draws a dashed line at that value. */
export default function HBars({ groups, max = 100, unit = '%', refAt, refLabel, ticks, aria, labW }) {
  const box = useRef(), w = useBox(box)
  const L = labW || (w < 520 ? 104 : 168), R = w < 520 ? 70 : 96, T = 20, PITCH = 21, GH = 22, GG = 10, B = 30
  const nrows = groups.reduce((a, g) => a + g.rows.length, 0)
  const H = T + groups.length * (GH + GG) + nrows * PITCH + B
  const pw = Math.max(60, w - L - R), X = (v) => L + (v / max) * pw
  const tk = ticks || [0, 25, 50, 75, 100].map((t) => t / 100 * max)
  return (
    <div ref={box} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img" aria-label={aria}>
          {tk.map((v) => <line key={v} className="gl" x1={X(v)} x2={X(v)} y1={T - 4} y2={H - B} />)}
          {refAt != null ? <g><line className="ref" x1={X(refAt)} x2={X(refAt)} y1={T - 8} y2={H - B} />{refLabel ? <text className="hi" x={X(refAt)} y={T - 10} textAnchor="middle">{refLabel}</text> : null}</g> : null}
          {groups.map((g, gi) => {
            const before = groups.slice(0, gi).reduce((a, q) => a + GH + q.rows.length * PITCH + GG, 0)
            const y0 = T + before, rows = g.rows.map((r, ri) => ({ r, yy: y0 + GH + ri * PITCH }))
            return (
              <g key={gi}>
                {g.label ? <text className="lbl" x={0} y={y0 + 12} style={{ fill: 'var(--ink)', fontWeight: 600 }}>{g.label}</text> : null}
                {rows.map(({ r, yy }, ri) => (
                  <g key={ri}>
                    <text x={L - 8} y={yy + PITCH / 2 + 4} textAnchor="end" >{r.label}</text>
                    <rect x={L} y={yy + 3} width={Math.max(1.5, X(Math.min(max, Math.max(0, r.v))) - L)} height={PITCH - 6} fill={r.color} opacity={r.dim ? 0.35 : 0.92} stroke={r.hi ? 'var(--accent)' : 'none'} strokeWidth={r.hi ? 2 : 0} />
                    <text className="bv" x={X(Math.min(max, Math.max(0, r.v))) + 6} y={yy + PITCH / 2 + 4}>{r.text}</text>
                    <title>{(g.label ? g.label + ', ' : '') + r.label + ': ' + r.text}</title>
                  </g>
                ))}
              </g>
            )
          })}
          <line className="ax" x1={L} x2={L} y1={T - 4} y2={H - B} />
          {tk.map((v) => <text key={v} x={X(v)} y={H - B + 14} textAnchor="middle">{Math.round(v * 10) / 10}</text>)}
          <text className="axt" x={L + pw / 2} y={H - 4} textAnchor="middle">{unit}</text>
        </svg>
      ) : null}
    </div>
  )
}
