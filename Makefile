.PHONY: test lint type-check build up down install migrate migrate-down push

install:
	cd backend && python3 -m pip install -r requirements.txt
	cd frontend && npm install

test:
	PYTHONPATH=backend python3 -m pytest tests/ -v --ignore=tests/integration/
	cd frontend && npm run test 2>/dev/null || true

migrate:
	cd backend && python3 -m pip install -q -r requirements.txt && python3 -m alembic upgrade head

migrate-down:
	cd backend && python3 -m pip install -q -r requirements.txt && python3 -m alembic downgrade -1

test-integration:
	docker compose up -d
	sleep 30
	DATABASE_URL=postgresql://iaas:iaas@localhost:5432/iaas python3 -m pytest tests/integration/ -v
	docker compose down

lint:
	cd backend && ruff check app/
	cd frontend && npm run lint 2>/dev/null || true

type-check:
	cd backend && mypy app/ 2>/dev/null || true
	cd frontend && npm run type-check 2>/dev/null || true

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

push:
	@if [ -z "$$(git remote -v)" ]; then \
		echo "No remote configured. Run: git remote add origin <your-repo-url>"; \
		exit 1; \
	fi; \
	echo "Pushing main..."; git push -u origin main; \
	echo "Pushing current branch..."; git push -u origin $$(git branch --show-current)
