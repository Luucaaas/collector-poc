# Journal des décisions

Décisions prises par le chef en cours de réalisation : questions remontées par le développeur, doutes signalés par l'auditeur, arbitrages après deux allers-retours non conformes. Les décisions d'architecture structurantes restent dans les ADR (`docs/02-architecture/adr`) ; ce journal en garde la trace quand elles naissent d'une tâche.

Une ligne par décision, la plus récente en bas. Mentionner l'identifiant de la tâche dans la colonne « question ».

| Date | Question | Options | Décision | Justification |
| --- | --- | --- | --- | --- |
| 31/10/2026 | Les agents `developpeur` et `auditeur` ne sont pas chargés dans la session en cours (créés après son démarrage). Comment réaliser la phase 2 ? | 1. Ouvrir une nouvelle session. 2. Utiliser l'agent généraliste avec le modèle imposé et le texte du fichier d'agent comme consigne | 2, validée par Lucas | Évite de couper la session. Le développeur tourne sur Sonnet, l'auditeur sur Haiku avec la consigne de ne rien modifier (non bloqué par l'outil). Les sessions suivantes utiliseront les vrais agents |
| 31/10/2026 | P2-03 : où s'exécutent les tests d'acceptation dans la CI ? | 1. Dans la suite pytest de chaque service. 2. Job CI dédié qui démarre une pile `docker compose` (PostgreSQL, RabbitMQ, Keycloak, les 2 services construits) puis lance `tests/acceptance`. 3. Uniquement sur le cluster, hors CI | 2 | Les critères traversent les deux services et Keycloak : seule une pile complète les teste en conditions réelles. Le `docker compose` de la phase 4 est réutilisé, sans dépendre du cluster local (inaccessible depuis GitHub) |
| 31/10/2026 | P2-01 : 4 ou 5 indicateurs ? | 1. Les 4 du plan. 2. Ajouter le taux de critères d'acceptation validés | 2, présentée à Lucas avec le découpage | La grille cite « fonctionnalité, performance, maintenabilité, fiabilité » : les 4 indicateurs du plan ne couvrent pas l'aptitude fonctionnelle. Le 5ᵉ ne demande aucun outil nouveau |
