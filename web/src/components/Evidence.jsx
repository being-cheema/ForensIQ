import { useRef } from 'react'
import { MODELS, SHORT, fmt, pc } from '../lib/data'
import { useGrow } from '../lib/hooks'
import Section from '../lib/Section'

function Detail(p) {
  const im = p.im, m = MODELS[p.m], t = im.targets.filter((x) => x.name === p.sel)[0], ref = useRef()
  useGrow(ref, [p.sel, p.m, p.img])
  if (!t) return <div className="panel detail" ref={ref}><p className="note">Select an evidence target.</p></div>
  const ok = t.ranks[m] <= p.K, drivers = t.shap[m] || t.shap[MODELS[0]], from = t.shap[m] ? SHORT[p.m] : SHORT[0]
  const mx = drivers && drivers.length ? (Math.max.apply(null, drivers.map((d) => Math.abs(d[1]))) || 1) : 1
  return (
    <div className="panel detail" ref={ref}>
      <div><span className={'chip ' + (ok ? 'ok' : 'bad')}>{ok ? 'caught' : 'missed'} at {pc(p.pct)}</span></div>
      <h3>{t.name}</h3><div className="mono note" style={{ wordBreak: 'break-all' }}>{t.path}</div>
      <dl className="kv"><dt>Rank under {SHORT[p.m]}</dt><dd>#{fmt(t.ranks[m])} of {fmt(im.files)}</dd><dt>Smallest budget that catches it</dt><dd>{pc(t.ranks[m] / im.files, 2)}</dd></dl>
      {drivers && drivers.length ? <><div><div className="eyebrow" style={{ marginBottom: 8 }}>Top drivers ({from} SHAP)</div>{drivers.map((d) => {
        const w = Math.abs(d[1]) / mx * 50, pos = d[1] >= 0, st = { width: w + '%', background: pos ? 'var(--ok)' : 'var(--bad)' }
        if (pos) st.left = '50%'; else st.right = '50%'
        return <div key={d[0]} className="fbar"><span>{d[0]}</span><span className="t"><i data-grow="1" data-w={w} style={st}></i></span><span className="num">{d[1] > 0 ? '+' : ''}{d[1].toFixed(2)}</span></div>
      })}</div><p className="note">Positive values pushed this file up the suspicion ranking. Generic features such as <span className="mono">is_shortcut_or_trace</span> also fire on harmless files, so a high value is a reason for the rank, not proof of intent.</p></>
        : <p className="note">No SHAP breakdown was computed for this file under this model: SHAP ran only on files the model flagged.</p>}
    </div>
  )
}

export default function Evidence(p) {
  const im = p.im, m = MODELS[p.m]
  const tg = im.targets.slice().sort((a, b) => a.ranks[m] - b.ranks[m])
  return (
    <Section id="evidence">
      <div className="sec-head rv"><div className="eyebrow">Evidence ledger and SHAP</div><h2>Which evidence, and why did the model flag it?</h2>
        <p>Each row is one evidence target. Pick one to see the features that pushed it up the ranking. SHAP explains the ranking, not intent: ordinary files can score the same way.</p></div>
      <div className="ledger rv"><div className="rows">{tg.map((t) => {
        const ok = t.ranks[m] <= p.K
        return <button key={t.name} className="row" type="button" aria-pressed={p.sel === t.name} onClick={() => p.setSel(t.name)}><span className={'ico ' + (ok ? 'ok' : 'bad')}></span><span>{t.name}<small>{t.copies} cop{t.copies > 1 ? 'ies' : 'y'} on disk</small></span><span className="mono num">#{fmt(t.ranks[m])}</span></button>
      })}</div><Detail im={im} m={p.m} K={p.K} pct={p.pct} sel={p.sel} img={p.img} /></div>
    </Section>
  )
}
