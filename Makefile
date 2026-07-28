-include backend/.env
export

.PHONY: help install lint format test test-backend test-backend-unit test-backend-integration test-frontend run-backend run-worker run-frontend db-up db-down db-logs db-clean db-migrate db-revision db-seed-admin prod-build prod-up prod-down prod-logs

BACKEND_DIR := backend
FRONTEND_DIR := frontend
BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 4200
APP_PORT ?= 8088

help: ## Display available Makefile commands
	@echo "\nProvenance Suite Operational Commands:\n"
	@grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Install workspace dependencies (backend via uv, frontend via npm)
	@echo "Installing workspace environments..."
	@command -v uv >/dev/null 2>&1 || (echo "Error: uv is not installed." && exit 1)
	cd $(BACKEND_DIR) && uv venv .venv --python 3.11
	cd $(BACKEND_DIR) && uv pip install -e ".[dev]"
	cd $(BACKEND_DIR) && uv pip compile pyproject.toml -o requirements.txt
	cd $(FRONTEND_DIR) && npm install

lint: ## Execute static analysis and linters for backend and frontend
	cd $(BACKEND_DIR) && .venv/bin/ruff check src/ tests/
	cd $(FRONTEND_DIR) && npx ng lint

format: ## Format codebase (Ruff for backend, Prettier for frontend)
	cd $(BACKEND_DIR) && .venv/bin/ruff check --fix src/ && .venv/bin/ruff format src/ tests/
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,html,css,json}"

test: test-backend test-frontend ## Run complete test suite across backend and frontend

test-backend: ## Run all Python backend tests (unit and integration)
	cd $(BACKEND_DIR) && .venv/bin/pytest -v

test-backend-unit: ## Run backend unit tests only
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/unit -v

test-backend-integration: ## Run backend integration tests only
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/integration -v

test-frontend: ## Run Angular frontend unit tests via Vitest
	cd $(FRONTEND_DIR) && npx ng test --watch=false

run-backend: ## Launch local development API server (FastAPI/Uvicorn)
	cd $(BACKEND_DIR) && .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port $(BACKEND_PORT)

run-worker: ## Launch background task worker (ARQ)
	cd $(BACKEND_DIR) && .venv/bin/arq src.infrastructure.worker.tasks.WorkerSettings

run-frontend: ## Launch local Angular development server
	cd $(FRONTEND_DIR) && npx ng serve --host 0.0.0.0 --port $(FRONTEND_PORT)

db-up: ## Spin up local infrastructure services (PostgreSQL, Redis, MinIO)
	docker compose --env-file $(BACKEND_DIR)/.env up -d db redis minio
	@echo "Waiting for PostgreSQL to complete internal initialization..."
	@until docker compose --env-file $(BACKEND_DIR)/.env exec -T db pg_isready -U $${POSTGRES_USER:-postgres} -d $${POSTGRES_DB:-provenance_vault} > /dev/null 2>&1; do \
		sleep 1; \
	done
	@echo "PostgreSQL is fully online and accepting connections."

db-down: ## Stop local infrastructure containers
	docker compose --env-file $(BACKEND_DIR)/.env stop db redis minio

db-logs: ## Tail logs for development infrastructure containers
	docker compose --env-file $(BACKEND_DIR)/.env logs -f db redis minio

db-migrate: ## Apply database migrations to head via Alembic
	cd $(BACKEND_DIR) && .venv/bin/alembic upgrade head

db-revision: ## Generate a new Alembic database migration
	@read -p "Enter migration description: " msg; \
	cd $(BACKEND_DIR) && .venv/bin/alembic revision --autogenerate -m "$$msg"

db-seed-admin: ## Create initial superuser account with generated credentials
	cd $(BACKEND_DIR) && .venv/bin/python -m src.cli.create_superuser

db-clean: ## Stop infrastructure containers and purge volumes
	docker compose --env-file $(BACKEND_DIR)/.env down -v

prod-build: ## Build all production Docker container images
	docker compose --env-file $(BACKEND_DIR)/.env build

prod-up: ## Launch production container stack (Caddy, Frontend, Backend, Worker, DB, Redis, MinIO)
	docker compose --env-file $(BACKEND_DIR)/.env up -d

prod-down: ## Stop full production container stack
	docker compose --env-file $(BACKEND_DIR)/.env down

prod-logs: ## Tail logs across all production stack containers
	docker compose --env-file $(BACKEND_DIR)/.env logs -f