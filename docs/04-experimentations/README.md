# 04 — Expérimentations en bac à sable

Un protocole par technologie testée. Chaque dossier contient le protocole (`protocole.md`), le script qui le rejoue (`run.sh`) et le code ou les manifestes nécessaires. Un protocole n'est pas un guide d'installation : il pose une question, mesure, constate les limites et aboutit à une décision.

## Index

| N° | Expérimentation | Dossier | Décision |
| --- | --- | --- | --- |
| 1 | RabbitMQ sur Kubernetes (k3d, image officielle, StatefulSet, sans opérateur) | [01-rabbitmq](01-rabbitmq/protocole.md) | Adoptée (0 message perdu sur 2 × 1 000, retour à Ready du broker en 10 s au lieu de 54 s avec l'opérateur, abandonné) |
| 2 | Keycloak + Traefik + certificat mkcert (images officielles, sans opérateur) | [02-keycloak-tls](02-keycloak-tls/protocole.md) | Adoptée (validation locale des JWT, 15 cas d'autorisation conformes ; PKCE et rotation des clés à tester avec le front) |
| 3 | Observabilité : kube-prometheus-stack (Prometheus, Grafana) sur k3d | [03-observabilite](03-observabilite/protocole.md) | Adoptée en version allégée (bornes d'histogramme à définir pour le p95) |
| 4 | (option) Kafka | écartée (journal des décisions du 02/11/2026) | Rejeté par l'ADR 0003 |

## Modèle commun des protocoles

Chaque `protocole.md` suit les 8 rubriques ci-dessous, dans cet ordre.

1. **Objectif et question posée** : ce qu'on veut prouver, formulé comme une question à laquelle l'expérience répond par oui ou non.
2. **Technologies testées et interactions** : composants en jeu et leurs échanges (schéma Mermaid court si utile).
3. **Environnement** : machine, système, Docker (CPU, mémoire), versions **exactes** de chaque outil, image et chart.
4. **Étapes reproductibles** : la commande unique (`run.sh`) et ce que fait chaque étape.
5. **Résultats mesurés** : tableau des valeurs réelles de la dernière exécution, avec sa date.
6. **Difficultés rencontrées et solutions** : ce qui a posé problème, comment c'est résolu.
7. **Limites de l'expérimentation** : ce que l'expérience ne prouve pas.
8. **Décision** : adoption, rejet ou conditions, avec renvoi vers l'ADR concernée.

Règles communes :

- Tout se rejoue par script, sur un cluster k3d jetable, supprimé à la fin (option `--keep` pour le conserver).
- Les versions sont figées, d'un tag précis et publié depuis plusieurs semaines. Aucun chart ni image Bitnami : l'infrastructure s'installe avec les opérateurs officiels des éditeurs.
- Aucun secret dans le dépôt : les identifiants sont générés par l'opérateur et lus dans le Secret Kubernetes.
- Le code de bac à sable est vérifié par Ruff et mypy, sans tests unitaires : ce n'est pas une fonctionnalité du POC.
