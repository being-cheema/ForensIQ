import { MVAR } from './data'

export default function Seg(props) {
  return (
    <div className={'seg' + (props.colored ? ' m' : '')} role="group" aria-label={props.label}>
      {props.items.map((t, i) => {
        const on = props.value === i
        return <button key={i} type="button" aria-pressed={on} style={props.colored && on ? { background: 'var(' + MVAR[i] + ')' } : undefined} onClick={() => props.onPick(i)}>{t}</button>
      })}
    </div>
  )
}
