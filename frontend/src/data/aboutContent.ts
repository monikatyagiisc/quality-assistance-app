/** Content derived from docs/QualityAssistantAgentArchitecture*.drawio */

export const AGENTS = [
  {
    name: 'Test Case Generation',
    description: 'Turns requirements and user stories into structured, prioritized test cases.',
  },
  {
    name: 'Test Data Generation',
    description: 'Produces realistic datasets and edge-case values aligned with each scenario.',
  },
  {
    name: 'Test Script Automation',
    description: 'Suggests automation approaches and script outlines for repeatable execution.',
  },
  {
    name: 'Test Execution',
    description: 'Simulates and summarizes test runs to surface failures early.',
  },
  {
    name: 'Self-Healing Test Scripts',
    description: 'Adapts scripts when UI or API elements change between builds.',
  },
  {
    name: 'Change Impact Analysis',
    description: 'Maps code diffs to affected modules and regression scope.',
  },
  {
    name: 'Bug Report Generation',
    description: 'Structures raw failures into actionable defect reports.',
  },
  {
    name: 'Test Summary Reporting',
    description: 'Aggregates execution results into stakeholder-ready summaries.',
  },
  {
    name: 'Release Readiness Evaluation',
    description: 'Weighs quality signals and risks before go-live decisions.',
  },
] as const

export const ARCHITECTURE_FLOW = [
  { step: 'User', detail: 'Submits requirements, stories, and optional code diffs via the web app.' },
  { step: 'Orchestrator', detail: 'Routes work across the STLC pipeline based on context and inputs.' },
  { step: 'Quality Assistant', detail: 'Specialized agents collaborate on planning, execution, and reporting.' },
  {
    step: 'LLM provider',
    detail:
      'Configurable model backend (Gemini, OpenAI via LiteLLM, Anthropic, and others) powers agent reasoning.',
  },
] as const

export const ARCHITECTURE_DIAGRAM = {
  title: 'Agent architecture',
  description:
    'User and test data flow through orchestration into specialist STLC agents backed by an LLM provider.',
  image: '/docs/quality-assistant-agent-architecture.png',
  sourceDrawio: '/docs/QualityAssistantAgentArchitecture.drawio',
}

export const E2E_SEQUENCE_DIAGRAM = {
  title: 'End-to-end request flow',
  description: 'Register, assist, and agent orchestration across frontend, backend, and agent services.',
  previewSvg: '/docs/quality-assistance-e2e-sequence.svg',
}
