from app.agent.prompts.stlc import test_execution as prompt
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="test_execution",
    description=prompt.DESCRIPTION,
    instruction=prompt.INSTRUCTION,
    examples=prompt.EXAMPLES,
    metadata=prompt.METADATA,
)
