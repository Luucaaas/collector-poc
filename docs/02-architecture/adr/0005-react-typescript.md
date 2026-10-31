---
statut: acceptée (mise à jour le 2026-10-31, voir ADR 0007)
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0005 — React et TypeScript pour le front

## Contexte et problème

Le POC a besoin d'une interface pour dérouler la démonstration, en quatre pages : catalogue, mise en vente et modification du prix, centres d'intérêt et notifications, catégories pour l'admin. L'application cible doit être internationalisée et accessible (EF-33, ENF-25), s'authentifier en OIDC et consommer les API de plusieurs services. Collector recrutera d'autres développeurs : la technologie doit être répandue sur le marché.

Quelle technologie retenir pour le front ?

## Facteurs de décision

- Technologie standard du marché, pour recruter et pour la pérennité.
- Typage statique, pour fiabiliser les échanges avec les API.
- Bibliothèques matures pour l'OIDC (PKCE), l'internationalisation, l'accessibilité et la gestion des données serveur.
- Front découplé des services : il ne doit pas appartenir à l'un d'eux.
- Testabilité : tests unitaires de composants et tests de bout en bout.

## Options étudiées

1. **React + TypeScript** (Vite), en application monopage (SPA).
2. **Vue 3 + TypeScript**.
3. **Angular**.
4. **Pages rendues côté serveur** (HTMX et gabarits Jinja servis par FastAPI).
5. **Streamlit**.

Pour la gestion des jetons, une variante a aussi été étudiée : un **BFF** (*Backend for Frontend*), qui fait l'échange OIDC côté serveur et ne donne au navigateur qu'un cookie de session `HttpOnly`.

## Décision

**Option 1 : React + TypeScript**, construit avec Vite et servi en fichiers statiques par nginx. Bibliothèques du POC, réduites au minimum (ADR 0007) : MUI (composants accessibles), React Router et react-oidc-context (OIDC + PKCE). L'internationalisation (react-i18next) et le contrôle d'accessibilité outillé relèvent de la cible. Par défaut, cette bibliothèque (via oidc-client-ts) conserve la session dans `sessionStorage` : on configure explicitement un `userStore` en mémoire (`InMemoryWebStorage`). Tests : Vitest pour les composants, Playwright pour les parcours de bout en bout.

### Conséquences

- ✅ La technologie front la plus répandue : vivier de recrutement large, documentation et écosystème abondants.
- ✅ TypeScript détecte à la compilation les incohérences avec les contrats d'API. Les types peuvent être générés à partir de l'OpenAPI des services.
- ✅ MUI fournit des composants qui respectent déjà les patrons ARIA, ce qui fait gagner du temps sur ENF-25.
- ✅ La SPA ne dépend d'aucun service backend : elle s'adresse à toutes les API derrière l'Ingress.
- ❌ **Nouvelle compétence pour le Lead Developer**, qui maîtrise surtout Python. Atténuation : périmètre d'interface volontairement réduit, et action de formation prévue dans le plan de compétences (`docs/05-competences`).
- ❌ Une SPA expose ses jetons au JavaScript de la page. La mémoire évite qu'un jeton persiste dans le stockage du navigateur, mais **ne protège pas d'un XSS actif**, qui peut appeler l'API avec le jeton en cours. Atténuation dans le POC : PKCE, durée de vie courte (5 min), échappement systématique par React. En cible : politique de sécurité de contenu (CSP) et passage à un BFF (voir ci-dessous).
- ❌ Le rendu côté client pénalise le référencement du catalogue public. C'est sans importance pour le POC, mais important pour une place de marché : la cible pourra passer le catalogue public en rendu serveur (Next.js) en gardant les mêmes composants React.

### Confirmation

Les tests Playwright déroulent le parcours de démonstration (connexion, publication, notification). Dans la cible, un contrôle axe et le score Lighthouse vérifieront ENF-25.

## Avantages et inconvénients des options

### Vue 3 + TypeScript

- ✅ Prise en main plus douce, très bonne documentation.
- ❌ Écosystème et vivier de recrutement plus restreints que React.

### Angular

- ✅ Cadre complet et structurant, apprécié pour les grandes équipes.
- ❌ Plus lourd et plus long à apprendre pour un premier projet front. Surdimensionné pour l'interface du POC.

### Pages rendues côté serveur (HTMX et Jinja)

- ✅ Reste en Python, très productif pour l'équipe actuelle.
- ❌ Lie l'interface à un service backend particulier, ce qui va à l'encontre du découpage (ADR 0001).
- ❌ Technologie moins classique en entreprise : écartée pour la pérennité et le recrutement.

### BFF (*Backend for Frontend*) pour les jetons

- ✅ Les jetons ne sont jamais accessibles au JavaScript : le navigateur ne détient qu'un cookie `HttpOnly`, `Secure`, `SameSite`. C'est la recommandation de l'IETF pour les applications navigateur les plus sensibles (*OAuth 2.0 for Browser-Based Applications*).
- ❌ Un composant de plus, avec un état de session à stocker et à répliquer, et une protection CSRF à mettre en place.
- Écarté pour le POC, **retenu pour la cible** dans le plan de remédiation, puisque la plateforme traitera des paiements.

### Streamlit

- ✅ Très rapide pour un prototype de données.
- ❌ Conçu pour des tableaux de bord, pas pour une application grand public : pas de contrôle fin de l'accessibilité, de l'internationalisation ni du flux OIDC.

> [!TIP]
> **À défendre à l'oral.** Le front n'est pas le cœur de l'évaluation, mais il doit être crédible pour une vraie place de marché : React + TypeScript est le standard du marché, MUI apporte l'accessibilité et react-oidc-context implémente PKCE, avec des jetons gardés en mémoire une fois le stockage configuré. On sait aussi dire ce que la mémoire ne protège pas (un XSS actif) et quelle est la réponse cible : un BFF. On assume que c'est une technologie nouvelle pour soi, et c'est précisément l'objet de l'action de formation.
