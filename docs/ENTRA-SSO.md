# Microsoft Entra ID single sign-on

The app supports Microsoft Entra ID as an additional sign-in option. Existing email/password login remains available. SSO is restricted to the configured Entra tenant; the backend validates Microsoft's ID-token signature, issuer, audience, tenant, expiry, and nonce before issuing the app's normal session token.

If no app account has the email in the validated Entra ID token, the first successful SSO sign-in creates one without a local password. For an existing account, first sign in with that account's current method, then link Microsoft in **Settings**. The account-link flow requires an authenticated app session and the same email from Microsoft, so an unverified app registration cannot claim an existing account just by matching its email. Users provisioned through SSO sign in through Microsoft. To control who can use SSO, configure the Entra enterprise application to require assignment and assign the intended users or groups.

## Register the app in Microsoft Entra

An Entra administrator or app owner should:

1. Register a new application in the organization's Microsoft Entra tenant.
2. Select **Accounts in this organizational directory only (single tenant)**.
3. Add a **Web** platform redirect URI:

   ```text
   http://localhost:8000/api/auth/entra/callback
   ```

   For a hosted deployment, register the exact public HTTPS URI, for example:

   ```text
   https://qa.example.com/api/auth/entra/callback
   ```

4. Create a client secret and store its value in the backend secret store. Do not put it in frontend configuration or source control.
5. In **Token configuration**, add the `email` optional claim to the ID token. The app requires it to create a new account or verify that an existing account is being linked to the correct Microsoft identity. Microsoft may not include an email claim by default.
6. Copy the **Directory (tenant) ID**, **Application (client) ID**, and secret value.
7. For restricted company access, set the enterprise application to require user assignment and assign the approved users or groups.

The app uses OpenID Connect sign-in scopes (`openid profile email`) only; it does not request Graph API access.

## Configure the app

Set these variables for the backend:

```dotenv
ENTRA_TENANT_ID=<Microsoft Entra directory tenant GUID>
ENTRA_CLIENT_ID=<application client ID>
ENTRA_CLIENT_SECRET=<application client secret>
ENTRA_REDIRECT_URI=https://qa.example.com/api/auth/entra/callback
ENTRA_FRONTEND_URL=https://qa.example.com/login
```

For local Docker Compose:

```dotenv
ENTRA_TENANT_ID=<Microsoft Entra directory tenant GUID>
ENTRA_CLIENT_ID=<application client ID>
ENTRA_CLIENT_SECRET=<application client secret>
ENTRA_REDIRECT_URI=http://localhost:8000/api/auth/entra/callback
ENTRA_FRONTEND_URL=http://localhost:5173/login
```

The callback must exactly match the URI registered in Entra. The backend accepts only a tenant GUID and requires all five settings together. Production callback and frontend URLs must use HTTPS. Keep the client secret in a backend-only secret store such as AWS Secrets Manager.

The database migration adds Entra identity fields, short-lived one-time OAuth state/ticket records, and nullable password hashes for SSO-provisioned accounts. On local Compose, the backend applies migrations on startup. For ECS, run the migration once using the documented migration procedure in [PRODUCTION-ECS.md](./PRODUCTION-ECS.md).

## Sign in

1. If you already have an app account, sign in with your current method, open **Settings**, and select **Link Microsoft account**. Use the same email address in both accounts.
2. Sign out or open the app's **Sign in** page.
3. Select **Sign in with Microsoft** and authenticate with the company account.
4. After successful authentication, the app returns to the dashboard. Password sign-in remains available for accounts that have a password.

OAuth state and PKCE protect the authorization-code flow. The backend stores only digests for state and one-use tickets, validates the ID token against Microsoft's tenant signing keys, and uses the short-lived ticket to return the app session without putting the session token in the URL. OAuth callback query parameters are redacted from Uvicorn access logs; configure load balancers and reverse proxies not to log callback query strings.

## Troubleshooting

- **Microsoft button is missing:** verify all five `ENTRA_*` values are set in the backend and restart/redeploy it.
- **Redirect URI mismatch:** compare `ENTRA_REDIRECT_URI` exactly with the Web redirect URI in the Entra app registration.
- **Email claim missing:** add the `email` optional claim to the ID token's Token configuration, then retry.
- **Access is not allowed:** verify the user belongs to the configured tenant and, if assignment is required, is assigned to the enterprise application.
- **Existing account mismatch:** the email in the Entra ID token must match the app account email. If a different Microsoft identity is already linked to that email, contact the app administrator.
