import { useMemo, useRef, useState } from 'react'
import { D, MODELS, IMGS } from './lib/data'
import Hero from './components/Hero'
import ControlStrip from './components/ControlStrip'
import Simulation from './components/Simulation'
import Verdict from './components/Verdict'
import Results from './components/Results'
import Findings from './components/Findings'
import Evidence from './components/Evidence'
import Pipeline from './components/Pipeline'
import Ablation from './components/Ablation'
import Stability from './components/Stability'
import Firing from './components/Firing'
import Audit from './components/Audit'
import Limits from './components/Limits'
import Footer from './components/Footer'

export default function App() {
  const [img, setImgRaw] = useState(IMGS[0])
  const [m, setM] = useState(2)
  const [pct, setPct] = useState(0.05)
  const [selRaw, setSel] = useState(null)
  const tipRef = useRef()
  const im = D.images[img], K = Math.max(1, Math.round(pct * im.files))
  const sel = useMemo(() => {
    if (selRaw && im.targets.some((t) => t.name === selRaw)) return selRaw
    const tg = im.targets.slice().sort((a, b) => a.ranks[MODELS[m]] - b.ranks[MODELS[m]])
    return tg.length ? tg[0].name : null
  }, [selRaw, img, m])
  const setImg = (i) => { setImgRaw(i); setSel(null) }
  return (
    <>
      <Hero />
      <ControlStrip img={img} m={m} pct={pct} K={K} setImg={setImg} setM={setM} setPct={setPct} />
      <div className="wrap">
        <Simulation img={img} im={im} m={m} K={K} sel={sel} tipRef={tipRef} />
        <Verdict />
        <Results img={img} im={im} m={m} pct={pct} />
        <Findings im={im} />
        <Evidence img={img} im={im} m={m} K={K} pct={pct} sel={sel} setSel={setSel} />
        <Pipeline img={img} im={im} />
        <Ablation img={img} im={im} />
        <Stability img={img} pct={pct} />
        <Firing img={img} />
        <Audit />
        <Limits im={im} />
        <Footer />
      </div>
      <div className="tip" ref={tipRef}></div>
    </>
  )
}
