from app.agent.prompts.stlc import release_readiness_evaluation as prompt
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="release_readiness_evaluation",
    description=prompt.DESCRIPTION,
    instruction=prompt.INSTRUCTION,
    examples=prompt.EXAMPLES,
    metadata=prompt.METADATA,
)
