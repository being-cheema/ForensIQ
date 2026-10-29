import { Fragment, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { MODELS, SHORT, fmt } from '../lib/data'
import { AN, canAnim, EASE } from '../lib/motion'
import { useOnceInView, useGrow } from '../lib/hooks'
import { useTrust } from '../lib/trust'
import Section from '../lib/Section'
import { Pr, Flag, Tag } from '../lib/Prose'
import { Fig, useBox, imgName } from './Plateau'

const BUDGETS = [5, 10, 15, 20]
const MS = ['IF', 'LOF', 'OC-SVM']
const snap = (pct) => BUDGETS.reduce((a, b) => (Math.abs(b - pct * 100) < Math.abs(a - pct * 100) ? b : a), BUDGETS[0])
const fb1 = (x) => (Math.round(x * 10) / 10).toString()
const bnote = (b) => (b === 5 ? 'strict comparison' : b === 15 ? 'recommended' : '')
const bl = (b) => b + '%' + (bnote(b) ? ' (' + bnote(b) + ')' : '')
const pr1 = (x) => (x * 100).toFixed(1) + '%'
const span = (a, f) => { const lo = Math.min.apply(null, a), hi = Math.max.apply(null, a); return f(lo) === f(hi) ? f(lo) : f(lo) + '–' + f(hi) }
const pfmt = (p) => (p == null ? 'n/a' : p < 1e-3 ? p.toExponential(1) : p.toFixed(3))
export const CAT_LABEL = { 'system-noise': 'system noise', log: 'log', registry: 'registry', 'user-document': 'user document', executable: 'executable', 'prefetch-or-lnk': 'prefetch / lnk', browser: 'browser', other: 'other' }

const ROW = 30, HDR = 30, VH = 440

/* ---------------- ranked list: windowed, only the visible rows are in the DOM ---------------- */
function RankList({ tool, K, resetKey }) {
  const box = useRef(), jt = useRef(0), busy = useRef(false), anim = useRef({ v: 0 }), jumped = useRef(-1), flashT = useRef(0)
  const [evOnly, setEvOnly] = useState(false)
  const [noNoise, setNoNoise] = useState(false)
  const [q, setQ] = useState('')
  const [st, setSt] = useState(0)
  const [flash, setFlash] = useState(null)
  const [msg, setMsg] = useState('')
  const raf = useRef(0)

  const cap = Math.min(K, tool.rows.length)
  const base = useMemo(() => tool.rows.slice(0, cap), [tool, cap])
  const rows = useMemo(() => {
    const s = q.trim().toLowerCase()
    return base.filter((r) => (!evOnly || r[3]) && (!noNoise || r[5] !== 'system-noise') &&
      (!s || r[2].toLowerCase().indexOf(s) >= 0 || r[3].toLowerCase().indexOf(s) >= 0 || (r[4] || '').indexOf(s) >= 0 || r[5].indexOf(s) >= 0 || CAT_LABEL[r[5]].indexOf(s) >= 0))
  }, [base, evOnly, noNoise, q])
  const evIdx = useMemo(() => { const a = []; rows.forEach((r, i) => { if (r[3]) a.push(i) }); return a }, [rows])
  const withWhy = useMemo(() => (base.length ? base.filter((r) => r[4]).length / base.length : 0), [base])
  const evInBase = useMemo(() => new Set(base.filter((r) => r[3]).map((r) => r[3])).size, [base])

  useEffect(() => { if (box.current) { box.current.scrollTop = 0 } setSt(0); jumped.current = -1; setMsg('') }, [resetKey, evOnly, noNoise, q, cap])
  useEffect(() => () => { cancelAnimationFrame(raf.current); clearTimeout(flashT.current); clearTimeout(jt.current); AN.remove(anim.current) }, [])

  const onScroll = (e) => { const t = e.currentTarget.scrollTop; cancelAnimationFrame(raf.current); raf.current = requestAnimationFrame(() => setSt(t)) }
  const first = Math.max(0, Math.floor(st / ROW) - 6), last = Math.min(rows.length, Math.floor(st / ROW) + Math.ceil(VH / ROW) + 8)

  const doFlash = (rank) => {
    clearTimeout(flashT.current)
    setFlash(rank)
    flashT.current = setTimeout(() => setFlash(null), 1900)
  }
  useEffect(() => {
    if (flash == null || !canAnim()) return
    const id = requestAnimationFrame(() => {
      const el = box.current && box.current.querySelector('.rk-flash[data-r="' + flash + '"]')
      if (el) { AN.remove(el); AN({ targets: el, opacity: [0.8, 0], duration: 1500, easing: EASE }) }
    })
    return () => cancelAnimationFrame(id)
  }, [flash])

  const jump = () => {
    const el = box.current
    if (!el || !evIdx.length) { setMsg(evOnly || q || noNoise ? 'No evidence rows match the filters.' : 'No evidence rows inside this list.'); return }
    const top = Math.floor(el.scrollTop / ROW)
    const cont = jumped.current >= 0 && busy.current || jumped.current >= 0 && Math.abs(top - Math.max(0, jumped.current - 2)) <= 3
    let nx = evIdx.find((i) => (cont ? i > jumped.current : i >= top)), wrapped = false
    if (nx == null) { nx = evIdx[0]; wrapped = true }
    jumped.current = nx
    const n = evIdx.indexOf(nx) + 1
    setMsg('Evidence ' + n + ' of ' + evIdx.length + (wrapped ? ' (back at the first)' : '') + ': rank ' + fmt(rows[nx][0]))
    const to = Math.max(0, (nx - 2) * ROW), rank = rows[nx][0]
    if (!canAnim()) { el.scrollTop = to; doFlash(rank); return }
    AN.remove(anim.current)
    clearTimeout(jt.current)
    busy.current = true
    let done = false
    const fin = () => { if (done) return; done = true; busy.current = false; clearTimeout(jt.current); AN.remove(anim.current); el.scrollTop = to; doFlash(rank) }
    anim.current = { v: el.scrollTop }
    AN({ targets: anim.current, v: to, duration: 520, easing: EASE, update: () => { if (!done) el.scrollTop = anim.current.v }, complete: fin })
    jt.current = setTimeout(fin, 900)
  }

  const out = []
  for (let i = first; i < last; i++) {
    const r = rows[i], ev = !!r[3]
    out.push(
      <div key={r[0]} className={'rk-row' + (ev ? ' ev' : '')} style={{ top: i * ROW }} role="row">
        <span className="rk-c n" role="cell">{fmt(r[0])}</span>
        <span className="rk-c n" role="cell">{r[1].toFixed(3)}</span>
        <span className="rk-c" role="cell"><span className={'ctag c-' + r[5]}>{CAT_LABEL[r[5]]}</span></span>
        <span className="rk-c rk-path" role="cell" title={r[2]}>{r[2]}</span>
        <span className="rk-c rk-why" role="cell">{r[4] || '–'}</span>
        <span className="rk-c rk-evc" role="cell">{ev ? <><Tag>evidence</Tag><span className="rk-nm" title={r[3]}>{r[3]}</span></> : null}</span>
        {flash === r[0] ? <i className="rk-flash" data-r={r[0]} aria-hidden="true"></i> : null}
      </div>)
  }

  return (
    <div className="rk">
      <div className="rk-ctl">
        <label className="rk-chk"><input type="checkbox" checked={evOnly} onChange={(e) => setEvOnly(e.target.checked)} /> Evidence only</label>
        <label className="rk-chk"><input type="checkbox" checked={noNoise} onChange={(e) => setNoNoise(e.target.checked)} /> Hide system noise</label>
        <label className="rk-find"><span className="sr">Search the list</span><input type="search" placeholder="Search path, reason or category" value={q} onChange={(e) => setQ(e.target.value)} /></label>
        <button type="button" className="btn lab-btn" onClick={jump}>Jump to next evidence</button>
      </div>
      <p className="small rk-stat" aria-live="polite">{fmt(rows.length)} of {fmt(cap)} rows shown · {fmt(evIdx.length)} evidence {evIdx.length === 1 ? 'row' : 'rows'}{msg ? ' · ' + msg : ''}</p>
      <div className="rk-box" ref={box} onScroll={onScroll} tabIndex={0} role="table" aria-label={'Ranked list, ' + rows.length + ' rows'} aria-rowcount={rows.length + 1} style={{ height: VH }}>
        <div className="rk-in">
          <div className="rk-row rk-head" role="row"><span className="rk-c n" role="columnheader">Rank</span><span className="rk-c n" role="columnheader">Score</span><span className="rk-c" role="columnheader">Type</span><span className="rk-c" role="columnheader">Path</span><span className="rk-c" role="columnheader">Top reason</span><span className="rk-c" role="columnheader">Evidence</span></div>
          <div className="rk-body" style={{ height: rows.length * ROW }}>
            {out}
            {!rows.length ? <p className="rk-none">No rows match these filters.</p> : null}
          </div>
        </div>
      </div>
      <p className="small rk-note">
        {tool.rows.length < K
          ? 'This list holds the top ' + fmt(tool.rows.length) + ' ranks of the ' + fmt(K) + ' files in the budget; the rest of the budget is not listed here. '
          : ''}
        {evInBase} {evInBase === 1 ? 'target appears' : 'targets appear'} in the {fmt(cap)} rows above. The reason is the strongest single SHAP feature pushing that file up the list; {Math.round(withWhy * 100)}% of these rows have one, and a dash means no explanation was computed for that file.
      </p>
    </div>
  )
}

/* ---------------- Figure: what the top K is made of ---------------- */
function parts(s) {
  const noise = s.systemNoise, log = s.categories.log || 0, user = s.userFiles, ev = s.targetFilesInTopK
  const other = Math.max(0, s.K - noise - log - user - ev)
  return [
    { k: 'noise', lab: 'system noise', n: noise, c: 'var(--ink2)', o: 0.6 },
    { k: 'log', lab: 'logs', n: log, c: 'var(--m1)', o: 0.85 },
    { k: 'user', lab: 'user documents', n: user, c: 'var(--m0)', o: 0.95 },
    { k: 'ev', lab: 'evidence files', n: ev, c: 'var(--accent)', o: 1 },
    { k: 'other', lab: 'everything else', n: other, c: 'var(--rule)', o: 1 }
  ]
}

function MixFig({ tool, bud, loaded }) {
  const boxr = useRef(), w = useBox(boxr)
  const seen = useRef(false), timer = useRef(0)
  const L = w < 520 ? 62 : 120, R = w < 520 ? 8 : 92, T = 22, PITCH = 40, BH = 20, B = 34
  const H = T + BUDGETS.length * PITCH + B
  const pw = Math.max(60, w - L - R)
  const run = () => {
    const root = boxr.current; if (!root || !canAnim()) return
    const els = root.querySelectorAll('rect.sbr'); if (!els.length) return
    const settle = () => els.forEach((e) => e.setAttribute('width', e.dataset.w))
    clearTimeout(timer.current); AN.remove(els)
    els.forEach((e) => e.setAttribute('width', 0))
    AN({ targets: els, width: (e) => [0, +e.dataset.w], duration: 760, delay: AN.stagger(110, { start: 60 }), easing: EASE, complete: settle })
    timer.current = setTimeout(settle, 2000)
  }
  useOnceInView(boxr, () => { seen.current = true; run(); return () => { clearTimeout(timer.current); if (boxr.current) AN.remove(boxr.current.querySelectorAll('rect.sbr')) } })
  useLayoutEffect(() => { if (seen.current) run() }, [tool, w > 0, loaded])
  const legend = parts(tool.summary['15'])
  return (
    <div ref={boxr} className="fpanel">
      {w > 0 ? (
        <svg className="fgsvg" width={w} height={H} viewBox={'0 0 ' + w + ' ' + H} role="img"
          aria-label={'Composition of the top-K files at each budget: ' + BUDGETS.map((b) => { const s = tool.summary[b]; return b + '% budget, ' + pr1(s.systemNoiseShare) + ' system noise, ' + pr1(s.userShare) + ' user documents' }).join('; ')}>
          <defs>{BUDGETS.map((b, i) => <clipPath key={b} id={'mixclip' + b}><rect className="sbr" x={L} y={T + i * PITCH - 4} height={BH + 8} width={pw} data-w={pw} /></clipPath>)}</defs>
          {[0, 25, 50, 75, 100].map((v) => <g key={v}><line className="gl" x1={L + v / 100 * pw} x2={L + v / 100 * pw} y1={T - 6} y2={T + BUDGETS.length * PITCH - 12} /><text x={L + v / 100 * pw} y={H - B + 14} textAnchor="middle">{v}%</text></g>)}
          <text className="axt" x={L + pw / 2} y={H - 6} textAnchor="middle">share of the files in the top K</text>
          {BUDGETS.map((b, i) => {
            const s = tool.summary[b], P = parts(s), tot = Math.max(s.K, P.reduce((a, p) => a + p.n, 0)), y = T + i * PITCH
            let x = L
            return (
              <g key={b} className={b === bud ? 'mix-cur' : ''}>
                <text className={'lbl' + (b === bud ? ' hi' : '')} x={L - 8} y={y + 10} textAnchor="end">{b}%</text>
                {w >= 520 && bnote(b) ? <text x={L - 8} y={y + 22} textAnchor="end" fontStyle="italic">{bnote(b)}</text> : null}
                <g clipPath={'url(#mixclip' + b + ')'}>
                  {P.map((p) => {
                    const wd = p.n / tot * pw, x0 = x; x += wd
                    if (p.n <= 0) return null
                    return <rect key={p.k} x={x0} y={y} width={Math.max(p.k === 'ev' || p.k === 'user' ? 2.5 : 0, wd)} height={BH} fill={p.c} opacity={p.o}><title>{p.lab + ': ' + fmt(p.n) + ' of ' + fmt(s.K) + ' (' + pr1(p.n / s.K) + ')'}</title></rect>
                  })}
                </g>
                <rect x={L} y={y} width={pw} height={BH} fill="none" stroke="var(--ink)" strokeWidth=".8" />
                {P[0].n / tot * pw > 70 ? <text className="bv" x={L + 6} y={y + 14} style={{ fill: 'var(--paper)', stroke: 'none' }}>{pr1(s.systemNoiseShare)} noise</text> : null}
                {w >= 520 ? <text className="bv" x={L + pw + 8} y={y + 14}>K = {fmt(s.K)}</text> : null}
              </g>
            )
          })}
          <line className="ax" x1={L} x2={L} y1={T - 6} y2={T + BUDGETS.length * PITCH - 12} />
        </svg>
      ) : null}
      <ul className="mixkey">{legend.map((p) => <li key={p.k}><i style={{ background: p.c, opacity: p.o }}></i>{p.lab}</li>)}</ul>
    </div>
  )
}

/* ---------------- fair verdicts ---------------- */
const INDS = [
  { k: 'timestomp', name: 'Timestomping', what: 'Flagged files whose $STANDARD_INFORMATION creation time is more than an hour before the $FILE_NAME one.' },
  { k: 'a_wiper_executed', name: 'Wiper or cleaner', what: 'Wiping or cleaning tools (Eraser, CCleaner, sdelete and similar) as executables or prefetch records.' },
  { k: 'b_recent_doc_traces', name: 'Document traces', what: 'Shortcut and jump-list records that point to document files.' },
  { k: 'c_removable_or_cloud', name: 'Removable or cloud', what: 'USB setup logs and the sync files of cloud storage clients.' },
  { k: 'd_hacking_tools', name: 'Hacking tools', what: 'Names of well-known attack or sniffing tools.' }
]

function Verdicts({ d, mo, bud, img }) {
  const v = d.verdicts.perModel[mo][bud], ev = d.verdicts.evaluation[mo][bud]
  const [open, setOpen] = useState({})
  const enr = useRef()
  const ts = v.timestomp
  useGrow(enr, [img, mo, bud])
  const tog = (k) => setOpen((o) => Object.assign({}, o, { [k]: !o[k] }))
  const get = (k) => (k === 'timestomp' ? ts : v.indicators[k])
  const fired = (k) => (k === 'timestomp' ? ts.indicated : v.indicators[k].fired)
  const lowEnr = ts.enrichment != null && ts.enrichment < 1
  const tsReliable = ts.enrichment != null && ts.enrichment >= 1
  const thr = (/enrichment >= ([\d.]+)/.exec(d.verdicts.method.timestomp) || [0, '1.5'])[1]
  const cards = [
    { name: 'Timestomping', rule: 'Fires when at least one flagged file has the pattern and the flagged files carry it at least ' + thr + ' times as often as the disk does.', on: ts.indicated, ok: ev.timestomp.correct, truth: ev.truth.timestomp, weak: !tsReliable },
    { name: 'Insider anti-forensic activity', rule: d.verdicts.method.insider.replace(/^indicated when >=2 of/, 'Fires when at least two of') + '.', on: v.insiderAntiForensic.indicated, ok: ev.insider.correct, truth: ev.truth.insider },
    { name: 'Hacking tools', rule: 'Fires when ' + d.verdicts.method.hacker.replace(/^\(d\) /, '').replace(/ in the flagged set$/, ' appear in the flagged files') + '.', on: v.hackerTools.indicated, ok: ev.hacker_tools.correct, truth: ev.truth.hacker_tools }
  ]
  const bar = (label, rate, n, tot, c) => (
    <div className="enrbar"><span>{label}</span><div className="t"><i data-grow data-w={rate * 100} style={{ width: rate * 100 + '%', background: c }}></i></div><span className="num">{pr1(rate)}<small> {fmt(n)} of {fmt(tot)}</small></span></div>
  )

  return (
    <div className="vd">
      <div className="tbl ledger vtbl"><table>
        <thead><tr><th>Indicator</th><th>From the flagged files</th><th className="n">Files</th><th>Supporting files</th></tr></thead>
        <tbody>{INDS.map((x) => {
          const o = get(x.k), isOpen = !!open[x.k], n = o.count, shown = o.files.length, f = fired(x.k)
          return (
            <Fragment key={x.k}>
              <tr className={isOpen ? 'vopen' : ''}>
                <td><b>{x.name}</b><div className="small vwhat">{x.what}</div></td>
                <td><Flag kind={f ? 'ok' : 'bad'}>{f ? 'fired' : 'not fired'}</Flag>{x.k === 'timestomp' && lowEnr ? <> <Flag kind="warn">unreliable here</Flag></> : null}</td>
                <td className="n">{fmt(n)}</td>
                <td>{n > 0 ? <button type="button" className="lnk vtog" aria-expanded={isOpen} aria-controls={'vf-' + x.k} onClick={() => tog(x.k)}>{isOpen ? 'Hide' : 'Show'} {shown < n ? 'first ' + shown : shown} {shown === 1 ? 'file' : 'files'}</button> : <span className="small">none flagged</span>}</td>
              </tr>
              {isOpen && n > 0 ? (
                <tr className="vfiles"><td colSpan="4" id={'vf-' + x.k}>
                  <ol className="fl-list">{o.files.map((f2) => <li key={f2[0] + f2[1]}><span className="n">{fmt(f2[0])}</span><span className="mono" title={f2[1]}>{f2[1]}</span></li>)}</ol>
                  {shown < n ? <p className="small">{fmt(n - shown)} more are flagged and not listed.</p> : null}
                </td></tr>
              ) : null}
            </Fragment>)
        })}</tbody></table></div>

      <h4 className="vd-h">Overall verdicts, and a separate check against the known scenario</h4>
      <div className="vcards">{cards.map((c) => (
        <div key={c.name} className="vcard">
          <h5>{c.name}</h5>
          <p className="vc-v"><Flag kind={c.on ? 'ok' : 'bad'}>{c.on ? 'indicated' : 'not indicated'}</Flag>{c.weak ? <> <Flag kind="warn">weak basis</Flag></> : null}</p>
          <p className="small">{c.rule}</p>
          <p className="vc-chk small">Checked against the known scenario ({c.truth ? 'yes' : 'no'} in the case): <Flag kind={c.ok ? 'ok' : 'err'}>{c.ok ? 'correct' : 'wrong'}</Flag></p>
        </div>))}</div>
      <p className="small">Known scenario: {ev.truth.note}. The check mark is applied after the verdict is made, and plays no part in it.</p>

      <h4 className="vd-h">Is the timestomping signal any good on this disk?</h4>
      <div ref={enr} className="enr">
        {bar('Flagged files', ts.flaggedRate, ts.count, ts.flaggedWithFn, 'var(--m0)')}
        {bar('Whole disk (base rate)', ts.diskRate, ts.diskCount, ts.diskWithFn, 'var(--ink2)')}
        <p className="enr-line"><b className="mono">{ts.enrichment == null ? 'n/a' : ts.enrichment.toFixed(2) + '×'}</b> enrichment (flagged rate divided by base rate) · one-sided Fisher exact test p = <span className="mono">{pfmt(ts.fisherP)}</span></p>
        <p>
          {lowEnr
            ? 'The flagged files are less timestomp-like than the disk as a whole: ' + pr1(ts.flaggedRate) + ' against a base rate of ' + pr1(ts.diskRate) + '. The tool has not concentrated timestomped files, so this indicator is unreliable on this disk and its answer should not be read as evidence either way.'
            : ts.enrichment != null && ts.enrichment >= 1.5
              ? 'The flagged files carry the pattern ' + ts.enrichment.toFixed(2) + ' times as often as the disk does (' + pr1(ts.flaggedRate) + ' against ' + pr1(ts.diskRate) + '), so here the tool really does concentrate timestomp-like files.'
              : 'The flagged files carry the pattern ' + (ts.enrichment == null ? '' : ts.enrichment.toFixed(2) + ' times as often as the disk does') + ', which is above average but below the ' + thr + ' times that this indicator requires, so it does not fire.'}
          {ts.diskRate > 0.5 ? ' The rule also trips on ' + pr1(ts.diskRate) + ' of the whole disk, so tripping it says little by itself.' : ''}
        </p>
        <p className="small">Sub-second precision could not be tested: {ts.subSecondCheck.replace(/^unavailable: /, '')}.</p>
      </div>
    </div>
  )
}

/* ---------------- the exhibit ---------------- */
export default function ToolOutput({ img, m, pct }) {
  const { d, err } = useTrust(img)
  const mo = MODELS[m], bud = snap(pct)
  const tool = d ? d.toolOutput[mo] : null
  const S = tool ? tool.summary[bud] : null

  const note = useMemo(() => {
    if (!d) return null
    const sh = (mm) => BUDGETS.map((b) => d.toolOutput[mm].summary[b].systemNoiseShare)
    const us = BUDGETS.map((b) => d.toolOutput[mo].summary[b].userShare)
    return (
      <><b>The tool shortens the pile; it does not hand over the answer.</b> On {imgName(img)}, {pr1(S.systemNoiseShare)} of {SHORT[m]}’s top {bud}% is system noise and {pr1(S.userShare)} is user documents. Across the four budgets, system noise is {MODELS.map((mm, i) => MS[i] + ' ' + span(sh(mm), (x) => Math.round(x * 100)) + '%').join(', ')} of the top files on this disk, and {SHORT[m]}’s user documents never pass {pr1(Math.max.apply(null, us))}.</>
    )
  }, [d, img, m, bud])

  return (
    <Section id="toolout" letter="D" title="What the examiner actually sees">
      <Pr note={note}>
        <p>Everything so far counted targets. This exhibit shows the thing an examiner would actually be handed: a ranked list of files, most unusual first, each with a score and the one feature that pushed it up. Reading starts at rank 1 and stops when the budget is spent.</p>
        {S ? <p>Most of that list is system noise. At {bl(bud)} on {imgName(img)}, {SHORT[m]} returns {fmt(S.K)} files and {pr1(S.systemNoiseShare)} of them are system files, while user documents are {pr1(S.userShare)}. The examiner still has to wade through the noise to reach the evidence, which is {fmt(S.targetsHit)} of {S.targetsTotal} targets here.</p> : null}
        {Math.abs(pct * 100 - bud) > 0.05 ? <p className="small">The tool was run at 5, 10, 15 and 20% only, so your {fb1(pct * 100)}% is shown as the nearest of those, {bud}%.</p> : null}
      </Pr>

      {err ? <p className="small">The tool-output data could not be loaded.</p> : null}
      {!d && !err ? <p className="lab-load">Loading the tool output for {imgName(img)}…</p> : null}

      {d && tool ? (
        <>
          <div className="pout" role="region" aria-label={'Tool report for ' + imgName(img) + ', ' + SHORT[m] + ', ' + bud + '% budget'}>
            <div className="pout-h"><span>FORENSIQ · TRIAGE REPORT</span><span>{d.label}</span></div>
            <div className="pout-h pout-h2"><span>model: {mo}</span><span>budget: {bl(bud)}</span></div>
            <dl className="pout-dl">
              {[
                ['files indexed', fmt(d.files)],
                ['features', d.features.length + ' (' + d.constantFeatures.length + ' constant)'],
                ['review budget K', fmt(S.K) + ' files'],
                ['targets caught', S.targetsHit + ' of ' + S.targetsTotal + '  (' + fmt(S.targetFilesInTopK) + ' evidence files)'],
                ['first target rank', tool.firstTargetRank == null ? 'none' : fmt(tool.firstTargetRank)],
                ['noise share of top K', pr1(S.systemNoiseShare) + '  (' + fmt(S.systemNoise) + ' system files)'],
                ['user documents in top K', pr1(S.userShare) + '  (' + fmt(S.userFiles) + ' files)']
              ].map((r) => <div key={r[0]}><dt>{r[0]}</dt><i className="ld" aria-hidden="true"></i><dd>{r[1]}</dd></div>)}
            </dl>
            <div className="pout-f">ranked list follows · reasons are the top SHAP feature per file</div>
          </div>

          <h3 className="rel-h"><span>1</span>The ranked list, as the examiner reads it</h3>
          <Pr><p>Scroll the list or filter it. Evidence rows carry the red tag. The tags in the Type column come from the file path alone.</p></Pr>
          <RankList tool={tool} K={S.K} resetKey={img + mo + bud} />

          <h3 className="rel-h"><span>2</span>What the top K is made of</h3>
          <Fig n="4" name={'tool-mix-' + img + '-' + m} caption={<>What fills the top K at each budget, {SHORT[m]} on {imgName(img)}. Your budget ({bud}%) is the red label here and the shaded row in the table below. Evidence files are the target files inside the top K; they are also counted in their own file type, so the segments can overlap by at most that many files. Types are guessed from the path.</>}>
            <MixFig tool={tool} bud={bud} loaded={!!d} />
          </Fig>
          <div className="tbl ledger"><table>
            <thead><tr><th>Budget</th><th className="n">Top K</th><th className="n">System noise</th><th className="n">Logs</th><th className="n">User documents</th><th className="n">Evidence files</th><th className="n">Targets caught</th></tr></thead>
            <tbody>{BUDGETS.map((b) => { const s = tool.summary[b]; return (
              <tr key={b} className={b === bud ? 'cur' : ''}>
                <td>{bl(b)}</td><td className="n">{fmt(s.K)}</td>
                <td className="n">{fmt(s.systemNoise)} · {pr1(s.systemNoiseShare)}</td>
                <td className="n">{fmt(s.categories.log || 0)} · {pr1((s.categories.log || 0) / s.K)}</td>
                <td className="n">{fmt(s.userFiles)} · {pr1(s.userShare)}</td>
                <td className="n">{fmt(s.targetFilesInTopK)} · {pr1(s.targetFilesInTopK / s.K)}</td>
                <td className="n">{s.targetsHit} / {s.targetsTotal}</td>
              </tr>) })}</tbody></table></div>

          <h3 className="rel-h"><span>3</span>Fair verdicts: only what the tool flagged</h3>
          <Pr note={<>An earlier version of this page scored its indicators against the answer key, which made the check circular: it could only agree with itself. These verdicts are computed from the flagged files alone. The known scenario is looked up <b>after</b> each verdict is made, and shown as its own mark.</>}>
            <p>For the {bl(bud)} budget, each indicator below counts how many of the {fmt(S.K)} files {SHORT[m]} flagged match a pattern. The verdicts use only those flagged files. They never see the answer key.</p>
          </Pr>
          <Verdicts d={d} mo={mo} bud={bud} img={img} />
        </>
      ) : null}
    </Section>
  )
}
