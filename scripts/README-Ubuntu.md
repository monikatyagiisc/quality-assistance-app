# Run Quality Assistance App on Ubuntu

This guide covers local development, with the frontend, backend, and AI agent running as separate local processes. PostgreSQL can run locally or in Docker.

## Prerequisites

Install the following tools before running the setup script:

- Ubuntu
- Python 3.11 or newer
- Node.js 20 or newer, with npm
- Yarn
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL 16 or newer, or Docker Engine with the Docker Compose plugin
- A Gemini API key for the default agent configuration (other providers are supported; see `agent/.env.example`)

The scripts check for the required tools, but do not install system packages or configure Docker for you.

## Set up and run

From the repository root:

```bash
chmod +x scripts/setup-ubuntu.sh scripts/run-ubuntu.sh
./scripts/setup-ubuntu.sh
```

The setup script creates `backend/.env`, `agent/.env`, and `frontend/.env` from their examples only when missing. It generates development JWT and encryption secrets when the backend values are still placeholders, installs project dependencies, and applies database migrations. If PostgreSQL is not reachable at the configured local address, it starts the project's PostgreSQL container; Docker must already be installed and running.

Set `GOOGLE_API_KEY` in `agent/.env` (or configure the provider selected by `AGENT_BACKEND`), then launch:

```bash
./scripts/run-ubuntu.sh
```

The launcher starts the agent, backend, and frontend. Open the web app at <http://localhost:5173>; API documentation is available at <http://localhost:8000/docs> and <http://localhost:8001/docs>. Press **Ctrl+C** to stop. Logs are written to `.logs/`.

The development secrets in `backend/.env` are for local use only. Keep `.env` files private and do not commit them.
