# Conformité du pipeline CI/CD au schéma

Ce document prouve que le pipeline réel ([`backend.yml`](../../.github/workflows/backend.yml)) suit le contrat décrit dans [cicd.md](cicd.md) : pour chaque élément du schéma, la ligne du workflow qui l'implémente et une exécution qui le démontre. Il sert de guide au jury pour passer d'une case du schéma à son exécution réelle.

- **Dépôt** : https://github.com/Luucaaas/collector-poc
- **Run de référence** (`main`, commit `49df273`, avec publication) : https://github.com/Luucaaas/collector-poc/actions/runs/41825781085. Toutes les durées et mesures ci-dessous en sont tirées (API `gh run view --json jobs`, journaux `gh run view --log`, artefacts `gh run download`), relevées le 04/11/2026.
- **Les références `backend.yml:<ligne>`** désignent le fichier tel qu'il est après la fusion de P5-04 (branche `phase-5/ci-sonar`, job `sonar` compris). Elles sont à revérifier (`grep -n`) si le workflow change.
- **État** : le pipeline complet du contrat est en place, `sonar` compris (P5-04). Le run de référence ci-dessous date d'avant `sonar` ; les preuves propres à `sonar` viennent des runs de la pull request n°1, et le run de `main` qui suit la fusion de P5-04 est relevé en section 1.
- **Second run de référence** (`main`, commit `32c68df`, pipeline complet **avec `sonar`**) : [42039814860](https://github.com/Luucaaas/collector-poc/actions/runs/42039814860). Tentative 1 : `sonar` rouge pour les deux services (« QUALITY GATE STATUS: FAILED » alors que l'API renvoie `status: NONE` : première analyse de la branche principale, sans période de référence pour le nouveau code). Tentative 2 (`gh run rerun --failed`) : 11 jobs verts, de `lint` à `publish` (images `sha-32c68df`, amd64 et arm64). Il montre le pipeline conforme au schéma de bout en bout, `sonar` compris, ce que le run 41825781085 (d'avant `sonar`) ne pouvait pas faire. Son analyse complète a relevé 3 constats, corrigés par la pull request n°2 (P5-06, run [42043594738](https://github.com/Luucaaas/collector-poc/actions/runs/42043594738)).
- **Runs de la pull request n°1** (branche `phase-5/ci-sonar`) : **PR-V** = [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092) (pull_request, 10 jobs dont `sonar` verts, `publish` sauté), **PR-ROUGE** = [42037061364](https://github.com/Luucaaas/collector-poc/actions/runs/42037061364) (quality gate en échec), **TRIVY-OS** = [42034598196](https://github.com/Luucaaas/collector-poc/actions/runs/42034598196) (apt, CVE-2026-109518).

## 1. Déroulé du run de référence

Durées calculées à partir de `startedAt` et `completedAt` des jobs (UTC, 04/11/2026). Durée totale : 5 min 47 s (12:02:06 → 12:07:53), 9 jobs verts.

| Job | Durée | Lien |
| --- | --- | --- |
| `lint (catalog-service)` | 14 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560013996) |
| `lint (notification-service)` | 19 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560014323) |
| `test (catalog-service)` | 1 min 9 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560183833) |
| `test (notification-service)` | 58 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560183707) |
| `build-scan (catalog-service)` | 40 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560764497) |
| `build-scan (notification-service)` | 43 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126560765812) |
| `acceptance` | 1 min 24 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126561138776) |
| `publish (catalog-service)` | 1 min 48 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126561848379) |
| `publish (notification-service)` | 1 min 58 s | [job](https://github.com/Luucaaas/collector-poc/actions/runs/41825781085/job/126561848665) |

Le chemin critique (jobs enchaînés par `needs`, chacun attendant le plus lent de l'étape précédente) est : lint 19 s, test 1 min 9 s, build-scan 43 s, acceptance 1 min 24 s, publish 1 min 58 s, soit environ 5 min 30 s de temps de calcul, le reste étant l'attente des exécuteurs.

**Artefacts du run** (API `actions/runs/41825781085/artifacts`) : `coverage-catalog-service`, `coverage-notification-service`, `junit-catalog-service`, `junit-notification-service`, `junit-acceptance`, `image-catalog-service` (72 Mo), `image-notification-service` (72 Mo), plus deux fichiers `*.dockerbuild` (journaux de build créés par `docker/build-push-action` pour son résumé ; ils ne sont pas dans le contrat et sont sans conséquence).

**Images publiées** (`docker buildx imagetools inspect ghcr.io/luucaaas/<service>:sha-49df273`, relevé le 04/11/2026) :

| Image | Digest de l'index multi-architecture | Plateformes |
| --- | --- | --- |
| `ghcr.io/luucaaas/catalog-service` | `sha256:87bf19b121dc1a27f9c7f28a3aa9eb06ed8eb14f7272d14ec3c56ae0c2fbba92` | `linux/amd64`, `linux/arm64` (plus 2 manifestes `unknown/unknown`, attestations de provenance ajoutées par Buildx) |
| `ghcr.io/luucaaas/notification-service` | `sha256:e9eca6496f5d7184ef4d9ee9b760c1a9e10ccf61d1d33b61030c0abc2d114373` | idem |

Au relevé qui a suivi ce run, le tag `main` pointait sur le même digest que `sha-49df273` (même commande avec `:main`). Ce tag est déplacé à chaque publication sur `main` : dès le run suivant (41826801260, commit 154eb6d), il pointe sur une autre image, alors que `sha-49df273` ne bouge pas. C'est la raison pour laquelle on déploie par tag `sha-…` et par digest (`cicd.md`, section 4). Les labels de l'image publiée, lus avec `docker buildx imagetools inspect --format '{{json .Image}}'`, sont identiques en amd64 et en arm64 : `org.opencontainers.image.revision = 49df273dbe46c00bd082a730ee99f58e3aac5724` (SHA complet), `source = https://github.com/Luucaaas/collector-poc`, `version = main`, utilisateur `10001` (non root).

## 2. Tableau de conformité

Légende des preuves : **R** = run de référence 41825781085 ; **ROUGE-LINT** = [41818132153](https://github.com/Luucaaas/collector-poc/actions/runs/41818132153), **ROUGE-TRIVY** = [41821035266](https://github.com/Luucaaas/collector-poc/actions/runs/41821035266), **BR** = [41824083640](https://github.com/Luucaaas/collector-poc/actions/runs/41824083640) (branche, `publish` sauté).

| Élément du contrat (`cicd.md`) | Implémentation | Preuve |
| --- | --- | --- |
| Déclencheur `push` sur les branches | `backend.yml:7-8` (`branches: ["**"]`) | Runs sur toutes les branches de tâche (BR, ROUGE-LINT) |
| Déclencheur `pull_request` vers `main` | `backend.yml:9-10` | PR-V : run déclenché par l'événement `pull_request` de la pull request n°1 (https://github.com/Luucaaas/collector-poc/pull/1). Écart E12 clos |
| Une exécution à la fois par ref | `backend.yml:15-17` (`concurrency`, annulation sauf sur `main`) | Run 41824633761, branche `phase-5/ci-publish`, conclusion `cancelled` : annulé par le run 41824958780 du push suivant sur la même branche (commit f745828) |
| Moindre privilège | `backend.yml:21-22` (`contents: read`), `backend.yml:262-264` (`packages: write` dans `publish` seulement) | Lecture du fichier |
| Environnement figé | `ubuntu-24.04` (`backend.yml:34, 62, 114, 145, 198, 257`), `UV_PYTHON` (`:25`), actions épinglées par SHA (18 lignes `uses:`) | `grep -n "uses:"` : aucun tag flottant |
| **`lint`** : matrice sur les 2 services | `backend.yml:32-38` | R : `lint (catalog-service)` 14 s, `lint (notification-service)` 19 s |
| `lint` : `ruff check`, `ruff format --check`, `mypy --strict src` | `backend.yml:52-57` | R : « All checks passed! », « 36 files already formatted » (catalog) et « 31 » (notification), « Success: no issues found in 19 source files » et « 15 » |
| `lint` : bloque si une erreur | Code de sortie de chaque étape | ROUGE-LINT : `import os` inutilisé (F401) placé avant d'autres imports, d'où `Found 5 errors` (1 F401 et 4 E402), `lint (catalog-service)` en échec, les 2 `test` sautés |
| **`test`** : `needs: lint`, matrice | `backend.yml:61, 63-70` | R : `test` démarré à 12:02:28, après la fin des `lint` (12:02:25) |
| `test` : pytest, couverture ≥ 80 %, JUnit, `coverage.xml` | `backend.yml:85-92` | R : « Required test coverage of 80% reached. Total coverage: 99.06% » (270 passed) et « 98.43% » (186 passed) |
| `test` : artefacts `coverage.xml` et `junit.xml` obligatoires | `backend.yml:93-106` (`if: always()`, `if-no-files-found: error`) | R : artefacts `coverage-*` et `junit-*` présents pour les 2 services |
| `test` : bloque si test KO ou couverture < 80 % | `--cov-fail-under=80` (`backend.yml:89`) | **Non démontré par un run rouge** : seul le blocage du `lint` l'est (ROUGE-LINT). Le seuil est une option de pytest-cov, documentée et exécutée à chaque run (« Required test coverage … reached ») |
| **`sonar`** : `needs: test`, matrice, `fetch-depth: 0` | `backend.yml:110-138` | PR-V : `sonar` démarré après les `test`, 2 projets SonarCloud (une clé par service) |
| `sonar` : `coverage.xml` du job `test`, `SONAR_TOKEN` depuis les secrets, `sonar.qualitygate.wait=true` | `backend.yml:125-138` ; `services/<service>/sonar-project.properties` | PR-V : « QUALITY GATE STATUS: PASSED » pour chaque service ; couverture SonarCloud 98,5 % et 97,6 % contre 98 % pour pytest-cov |
| `sonar` : exécuté sur `main` et les pull requests seulement. Écart E14 | `backend.yml:113` | Push de branche [42037647157](https://github.com/Luucaaas/collector-poc/actions/runs/42037647157) : `sonar` sauté, suite verte ; PR [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092) : `sonar` exécuté |
| `sonar` : bloque si le quality gate échoue | Code de sortie du scanner (`sonar.qualitygate.wait=true`) | PR-ROUGE : [42037061364](https://github.com/Luucaaas/collector-poc/actions/runs/42037061364), voir section 4 |
| **`build-scan`** : `needs: sonar`, matrice, `if: !failure() && !cancelled()` | `backend.yml:140-151` | PR-V : démarré après la fin de `sonar` ; push de branche (`sonar` sauté) : exécuté ; PR-ROUGE : sauté parce que `sonar` échoue |
| `build-scan` : image amd64 non root, `GIT_SHA` | `backend.yml:157-162` (`docker build`) ; Dockerfile `ARG GIT_SHA`, `LABEL`, `USER 10001` | R : journal « Afficher les labels OCI » ; image publiée : utilisateur 10001 |
| `build-scan` : Trivy `vuln,secret`, `CRITICAL,HIGH`, `--ignore-unfixed`, `--exit-code 1` | `backend.yml:175-182` | R : « Report Summary » : `debian 13.7` 0 vulnérabilité et 41 cibles `python-pkg` à 0, colonne Secrets sans constat, pour chaque service |
| Trivy : version et intégrité | `backend.yml:28-29, 165-174` (0.76.0, SHA-256 vérifié, `sha256sum --check --strict`) | R : `trivy_0.76.0_Linux-64bit.tar.gz: OK`. Écart E6 |
| `build-scan` : bloque si CRITICAL ou HIGH corrigeable | Code de sortie 1 de Trivy | ROUGE-TRIVY : `h11` 0.14.0 forcée, `CVE-2025-43859` CRITICAL, corrigée en 0.16.0, `Total: 1 (HIGH: 0, CRITICAL: 1)`, `build-scan (notification-service)` en échec, `acceptance` sauté |
| `build-scan` : artefact image tar | `backend.yml:183-191` (`docker save`, `upload-artifact`, `retention-days: 7`) | R : `image-catalog-service` et `image-notification-service`, 72 Mo chacun |
| **`acceptance`** : `needs: build-scan` des 2 services | `backend.yml:194` (et `if: !failure() && !cancelled()`, `:197`) | R : démarré à 12:04:27, après la fin des `build-scan` (12:04:24) |
| `acceptance` : récupération et `docker load` des images construites | `backend.yml:210-218` | R : journal « Récupérer les images » (2 artefacts), « Charger les images » |
| `acceptance` : lint de `tests/acceptance` | `backend.yml:222-230` | R : « All checks passed! », « 9 files already formatted », « Success: no issues found in 8 source files ». Écart E8 |
| `acceptance` : pile `docker compose`, attente des sondes | `backend.yml:231-232` (`up.sh --no-build`) | R : étape verte (le script échoue si une sonde ne répond pas dans le délai) |
| `acceptance` : `pytest tests/acceptance` (17 critères) | `backend.yml:233-235` | R : « 17 passed in 9.50s » ; `junit-acceptance` : 17 tests, 0 échec, 0 erreur, 0 ignoré, 5 stories |
| `acceptance` : artefact JUnit | `backend.yml:236-242` | R : `junit-acceptance` (artefact zippé de 818 octets, `junit.xml` de 2 897 octets) |
| `acceptance` : journaux des conteneurs si échec, arrêt de la pile | `backend.yml:243-249` | R : étape « Arrêter la pile » exécutée (`if: always()`) |
| `acceptance` : bloque si un critère échoue | Code de sortie de pytest | **Non démontré par un run rouge** (aucun critère n'a été volontairement cassé) |
| **`publish`** : `needs: acceptance`, matrice | `backend.yml:255, 258-261` | R : démarré à 12:05:54, après la fin d'`acceptance` (12:05:51) |
| `publish` : condition `main` | `backend.yml:256` (`github.ref == 'refs/heads/main' && github.event_name == 'push'`). Écart E9 | R : exécuté sur `main` ; BR : `publish` sauté sur une branche |
| `publish` : Buildx + QEMU, amd64 + arm64, cache | `backend.yml:272-273, 288-299` (`platforms: linux/amd64,linux/arm64`, cache `gha`) | R : `imagetools inspect` : `linux/amd64` et `linux/arm64` pour les 2 images (section 1) |
| `publish` : connexion à GHCR sans secret personnel | `backend.yml:274-279` (`GITHUB_TOKEN`) | R : push réussi ; aucun secret ajouté au dépôt pour GHCR |
| `publish` : tags `sha-<7>` et `main` | `backend.yml:280-287` (`docker/metadata-action`) | `imagetools inspect` sur `:sha-49df273` et `:main` : même digest juste après ce run (le tag `main` est ensuite déplacé par chaque publication, voir section 1) |
| `publish` : digest dans le résumé du job | `backend.yml:300-316` (`GITHUB_STEP_SUMMARY`) | R : digests de la section 1 (le journal du build affiche le même `containerimage.digest`) |
| Labels OCI `revision` et `source` | Dockerfile (`ARG GIT_SHA`, `LABEL`) et `backend.yml:295-297` (`build-args`, `labels`) | Image publiée : `revision` = SHA complet du commit, `source` = URL du dépôt |
| Paquets GHCR lisibles sans secret | Visibilité des paquets réglée sur « public » | Lecture anonyme du manifeste : HTTP 200 pour les 2 paquets (relevé du chef, fiche P5-03) |
| **Déploiement** (manuel) : `deploy.sh <tag sha>` (`helm upgrade --install --wait`), puis `rollout status` et sondes ; échec : `helm rollback` | `deploy/local/deploy.sh` (fonctions `check_images`, `services`, `rollback_all`) ; image déployée par `tag@digest` | [Protocole 4](../04-experimentations/04-deploiement/protocole.md), exécution du 06/11/2026 : déploiement à froid en 199 s, `smoke.sh` 8/8 ; version défaillante (`DEPLOY_VALUES`, limite mémoire de 24 Mi) : `UPGRADE FAILED`, code de sortie 1, `helm history` `failed` puis `Rollback to 1`, 2 113 requêtes sur 2 113 servies pendant l'opération. [Journal](../04-experimentations/04-deploiement/resultats/run-20261106-0039.log) |
| Traçabilité (`cicd.md` §4) : pod → `imageID` → tag `sha-…` → commit → run | `kubectl get pod -o jsonpath`, `docker buildx imagetools inspect`, `git rev-parse`, `gh run list --commit` | Protocole 4, section « Traçabilité » : `imageID` = digest du tag `sha-bec38ed` sur GHCR (`sha256:81a09f74…`), label OCI `revision` = `bec38edd…`, run 42046581865 `success` |
| charge (phase 8), audit (phase 9) | Hors de cette tâche | — |

## 3. Écarts trouvés et traitement

Les écarts E15 à E18, propres à `frontend.yml`, sont décrits en section 6. Les écarts E1 à E14 ont été tranchés par le chef et ramenés à un état conforme (E12 et E13 clos par P5-04). Sens de la correction : **contrat** = `cicd.md` mis à jour pour refléter le workflow ; **workflow** = `backend.yml` corrigé.

| # | Écart | Sens | Pourquoi |
| --- | --- | --- | --- |
| E1 | `--cov-report=term` ajouté à pytest | Contrat (section 3) | Le taux de couverture se lit dans le journal du job, source de la mesure d'I1 |
| E2 | `ruff check .` et `ruff format --check .` | Contrat (précision) | `.` est le chemin par défaut : commande strictement équivalente |
| E3 | `push` limité aux branches (`branches: ["**"]`) | Workflow conforme, contrat précisé | Les tags ne déclenchent pas la CI, comme dans le schéma |
| E4 | `ubuntu-24.04` au lieu de `ubuntu-latest`, actions épinglées par SHA, `persist-credentials: false` | Contrat (section 1) | Environnement reproductible, chaîne d'approvisionnement maîtrisée (compromission des actions Trivy en mars 2026), jeton non laissé dans `.git/config` |
| E5 | Artefacts obligatoires (`if-no-files-found: error`) | Contrat (section 3) | Un job ne doit pas être vert sans produire son artefact (`coverage.xml` alimentera `sonar`) |
| E6 | `build-scan` par `docker build` et Trivy 0.76.0 en binaire vérifié par SHA-256, sans `trivy-action` | Contrat (section 3 et précisions) | Buildx n'est utile qu'au `publish` (multi-architecture, lent) ; aucune action tierce avec accès au jeton pour le scanner de sécurité |
| E7 | Rétention de 7 jours pour les archives d'image (`retention-days: 7`) | Contrat (section 3) | Les images ne servent qu'au job `acceptance` (72 Mo chacune) |
| E8 | Lint de `tests/acceptance` (Ruff, `mypy --strict .`) fait dans le job `acceptance` et non dans `lint` | Contrat (section 3) et schéma | Les dépendances des tests d'acceptation y sont déjà installées ; le schéma `pipeline-backend` est mis à jour |
| E9 | Condition de `publish` complétée par `github.event_name == 'push'` | Contrat (section 1) et schéma | Une pull request ne peut jamais obtenir `packages: write` ni publier |
| E10 | `concurrency` : pas d'annulation sur `main` | Contrat (section 1) | Annuler un `publish` en cours laisserait un service publié et l'autre non |
| E11 | Paquets GHCR publics | Contrat (section 3) | Le cluster k3d tire les images sans `imagePullSecret` (phase 6) |
| E12 | Déclencheur `pull_request` jamais exercé | **Clos** | Exercé par la pull request n°1 (https://github.com/Luucaaas/collector-poc/pull/1) : run [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092), événement `pull_request`, `sonar` exécuté, `publish` sauté |
| E13 | Job `sonar` absent du workflow | **Clos** | Ajouté par P5-04 (`backend.yml:110`) |
| E14 | `sonar` exécuté seulement sur `main` et les pull requests (`if: github.ref == 'refs/heads/main' \|\| github.event_name == 'pull_request'`) ; `build-scan` et `acceptance` portent `if: !failure() && !cancelled()` | Contrat (section 1 et ligne `sonar`) à mettre à jour à la fusion | Le plan Free de SonarCloud n'analyse que la branche principale et les pull requests : sur un push de branche de tâche, l'organisation n'a pas accès aux données de la branche (« Organization is not allowed to access data from non main branches », run [42034154273](https://github.com/Luucaaas/collector-poc/actions/runs/42034154273)). Un `sonar` sauté ne bloque pas la suite, un `sonar` en échec la bloque. |

Le schéma `img/pipeline-backend.svg` a été régénéré (sources Mermaid modifiées : lint des tests d'acceptation, condition de `publish`, rétention de l'image). `img/pipeline-cicd.svg` (vue d'ensemble) est inchangé.

## 4. Preuves de blocage

| Blocage | Run | Résultat |
| --- | --- | --- |
| `lint` bloque la suite (P5-01) | [41818132153](https://github.com/Luucaaas/collector-poc/actions/runs/41818132153) (commit temporaire, `import os` inutilisé) | `lint (catalog-service)` en échec (Ruff F401), `test` sautés |
| `build-scan` bloque sur une vulnérabilité CRITICAL (P5-02) | [41821035266](https://github.com/Luucaaas/collector-poc/actions/runs/41821035266) (commit temporaire, `h11` 0.14.0 forcée) | `build-scan (notification-service)` en échec : CVE-2025-43859, CRITICAL ; `acceptance` sauté ; aucune publication possible |
| `publish` ne s'exécute pas hors `main` (P5-03) | [41824083640](https://github.com/Luucaaas/collector-poc/actions/runs/41824083640) (branche `phase-5/ci-publish`) | 7 jobs verts, `publish` sauté |
| Quality gate SonarCloud (P5-04) | [42037061364](https://github.com/Luucaaas/collector-poc/actions/runs/42037061364) (PR n°1, commit temporaire : module `catalog/demo_gate.py` de 33 lignes sans test) | `sonar (catalog-service)` en échec ; `api/qualitygates/project_status?projectKey=Luucaaas_collector-poc_catalog-service&pullRequest=1` : condition `new_coverage` en ERROR (0,0 % pour un seuil de 80 %) ; les deux `build-scan`, `acceptance` et `publish` sautés. Couverture pytest globale inchangée (94,70 % ≥ 80 %), donc c'est bien SonarCloud qui bloque. Annulé par `git revert`, run vert [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092) |
| `build-scan` bloque sur une vulnérabilité de l'OS (P5-04, constat fortuit) | [42034598196](https://github.com/Luucaaas/collector-poc/actions/runs/42034598196) (PR n°1) | Trivy : CVE-2026-109518 (HIGH) dans `apt` 3.0.3 de l'image de base `python:3.12-slim` (correctif 3.0.4) ; les 2 `build-scan` en échec. Corrigé par la mise à jour du digest de l'image de base (relevé du 05/11/2026), run vert [42037655092](https://github.com/Luucaaas/collector-poc/actions/runs/42037655092) |
| Test en échec ou couverture < 80 %, critère d'acceptation en échec | — | Non démontrés par un run rouge (voir tableau de conformité) |

Les commits temporaires des runs rouges ont été annulés par `git revert` sur leur branche ; aucun n'a été poussé sur `main`, et le run de référence n'en contient pas l'effet.

## 5. Questions ouvertes

Les deux questions ouvertes par P5-05 sont tranchées (journal des décisions) :

1. Déclencheur `pull_request` : prouvé par la pull request n°1 (E12 clos).
2. Runs rouges de `test` et d'`acceptance` : non provoqués. Un test en échec ou une couverture sous 80 % rend pytest non nul, donc le job rouge ; `failure()` est vrai dès qu'un job ancêtre échoue (documentation de GitHub Actions), ce qui saute `sonar`, `build-scan`, `acceptance` et `publish`. Le même mécanisme est démontré par les runs rouges de `lint`, Trivy et du quality gate. Le blocage peut être montré en direct à la soutenance.

## 6. Conformité de `frontend.yml` (P7-03)

Les références `frontend.yml:<ligne>` désignent [`.github/workflows/frontend.yml`](../../.github/workflows/frontend.yml) tel qu'il est sur la branche `phase-7/ci-front`. Runs de preuve : **FV** = [42184993666](https://github.com/Luucaaas/collector-poc/actions/runs/42184993666) (branche, vert, `publish` sauté), **F-ESLINT** = [42185384274](https://github.com/Luucaaas/collector-poc/actions/runs/42185384274) (rouge), **F-TRIVY** = [42184547804](https://github.com/Luucaaas/collector-poc/actions/runs/42184547804) (rouge). La publication réelle sur `main` est relevée après la fusion.

| Élément du contrat | Implémentation | Preuve |
| --- | --- | --- |
| Déclencheurs `push` (toutes branches) et `pull_request` vers `main` | `frontend.yml:6-9` | Runs sur la branche de tâche (FV) |
| Une exécution à la fois par ref, pas d'annulation sur `main` | `frontend.yml:13-15` | Note sous le tableau (annulation d'un run précédent sur la même ref) |
| Moindre privilège | `frontend.yml:18-19` (`contents: read`), `frontend.yml:90-92` (`packages: write` dans `publish` seulement) | Lecture du fichier |
| Environnement figé, actions épinglées par SHA | `ubuntu-24.04` (`:29, :89`), 8 lignes `uses:` à SHA complet (`:36, :39, :96, :100, :101, :103, :110, :122`) | `grep -n "uses:" frontend.yml` : aucun tag flottant ; `setup-node` v7.1.0 publié le 08/10/2026 (29 jours) |
| Dossier de travail `frontend` | `frontend.yml:30-32` | FV |
| `npm ci`, ESLint, Vitest | `frontend.yml:44-49` | FV : 11 fichiers, 62 tests passés |
| ESLint bloque | Code de sortie de `npm run lint --max-warnings 0` | F-ESLINT : `'inutilise' is assigned a value but never used`, étape ESLint en échec, `publish` sauté |
| `npm audit --omit=dev --audit-level=high` (ajout au contrat) | `frontend.yml:53-54` | FV : « found 0 vulnerabilities » |
| Image : build amd64, `GIT_SHA`, labels OCI, non root | `frontend.yml:57-64` ; `frontend/Dockerfile` (`ARG GIT_SHA`, `LABEL`, `USER 101`) | Journal « Afficher les labels OCI » ; essai local : `uid=101(nginx)`, démarrage `--read-only` |
| Trivy 0.76.0 vérifié par SHA-256 (dans `frontend` et dans `publish`) | `frontend.yml:22-25, 65-74` et `131-140` | FV : `sha256sum --check` OK |
| Trivy `vuln,secret`, `CRITICAL,HIGH`, `--ignore-unfixed`, `--exit-code 1` sur l'image amd64 construite | `frontend.yml:75-82` | FV : cible `alpine 3.24.2` du tableau de Trivy, 0 vulnérabilité, colonne Secrets `-` |
| Trivy bloque | Code de sortie 1 | F-TRIVY : brotli-libs CVE-2026-111497 (CRITICAL), curl, libexpat, zlib (HIGH) sur la base nginx publiée le 19/10/2026 ; corrigé par `apk upgrade` (écart E15) |
| **`publish`** : `needs: frontend`, condition `main` et `push` | `frontend.yml:86-88` | FV : `publish` sauté sur la branche |
| `publish` : QEMU, Buildx, connexion par `GITHUB_TOKEN`, metadata (tags calculés), index amd64 + arm64 poussé **par digest, sans tag**, cache `gha` | `frontend.yml:100-130` | À relever après fusion sur `main` (`docker buildx imagetools inspect ghcr.io/luucaaas/frontend:sha-<7>`) |
| `publish` : Trivy sur le digest publié, amd64 puis arm64, mêmes options bloquantes | `frontend.yml:142-152` (amd64), `153-163` (arm64) | À relever après fusion sur `main` |
| `publish` : étiquetage `sha-<7>` et `main` par `docker buildx imagetools create`, seulement si les deux scans passent (tags passés par `env`), puis garde-fou : chaque tag doit désigner le digest scanné, sinon échec | `frontend.yml:165-186` | À relever après fusion sur `main` ; sur la branche, `publish` est sauté (FV) |
| Digest, tags et résultat des scans dans `GITHUB_STEP_SUMMARY`, valeurs passées par `env` | `frontend.yml:188-204` | À relever après fusion sur `main` |

Note sur la concurrence : un push de la branche annule le run précédent de la même ref (backend 42184897635, `cancelled`).

Écarts : **E15** `apk upgrade --no-cache` dans l'image finale (voir `cicd.md`, précisions ; contenu dépendant des dépôts Alpine, le digest publié fait foi). **E16** `npm audit --omit=dev --audit-level=high` ajouté au contrat. **E18** `publish` du front en « publier par digest, scanner, puis étiqueter » (le backend scanne l'amd64 avant `publish` et reconstruit ensuite ; voir `cicd.md`, « Pourquoi Trivy avant toute étiquette »). **E17** `actionlint` n'est pas installé sur le poste : le workflow n'a pas été analysé par cet outil, sa validité est établie par l'exécution réelle sur GitHub (runs ci-dessus). Les 10 vulnérabilités modérées de la chaîne ESLint (outillage de développement, `minimatch`) sont hors seuil et notées sans mise à jour forcée.
