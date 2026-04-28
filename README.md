# Brand Decision System

Real-Time Brand Decision System — a facilitator-operated bilingual (Arabic + English)
ideation tool that compresses weeks of agency-client iteration into a single 50-minute
session across Discovery, Decision, and Generation phases.

The architectural rules and milestone scope live in [`CLAUDE.md`](./CLAUDE.md).
Source product specs live alongside this README as `Brand_Decision_System_*.docx`
and `Brand_Decision_System_Product_Detailing.pdf`. Per-document stubs are in
[`docs/`](./docs).

## Prerequisites

- Python 3.11+
- Docker (for local Postgres)

## Setup

```bash
git clone <this repo>
cd protagt
cp .env.example .env

docker compose up -d                  # starts Postgres on :5432

python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -e ".[dev]"

# Make sure Postgres is running first (e.g. `docker compose up -d`)
alembic upgrade head                  # no migrations exist yet — exits cleanly
uvicorn src.main:app --reload         # serves on :8000
curl http://localhost:8000/health
```

## Tests

```bash
pytest
```

## Lint & format

```bash
ruff check .
black .
```

CI runs the same three commands on every push and pull request — see
`.github/workflows/ci.yml`.
