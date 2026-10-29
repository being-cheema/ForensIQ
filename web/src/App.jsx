import { useEffect, useMemo, useRef, useState } from 'react'
import { D, MODELS, IMGS } from './lib/data'
import Hero from './components/Hero'
import ControlStrip from './components/ControlStrip'
import Lab from './lab/Lab'
import Verdict from './components/Verdict'
import Plateau from './components/Plateau'
import ToolOutput from './components/ToolOutput'
import Cleanup from './components/Cleanup'
import Ablations from './components/Ablations'
import Explain from './components/Explain'
import Remediation from './components/Remediation'
import Evidence from './components/Evidence'
import Pipeline from './components/Pipeline'
import Audit from './components/Audit'
import Limits from './components/Limits'
import Footer from './components/Footer'

export default function App() {
  const [img, setImgRaw] = useState(IMGS[0])
  const [m, setM] = useState(0)
  const [pct, setPct] = useState(0.2)
  const [selRaw, setSel] = useState(null)
  const [theme, setTheme] = useState(null)
  const tipRef = useRef()
  const im = D.images[img], K = Math.max(1, Math.round(pct * im.files))
  const sel = useMemo(() => {
    if (selRaw && im.targets.some((t) => t.name === selRaw)) return selRaw
    const tg = im.targets.slice().sort((a, b) => a.ranks[MODELS[m]] - b.ranks[MODELS[m]])
    return tg.length ? tg[0].name : null
  }, [selRaw, img, m])
  const setImg = (i) => { setImgRaw(i); setSel(null) }
  useEffect(() => {
    const r = document.documentElement
    if (theme) r.setAttribute('data-theme', theme); else r.removeAttribute('data-theme')
  }, [theme])
  const dark = theme ? theme === 'dark' : !!(window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches)
  return (
    <>
      <svg width="0" height="0" style={{ position: 'absolute' }} aria-hidden="true" focusable="false">
        <filter id="rough" x="-5%" y="-10%" width="110%" height="120%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="n" /><feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" /></filter>
      </svg>
      <Hero img={img} pct={pct} dark={dark} toggleTheme={() => setTheme(dark ? 'light' : 'dark')} />
      <ControlStrip img={img} m={m} pct={pct} K={K} setImg={setImg} setM={setM} setPct={setPct} />
      <main>
        <Lab img={img} m={m} pct={pct} tipRef={tipRef} />
        <Verdict />
        <Plateau img={img} m={m} pct={pct} />
        <ToolOutput img={img} m={m} pct={pct} />
        <Cleanup />
        <Ablations />
        <Explain />
        <Remediation img={img} />
        <Evidence img={img} im={im} m={m} K={K} pct={pct} sel={sel} setSel={setSel} />
        <Pipeline img={img} im={im} />
        <Audit />
        <Limits />
      </main>
      <Footer />
      <div className="tip" ref={tipRef}></div>
    </>
  )
}
