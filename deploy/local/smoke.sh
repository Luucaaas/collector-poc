#!/usr/bin/env bash
# Test de fumée des services déployés, par l'Ingress (HTTPS sans -k : la CA mkcert est installée
# dans le Mac). Aucun jeton : le cluster n'a pas de client Keycloak de test (les 17 tests
# d'acceptation tournent dans la CI).
#
# Usage : deploy/local/smoke.sh        (code de sortie non nul au premier contrôle en échec)
set -euo pipefail

API="https://api.127.0.0.1.sslip.io"
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

exit "$fail"
