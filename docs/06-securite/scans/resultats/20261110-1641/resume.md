# Synthèse de l'exécution 20261110-1641

## Trivy : images (toutes sévérités, sans --ignore-unfixed)

| Image | Arch. | Système | CRITICAL | HIGH | MEDIUM | LOW | UNKNOWN | Total | CVE distinctes | Sans correctif | Secrets |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| catalog-service | amd64 | debian 13.7 | 0 (0) | 49 (47) | 82 (74) | 66 (65) | 0 (0) | 197 | 95 | 186 (CVE distinctes : H 11 ; M 38 ; L 35) | 0 |
| catalog-service | arm64 | debian 13.7 | 0 (0) | 49 (47) | 82 (74) | 66 (65) | 0 (0) | 197 | 95 | 186 (CVE distinctes : H 11 ; M 38 ; L 35) | 0 |
| frontend | amd64 | alpine 3.24.2 | 0 (0) | 0 (0) | 1 (0) | 0 (0) | 0 (0) | 1 | 1 | 0 (CVE distinctes : 0) | 0 |
| frontend | arm64 | alpine 3.24.2 | 0 (0) | 0 (0) | 1 (0) | 0 (0) | 0 (0) | 1 | 1 | 0 (CVE distinctes : 0) | 0 |
| notification-service | amd64 | debian 13.7 | 0 (0) | 49 (47) | 82 (74) | 66 (65) | 0 (0) | 197 | 95 | 186 (CVE distinctes : H 11 ; M 38 ; L 35) | 0 |
| notification-service | arm64 | debian 13.7 | 0 (0) | 49 (47) | 82 (74) | 66 (65) | 0 (0) | 197 | 95 | 186 (CVE distinctes : H 11 ; M 38 ; L 35) | 0 |

Chaque cellule de sévérité : nombre total de lignes (paquet, version, CVE), dont sans correctif entre parenthèses.

### Vulnérabilités avec correctif disponible (à corriger : mise à jour de paquet ou de dépendance)

- catalog-service : 11 ligne(s)
  - HIGH CVE-2026-76844 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - HIGH CVE-2026-85091 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - MEDIUM CVE-2025-8869 pip 25.0.1 -> 25.3 (amd64+arm64)
  - MEDIUM CVE-2026-101918 PyJWT 2.14.0 -> 2.15.0 (amd64+arm64)
  - MEDIUM CVE-2026-102275 PyJWT 2.14.0 -> 2.15.0 (amd64+arm64)
  - MEDIUM CVE-2026-13346 pip 25.0.1 -> 26.2.0 (amd64+arm64)
  - MEDIUM CVE-2026-27171 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - MEDIUM CVE-2026-3219 pip 25.0.1 -> 26.1 (amd64+arm64)
  - MEDIUM CVE-2026-6357 pip 25.0.1 -> 26.1 (amd64+arm64)
  - MEDIUM CVE-2026-8643 pip 25.0.1 -> 26.1.2 (amd64+arm64)
  - LOW CVE-2026-1703 pip 25.0.1 -> 26.0 (amd64+arm64)
- frontend : 1 ligne(s)
  - MEDIUM CVE-2026-4738 zlib 1.3.2-r1 -> 1.4-r0 (amd64+arm64)
- notification-service : 11 ligne(s)
  - HIGH CVE-2026-76844 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - HIGH CVE-2026-85091 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - MEDIUM CVE-2025-8869 pip 25.0.1 -> 25.3 (amd64+arm64)
  - MEDIUM CVE-2026-101918 PyJWT 2.14.0 -> 2.15.0 (amd64+arm64)
  - MEDIUM CVE-2026-102275 PyJWT 2.14.0 -> 2.15.0 (amd64+arm64)
  - MEDIUM CVE-2026-13346 pip 25.0.1 -> 26.2.0 (amd64+arm64)
  - MEDIUM CVE-2026-27171 zlib1g 1:1.3.dfsg+really1.3.1-1+b1 -> 1:1.3.dfsg+really1.3.1-1+deb13u1 (amd64+arm64)
  - MEDIUM CVE-2026-3219 pip 25.0.1 -> 26.1 (amd64+arm64)
  - MEDIUM CVE-2026-6357 pip 25.0.1 -> 26.1 (amd64+arm64)
  - MEDIUM CVE-2026-8643 pip 25.0.1 -> 26.1.2 (amd64+arm64)
  - LOW CVE-2026-1703 pip 25.0.1 -> 26.0 (amd64+arm64)

