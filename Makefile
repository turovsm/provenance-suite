-include backend/.env
export

.PHONY: help install lint format test test-backend test-backend-unit test-backend-integration test-backend-cov test-frontend run-backend run-worker run-frontend db-up db-down db-logs db-clean db-shell db-redis-cli db-migrate db-revision db-seed-admin db-seed-events backup-list backup-verify backup-restore backup-dump-logical backup-base-physical prod-build prod-up prod-down prod-logs

BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 4200
APP_PORT ?= 8088

# HELP & DISCOVERY

help: ## Display available Makefile commands
	@echo "\n\033[1;37mProvenance Suite Operational Commands:\033[0m\n"
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""

# WORKSPACE SETUP & DEPENDENCIES

install: ## Install workspace dependencies (backend via uv, frontend via npm)
	@echo "Installing workspace environments..."
	@command -v uv >/dev/null 2>&1 || (echo "Error: uv is not installed." && exit 1)
	cd $(BACKEND_DIR) && uv venv .venv --python 3.11
	cd $(BACKEND_DIR) && uv pip install -e ".[dev]"
	cd $(BACKEND_DIR) && uv pip compile pyproject.toml -o requirements.txt
	cd $(FRONTEND_DIR) && npm install

# CODE QUALITY & FORMATTING

lint: ## Execute static analysis and linters for backend and frontend
	cd $(BACKEND_DIR) && .venv/bin/ruff check src/ tests/
	cd $(FRONTEND_DIR) && npx ng lint

format: ## Format and autofix codebase (Ruff for backend, Prettier for frontend)
	cd $(BACKEND_DIR) && .venv/bin/ruff check --fix src/ tests/ && .venv/bin/ruff format src/ tests/
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,html,css,json}"

# TESTING & VERIFICATION

test: test-backend test-frontend ## Run complete test suite across backend and frontend

test-backend: ## Run all Python backend tests (unit and integration)
	cd $(BACKEND_DIR) && .venv/bin/pytest -v

test-backend-unit: ## Run backend unit tests only
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/unit -v

test-backend-integration: ## Run backend integration tests only
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/integration -v

test-backend-cov: ## Run backend tests with terminal missing-line coverage report
	cd $(BACKEND_DIR) && .venv/bin/pytest --cov=src --cov-report=term-missing --cov-report=html tests/

test-frontend: ## Run Angular frontend unit tests via Vitest
	cd $(FRONTEND_DIR) && npx ng test --watch=false

# LOCAL DEVELOPMENT SERVERS

run-backend: ## Launch local development API server (FastAPI/Uvicorn)
	cd $(BACKEND_DIR) && .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

run-worker: ## Launch background task worker (ARQ)
	cd $(BACKEND_DIR) && .venv/bin/arq src.infrastructure.worker.tasks.WorkerSettings

run-frontend: ## Launch local Angular development server
	cd $(FRONTEND_DIR) && npx ng serve --host 0.0.0.0 --port $(FRONTEND_PORT)

# LOCAL INFRASTRUCTURE & DATABASE

db-up: ## Spin up local infrastructure services (PostgreSQL, Redis, MinIO, MinIO-Init)
	docker compose --env-file $(BACKEND_DIR)/.env up -d minio redis minio-init postgres
	@echo "Waiting for PostgreSQL to complete internal initialization..."
	@until docker compose --env-file $(BACKEND_DIR)/.env exec -T postgres pg_isready -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-provenance_vault} > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "PostgreSQL is online and accepting connections."

db-down: ## Stop local infrastructure containers
	docker compose --env-file $(BACKEND_DIR)/.env stop postgres redis minio minio-init

db-logs: ## Tail logs for development infrastructure containers
	docker compose --env-file $(BACKEND_DIR)/.env logs -f postgres redis minio

db-clean: ## Stop infrastructure containers and purge persistent storage volumes
	docker compose --env-file $(BACKEND_DIR)/.env down -v

