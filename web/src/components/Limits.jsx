import { fmt } from '../lib/data'
import Section from '../lib/Section'
import { A2, A7, DISKS, PROTOCOL_URL, AMENDMENT_URL, f1, rangeTxt } from '../lib/study'

export default function Limits() {
  const spreads = DISKS.map((t) => A2.disks[t].models.IF.summary.knee_spread_pp)
  const noise = ['img1', 'img3'].map((t) => A7.results.noise3600[t].at15.rel_drop_pct)
  return (
    <Section id="limits" letter="L" title="What these numbers do not show">
      <ol className="notes">
        <li><b>Three disks are not a population.</b> One is an outside intrusion, one an insider data leak and one a lone-wolf case. Nothing here shows that a 20% budget works on a disk from another case.</li>
        <li><b>The targets are not an official answer key everywhere.</b> Disk 1 targets are rebuilt from case notes and disk 2 from the repository’s CFReDS list. On disk 3 the targets are the files an examiner tagged in the suspect’s home folder, because the official key is access-restricted. A plain “read the user folder first” rule therefore also finds 34 of 34 there (A4). Disk 3 mostly shows that the model agrees with that examiner.</li>
        <li><b>The exact budget is not stable.</b> The point where 90% of targets are found moves by {rangeTxt(Math.min.apply(null, spreads), Math.max.apply(null, spreads))} percentage points between seeds for Isolation Forest, and the pre-registered stability test failed (A2). A 20% budget worked in every seed here, but it was not derived from a stable threshold.</li>
        <li><b>Timestamp features add little for Isolation Forest.</b> Removing the whole timestamp group lowered recall on none of the three disks (A1). The model leans on file location and activity. The timestamp features still matter for explanations of tampering, but not for ranking.</li>
        <li><b>Noisy clocks hurt.</b> With about an hour of random noise on every timestamp, recall at 15% fell by {f1(noise[0])}% on Image 1 and {f1(noise[1])}% on Image 3, past the 10% allowed (A7). The burst features, which rely on files sharing a modified time, are the likely weak spot. Dropping 10% of files did not hurt.</li>
        <li><b>The explanation is only as good as the model.</b> LOF fails every explainability test (Exhibit G), so its reasons should not be shown to an examiner. Isolation Forest finds only about half of the planted attacks at 20%, although it names the right cause for 92 to 100% of those it does find.</li>
        <li><b>SHAP explains the ranking, not intent.</b> Shortcut and log files score highly whether or not they relate to the case, and a flagged file is a lead, not a verdict.</li>
        <li><b>Reading 20% is still a lot.</b> On the largest disk that is {fmt(Math.round(0.2 * A2.disks.img3.N))} files, and most of them are not evidence (Exhibit D).</li>
        <li><b>The advice generator is lightly tested.</b> It was scored on three disks and nine indicators. Its commands were pattern-checked, never executed, and they are written for a live system, never for evidence.</li>
        <li><b>This study was pre-registered, with one amendment.</b> The pass rules were fixed before any result was computed, and failures are reported as failures. One rule, drop any feature whose removal does not hurt, gave a degenerate result and was replaced by the burst-feature rule, which passed as written. Read the <a href={PROTOCOL_URL} rel="noopener noreferrer">protocol</a> and the <a href={AMENDMENT_URL} rel="noopener noreferrer">amendment</a> on GitHub.</li>
      </ol>
    </Section>
  )
}
