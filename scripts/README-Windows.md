# Run Quality Assistance App on Windows

This guide covers two ways to run the app:

1. **Local development:** run the frontend, backend, and AI agent directly on Windows. PostgreSQL can run locally or in Docker.
2. **Full Docker:** run PostgreSQL, frontend, backend, and agent in Docker containers.

Use local development when you want to edit code and use hot reload. Use full Docker when you want the fewest development tools installed on Windows.

## Choose Your Run Mode

| Mode | Install on Windows | Python virtual environments |
|---|---|---|
| Local development | Python, uv, Node.js, Yarn, and PostgreSQL or Docker Desktop | Created under `agent\.venv` and `backend\.venv` |
| Full Docker | Docker Desktop only, plus a Gemini API key | Not needed on Windows; Python dependencies are installed inside containers |

## 1. Install Tools

Use **Windows 10 or 11**. Commands below can be run in PowerShell unless marked **Command Prompt**. After installing a tool, close and reopen the terminal if its command is not found.

### Local development tools

1. **Python 3.11 or newer:** install from [python.org](https://www.python.org/downloads/windows/). During setup, select **Add python.exe to PATH**.
2. **Node.js 20 or newer:** install the LTS release from [nodejs.org](https://nodejs.org/). This also installs `npm`.
3. **uv:** in PowerShell, run the official installer:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   Close and reopen PowerShell after the installer completes.
4. **Yarn:** in PowerShell or Command Prompt, run:

   ```text
   npm install --global yarn
   ```

5. **Database:** choose one:
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and start it before running setup. The scripts can start the project's PostgreSQL container.
   - Or install PostgreSQL 16 or newer and configure its connection in `backend\.env`.

Check the required commands in PowerShell or Command Prompt:

```text
python --version
node --version
npm --version
uv --version
yarn --version
docker --version
```

Python, Node.js, uv, and Yarn are required for the local workflow. Docker is needed for the database only if you are not running PostgreSQL locally. Git is only needed to clone or update the repository.

### AI model credentials

For the default configuration, create a Gemini API key at [Google AI Studio](https://aistudio.google.com/app/apikey). OpenAI through LiteLLM, Amazon Bedrock, and local Ollama are also configurable; see `agent\.env.example` for the relevant settings.

## 2. Local Development

### Open a terminal in the project folder

In File Explorer, open the `quality-assistance-app` folder, click the address bar, type `powershell`, and press **Enter**. Or open PowerShell and change directory, replacing the path with your project location:

```powershell
cd C:\path\to\final-year-project\quality-assistance-app
```

### Run first-time setup

If PowerShell blocks the script, allow scripts for this PowerShell window only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Run setup:

```powershell
.\scripts\setup-windows.ps1
```

The setup script creates missing `.env` files, generates development JWT and encryption secrets without replacing custom values, starts Docker PostgreSQL if no database is reachable, installs project dependencies, and applies migrations. Python dependency commands create `agent\.venv` and `backend\.venv`; you do not need to activate these environments manually.

If setup needs Docker PostgreSQL, Docker Desktop must already be installed and running. If you use local PostgreSQL, make sure it is running and that `backend\.env` has the correct connection settings.

### Add your AI key

Open the agent environment file in Notepad:

```powershell
notepad .\agent\.env
```

Replace `your-gemini-api-key` with your Gemini key, save the file, and close Notepad. Do not share or commit `.env` files.

### Start the whole app

In the same PowerShell window, run:

```powershell
.\scripts\dev.ps1
```

The launcher starts PostgreSQL if needed, checks dependencies, applies migrations, and starts the agent, backend, and frontend. When the frontend responds, it opens your default browser.

| Service | Address |
|---|---|
| Web app | http://localhost:5173 |
| Backend API docs | http://localhost:8000/docs |
| Agent API docs | http://localhost:8001/docs |

Keep the PowerShell window open while using the app. Press **Ctrl+C** to stop the app services. Logs are saved in `.logs\`. A PostgreSQL container that was already running before launch is left running.

### Run commands from Command Prompt (cmd.exe)

PowerShell scripts cannot be run by typing their names directly in Command Prompt. From Command Prompt, change to the project folder and invoke PowerShell explicitly:

```bat
cd /d C:\path\to\final-year-project\quality-assistance-app
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
notepad agent\.env
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\dev.ps1
```

Add and save your Gemini key in Notepad before starting the app. Keep the Command Prompt window open; press **Ctrl+C** there to stop the launcher.

### Start services manually in separate terminals

Usually `dev.ps1` is easier. To run services separately, first run setup and configure `agent\.env`, then open four PowerShell or Command Prompt windows. In each one, change directory to the project folder as shown.

**Terminal 1 — PostgreSQL**, if using Docker for the database:

```powershell
cd C:\path\to\final-year-project\quality-assistance-app
docker compose up -d postgres
```

Skip this terminal if local PostgreSQL is running.

**Terminal 2 — Agent:**

```powershell
cd C:\path\to\final-year-project\quality-assistance-app\agent
uv run quality-assistance-agent
```

**Terminal 3 — Backend:**

```powershell
cd C:\path\to\final-year-project\quality-assistance-app\backend
uv run alembic upgrade head
uv run quality-assistance-backend
```

**Terminal 4 — Frontend:**

```powershell
cd C:\path\to\final-year-project\quality-assistance-app\frontend
yarn dev
```

Open http://localhost:5173 in your browser. Leave the service windows open. Stop each service with **Ctrl+C** in its window.

## 3. Full Docker Setup

This mode runs the whole app in containers. You do not need to install Python, uv, Node.js, or Yarn on Windows.

1. Install and open Docker Desktop. Wait until Docker Desktop reports that it is running.
2. Open PowerShell in the `quality-assistance-app` folder and copy the Docker environment example:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.docker.example .env }
   notepad .env
   ```

3. In Notepad, replace `your-gemini-api-key` with your Gemini key. Save and close the file.
4. Start the full stack:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\scripts\docker-up.ps1
   ```

The script builds the containers and waits for the services to become healthy. Open http://localhost:5173 when it reports that the services are up. API docs are at http://localhost:8000/docs and http://localhost:8001/docs.

To use Command Prompt instead, run these commands from the project folder:

```bat
if not exist .env copy .env.docker.example .env
notepad .env
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\docker-up.ps1
```

Save your Gemini key in Notepad before running the last command.

To follow container logs:

```text
docker compose logs -f
```

To stop the full Docker stack:

```text
docker compose down
```

## 4. Common Problems

- **A command is not recognized:** install the named tool, reopen the terminal, and retry its version command.
- **PowerShell says scripts are disabled:** run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that PowerShell window, then retry.
- **Docker database will not start:** open Docker Desktop and wait for it to finish starting. Make sure port `5432` is not already used by another PostgreSQL instance.
- **Agent reports missing credentials:** check `GOOGLE_API_KEY` in `agent\.env` for local development or the root `.env` for full Docker.
- **Port already in use:** stop the other app using ports `5173`, `8000`, `8001`, or `5432`, then retry.
- **Need more detail:** see [the Windows setup guide](../docs/SETUP-WINDOWS.md) and [the project README](../README.md).