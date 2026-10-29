import { useEffect, useState } from 'react'

/* The trust data (tool output, verdicts, explanation checks) is large, so each disk is its own chunk, loaded on demand. */
const LOAD = {
  img1: () => import('../data/trust/img1.json'),
  img2: () => import('../data/trust/img2.json'),
  img3: () => import('../data/trust/img3.json')
}
const cache = {}, pending = {}

export function loadTrust(img) {
  if (cache[img]) return Promise.resolve(cache[img])
  if (!pending[img]) pending[img] = LOAD[img]().then((m) => { cache[img] = m.default; return cache[img] })
  return pending[img]
}

/* One disk's trust data, or null while it loads (or if it failed). */
export function useTrust(img) {
  const [st, setSt] = useState({ img, d: cache[img] || null, err: false })
  useEffect(() => {
    let on = true
    if (cache[img]) { setSt({ img, d: cache[img], err: false }); return }
    setSt({ img, d: null, err: false })
    loadTrust(img).then((d) => { if (on) setSt({ img, d, err: false }) }).catch(() => { if (on) setSt({ img, d: null, err: true }) })
    return () => { on = false }
  }, [img])
  return { d: st.img === img ? st.d : cache[img] || null, err: st.err }
}
