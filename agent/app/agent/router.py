STLC_ROUTING_INSTRUCTION_FRAGMENT = """Route work to the right specialist based on the user request:
- Requirements or user stories → test case and test data agents
- Code diffs → change impact analysis agent
- Execution logs → test execution, bug report, and summary agents
- Release questions → release readiness agent"""


def build_routing_instruction_fragment() -> str:
    return STLC_ROUTING_INSTRUCTION_FRAGMENT
