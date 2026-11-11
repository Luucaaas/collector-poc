#!/usr/bin/env bash
# Test de fumée des services et du front déployés, par l'Ingress (HTTPS sans -k : la CA mkcert est installée
# dans le Mac). Aucun jeton : le cluster n'a pas de client Keycloak de test (les 17 tests
# d'acceptation tournent dans la CI).
#
# Usage : deploy/local/smoke.sh        (code de sortie non nul au premier contrôle en échec)
set -euo pipefail

API="https://api.127.0.0.1.sslip.io"
APP="https://app.127.0.0.1.sslip.io"
fail=0

# Attend (jusqu'à 60 s) qu'une URL réponde avec le code attendu : l'Ingress met quelques secondes
# à prendre en compte un nouvel objet.
check() {   # $1 libellé, $2 code attendu, $3 URL
  local code="" _
  for _ in $(seq 1 30); do
    code="$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "$3" || true)"
    [[ "$code" == "$2" ]] && break
    sleep 2
  done
  if [[ "$code" == "$2" ]]; then
    printf 'OK    %-55s HTTP %s\n' "$1" "$code"
  else
    printf 'ECHEC %-55s HTTP %s (attendu %s)\n' "$1" "$code" "$2" >&2
    fail=1
  fi
}

check "catalogue : liste des catégories (public)" 200 "${API}/catalog/api/v1/categories"
check "catalogue : liste des articles (public)" 200 "${API}/catalog/api/v1/articles"
# Route protégée sans jeton : 401 (notification-service n'a que des routes /me).
check "notification : route protégée sans jeton" 401 "${API}/notification/api/v1/me/notifications"
# Les sondes et les métriques ne sont pas routées par l'Ingress.
check "catalogue : /health/ready hors de l'Ingress" 404 "${API}/catalog/health/ready"
check "catalogue : /metrics hors de l'Ingress" 404 "${API}/catalog/metrics"
check "notification : /health/ready hors de l'Ingress" 404 "${API}/notification/health/ready"
check "notification : /metrics hors de l'Ingress" 404 "${API}/notification/metrics"

# X-Request-ID présent sur une réponse (corrélation des logs).
# Lu dans une variable puis testé (pas de « curl | grep -q » : sous pipefail, grep -q peut fermer le tube
# trop tôt et faire échouer curl).
headers="$(curl -s --max-time 10 -D - -o /dev/null "${API}/catalog/api/v1/categories" || true)"
if grep -qi '^x-request-id: .' <<< "$headers"; then
  printf 'OK    %-55s\n' "catalogue : en-tête X-Request-ID présent"
else
  printf 'ECHEC %-55s\n' "catalogue : en-tête X-Request-ID absent" >&2
  fail=1
fi

# Audit P9-01 (F-06, F-07). Keycloak : l'hôte public n'expose que /realms/ et /resources/ ; la console
# d'administration n'est plus joignable de l'extérieur (L19), la configuration OpenID l'est toujours.
AUTH="https://auth.127.0.0.1.sslip.io"
check "keycloak : console d'administration hors de l'hôte public" 404 "${AUTH}/admin/"
check "keycloak : console du realm master hors de l'hôte public" 404 "${AUTH}/admin/master/console/"
check "keycloak : configuration OpenID du realm collector" 200 "${AUTH}/realms/collector/.well-known/openid-configuration"

# En-têtes de sécurité posés par Traefik (middleware) : HSTS et nosniff sur l'API, HSTS sur Keycloak.
headers="$(curl -s --max-time 10 -D - -o /dev/null "${API}/catalog/api/v1/categories" || true)"
for name in Strict-Transport-Security X-Content-Type-Options Cross-Origin-Resource-Policy; do
  if grep -qi "^${name}: ." <<< "$headers"; then
    printf 'OK    %-55s\n' "catalogue : en-tête ${name} présent"
  else
    printf 'ECHEC %-55s\n' "catalogue : en-tête ${name} absent" >&2
    fail=1
  fi
done
headers="$(curl -s --max-time 10 -D - -o /dev/null "${AUTH}/realms/collector/.well-known/openid-configuration" || true)"
if grep -qi '^strict-transport-security: .' <<< "$headers"; then
  printf 'OK    %-55s\n' "keycloak : en-tête Strict-Transport-Security présent"
else
  printf 'ECHEC %-55s\n' "keycloak : en-tête Strict-Transport-Security absent" >&2
  fail=1
fi

# Front (nginx) : page d'accueil, en-têtes de sécurité, configuration d'exécution, fallback SPA.
check "front : page d'accueil" 200 "${APP}/"
check "front : route de l'application (fallback SPA)" 200 "${APP}/vendre"
check "front : /config.json" 200 "${APP}/config.json"
check "front : fichier caché refusé (/.git/config)" 404 "${APP}/.git/config"

headers="$(curl -s --max-time 10 -D - -o /dev/null "${APP}/" || true)"
for name in Content-Security-Policy X-Content-Type-Options Strict-Transport-Security X-Frame-Options; do
  if grep -qi "^${name}: ." <<< "$headers"; then
    printf 'OK    %-55s\n' "front : en-tête ${name} présent"
  else
    printf 'ECHEC %-55s\n' "front : en-tête ${name} absent" >&2
    fail=1
  fi
done
# La CSP autorise les origines du cluster (API et Keycloak) : sans elles, le navigateur bloquerait les appels.
csp="$(grep -i '^Content-Security-Policy:' <<< "$headers" || true)"
if grep -q 'https://api.127.0.0.1.sslip.io' <<< "$csp" && grep -q 'https://auth.127.0.0.1.sslip.io' <<< "$csp"; then
  printf 'OK    %-55s\n' "front : CSP avec les origines de l'API et de Keycloak"
else
  printf 'ECHEC %-55s\n' "front : CSP sans les origines du cluster" >&2
  fail=1
fi
# config.json : client OIDC du cluster (lu dans une variable, pas de tube vers grep -q).
config="$(curl -s --max-time 10 "${APP}/config.json" || true)"
if grep -q 'collector-web' <<< "$config"; then
  printf 'OK    %-55s\n' "front : config.json contient collector-web"
else
  printf 'ECHEC %-55s\n' "front : config.json sans collector-web" >&2
  fail=1
fi

exit "$fail"
