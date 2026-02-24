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

- **Backend:** Python 3.11+, FastAPI, PostgreSQL 16 + pgvector, Redis
- **Frontend:** Next.js 14, TypeScript, Vitest
- **Tests:** pytest (backend), Vitest (frontend)

## User Stories Implemented

- **US-1.01:** Monorepo Setup & CI/CD Pipeline ✅
- **US-1.02:** PostgreSQL Database Schema & Migrations ✅
