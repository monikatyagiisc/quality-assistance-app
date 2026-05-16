"""Google ADK root agent — model is configured via AGENT_BACKEND / AGENT_MODEL in .env."""

from quality_assistance_agent.agent_factory import create_root_agent, root_agent

__all__ = ["create_root_agent", "root_agent"]
