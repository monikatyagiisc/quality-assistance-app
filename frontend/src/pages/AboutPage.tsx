import { AGENTS, ARCHITECTURE_FLOW, DIAGRAM_FILES } from '../data/aboutContent'
import './AboutPage.css'

export function AboutPage() {
  return (
    <div className="about">
      <section className="about-hero">
        <p className="eyebrow">About</p>
        <h1>Quality Assistance Platform</h1>
        <p className="about-lead">
          An AI-powered software test life cycle (STLC) assistant that orchestrates specialized agents
          to help QA teams plan, execute, and report with confidence. Architecture and agent design are
          documented in the project{' '}
          <code>docs/</code> diagrams.
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
          From <strong>QualityAssistantAgentArchitecture</strong> — each agent focuses on one STLC
          capability and collaborates through the orchestrator.
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
          Open these Draw.io files from the repository docs folder (also bundled under{' '}
          <code>frontend/public/docs/</code>):
        </p>
        <ul className="diagram-list">
          {DIAGRAM_FILES.map((diagram) => (
            <li key={diagram.file}>
              <a href={diagram.file} target="_blank" rel="noreferrer">
                {diagram.title}
              </a>
            </li>
          ))}
        </ul>
        <p className="diagram-hint">
          View in{' '}
          <a href="https://app.diagrams.net/" target="_blank" rel="noreferrer">
            diagrams.net
          </a>{' '}
          via File → Open from → Device.
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
            <p>Google ADK, Gemini</p>
          </div>
        </div>
      </section>
    </div>
  )
}
