from google.adk.agents import Agent

from app.agent.capabilities import attach_agent_metadata
from app.callbacks.logger import AGENT_LOG_CALLBACKS
from app.agent.config import ROOT_AGENT_DESCRIPTION, ROOT_AGENT_NAME
from app.agent.prompts.consolidated import build_consolidated_instruction
from app.agent.prompts.root import METADATA as ROOT_AGENT_METADATA
from app.agent.prompts.root import build_root_instruction
from app.agent.registry import REGISTERED_SUB_AGENTS
from app.config.settings import settings
from app.tools import ROOT_TOOLS
from app.utils.llm import resolve_model


def build_root_agent() -> Agent:
    # Local Ollama models often invent tool names instead of using transfer_to_agent.
    # Use a single consolidated agent (no sub-agents) for reliable tool calling.
    use_sub_agents = settings.agent_backend != "ollama"

    agent = Agent(
        model=resolve_model(),
        name=ROOT_AGENT_NAME,
        description=ROOT_AGENT_DESCRIPTION,
        instruction=build_root_instruction() if use_sub_agents else build_consolidated_instruction(),
        tools=ROOT_TOOLS if use_sub_agents else [],
        sub_agents=REGISTERED_SUB_AGENTS if use_sub_agents else [],
        **AGENT_LOG_CALLBACKS,
    )
    attach_agent_metadata(agent, ROOT_AGENT_METADATA)
    return agent
