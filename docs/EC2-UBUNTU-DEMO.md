# Demo deployment on one Ubuntu EC2 instance

This guide deploys the frontend, backend, agent, and PostgreSQL on one Ubuntu EC2 instance using Docker Compose. It is intended for a presentation or a small, time-limited test group, not a production service. The instance is a single point of failure, and the database shares its disk with the application.

## What you will run

```text
Tester browser
    |
    | HTTPS (80/443)
    v
Caddy reverse proxy
    |-- /api/* -> backend container (8000)
    `-- everything else -> frontend container (8080)

Backend -> PostgreSQL container (5432)
Backend -> agent container (8001)
Agent -> Amazon Bedrock
```

Resources: one Ubuntu EC2 instance, one EBS volume, one EC2 instance profile for Bedrock, and optionally a domain name and DNS record. PostgreSQL runs as a Compose service and stores its files in the `postgres_data` named volume.

## Checklist: collect these before starting

### AWS access and instance details

- [ ] AWS account and target region.
- [ ] Permission to create/start EC2 instances, security groups, instance profiles, and (if needed) Elastic IPs.
- [ ] Ubuntu 24.04 LTS AMI, instance type, and disk size approved by your administrator. A useful starting point for this four-container demo is 2 vCPU, 8 GiB RAM, and 30-50 GiB gp3 EBS.
- [ ] A way to connect: an SSH key pair with the private key stored safely, or an approved Systems Manager Session Manager setup.
- [ ] VPC and subnet selection, and whether outbound internet access is available for package/image downloads and Bedrock.
- [ ] Public IP or Elastic IP for the instance.

### Network access

- [ ] Security group allows SSH on port 22 only from your own IP, or allows the approved Session Manager path.
- [ ] Security group allows HTTP 80 and HTTPS 443 from the tester audience.
- [ ] No inbound rules for PostgreSQL 5432, agent 8001, backend 8000, or frontend 5173.
- [ ] For an EC2 instance profile accessed by containers, configure the instance metadata options so IMDSv2 responses have a hop limit of 2. Use a narrowly scoped instance role because containers on this host may be able to access it.

### Bedrock and application

- [ ] The chosen Bedrock model or inference profile is enabled and available in the selected region/account.
- [ ] An EC2 instance profile with least-privilege permission to invoke only the approved Bedrock model/profile.
- [ ] The model ID, e.g. `openai.gpt-oss-120b-1:0`, confirmed in the target region/account.
- [ ] A domain name and a DNS A/AAAA record pointing to the instance if you want Caddy to issue HTTPS automatically. Without a domain, restrict the demo to a controlled network; do not collect real passwords over plain HTTP.
- [ ] A Git checkout/deploy method for this repository. For a private repository, use an approved SSH deploy key or other organization-approved method; do not place a personal access token in a clone URL.

## AWS and software documentation to consult

These are the external references needed for the AWS-side setup. Follow current AWS guidance and your organization's policies:

1. [Launch an EC2 instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/LaunchingAndUsingInstances.html) - AMI, instance type, storage, key pair, and metadata options.
2. [EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html) - restrict SSH and web traffic.
3. [IAM roles for EC2](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html) - attach an instance profile rather than storing AWS keys on the VM.
4. [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) and [Bedrock IAM actions](https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonbedrock.html) - verify model access and scope the role.
5. [EC2 instance metadata options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html) - require IMDSv2 and set the container-compatible response hop limit.
6. [Elastic IP addresses](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html) - optional stable public IP.
7. [Route 53 DNS records](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/rrsets-working-with.html) - optional domain-to-instance mapping.
8. [Install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) - install Docker and the Compose plugin.
9. [Caddy installation](https://caddyserver.com/docs/install) - install the reverse proxy from its official package source.

## 1. Launch and secure the instance

Launch the approved Ubuntu instance with the settings from the checklist. Attach the Bedrock instance profile. Require IMDSv2; when Docker containers need the instance profile, set the metadata response hop limit to 2. Ensure the role contains only the Bedrock actions/resources needed by this demo.

Configure the security group before launching:

| Port | Source | Purpose |
|---|---|---|
| 22 | Your IP only, or omit if using Session Manager | Administration |
| 80 | Tester network or internet if using public DNS/ACME | HTTP redirect and certificate validation |
| 443 | Tester network or internet | HTTPS application access |

Do not open ports 5432, 8000, 8001, or 5173 to the public internet.

## 2. Install Docker and retrieve the code

Connect to the instance using SSH or Session Manager, then install Docker Engine and its Compose plugin using the official Docker Ubuntu instructions linked above. Verify the installation:

```bash
docker --version
docker compose version
sudo systemctl enable --now docker
```

For convenience, you can add your login user to the Docker group:

```bash
sudo usermod -aG docker "$USER"
```

Log out and reconnect before using Docker without `sudo`. Membership in the Docker group is effectively root-level access, so only do this for a trusted admin account.

Clone the repository into the admin user's home directory:

```bash
cd ~
git clone <approved-repository-url>
cd quality-assistance-app
```

## 3. Make the Compose file suitable for the EC2 demo

The checked-in [docker-compose.yml](../docker-compose.yml) is for local development. It contains default database credentials and publishes internal service ports. Before running it on EC2, edit it as follows:

1. In `postgres.environment`, replace the fixed user, password, and database with:

   ```yaml
   POSTGRES_USER: ${DB_USER}
   POSTGRES_PASSWORD: ${DB_PASSWORD}
   POSTGRES_DB: ${DB_NAME}
   ```

2. In `backend.environment`, replace the fixed database user/password/name with:

   ```yaml
   DB_USER: ${DB_USER}
   DB_PASSWORD: ${DB_PASSWORD}
   DB_NAME: ${DB_NAME}
   ```

   Keep `DB_HOST: postgres` and `DB_PORT: 5432`; Compose provides private service-to-service DNS. Set `RUN_MIGRATIONS: "true"` for this single-instance demo so the backend applies migrations on startup.

3. Remove the `ports` section from the `postgres` service and remove the `ports` section from the `agent` service. They do not need host-published ports.

4. Bind the backend and frontend only to the local host so Caddy is the only internet-facing process:

   ```yaml
   # backend
   ports:
     - "127.0.0.1:8000:8000"

   # frontend
   ports:
     - "127.0.0.1:5173:8080"
   ```

5. In `agent.environment`, remove `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN`. Set:

   ```yaml
   AWS_USE_IAM_ROLE: "true"
   ```

   Keep `AWS_REGION_NAME`. This lets the agent use the EC2 instance profile rather than long-lived AWS credentials.

6. Set `API_DOCS_ENABLED: "false"` and use a non-default JWT secret and encryption key in the backend environment file described below. Keep `APP_ENV` as `development` for this single-host Compose setup: the backend's strict production mode requires a TLS-enabled database, which this local Compose PostgreSQL setup does not configure. HTTPS from browser to Caddy is still recommended.

Validate the edited configuration before starting containers:

```bash
docker compose config --quiet
```

## 4. Configure secrets and model settings

Create a root `.env` file. It is ignored by Git; do not commit it or paste secrets into tickets/chat:

```bash
nano .env
```

Example values:

```dotenv
DB_USER=quality_assistance
DB_NAME=quality_assistance
DB_PASSWORD=<unique-random-database-password>

