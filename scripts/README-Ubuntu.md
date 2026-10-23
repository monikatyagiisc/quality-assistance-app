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

From the repository root, if using the JFrog registry, first read the token without echoing it and export it for setup:

```bash
read -rsp 'JFrog npm token: ' JFROG_NPM_TOKEN
echo
export JFROG_NPM_TOKEN
```

Then run setup:

```bash
chmod +x scripts/setup-ubuntu.sh scripts/run-ubuntu.sh
./scripts/setup-ubuntu.sh
unset JFROG_NPM_TOKEN
```

The setup script creates `backend/.env`, `agent/.env`, and `frontend/.env` from their examples only when missing. It generates development JWT and encryption secrets when the backend values are still placeholders, installs project dependencies, and applies database migrations. If `JFROG_NPM_TOKEN` is set, it uses the JFrog install helper for the frontend. If PostgreSQL is not reachable at the configured local address, it starts the project's PostgreSQL container; Docker must already be installed and running.

Set `GOOGLE_API_KEY` in `agent/.env` (or configure the provider selected by `AGENT_BACKEND`), then launch:

```bash
./scripts/run-ubuntu.sh
```

The launcher starts the agent, backend, and frontend, and attempts to open the web app in your default browser when running in a graphical Ubuntu session. If no browser opens, visit <http://localhost:5173> manually. API documentation is available at <http://localhost:8000/docs> and <http://localhost:8001/docs>. Press **Ctrl+C** to stop. Logs are written to `.logs/`.

The development secrets in `backend/.env` are for local use only. Keep `.env` files private and do not commit them.

## Install frontend packages through JFrog

If setup has already completed and you only need to install the frontend dependencies through JFrog, run:

```bash
read -rsp 'JFrog npm token: ' JFROG_NPM_TOKEN
echo
export JFROG_NPM_TOKEN
./scripts/yarn-install-jfrog.sh
unset JFROG_NPM_TOKEN
```

The script uses the repository URL supplied for this setup, routes the Yarn lockfile's public registry download URLs through JFrog for the duration of the install, and restores `frontend/yarn.lock` afterward. It writes the token only to a permission-restricted temporary npm config and removes that file when it exits. It does not save credentials in project or global npm/Yarn configuration.
