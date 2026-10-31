---
statut: acceptée
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0004 — Keycloak comme serveur d'identité et d'autorisation

## Contexte et problème

La plateforme distingue les acheteurs, les vendeurs et les administrateurs (EF-09). L'inscription est obligatoire pour acheter ou vendre (EF-08). Les transactions financières font de la sécurité une exigence de premier plan. Les salariés de Collector disposent déjà de comptes Microsoft 365. Les services doivent vérifier l'identité et les rôles de l'appelant, sans session partagée entre eux.

Comment gérer l'authentification et les rôles ?

## Facteurs de décision

- Protocoles standards : OpenID Connect et OAuth 2.0, jetons JWT vérifiables par chaque service sans appel réseau (ENF-02).
- Gestion des rôles (RBAC) et transport des rôles dans le jeton.
- Fonctions de sécurité prêtes à l'emploi : MFA, politique de mots de passe, protection contre la force brute, inscription en libre-service, vérification de l'email.
- Fédération d'identité avec Microsoft Entra ID pour les salariés.
- Gratuité, auto-hébergement et données d'identité maîtrisées dans l'UE (RGPD).
- Ne pas développer soi-même de code cryptographique ni de gestion de mots de passe.

## Options étudiées

1. **Keycloak** (open source, projet CNCF en incubation), auto-hébergé.
2. **Auth0 ou Okta** (SaaS).
3. **Amazon Cognito** (service cloud).
4. **Authentification maison** dans FastAPI (table des utilisateurs, hachage, émission de JWT).
5. **Zitadel ou Authentik** (open source, plus légers).

## Décision

**Option 1 : Keycloak**, avec un realm `collector`, les rôles de realm `buyer`, `seller` et `admin`, un client public `collector-web` (*Authorization Code* + PKCE) pour le front et une audience `collector-api` pour les services. Keycloak n'émet pas cette audience par défaut : un *client scope* dédié, rattaché au client `collector-web`, porte un mapper « Audience » qui l'ajoute au claim `aud`. La configuration du realm, comptes de démonstration compris (`admin`, `alice`, `bob`, `chloe`), est exportée en JSON, versionnée sans secret réel, et importée au démarrage de Keycloak : l'environnement est reproductible.

### Conséquences

- ✅ Chaque service vérifie le JWT localement avec les clés publiques du realm (JWKS) : pas de point de contention ni d'appel réseau par requête.
- ✅ MFA, verrouillage après échecs, politique de mots de passe et inscription en libre-service sont activables sans code.
- ✅ La fédération Entra ID (*identity brokering*) permet aux salariés administrateurs d'utiliser leur compte Microsoft 365.
- ✅ Aucun coût de licence, aucune dépendance à un fournisseur. Les données d'identité restent sur notre infrastructure.
- ❌ Empreinte notable (Java, de l'ordre de 512 Mo à 1 Go de mémoire) et une base PostgreSQL de plus à exploiter.
- ❌ Mises à jour de sécurité à suivre et à appliquer nous-mêmes. Atténuation : image suivie par Trivy, version fixée dans les values Helm.
- ❌ Point critique : si Keycloak est indisponible, plus aucune connexion n'est possible. Les jetons déjà émis restent valides jusqu'à leur expiration (5 min). La cible prévoit un Keycloak à plusieurs réplicas.

### Confirmation

Un protocole d'expérimentation déploie Keycloak dans le cluster derrière Traefik en TLS, importe le realm, puis vérifie le flux PKCE depuis le navigateur et la validation du jeton par un service. Les tests d'acceptation couvrent les cas 401 (jeton absent) et 403 (rôle insuffisant). Les tests unitaires des services couvrent les jetons expirés ou falsifiés.

## Avantages et inconvénients des options

### Auth0 ou Okta

- ✅ Aucune exploitation, très bonne expérience développeur.
- ❌ Payant au-delà d'un palier gratuit limité en utilisateurs actifs : coût croissant avec le succès de la plateforme.
- ❌ Données d'identité chez un fournisseur américain, avec des questions de transfert hors UE.

### Amazon Cognito

- ✅ Managé, peu coûteux.
- ❌ Lie la plateforme à AWS, alors que l'hébergement cible n'est pas décidé. Personnalisation limitée.

### Authentification maison

- ✅ Aucune dépendance supplémentaire.
- ❌ Il faudrait réimplémenter et maintenir le hachage des mots de passe, le renouvellement des jetons, la rotation des clés, le MFA et la protection contre la force brute : source majeure de vulnérabilités (OWASP A07, *Identification and Authentication Failures*).
- ❌ Pas de fédération Entra ID sans développement important.

### Zitadel ou Authentik

- ✅ Plus légers, modernes.
- ❌ Moins répandus. Keycloak reste la référence citée par la consigne et la plus documentée.

## Plus d'informations

- Les rôles sont des rôles de realm (`realm_access.roles`) plutôt que des rôles de client : un utilisateur a les mêmes rôles pour tous les services, ce qui simplifie le POC. La cible pourra introduire des rôles par client, par exemple un modérateur limité au back-office.
- Le POC ne fait pas d'*introspection* de jeton (RFC 7662) : la vérification locale suffit avec des jetons à durée de vie courte. La révocation immédiate est un point du plan de remédiation.

> [!TIP]
> **À défendre à l'oral.** L'authentification est le dernier endroit où l'on veut écrire du code soi-même. Keycloak apporte des standards (OIDC, PKCE, JWT signés RS256), le MFA et la fédération avec le Microsoft 365 déjà en place chez Collector, gratuitement et sans dépendance à un fournisseur. Les services ne lui font pas confiance aveuglément : chacun vérifie la signature, l'émetteur, l'audience et l'expiration du jeton.
