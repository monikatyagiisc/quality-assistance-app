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
  { step: 'Google Cloud', detail: 'Cloud Run hosts services; Vertex AI / Gemini powers reasoning (see project docs).' },
] as const

export const DIAGRAM_FILES = [
  {
    title: 'Agent architecture (overview)',
    file: '/docs/QualityAssistantAgentArchitecture.drawio',
  },
  {
    title: 'Agent architecture (detailed)',
    file: '/docs/QualityAssistantAgentArchitecture2.drawio',
  },
] as const
