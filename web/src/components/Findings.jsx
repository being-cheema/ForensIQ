import { MODELS, SHORT, MVAR, fmt } from '../lib/data'
import Section from '../lib/Section'

export default function Findings(p) {
  const im = p.im
  return (
    <Section id="verdicts">
      <div className="sec-head rv"><div className="eyebrow">Findings</div><h2>Timestomping and insider attack</h2>
        <p>{im.scenario === 'external'
          ? 'This disk is an outside intrusion, so the insider-attack test does not apply. Timestomping is confirmed only when a known timestomped file is flagged.'
          : 'Insider attack is called when at least half of the evidence targets are flagged. Timestomping is confirmed only when a known timestomped file is flagged; otherwise it is unverified.'}</p></div>
      <div className="panel scroll-x rv"><table><thead><tr><th>Model</th><th>Timestomping</th><th>Known timestomped file flagged</th><th className="n">$SI vs $FN mismatches in flagged set</th><th>Insider attack</th></tr></thead><tbody>{MODELS.map((m, i) => {
        const v = im.verdicts[m], ts = v.timestomp, cls = ts === 'YES' ? 'ok' : ts === 'NO' ? 'bad' : 'warn', ia = v.insider, ic = /CONFIRMED/.test(ia) ? 'ok' : /NOT/.test(ia) ? 'bad' : 'warn'
        return <tr key={m}><td><i className="dotkey" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{SHORT[i]}</td><td><span className={'chip ' + cls}>{ts}</span></td><td>{v.known_ts_hit && v.known_ts_hit.length ? v.known_ts_hit.join(', ') : '–'}</td><td className="n">{fmt(v.si_fn_mismatch_flagged || 0)}</td><td><span className={'chip ' + ic}>{ia}</span></td></tr>
      })}</tbody></table><p className="note" style={{ marginTop: 10 }}>A mismatch between the two timestamp sets is a hint of tampering, not proof: ordinary file operations also cause it.</p></div>
    </Section>
  )
}
