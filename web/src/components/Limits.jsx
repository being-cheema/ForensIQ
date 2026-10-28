import { fmt } from '../lib/data'
import Section from '../lib/Section'

export default function Limits(p) {
  const im = p.im, c = im.constant || [], rb = im.robustness || {}
  return (
    <Section id="limits" letter="K" title="What these numbers do not show">
      <ol className="notes">
        {c.length ? <li><b>{c.length} of the 23 features never vary on this disk</b> ({c.join(', ')}), so the models use {im.features.length - c.length} active features. <span className="mono">future_m</span> can never fire because its reference time is the newest timestamp on the same disk.</li> : null}
        <li><b>Targets are not an official answer key everywhere.</b> Disk 1 targets are rebuilt from case notes, disk 2 from the repository's CFReDS list, and disk 3 from the scenario author's own published examiner tags, because the official answer key for that scenario is access-restricted.</li>
        <li><b>The best model depends on the budget.</b> One-Class SVM leads at a strict 5% budget; Isolation Forest on 23 features leads from about 15%. Neither result is a claim about every disk.</li>
        <li><b>One-Class SVM trains on a 10,000-file subsample</b> and then scores every file. Its recall held across five subsample seeds{rb.ocsvm ? ' (' + Object.keys(rb.ocsvm).map((n) => { const v = rb.ocsvm[n]; return 'n=' + fmt(n) + ': ' + Math.min.apply(null, v) + '–' + Math.max.apply(null, v) + ' targets' }).join('; ') + ')' : ''}.</li>
        {rb.lof ? <li><b>LOF is sensitive to its neighbour count and is weakest at every setting tried</b> ({Object.keys(rb.lof).map((k) => 'k=' + k + ': ' + rb.lof[k]).join(', ')} targets). Duplicate feature rows distort it ({fmt(rb.unique_rows)} unique of {fmt(rb.rows)} rows).</li> : null}
        <li><b>SHAP explains the ranking, not intent.</b> Shortcut and log files score highly whether or not they relate to the case.</li>
        <li><b>Time-of-day features use UTC</b> (08:00 to 18:00 working hours); the disk's own time zone is not applied.</li>
      </ol>
    </Section>
  )
}
