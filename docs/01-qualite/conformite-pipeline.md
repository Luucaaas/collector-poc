# Conformité du pipeline CI/CD au schéma

Ce document prouve que le pipeline réel ([`backend.yml`](../../.github/workflows/backend.yml)) suit le contrat décrit dans [cicd.md](cicd.md) : pour chaque élément du schéma, la ligne du workflow qui l'implémente et une exécution qui le démontre. Il sert de guide au jury pour passer d'une case du schéma à son exécution réelle.

- **Dépôt** : https://github.com/Luucaaas/collector-poc
- **Run de référence** (`main`, commit `49df273`, avec publication) : https://github.com/Luucaaas/collector-poc/actions/runs/41825781085. Toutes les durées et mesures ci-dessous en sont tirées (API `gh run view --json jobs`, journaux `gh run view --log`, artefacts `gh run download`), relevées le 04/11/2026.
- **Les références `backend.yml:<ligne>`** désignent le fichier tel qu'il est sur `main` au commit `154eb6d`. Elles sont à revérifier (`grep -n`) si le workflow change, par exemple quand P5-04 ajoute le job `sonar`.
- **État** : le job `sonar` n'est pas encore dans le workflow (tâche P5-04, qui passe après celle-ci). Sa ligne est marquée « à compléter par P5-04 » et n'est pas comptée comme conforme.

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
| Déclencheur `pull_request` vers `main` | `backend.yml:9-10` | **Déclaré, jamais exécuté** : aucune pull request n'a été ouverte (le flux de branches fusionne en local), donc aucune preuve par un run. Voir écart E12 |
| Une exécution à la fois par ref | `backend.yml:15-17` (`concurrency`, annulation sauf sur `main`) | Run 41824633761, branche `phase-5/ci-publish`, conclusion `cancelled` : annulé par le run 41824958780 du push suivant sur la même branche (commit f745828) |
| Moindre privilège | `backend.yml:21-22` (`contents: read`), `backend.yml:225-227` (`packages: write` dans `publish` seulement) | Lecture du fichier |
| Environnement figé | `ubuntu-24.04` (`backend.yml:34, 62, 111, 161, 220`), `UV_PYTHON` (`:25`), actions épinglées par SHA (18 lignes `uses:`) | `grep -n "uses:"` : aucun tag flottant |
| **`lint`** : matrice sur les 2 services | `backend.yml:32-38` | R : `lint (catalog-service)` 14 s, `lint (notification-service)` 19 s |
| `lint` : `ruff check`, `ruff format --check`, `mypy --strict src` | `backend.yml:52-57` | R : « All checks passed! », « 36 files already formatted » (catalog) et « 31 » (notification), « Success: no issues found in 19 source files » et « 15 » |
| `lint` : bloque si une erreur | Code de sortie de chaque étape | ROUGE-LINT : `import os` inutilisé (F401) placé avant d'autres imports, d'où `Found 5 errors` (1 F401 et 4 E402), `lint (catalog-service)` en échec, les 2 `test` sautés |
| **`test`** : `needs: lint`, matrice | `backend.yml:61, 63-70` | R : `test` démarré à 12:02:28, après la fin des `lint` (12:02:25) |
| `test` : pytest, couverture ≥ 80 %, JUnit, `coverage.xml` | `backend.yml:85-92` | R : « Required test coverage of 80% reached. Total coverage: 99.06% » (270 passed) et « 98.43% » (186 passed) |
| `test` : artefacts `coverage.xml` et `junit.xml` obligatoires | `backend.yml:93-106` (`if: always()`, `if-no-files-found: error`) | R : artefacts `coverage-*` et `junit-*` présents pour les 2 services |
| `test` : bloque si test KO ou couverture < 80 % | `--cov-fail-under=80` (`backend.yml:89`) | **Non démontré par un run rouge** : seul le blocage du `lint` l'est (ROUGE-LINT). Le seuil est une option de pytest-cov, documentée et exécutée à chaque run (« Required test coverage … reached ») |
| **`sonar`** | — | **À compléter par P5-04** (job pas encore dans `backend.yml`) |
| **`build-scan`** : `needs`, matrice | `backend.yml:110, 112-115` (`needs: test`) | R : démarré à 12:03:40, après la fin des `test` (12:03:37). Passera à `needs: sonar` avec P5-04 |
| `build-scan` : image amd64 non root, `GIT_SHA` | `backend.yml:123-128` (`docker build`) ; Dockerfile `ARG GIT_SHA`, `LABEL`, `USER 10001` | R : journal « Afficher les labels OCI » ; image publiée : utilisateur 10001 |
| `build-scan` : Trivy `vuln,secret`, `CRITICAL,HIGH`, `--ignore-unfixed`, `--exit-code 1` | `backend.yml:141-148` | R : « Report Summary » : `debian 13.7` 0 vulnérabilité et 41 cibles `python-pkg` à 0, colonne Secrets sans constat, pour chaque service |
| Trivy : version et intégrité | `backend.yml:28-29, 131-140` (0.76.0, SHA-256 vérifié, `sha256sum --check --strict`) | R : `trivy_0.76.0_Linux-64bit.tar.gz: OK`. Écart E6 |
| `build-scan` : bloque si CRITICAL ou HIGH corrigeable | Code de sortie 1 de Trivy | ROUGE-TRIVY : `h11` 0.14.0 forcée, `CVE-2025-43859` CRITICAL, corrigée en 0.16.0, `Total: 1 (HIGH: 0, CRITICAL: 1)`, `build-scan (notification-service)` en échec, `acceptance` sauté |
| `build-scan` : artefact image tar | `backend.yml:149-157` (`docker save`, `upload-artifact`, `retention-days: 7`) | R : `image-catalog-service` et `image-notification-service`, 72 Mo chacun |
| **`acceptance`** : `needs: build-scan` des 2 services | `backend.yml:160` | R : démarré à 12:04:27, après la fin des `build-scan` (12:04:24) |
| `acceptance` : récupération et `docker load` des images construites | `backend.yml:173-181` | R : journal « Récupérer les images » (2 artefacts), « Charger les images » |
| `acceptance` : lint de `tests/acceptance` | `backend.yml:185-193` | R : « All checks passed! », « 9 files already formatted », « Success: no issues found in 8 source files ». Écart E8 |
| `acceptance` : pile `docker compose`, attente des sondes | `backend.yml:194-195` (`up.sh --no-build`) | R : étape verte (le script échoue si une sonde ne répond pas dans le délai) |
| `acceptance` : `pytest tests/acceptance` (17 critères) | `backend.yml:196-198` | R : « 17 passed in 9.50s » ; `junit-acceptance` : 17 tests, 0 échec, 0 erreur, 0 ignoré, 5 stories |
| `acceptance` : artefact JUnit | `backend.yml:199-205` | R : `junit-acceptance` (artefact zippé de 818 octets, `junit.xml` de 2 897 octets) |
| `acceptance` : journaux des conteneurs si échec, arrêt de la pile | `backend.yml:206-212` | R : étape « Arrêter la pile » exécutée (`if: always()`) |
| `acceptance` : bloque si un critère échoue | Code de sortie de pytest | **Non démontré par un run rouge** (aucun critère n'a été volontairement cassé) |
| **`publish`** : `needs: acceptance`, matrice | `backend.yml:218, 221-224` | R : démarré à 12:05:54, après la fin d'`acceptance` (12:05:51) |
| `publish` : condition `main` | `backend.yml:219` (`github.ref == 'refs/heads/main' && github.event_name == 'push'`). Écart E9 | R : exécuté sur `main` ; BR : `publish` sauté sur une branche |
| `publish` : Buildx + QEMU, amd64 + arm64, cache | `backend.yml:235-236, 251-262` (`platforms: linux/amd64,linux/arm64`, cache `gha`) | R : `imagetools inspect` : `linux/amd64` et `linux/arm64` pour les 2 images (section 1) |
| `publish` : connexion à GHCR sans secret personnel | `backend.yml:237-242` (`GITHUB_TOKEN`) | R : push réussi ; aucun secret ajouté au dépôt pour GHCR |
| `publish` : tags `sha-<7>` et `main` | `backend.yml:243-250` (`docker/metadata-action`) | `imagetools inspect` sur `:sha-49df273` et `:main` : même digest juste après ce run (le tag `main` est ensuite déplacé par chaque publication, voir section 1) |
| `publish` : digest dans le résumé du job | `backend.yml:263-279` (`GITHUB_STEP_SUMMARY`) | R : digests de la section 1 (le journal du build affiche le même `containerimage.digest`) |
| Labels OCI `revision` et `source` | Dockerfile (`ARG GIT_SHA`, `LABEL`) et `backend.yml:258-260` (`build-args`, `labels`) | Image publiée : `revision` = SHA complet du commit, `source` = URL du dépôt |
| Paquets GHCR lisibles sans secret | Visibilité des paquets réglée sur « public » | Lecture anonyme du manifeste : HTTP 200 pour les 2 paquets (relevé du chef, fiche P5-03) |
| `frontend` (phase 7), déploiement manuel (phase 6), charge (phase 8), audit (phase 9) | Hors de cette tâche | — |

## 3. Écarts trouvés et traitement

Les écarts E1 à E11 ont été tranchés par le chef et ramenés à un état conforme ; E12 et E13 restent ouverts. Sens de la correction : **contrat** = `cicd.md` mis à jour pour refléter le workflow ; **workflow** = `backend.yml` corrigé.

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
| E12 | Déclencheur `pull_request` jamais exercé | **Ouvert** | À démontrer en ouvrant une pull request vers `main` (voir questions ouvertes) |
| E13 | Job `sonar` absent du workflow | **Ouvert, P5-04** | Le job reste dans le contrat et dans le schéma ; il sera ajouté puis cette ligne complétée |

Le schéma `img/pipeline-backend.svg` a été régénéré (sources Mermaid modifiées : lint des tests d'acceptation, condition de `publish`, rétention de l'image). `img/pipeline-cicd.svg` (vue d'ensemble) est inchangé.

## 4. Preuves de blocage

| Blocage | Run | Résultat |
| --- | --- | --- |
| `lint` bloque la suite (P5-01) | [41818132153](https://github.com/Luucaaas/collector-poc/actions/runs/41818132153) (commit temporaire, `import os` inutilisé) | `lint (catalog-service)` en échec (Ruff F401), `test` sautés |
| `build-scan` bloque sur une vulnérabilité CRITICAL (P5-02) | [41821035266](https://github.com/Luucaaas/collector-poc/actions/runs/41821035266) (commit temporaire, `h11` 0.14.0 forcée) | `build-scan (notification-service)` en échec : CVE-2025-43859, CRITICAL ; `acceptance` sauté ; aucune publication possible |
| `publish` ne s'exécute pas hors `main` (P5-03) | [41824083640](https://github.com/Luucaaas/collector-poc/actions/runs/41824083640) (branche `phase-5/ci-publish`) | 7 jobs verts, `publish` sauté |
| Quality gate SonarCloud (P5-04) | — | À compléter par P5-04 |
| Test en échec ou couverture < 80 %, critère d'acceptation en échec | — | Non démontrés par un run rouge (voir tableau de conformité) |

Les commits temporaires des runs rouges ont été annulés par `git revert` sur leur branche ; aucun n'a été poussé sur `main`, et le run de référence n'en contient pas l'effet.

## 5. Questions ouvertes

1. Ouvrir une pull request vers `main` (même éphémère) pour prouver le déclencheur `pull_request` (E12), ou accepter de le laisser déclaré sans preuve.
2. Faut-il provoquer un run rouge de `test` (couverture) et d'`acceptance` pour compléter les preuves de blocage ? Coût : deux commits temporaires et deux runs.
