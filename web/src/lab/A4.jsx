import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { AN, canAnim } from '../lib/motion'
import { fmt } from '../lib/data'
import Num from '../lib/Num'
import { fitIsolationForest } from './engine.js'
import { Part } from './ui'
import { utcDay, shuffled, shortPath } from './data'

const READS = 40, SECS = 90, ROW = 52

export default function A4({ d }) {
  const [phase, setPhase] = useState('ready')       // ready | playing | done
  const [seedN, setSeedN] = useState(1)
  const [reads, setReads] = useState([])             // indices in the order read
  const [fresh, setFresh] = useState(-1)
  const [left, setLeft] = useState(SECS)
  const [hints, setHints] = useState(false)
  const [q, setQ] = useState('')
  const [top, setTop] = useState(0)
  const [shown, setShown] = useState(0)
  const box = useRef(), barRef = useRef(), revealRef = useRef(), endAt = useRef(0)

  // the model: Isolation Forest, all 23 features, fitted live on this sample
  const model = useMemo(() => {
    const f = fitIsolationForest(d.X, { nTrees: 200, sampleSize: 256, seed: 42 })
    const s = d.X.map((x) => f.score(x))
    let lo = Infinity, hi = -Infinity; s.forEach((v) => { if (v < lo) lo = v; if (v > hi) hi = v })
    const order = s.map((v, i) => i).sort((a, b) => s[b] - s[a])
    return { s, lo, hi, order }
  }, [d])
  const order = useMemo(() => shuffled(d.n, seedN * 7919 + d.n), [d, seedN])
  const readSet = useMemo(() => new Set(reads), [reads])
  const list = useMemo(() => {
    const s = q.trim().toLowerCase()
    return s ? order.filter((i) => d.rows[i].p.toLowerCase().includes(s)) : order
  }, [order, q, d])

  useEffect(() => { reset() }, [d])
  function reset() {
    setPhase('ready'); setReads([]); setFresh(-1); setLeft(SECS); setShown(0); setQ(''); setTop(0)
    if (box.current) box.current.scrollTop = 0
    if (barRef.current) barRef.current.style.width = '100%'
    AN.remove(barRef.current)
  }
  function start() { reset(); setPhase('playing'); endAt.current = performance.now() + SECS * 1000 }
  function again() { setSeedN((s) => s + 1); reset() }
  // clock
  useEffect(() => {
    if (phase !== 'playing') return
    const id = setInterval(() => {
      const rem = Math.max(0, (endAt.current - performance.now()) / 1000)
      setLeft(Math.ceil(rem))
      if (barRef.current) barRef.current.style.width = (rem / SECS) * 100 + '%'
      if (rem <= 0) finish()
    }, 120)
    return () => clearInterval(id)
  }, [phase])
  const readsRef = useRef(reads); readsRef.current = reads
  function finish() { setPhase('done') }
  function read(i) {
    if (phase !== 'playing' || readSet.has(i)) return
    const next = reads.concat(i); setReads(next); setFresh(i)
    if (next.length >= READS) setTimeout(finish, 650)
  }

  // results
  const humanHits = reads.filter((i) => d.isT[i]).length
  const picks = model.order.slice(0, READS)
  const modelHits = picks.filter((i) => d.isT[i]).length
  const T = d.targetIdx.length
  const humanSet = readSet, modelSet = useMemo(() => new Set(picks), [model])
  const hRows = Math.max(1, reads.length), nRows = hRows + READS

  // reveal animation: rows come in one by one
  useLayoutEffect(() => {
    if (phase !== 'done') return
    const root = revealRef.current; if (!root) return
    const rows = root.querySelectorAll('.rv-row')
    const rc = root.getBoundingClientRect(); if (rc.top > window.innerHeight * 0.6) window.scrollBy({ top: rc.top - 120, behavior: canAnim() ? 'smooth' : 'auto' })
    if (!canAnim()) { setShown(9999); return }
    setShown(0)
    const per = 55
    AN.set(rows, { opacity: 0 })
    AN({ targets: rows, opacity: [0, 1], translateX: (el) => [el.dataset.side === 'm' ? 14 : -14, 0], delay: AN.stagger(per), duration: 300, easing: 'easeOutQuart',
      update: (a) => setShown(Math.floor(a.currentTime / per)), complete: () => setShown(9999) })
    const t = setTimeout(() => { AN.set(rows, { opacity: 1, translateX: 0 }); setShown(9999) }, rows.length * 55 + 1800)
    return () => { clearTimeout(t); AN.remove(rows) }
  }, [phase])
  // the displayed scores follow the reveal
  const hShown = phase === 'done' ? reads.slice(0, shown).filter((i) => d.isT[i]).length : 0
  const mShown = phase === 'done' ? picks.slice(0, Math.max(0, shown - hRows)).filter((i) => d.isT[i]).length : 0
  const settled = shown >= nRows

  // windowed list
  const onScroll = useCallback((e) => { setTop(e.currentTarget.scrollTop) }, [])
  const first = Math.max(0, Math.floor(top / ROW) - 4), last = Math.min(list.length, first + Math.ceil(420 / ROW) + 10)
  const range = list.slice(first, last)

  const mm = model.hi - model.lo || 1
  const verdict = humanHits > modelHits ? 'You beat the model on this sample.' : humanHits === modelHits ? 'A tie with the model.' : 'The model read the same number of files and found ' + (modelHits - humanHits) + ' more.'
  const ledger = d.targetIdx.filter((i) => humanSet.has(i) || modelSet.has(i))

  return (
    <Part n="A4" title="Examiner versus machine"
      intro={'You have ' + READS + ' reads and ' + SECS + ' seconds to find as much evidence as you can in the sample. Click a file to read it. When the round ends, the Isolation Forest gets the same ' + READS + ' reads.'}
      note={<>The model has never seen which files are evidence; it ranks purely on the 23 features, fitted live on this sample. A random reader would expect to find about <b>{(READS / d.n * T).toFixed(1)}</b> of the sample's {T} evidence files.</>}>
      <div className="g-bar">
        <div className="g-stats" aria-live="polite" aria-atomic="true">
          <span><b className="num"><Num value={Math.max(0, READS - reads.length)} fmt={String} /></b> reads left</span>
          <span><b className="num">{phase === 'ready' ? SECS : left}</b> s</span>
          <span><b className="num"><Num value={humanHits} fmt={String} /></b> evidence found</span>
        </div>
        <div className="g-btns">
          {phase === 'ready' ? <button type="button" className="btn lab-btn pri" onClick={start}>Start the {SECS}-second round</button> : null}
          {phase === 'playing' ? <button type="button" className="btn lab-btn" onClick={finish}>Stop and reveal</button> : null}
          {phase === 'done' ? <button type="button" className="btn lab-btn pri" onClick={again}>Play again (reshuffle)</button> : null}
          <label className="lf"><input type="checkbox" checked={hints} onChange={(e) => setHints(e.target.checked)} /><span>Show hints (model score)</span></label>
        </div>
      </div>
      <div className="g-clock" aria-hidden="true"><i ref={barRef}></i></div>
      <div className="g-find"><label htmlFor="a4-q" className="small">Search paths</label><input id="a4-q" type="search" placeholder="e.g. .exe, Downloads, temp" value={q} onChange={(e) => { setQ(e.target.value); if (box.current) box.current.scrollTop = 0; setTop(0) }} />
        <span className="small">{fmt(list.length)} files</span></div>
      <div className={'g-list' + (phase === 'ready' ? ' wait' : '')} ref={box} onScroll={onScroll} tabIndex={-1} role="list" aria-label="Files in the sample">
        <div style={{ height: list.length * ROW, position: 'relative' }}>
          {range.map((i, k) => {
            const isR = readSet.has(i), t = d.isT[i], y = (first + k) * ROW
            return (
              <Row key={i} y={y} i={i} d={d} read={isR} target={isR && t} fresh={fresh === i} disabled={phase !== 'playing' || isR}
                hint={hints ? (model.s[i] - model.lo) / mm : -1} onRead={read} />
            )
          })}
        </div>
        {phase === 'ready' ? <div className="g-veil"><p>Press start. The clock only runs while you play.</p></div> : null}
      </div>
      {phase === 'done' ? (
        <div className="g-result" ref={revealRef}>
          <div className="g-score" aria-live="polite">
            <span>You: <b className="num"><Num value={hShown} fmt={String} />/{T}</b></span>
            <span className="mid">·</span>
            <span>Isolation Forest: <b className="num m"><Num value={mShown} fmt={String} />/{T}</b></span>
          </div>
          <p className="g-verdict">{settled ? verdict : ' '}</p>
          <div className="g-cols">
            <div><h4 className="cap">Your {reads.length} reads</h4>
              <ol className="rv">
                {reads.map((i, k) => <li key={i} className={'rv-row' + (d.isT[i] ? ' t' : '')} data-side="h"><span className="ix">{k + 1}</span><span className="nm">{d.name[i]}</span>{d.isT[i] ? <span className="tag"><i></i>Evidence</span> : null}</li>)}
                {!reads.length ? <li className="rv-row idle" data-side="h">No reads.</li> : null}
              </ol></div>
            <div><h4 className="cap">Isolation Forest, top {READS}</h4>
              <ol className="rv">
                {picks.map((i, k) => <li key={i} className={'rv-row' + (d.isT[i] ? ' t' : '')} data-side="m"><span className="ix">{k + 1}</span><span className="nm">{d.name[i]}</span>{d.isT[i] ? <span className="tag"><i></i>Evidence</span> : null}</li>)}
              </ol></div>
          </div>
          {settled ? (
            <div className="tbl"><table>
              <thead><tr><th>Evidence file</th><th>You</th><th>Model</th></tr></thead>
              <tbody>
                {ledger.slice(0, 14).map((i) => <tr key={i}><td>{d.name[i]}<div className="sub">{d.rows[i].t}</div></td><td>{humanSet.has(i) ? <span className="flag ok">Found</span> : <span className="flag bad">No</span>}</td><td>{modelSet.has(i) ? <span className="flag ok">Found</span> : <span className="flag bad">No</span>}</td></tr>)}
                {!ledger.length ? <tr><td colSpan="3">Neither side found any evidence file.</td></tr> : null}
              </tbody></table>
              {ledger.length > 14 ? <p className="small">and {ledger.length - 14} more found by one side or the other.</p> : null}
              <p className="small">{T - ledger.length} of the sample's {T} evidence files were found by neither.</p></div>
          ) : null}
        </div>
      ) : null}
    </Part>
  )
}

function Row({ y, i, d, read, target, fresh, disabled, hint, onRead }) {
  const tag = useRef(), btn = useRef()
  useLayoutEffect(() => {
    if (!fresh || !target) return
    if (!tag.current || !canAnim()) return
    AN({ targets: tag.current, scale: [2.4, 1], rotate: [-14, -3], opacity: [0, 1], duration: 420, easing: 'easeOutBack' })
    AN({ targets: btn.current, backgroundColor: ['rgba(200,55,31,.28)', 'rgba(200,55,31,.08)'], duration: 700, easing: 'easeOutQuad' })
  }, [fresh, target])
  const t = d.mtime[i]
  return (
    <button ref={btn} type="button" role="listitem" className={'g-row' + (read ? ' read' : '') + (target ? ' hit' : '')} style={{ transform: 'translateY(' + y + 'px)', height: ROW }} disabled={disabled && !read}
      aria-disabled={disabled} onClick={() => onRead(i)} aria-label={d.name[i] + ', ' + d.folder[i] + (read ? (target ? ', read: evidence' : ', read') : '')}>
      <span className="g-nm"><b>{d.name[i]}</b><small className="mono">{shortPath(d.folder[i], 46)}</small></span>
      <span className="g-dt mono">{t ? utcDay(t) : '—'}</span>
      {target ? <span ref={tag} className="tag g-tag"><i></i>Evidence</span> : read ? <span className="g-ok" aria-hidden="true">read</span> : null}
      {hint >= 0 ? <i className="g-hint" style={{ width: Math.max(2, hint * 100) + '%' }} aria-hidden="true"></i> : null}
    </button>
  )
}
