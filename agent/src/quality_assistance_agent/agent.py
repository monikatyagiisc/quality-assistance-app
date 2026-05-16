"""Google ADK root agent for quality assistance (STLC-focused)."""

from google.adk.agents import Agent


def summarize_requirements(requirements: str) -> dict:
    """Extract key themes from software requirements for test planning."""
    lines = [line.strip() for line in requirements.splitlines() if line.strip()]
    return {
        "status": "success",
        "line_count": len(lines),
        "preview": "\n".join(lines[:5]),
    }


root_agent = Agent(
    model="gemini-2.0-flash",
    name="quality_assistance_agent",
    description=(
        "Quality engineering assistant for test planning, test cases, "
        "and release readiness guidance across the STLC."
    ),
    instruction="""You are a senior QA engineer assistant. Help teams with:
- Turning requirements and user stories into structured test cases
- Suggesting test data and automation approaches
- Summarizing risks, defects, and release readiness

Be concise, actionable, and organized with clear headings and bullet points.
When requirements are provided, use the summarize_requirements tool first.""",
    tools=[summarize_requirements],
)
