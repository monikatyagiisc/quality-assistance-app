STLC_ROUTING_INSTRUCTION_FRAGMENT = """Route work to the right specialist based on the user request:
- Requirements or user stories → test case and test data agents
- Code diffs → change impact analysis agent
- Execution logs → test execution, bug report, and summary agents
- Release questions → release readiness agent"""


def build_sub_agent_names_fragment(agent_names: list[str]) -> str:
    quoted = ", ".join(f'"{name}"' for name in agent_names)
    return f"""Delegation rules (mandatory):
- Hand off work using ONLY the transfer_to_agent tool.
- Never invent tool names (e.g. do not call generate_test_cases or similar).
- Valid agent_name values: {quoted}.
- Your only other callable tool is summarize_requirements."""


def build_routing_instruction_fragment(agent_names: list[str] | None = None) -> str:
    parts = [STLC_ROUTING_INSTRUCTION_FRAGMENT]
    if agent_names:
        parts.append(build_sub_agent_names_fragment(agent_names))
    return "\n\n".join(parts)
