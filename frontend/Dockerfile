# Étape 1 : build de production (Vite), aux versions figées par package-lock.json.
# Image épinglée par le digest de l'index multi-architecture (node 22.23.4, Alpine 3.24).
FROM node:22.23.4-alpine3.24@sha256:0e1754758c2df4cfa3e68d59e2e1b7374bb7fd9ea6328eaaacf15cc934af8202 AS builder
WORKDIR /app
COPY package.json package-lock.json ./
# --ignore-scripts : aucun script d'installation de paquet n'est exécuté (chaîne d'approvisionnement).
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

# Stage 2: runtime image. Official unprivileged nginx (user 101, port 8080),
# pinned by digest (base nginx 1.30.6, stable branch). It only holds dist/ and the configuration.
FROM nginxinc/nginx-unprivileged:1.30.6-alpine3.24@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03
# Traçabilité (docs/01-qualite/cicd.md, section 4) : le commit et le dépôt sont lisibles par `docker inspect`.
ARG GIT_SHA=unknown
LABEL org.opencontainers.image.revision=$GIT_SHA \
      org.opencontainers.image.source=https://github.com/Luucaaas/collector-poc

# Origines autorisées pour les appels réseau (CSP connect-src), en plus de l'origine du front :
# l'API et Keycloak. Valeur par défaut = celles du config.json fourni (cluster local) ; à
# remplacer au démarrage (-e CSP_CONNECT_SRC=...) ailleurs. Jamais de joker.
ENV CSP_CONNECT_SRC="https://api.127.0.0.1.sslip.io https://auth.127.0.0.1.sslip.io" \
    NGINX_ENVSUBST_FILTER="^CSP_"

# apk upgrade, then nginx and its 4 modules moved to 1.30.7 (CVE fixes) from nginx.org, with the
# repository and signing key the base image already uses (never --allow-untrusted). Owners reset to root
# by the packages are restored. Drop this once an upstream image ships 1.30.7 (the published digest is authoritative).
USER root
RUN apk upgrade --no-cache \
 && apk add --no-cache --repositories-file /dev/null -X https://nginx.org/packages/alpine/v3.24/main nginx=1.30.7-r1 nginx-module-xslt=1.30.7-r1 nginx-module-geoip=1.30.7-r1 nginx-module-image-filter=1.30.7-r1 nginx-module-njs=1.30.7.1.0.2-r1 \
 && rm -f /etc/nginx/nginx.conf.apk-new /etc/nginx/conf.d/default.conf.apk-new \
 && cd /etc/nginx && chown -h nginx:root fastcgi.conf fastcgi_params mime.types scgi_params uwsgi_params modules && chmod 664 fastcgi.conf fastcgi_params mime.types scgi_params uwsgi_params
COPY nginx/default.conf.template nginx/security-headers.inc.template /etc/nginx/templates/
COPY --from=builder /app/dist /usr/share/nginx/html
# Le dossier de sortie du modèle (/etc/nginx/conf.d) est déjà modifiable par l'utilisateur 101.
USER 101
EXPOSE 8080
