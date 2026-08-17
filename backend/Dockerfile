# Build Stage
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m venv /app/.venv && \
    /app/.venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Runner Stage
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gnupg \
    tar \
    zstd \
    lz4 \
    libpq5 \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg \
    && echo "deb http://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update && apt-get install -y --no-install-recommends postgresql-client-16 \
    && curl -fsSL https://github.com/wal-g/wal-g/releases/download/v3.0.3/wal-g-pg-ubuntu-20.04-amd64.tar.gz -o /tmp/wal-g.tar.gz \
    && tar -xzf /tmp/wal-g.tar.gz -C /usr/local/bin/ \
    && mv /usr/local/bin/wal-g-pg-ubuntu-20.04-amd64 /usr/local/bin/wal-g \
    && chmod +x /usr/local/bin/wal-g \
    && rm -rf /tmp/wal-g.tar.gz /var/lib/apt/lists/* \
    && groupadd -r provenance && useradd -r -g provenance -d /app -s /sbin/nologin appuser \
    && mkdir -p /tmp/provenance_backups \
    && chown -R appuser:provenance /app /tmp/provenance_backups

COPY --from=builder --chown=appuser:provenance /app/.venv /app/.venv
COPY --chown=appuser:provenance . .

RUN chmod +x /app/entrypoint.sh

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]