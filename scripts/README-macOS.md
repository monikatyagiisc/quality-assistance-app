# Run Quality Assistance App on macOS

This guide covers two ways to run the app:

1. **Local development:** run the frontend, backend, and AI agent directly on your Mac. PostgreSQL can run locally or in Docker.
2. **Full Docker:** run PostgreSQL, frontend, backend, and agent in Docker containers.

Use the local option when you want to edit code and use hot reload. Use full Docker when you want the fewest local development tools installed.

## Choose Your Run Mode

| Mode | Install on your Mac | Python virtual environments |
|---|---|---|
| Local development | Python, uv, Node.js, Yarn, and PostgreSQL or Docker Desktop | Created under `agent/.venv` and `backend/.venv` |
| Full Docker | Docker Desktop only, plus a Gemini API key | Not needed on the Mac; Python dependencies are installed inside containers |

## 1. Install Tools

Open the **Terminal** app. Install Homebrew first if you do not already have it: [brew.sh](https://brew.sh/).

### Local development tools

Install Node.js, Python, and uv:

```bash
brew install node python@3.11 uv
```

Install Yarn:

```bash
npm install --global yarn
```

Check that the commands are available:

```bash
node --version
python3.11 --version
uv --version
yarn --version
```

The app requires Node.js 20 or newer and Python 3.11 or newer. If Terminal says a command is not found after installation, close and reopen Terminal, then check again.

### Database

Choose one:

- **Docker PostgreSQL (recommended):** install Docker Desktop with `brew install --cask docker`, open Docker Desktop from Applications, and wait until it says Docker is running. The local app script can start the PostgreSQL container when needed.
- **Local PostgreSQL:** install PostgreSQL 16 or newer and make sure it listens on port `5432`. Configure its credentials in `backend/.env` to match your local database.

### AI model credentials

For the default configuration, create a Gemini API key in [Google AI Studio](https://aistudio.google.com/app/apikey). The app can also be configured for OpenAI through LiteLLM, Amazon Bedrock, or local Ollama; see `agent/.env.example` for the related settings.

## 2. Get the Project Ready

In Terminal, go to the project folder. Replace the example path with the location where you have this repository:

```bash
cd ~/path/to/final-year-project/quality-assistance-app
```

Create local environment files from the examples:

```bash
[ -f backend/.env ] || cp backend/.env.example backend/.env
[ -f agent/.env ] || cp agent/.env.example agent/.env
[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
```

Open `agent/.env` in a text editor and replace `your-gemini-api-key` with your real Gemini key. Do not share or commit `.env` files.

Open `backend/.env` and set the database values. For the project's Docker PostgreSQL container, use:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=quality_assistance
DB_PASSWORD=quality_assistance
DB_NAME=quality_assistance
```

Replace the example JWT secret with a random development value. You can generate one in Terminal:

```bash
openssl rand -hex 32
```

The example Fernet encryption key is only a placeholder and must be replaced. First create the Python environments and install the backend dependencies in the next section, then generate a valid key:

```bash
cd backend
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the printed value into `backend/.env` as `ENCRYPTION_KEY=...`. Keep the key private and do not change it after storing encrypted repository credentials.

## 3. Local Development

### Create Python virtual environments and install dependencies

Each Python project has its own environment. From the repository root, run:

```bash
cd agent
uv venv
uv sync

cd ../backend
uv venv
uv sync

cd ../frontend
yarn install

cd ..
```

This creates `agent/.venv` and `backend/.venv`. You do not need to activate them: commands such as `uv run ...` use the correct environment automatically. The `scripts/dev.sh` launcher also runs `uv sync` for both projects and `yarn install`, so these install commands are optional if you use the launcher directly.

### Start all services with one command

From the repository root:

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

The script checks or starts PostgreSQL, installs dependencies, applies database migrations, and starts the agent, backend, and frontend. It prints service URLs and attempts to open the frontend in your default browser.

| Service | Address |
|---|---|
| Web app | http://localhost:5173 |
| Backend API docs | http://localhost:8000/docs |
| Agent API docs | http://localhost:8001/docs |

Keep this Terminal window open while using the app. Press **Control+C** to stop the app services. Logs are written to `.logs/`. If the script started PostgreSQL, it stops that container on exit.

### Start services manually in separate Terminal windows

Use this option if you want to see each service's output in its own window. First make sure the `.env` files are configured and the Python environments above are created.

**Terminal 1 — PostgreSQL**, if you use Docker for the database:

```bash
cd ~/path/to/final-year-project/quality-assistance-app
docker compose up -d postgres
```

If you installed PostgreSQL locally and it is already running, skip this terminal.

**Terminal 2 — Agent:**

```bash
cd ~/path/to/final-year-project/quality-assistance-app/agent
uv run quality-assistance-agent
```

**Terminal 3 — Backend:**

```bash
cd ~/path/to/final-year-project/quality-assistance-app/backend
uv run alembic upgrade head
uv run quality-assistance-backend
```

**Terminal 4 — Frontend:**

```bash
cd ~/path/to/final-year-project/quality-assistance-app/frontend
yarn dev
```

Open http://localhost:5173 in your browser. Leave all four terminals open while the app is running. Stop each service with **Control+C** in its Terminal window.

## 4. Full Docker Setup

This mode runs the whole app in containers. You do not need to install Python, uv, Node.js, or Yarn on your Mac.

1. Install and open Docker Desktop. Wait for it to report that Docker is running.
2. In Terminal, go to the repository root and copy the Docker environment example:

   ```bash
   cd ~/path/to/final-year-project/quality-assistance-app
   if [ ! -f .env ]; then cp .env.docker.example .env; fi
   open -e .env
   ```

3. In the text editor, replace `your-gemini-api-key` with your Gemini API key. Save and close the file.
4. Build and start the full stack:

   ```bash
   chmod +x scripts/docker-up.sh
   ./scripts/docker-up.sh
   ```

The script waits for the services to become healthy. Then open http://localhost:5173. API docs are at http://localhost:8000/docs and http://localhost:8001/docs.

To follow container logs, open another Terminal at the repository root and run:

```bash
docker compose logs -f
```

To stop the full Docker stack:

```bash
docker compose down
```

## 5. Common Problems

- **`uv`, `yarn`, or `docker` not found:** install the missing tool, reopen Terminal, and check its version command again.
- **Docker database will not start:** open Docker Desktop and wait for it to finish starting; make sure port `5432` is not occupied by another PostgreSQL instance.
- **Agent reports missing credentials:** check `GOOGLE_API_KEY` in `agent/.env` for local development or in the root `.env` for full Docker.
- **Port already in use:** stop the other app using ports `5173`, `8000`, `8001`, or `5432`, then retry.
- **Need more detail:** see [the macOS setup guide](../docs/SETUP-MAC.md) and [the project README](../README.md).