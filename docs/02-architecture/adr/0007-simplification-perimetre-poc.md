---
statut: acceptée
date: 2026-10-31
décideurs: Lucas (Lead Developer)
---

# 0007 — Simplification du périmètre du POC

## Contexte et problème

La première version du POC (ADR 0001 et 0006 dans leur rédaction du 30/10/2026) comptait trois services, trois instances PostgreSQL, une outbox, des *quorum queues* et des *dead-letter queues*, des NetworkPolicies, des règles de placement, cert-manager, Argo CD, un front internationalisé et des tests Gherkin. Chaque composant se justifiait, mais leur somme dépasse ce qu'un Lead Developer seul peut construire, tester, rendre fiable pour la démo et défendre en 20 minutes. Il découvre en plus Kubernetes, Helm, React et GitHub Actions.

La consigne demande de **démontrer la faisabilité par un POC** et d'implémenter **au moins une fonctionnalité métier**, et non l'architecture cible entière. Le risque principal pour la note n'est pas un composant absent, mais une démo instable ou un choix que l'on ne sait pas expliquer.

Quel est le plus petit POC qui démontre chaque point évalué ?

## Facteurs de décision

- Chaque critère de la grille doit rester démontré : découpage et communication interservices (critère 2), fonctionnalité métier (3), pipeline CI/CD réel (4), environnement d'exécution, disponibilité et montée en charge (5), au moins 2 types de tests (7), au moins 2 bonnes pratiques de sécurité dans le POC (8).
- Chaque composant conservé doit servir au moins un de ces critères.
- Chaque composant retiré doit rester dans l'architecture cible, avec son risque documenté. Les limites alimentent le plan de remédiation (critère 8).
- Stabilité de la démo et charge de travail compatibles avec le calendrier.

## Options étudiées

1. **Garder le POC complet** de la première version.
2. **POC minimal outillé** : le plus petit ensemble qui démontre chaque critère, le reste documenté comme limite assumée.
3. **Monolithe déployé sur Kubernetes** : un seul service FastAPI, sans broker.

## Décision

