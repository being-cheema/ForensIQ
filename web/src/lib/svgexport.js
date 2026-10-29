import { css } from './data'

const PROPS = ['fill', 'fill-opacity', 'stroke', 'stroke-width', 'stroke-opacity', 'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin', 'opacity',
  'font-family', 'font-size', 'font-weight', 'font-style', 'text-anchor', 'paint-order', 'font-variant-numeric']
function inline(src, dst) {
  const cs = getComputedStyle(src)
  PROPS.forEach((p) => dst.style.setProperty(p, cs.getPropertyValue(p)))
  ;['fill', 'stroke'].forEach((a) => { const v = dst.getAttribute(a); if (v && v.indexOf('var(') >= 0) dst.removeAttribute(a) })
  for (let i = 0; i < src.children.length; i++) inline(src.children[i], dst.children[i])
}

/* Serializes every svg.fgsvg inside root into one standalone SVG, with CSS variables resolved for the current theme. */
export function exportSvg(root, name) {
  const NS = 'http://www.w3.org/2000/svg', rr = root.getBoundingClientRect()
  const out = document.createElementNS(NS, 'svg')
  out.setAttribute('xmlns', NS); out.setAttribute('width', rr.width); out.setAttribute('height', rr.height)
  out.setAttribute('viewBox', '0 0 ' + rr.width + ' ' + rr.height)
  const bg = document.createElementNS(NS, 'rect'); bg.setAttribute('width', '100%'); bg.setAttribute('height', '100%'); bg.setAttribute('fill', css('--paper')); out.appendChild(bg)
  root.querySelectorAll('svg.fgsvg').forEach((s) => {
    const r = s.getBoundingClientRect(), c = s.cloneNode(true)
    inline(s, c)
    c.querySelectorAll('.no-export').forEach((n) => n.remove())
    c.setAttribute('x', r.left - rr.left); c.setAttribute('y', r.top - rr.top); c.setAttribute('width', r.width); c.setAttribute('height', r.height)
    out.appendChild(c)
  })
  const blob = new Blob(['<?xml version="1.0" encoding="UTF-8"?>\n' + new XMLSerializer().serializeToString(out)], { type: 'image/svg+xml' })
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = name + '.svg'
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000)
}
