import { Link } from 'react-router-dom'
import { AGENTS } from '../data/aboutContent'
import './LandingPage.css'

export function LandingPage() {
  return (
    <div className="landing">
      <section className="landing-hero">
        <p className="eyebrow">AI · STLC · Quality Engineering</p>
        <h1>
          Ship with confidence using an <span className="gradient-text">intelligent QA copilot</span>
        </h1>
        <p className="landing-lead">
          Quality Assistance orchestrates specialized agents — from test case design to release
          readiness — powered by Google ADK and your software requirements.
        </p>
        <div className="landing-cta">
          <Link to="/register" className="btn btn-primary btn-lg">
            Get started free
          </Link>
          <Link to="/about" className="btn btn-ghost btn-lg">
            Learn more
          </Link>
        </div>
      </section>

      <section className="landing-agents">
        <h2>Powered by multi-agent STLC</h2>
        <div className="landing-agent-grid">
          {AGENTS.slice(0, 6).map((agent) => (
            <div key={agent.name} className="landing-agent-pill">
              {agent.name}
            </div>
          ))}
          <div className="landing-agent-pill muted-pill">+{AGENTS.length - 6} more</div>
        </div>
      </section>
    </div>
  )
}