JWT_SECRET=<unique-random-secret-at-least-32-characters>
ENCRYPTION_KEY=<valid-Fernet-key>

AGENT_BACKEND=bedrock
AGENT_MODEL=openai.gpt-oss-120b-1:0
AWS_USE_IAM_ROLE=true
AWS_REGION_NAME=us-east-1

API_DOCS_ENABLED=false
CORS_ORIGINS=https://qa.example.com
VITE_API_URL=https://qa.example.com

# Optional Jira Cloud OAuth (follow docs/JIRA-CLOUD-OAUTH.md)
JIRA_CLIENT_ID=<Atlassian OAuth client ID>
JIRA_CLIENT_SECRET=<Atlassian OAuth client secret>
JIRA_REDIRECT_URI=https://qa.example.com/api/settings/jira/callback
JIRA_FRONTEND_URL=https://qa.example.com/settings

# Optional Microsoft Entra single sign-on (follow docs/ENTRA-SSO.md)
ENTRA_TENANT_ID=<Microsoft Entra tenant GUID>
ENTRA_CLIENT_ID=<Microsoft Entra application client ID>
ENTRA_CLIENT_SECRET=<Microsoft Entra client secret>
ENTRA_REDIRECT_URI=https://qa.example.com/api/auth/entra/callback
ENTRA_FRONTEND_URL=https://qa.example.com/login
```

Replace the example model and region with values actually enabled in your account. Generate secrets locally on the instance:

```bash
openssl rand -hex 32
python3 -c 'import base64,secrets; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())'
```

Use the first output for `JWT_SECRET` and the second for `ENCRYPTION_KEY`. Keep the encryption key backed up and unchanged; rotating it without a migration makes previously encrypted repository credentials unreadable.

The frontend embeds `VITE_API_URL` at build time. Set it to the public site origin (no `/api` suffix), such as `https://qa.example.com`; the app adds `/api/...` to its requests.
For Jira OAuth, configure the same `JIRA_REDIRECT_URI` in the Atlassian app and keep `JIRA_CLIENT_SECRET` only in the backend environment. For Microsoft Entra SSO, register `ENTRA_REDIRECT_URI` in the Entra app and keep `ENTRA_CLIENT_SECRET` backend-only. The Compose backend service passes both sets of variables through from the root `.env`.

