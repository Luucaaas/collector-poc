# Étape 1 : environnement virtuel construit par uv, aux versions figées par uv.lock
FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# Étape 2 : image d'exécution, sans uv ni outils de développement, utilisateur non-root
FROM python:3.12-slim@sha256:b18b261e1b4974b4f321451ad5251ded85abb22c2b8b262da527dda1d031ab30
# Traçabilité (docs/01-qualite/cicd.md, section 4) : le commit et le dépôt sont lisibles par `docker inspect`.
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.source=https://github.com/Luucaaas/collector-poc
RUN useradd --system --uid 10001 --no-create-home app
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8000
# Forme exec : uvicorn est le PID 1, reçoit SIGTERM et ferme le pool avant de s'arrêter.
CMD ["uvicorn", "--factory", "catalog.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
