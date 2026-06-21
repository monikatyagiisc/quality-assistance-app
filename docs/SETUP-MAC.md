# Local setup — macOS

Complete checklist to run **Quality Assistance App** on macOS (Intel or Apple Silicon).

---

## 1. Software to install

| Tool | Version | Why |
|------|---------|-----|
| **Node.js** | 20+ | Frontend (Vite + React) — `brew install node` or [nodejs.org](https://nodejs.org/) |
| **Yarn** | Latest | `yarn install` / `yarn dev` in `frontend/` — `npm install -g yarn` or `brew install yarn` |
| **Python** | 3.11+ | Backend + agent — `brew install python@3.11` |
| **uv** | Latest | Python deps & run scripts — `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **PostgreSQL** | 16+ | App database — see [Database](#4-database-postgresql) below |
| **Docker Desktop** | Latest | Easiest way to run PostgreSQL — `brew install --cask docker` or [docker.com](https://www.docker.com/products/docker-desktop/) |
| **Git** | — | Clone the repo — Xcode CLI tools or `brew install git` |

**PostgreSQL — pick one approach:**

| Approach | What to install | When to use |
|----------|-----------------|-------------|
| **A. Docker (recommended)** | Docker Desktop | `docker compose up -d` for Postgres 16 |
| **B. Local PostgreSQL** | `brew install postgresql@16` | You manage Postgres; port **5432** free |

**Run everything:**

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

**Editor (optional):** VS Code — open `quality-assistance-app.code-workspace`.

---

## 2. API keys and secrets

| Item | Where | Required for |
|------|--------|----------------|
| **Gemini API key** | [Google AI Studio](https://aistudio.google.com/app/apikey) → `agent/.env` as `GOOGLE_API_KEY` | Default agent (`AGENT_BACKEND=gemini`) |
| **OpenAI API key** | `agent/.env` as `OPENAI_API_KEY` | `AGENT_BACKEND=litellm` + OpenAI model |
| **AWS credentials** | `agent/.env` as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION_NAME` | `AGENT_BACKEND=bedrock` (Amazon Bedrock) |
| **Ollama** | Install from [ollama.com](https://ollama.com), then `ollama pull llama3.2` | `AGENT_BACKEND=ollama` (local, free) |
| **JWT secret** | `backend/.env` → `JWT_SECRET` | Login / API auth |
| **Fernet key** | `backend/.env` → `ENCRYPTION_KEY` | Password storage at rest |

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 3. Environment files

```bash
cd quality-assistance-app
cp backend/.env.example backend/.env
cp agent/.env.example agent/.env
cp frontend/.env.example frontend/.env
```

### `backend/.env`

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=quality_assistance
DB_PASSWORD=quality_assistance
DB_NAME=quality_assistance

AGENT_SERVICE_URL=http://localhost:8001
CORS_ORIGINS=http://localhost:5173
JWT_SECRET=<your-random-secret>
ENCRYPTION_KEY=<fernet-key>
```

### `agent/.env`

Default (Gemini):

```env
AGENT_BACKEND=gemini
AGENT_MODEL=gemini-2.0-flash
GOOGLE_API_KEY=<your-gemini-key>
LOG_LEVEL=INFO
```

Free local option (Ollama):

```env
AGENT_BACKEND=ollama
AGENT_MODEL=llama3.2
OLLAMA_API_BASE=http://localhost:11434
LOG_LEVEL=INFO
```

Install Ollama from [ollama.com](https://ollama.com), open the app (or run `ollama serve`), then:

```bash
ollama pull llama3.2
```

If `ollama` is not on your PATH after install, use the app from **Applications → Ollama**, or:

```bash
/Applications/Ollama.app/Contents/Resources/ollama pull llama3.2
```

### `frontend/.env`

```env
VITE_API_URL=http://localhost:8000
```

---

## 4. Database (PostgreSQL)

### Option A — Docker (recommended)

**Postgres only** (used by `dev.sh` when local Postgres is not running):

```bash
docker compose up -d postgres
```

**Entire app in Docker** (Postgres + agent + backend + frontend): see [Run full stack with Docker Compose](#run-full-stack-with-docker-compose).

| Setting | Value |
|---------|--------|
| Host | `localhost` |
| Port | `5432` |
| User / password / DB | `quality_assistance` |

### Option B — Local PostgreSQL (Homebrew)

```bash
brew install postgresql@16
brew services start postgresql@16
createuser -s quality_assistance  # or use psql to match backend/.env
createdb quality_assistance
```

Match `DB_*` in `backend/.env`.

---

## 5. Install dependencies (first time)

```bash
cd agent && uv sync
cd ../backend && uv sync && uv run alembic upgrade head
cd ../frontend && yarn install
```

---

## Run full stack with Docker Compose

Runs **PostgreSQL**, **agent**, **backend**, and **frontend** in Docker. Requires **Docker Desktop** and a **Gemini API key** in root `.env` (not `agent/.env`).

```bash
cd quality-assistance-app

cp .env.docker.example .env
# Edit .env — set GOOGLE_API_KEY=your-gemini-key

chmod +x scripts/docker-up.sh
./scripts/docker-up.sh
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

Same steps as [Run full stack with Docker Compose](#run-full-stack-with-docker-compose) above.

Use the [Docker Compose](#run-full-stack-with-docker-compose) section above. For local development with hot reload, use **Option B** below.

### Option B — Local dev (`dev.sh`)

```bash
./scripts/dev.sh
```

### Option C — Manual (four terminals)

```bash
# 1. Postgres only
docker compose up -d postgres

# 2. Agent
cd agent && uv run quality-assistance-agent

# 3. Backend
cd backend && uv run alembic upgrade head && uv run quality-assistance-backend

# 4. Frontend
cd frontend && yarn dev
```

---

## 7. Use the app

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web UI |
| http://localhost:8000/docs | Backend |
| http://localhost:8001/docs | Agent |

Register → dashboard → submit requirements (try **samples**).

---

## 8. Ports to keep free

| Port | Service |
|------|---------|
| **5432** | **PostgreSQL** |
| 5173 | Frontend |
| 8000 | Backend |
| 8001 | Agent |

---

## 9. Health checks

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
docker compose ps
```

---

## 10. Troubleshooting (macOS)

| Issue | Fix |
|-------|-----|
| `uv` not found | `source $HOME/.local/bin/env` |
| Postgres failed | `docker compose up -d`; check `DB_*` in `backend/.env` |
| Port 5432 in use | `lsof -i :5432` — stop conflicting Postgres |
| Agent 429 / quota | Wait; check Gemini billing or LiteLLM + OpenAI |

---

## Minimal checklist

**Docker full stack:** Docker Desktop + root `.env` with `GOOGLE_API_KEY` → `./scripts/docker-up.sh`

**Local dev:**

- [ ] Node.js 20+, Yarn, Python 3.11+, uv  
- [ ] PostgreSQL (Docker or local) on port **5432**  
- [ ] `backend/.env`, `agent/.env`, `frontend/.env`  
- [ ] `GOOGLE_API_KEY`, `JWT_SECRET`, `ENCRYPTION_KEY`  
- [ ] `uv sync`, `alembic upgrade head`, `yarn install`  
- [ ] Services running (`./scripts/dev.sh` or manual)  
- [ ] http://localhost:5173  

---

## Related docs

- [Main README](../README.md)  
- [Windows setup](./SETUP-WINDOWS.md)  
- [End-to-end sequence diagram](./quality-assistance-e2e-sequence.puml)
