#!/usr/bin/env bash
# Smoke test of the deployed services and front end, through the Ingress (HTTPS without -k: the mkcert CA is installed
# in the Mac). No token: the cluster has no test Keycloak client (the 17 acceptance
# tests run in the CI).
#
# Usage: deploy/local/smoke.sh   (non-zero exit code if a check fails; docs/07-soutenance/demo/preparer.sh counts the OK and FAIL prefixes)
set -euo pipefail

API="https://api.127.0.0.1.sslip.io"
APP="https://app.127.0.0.1.sslip.io"
fail=0

# Waits (up to 60 s) for a URL to answer with the expected code: the Ingress takes a few seconds
# to pick up a new object.
check() {   # $1 label, $2 expected code, $3 URL
  local code="" _
  for _ in $(seq 1 30); do
    code="$(curl -s --max-time 10 -o /dev/null -w '%{http_code}' "$3" || true)"
    [[ "$code" == "$2" ]] && break
    sleep 2
  done
  if [[ "$code" == "$2" ]]; then
    printf 'OK    %-55s HTTP %s\n' "$1" "$code"
  else
    printf 'FAIL  %-55s HTTP %s (expected %s)\n' "$1" "$code" "$2" >&2
    fail=1
  fi
}

check "catalog: category list (public)" 200 "${API}/catalog/api/v1/categories"
check "catalog: article list (public)" 200 "${API}/catalog/api/v1/articles"
# Protected route without a token: 401 (notification-service only has /me routes).
check "notification: protected route without a token" 401 "${API}/notification/api/v1/me/notifications"
# The probes and the metrics are not routed by the Ingress.
check "catalog: /health/ready outside the Ingress" 404 "${API}/catalog/health/ready"
check "catalog: /metrics outside the Ingress" 404 "${API}/catalog/metrics"
check "notification: /health/ready outside the Ingress" 404 "${API}/notification/health/ready"
check "notification: /metrics outside the Ingress" 404 "${API}/notification/metrics"

# X-Request-ID present on a response (log correlation).
# Read into a variable then tested (no "curl | grep -q": under pipefail, grep -q may close the pipe
# too early and make curl fail).
headers="$(curl -s --max-time 10 -D - -o /dev/null "${API}/catalog/api/v1/categories" || true)"
if grep -qi '^x-request-id: .' <<< "$headers"; then
  printf 'OK    %-55s\n' "catalog: X-Request-ID header present"
else
  printf 'FAIL  %-55s\n' "catalog: X-Request-ID header missing" >&2
  fail=1
fi

# Audit P9-01 (F-06, F-07). Keycloak: the public host only exposes /realms/ and /resources/; the
# admin console is no longer reachable from outside (L19), the OpenID configuration still is.
AUTH="https://auth.127.0.0.1.sslip.io"
check "keycloak: admin console outside the public host" 404 "${AUTH}/admin/"
check "keycloak: master realm console outside the public host" 404 "${AUTH}/admin/master/console/"
check "keycloak: OpenID configuration of the collector realm" 200 "${AUTH}/realms/collector/.well-known/openid-configuration"

# Security headers set by Traefik (middleware): HSTS and nosniff on the API, HSTS on Keycloak.
headers="$(curl -s --max-time 10 -D - -o /dev/null "${API}/catalog/api/v1/categories" || true)"
for name in Strict-Transport-Security X-Content-Type-Options Cross-Origin-Resource-Policy; do
  if grep -qi "^${name}: ." <<< "$headers"; then
    printf 'OK    %-55s\n' "catalog: ${name} header present"
  else
    printf 'FAIL  %-55s\n' "catalog: ${name} header missing" >&2
    fail=1
  fi
done
headers="$(curl -s --max-time 10 -D - -o /dev/null "${AUTH}/realms/collector/.well-known/openid-configuration" || true)"
if grep -qi '^strict-transport-security: .' <<< "$headers"; then
  printf 'OK    %-55s\n' "keycloak: Strict-Transport-Security header present"
else
  printf 'FAIL  %-55s\n' "keycloak: Strict-Transport-Security header missing" >&2
  fail=1
fi

# Front end (nginx): home page, security headers, runtime configuration, SPA fallback.
check "front: home page" 200 "${APP}/"
check "front: application route (SPA fallback)" 200 "${APP}/vendre"
check "front: /config.json" 200 "${APP}/config.json"
check "front: hidden file refused (/.git/config)" 404 "${APP}/.git/config"

headers="$(curl -s --max-time 10 -D - -o /dev/null "${APP}/" || true)"
for name in Content-Security-Policy X-Content-Type-Options Strict-Transport-Security X-Frame-Options; do
  if grep -qi "^${name}: ." <<< "$headers"; then
    printf 'OK    %-55s\n' "front: ${name} header present"
  else
    printf 'FAIL  %-55s\n' "front: ${name} header missing" >&2
    fail=1
  fi
done
# The CSP allows the cluster origins (API and Keycloak): without them, the browser would block the calls.
csp="$(grep -i '^Content-Security-Policy:' <<< "$headers" || true)"
if grep -q 'https://api.127.0.0.1.sslip.io' <<< "$csp" && grep -q 'https://auth.127.0.0.1.sslip.io' <<< "$csp"; then
  printf 'OK    %-55s\n' "front: CSP with the API and Keycloak origins"
else
  printf 'FAIL  %-55s\n' "front: CSP without the cluster origins" >&2
  fail=1
fi
# config.json: OIDC client of the cluster (read into a variable, no pipe to grep -q).
config="$(curl -s --max-time 10 "${APP}/config.json" || true)"
if grep -q 'collector-web' <<< "$config"; then
  printf 'OK    %-55s\n' "front: config.json contains collector-web"
else
  printf 'FAIL  %-55s\n' "front: config.json without collector-web" >&2
  fail=1
fi

exit "$fail"