**Option 2 : POC minimal outillé.** Le tableau suivant liste chaque retrait, ce qui reste démontré et la référence de la limite correspondante dans [architecture-poc.md](../architecture-poc.md#8-limites-assumées-du-poc).

| Retiré du POC | Justification | Ce qui reste démontré | Limite |
| --- | --- | --- | --- |
| `fraud-service` et US-06 (alertes de fraude) | Un second consommateur ne prouve rien de plus qu'un premier sur le découpage. La consigne n'exige qu'une fonctionnalité métier | Communication asynchrone par `notification-service`. Point d'extension anti-fraude démontré en liant une file supplémentaire à l'exchange | L1 |
| *Transactional outbox* | Relais, table et verrouillage à écrire et à tester. La perte d'événement ne se produit que si le broker tombe entre le commit et la publication | Publication persistante avec confirmation du broker, juste après le commit | L2 |
| *Quorum queues*, *dead-letter queues*, table `processed_events` | Un seul nœud RabbitMQ : la réplication Raft n'apporte rien. La DLQ n'est utile qu'avec un outil de rejeu | File durable, acquittement après traitement. Doublons évités par une contrainte d'unicité sur les notifications | L7 |
| Trois instances PostgreSQL | Une instance par service triple la mémoire et l'exploitation sur un poste de 8 Go | Une base logique et un utilisateur par service : les données restent séparées et cloisonnées par les droits | L3 |
| NetworkPolicies | Un flux oublié bloque la démo, et leur mise au point est longue | Isolation des données par les droits PostgreSQL, JWT vérifié dans chaque service | L4 |
| Règles de placement, PodDisruptionBudget, démo de panne de nœud | Sans répartition garantie, une démo de panne de nœud est aléatoire. Le PDB ne sert qu'aux évictions volontaires | Auto-réparation d'un pod supprimé, HPA de 2 à 5 réplicas sous charge Locust | L8 |
| cert-manager | Sans domaine public, il faut quand même une CA locale. mkcert produit le certificat en une commande | HTTPS de bout en bout via Traefik, redirection HTTP → HTTPS | L11 |
| Argo CD | La consigne ne pénalise pas l'absence de déploiement automatique. Un composant de plus à maîtriser | Pipeline réel jusqu'à la publication des images sur GHCR, déploiement reproductible par `deploy.sh` | L12 |
| Semgrep, Bandit, pip-audit, Gitleaks, ZAP dans la CI | SonarCloud couvre l'analyse statique, Trivy les dépendances, les images et les secrets. Moins d'outils à configurer et à interpréter | Pipeline Ruff + mypy → pytest + couverture → SonarCloud → build multi-arch → Trivy → GHCR. ZAP lancé ponctuellement pour l'audit de sécurité | L13 |
| Internationalisation et contrôle d'accessibilité | Ils ne démontrent aucun critère de la grille | Interface en français, composants MUI qui respectent les patrons ARIA | L14 |
| Gherkin et pytest-bdd | Une couche de traduction en plus (fichiers `.feature` et définitions d'étapes) pour le même résultat | Tests d'acceptation pytest + httpx, nommés d'après les critères d'acceptation : environ 15 tests | — |
| Alertmanager | Aucune alerte n'est exploitée pendant la démo | Prometheus et un tableau de bord Grafana : débit, latence p95, taux d'erreur | — |

**Conservé parce que chaque élément démontre un critère** : 2 services et RabbitMQ (critère 2), Keycloak avec le realm importé et la vérification du JWT dans chaque service (critères 2 et 8), k3d multi-nœuds, Helm, HPA et sondes (critère 5), pipeline GitHub Actions avec SonarCloud et Trivy (critères 4 et 6), tests unitaires, d'intégration, d'acceptation et de charge (critère 7), Prometheus et Grafana (critères 5 et 6).

### Conséquences

- ✅ Moins de composants à faire fonctionner ensemble : démo plus stable, et chaque choix restant peut être expliqué en détail.
- ✅ Le temps libéré va à ce qui est noté : tests, indicateurs de qualité, protocoles d'expérimentation, plan de remédiation.
- ✅ Les limites L1 à L16 donnent au plan de remédiation une base concrète, priorisée et propre au projet.
- ❌ Le POC s'éloigne davantage de la cible. Atténuation : l'architecture cible reste complète, et la section 7 d'`architecture-cible.md` met les deux en regard point par point.
- ❌ Un jury peut demander pourquoi l'outbox ou les NetworkPolicies manquent. La réponse est préparée : le risque est connu, mesuré et priorisé dans les limites assumées.

### Confirmation

Chaque critère de la grille reste couvert par au moins un élément conservé. Le tableau de correspondance est en section 9 d'`architecture-poc.md`.

## Avantages et inconvénients des options

### Garder le POC complet

- ✅ Plus proche de la cible, plus impressionnant sur le papier.
- ❌ Charge de travail et nombre de composants incompatibles avec une démo fiable préparée par une seule personne.
- ❌ Plus de composants à défendre, chacun pouvant ouvrir une question à laquelle on répond mal.

### POC minimal outillé

- ✅ Chaque critère démontré, chaque composant justifié, chaque retrait documenté.
- ❌ Demande de bien préparer l'argumentaire sur les limites.

### Monolithe déployé sur Kubernetes

- ✅ Encore plus simple.
- ❌ Ne démontre ni le découpage en services ni la communication interservices, explicitement attendus pour le critère 2.

> [!TIP]
> **À défendre à l'oral.** Un POC sert à lever les risques techniques, pas à construire la cible. On a gardé tout ce qui prouve la faisabilité de l'architecture (deux services découplés par un broker, identité centralisée, orchestration avec autoscaling, pipeline outillé) et retiré ce qui relève de l'industrialisation. Chaque retrait est un choix tracé, avec son risque et sa remédiation, pas un oubli.
