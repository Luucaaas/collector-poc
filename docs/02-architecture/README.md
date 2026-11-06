# 02 — Architecture

| Document | Contenu |
| --- | --- |
| [architecture-cible.md](architecture-cible.md) | Toute la plateforme Collector.shop : services par domaine, bus d'événements, intégrations externes, hébergement cible |
| [architecture-poc.md](architecture-poc.md) | Le POC simplifié sur k3d : vue logique, vue physique, disponibilité et montée en charge, points de sécurité, diagrammes de séquence (publication d'un article, authentification OIDC), limites assumées (L1 à L23) |
| [contrats.md](contrats.md) | Endpoints REST des 2 services, schémas JSON des 2 événements, topologie RabbitMQ, modèle de données |
| [adr/](adr/README.md) | Les décisions d'architecture (format MADR) |
| [img/](img/) | Diagrammes exportés en SVG pour les slides |

## Diagrammes

Les diagrammes sont écrits en Mermaid, directement dans les fichiers Markdown, et GitHub les affiche tels quels. Pour régénérer les SVG de `img/` après une modification :

```bash
docs/02-architecture/export-diagrams.sh
```

Le script exporte aussi les diagrammes de `docs/01-qualite` (vers `docs/01-qualite/img/`). Il exporte chaque bloc Mermaid qui contient une ligne `%% id: <nom>` vers `img/<nom>.svg`. Il s'appuie sur mermaid-cli, avec une version épinglée, lancé via `npx`.
