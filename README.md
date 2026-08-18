# Provenance Suite

A web application for cataloging music collections, physical CD/DVD/BD rips, artwork scans, and archival backups.

---

## Overview

Provenance Suite tracks albums across physical and digital formats, preserving metadata such as track credits, cue sheets, AccurateRip verification summaries, rip logs, and storage locations.

* **Backend**: FastAPI (Python 3.11), PostgreSQL 16, Redis 7.2, SQLAlchemy (asyncpg), Alembic
* **Background Worker**: ARQ for scheduled database dumps and background file hashing
* **Storage**: MinIO for album art, scans, and database snapshots
* **Frontend**: Angular 19 (TypeScript)
* **Reverse Proxy**: Caddy

---

## Requirements

* Python 3.11+
* Node.js 22+ & npm
* [`uv`](https://github.com/astral-sh/uv) (Python package manager)
* Docker and Docker Compose

---

## Development Setup

### 1. Environment Configuration

Copy the example environment file:

```bash
cp backend/.env.example backend/.env
```

### 2. Install Dependencies

Install Python virtual environment packages and frontend node modules:

```bash
make install
```

### 3. Start Database and Storage Services

Start local PostgreSQL, Redis, and MinIO containers:

```bash
make db-up
```

### 4. Run Database Migrations

Apply current database migrations:

```bash
make db-migrate
```

### 5. Create Admin Account

Seed an initial superuser account:

```bash
make db-seed-admin
```

### 6. Run Application

Run the backend API, background worker, and frontend dev server in separate terminals:

```bash
make run-backend    # API server at http://localhost:8000
make run-worker     # Background task worker
make run-frontend   # Web interface at http://localhost:4200
```

API documentation is available at `http://localhost:8000/docs`.

---

## Tests and Linting

Run test suites:

```bash
# Run all tests
make test

# Run backend unit tests
make test-backend-unit

# Run frontend tests
make test-frontend
```

Run code linters and formatters:

```bash
# Check linting (ruff, ng lint)
make lint

# Auto-format code
make format
```

---

## Production Setup

To run all services containerized behind Caddy:

```bash
# Build Docker images
make prod-build

# Start containers in background
make prod-up
```

The application will be available at `http://localhost:8088` (or the port defined in `backend/.env`).

Stop production containers:

```bash
make prod-down
```