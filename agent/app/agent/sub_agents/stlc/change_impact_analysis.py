from app.agent.prompts.stlc import change_impact_analysis as prompt
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="change_impact_analysis",
    description=prompt.DESCRIPTION,
    instruction=prompt.INSTRUCTION,
    examples=prompt.EXAMPLES,
    metadata=prompt.METADATA,
)
