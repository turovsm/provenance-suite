.PHONY: install lint format test-backend test-frontend run-backend run-frontend db-up db-down db-logs db-clean db-migrate db-revision

BACKEND_DIR := backend
FRONTEND_DIR := frontend

install:
	@echo "Installing workspace environments via uv and npm..."
	@command -v uv >/dev/null 2>&1 || (echo "Error: uv is not installed." && exit 1)
	cd $(BACKEND_DIR) && uv venv .venv --python 3.11
	cd $(BACKEND_DIR) && uv pip install -e . ruff pytest pytest-asyncio engineering-notation httpx minio
	cd $(BACKEND_DIR) && uv pip compile pyproject.toml -o requirements.txt
	cd $(FRONTEND_DIR) && npm install && npm install --save-dev prettier @angular-eslint/schematics

lint:
	cd $(BACKEND_DIR) && .venv/bin/ruff check src/
	cd $(FRONTEND_DIR) && npx ng lint

format:
	cd $(BACKEND_DIR) && .venv/bin/ruff check --fix src/ && .venv/bin/ruff format src/
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,html,css,json}"

test-backend:
	cd $(BACKEND_DIR) && .venv/bin/pytest -v

test-frontend:
	cd $(FRONTEND_DIR) && npx ng test --watch=false

run-backend:
	cd $(BACKEND_DIR) && .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd $(FRONTEND_DIR) && npx ng serve --host 0.0.0.0 --port 4200

db-up:
	@echo "Launching PostgreSQL & MinIO containers..."
	docker compose --env-file $(BACKEND_DIR)/.env up -d

db-down:
	@echo "Stopping database & object storage containers..."
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