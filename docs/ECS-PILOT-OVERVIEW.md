# AWS ECS pilot deployment overview

This overview summarizes the AWS resources and deployment sequence for a small pilot of the Quality Assistance App. It assumes the app runs on ECS Fargate, PostgreSQL is hosted by Amazon RDS, and the agent calls Amazon Bedrock. It is a planning document, not a ready-to-deploy infrastructure template.

## Architecture

```text
Browser
  |
  | HTTPS
  v
Application Load Balancer
  |-- /api/* -> ECS backend service
  `-- everything else -> ECS frontend service

Backend ECS service -> private agent ECS service -> Amazon Bedrock
Backend ECS service -> private RDS PostgreSQL
```

The frontend, backend, and agent are separate containers. The app does not need GPU instances when using Bedrock; inference is provided by the AWS service.

## Pilot resource list

| AWS resource | Quantity | Purpose |
|---|---:|---|
| ECS cluster | 1 | Logical home for the ECS services |
| ECS services and task definitions | 3 | Frontend, backend, and agent; start with one running task per service |
| ECR repositories | 3 | Store versioned container images |
| Application Load Balancer | 1 | Public HTTPS endpoint; route `/api/*` to the backend and other requests to the frontend |
| RDS for PostgreSQL | 1 | Persistent application database; Single-AZ is a lower-cost pilot option |
| VPC and subnets | 1 VPC spanning 2 Availability Zones | Public subnets for the ALB; private subnets for ECS tasks and RDS |
| Security groups | About 3 | Restrict ALB ingress, app-service communication, and database access |
| IAM roles | Typically 4 | ECS execution role plus frontend, backend, and agent task roles; the agent role gets Bedrock permissions |
| CloudWatch log groups | 3 | Logs for frontend, backend, and agent |
| Secrets Manager secrets | 3, or 1 grouped secret | Database password, JWT secret, and encryption key |
| ACM certificate and DNS record | 1 each, if using a custom domain | TLS certificate and friendly application URL |

Networking may also require NAT gateways or VPC endpoints so private tasks can access AWS services and external model/API endpoints. These can materially affect cost; check whether your AWS account already has shared network infrastructure.

## Deployment sequence

1. **Prepare the AWS environment.** Choose a region where your approved Bedrock model or inference profile is available. Confirm VPC/subnets, security groups, ACM certificate, and DNS if using a custom domain.
2. **Create RDS and secrets.** Put RDS in private subnets, enable encryption and backups, and create the database credentials. Store `DB_PASSWORD`, `JWT_SECRET`, and `ENCRYPTION_KEY` in Secrets Manager. Keep `ENCRYPTION_KEY` stable because changing it can make previously encrypted repository tokens unreadable.
3. **Build and push images.** Build the frontend, backend, and agent images and push them to their ECR repositories. Build the frontend with `VITE_API_URL=https://<your-domain>`; this value is embedded into the frontend at build time.
4. **Create ECS task definitions and services.** Use container ports `8080` (frontend), `8000` (backend), and `8001` (agent). Keep agent and database private. Only the ALB should be publicly reachable.
5. **Configure runtime settings and IAM.** Set backend `APP_ENV=production`, `DB_SSL=true`, `CORS_ORIGINS=https://<your-domain>`, and `RUN_MIGRATIONS=false`. Configure the agent with `AGENT_BACKEND=bedrock`, `AGENT_MODEL=<approved-model-or-profile>`, `AWS_REGION_NAME=<region>`, and `AWS_USE_IAM_ROLE=true`. Give the agent task role least-privilege permission to invoke the selected model/profile.
6. **Run database migrations once.** Run an ECS one-off task using the backend image and command `alembic upgrade head` before updating the service. Keep `RUN_MIGRATIONS=false` on normal service tasks to avoid concurrent migration attempts.
7. **Deploy and validate.** Check service health, sign in, submit a representative request, and verify that Bedrock invocation succeeds. The backend `/ready` endpoint checks database and agent health; a model request separately validates Bedrock access.

The ECS task execution role and task roles have different purposes: the execution role supports image pulls, logging, and secret injection; the agent task role provides Bedrock access. Do not put AWS SSO profiles or static AWS access keys into task definitions.

## How many tasks?

- **Pilot:** 3 running tasks total—one task each for frontend, backend, and agent.
- **Higher availability:** at least 6 running tasks—two per service across Availability Zones—plus Multi-AZ RDS.

The pilot setup is cheaper but has less resilience. Choose task CPU and memory after measuring the real workload rather than assuming a fixed size.

## Main cost drivers

The primary variable costs are Fargate task uptime, RDS, the ALB, NAT/networking, storage and CloudWatch logs, and Bedrock model usage. NAT gateways and always-on load balancers can be significant for a small test, so estimate costs in the target region and check whether your organization provides shared VPC/network resources.

## Detailed deployment instructions

For environment variables, container details, and the release checklist, see the [AWS ECS production deployment guide](./PRODUCTION-ECS.md). That guide is also a checklist, not an automated CloudFormation or Terraform stack; resources must be created in your AWS account.
