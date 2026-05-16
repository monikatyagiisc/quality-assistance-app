from app.agent.capabilities import collect_capabilities
from app.agent.sub_agents.stlc.bug_report_generation import agent as bug_report_generation
from app.agent.sub_agents.stlc.change_impact_analysis import agent as change_impact_analysis
from app.agent.sub_agents.stlc.release_readiness_evaluation import agent as release_readiness_evaluation
from app.agent.sub_agents.stlc.self_healing_test_scripts import agent as self_healing_test_scripts
from app.agent.sub_agents.stlc.test_case_generation import agent as test_case_generation
from app.agent.sub_agents.stlc.test_data_generation import agent as test_data_generation
from app.agent.sub_agents.stlc.test_execution import agent as test_execution
from app.agent.sub_agents.stlc.test_script_automation import agent as test_script_automation
from app.agent.sub_agents.stlc.test_summary_reporting import agent as test_summary_reporting

REGISTERED_SUB_AGENTS = [
    test_case_generation,
    test_data_generation,
    test_script_automation,
    test_execution,
    self_healing_test_scripts,
    change_impact_analysis,
    bug_report_generation,
    test_summary_reporting,
    release_readiness_evaluation,
]

REGISTERED_AGENT_CAPABILITIES = collect_capabilities(REGISTERED_SUB_AGENTS)
