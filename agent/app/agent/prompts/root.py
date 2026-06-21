from app.agent.capabilities import AgentCapabilities
from app.agent.prompts.fragments.clarification import FRAGMENT as CLARIFICATION_FRAGMENT
from app.agent.prompts.fragments.requirements_tools import FRAGMENT as REQUIREMENTS_TOOLS_FRAGMENT
from app.agent.registry import REGISTERED_SUB_AGENTS
from app.agent.router import build_routing_instruction_fragment

INSTRUCTION = """You are the Quality Assistance orchestrator for the STLC.

Be concise, actionable, and use clear headings and bullet points.
Synthesize sub-agent expertise when multiple areas apply."""

EXAMPLES = ""

METADATA: AgentCapabilities = {
    "category": "stlc",
    "bucket": "orchestrator",
    "supported_codes": ["ROOT"],
}


def build_root_instruction() -> str:
    agent_names = [agent.name for agent in REGISTERED_SUB_AGENTS]
    return "\n\n".join(
        [
            INSTRUCTION,
            build_routing_instruction_fragment(agent_names),
            REQUIREMENTS_TOOLS_FRAGMENT,
            CLARIFICATION_FRAGMENT,
        ]
    )
