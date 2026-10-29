import { useEffect, useMemo, useRef, useState } from 'react'
import { fmt } from '../lib/data'
import Section from '../lib/Section'
import { Pr } from '../lib/Prose'
import { useDisk, fitModel, DEFAULT_CFG } from './data'
import A1 from './A1'
import A2 from './A2'
import A3 from './A3'
import A4 from './A4'
import A5 from './A5'

const MODEL_KEYS = ['if', 'lof', 'svm']

export default function Lab({ img, m, pct, tipRef }) {
  const { d, err } = useDisk(img)
  return (
    <Section id="lab" letter="A" title="The Lab">
      <Pr note={<>The sample holds <b>every labelled evidence file</b> plus a random draw of ordinary files, so evidence is far more common here than on a real disk. Read the rates in this exhibit as a demonstration of how the model behaves, not as the headline recall.</>}>
        <p>Everything below runs in your browser, on a 2,000-file sample of the selected disk. Change a setting and the model is refitted on the spot. The full-disk ranks you see elsewhere on this page come from the Python run on every file; One-Class SVM is not run live, so wherever it appears here it is that saved full-disk rank.</p>
      </Pr>
      {err ? <p className="small">The sample for this disk could not be loaded.</p> : !d ? <div className="lab-load" role="status">Loading the sample…</div> : <LabBody key={img} d={d} m={m} pct={pct} tipRef={tipRef} />}
    </Section>
  )
}

function LabBody({ d, m, pct, tipRef }) {
  const [cfg, setCfgRaw] = useState(() => ({ ...DEFAULT_CFG, mask: d.features.map(() => true), model: 'if' }))
  const [live, setLive] = useState(cfg)
  const [planted, setPlanted] = useState(null)
  const timer = useRef(0)
  const setCfg = (fn) => setCfgRaw((c) => (typeof fn === 'function' ? fn(c) : fn))
  // follow the model chosen in the control bar
  const firstM = useRef(true)
  useEffect(() => { if (firstM.current) { firstM.current = false; return } setCfg((c) => ({ ...c, model: MODEL_KEYS[m] || 'if' })) }, [m])
  // refit about 120 ms after the last change
  useEffect(() => { clearTimeout(timer.current); timer.current = setTimeout(() => { if (cfg.mask.some(Boolean)) setLive(cfg) }, 120); return () => clearTimeout(timer.current) }, [cfg])
  const fit = useMemo(() => fitModel(d, live), [d, live])
  const [history, setHistory] = useState([])
  useEffect(() => { setHistory((h) => h.concat({ ranks: fit.ranks }).slice(-10)) }, [fit])

  return (
    <>
      <A1 d={d} fit={fit} cfg={cfg} setCfg={setCfg} pct={pct} tipRef={tipRef} history={history} planted={planted} />
      <A2 d={d} cfg={live} tipRef={tipRef} />
      <A3 d={d} fit={fit} pct={pct} setPlanted={setPlanted} />
      <A4 d={d} />
      <A5 d={d} fit={fit} tipRef={tipRef} />
    </>
  )
}