db-shell: ## Open an interactive psql shell inside the running PostgreSQL container
	docker compose --env-file $(BACKEND_DIR)/.env exec -it postgres psql -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-provenance_vault}

db-redis-cli: ## Open an interactive redis-cli shell inside the running Redis container
	docker compose --env-file $(BACKEND_DIR)/.env exec -it redis redis-cli

db-migrate: ## Apply database migrations to head via Alembic
	cd $(BACKEND_DIR) && .venv/bin/alembic upgrade head

db-revision: ## Generate a new Alembic database migration
	@read -p "Enter migration description: " msg; \
	cd $(BACKEND_DIR) && .venv/bin/alembic revision --autogenerate -m "$$msg"

db-seed-admin: ## Create initial superuser account with generated credentials
	cd $(BACKEND_DIR) && .venv/bin/python -m src.cli.create_superuser

db-seed-events: ## Transfer event data from json file to the DB
	cd $(BACKEND_DIR) && .venv/bin/python -m src.cli.seed_events events.json

# BACKUP & DISASTER RECOVERY

backup-list: ## List all logical dumps and physical WAL-G snapshots in MinIO
	cd $(BACKEND_DIR) && .venv/bin/python -m src.cli.restore_db list

backup-verify: ## Verify SHA256 integrity manifest for latest logical dump
	cd $(BACKEND_DIR) && .venv/bin/python -m src.cli.restore_db restore-logical --verify-only

backup-restore: ## Restore database from latest cold logical dump (parallel pg_restore)
	@if docker compose --env-file $(BACKEND_DIR)/.env ps --status running --services | grep -q "^backend$$"; then \
		docker compose --env-file $(BACKEND_DIR)/.env exec -T backend python -m src.cli.restore_db restore-logical --jobs 4; \
	else \
		docker compose --env-file $(BACKEND_DIR)/.env run --rm -T backend python -m src.cli.restore_db restore-logical --jobs 4; \
	fi

backup-dump-logical: ## Execute a zero-RAM cold logical dump and upload to MinIO
	@if docker compose --env-file $(BACKEND_DIR)/.env ps --status running --services | grep -q "^worker$$"; then \
		docker compose --env-file $(BACKEND_DIR)/.env exec -T worker python -c "import asyncio; from src.infrastructure.worker.tasks import cold_logical_dump; asyncio.run(cold_logical_dump({}))"; \
	else \
		docker compose --env-file $(BACKEND_DIR)/.env run --rm -T worker python -c "import asyncio; from src.infrastructure.worker.tasks import cold_logical_dump; asyncio.run(cold_logical_dump({}))"; \
	fi

backup-base-physical: ## Execute a physical base backup snapshot via WAL-G
	docker compose --env-file $(BACKEND_DIR)/.env exec -u postgres -T postgres env PGUSER=$${POSTGRES_USER:-postgres} PGDATABASE=$${POSTGRES_DB:-provenance_vault} PGPASSWORD=$${POSTGRES_PASSWORD:-postgres} wal-g backup-push /var/lib/postgresql/data
	docker compose --env-file $(BACKEND_DIR)/.env exec -u postgres -T postgres env PGUSER=$${POSTGRES_USER:-postgres} PGDATABASE=$${POSTGRES_DB:-provenance_vault} PGPASSWORD=$${POSTGRES_PASSWORD:-postgres} wal-g delete retain FULL $${WALG_BASE_BACKUP_RETENTION_COUNT:-4} --confirm

# PRODUCTION CONTAINER STACK

prod-build: ## Build all production Docker container images
	docker compose --env-file $(BACKEND_DIR)/.env build

prod-up: ## Launch production container stack (Caddy, Frontend, Backend, Worker, DB, Redis, MinIO)
	docker compose --env-file $(BACKEND_DIR)/.env up -d

prod-down: ## Stop full production container stack
	docker compose --env-file $(BACKEND_DIR)/.env down

prod-logs: ## Tail logs across all production stack containers
	docker compose --env-file $(BACKEND_DIR)/.env logs -f