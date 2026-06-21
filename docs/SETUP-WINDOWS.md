# Local setup — Windows

Complete checklist to run **Quality Assistance App** on Windows 10/11.

---

## 1. Software to install

| Tool | Version | Why |
|------|---------|-----|
| **Node.js** | 20+ | Frontend (Vite + React) — [nodejs.org](https://nodejs.org/) LTS |
| **Yarn** | Latest | `yarn install` / `yarn dev` in `frontend/` — `npm install -g yarn` or `corepack enable` |
| **Python** | 3.11+ | Backend + agent — [python.org](https://www.python.org/downloads/) (check **Add Python to PATH**) |
| **uv** | Latest | Python deps & run scripts — [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| **PostgreSQL** | 16+ | App database (users, assistance requests) — see [Database](#4-database-postgresql) below |
| **Docker Desktop** | Latest | Easiest way to run PostgreSQL in a container — [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Git** (optional) | — | Clone the repo — [git-scm.com](https://git-scm.com/download/win) |
| **PowerShell** | 5.1+ | Built into Windows; used for `scripts/dev.ps1` |

**Install uv (PowerShell):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart the terminal after install. If `uv` is not found, add `%USERPROFILE%\.local\bin` to your **PATH**.

**PostgreSQL — pick one approach:**

| Approach | What to install | When to use |
|----------|-----------------|-------------|
| **A. Docker (recommended)** | Docker Desktop only | Script runs `docker compose up -d` for Postgres 16 |
| **B. Local PostgreSQL** | [PostgreSQL for Windows](https://www.postgresql.org/download/windows/) | You manage Postgres yourself; port **5432** must be free |

**Shell options:**

| Script | Shell |
|--------|--------|
| `scripts/dev.ps1` | **PowerShell** (native Windows) |
| `scripts/dev.sh` | **Git Bash** or **WSL2** |

**Editor (optional):** [VS Code](https://code.visualstudio.com/) — open `quality-assistance-app.code-workspace`.

---

## 2. API keys and secrets

| Item | Where | Required for |
|------|--------|----------------|
| **Gemini API key** | [Google AI Studio](https://aistudio.google.com/app/apikey) → `agent\.env` as `GOOGLE_API_KEY` | Default agent (`AGENT_BACKEND=gemini`) |
| **OpenAI API key** | `agent\.env` as `OPENAI_API_KEY` | Only if `AGENT_BACKEND=litellm` + `openai/...` model |
| **AWS credentials** | `agent\.env` as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION_NAME` | Only if `AGENT_BACKEND=bedrock` (Amazon Bedrock) |
| **Ollama** | Install from [ollama.com](https://ollama.com), then `ollama pull llama3.2` | Only if `AGENT_BACKEND=ollama` (local, free) |
| **JWT secret** | `backend\.env` → `JWT_SECRET` | Login / API auth |
| **Fernet key** | `backend\.env` → `ENCRYPTION_KEY` | Encrypting password data at rest |

**Generate Fernet key (PowerShell):**

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output into `backend\.env` as `ENCRYPTION_KEY=...`.

---

## 3. Environment files

From the project root `quality-assistance-app\`:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item agent\.env.example agent\.env
Copy-Item frontend\.env.example frontend\.env
```

### `backend\.env` (important fields)

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=quality_assistance
DB_PASSWORD=quality_assistance
DB_NAME=quality_assistance

AGENT_SERVICE_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:5173
JWT_SECRET=<your-random-secret>
ENCRYPTION_KEY=<fernet-key-from-above>
```

If you use **Docker Postgres** from `docker-compose.yml`, keep `DB_PASSWORD=quality_assistance` (matches the compose file).

### `agent\.env`

```env
AGENT_BACKEND=gemini
AGENT_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=<your-gemini-key>
AGENT_HOST=0.0.0.0
AGENT_PORT=8001
LOG_LEVEL=INFO
```

### `frontend\.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## 4. Database (PostgreSQL)

The backend stores users and assistance requests in **PostgreSQL** on port **5432**.

### Option A — Docker (recommended)

Requires **Docker Desktop** running.

```powershell
cd quality-assistance-app
docker compose up -d postgres
```

This starts **PostgreSQL 16** only (for local `dev.ps1` / `dev.sh`):

**Entire app in Docker** (Postgres + agent + backend + frontend): see [Run full stack with Docker Compose](#run-full-stack-with-docker-compose).

Default Postgres container settings:

| Setting | Value |
|---------|--------|
| Host | `localhost` |
| Port | `5432` |
| User | `quality_assistance` |
| Password | `quality_assistance` |
| Database | `quality_assistance` |

`dev.ps1` / `dev.sh` will skip Docker if Postgres is already reachable on that port.

### Option B — Local PostgreSQL install

1. Install PostgreSQL 16+ for Windows.
2. Create a user and database (or use defaults that match `backend\.env`):

```sql
CREATE USER quality_assistance WITH PASSWORD 'quality_assistance';
CREATE DATABASE quality_assistance OWNER quality_assistance;
```

3. Ensure PostgreSQL listens on `localhost:5432`.
4. Set `DB_*` in `backend\.env` to match your instance.

**Optional tools:** [pgAdmin](https://www.pgadmin.org/) or `psql` to inspect tables after migrations.

---

## 5. Install dependencies (first time)

Run once from PowerShell (or let `dev.ps1` do this for you):

```powershell
cd quality-assistance-app\agent
uv sync

cd ..\backend
uv sync
uv run alembic upgrade head

cd ..\frontend
yarn install
```

---

## Run full stack with Docker Compose

Runs **PostgreSQL**, **agent**, **backend**, and **frontend** in Docker. Requires **Docker Desktop** and a **Gemini API key** in root `.env` (not `agent\.env`).

```powershell
cd quality-assistance-app

Copy-Item .env.docker.example .env
# Edit .env — set GOOGLE_API_KEY=your-gemini-key

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\docker-up.ps1
```

Or: `docker compose up --build`

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web UI |
| http://localhost:8000/docs | Backend |
| http://localhost:8001/docs | Agent |

Stop: `docker compose down` · Logs: `docker compose logs -f`

---

## 6. Run the app

### Option A — Full stack in Docker (simplest)

Use the [Docker Compose](#run-full-stack-with-docker-compose) section above. For local development with hot reload, use **Option B** below.

### Option B — Local dev (`dev.ps1`, recommended for coding)

```powershell
cd quality-assistance-app
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\dev.ps1
```

Starts **PostgreSQL** (if needed), **agent** (`:8001`), **backend** (`:8000`), **frontend** (`:5173`), runs migrations, installs deps.

Logs: `.logs\agent.log`, `.logs\backend.log`, `.logs\frontend.log`

Press **Ctrl+C** to stop.

### Option C — Git Bash / WSL

```bash
./scripts/dev.sh
```

### Option D — Manual (four terminals)

**Terminal 1 — PostgreSQL (if not already running)**

```powershell
docker compose up -d postgres
```

**Terminal 2 — Agent**

```powershell
cd quality-assistance-app\agent
uv run quality-assistance-agent
```

**Terminal 3 — Backend**

```powershell
cd quality-assistance-app\backend
uv run alembic upgrade head
uv run quality-assistance-backend
```

**Terminal 4 — Frontend**

```powershell
cd quality-assistance-app\frontend
yarn dev
```

---

## 7. Use the app

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web UI — register / login, dashboard |
| http://localhost:8000/docs | Backend API docs |
| http://localhost:8001/docs | Agent API docs |

**Steps:**

1. Open http://localhost:5173  
2. **Register** a user  
3. Load a **sample** on the dashboard (optional)  
4. Click **Get quality assistance**

---

## 8. Ports to keep free

| Port | Service |
|------|---------|
| **5432** | **PostgreSQL** |
| 5173 | Frontend (Vite) |
| 8000 | Backend (FastAPI) |
| 8001 | Agent (Google ADK) |

---

## 9. Quick health checks

```powershell
curl http://localhost:8000/health
curl http://localhost:8001/health
```

**PostgreSQL (Docker):**

```powershell
docker compose ps
docker exec -it quality-assistance-postgres pg_isready -U quality_assistance -d quality_assistance
```

---

## 10. Common Windows issues

| Issue | What to do |
|-------|------------|
| `uv` not found | Restart terminal; add `%USERPROFILE%\.local\bin` to PATH |
| `yarn` not found | `npm install -g yarn` or `corepack enable` |
| `dev.ps1` cannot run | `Set-ExecutionPolicy -Scope Process Bypass` |
| Docker not running | Start **Docker Desktop**; wait until healthy |
| Postgres connection failed | `docker compose up -d`; match `DB_*` in `backend\.env`; check port 5432 |
| Port 5432 in use | Stop other Postgres instances or change `DB_PORT` in `.env` + compose |
| Agent quota / 429 | Friendly UI message; wait or fix Gemini billing / use LiteLLM + OpenAI |
| `dev.sh` won't run on CMD | Use PowerShell (`dev.ps1`) or Git Bash |
| Firewall prompts | Allow Node/Python on private network |

---

## Minimal checklist

**Docker full stack:** Docker Desktop + root `.env` with `GOOGLE_API_KEY` → `.\scripts\docker-up.ps1`

**Local dev** — copy and tick off:

- [ ] **Node.js** 20+ installed  
- [ ] **Yarn** installed  
- [ ] **Python** 3.11+ installed (on PATH)  
- [ ] **uv** installed  
- [ ] **PostgreSQL** available — Docker Desktop **or** local Postgres 16+ on port **5432**  
- [ ] `backend\.env`, `agent\.env`, `frontend\.env` created from examples  
- [ ] `GOOGLE_API_KEY`, `JWT_SECRET`, `ENCRYPTION_KEY` set  
- [ ] Postgres running (`docker compose up -d postgres` or local service)  
- [ ] `uv sync` in `agent\` and `backend\`  
- [ ] `uv run alembic upgrade head` in `backend\`  
- [ ] `yarn install` in `frontend\`  
- [ ] Agent + backend + frontend running (`dev.ps1` or manual)  
- [ ] Browser open at http://localhost:5173  

---

## Related docs

- [Main README](../README.md)  
- [macOS setup](./SETUP-MAC.md)  
- [End-to-end sequence diagram](./quality-assistance-e2e-sequence.puml)
