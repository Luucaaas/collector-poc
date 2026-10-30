# 02 — Architecture

| Document | Contenu |
| --- | --- |
| [architecture-cible.md](architecture-cible.md) | Toute la plateforme Collector.shop : services par domaine, bus d'événements, intégrations externes, hébergement cible |
| [architecture-poc.md](architecture-poc.md) | Le POC réel sur k3d : vue logique, vue physique (placement sur les 3 nœuds), disponibilité, points de sécurité, NetworkPolicies, diagrammes de séquence (publication d'un article, authentification OIDC) |
| [contrats.md](contrats.md) | Endpoints REST par service, schémas JSON des événements, modèle de données de chaque service |
| [adr/](adr/README.md) | Les décisions d'architecture (format MADR) |
| [img/](img/) | Diagrammes exportés en SVG pour les slides |

## Diagrammes

Les diagrammes sont écrits en Mermaid, directement dans les fichiers Markdown, et GitHub les affiche tels quels. Pour régénérer les SVG de `img/` après une modification :

```bash
docs/02-architecture/export-diagrams.sh
```

Le script exporte chaque bloc Mermaid qui contient une ligne `%% id: <nom>` vers `img/<nom>.svg`. Il s'appuie sur mermaid-cli, avec une version épinglée, lancé via `npx`.
