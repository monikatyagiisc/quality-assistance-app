from app.agent.descriptions.stlc import test_script_automation as desc
from app.agent.instructions.stlc import test_script_automation as instr
from app.agent.sub_agents.stlc._factory import build_stlc_agent

agent = build_stlc_agent(
    name="test_script_automation",
    description=desc.DESCRIPTION,
    instruction=instr.INSTRUCTION,
)
