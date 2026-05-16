# Quality Assistance App

Monorepo for an AI-powered quality engineering assistant across the software test life cycle (STLC).

| Folder | Stack | Purpose |
|--------|-------|---------|
| `frontend/` | React + Vite + Yarn | Web UI for submitting requirements and viewing agent output |
| `backend/` | Python + FastAPI + uv | REST API, PostgreSQL persistence, orchestration |
| `agent/` | Python + Google ADK + uv | Multi-model quality assistance agent (Gemini / LiteLLM) |

## Architecture

```mermaid
flowchart LR
  UI[React Frontend] --> API[FastAPI Backend]
  API --> DB[(PostgreSQL)]
  API --> AGT[ADK Agent Service]
  AGT --> LLM[Gemini / LiteLLM]
```

## Platform setup guides

Detailed install and troubleshooting:

| Platform | Guide |
|----------|--------|
| **macOS** | [docs/SETUP-MAC.md](docs/SETUP-MAC.md) |
| **Windows** | [docs/SETUP-WINDOWS.md](docs/SETUP-WINDOWS.md) |

## Prerequisites (all platforms)

| Tool | Purpose |
|------|---------|
| **Node.js** 20+ & **Yarn** | Frontend |
| **Python** 3.11+ & **[uv](https://docs.astral.sh/uv/)** | Backend & agent |
| **PostgreSQL** 16+ | Database (users, assistance history) |
| **Docker Desktop** *or* local Postgres | Run Postgres on port **5432** |
| **Gemini API key** | [Google AI Studio](https://aistudio.google.com/app/apikey) (or OpenAI for LiteLLM) |

Full checklists: **[Windows](docs/SETUP-WINDOWS.md)** · **[macOS](docs/SETUP-MAC.md)**

## Quick start

### macOS / Linux

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev.ps1
```

Both scripts:

- Create `.env` files from examples if missing
- Use existing local Postgres on `5432`, or start Docker Postgres
- Install dependencies, run migrations, start all services

Press **Ctrl+C** to stop. Logs: `.logs/agent.log`, `.logs/backend.log`, `.logs/frontend.log`

### First-time configuration

Copy env templates and set secrets (see platform guides for details):

```bash
# macOS / Linux / Git Bash
cp backend/.env.example backend/.env
cp agent/.env.example agent/.env
cp frontend/.env.example frontend/.env
```

```powershell
# Windows PowerShell
Copy-Item backend\.env.example backend\.env
Copy-Item agent\.env.example agent\.env
Copy-Item frontend\.env.example frontend\.env
```

**Required:**

- `agent/.env` → `GOOGLE_API_KEY` (when `AGENT_BACKEND=gemini`)
- `backend/.env` → `JWT_SECRET`, `ENCRYPTION_KEY`

Generate Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Open the app

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web UI — register, sign in, submit requirements |
| http://localhost:8000/docs | Backend API |
| http://localhost:8001/docs | Agent API |

## Services and ports

| Port | Service |
|------|---------|
| 5173 | Frontend (Vite) |
| 8000 | Backend (FastAPI) |
| 8001 | Agent (ADK) |
| 5432 | PostgreSQL |

## Manual run (separate terminals)

See [docs/SETUP-MAC.md](docs/SETUP-MAC.md) or [docs/SETUP-WINDOWS.md](docs/SETUP-WINDOWS.md).

**Agent** (port 8001):

```bash
cd agent && uv sync && uv run quality-assistance-agent
```

**Backend** (port 8000):

```bash
cd backend && uv sync && uv run alembic upgrade head && uv run quality-assistance-backend
```

**Frontend** (port 5173):

```bash
cd frontend && yarn install && yarn dev
```

**PostgreSQL:**

```bash
docker compose up -d
```

## Auth API

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/register` | Create account |
| `POST /api/auth/login` | Sign in (returns JWT) |
| `GET /api/auth/me` | Current user (Bearer token) |

`POST /api/assist` requires authentication.

## API endpoints

| Service | Endpoint | Description |
|---------|----------|-------------|
| Backend | `GET /health` | Health check |
| Backend | `POST /api/assist` | Run quality assistance (persists to PostgreSQL) |
| Agent | `GET /health` | Health check |
| Agent | `POST /assist` | Invoke ADK agent directly |

## Model configuration

Default (Gemini) in `agent/.env`:

```env
AGENT_BACKEND=gemini
AGENT_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=your-key
```

OpenAI via LiteLLM:

```env
AGENT_BACKEND=litellm
AGENT_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=your-key
```

## Database migrations

Migrations run automatically when using `dev.sh` / `dev.ps1` and on backend startup.

```bash
cd backend
uv run alembic revision --autogenerate -m "describe_change"
uv run alembic upgrade head
```

## Project layout

```
quality-assistance-app/
├── frontend/              # React app (yarn)
├── backend/               # FastAPI API (uv)
├── agent/                 # Google ADK agent (uv)
│   └── agents/quality_assistance/   # ADK CLI entrypoint
├── scripts/
│   ├── dev.sh             # macOS / Linux / Git Bash
│   └── dev.ps1            # Windows PowerShell
├── docs/
│   ├── SETUP-MAC.md
│   ├── SETUP-WINDOWS.md
│   └── quality-assistance-e2e-sequence.puml
├── docker-compose.yml
└── quality-assistance-app.code-workspace
```

## Related project

The sibling `quality-assistant/` folder in this repo contains an earlier LangGraph-based prototype you can reference for STLC agent ideas.
