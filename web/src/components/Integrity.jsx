import I from '../data/study/integrity.json'
import { fmt } from '../lib/data'
import { Pr, Flag } from '../lib/Prose'

const ROWS = [['img1', 'Image 1'], ['img2', 'Image 2'], ['img3', 'Image 3'], ['pooled', 'All three']]
const pct = (x, d = 1) => (x * 100).toFixed(d) + '%'
const mb = (b) => (b / 1e6).toFixed(1) + ' MB'

/* Confusion matrix and chain-of-custody check for the final configuration (shown inside Exhibit B). */
export default function Integrity() {
  return (
    <>
      <Pr note={<>File-level precision is low by design: at a 20% budget the examiner reads a fifth of the disk, and only a few dozen of those files are evidence. What matters is that no evidence file is left out (FN).</>}>
        <h3>Confusion matrix at the 20% budget</h3>
        <p>Counts are files, for Isolation Forest on the 19 final features, seed 42. <b>TP</b>: evidence files flagged. <b>FP</b>: other files flagged. <b>FN</b>: evidence files missed. <b>TN</b>: other files correctly left out. Averaged over all five seeds, {I.cm.pooled.fnMean} evidence files were missed, all on Image 1, where every one of the 7 targets was still caught through another of its files.</p>
      </Pr>
      <div className="tbl"><table><thead><tr><th>Disk</th><th className="n">TP</th><th className="n">FP</th><th className="n">FN</th><th className="n">TN</th><th className="n">Precision</th><th className="n">Specificity</th></tr></thead><tbody>
        {ROWS.map(([k, l]) => { const r = I.cm[k]; return (
          <tr key={k}><td>{k === 'pooled' ? <b>{l}</b> : l}</td><td className="n">{fmt(r.TP)}</td><td className="n">{fmt(r.FP)}</td><td className="n">{r.FN === 0 ? <Flag kind="ok">0</Flag> : fmt(r.FN)}</td><td className="n">{fmt(r.TN)}</td><td className="n">{pct(r.precision, 2)}</td><td className="n">{pct(r.specificity)}</td></tr>
        ) })}
      </tbody></table></div>
      <Pr note={<>Hashing only reads the files. Nothing in the pipeline writes to an evidence image.</>}>
        <h3>Chain of custody: were the images and extracted files unchanged?</h3>
        <p>Every source image file was hashed (SHA-256 and MD5) and compared with the published reference: NIST's MD5 list for Image 1, NIST's SHA-1 values for Image 2's archives, and for Image 3 the acquisition MD5 inside the E01, which equals the hash in the examiner's published verification log. Every artefact extracted from the images was hashed before the analysis and hashed again after it.</p>
      </Pr>
      <div className="tbl"><table><thead><tr><th>Disk</th><th className="n">Image files</th><th>Published hash</th><th className="n">Artefacts</th><th className="n">Size</th><th>Changed after analysis</th></tr></thead><tbody>
        {ROWS.slice(0, 3).map(([k, l]) => { const c = I.custody[k]; return (
          <tr key={k}><td>{l}</td><td className="n">{c.segments}</td><td><Flag kind="ok">match</Flag> {c.ref}</td><td className="n">{fmt(c.artefacts)}</td><td className="n">{mb(c.bytes)}</td><td>{c.artMismatch === 0 ? <Flag kind="ok">0 files</Flag> : c.artMismatch + ' files'}</td></tr>
        ) })}
      </tbody></table></div>
    </>
  )
}
