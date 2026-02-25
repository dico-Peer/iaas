# IaaS — Interviewer As a Service

AI-powered interview platform for structured stakeholder conversations.

## Quick Start

```bash
# Run tests (backend + frontend)
make test

# Start all services (backend, frontend, PostgreSQL, Redis)
make up

# Run database migrations
make migrate

# Stop services
make down
```

## Project Structure

```
IaaS/
├── backend/          # FastAPI application
├── frontend/         # Next.js 14 application
├── shared/           # Shared types
├── tests/            # Test suite
├── infrastructure/   # Terraform (Azure)
├── docker-compose.yml
├── Makefile
└── .github/workflows/ci.yml
```

## Development

- **Backend:** Python 3.9+, FastAPI, PostgreSQL 16 + pgvector, Redis
- **Frontend:** Next.js 14, TypeScript, Vitest
- **Tests:** pytest (backend), Vitest (frontend)

## User Stories Implemented

- **US-1.01:** Monorepo Setup & CI/CD Pipeline ✅
- **US-1.02:** PostgreSQL Database Schema & Migrations ✅
- **US-1.03:** JWT Auth (register, login, refresh, protected endpoints) ✅
- **US-1.04:** Organization & User Management (invite, accept-invite, list users) ✅
- **US-1.05:** Application Shell & Navigation (sidebar, top bar, route guards) ✅
- **US-2.01:** Interview Project CRUD (create, list, update, delete, clone) 🚧

## Publishing (Push & PR)

First-time setup: add your remote and push both branches.

```bash
# Add remote (replace with your repo URL)
git remote add origin git@github.com:YOUR_USERNAME/iaas.git
# or: git remote add origin https://github.com/YOUR_USERNAME/iaas.git

# Push main and feature branch
git push -u origin main
git push -u origin feature/us-1.05
```

Then create a Pull Request: **base `main`** ← **compare `feature/us-1.05`**
