from app.agent.prompts.stlc import test_summary_reporting as prompt
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="test_summary_reporting",
    description=prompt.DESCRIPTION,
    instruction=prompt.INSTRUCTION,
    examples=prompt.EXAMPLES,
    metadata=prompt.METADATA,
)
