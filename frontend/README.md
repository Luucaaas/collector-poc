# Front React de Collector.shop

Application web en **React + TypeScript** (outil de build : Vite), interface **MUI** en français. Cette première étape (P7-01) fournit le socle : connexion à Keycloak, appels aux deux API, page catalogue publique. Les pages vendeur, acheteur et administrateur sont des emplacements vides, réalisés ensuite.

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
| `pages/` | Une page par route : `CataloguePage.tsx` est complète, les autres sont des emplacements |
| `format.ts` | Montants en euros (`"120.00"` devient `120,00 €`) |
| `test/` | Réglages des tests (jest-dom, nettoyage des stockages) |

Les tests sont à côté du code qu'ils vérifient (`*.test.ts` et `*.test.tsx`).

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
