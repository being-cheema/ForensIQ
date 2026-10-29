import { useEffect, useMemo, useRef, useState } from 'react'
import { IMGS, MVAR, MODELS, fmt } from '../lib/data'
import { useDraw } from '../lib/hooks'
import { useTrustAll } from '../lib/trust'
import Section from '../lib/Section'
import Seg from '../lib/Seg'
import { Pr, Flag } from '../lib/Prose'
import { Fig, useBox, imgName } from './Plateau'

const MS = ['IF', 'LOF', 'OC-SVM']
const LONG = ['Isolation Forest', 'LOF', 'One-Class SVM']
const pfmt = (p) => (p == null ? 'n/a' : p < 1e-3 ? p.toExponential(1) : p.toFixed(3))
const f2 = (x) => (x == null ? '–' : x.toFixed(2))
const span = (a, f) => { const lo = Math.min.apply(null, a), hi = Math.max.apply(null, a); return f(lo) === f(hi) ? f(lo) : f(lo) + '–' + f(hi) }
const sgn = (v) => (v < 0 ? '−' + fmt(Math.round(-v)) : fmt(Math.round(v)))

/* the deletion test passes when removing the top-3 SHAP features drops the file further than random features do, significantly, and in the right direction */
const passes = (f) => !!f && f.medianRankChangeShapTop3 > 0 && f.wilcoxonP != null && f.wilcoxonP < 0.05 && f.medianRankChangeShapTop3 > f.medianRankChangeRandom3
const ratio = (f) => (f && f.medianRankChangeRandom3 > 0 && f.medianRankChangeShapTop3 > 0 ? f.medianRankChangeShapTop3 / f.medianRankChangeRandom3 : null)

/* ---------------- shared row layout: three disks, three models each ---------------- */
function useRows(T, GH, PITCH, GAP) {
  return useMemo(() => IMGS.map((t, ti) => ({ t, y0: T + ti * (GH + 3 * PITCH + GAP) })), [T, GH, PITCH, GAP])
}

