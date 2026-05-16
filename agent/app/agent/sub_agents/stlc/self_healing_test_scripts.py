from app.agent.prompts.stlc import self_healing_test_scripts as prompt
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="self_healing_test_scripts",
    description=prompt.DESCRIPTION,
    instruction=prompt.INSTRUCTION,
    examples=prompt.EXAMPLES,
    metadata=prompt.METADATA,
)
