.PHONY: install lint format run-backend run-frontend db-up db-down db-logs db-clean

BACKEND_DIR := backend
FRONTEND_DIR := frontend

install:
	@echo "Installing full-stack application workspace environments..."
	cd $(BACKEND_DIR) && python3 -m venv .venv && .venv/bin/pip install --upgrade pip && .venv/bin/pip install -e . ruff pytest httpx
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
	docker compose up -d

db-down:
	@echo "Stopping containerized PostgreSQL data persistence layer..."
	docker compose down

db-logs:
	docker compose logs -f db

db-clean:
	@echo "Executing destructive cleanup of container storage tracks..."
	docker compose down -v