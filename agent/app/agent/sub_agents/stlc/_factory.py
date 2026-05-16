from google.adk.agents import Agent

from app.agent.capabilities import AgentCapabilities, attach_agent_metadata
from app.agent.prompts._helpers import build_instruction
from app.utils.llm import resolve_model


def build_stlc_agent(
    *,
    name: str,
    description: str,
    instruction: str,
    examples: str = "",
    metadata: AgentCapabilities | None = None,
) -> Agent:
    agent = Agent(
        model=resolve_model(),
        name=name,
        description=description,
        instruction=build_instruction(instruction, examples),
    )
    if metadata is not None:
        attach_agent_metadata(agent, metadata)
    return agent