## 5. Install and configure Caddy for HTTPS

Point the domain's DNS A record to the instance's public/Elastic IP and allow inbound 80 and 443. Install Caddy using its official Ubuntu instructions linked above. Configure `/etc/caddy/Caddyfile`:

```caddyfile
qa.example.com {
    @api path /api/*
    reverse_proxy @api 127.0.0.1:8000
    reverse_proxy 127.0.0.1:5173
}
```

Replace `qa.example.com` with your domain, validate and reload:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Caddy will request and renew a certificate when DNS points to this instance and the required network access is available. If you have no domain, do not claim the plain-HTTP setup is safe for real credentials; use a VPN or limit access to the demo audience/network.

## 6. Build, start, and test the services

From the repository root:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Watch startup logs:

```bash
docker compose logs --tail=100 postgres backend agent frontend
```

Check backend readiness from the instance:

```bash
curl -fsS http://127.0.0.1:8000/ready
```

Then open `https://qa.example.com`, create a test account, and submit a representative request. `/ready` checks the database and agent health; the representative request verifies the agent can call Bedrock.

## 7. Data, updates, and troubleshooting

PostgreSQL data persists in the `postgres_data` Docker volume on the instance's EBS disk. Back it up before significant demos or updates:

```bash
mkdir -p ~/quality-assistance-backups
docker compose exec -T postgres sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "$HOME/quality-assistance-backups/db-$(date +%F-%H%M).sql"
```

Copy backups off the instance if you need protection from instance/disk loss. Never run `docker compose down -v` unless you intend to delete the database volume.

To update the app, pull the approved revision and rebuild:

```bash
git pull
docker compose up -d --build
docker compose ps
```

Useful checks:

```bash
docker compose logs -f backend agent
docker compose exec postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
curl -fsS http://127.0.0.1:8000/ready
```

If Bedrock calls fail, verify the instance profile is attached, IMDSv2 is enabled and reachable from the agent container, the region/model ID are correct, and the model is enabled for the account. Do not solve credential errors by adding permanent AWS keys to `.env`.

## Scope and limitations

- One EC2 instance means downtime during host maintenance or failure; all app services and database share its resources.
- The Compose PostgreSQL volume is not a managed backup or high-availability solution.
- Use only synthetic/demo data unless the application's data handling has been reviewed and approved.
- This guide is separate from the multi-service managed deployment in [PRODUCTION-ECS.md](./PRODUCTION-ECS.md).
