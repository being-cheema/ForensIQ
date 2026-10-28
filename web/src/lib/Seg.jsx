import { MVAR } from './data'

/* Underlined tabs: a segmented control that reads like a form's tab row. */
export default function Seg(props) {
  return (
    <div className="tabs" role="group" aria-label={props.label}>
      {props.items.map((t, i) => (
        <button key={i} type="button" aria-pressed={props.value === i} style={props.colored ? { '--c': 'var(' + MVAR[i] + ')' } : undefined} onClick={() => props.onPick(i)}>{t}</button>
      ))}
    </div>
  )
}
