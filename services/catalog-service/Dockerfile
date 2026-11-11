# Étape 1 : environnement virtuel construit par uv, aux versions figées par uv.lock
FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.6@sha256:af22a52f5eafef3d78e551599d405c02df61919d18028f0cea8eda93bc9986d0 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable

# Étape 2 : image d'exécution, sans uv ni outils de développement, utilisateur non-root
FROM python:3.12-slim@sha256:e695ab189fa2d082b1c61c69a6b888a5adeca61ceeccad107b1ed2a125721a9e
# Traçabilité (docs/01-qualite/cicd.md, section 4) : le commit et le dépôt sont lisibles par `docker inspect`.
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.source=https://github.com/Luucaaas/collector-poc
# zlib1g : correctif DSA-6613-1 (CVE-2026-76844, CVE-2026-85091), présent seulement dans le dépôt security
# de Debian, pas encore dans l'image de base (audit P9-01, F-01). Contenu dépendant des dépôts au moment
# du build (limite L25) : retirer cette ligne dès qu'un digest corrigé de python:3.12-slim a au moins 14 jours.
RUN apt-get update && apt-get install -y --no-install-recommends --only-upgrade zlib1g && rm -rf /var/lib/apt/lists/*
RUN useradd --system --uid 10001 --no-create-home app
# pip ne sert pas à l'exécution (les dépendances sont dans /app/.venv, construit par uv) : le retirer
# supprime ses CVE de l'image (audit P9-01, F-03) et empêche d'installer un paquet dans un conteneur compromis.
RUN rm -rf /usr/local/lib/python3.12/site-packages/pip /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
           /usr/local/bin/pip /usr/local/bin/pip3 /usr/local/bin/pip3.12
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY alembic.ini ./
COPY migrations ./migrations
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER 10001
EXPOSE 8000
# Forme exec : uvicorn est le PID 1, reçoit SIGTERM et ferme le pool avant de s'arrêter.
CMD ["uvicorn", "--factory", "catalog.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
