# Connect Jira Cloud with OAuth

The app's Jira issue picker uses Atlassian OAuth 2.0 (3LO). Each app user authorizes their own Atlassian account; the backend stores access and refresh tokens encrypted and queries issues assigned to the signed-in Jira user. Jira credentials are not sent to the AI agent.

The separate Jira MCP settings are for agent-side MCP tools and do not enable this web-app issue picker.

## Requirements

- Jira Cloud access for the users who will test the integration.
- Permission under your organization's Atlassian policy to create or use an OAuth integration. Your Jira administrator may need to approve access.
- A backend callback URL reachable by the user's browser and registered exactly in the Atlassian app.
- A stable backend encryption key (`ENCRYPTION_KEY`) so refresh tokens remain decryptable.

## Create/configure the Atlassian OAuth app

1. Ask the application owner/Atlassian administrator to configure one organization-managed OAuth 2.0 integration using the 3LO (three-legged OAuth) flow. Each app user authorizes that shared app with their own account; testers should not create separate OAuth apps. Atlassian recommends a single distributable integration rather than asking each customer to register a separate app.
2. Add the callback URL. For local development:

   ```text
   http://localhost:8000/api/settings/jira/callback
   ```

   For a hosted deployment, use the public HTTPS API origin and the exact callback path, for example:

   ```text
   https://qa.example.com/api/settings/jira/callback
   ```

3. Add the Jira API scopes:

   ```text
   read:jira-user
   read:jira-work
   offline_access
   ```

   The integration uses `read:jira-user` and `read:jira-work` to identify the authorized Jira user and read assigned issue details. `offline_access` is needed to refresh tokens without asking the user to sign in each time.
4. Copy the OAuth client ID and client secret into the backend environment. Do not commit the secret, send it through chat, or expose it to frontend build variables.
5. Confirm the Jira API is enabled for the app and that the permitted Jira site/users satisfy your organization's approval requirements. During consent, authorize only the intended office Jira site. The app currently requires exactly one accessible Jira site with the needed scopes to avoid selecting the wrong Jira by accident.

Atlassian documentation:

- [OAuth 2.0 (3LO) apps](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [OAuth 2.0 authorization-code grants](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/#implementing-oauth-2-0-authorization-code-grants)
- [Jira Cloud REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)

## Configure the app

Set these variables for the backend service:

```dotenv
JIRA_CLIENT_ID=<Atlassian OAuth client ID>
JIRA_CLIENT_SECRET=<Atlassian OAuth client secret>
JIRA_REDIRECT_URI=https://qa.example.com/api/settings/jira/callback
JIRA_FRONTEND_URL=https://qa.example.com/settings
```

For local Docker Compose, use:

```dotenv
JIRA_REDIRECT_URI=http://localhost:8000/api/settings/jira/callback
JIRA_FRONTEND_URL=http://localhost:5173/settings
```

The redirect URI must match the value registered in the Atlassian developer console exactly. Set `JIRA_FRONTEND_URL` to the page where the user should return after authorization. Restart/redeploy the backend after configuring these values. The database migration is applied by the normal local Compose startup; in ECS, run the migration task documented in the [ECS guide](./PRODUCTION-ECS.md).

## User flow

1. Sign in to the app and open **Settings**.
2. Choose **Connect Jira** and authorize with the corporate Atlassian account.
3. On the workspace, choose **Load my issues**. The app searches issues assigned to the current Jira user and sorts recently updated issues first.
4. Select an issue key. The app fetches its description after checking it is still assigned to you, previews the title and description, and copies them into the **User stories** input. Review or edit the content before submitting.
5. Disconnect Jira from Settings to remove the locally stored encrypted OAuth tokens.

The picker retrieves issue keys, summaries, issue types, and statuses in pages of up to 50. It fetches the description only for the selected issue and confirms that issue is still assigned to the signed-in user. Access remains limited by that user's Jira permissions and the scopes approved for the OAuth app.

## Troubleshooting

- **Jira OAuth is not configured:** verify the backend has all three `JIRA_CLIENT_ID`, `JIRA_CLIENT_SECRET`, and `JIRA_REDIRECT_URI` values.
- **Redirect URL mismatch:** compare the configured `JIRA_REDIRECT_URI` with the Atlassian app callback URL; they must match exactly, including scheme, hostname, path, and trailing slash.
- **No Jira sites or issues:** verify the user has Jira product access, the app was granted the scopes above, and issues are assigned to that same Atlassian identity.
- **Authorization expired:** reconnect Jira from Settings. The app refreshes rotating OAuth tokens automatically; each successful refresh replaces the previous refresh token.
- **Multiple Jira sites authorized:** reconnect and select only the office Jira site; if the consent screen or policy prevents this, ask the Atlassian administrator to review the app's grant/site configuration.
- **Organization approval required:** ask the Jira administrator to review/approve the OAuth integration; do not bypass company SSO or access controls.

Disconnecting in the app removes the locally stored encrypted OAuth tokens. To revoke the Atlassian consent itself, use your Atlassian account's connected-app controls or ask your administrator. The callback contains a short-lived authorization code; the backend redacts its callback query from Uvicorn access logs. Configure any ALB, reverse-proxy, or centralized access logging not to retain callback query parameters.

Do not use a shared service account or paste Jira credentials into issue fields. Use synthetic/demo content unless your organization approves sending Jira descriptions to this app's configured AI provider.
