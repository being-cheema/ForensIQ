/* Prose row: a 680px column with an optional margin note beside it (inline on narrow screens). */
export function Pr({ children, note, className }) {
  return (
    <div className={'pr' + (className ? ' ' + className : '')}>
      <div className="pr-main">{children}</div>
      {note ? <aside className="side">{note}</aside> : null}
    </div>
  )
}

export function Flag({ kind, children }) { return <span className={'flag ' + kind}>{children}</span> }

export function Tag({ children }) { return <span className="tag"><i aria-hidden="true"></i>{children}</span> }
