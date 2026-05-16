import { useMemo } from 'react'
import type { ArchitectureDiagram } from '../data/aboutContent'
import './ArchitectureDiagramCard.css'

type ArchitectureDiagramCardProps = {
  diagram: ArchitectureDiagram
}

function buildDrawioViewerUrl(drawioPath: string): string {
  const absolute = new URL(drawioPath, window.location.origin).href
  const encoded = encodeURIComponent(absolute)
  return `https://viewer.diagrams.net/?lightbox=1&nav=1&title=${encodeURIComponent(drawioPath)}#U${encoded}`
}

export function ArchitectureDiagramCard({ diagram }: ArchitectureDiagramCardProps) {
  const viewerUrl = useMemo(() => buildDrawioViewerUrl(diagram.drawioFile), [diagram.drawioFile])
  const fileName = diagram.drawioFile.split('/').pop() ?? 'diagram.drawio'

  return (
    <article className="diagram-card">
      <header className="diagram-card-header">
        <h3>{diagram.title}</h3>
        <p>{diagram.description}</p>
      </header>

      <div className="diagram-viewer-wrap">
        <iframe
          title={diagram.title}
          className="diagram-viewer"
          src={viewerUrl}
          loading="lazy"
          referrerPolicy="no-referrer"
        />
      </div>

      <div className="diagram-actions">
        <a className="btn btn-ghost btn-sm" href={diagram.drawioFile} download={fileName}>
          Download .drawio
        </a>
        <a className="btn btn-ghost btn-sm" href={viewerUrl} target="_blank" rel="noreferrer">
          Open in diagrams.net
        </a>
      </div>
    </article>
  )
}
