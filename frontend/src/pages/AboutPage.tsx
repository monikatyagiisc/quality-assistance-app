import { Link } from 'react-router-dom'
import { AGENTS, ARCHITECTURE_FLOW } from '../data/aboutContent'
import './AboutPage.css'

export function AboutPage() {
  return (
    <div className="about">
      <section className="about-hero">
        <div className="about-hero-content">
          <p className="eyebrow">About the platform</p>
          <h1>Quality engineering, made more actionable</h1>
          <p className="about-lead">
            Quality Assistance helps teams turn requirements, user stories, code changes, and test
            results into practical quality-engineering guidance. Specialized AI agents support
            planning, analysis, and reporting across the software test life cycle.
          </p>
          <div className="about-actions">
            <Link to="/user-guide" className="btn btn-primary">Explore the user guide</Link>
            <Link to="/contact" className="btn btn-ghost">Contact us</Link>
          </div>
        </div>
        <aside className="about-hero-note">
          <span className="about-note-mark" aria-hidden="true">QA</span>
          <p>Designed to complement your team’s expertise—not replace human review.</p>
        </aside>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <p className="eyebrow">A guided workflow</p>
          <h2>How it works</h2>
          <p className="section-desc">
            Start with the context you already have. The assistant organizes it into focused
            guidance that your team can review and apply.
          </p>
        </div>
        <div className="flow-grid">
          {ARCHITECTURE_FLOW.map((item, index) => (
            <article key={item.step} className="flow-card">
              <span className="flow-step" aria-label={`Step ${index + 1}`}>
                {String(index + 1).padStart(2, '0')}
              </span>
              <h3>{item.step}</h3>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-section">
        <div className="about-section-heading">
          <p className="eyebrow">Specialized capabilities</p>
          <h2>Support across the quality life cycle</h2>
          <p className="section-desc">
            Each specialist focuses on a quality-engineering activity. Together, they help you move
            from early planning through change review and release communication.
          </p>
        </div>
        <div className="agent-grid">
          {AGENTS.map((agent) => (
            <article key={agent.name} className="agent-card">
              <h3>{agent.name}</h3>
              <p>{agent.description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-section stack-card">
        <div>
          <p className="eyebrow">Built for flexibility</p>
          <h2>Technology at a glance</h2>
          <p className="stack-intro">
            A modular application with a configurable AI provider and a web-based workspace.
          </p>
        </div>
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

      <section className="about-next-step">
        <div>
          <p className="eyebrow">Get started</p>
          <h2>Put the assistant to work on your next quality task</h2>
          <p>Try a sample workflow or follow the step-by-step guide to explore the workspace.</p>
        </div>
        <div className="about-actions">
          <Link to="/user-guide" className="btn btn-primary">Read the user guide</Link>
          <Link to="/dashboard" className="btn btn-ghost">Open workspace</Link>
        </div>
      </section>
    </div>
  )
}
