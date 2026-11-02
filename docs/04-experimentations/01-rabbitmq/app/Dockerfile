# Étape 1 : construction de l'environnement virtuel avec uv (versions du uv.lock)
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev

# Étape 2 : image d'exécution minimale, utilisateur non-root
FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001
CMD ["python", "-m", "exp.consumer"]
