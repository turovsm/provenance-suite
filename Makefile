.PHONY: install lint format test-backend test-backend-unit test-backend-integration test-frontend run-backend run-worker run-frontend db-up db-down db-logs db-clean db-migrate db-revision

BACKEND_DIR := backend
FRONTEND_DIR := frontend

install:
	@echo "Installing workspace environments via uv and npm..."
	@command -v uv >/dev/null 2>&1 || (echo "Error: uv is not installed." && exit 1)
	cd $(BACKEND_DIR) && uv venv .venv --python 3.11
	cd $(BACKEND_DIR) && uv pip install -e ".[dev]"
	cd $(BACKEND_DIR) && uv pip compile pyproject.toml -o requirements.txt
	cd $(FRONTEND_DIR) && npm install && npm install --save-dev prettier @angular-eslint/schematics

lint:
	cd $(BACKEND_DIR) && .venv/bin/ruff check src/ tests/
	cd $(FRONTEND_DIR) && npx ng lint

format:
	cd $(BACKEND_DIR) && .venv/bin/ruff check --fix src/ && .venv/bin/ruff format src/ tests/
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,html,css,json}"

test-backend:
	cd $(BACKEND_DIR) && .venv/bin/pytest -v

test-backend-unit:
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/unit -v

test-backend-integration:
	cd $(BACKEND_DIR) && .venv/bin/pytest tests/integration -v

test-frontend:
	cd $(FRONTEND_DIR) && npx ng test --watch=false

run-backend:
	cd $(BACKEND_DIR) && .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	cd $(BACKEND_DIR) && .venv/bin/arq src.infrastructure.worker.tasks.WorkerSettings

run-frontend:
	cd $(FRONTEND_DIR) && npx ng serve --host 0.0.0.0 --port 4200

db-up:
	@echo "Launching PostgreSQL, Redis & MinIO containers..."
	docker compose --env-file $(BACKEND_DIR)/.env up -d

db-down:
	@echo "Stopping database & storage containers..."
	docker compose --env-file $(BACKEND_DIR)/.env down

db-logs:
	docker compose --env-file $(BACKEND_DIR)/.env logs -f

db-migrate:
	@echo "Executing database migrations..."
	cd $(BACKEND_DIR) && .venv/bin/alembic upgrade head

db-revision:
	@read -p "Enter migration message: " msg; \
	cd $(BACKEND_DIR) && .venv/bin/alembic revision --autogenerate -m "$$msg"

db-clean:
	@echo "Purging containerized persistent volumes..."
	docker compose --env-file $(BACKEND_DIR)/.env down -v