### Sans correctif : CRITICAL et HIGH, regroupés par CVE (MEDIUM et LOW : voir les JSON)

- catalog-service (identique en amd64 et arm64)
  - HIGH CVE-2025-69720 : ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary code execu (4 paquet(s) : libncursesw6, libtinfo6, ncurses-base, ncurses-bin)
  - HIGH CVE-2026-119373 : sqlite: sqlite: Denial of service via heap-based buffer overflow in FTS5 (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-119374 : sqlite: sqlite: Arbitrary code execution via corrupted FTS5 index (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-119379 : sqlite: sqlite: Arbitrary code execution via crafted session changesets (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-16742 : systemd: systemd-homed: Local privilege escalation via missing home-record signa (2 paquet(s) : libsystemd0, libudev1)
  - HIGH CVE-2026-54369 : acl: Symlink traversal privilege escalation via libacl functions (1 paquet(s) : libacl1)
  - HIGH CVE-2026-76642 : util-linux: util-linux: failed external mount helper still runs privileged X-mou (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78408 : util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migration author (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78409 : util-linux: util-linux: X-mount.subdir detached-tree resolution can escape via i (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78410 : util-linux: util-linux: restricted bind mounts do not pin the source, allowing X (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-9538 : perl-Archive-Tar: perl-Archive-Tar: Denial of Service via crafted tar header wit (1 paquet(s) : perl-base)
- frontend (identique en amd64 et arm64)
- notification-service (identique en amd64 et arm64)
  - HIGH CVE-2025-69720 : ncurses: ncurses: Buffer overflow vulnerability may lead to arbitrary code execu (4 paquet(s) : libncursesw6, libtinfo6, ncurses-base, ncurses-bin)
  - HIGH CVE-2026-119373 : sqlite: sqlite: Denial of service via heap-based buffer overflow in FTS5 (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-119374 : sqlite: sqlite: Arbitrary code execution via corrupted FTS5 index (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-119379 : sqlite: sqlite: Arbitrary code execution via crafted session changesets (1 paquet(s) : libsqlite3-0)
  - HIGH CVE-2026-16742 : systemd: systemd-homed: Local privilege escalation via missing home-record signa (2 paquet(s) : libsystemd0, libudev1)
  - HIGH CVE-2026-54369 : acl: Symlink traversal privilege escalation via libacl functions (1 paquet(s) : libacl1)
  - HIGH CVE-2026-76642 : util-linux: util-linux: failed external mount helper still runs privileged X-mou (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78408 : util-linux: util-linux: nsenter --join-cgroup leaks root cgroup migration author (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78409 : util-linux: util-linux: X-mount.subdir detached-tree resolution can escape via i (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-78410 : util-linux: util-linux: restricted bind mounts do not pin the source, allowing X (9 paquet(s) : bsdutils, libblkid1, liblastlog2-2, libmount1, libsmartcols1, libuuid1, login, mount, util)
  - HIGH CVE-2026-9538 : perl-Archive-Tar: perl-Archive-Tar: Denial of Service via crafted tar header wit (1 paquet(s) : perl-base)

## Trivy : configuration (Dockerfiles, manifestes, chart rendu)

| Cible | Sévérité | Identifiant | Constat | Lignes |
| --- | --- | --- | --- | --- |
| infra/keycloak.yaml | LOW | KSV-0011 | CPU not limited | 48-107 |
| infra/keycloak.yaml | HIGH | KSV-0014 | Root file system is not read-only | 48-107 |
| infra/keycloak.yaml | LOW | KSV-0020 | Runs with UID <= 10000 | 48-107 |
| infra/keycloak.yaml | LOW | KSV-0021 | Runs with GID <= 10000 | 48-107 |
| infra/keycloak.yaml | LOW | KSV-0116 | Runs with a root primary or supplementary GID | ?-? |
| infra/keycloak.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 48-107 |
| infra/postgres.yaml | LOW | KSV-0011 | CPU not limited | 50-99 |
| infra/postgres.yaml | LOW | KSV-0020 | Runs with UID <= 10000 | 50-99 |
| infra/postgres.yaml | LOW | KSV-0021 | Runs with GID <= 10000 | 50-99 |
| infra/rabbitmq.yaml | MEDIUM | KSV-0001 | Can elevate its own privileges | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0003 | Default capabilities: some containers do not drop all | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0004 | Default capabilities: some containers do not drop any | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0011 | CPU not limited | 70-110 |
| infra/rabbitmq.yaml | MEDIUM | KSV-0012 | Runs as root user | 70-110 |
| infra/rabbitmq.yaml | HIGH | KSV-0014 | Root file system is not read-only | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0020 | Runs with UID <= 10000 | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0021 | Runs with GID <= 10000 | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0030 | Runtime/Default Seccomp profile not set | 70-110 |
| infra/rabbitmq.yaml | MEDIUM | KSV-0104 | Seccomp policies disabled | 70-110 |
| infra/rabbitmq.yaml | LOW | KSV-0106 | Container capabilities must only include NET_BIND_SERVICE | 70-110 |
| infra/rabbitmq.yaml | HIGH | KSV-0118 | Default security context configured | 70-110 |
| infra/rabbitmq.yaml | HIGH | KSV-0118 | Default security context configured | 57-117 |
| k8s/traefik-config.yaml | MEDIUM | KSV-0037 | User resources should not be placed in kube-system namespace | 10-11 |
| k8s/traefik-config.yaml | MEDIUM | KSV-0037 | User resources should not be placed in kube-system namespace | 26-28 |
| k8s/whoami-verif.yaml | MEDIUM | KSV-0001 | Can elevate its own privileges | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0003 | Default capabilities: some containers do not drop all | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0004 | Default capabilities: some containers do not drop any | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0011 | CPU not limited | 17-19 |
| k8s/whoami-verif.yaml | MEDIUM | KSV-0012 | Runs as root user | 17-19 |
| k8s/whoami-verif.yaml | HIGH | KSV-0014 | Root file system is not read-only | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0015 | CPU requests not specified | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0016 | Memory requests not specified | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0018 | Memory not limited | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0020 | Runs with UID <= 10000 | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0021 | Runs with GID <= 10000 | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0030 | Runtime/Default Seccomp profile not set | 17-19 |
| k8s/whoami-verif.yaml | MEDIUM | KSV-0104 | Seccomp policies disabled | 17-19 |
| k8s/whoami-verif.yaml | LOW | KSV-0106 | Container capabilities must only include NET_BIND_SERVICE | 17-19 |
| k8s/whoami-verif.yaml | MEDIUM | KSV-0117 | Prevent binding to privileged ports | ?-? |
| k8s/whoami-verif.yaml | HIGH | KSV-0118 | Default security context configured | 17-19 |
| k8s/whoami-verif.yaml | HIGH | KSV-0118 | Default security context configured | 15-19 |
| k8s/whoami-verif.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 17-19 |
| catalog-service/Dockerfile | LOW | DS-0026 | No HEALTHCHECK defined | ?-? |
| notification-service/Dockerfile | LOW | DS-0026 | No HEALTHCHECK defined | ?-? |
| Dockerfile | LOW | DS-0026 | No HEALTHCHECK defined | ?-? |
| catalog-service.yaml | MEDIUM | KSV-01010 | ConfigMap with sensitive content | ?-? |
| catalog-service.yaml | LOW | KSV-0110 | Workloads in the default namespace | 43-49 |
| catalog-service.yaml | LOW | KSV-0110 | Workloads in the default namespace | 240-250 |
| catalog-service.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 78-129 |
| catalog-service.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 267-295 |
| frontend.yaml | LOW | KSV-0020 | Runs with UID <= 10000 | 97-152 |
| frontend.yaml | LOW | KSV-0021 | Runs with GID <= 10000 | 97-152 |
| frontend.yaml | LOW | KSV-0110 | Workloads in the default namespace | 60-66 |
| frontend.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 97-152 |
| notification-service.yaml | MEDIUM | KSV-01010 | ConfigMap with sensitive content | ?-? |
| notification-service.yaml | LOW | KSV-0110 | Workloads in the default namespace | 43-49 |
| notification-service.yaml | LOW | KSV-0110 | Workloads in the default namespace | 240-250 |
| notification-service.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 78-129 |
| notification-service.yaml | MEDIUM | KSV-0125 | Restrict container images to trusted registries | 267-295 |

## ZAP

### api-catalog-alice

Alertes par niveau : Low 3, Informational 4

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Low | 10021 | X-Content-Type-Options Header Missing | 2 |
| Low | 10035 | Strict-Transport-Security Header Not Set | 5 |
| Low | 90004 | Cross-Origin-Resource-Policy Header Missing or Invalid | 2 |
| Informational | 100000 | A Client Error response code was returned by the server | 216 |
| Informational | 10015 | Re-examine Cache-control Directives | 2 |
| Informational | 10049 | Non-Storable Content | 5 |
| Informational | 10104 | User Agent Fuzzer | 5 |

### api-catalog-anonyme

Alertes par niveau : Low 3, Informational 5

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Low | 10021 | X-Content-Type-Options Header Missing | 1 |
| Low | 10035 | Strict-Transport-Security Header Not Set | 5 |
| Low | 90004 | Cross-Origin-Resource-Policy Header Missing or Invalid | 1 |
| Informational | 100000 | A Client Error response code was returned by the server | 218 |
| Informational | 10015 | Re-examine Cache-control Directives | 1 |
| Informational | 10049 | Non-Storable Content | 5 |
| Informational | 10049 | Storable and Cacheable Content | 3 |
| Informational | 10104 | User Agent Fuzzer | 5 |

### api-notification-alice

Alertes par niveau : Low 3, Informational 4

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Low | 10021 | X-Content-Type-Options Header Missing | 4 |
| Low | 10035 | Strict-Transport-Security Header Not Set | 5 |
| Low | 90004 | Cross-Origin-Resource-Policy Header Missing or Invalid | 4 |
| Informational | 100000 | A Client Error response code was returned by the server | 170 |
| Informational | 10015 | Re-examine Cache-control Directives | 4 |
| Informational | 10049 | Non-Storable Content | 5 |
| Informational | 10104 | User Agent Fuzzer | 5 |

### api-notification-anonyme

Alertes par niveau : Low 1, Informational 4

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Low | 10035 | Strict-Transport-Security Header Not Set | 5 |
| Informational | 100000 | A Client Error response code was returned by the server | 181 |
| Informational | 10049 | Non-Storable Content | 5 |
| Informational | 10049 | Storable and Cacheable Content | 2 |
| Informational | 10104 | User Agent Fuzzer | 5 |

### front

Alertes par niveau : Medium 2, Low 4, Informational 5

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Medium | 10055 | CSP: Wildcard Directive | 3 |
| Medium | 10055 | CSP: style-src unsafe-inline | 3 |
| Low | 10096 | Timestamp Disclosure - Unix | 1 |
| Low | 90004 | Cross-Origin-Embedder-Policy Header Missing or Invalid | 3 |
| Low | 90004 | Cross-Origin-Opener-Policy Header Missing or Invalid | 3 |
| Low | 90004 | Cross-Origin-Resource-Policy Header Missing or Invalid | 3 |
| Informational | 10015 | Re-examine Cache-control Directives | 3 |
| Informational | 10027 | Information Disclosure - Suspicious Comments | 1 |
| Informational | 10049 | Non-Storable Content | 3 |
| Informational | 10049 | Storable and Cacheable Content | 1 |
| Informational | 10109 | Modern Web Application | 3 |

### keycloak

Alertes par niveau : Medium 5, Low 7, Informational 6

| Niveau | Identifiant | Alerte | Instances |
| --- | --- | --- | --- |
| Medium | 10055 | CSP: Failure to Define Directive with No Fallback | 2 |
| Medium | 10055 | CSP: Wildcard Directive | 2 |
| Medium | 10055 | CSP: script-src unsafe-inline | 2 |
| Medium | 10055 | CSP: style-src unsafe-inline | 2 |
| Medium | 10202 | Absence of Anti-CSRF Tokens | 1 |
| Low | 10010 | Cookie No HttpOnly Flag | 1 |
| Low | 10035 | Strict-Transport-Security Header Not Set | 2 |
| Low | 10054 | Cookie with SameSite Attribute None | 3 |
| Low | 10063 | Permissions Policy Header Not Set | 3 |
| Low | 90004 | Cross-Origin-Embedder-Policy Header Missing or Invalid | 2 |
| Low | 90004 | Cross-Origin-Opener-Policy Header Missing or Invalid | 2 |
| Low | 90004 | Cross-Origin-Resource-Policy Header Missing or Invalid | 5 |
| Informational | 10015 | Re-examine Cache-control Directives | 2 |
| Informational | 10049 | Non-Storable Content | 3 |
| Informational | 10049 | Storable and Cacheable Content | 5 |
| Informational | 10049 | Storable but Non-Cacheable Content | 1 |
| Informational | 10109 | Modern Web Application | 2 |
| Informational | 10112 | Session Management Response Identified | 1 |

## SonarCloud (API publique)

- catalog-service : quality gate OK, 1 issue(s) ouverte(s), 0 security hotspot(s)
  - python:S9152 MAJOR (CODE_SMELL) src/catalog/main.py:33 : Cleanup after this "yield" may be skipped on early exit.
- notification-service : quality gate OK, 1 issue(s) ouverte(s), 0 security hotspot(s)
  - python:S9152 MAJOR (CODE_SMELL) src/notification/main.py:31 : Cleanup after this "yield" may be skipped on early exit.

## npm audit

- npm audit complet (développement compris) : info 0, low 0, moderate 10, high 0, critical 0, total 10
  - @eslint/config-array moderate (direct : False) : minimatch
  - @eslint/js moderate (direct : True) : eslint
  - @typescript-eslint/eslint-plugin moderate (direct : False) : @typescript-eslint/parser; @typescript-eslint/type-utils; @typescript-eslint/utils
  - @typescript-eslint/parser moderate (direct : False) : @typescript-eslint/typescript-estree
  - @typescript-eslint/type-utils moderate (direct : False) : @typescript-eslint/typescript-estree; @typescript-eslint/utils
  - @typescript-eslint/typescript-estree moderate (direct : False) : minimatch
  - @typescript-eslint/utils moderate (direct : False) : @typescript-eslint/typescript-estree
  - eslint moderate (direct : True) : @eslint/config-array; minimatch
  - minimatch moderate (direct : False) : minimatch has potential denial of service via globparts amplification
  - typescript-eslint moderate (direct : True) : @typescript-eslint/eslint-plugin; @typescript-eslint/parser; @typescript-eslint/typescript-estree; @typescript
- npm audit embarqué (--omit=dev) : info 0, low 0, moderate 0, high 0, critical 0, total 0

