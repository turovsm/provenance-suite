.PHONY: install lint format run-backend run-frontend

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