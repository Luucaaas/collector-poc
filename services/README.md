# Services backend (Python / FastAPI)

| Service | Rôle |
| --- | --- |
| `catalog-service` | Catégories, boutiques, articles, contrôle automatique, historique des prix, publication des événements sur l'exchange `article.events` |
| `notification-service` | Centres d'intérêt, préférences, consommation des événements, notifications |

L'outil anti-fraude n'est pas dans le POC. C'est un point d'extension : interne ou acheté, il s'abonnera à l'exchange `article.events` avec sa propre file, sans modification de `catalog-service` (ADR 0007).
