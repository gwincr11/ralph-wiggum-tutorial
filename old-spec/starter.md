# Project Setup Plan — ralph-wiggum-tutorial

## Goal
Set up a full-stack development environment in a GitHub Codespace with a Flask (Python 3.12) backend using MVC structure, Pydantic types, SQLAlchemy ORM, PostgreSQL, and a React islands frontend (Vite + Tailwind + TypeScript) mounted into Jinja2 templates. Includes CI, linting, testing, and GitHub's "Scripts to Rule Them All" pattern.

## Approach
Build bottom-up: devcontainer → Python backend → frontend → scripts → CI → docs.

---

## Todos

### 1. Devcontainer & Environment (`devcontainer`)
- `.devcontainer/devcontainer.json` with Python 3.12 base image
- PostgreSQL feature (runs in-codespace)
- Node.js feature (for frontend tooling)
- Copilot CLI + GitHub CLI pre-installed (already in Codespaces, just ensure features listed)
- Post-create command wires to `script/setup`

### 2. Environment Config (`env-config`)
- `.env.example` with all required env vars documented:
  - `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/app`
  - `FLASK_ENV=development`
  - `FLASK_SECRET_KEY=change-me-in-production`
  - `FLASK_DEBUG=1`
- `.env` added to `.gitignore`
- `script/setup` copies `.env.example` → `.env` if `.env` doesn't exist

### 3. Python gitignore (`gitignore`)
- Add `.gitignore` with standard Python ignores + node_modules, dist, .venv, .env, etc.

### 4. Flask Backend (`flask-backend`)
- MVC folder structure under `src/`:
  ```
  src/
    app/
      __init__.py          # Flask app factory
      config.py            # Config via env vars (reads from .env)
      errors.py            # Error handlers (400, 404, 500) with JSON + HTML responses
      logging_config.py    # Structured logging setup
      models/
        __init__.py
        base.py            # SQLAlchemy base + session
        hello.py           # Example model
      views/
        __init__.py
        hello.py           # Blueprint with route
      controllers/
        __init__.py
        hello.py           # Business logic
      schemas/
        __init__.py
        hello.py           # Pydantic schemas
      templates/
        base.html
        errors/
          404.html
          500.html
        hello/
          index.html       # Jinja2 template with React island mount point
      static/              # Vite build output lands here
  ```
- SQLAlchemy setup with Postgres connection string from `DATABASE_URL` env var
- Pydantic models for request/response validation
- Hello world route: `GET /` renders a Jinja2 template
- Error handlers registered on app factory: 400, 404, 500
  - Returns JSON if request `Accept: application/json`, otherwise renders error template
- Logging: structured JSON logs in production, readable format in development
  - Configure via `logging_config.py`, called from app factory

### 5. Database Migrations (`db-migrations`)
- Flask-Migrate (Alembic wrapper) for schema management
- Add `flask-migrate` to `requirements.txt`
- `migrations/` directory initialized via `flask db init`
- Initial migration generated from models
- `script/setup` runs `flask db upgrade` to apply migrations
- `script/db-seed` populates dev database with example data (hello world record)
- Migration commands available:
  - `flask db migrate -m "description"` — generate migration
  - `flask db upgrade` — apply migrations
  - `flask db downgrade` — rollback one migration

### 6. Python Tooling (`python-tooling`)
- `requirements.txt` (Flask, SQLAlchemy, Flask-Migrate, Pydantic, gunicorn, psycopg2-binary, python-dotenv)
- `requirements-dev.txt` (pytest, flake8, mypy/pyright stubs, pre-commit)
- `pyproject.toml` for flake8 config, pytest config, and mypy/pyright settings
- Basic test: `tests/test_hello.py`

### 7. React Islands Frontend (`react-frontend`)
- `frontend/` directory at repo root with the following structure:
  ```
  frontend/
    src/
      islands/             # Each island = independent React entry point
        hello/
          HelloIsland.tsx  # React component
          index.ts         # Mount logic for this island
      components/          # Shared UI components (used across islands)
        ui/                # Primitives: Button, Input, Card, etc.
      hooks/               # Shared custom React hooks
      lib/                 # Utility functions, API client helpers
      types/               # Shared TypeScript types & interfaces
      styles/
        globals.css        # Tailwind @import directives
      main.ts              # Island registry & auto-mount logic
    tests/                 # Mirrors src/ structure
      islands/
        hello/
          HelloIsland.test.tsx
    package.json
    vite.config.ts         # Builds islands, outputs to src/app/static/
    tsconfig.json
    tailwind.config.ts
    postcss.config.js
    eslint.config.js       # Flat config for TS/React
    vitest.config.ts
  ```
- **Island pattern conventions:**
  - Each island directory contains its component + mount `index.ts`
  - `main.ts` scans for `[data-island]` attributes and lazy-loads matching island modules
  - Island-specific code stays colocated in its directory
  - When 2+ islands share code, elevate it to `components/`, `hooks/`, or `lib/`
  - Keep directories flat until they exceed ~7 files, then add subdirectories
- **Vite dev server:**
  - Dev mode: Vite runs on port 5173 with HMR, Flask on port 5000
  - `vite.config.ts` sets `server.origin` to `http://localhost:5173` in dev
  - Jinja2 `base.html` loads Vite client + module scripts from Vite dev server in development
  - Production: Vite builds to `src/app/static/`, Jinja2 reads `manifest.json` for hashed paths

### 8. Pre-commit Hooks (`pre-commit`)
- `.pre-commit-config.yaml` with hooks for:
  - flake8 (Python lint)
  - mypy/pyright (Python typecheck)
  - eslint (JS/TS lint)
  - trailing whitespace / end-of-file fixer
- Installed via `pre-commit install` in `script/setup`

### 9. Scripts to Rule Them All (`scripts`)
- `script/bootstrap` — install system deps (pip, npm)
- `script/setup` — copy .env.example, create DB, run migrations, install deps, install pre-commit hooks
- `script/server` — start Flask dev server + Vite dev server (concurrently)
- `script/test` — run pytest + vitest
- `script/lint` — run flake8 + eslint
- `script/typecheck` — run pyright/mypy + tsc --noEmit
- `script/update` — update deps (pip + npm)
- `script/console` — open Flask shell
- `script/db-seed` — populate database with dev data
- `Procfile` for gunicorn (production)

### 10. GitHub Actions CI (`ci`)
- `.github/workflows/ci.yml`
  - Trigger: push + PR to main
  - Jobs: lint, typecheck, test (Python + Node)
  - Services: PostgreSQL
  - Caching: pip + npm

### 11. Update AGENTS.md & README (`docs`)
- Update AGENTS.md with build/run/test/lint/typecheck commands
- Update README with project overview, setup instructions, and architecture diagram

---

## Notes
- Postgres runs inside the codespace via devcontainer feature (no external DB)
- Database name: `app`
- React islands pattern: server renders HTML, Vite bundles JS that hydrates specific DOM nodes
- Flask serves both HTML pages and could serve API endpoints later
- Vite manifest used in Jinja2 to resolve hashed asset paths
- In dev, Vite dev server provides HMR; `script/server` runs both Flask + Vite concurrently
- `.env` is never committed; `.env.example` is the source of truth for required variables
- Pre-commit hooks enforce quality locally before CI catches issues
- Flask-Migrate wraps Alembic — all schema changes go through migrations, never raw SQL
