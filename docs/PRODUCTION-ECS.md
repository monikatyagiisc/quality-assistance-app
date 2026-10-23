# Production deployment on AWS ECS

This is a deployment checklist for the current app, not a ready-to-apply ECS stack. Account IDs, VPCs, domains, certificates, image repositories, and organization policies are environment-specific and should be supplied by the AWS administrator.

## Recommended architecture

- **Frontend:** ECS service behind an HTTPS Application Load Balancer (ALB); only the ALB is public.
- **Backend API:** private ECS service, reachable from the ALB and frontend's browser API route.
- **Agent:** private ECS service, reachable only by the backend.
- **Database:** Amazon RDS for PostgreSQL in private subnets, with automated backups and encryption enabled.
- **Secrets:** AWS Secrets Manager or SSM Parameter Store; never bake `.env` files into images or task definitions.
- **Images:** build and scan versioned images, push them to Amazon ECR, and deploy immutable image digests.

Configure ALB routing so `/api/*` reaches the backend and all other application routes reach the frontend. Set the frontend build argument `VITE_API_URL` to the public HTTPS origin (for example `https://qa.example.com`) so browser requests use the ALB's `/api` route. Set backend `CORS_ORIGINS` to that exact HTTPS origin. Do not expose the agent or database ports publicly.

## ECS task configuration

Use separate task definitions/services for frontend, backend, and agent. Set container ports to `8080`, `8000`, and `8001` respectively. Configure ECS health checks against frontend `/`, backend `/ready`, and agent `/health`. Give containers CPU, memory, ephemeral storage, and autoscaling settings appropriate for the selected model and measured workload.

### Backend environment

Set these as task environment values:

```text
APP_ENV=production
DB_HOST=<RDS endpoint>
DB_PORT=5432
DB_USER=<application database user>
DB_NAME=<application database>
DB_SSL=true
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
AGENT_SERVICE_URL=http://<private-agent-service>:8001
CORS_ORIGINS=https://<application-domain>
RUN_MIGRATIONS=false
API_DOCS_ENABLED=false
```

Inject `DB_PASSWORD`, `JWT_SECRET`, and `ENCRYPTION_KEY` from Secrets Manager. Generate unique production values, for example:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

`ENCRYPTION_KEY` must be a valid Fernet key; keep it stable because changing it makes existing encrypted repository tokens unreadable. Production settings validation rejects placeholder JWT secrets, missing/invalid encryption keys, non-HTTPS CORS origins, and non-SSL database connections.

Run Alembic migrations once as a controlled deployment task before updating backend service tasks. Override the backend container command with `alembic upgrade head`; the image entrypoint executes supplied commands directly. The normal service must use `RUN_MIGRATIONS=false` so concurrent replicas do not race migrations.

### Agent environment and IAM

Set:

```text
AGENT_BACKEND=bedrock
AGENT_MODEL=<approved Bedrock model or inference-profile ID>
AWS_REGION_NAME=<Bedrock region>
AWS_USE_IAM_ROLE=true
```

Attach a least-privilege **task role** with the required Bedrock invocation permissions for the approved model/profile. Do not place AWS SSO profiles or static access keys in ECS task definitions. Use the **task execution role** separately for ECR image pulls, CloudWatch logging, and Secrets Manager injection. Verify Bedrock model access and inference-profile requirements in the target account and region.

### Frontend

Build the frontend image with the production ALB origin:

```bash
docker build \
  --build-arg VITE_API_URL=https://<application-domain> \
  -t <ecr-frontend-repository>:<release-tag> \
  frontend
```

The frontend container runs as an unprivileged user on port `8080`.

## Release and operations checklist

- Use HTTPS at the ALB with an ACM certificate, redirect HTTP to HTTPS, and restrict inbound network rules.
- Store secrets in Secrets Manager; rotate them according to organization policy.
- Restrict RDS security groups to backend tasks and keep the database in private subnets.
- Enable RDS backups, deletion protection, encryption, and an agreed recovery objective.
- Enable CloudWatch application/container logs, alarms for 5xx responses, unhealthy tasks, database pressure, and Bedrock throttling.
- Configure ECS deployment circuit breakers and rollback; deploy images by digest after CI succeeds.
- Confirm rate limits, user/account lifecycle, privacy/retention rules, and model data-handling requirements before opening registration to external users.
- Run dependency and image vulnerability scans and review IAM policies before production launch.

The root `docker-compose.yml` remains a local development convenience. It uses development database credentials and port mappings and is not the production ECS deployment configuration.
