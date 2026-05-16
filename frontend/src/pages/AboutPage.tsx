import { ARCHITECTURE_DIAGRAMS, AGENTS, ARCHITECTURE_FLOW, E2E_SEQUENCE_DIAGRAM } from '../data/aboutContent'
import { ArchitectureDiagramCard } from '../components/ArchitectureDiagramCard'
import './AboutPage.css'

export function AboutPage() {
  return (
    <div className="about">
      <section className="about-hero">
        <p className="eyebrow">About</p>
        <h1>Quality Assistance Platform</h1>
        <p className="about-lead">
          An AI-powered software test life cycle (STLC) assistant that orchestrates specialized agents
          to help QA teams plan, execute, and report with confidence. The stack is model-agnostic:
          swap Gemini, OpenAI, or other providers via agent configuration without changing the UI.
        </p>
      </section>

      <section className="about-section">
        <h2>How it works</h2>
        <div className="flow-grid">
          {ARCHITECTURE_FLOW.map((item, index) => (
            <article key={item.step} className="flow-card">
              <span className="flow-step">{index + 1}</span>
              <h3>{item.step}</h3>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-section">
        <h2>Quality Assistant agents</h2>
        <p className="section-desc">
          Each specialist focuses on one STLC capability and collaborates through the root
          orchestrator. Configure the active model in <code>agent/.env</code> (
          <code>AGENT_BACKEND</code>, <code>AGENT_MODEL</code>).
        </p>
        <div className="agent-grid">
          {AGENTS.map((agent) => (
            <article key={agent.name} className="agent-card">
              <h3>{agent.name}</h3>
              <p>{agent.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-section">
        <h2>Architecture diagrams</h2>
        <p className="section-desc">
          Interactive views of the Draw.io source files from the repository. If a diagram does not
          load (offline or blocked network), use <strong>Download .drawio</strong> or{' '}
          <strong>Open in diagrams.net</strong>.
        </p>
        <div className="diagram-grid">
          {ARCHITECTURE_DIAGRAMS.map((diagram) => (
            <ArchitectureDiagramCard key={diagram.id} diagram={diagram} />
          ))}
        </div>
      </section>

      <section className="about-section">
        <h2>End-to-end sequence</h2>
        <p className="section-desc">{E2E_SEQUENCE_DIAGRAM.description}</p>
        <div className="e2e-diagram-wrap">
          <img
            src={E2E_SEQUENCE_DIAGRAM.previewSvg}
            alt="Sequence diagram: user, frontend, backend, agent, database, and LLM provider"
          />
        </div>
        <p className="diagram-hint">
          Source: <code>docs/quality-assistance-e2e-sequence.puml</code> (PlantUML). Regenerate SVG
          after editing the sequence if needed.
        </p>
      </section>

      <section className="about-section stack-card">
        <h2>Technology stack</h2>
        <div className="stack-grid">
          <div>
            <h4>Frontend</h4>
            <p>React, Vite, Yarn, React Router</p>
          </div>
          <div>
            <h4>Backend</h4>
            <p>FastAPI, PostgreSQL, JWT auth</p>
          </div>
          <div>
            <h4>Agent</h4>
            <p>Google ADK orchestration</p>
            <p className="stack-sub">LLM: Gemini, OpenAI (LiteLLM), or compatible providers</p>
          </div>
        </div>
      </section>
    </div>
  )
}
