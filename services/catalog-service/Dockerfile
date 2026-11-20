# Stage 1: virtual environment built by uv, with the versions pinned by uv.lock
FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# Stage 2: runtime image, without uv or development tools, non-root user
FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e
# Traceability (docs/01-qualite/cicd.md, section 4): the commit and the repository can be read with `docker inspect`.
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.source=https://github.com/Luucaaas/collector-poc
# zlib1g: fix DSA-6613-1 (CVE-2026-76844, CVE-2026-85091), only in Debian's security repository
# and not yet in the base image (audit P9-01, F-01). Content depends on the repositories at
# build time (limit L25): remove this line as soon as a fixed python:3.12-slim digest is 14 days old.
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --no-create-home app
# pip is not used at runtime (the dependencies are in /app/.venv, built by uv): removing it
# removes its CVEs from the image (audit P9-01, F-03) and prevents installing a package in a compromised container.
RUN rm -rf /usr/local/lib/python3.12/site-packages/pip /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
           /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.12
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8000
# Exec form: uvicorn is PID 1, receives SIGTERM and closes the pool before stopping.
CMD ["uvicorn", "--factory", "catalog.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
