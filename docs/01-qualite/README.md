# 01 — Processus qualité

| Document | Contenu | Critère de la grille |
| --- | --- | --- |
| [indicateurs.md](indicateurs.md) | Les 5 indicateurs qualité (ISO 25010) : définition, formule, seuil, outil de mesure, moment, action en cas de dépassement, effet sur la dette technique | 6 — Indicateurs qualité |
| [devsecops.md](devsecops.md) | Cycle de vie DevSecOps : une ou plusieurs mesures de sécurité par étape, boucle de rétroaction vers le backlog, écarts entre le POC et la cible | 8 — Sécurité (bonnes pratiques) |
| [cicd.md](cicd.md) | Schéma CI/CD détaillé : environnements, jobs (`lint` à `publish`), conditions de blocage, traçabilité par tag et digest, écarts entre le POC et la cible | 4 — CI/CD |
| [processus-test.md](processus-test.md) | Processus de test : pyramide, types de tests (outil, moment, sortie attendue, responsable), correspondance avec les jobs, RACI, gestion des anomalies | 7 — Tests |
| [img/](img/) | Diagrammes exportés en SVG (cycle DevSecOps, pipeline CI/CD, pyramide des tests) | 4, 7, 8, 10 |

Les 5 indicateurs (I1 couverture, I2 dette technique, I3 latence et taux d'erreur, I4 vulnérabilités et secrets, I5 critères d'acceptation) sont rattachés aux jobs de la CI dans [cicd.md](cicd.md) et aux types de tests dans [processus-test.md](processus-test.md). Les diagrammes sont régénérés par `docs/02-architecture/export-diagrams.sh`.
