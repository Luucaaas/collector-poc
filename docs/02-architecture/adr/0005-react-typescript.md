---
statut: acceptée
date: 2026-10-30
décideurs: Lucas (Lead Developer)
---

# 0005 — React et TypeScript pour le front

## Contexte et problème

Le POC a besoin d'une interface pour dérouler la démonstration : publication d'un article, modification du prix, centres d'intérêt et notifications, alertes de fraude. L'application cible doit être internationalisée et accessible (EF-33, ENF-25), s'authentifier en OIDC et consommer les API de plusieurs services. Collector recrutera d'autres développeurs : la technologie doit être répandue sur le marché.

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

## Décision

**Option 1 : React + TypeScript**, construit avec Vite et servi en fichiers statiques par nginx. Bibliothèques : MUI (composants accessibles), React Router, TanStack Query (cache et rafraîchissement des données serveur), React Hook Form + Zod (formulaires et validation), react-i18next (français et anglais), react-oidc-context (OIDC + PKCE, jetons en mémoire). Tests : Vitest pour les composants, Playwright pour les parcours de bout en bout.

### Conséquences

- ✅ La technologie front la plus répandue : vivier de recrutement large, documentation et écosystème abondants.
- ✅ TypeScript détecte à la compilation les incohérences avec les contrats d'API. Les types peuvent être générés à partir de l'OpenAPI des services.
- ✅ MUI fournit des composants qui respectent déjà les patrons ARIA, ce qui fait gagner du temps sur ENF-25.
- ✅ La SPA ne dépend d'aucun service backend : elle s'adresse à toutes les API derrière l'Ingress.
- ❌ **Nouvelle compétence pour le Lead Developer**, qui maîtrise surtout Python. Atténuation : périmètre d'interface volontairement réduit, et action de formation prévue dans le plan de compétences (`docs/05-competences`).
- ❌ Une SPA expose ses jetons au JavaScript de la page. Atténuation : PKCE, jetons gardés en mémoire uniquement (jamais dans `localStorage`), durée de vie courte, et politique de sécurité de contenu (CSP) en cible.
- ❌ Le rendu côté client pénalise le référencement du catalogue public. C'est sans importance pour le POC, mais important pour une place de marché : la cible pourra passer le catalogue public en rendu serveur (Next.js) en gardant les mêmes composants React.

### Confirmation

Les tests Playwright déroulent le parcours de démonstration (connexion, publication, notification). Un contrôle axe et le score Lighthouse vérifient ENF-25.

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

### Streamlit

- ✅ Très rapide pour un prototype de données.
- ❌ Conçu pour des tableaux de bord, pas pour une application grand public : pas de contrôle fin de l'accessibilité, de l'internationalisation ni du flux OIDC.

> [!TIP]
> **À défendre à l'oral.** Le front n'est pas le cœur de l'évaluation, mais il doit être crédible pour une vraie place de marché : React + TypeScript est le standard du marché, MUI apporte l'accessibilité et react-oidc-context implémente PKCE avec des jetons gardés en mémoire. On assume que c'est une technologie nouvelle pour soi, et c'est précisément l'objet de l'action de formation.
