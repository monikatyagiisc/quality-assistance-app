"""Build the ADK agent with a configurable model backend."""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from quality_assistance_agent.settings import settings


def summarize_requirements(requirements: str) -> dict:
    """Extract key themes from software requirements for test planning."""
    lines = [line.strip() for line in requirements.splitlines() if line.strip()]
    return {
        "status": "success",
        "line_count": len(lines),
        "preview": "\n".join(lines[:5]),
    }


AGENT_INSTRUCTION = """You are a senior QA engineer assistant. Help teams with:
- Turning requirements and user stories into structured test cases
- Suggesting test data and automation approaches
- Summarizing risks, defects, and release readiness

Be concise, actionable, and organized with clear headings and bullet points.
When requirements are provided, use the summarize_requirements tool first."""


def resolve_model():
    """Return an ADK model: Gemini string or LiteLLM wrapper for other providers."""
    if settings.agent_backend == "litellm":
        return LiteLlm(model=settings.agent_model)
    return settings.agent_model


def create_root_agent() -> Agent:
    return Agent(
        model=resolve_model(),
        name="quality_assistance_agent",
        description=(
            "Quality engineering assistant for test planning, test cases, "
            "and release readiness guidance across the STLC."
        ),
        instruction=AGENT_INSTRUCTION,
        tools=[summarize_requirements],
    )


root_agent = create_root_agent()
