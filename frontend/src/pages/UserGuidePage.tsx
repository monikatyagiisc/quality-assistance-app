import { useRef } from 'react'
import { Link } from 'react-router-dom'
import baseStyles from '../index.css?inline'
import guideStyles from './UserGuidePage.css?inline'
import './UserGuidePage.css'

const guideSections = [
  ['what-it-does', 'What this application does'],
  ['before-you-start', 'Before you start'],
  ['create-account', 'Create your account and sign in'],
  ['first-run', 'Run your first quality review'],
  ['inputs', 'Understand the input fields'],
  ['jira', 'Use Jira to import a story'],
  ['github', 'Connect GitHub and import a code change'],
  ['results', 'Read, download, and continue results'],
  ['settings', 'Manage settings and connections'],
  ['workflows', 'Things you can do with the assistant'],
  ['privacy', 'Data, safety, and good practices'],
  ['troubleshooting', 'Troubleshooting'],
]

export function UserGuidePage() {
  const guideRef = useRef<HTMLElement>(null)

  const downloadGuide = () => {
    const guide = guideRef.current?.cloneNode(true)
    if (!(guide instanceof HTMLElement)) return

    guide.querySelector('[data-guide-download]')?.remove()
    const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Quality Assistance — User Guide</title>
  <style>
${baseStyles}
${guideStyles}
  </style>
</head>
<body>
  ${guide.outerHTML}
</body>
</html>`
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `quality-assistance-user-guide-${new Date().toISOString().slice(0, 10)}.html`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return (
    <article className="user-guide" ref={guideRef}>
      <header className="guide-hero">
        <p className="eyebrow">First-time user guide</p>
        <h1>Your step-by-step guide to Quality Assistance</h1>
        <p className="guide-lead">
          Learn what the application can do, how to get started, and how to turn requirements,
          Jira stories, code changes, and test results into practical quality-engineering guidance.
          No testing or AI experience is required.
        </p>
        <div className="guide-hero-actions">
          <Link to="/register" className="btn btn-primary btn-lg">Create an account</Link>
          <Link to="/login" className="btn btn-ghost btn-lg">I already have an account</Link>
          <button
            type="button"
            className="btn btn-ghost btn-lg"
            data-guide-download
            onClick={downloadGuide}
          >
            Download HTML guide
          </button>
        </div>
      </header>

      <nav className="guide-toc panel" aria-label="On this page">
        <h2>On this page</h2>
        <ol>
          {guideSections.map(([id, title]) => (
            <li key={id}><a href={`#${id}`}>{title}</a></li>
          ))}
        </ol>
      </nav>

      <section id="what-it-does" className="guide-section">
        <p className="eyebrow">Overview</p>
        <h2>What this application does</h2>
        <p>
          Quality Assistance is an AI-powered helper for software quality engineering. You provide
          context about a feature or change; the application sends that context to its configured
          AI service, where specialized assistants generate suggestions and analysis.
        </p>
        <div className="guide-card-grid">
          <article className="guide-card">
            <h3>Plan tests</h3>
            <p>Turn requirements and user stories into test scenarios, priorities, and coverage ideas.</p>
          </article>
          <article className="guide-card">
            <h3>Explore test data</h3>
            <p>Suggest normal, boundary, invalid, and other useful data values for test scenarios.</p>
          </article>
          <article className="guide-card">
            <h3>Plan automation</h3>
            <p>Get automation approaches, script outlines, and ideas for handling changed selectors.</p>
          </article>
          <article className="guide-card">
            <h3>Analyze changes and failures</h3>
            <p>Review code diffs or test-run logs for possible impact, defects, and follow-up checks.</p>
          </article>
          <article className="guide-card">
            <h3>Summarize quality</h3>
            <p>Create test summaries and release-readiness considerations for people to review.</p>
          </article>
        </div>
        <div className="guide-callout guide-callout-warn">
          <strong>Important:</strong> The application generates AI suggestions; it does not run your
          product’s test suite or make a release decision. Review and verify every result with your
          team and your actual system.
        </div>
      </section>

      <section id="before-you-start" className="guide-section">
        <p className="eyebrow">Preparation</p>
        <h2>Before you start</h2>
        <ul className="guide-list">
          <li>Use a supported, up-to-date web browser and the application URL provided by your team.</li>
          <li>Have a short feature description, acceptance criteria, or test evidence ready. You can start with one of the built-in samples instead.</li>
          <li>Account creation and sign-in must be enabled by the application administrator.</li>
          <li>
            Jira, Microsoft SSO, and GitHub are optional integrations. They appear only after an
            administrator configures the corresponding integration for this deployment.
          </li>
          <li>
            Use only information that your organization permits you to share with this application
            and its configured AI provider.
          </li>
        </ul>
        <p>
          If you are new to the tool, you can skip integrations and use a sample or enter a
          requirement manually.
        </p>
      </section>

      <section id="create-account" className="guide-section">
        <p className="eyebrow">Step 1</p>
        <h2>Create your account and sign in</h2>
        <ol className="guide-steps">
          <li>Open the application and choose <strong>Get started</strong> or <strong>Create an account</strong>.</li>
          <li>Enter your name, work email, and a password that meets the form’s minimum length.</li>
          <li>Choose <strong>Create account</strong>. After registration, the app opens your workspace.</li>
        </ol>
        <p>
          If your organization has enabled Microsoft Entra ID, you can use <strong>Sign in with
            Microsoft</strong>. Existing app accounts may need to sign in once with their current
          method and link the same-email Microsoft account in <strong>Settings</strong> first.
          Otherwise, use your app email and password. Select <strong>Sign out</strong> from your
          profile menu when you finish on a shared device.
        </p>
      </section>

      <section id="first-run" className="guide-section">
        <p className="eyebrow">Step 2</p>
        <h2>Run your first quality review</h2>
        <ol className="guide-steps">
          <li>
            Open <strong>Workspace</strong>. The workspace has separate <strong>Input</strong> and
            <strong> Results</strong> tabs.
          </li>
          <li>
            For an easy first try, select a sample card such as <strong>Smoke test</strong> or
            <strong>Full E2E demo</strong>. The sample fills in the form; it does not run until you
            submit.
          </li>
          <li>
            Or type your own feature description in <strong>Software requirements</strong>. Include
            what should happen, who uses the feature, important rules, and acceptance criteria.
          </li>
          <li>
            Optionally add a user story or code change. See <a href="#inputs">Understand the input fields</a>.
          </li>
          <li>
            Choose <strong>Get quality assistance</strong>. The Results tab opens and shows progress
            while the assistant works.
          </li>
          <li>
            Read the response, check assumptions, and refine your input or ask a follow-up if needed.
          </li>
        </ol>
        <div className="guide-callout">
          <strong>Tip:</strong> More context usually gives more relevant suggestions. State
          constraints explicitly—for example supported browsers, roles, data rules, error behavior,
          or out-of-scope areas.
        </div>
      </section>

      <section id="inputs" className="guide-section">
        <p className="eyebrow">Workspace basics</p>
        <h2>Understand the input fields</h2>
        <div className="guide-table-wrap">
          <table className="guide-table">
            <thead>
              <tr><th>Field</th><th>What to enter</th><th>Required?</th></tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Software requirements</th>
                <td>Feature behavior, business rules, acceptance criteria, and constraints. This is the main description of what you want reviewed.</td>
                <td>Yes</td>
              </tr>
              <tr>
                <th scope="row">User stories</th>
                <td>One or more user stories that explain the user, their goal, and its value. A selected Jira issue can be copied here for you.</td>
                <td>No</td>
              </tr>
              <tr>
                <th scope="row">Code diffs</th>
                <td>A code change to review for impact and regression scope. Paste a diff or fetch one from the configured GitHub repository.</td>
                <td>No</td>
              </tr>
            </tbody>
          </table>
        </div>
        <h3>Built-in sample requests</h3>
        <ul className="guide-list">
          <li><strong>Smoke test:</strong> a small example for trying requirement analysis.</li>
          <li><strong>Full E2E demo:</strong> a sample with requirements, user stories, and a sample code diff.</li>
          <li><strong>All agents demo:</strong> a sample with requirements, a test run log, a locator change, user stories, and a code diff, written to ask for all nine specialists.</li>
          <li><strong>Change impact:</strong> an example focused on reviewing a code change.</li>
          <li><strong>Execution &amp; reporting:</strong> sample test-run results to analyze and summarize.</li>
          <li><strong>Automation &amp; self-healing:</strong> example automation context and selector changes.</li>
          <li><strong>Follow-up (same session):</strong> a refinement request that uses an earlier response in the current session.</li>
        </ul>
        <p>
          Samples are starting points, not fixed tests. After loading a sample, edit any field to
          fit your scenario. Choose <strong>Clear</strong> to clear the current inputs and result.
        </p>
      </section>

      <section id="jira" className="guide-section">
        <p className="eyebrow">Optional integration</p>
        <h2>Use Jira to import a story</h2>
        <p>
          When Jira Cloud OAuth has been configured, you can connect your own Atlassian account and
          load issues assigned to you. The issue picker imports a story’s key, title, and
          description into the user-story field.
        </p>
        <ol className="guide-steps">
          <li>Open your profile menu and choose <strong>Settings</strong>.</li>
          <li>Under <strong>Jira Cloud</strong>, choose <strong>Connect Jira</strong>.</li>
          <li>Sign in to Atlassian with the account that can access your company Jira site and approve the requested access.</li>
          <li>Return to <strong>Workspace → Input</strong>, then choose <strong>Load my issues</strong>.</li>
          <li>Select an issue from the dropdown. Review its preview; the title and description are copied into <strong>User stories</strong>.</li>
          <li>Review or edit the imported text before submitting. Use <strong>Load more issues</strong> if the issue is not on the first page.</li>
        </ol>
        <p>
          The issue must be assigned to the Jira account you authorized and visible to that account.
          If the Jira section says it is not configured, contact your application or Atlassian
          administrator; a Jira URL by itself does not connect the integration.
        </p>
      </section>

      <section id="github" className="guide-section">
        <p className="eyebrow">Optional integration</p>
        <h2>Connect GitHub and import a code change</h2>
        <p>
          GitHub import is useful when you want change-impact suggestions based on a pull request or
          branch comparison. The app does not clone your repository.
        </p>
        <ol className="guide-steps">
          <li>Open <strong>Settings → GitHub repository</strong>.</li>
          <li>Enter the repository owner or organization, repository name, and base branch (usually <code>main</code>).</li>
          <li>Enter a GitHub personal access token with read access to repository contents and pull requests, then save the repository.</li>
          <li>Return to the workspace and enter your requirement and story context.</li>
          <li>Under <strong>Code diffs</strong>, choose <strong>From GitHub</strong>, enter a pull request number or a head branch/commit SHA, then choose <strong>Import diff into form</strong>.</li>
          <li>Review the imported diff and choose <strong>Get quality assistance</strong>.</li>
        </ol>
        <p>
          The <strong>Paste</strong> option is available for supplying diff text in the workspace,
          but this deployment currently requires a saved GitHub repository and token before accepting
          non-empty diff content. If you only want requirement or story analysis, leave Code diffs
          blank.
        </p>
        <p>
          To replace or remove the saved repository connection, return to Settings. The token is
          stored by the backend and is not displayed again after saving.
        </p>
      </section>

      <section id="results" className="guide-section">
        <p className="eyebrow">Step 3</p>
        <h2>Read, download, and continue results</h2>
        <ul className="guide-list">
          <li>Open the <strong>Results</strong> tab if it is not already selected. Responses are rendered with headings, lists, tables, and code formatting.</li>
          <li>Use <strong>Markdown</strong> to save a portable Markdown copy or <strong>HTML</strong> to save a web page you can open or print.</li>
          <li>Use the current result and its session context to ask for a refinement, such as prioritizing critical cases or adding negative tests.</li>
          <li>Choose <strong>New session</strong> to clear the current session context and begin a separate request. This does not delete a previously downloaded file.</li>
        </ul>
        <div className="guide-callout guide-callout-warn">
          Results are generated guidance, not a record of tests executed by the application.
          Validate test cases, scripts, defects, and release recommendations before using them.
        </div>
      </section>

      <section id="settings" className="guide-section">
        <p className="eyebrow">Account and connections</p>
        <h2>Manage settings and connections</h2>
        <p>
          Open the profile menu in the upper-right corner and select <strong>Settings</strong>.
          Depending on what your administrator has enabled, you may see:
        </p>
        <ul className="guide-list">
          <li><strong>Jira Cloud:</strong> connect, reconnect, or disconnect your Atlassian account.</li>
          <li><strong>Microsoft Entra ID:</strong> link the same-email company account to your app account so you can use Microsoft SSO at the next sign-in.</li>
          <li><strong>GitHub repository:</strong> save or update the repository, base branch, and token for diff imports, or remove that connection.</li>
        </ul>
        <p>
          Settings show whether a connection is configured or linked. If an integration is not
          available, ask the application administrator whether its credentials, callback URL, and
          database setup are ready.
        </p>
      </section>

      <section id="workflows" className="guide-section">
        <p className="eyebrow">Ideas to try</p>
        <h2>Things you can do with the assistant</h2>
        <div className="guide-card-grid">
          <article className="guide-card">
            <h3>Design test cases</h3>
            <p>Provide acceptance criteria and ask for functional, negative, boundary, and accessibility checks.</p>
          </article>
          <article className="guide-card">
            <h3>Generate data ideas</h3>
            <p>Ask for representative, edge, invalid, and boundary values tied to specific test cases.</p>
          </article>
          <article className="guide-card">
            <h3>Review a pull request</h3>
            <p>Provide requirements plus a diff to identify affected areas and a focused regression scope.</p>
          </article>
          <article className="guide-card">
            <h3>Analyze a test run</h3>
            <p>Paste a test log or result summary in the requirement field and ask for failure triage and next steps.</p>
          </article>
          <article className="guide-card">
            <h3>Plan test automation</h3>
            <p>Describe the framework and application behavior, then ask for maintainable automation ideas.</p>
          </article>
          <article className="guide-card">
            <h3>Prepare a quality summary</h3>
            <p>Share verified test outcomes and known risks, then request a stakeholder-friendly summary.</p>
          </article>
        </div>
        <p>
          The exact response depends on the information you provide and the AI model configured by
          your administrator. Ask one clear question at a time, and request a table or checklist if
          that format is easier to use.
        </p>
      </section>

      <section id="privacy" className="guide-section">
        <p className="eyebrow">Responsible use</p>
        <h2>Data, safety, and good practices</h2>
        <ul className="guide-list">
          <li>Do not enter passwords, access tokens, private keys, customer personal data, or other secrets in requirements, stories, diffs, or test logs.</li>
          <li>Follow your organization’s rules for sharing Jira content, source code, and test data with the configured AI provider.</li>
          <li>Connected integrations operate with the permissions of your authorized account; only connect accounts and repositories you are allowed to use.</li>
          <li>Review generated test steps and scripts before running them. Check for inaccurate assumptions, missing security coverage, and unsafe commands.</li>
          <li>Keep important results by downloading them; the workspace is designed for the current session and does not provide a searchable results archive.</li>
        </ul>
      </section>

      <section id="troubleshooting" className="guide-section">
        <p className="eyebrow">Need help?</p>
        <h2>Troubleshooting</h2>
        <dl className="guide-troubleshooting">
          <dt>I cannot create an account or sign in.</dt>
          <dd>Check your email and password. If your organization uses Microsoft SSO, try Sign in with Microsoft; an existing account may first need to be linked in Settings. Contact your app administrator if the option is missing.</dd>
          <dt>The Jira or Microsoft connection option is missing or unavailable.</dt>
          <dd>The administrator must configure the provider credentials, exact callback URL, and required database migration. Do not try to work around organization approval.</dd>
          <dt>My Jira issue does not appear.</dt>
          <dd>Reconnect the correct Atlassian account, refresh the issue list, and confirm the issue is assigned to that user and visible to them.</dd>
          <dt>GitHub diff import fails.</dt>
          <dd>Check the saved owner, repository, base branch, token permissions, and pull request number or head branch/SHA. Ask an administrator to verify network access if the issue continues.</dd>
          <dt>The response is slow or an error appears.</dt>
          <dd>Wait for the request to finish, check that the application services are available, then retry with a shorter input. If it persists, share the error text with your administrator without including secrets or sensitive work content.</dd>
          <dt>The answer is incomplete or incorrect.</dt>
          <dd>Add missing constraints or examples, ask a focused follow-up, and verify recommendations against your requirements and actual system.</dd>
        </dl>
      </section>

      <footer className="guide-ending panel">
        <h2>Ready to begin?</h2>
        <p>Start with a sample, learn the workspace, and then try one of your own requirements.</p>
        <Link to="/dashboard" className="btn btn-primary">Open workspace</Link>
      </footer>
    </article>
  )
}