/* ---------------- Figure: faithfulness, log scale ---------------- */
function FaithFig({ all, img, m }) {
  const boxr = useRef(), w = useBox(boxr)
  const narrow = w < 520
  const L = narrow ? 56 : 84, R = narrow ? 104 : 140, T = 30, GH = 20, PITCH = 24, GAP = 10, B = 44
  const H = T + IMGS.length * (GH + 3 * PITCH + GAP) - GAP + B
  const pw = Math.max(60, w - L - R)
  const grp = useRows(T, GH, PITCH, GAP)
  let mx = 1
  IMGS.forEach((t) => MODELS.forEach((mo) => { const f = all[t].xai.faithfulness[mo]; mx = Math.max(mx, f.medianRankChangeShapTop3, f.medianRankChangeRandom3) }))
  const hiE = Math.log10(mx) + 0.15
  const X = (v) => L + (Math.log10(Math.max(1, v)) / hiE) * pw
  const ticks = []; for (let e = 0; e <= Math.floor(hiE); e++) ticks.push(Math.pow(10, e))
  const tl = (v) => (v >= 1e6 ? v / 1e6 + 'M' : v >= 1e3 ? v / 1e3 + 'k' : String(v))
  const yB = H - B
  return (
    <div ref={boxr} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Median places a file falls down the ranking when its top-3 SHAP features are removed, against three random features, per disk and model: ' +
            IMGS.map((t) => imgName(t) + ': ' + MODELS.map((mo, i) => { const f = all[t].xai.faithfulness[mo]; return MS[i] + ' ' + sgn(f.medianRankChangeShapTop3) + ' against ' + sgn(f.medianRankChangeRandom3) }).join(', ')).join('; ')}>
          {ticks.map((v) => <g key={v}><line className="gl" x1={X(v)} x2={X(v)} y1={T - 4} y2={yB} /><text x={X(v)} y={yB + 14} textAnchor="middle">{tl(v)}</text></g>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">median places the file falls down the ranking (log scale)</text>
          <g transform={'translate(' + L + ' 10)'}>
            <circle cx="5" cy="0" r="4.2" fill="var(--ink)" /><text x="14" y="4">top-3 SHAP features removed</text>
            <circle cx={narrow ? 5 : 188} cy={narrow ? 14 : 0} r="4" fill="var(--paper)" stroke="var(--ink2)" strokeWidth="1.6" /><text x={narrow ? 14 : 197} y={narrow ? 18 : 4}>3 random features removed</text>
          </g>
          {grp.map(({ t, y0 }) => (
            <g key={t}>
              {t === img ? <rect x="0" y={y0 - 2} width={w} height={GH + 3 * PITCH} fill="var(--accent)" opacity=".06" /> : null}
              <text className="lbl" x="0" y={y0 + 12} style={{ fill: 'var(--ink)' }}>{imgName(t)}</text>
              {MODELS.map((mo, mi) => {
                const f = all[t].xai.faithfulness[mo], y = y0 + GH + mi * PITCH + PITCH / 2, a = f.medianRankChangeShapTop3, b = f.medianRankChangeRandom3
                const ok = passes(f), r = ratio(f), col = 'var(' + MVAR[mi] + ')', sel = t === img && mi === m
                const ax = X(a), bx = X(b)
                return (
                  <g key={mo}>
                    <text x={L - 8} y={y + 4} textAnchor="end" style={{ fill: col, fontWeight: sel ? 700 : 600 }}>{MS[mi]}</text>
                    <line x1={Math.min(ax, bx)} x2={Math.max(ax, bx)} y1={y} y2={y} stroke={ok ? col : 'var(--ink2)'} strokeWidth={ok ? 2 : 1.2} strokeDasharray={ok ? undefined : '3 3'} data-dash={ok ? undefined : '3 3'} className="draw" />
                    <circle className="fadein" data-op="1" cx={bx} cy={y} r="4" fill="var(--paper)" stroke="var(--ink2)" strokeWidth="1.6" />
                    <circle className="fadein" data-op="1" cx={ax} cy={y} r={sel ? 5.4 : 4.4} fill={col} stroke={ok ? 'var(--paper)' : 'var(--accent)'} strokeWidth={ok ? 1.2 : 1.8} />
                    {a <= 0 || b <= 0 ? <text className="bv" x={Math.max(ax, bx) + 10} y={y + 4}>{(a <= 0 ? 'top-3 ' + sgn(a) : '') + (a <= 0 && b <= 0 ? ', ' : '') + (b <= 0 ? 'random ' + sgn(b) : '')}</text> : null}
                    <text className="bv" x={L + pw + 10} y={y + 4} style={{ fill: ok ? 'var(--ink)' : 'var(--accent-ink)' }}><tspan style={{ fontWeight: 700 }}>{ok ? (r ? '×' + (r < 10 ? r.toFixed(1) : Math.round(r)) : 'pass') : 'fails'}</tspan><tspan style={{ fill: 'var(--ink2)' }}> p {narrow ? (f.wilcoxonP == null ? 'n/a' : f.wilcoxonP < 1e-3 ? f.wilcoxonP.toExponential(0) : f.wilcoxonP.toFixed(2)) : pfmt(f.wilcoxonP)}</tspan></text>
                    <title>{LONG[mi] + ', ' + imgName(t) + ': top-3 SHAP removal moves the file ' + sgn(a) + ' places (median), random removal ' + sgn(b) + '; Wilcoxon p = ' + pfmt(f.wilcoxonP) + ', n = ' + f.n}</title>
                  </g>)
              })}
            </g>))}
          <line className="ax" x1={L} x2={L} y1={T - 4} y2={yB} />
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- Figure: stability across seeds ---------------- */
function StabFig({ all, img, m }) {
  const boxr = useRef(), w = useBox(boxr)
  const narrow = w < 520
  const L = narrow ? 56 : 84, R = 48, T = 30, GH = 20, PITCH = 30, GAP = 10, B = 40
  const H = T + IMGS.length * (GH + 3 * PITCH + GAP) - GAP + B
  const pw = Math.max(60, w - L - R), X = (v) => L + v * pw
  const grp = useRows(T, GH, PITCH, GAP)
  const yB = H - B
  return (
    <div ref={boxr} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Agreement of the top-3 reasons across five seeds, per disk and model: ' +
            IMGS.map((t) => imgName(t) + ': ' + MODELS.map((mo, i) => { const s = all[t].xai.stability[mo]; return MS[i] + ' Jaccard ' + f2(s.meanJaccardTop3) + ', top-1 agreement ' + f2(s.top1AgreementPairwise) }).join(', ')).join('; ')}>
          {[0, 0.25, 0.5, 0.75, 1].map((v) => <g key={v}><line className="gl" x1={X(v)} x2={X(v)} y1={T - 4} y2={yB} /><text x={X(v)} y={yB + 14} textAnchor="middle">{v}</text></g>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">agreement across 5 seeds (1 = identical every time)</text>
          <g transform={'translate(' + L + ' 10)'}>
            <rect x="0" y="-4" width="14" height="8" fill="var(--ink)" /><text x="20" y="4">Jaccard of the top-3 reasons</text>
            <rect x={narrow ? 0 : 196} y={narrow ? 10 : -4} width="14" height="8" fill="var(--ink)" opacity=".38" /><text x={narrow ? 20 : 216} y={narrow ? 18 : 4}>same top-1 reason (pairs of seeds)</text>
          </g>
          {grp.map(({ t, y0 }) => (
            <g key={t}>
              {t === img ? <rect x="0" y={y0 - 2} width={w} height={GH + 3 * PITCH} fill="var(--accent)" opacity=".06" /> : null}
              <text className="lbl" x="0" y={y0 + 12} style={{ fill: 'var(--ink)' }}>{imgName(t)}</text>
              {MODELS.map((mo, mi) => {
                const s = all[t].xai.stability[mo], y = y0 + GH + mi * PITCH + 4, col = 'var(' + MVAR[mi] + ')', sel = t === img && mi === m
                return (
                  <g key={mo}>
                    <text x={L - 8} y={y + 14} textAnchor="end" style={{ fill: col, fontWeight: sel ? 700 : 600 }}>{MS[mi]}</text>
                    <rect x={L} y={y} width={Math.max(1, s.meanJaccardTop3 * pw)} height="10" fill={col} className="fadein" data-op="1" />
                    <text className="bv" x={L + s.meanJaccardTop3 * pw + 5} y={y + 9}>{f2(s.meanJaccardTop3)}</text>
                    <rect x={L} y={y + 12} width={Math.max(1, s.top1AgreementPairwise * pw)} height="10" fill={col} opacity=".38" className="fadein" data-op=".38" />
                    <text className="bv" x={L + s.top1AgreementPairwise * pw + 5} y={y + 21}>{f2(s.top1AgreementPairwise)}</text>
                    <title>{LONG[mi] + ', ' + imgName(t) + ': Jaccard ' + f2(s.meanJaccardTop3) + ', top-1 pairwise ' + f2(s.top1AgreementPairwise) + ', top-1 identical in all 5 seeds ' + f2(s.top1AllSeedsSame) + ' (n = ' + s.n + ' targets)'}</title>
                  </g>)
              })}
            </g>))}
          <line className="ax" x1={L} x2={L} y1={T - 4} y2={yB} />
        </svg>
      ) : null}
    </div>
  )
}

/* ---------------- the exhibit ---------------- */
export default function TrustXai({ img, m }) {
  const { all, err } = useTrustAll()
  const [sf, setSf] = useState(m + 1)
  const body = useRef()
  useEffect(() => { setSf(m + 1) }, [m])
  useDraw(body, [img, !!all])

  const S = useMemo(() => {
    if (!all) return null
    const per = (mo) => IMGS.map((t) => ({ t, f: all[t].xai.faithfulness[mo], s: all[t].xai.stability[mo], u: all[t].xai.summary[mo] }))
    const o = {}
    MODELS.forEach((mo) => {
      const p = per(mo)
      const rs = p.map((x) => ratio(x.f)).filter((v) => v != null)
      const sense = IMGS.reduce((a, t) => a.concat(all[t].xai.sense.filter((x) => x.model === mo)), [])
      o[mo] = { p, pass: p.filter((x) => passes(x.f)).length, rs, jac: p.map((x) => x.s.meanJaccardTop3), t1: p.map((x) => x.s.top1AgreementPairwise), t1all: p.map((x) => x.s.top1AllSeedsSame),
        sense: p.map((x) => x.u.senseMatch), senseAll: sense.length ? sense.filter((x) => x.match).length / sense.length : null, senseN: sense.length, nonpos: p.filter((x) => x.f.medianRankChangeShapTop3 <= 0).length }
    })
    let cm = 0, nm = 0
    IMGS.forEach((t) => MODELS.forEach((mo) => { cm = Math.max(cm, all[t].xai.summary[mo].shapMassConstant); nm = Math.max(nm, all[t].xai.summary[mo].shapMassNearConstant) }))
    const notes = all[IMGS[0]].xai.notes.kernelCaps || '', mm = /<=\s*(\d+) caught targets and (\d+)/.exec(notes)
    const st = all[IMGS[0]].xai.stability[MODELS[2]].nsamples || '', sm = /nsamples=(\d+).*<=\s*(\d+) targets/.exec(st)
    const im = /IF: all caught targets \+ (\d+)/.exec(notes)
    return { o, cm, nm, caps: mm ? { t: mm[1], n: mm[2] } : null, stab: sm ? { ns: sm[1], t: sm[2] } : null, ifNon: im ? im[1] : null }
  }, [all])

  if (!all || !S) {
    return (
      <Section id="trust" letter="F" title="Can you trust the explanation?">
        <Pr><p>Each flagged file comes with a reason: the features that pushed it up the list. This exhibit tests whether those reasons can be believed.</p></Pr>
        {err ? <p className="small">The explanation data could not be loaded.</p> : <p className="lab-load">Loading the explanation checks for the three disks…</p>}
      </Section>
    )
  }

  const d = all[img], mo = MODELS[m], f = d.xai.faithfulness[mo], s = d.xai.stability[mo]
  const stabTxt = (x) => (x >= 0.7 ? 'stable' : x >= 0.6 ? 'less stable' : 'unstable')
  const O = S.o
  const IFo = O[MODELS[0]], LOo = O[MODELS[1]], OCo = O[MODELS[2]]
  const capsTxt = S.caps ? 'KernelSHAP was run on ' + S.caps.t + ' caught targets and ' + S.caps.n + ' flagged non-targets per disk' : 'KernelSHAP was run on a capped sample'
  const stabCap = S.stab ? 'The KernelSHAP stability runs used ' + S.stab.t + ' targets with nsamples=' + S.stab.ns + '.' : 'The KernelSHAP stability runs used a capped number of targets.'
  const sense = d.xai.sense.filter((x) => sf === 0 || x.model === MODELS[sf - 1]).slice().sort((a, b) => MODELS.indexOf(a.model) - MODELS.indexOf(b.model) || a.rank - b.rank)
  const share = (arr) => (arr.length ? Math.round(arr.filter((x) => x.match).length / arr.length * 100) + '%' : '–')

  const note = (
    <>
      <b>Isolation Forest’s explanations can be trusted.</b> They are faithful on {IFo.pass} of 3 disks (removing the top-3 features moves the file {span(IFo.rs, (x) => Math.round(x))} times as far as random ones), stable (Jaccard {span(IFo.jac, f2)}) and forensically sensible ({span(IFo.sense, (x) => Math.round(x * 100) + '%')} match what an examiner expects).{' '}
      <b>One-Class SVM’s are faithful but less stable.</b> They pass on {OCo.pass} of 3 disks, by {span(OCo.rs, (x) => Math.round(x * 10) / 10)} times, but their Jaccard is {span(OCo.jac, f2)}. KernelSHAP is an approximation, and it ran on a capped sample.{' '}
      <b>LOF’s should not be trusted.</b> It fails the deletion test on {3 - LOo.pass} of 3 disks and its top reason agrees across seeds {span(LOo.t1all, (x) => Math.round(x * 100) + '%')} of the time. Its reasons often look plausible ({span(LOo.sense, (x) => Math.round(x * 100) + '%')} match), which is not the same as being faithful.
    </>
  )

  return (
    <Section id="trust" letter="F" title="Can you trust the explanation?">
      <Pr note={<>Across all three disks and all three models, {S.cm === 0 ? 'none of the explanation weight lands on features that never vary' : 'at most ' + (S.cm * 100).toFixed(2) + '% of the explanation weight lands on features that never vary'}.</>}>
        <p>Every flagged file comes with a reason: the features that pushed it up the list. A reason is only useful if it is faithful (the model really does lean on those features), stable (it does not change when the model is refit) and sensible (it points at something an examiner would expect). The three checks below test each in turn. The disk, model and a 20% budget follow the controls above; the figures show all nine combinations with yours highlighted.</p>
      </Pr>

      <div ref={body}>
        <h3 className="rel-h"><span>1</span>Faithful: does removing the named features change the ranking?</h3>
        <Pr><p>For each file, replace its top-3 SHAP features with the disk average and see how far it falls down the ranking. Do the same for 3 random features. If the explanation is faithful, the named features should matter much more than random ones.</p></Pr>
        <Fig n="8" name="faithfulness" caption={<>Median number of places a file falls down the ranking when its top-3 SHAP features are removed (filled dot) against three random features (open dot), on a log axis, with the one-sided Wilcoxon signed-rank p-value for each pairing. The multiplier is the ratio of the two medians. Values at or below zero cannot sit on a log axis: they are drawn on the left edge and labelled, and a negative value means the file moved <em>up</em> the list after its “top” features were removed. {capsTxt}; the Isolation Forest test uses every caught target plus {S.ifNon || 'a sample of'} flagged non-targets.</>}>
          <FaithFig all={all} img={img} m={m} />
        </Fig>
        <Pr note={<>{LONG[2]} passes by {span(OCo.rs, (x) => Math.round(x * 10) / 10)} times and {LONG[0]} by {span(IFo.rs, (x) => Math.round(x))} times.</>}>
          <p className="deadline">{passes(f)
            ? LONG[m] + ' on ' + imgName(img) + ': removing the top-3 features drops a file ' + fmt(Math.round(f.medianRankChangeShapTop3)) + ' places, against ' + fmt(Math.round(f.medianRankChangeRandom3)) + ' for random ones (p = ' + pfmt(f.wilcoxonP) + ', n = ' + f.n + '). The explanation is faithful.'
            : LONG[m] + ' on ' + imgName(img) + ' fails: removing the top-3 features ' + (f.medianRankChangeShapTop3 < 0 ? 'lifts the median file ' + fmt(Math.round(-f.medianRankChangeShapTop3)) + ' places up the list' : f.medianRankChangeShapTop3 === 0 ? 'does not move the median file' : 'drops the median file only ' + fmt(Math.round(f.medianRankChangeShapTop3)) + ' places') + ', against ' + sgn(f.medianRankChangeRandom3) + ' for random ones' + (f.medianRankChangeShapTop3 <= 0 ? ', so the file does not look more normal without the features it was said to depend on' : '') + '. The explanation is no better than random.'}</p>
        </Pr>
        {LOo.nonpos > 0 ? <Pr><p>LOF fails this test. On {LOo.nonpos} of 3 disks the median file does not fall at all after its top-3 features are removed{LOo.p.some((x) => !passes(x.f) && x.f.wilcoxonP != null && x.f.wilcoxonP < 0.05) ? '; where a paired p-value does dip below 0.05 (' + LOo.p.filter((x) => !passes(x.f) && x.f.wilcoxonP != null && x.f.wilcoxonP < 0.05).map((x) => imgName(x.t)).join(', ') + '), both medians are still below zero, so it is not evidence of faithfulness' : ''}.</p></Pr> : null}

        <h3 className="rel-h"><span>2</span>Stable: do five refits give the same reason?</h3>
        <Pr><p>The model was refit with 5 seeds and each caught target was explained again. Jaccard is the overlap between the top-3 reasons of two seeds (1 means identical sets); top-1 agreement is how often two seeds name the same strongest reason.</p></Pr>
        <Fig n="9" name="stability" caption={<>Agreement of the explanation across 5 seeds for the caught targets. The dark bar is the mean pairwise Jaccard of the top-3 reasons; the pale bar is the share of seed pairs that name the same top reason. Isolation Forest uses exact TreeSHAP; the other two use KernelSHAP, which is sampled, so part of their instability is the approximation itself. {stabCap}</>}>
          <StabFig all={all} img={img} m={m} />
        </Fig>
        <Pr>
          <p className="deadline">{LONG[m]} on {imgName(img)}: Jaccard {f2(s.meanJaccardTop3)}, same top reason in {Math.round(s.top1AgreementPairwise * 100)}% of seed pairs and in all five seeds for {Math.round(s.top1AllSeedsSame * 100)}% of targets ({s.n} targets). That is {stabTxt(s.meanJaccardTop3)}.</p>
        </Pr>

        <div className="tbl ledger"><table>
          <thead><tr><th>Disk</th><th>Model</th><th className="n">Files tested</th><th className="n">Median drop, SHAP top-3</th><th className="n">Median drop, random 3</th><th className="n">Ratio</th><th className="n">Wilcoxon p</th><th>Faithful?</th><th className="n">Jaccard</th><th className="n">Top-1, pairs</th><th className="n">Top-1, all seeds</th></tr></thead>
          <tbody>{IMGS.map((t) => MODELS.map((mm, mi) => {
            const ff = all[t].xai.faithfulness[mm], ss = all[t].xai.stability[mm], r = ratio(ff)
            return (
              <tr key={t + mm} className={(mi === 0 ? 'grp' : '') + (t === img ? ' cur' : '')}>
                <td>{mi === 0 ? imgName(t) : ''}</td>
                <td><i className="key" style={{ background: 'var(' + MVAR[mi] + ')' }}></i>{LONG[mi]}</td>
                <td className="n">{ff.n}</td><td className="n">{sgn(ff.medianRankChangeShapTop3)}</td><td className="n">{sgn(ff.medianRankChangeRandom3)}</td>
                <td className="n">{r ? '×' + (r < 10 ? r.toFixed(1) : Math.round(r)) : '–'}</td><td className="n">{pfmt(ff.wilcoxonP)}</td>
                <td><Flag kind={passes(ff) ? 'ok' : 'err'}>{passes(ff) ? 'yes' : 'no'}</Flag></td>
                <td className="n">{f2(ss.meanJaccardTop3)}</td><td className="n">{f2(ss.top1AgreementPairwise)}</td><td className="n">{f2(ss.top1AllSeedsSame)}</td>
              </tr>)
          }))}</tbody></table></div>

        <h3 className="rel-h"><span>3</span>Sensible: do the reasons match what an examiner expects?</h3>
        <Pr note={<>A match means at least one of a target’s top-3 reasons is in the list of features that should explain a file of that kind. The expected lists were written by hand, so this is a plausibility check, not a proof.</>}>
          <p>For every caught target on {imgName(img)} the table gives the model’s top-3 reasons, the features a forensic examiner would expect for that kind of file, and whether they overlap. Reasons that are in the expected set are underlined.</p>
        </Pr>
        <div className="sensebar">
          <div className="fld"><span className="lab">Model</span>
            <Seg label="Filter the table by model" items={['All', 'IF', 'LOF', 'OC-SVM']} value={sf} onPick={setSf} /></div>
          <ul className="sshare">{MODELS.map((mm, mi) => {
            const mine = d.xai.sense.filter((x) => x.model === mm)
            return <li key={mm} className={mi === sf - 1 ? 'on' : ''}><i className="key" style={{ background: 'var(' + MVAR[mi] + ')' }}></i><b>{MS[mi]}</b> {mine.filter((x) => x.match).length}/{mine.length} match · {share(mine)}<small> all disks {O[mm].senseAll != null ? Math.round(O[mm].senseAll * 100) + '%' : '–'}</small></li>
          })}</ul>
        </div>
        <div className="tbl ledger sense-tbl"><table>
          <thead><tr><th>Caught target</th><th>Model</th><th className="n">Rank</th><th>Top-3 reasons</th><th>Expected reasons</th><th>Match</th></tr></thead>
          <tbody>{sense.map((x) => {
            const mi = MODELS.indexOf(x.model), ex = new Set(x.expected)
            return (
              <tr key={x.model + x.target}>
                <td className="sn">{x.target}</td>
                <td><i className="key" style={{ background: 'var(' + MVAR[mi] + ')' }}></i>{MS[mi]}</td>
                <td className="n">{fmt(x.rank)}</td>
                <td className="rsns">{x.top3.map((r) => <span key={r} className={'rsn' + (ex.has(r) ? ' hit' : '')}>{r}</span>)}</td>
                <td className="small exp">{x.expected.length ? x.expected.join(', ') : 'none defined'}</td>
                <td><Flag kind={x.match ? 'ok' : 'err'}>{x.match ? 'match' : 'no match'}</Flag></td>
              </tr>)
          })}</tbody></table></div>

        <Pr>
          <p className="trust-const" style={{ marginTop: 18 }}>Share of explanation weight on features that never vary: <b className="mono">{S.cm.toFixed(4)}</b> on every disk and model (the largest value over all nine combinations). On features that are almost constant it is at most <span className="mono">{S.nm.toFixed(4)}</span>.</p>
        </Pr>
        <Pr note={note}>
          <p>So the tool’s reasons are worth reading when the model is Isolation Forest, worth reading with care for One-Class SVM, and not worth reading for LOF. {capsTxt}, and the stability runs used {S.stab ? S.stab.t : 'a capped number of'} targets, so the weaker models’ numbers rest on fewer files than Isolation Forest’s.</p>
        </Pr>
      </div>
    </Section>
  )
}
