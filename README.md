# Provenance Suite

A digital asset cataloging and music preservation system built for detailed metadata tracking, rip verification, and storage provenance across physical and digital releases.

---

## Architectural Summary

The system is built on **Clean Architecture and Domain-Driven Design (DDD)** principles, strictly isolating domain logic from framework and storage concerns:

* **Backend Core**: Python 3.11 with FastAPI, SQLAlchemy 2.0 (asyncpg), PostgreSQL, and Alembic migrations.
* **Authentication**: JWT access tokens with single-use rotating refresh token families stored in Redis, protected by Argon2id password hashing with pepper injection and non-existent account verification timing equalization.
* **Object Storage**: MinIO (S3-compatible) image pipeline generating Lanczos-resampled 500px web covers and Base64 ThumbHash strings on upload.
* **Background Worker**: ARQ worker running scheduled nightly PostgreSQL custom-format (`pg_dump -Fc`) backups to private storage with automated 14-day retention pruning.
* **Frontend Application**: Angular 19+ standalone component tree built on reactive Signals, featuring automatic request correlation tracking and non-blocking JWT refresh retry queuing.
* **Reverse Proxy Gateway**: Caddy server handling unified TLS termination and sub-path routing (`/api/*`, `/provenance-covers/*`, `/*`).

---

## System Requirements

* **Python**: 3.11+
* **Node.js**: 22+ & npm 10+
* **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (for Python virtual environment management)
* **Containers**: Docker & Docker Compose

---

## Quickstart (Development Setup)

### 1. Environment Configuration

Copy default configuration files into place:

```bash
cp backend/.env.example backend/.env
```

### 2. Workspace Installation

Install dependencies across both backend and frontend layers:

```bash
make install
```

### 3. Spin Up Infrastructure Services

Launch PostgreSQL 16, Redis 7.2, and MinIO object storage:

```bash
make db-up
```

### 4. Execute Schema Migrations

Apply database schema to head:

```bash
make db-migrate
```

### 5. Seed Initial Superuser Account

Generate an admin account with a randomized password:

```bash
make db-seed-admin
```

### 6. Run Application Components

In separate terminal sessions:

```bash
make run-backend    # API server running on http://localhost:8000
make run-worker     # ARQ background task process
make run-frontend   # Angular UI running on http://localhost:4200
```

Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## Testing & Quality Assurance

Execute the complete backend and frontend test suites:

```bash
# Run all tests
make test

# Run backend tests only (pytest)
make test-backend

# Run frontend tests only (Vitest)
make test-frontend
```

Code formatting and static analysis:

```bash
# Lint codebases
make lint

# Format codebases
make format
```

---

## Production Deployment

To run the complete system behind Caddy in production mode:

```bash
# Build production container images
make prod-build

# Launch all production containers in detached mode
make prod-up
```

The system will be accessible on port `8088` by default. `APP_PORT` can be configured in `.env` file.