# Front React de Collector.shop

Application web en **React + TypeScript** (outil de build : Vite), interface **MUI** en français. Elle couvre les 5 user stories : connexion à Keycloak, appels aux deux API, et 4 pages (voir ci-dessous).

## Prérequis

- **Node 22** (`node --version` doit afficher `v22.x`) et npm 10.
- Pour se connecter en développement : la pile locale lancée par `deploy/compose/up.sh` (Keycloak sur `http://localhost:8080`, `catalog-service` sur le port 8001, `notification-service` sur le 8002).

## Commandes

Depuis le dossier `frontend/` :

| Commande | Effet |
| --- | --- |
| `npm ci` | Installe exactement les versions du `package-lock.json` (à préférer à `npm install`) |
| `npm run dev` | Serveur de développement sur `http://localhost:5173` (le port est imposé : Keycloak n'accepte que lui) |
| `npm run lint` | ESLint, aucun avertissement toléré |
| `npm test` | Tests Vitest (une seule exécution) |
| `npm run e2e` | Parcours Playwright (Chromium), **hors CI** : voir « Tests de bout en bout » |
| `npm run build` | Vérification des types (`tsc -b`) puis build de production dans `dist/` |

Les comptes de démonstration (`alice`, `bob`, `chloe`, `admin`) ont leurs mots de passe dans `deploy/compose/.env` (jamais versionné).

## Configuration au démarrage

L'application charge `/config.json` **avant** de démarrer : `authority` (adresse du realm Keycloak), `clientId`, `catalogApiUrl` et `notificationApiUrl`. Ainsi, une même image servira partout, seul ce fichier change.

- `public/config.json` : valeurs du cluster (`*.127.0.0.1.sslip.io`). C'est lui que le build copie dans `dist/`.
- `config.dev.json` : valeurs de la pile docker compose. En `npm run dev`, le serveur Vite le sert à la place, sur `/config.json`. Il n'est pas dans `public/`, donc jamais dans `dist/`.
- Fichier absent ou invalide : un message d'erreur en français s'affiche, jamais un écran blanc.

## Les dossiers de `src/`

| Dossier ou fichier | Rôle |
| --- | --- |
| `main.tsx`, `Bootstrap.tsx` | Point d'entrée ; charge la configuration, puis monte le routeur et l'authentification |
| `config.ts` | Lecture et validation de `/config.json` |
| `auth/` | `oidc.ts` (réglages OIDC), `roles.ts` (lecture des rôles), `RequireRole.tsx` (garde de route) |
| `api/` | `client.ts` (fonction unique `apiRequest`), `errors.ts` (erreurs RFC 9457 traduites en français), `types.ts` (réponses, d'après `docs/02-architecture/contrats.md`), `useApi.ts` et `useAsync.ts` (hooks maison) |
| `components/` | `Layout.tsx` : barre de navigation (nom, rôles, connexion, déconnexion) |
| `pages/` | Une page par route (détail ci-dessous) ; `pages/sell/` : formulaire de mise en vente et liste des articles du vendeur |
| `format.ts`, `money.ts`, `reasons.ts` | Montants en euros et dates en `fr-FR` ; validation des montants saisis (chaîne décimale, jamais de `number`) ; motifs de rejet traduits |
| `api/useAction.ts` | Hook d'envoi de formulaire : bouton désactivé pendant l'envoi, erreur traduite, pas de double soumission |
| `test/` | Réglages des tests (jest-dom, nettoyage des stockages) |

Les tests sont à côté du code qu'ils vérifient (`*.test.ts` et `*.test.tsx`).

## Les 4 pages

| Route | Rôle | Contenu |
| --- | --- | --- |
| `/` Catalogue | public | Articles `PUBLISHED`, filtre par catégorie, pagination |
| `/categories` Catégories | `admin` (US-01) | Liste et création ; nom déjà utilisé ou invalide affiché en français |
| `/vendre` Vendre | `seller` (US-02 à US-04) | Mes boutiques et création ; mise en vente avec le résultat du contrôle automatique (`Article publié`, `Article rejeté` avec motifs, ou `Saisie à corriger` pour un 422) ; mes articles par boutique, modification du prix et historique |
| `/centres-interet` Mes centres d'intérêt | `buyer` (US-05) | Catégories suivies, préférences `new_article` et `price_changed`, notifications (bouton « Actualiser », pas de rafraîchissement automatique) |

Un prix identique au prix actuel n'est pas envoyé à l'API : l'interface dit qu'aucune modification n'a été enregistrée (RM-04 : pas de ligne d'historique).

## Image Docker (nginx)

`frontend/Dockerfile` (multi-stage) construit `dist/` sur `node:22.23.4-alpine3.24` (`npm ci --ignore-scripts`, `npm run build`), puis le sert avec `nginxinc/nginx-unprivileged` : utilisateur 101, port **8080**, bases épinglées par digest, `apk upgrade` pour les CVE de la base (voir `docs/01-qualite/cicd.md`). `/healthz` répond 200 (sondes). `index.html` et `config.json` ne sont jamais mis en cache ; `assets/` l'est un an.

Les en-têtes de sécurité (CSP, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, HSTS) viennent des modèles `nginx/*.template`, traités par `envsubst` au démarrage. Les origines de l'API et de Keycloak ne sont pas dans l'image : variable `CSP_CONNECT_SRC` (adresses séparées par un espace, sans joker ; défaut = celles du cluster local). `style-src` garde `'unsafe-inline'` car MUI (Emotion) injecte des styles : limite connue.

```bash
docker build --build-arg GIT_SHA=$(git rev-parse HEAD) -t collector/frontend:local frontend
docker run --rm --read-only --tmpfs /tmp --tmpfs /etc/nginx/conf.d:uid=101,gid=101 -p 8080:8080 \
  -e CSP_CONNECT_SRC="http://localhost:8001 http://localhost:8002 http://localhost:8080" \
  -v "$PWD/frontend/config.dev.json:/usr/share/nginx/html/config.json:ro" collector/frontend:local
```

Avec un système de fichiers en lecture seule, `/tmp` et `/etc/nginx/conf.d` doivent être des volumes inscriptibles. Le workflow `.github/workflows/frontend.yml` (ESLint, Vitest, `npm audit`, build, Trivy, publication sur `ghcr.io/luucaaas/frontend:sha-<7>`) est décrit dans `docs/01-qualite/cicd.md`.

## Tests de bout en bout (Playwright)

Six parcours dans `e2e/parcours.spec.ts` : (1) `admin` crée une catégorie, (2) `chloe` la choisit, (3) `alice` crée une boutique, publie un article accepté puis un article rejeté (téléphone dans la description), change le prix et voit l'historique, (4) `chloe` voit les notifications `NEW_ARTICLE` et `PRICE_CHANGED`, (5) la déconnexion revient sur l'application, (6) aucun jeton dans `localStorage` ni `sessionStorage`. Les noms contiennent un suffixe horodaté : les parcours se relancent sans réinitialiser la base.

```bash
deploy/compose/up.sh                      # pile locale (une fois)
cd frontend && npm ci
npx playwright install chromium           # une fois ; Chromium est stocké dans ~/Library/Caches/ms-playwright, hors du dépôt
./e2e/run-compose.sh                      # lance Vite (npm run dev) puis les 6 parcours
```

`run-compose.sh` lit les mots de passe des comptes de démonstration dans `deploy/compose/.env` et les exporte (`E2E_ADMIN_PASSWORD`, `E2E_ALICE_PASSWORD`, `E2E_CHLOE_PASSWORD`) pour ce seul processus. Ils ne sont ni affichés ni écrits. La configuration Playwright coupe les traces, captures et vidéos et n'écrit pas de rapport HTML, car ils reprennent les valeurs saisies ; la saisie du mot de passe passe par `evaluate`, dont les arguments n'apparaissent pas dans les messages d'erreur. Pour viser une autre adresse (le cluster, plus tard) : `E2E_BASE_URL=https://app.127.0.0.1.sslip.io`, avec les trois variables définies.

## La connexion en 5 lignes (Authorization Code + PKCE)

1. L'utilisateur clique sur « Connexion » : le front génère un secret aléatoire (`code_verifier`) et envoie son empreinte SHA-256 (`code_challenge`) à Keycloak, avec une valeur `state` anti-falsification.
2. Keycloak affiche sa page de connexion (le front ne voit jamais le mot de passe) puis renvoie le navigateur vers le front avec un `code` à usage unique.
3. Le front échange ce `code` contre les jetons en présentant le `code_verifier` : sans lui, un code volé est inutilisable (c'est tout l'intérêt de PKCE).
4. Chaque appel d'API porte `Authorization: Bearer <jeton d'accès>` ; les API vérifient la signature et les rôles.
5. Le jeton dure 5 minutes et est renouvelé automatiquement avec le jeton de rafraîchissement ; « Déconnexion » termine aussi la session Keycloak.

## Où sont les jetons, et pourquoi

Les jetons (accès, rafraîchissement, identité) sont gardés **en mémoire JavaScript** (`InMemoryWebStorage`), et nulle part dans `localStorage` ni `sessionStorage` : un script malveillant injecté dans la page (XSS) ne peut pas les y récupérer après coup. Conséquence assumée : recharger la page déconnecte, mais le cookie de session Keycloak rend la reconnexion immédiate.

Seul l'état de la redirection (`state` et `code_verifier`, sans aucun jeton) passe par `sessionStorage` de l'onglet (`stateStore`, qui vaut `localStorage` par défaut dans oidc-client-ts) : la page est quittée pour Keycloak, donc cet état ne peut pas rester en mémoire. Il est supprimé par la bibliothèque dès le retour. Le `code_verifier` seul ne permet rien sans le code d'autorisation. Un test Vitest (`src/auth/oidc.test.ts`) vérifie qu'aucune clé `oidc.*` n'est écrite après une connexion.

Le nom affiché vient du claim `preferred_username` (scope `profile` du realm, limité à ce seul champ). Les rôles affichés dans la barre et les menus viennent du jeton d'accès (`realm_access.roles`) **pour l'affichage seulement** : masquer un lien n'est pas un contrôle d'accès, les API refusent (403) ce que le rôle n'autorise pas.

## Chaîne d'approvisionnement

Versions **exactes** dans `package.json` (`.npmrc` : `save-exact=true`), `package-lock.json` versionné, chaque version publiée depuis au moins 14 jours à l'installation (`npm install --before=<date>`). Aucune dépendance au-delà de la liste décidée (pas d'axios, de TanStack Query ni de bibliothèque de formulaires) : `fetch` et des hooks maison suffisent.
