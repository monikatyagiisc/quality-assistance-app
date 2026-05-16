from typing import TypedDict

from google.adk.agents import Agent


class AgentCapabilities(TypedDict):
    category: str
    bucket: str
    supported_codes: list[str]


def attach_agent_metadata(agent: Agent, metadata: AgentCapabilities) -> Agent:
    object.__setattr__(agent, "metadata", metadata)
    return agent


def get_agent_metadata(agent: Agent) -> AgentCapabilities | None:
    value = getattr(agent, "metadata", None)
    if isinstance(value, dict):
        return value  # type: ignore[return-value]
    return None


def collect_capabilities(agents: list[Agent]) -> dict[str, AgentCapabilities]:
    capabilities: dict[str, AgentCapabilities] = {}
    for agent in agents:
        metadata = get_agent_metadata(agent)
        if metadata is not None:
            capabilities[agent.name] = metadata
    return capabilities


def agent_supports_code(agent: Agent, code: str) -> bool:
    metadata = get_agent_metadata(agent)
    if metadata is None:
        return False
    return code.upper() in {c.upper() for c in metadata["supported_codes"]}
