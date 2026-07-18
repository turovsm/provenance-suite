.PHONY: install lint format run-backend run-frontend db-up db-down db-logs db-clean

BACKEND_DIR := backend
FRONTEND_DIR := frontend

install:
	@echo "Installing full-stack application workspace environments via uv..."
	@command -v uv >/dev/null 2>&1 || (echo "Error: uv is not installed." && exit 1)
	cd $(BACKEND_DIR) && uv venv .venv --python 3.11
	cd $(BACKEND_DIR) && uv pip install -e . ruff pytest httpx
	cd $(BACKEND_DIR) && uv pip compile pyproject.toml -o requirements.txt
	cd $(FRONTEND_DIR) && npm install && npm install --save-dev prettier @angular-eslint/schematics

lint:
	cd $(BACKEND_DIR) && .venv/bin/ruff check src/
	cd $(FRONTEND_DIR) && npx ng lint

format:
	cd $(BACKEND_DIR) && .venv/bin/ruff check --fix src/ && .venv/bin/ruff format src/
	cd $(FRONTEND_DIR) && npx prettier --write "src/**/*.{ts,html,css,json}"

run-backend:
	cd $(BACKEND_DIR) && .venv/bin/uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

run-frontend:
	cd $(FRONTEND_DIR) && npx ng serve --host 127.0.0.1 --port 4200

db-up:
	@echo "Launching containerized PostgreSQL data persistence layer..."
	docker compose --env-file $(BACKEND_DIR)/.env up -d

db-down:
	@echo "Stopping containerized PostgreSQL data persistence layer..."
	docker compose --env-file $(BACKEND_DIR)/.env down

db-logs:
	docker compose --env-file $(BACKEND_DIR)/.env logs -f db

db-clean:
	@echo "Executing destructive cleanup of container storage tracks..."
	docker compose --env-file $(BACKEND_DIR)/.env down -v