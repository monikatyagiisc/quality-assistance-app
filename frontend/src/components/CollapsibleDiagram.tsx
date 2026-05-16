import { useId, useState } from 'react'
import './CollapsibleDiagram.css'

type CollapsibleDiagramProps = {
  src: string
  alt: string
  previewHeight?: number
  theme?: 'light' | 'dark'
}

export function CollapsibleDiagram({
  src,
  alt,
  previewHeight = 140,
  theme = 'dark',
}: CollapsibleDiagramProps) {
  const [expanded, setExpanded] = useState(false)
  const panelId = useId()
  const themeClass = theme === 'light' ? ' collapsible-diagram--light' : ''

  return (
    <div className={`collapsible-diagram${themeClass}${expanded ? ' is-expanded' : ' is-collapsed'}`}>
      <div className="collapsible-diagram-toolbar">
        <button
          type="button"
          className="btn btn-ghost btn-sm collapsible-diagram-toggle"
          aria-expanded={expanded}
          aria-controls={panelId}
          onClick={() => setExpanded((open) => !open)}
        >
          {expanded ? 'Hide diagram' : 'Expand diagram'}
        </button>
        {!expanded && (
          <span className="muted collapsible-diagram-hint">Preview shown — expand for full view</span>
        )}
      </div>

      <div
        id={panelId}
        className="collapsible-diagram-body"
        style={expanded ? undefined : { maxHeight: `${previewHeight}px` }}
      >
        <div className="collapsible-diagram-wrap">
          <img src={src} alt={alt} />
        </div>
        {!expanded && <div className="collapsible-diagram-fade" aria-hidden="true" />}
      </div>
    </div>
  )
}
