import { MODELS, SHORT, MVAR, fmt } from '../lib/data'
import Section from '../lib/Section'
import { Pr, Flag } from '../lib/Prose'

export default function Findings(p) {
  const im = p.im
  return (
    <Section id="verdicts" letter="I" title="The answer-key verdicts (circular, kept for comparison)">
      <Pr note={<>A mismatch between the two timestamp sets is a hint of tampering, not proof: ordinary file operations also cause it.</>}>
        <p><strong>These verdicts peek at the answer key</strong>: they say yes when a file already known to be evidence is flagged. A real case has no answer key, so they cannot be used as a finding. The fair verdicts, built only from what the tool flagged, are in Exhibit D.</p>
        <p>{im.scenario === 'external'
          ? 'This disk is an outside intrusion, so the insider-attack test does not apply. Timestomping is confirmed only when a known timestomped file is flagged.'
          : 'Insider attack is called when at least half of the evidence targets are flagged. Timestomping is confirmed only when a known timestomped file is flagged; otherwise it is unverified.'}</p>
      </Pr>
      <div className="tbl"><table><thead><tr><th>Model</th><th>Timestomping</th><th>Known timestomped file flagged</th><th className="n">$SI vs $FN mismatches in flagged set</th><th>Insider attack</th></tr></thead><tbody>{MODELS.map((m, i) => {
        const v = im.verdicts[m], ts = v.timestomp, cls = ts === 'YES' ? 'ok' : ts === 'NO' ? 'bad' : 'warn', ia = v.insider, ic = /CONFIRMED/.test(ia) ? 'ok' : /NOT/.test(ia) ? 'bad' : 'warn'
        return <tr key={m}><td><i className="key" style={{ background: 'var(' + MVAR[i] + ')' }}></i>{SHORT[i]}</td><td><Flag kind={cls}>{ts}</Flag></td><td>{v.known_ts_hit && v.known_ts_hit.length ? v.known_ts_hit.join(', ') : '–'}</td><td className="n">{fmt(v.si_fn_mismatch_flagged || 0)}</td><td><Flag kind={ic}>{ia}</Flag></td></tr>
      })}</tbody></table></div>
    </Section>
  )
}
