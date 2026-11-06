# Résumé de l'exécution de charge

**Tous les seuils sont respectés.**

Code de sortie de `run.sh` : 0 dans tous les cas (un dépassement ouvre un ticket de dette sans bloquer, conformément au processus de test).

## Mesures et seuils

| Mesure | Valeur | Seuil | Verdict | Source |
| --- | --- | --- | --- | --- |
| Lecture du catalogue (liste) | 21 ms | p95 < 300 ms | conforme | 3034 requêtes |
| Publication d'article | 23 ms | p95 < 500 ms | conforme | 291 requêtes |
| Réponses 5xx, vues par Locust | 0,000 % (0 sur 6564) | < 1 % | conforme | toutes requêtes de charge |
| Réponses 5xx, vues par les services | 0,000 % (0 sur 6630) | < 1 % | conforme | Prometheus, hors sondes et /metrics |
| Délai des notifications (ENF-14) | moins de 0,1 s | p95 < 2 s | conforme | Prometheus ; p95 interpolé dans le seau 0 à 0,1 s (valeur interpolée : 0,095 s) |

Le total vu par les services (Prometheus) diffère de celui de Locust : `increase()` est calculé sur une fenêtre élargie de 35 s après la fin du test (dernière collecte) et extrapolé aux bords de la fenêtre, et il compte aussi les requêtes qui ne viennent pas de Locust.

Compléments (mêmes seuils de lecture ou de publication, à titre indicatif) :

| Mesure | Valeur | Seuil | Verdict | Source |
| --- | --- | --- | --- | --- |
| GET /categories (complément) | 13 ms | p95 < 300 ms | conforme | 1169 requêtes |
| GET /articles/{id} (complément) | 16 ms | p95 < 300 ms | conforme | 1918 requêtes |
| PUT /articles/{id}/price (complément) | 28 ms | p95 < 500 ms | conforme | 152 requêtes |

## Détail par requête (Locust, plateau seulement)

| Requête | Requêtes | Échecs | Médiane (ms) | p95 (ms) |
| --- | ---: | ---: | ---: | ---: |
| GET /articles | 3034 | 0 | 12 | 21 |
| GET /articles/{id} | 1918 | 0 | 9 | 16 |
| GET /categories | 1169 | 0 | 7 | 13 |
| POST /articles | 291 | 0 | 14 | 23 |
| PUT /articles/{id}/price | 152 | 0 | 17 | 28 |
| [connexion] renouvellement (hors seuils) | 10 | 0 | 35 | 97 |

## Fenêtre de mesure

Plateau de 06/11/2026 11:07:02 à 06/11/2026 11:12:13 (310 s), catégorie de l'exécution « Charge 20261106-1106 ». Prometheus interrogé 35 s après la fin pour inclure la dernière collecte.

## Environnement

```
Date de début : 06/11/2026 11:06:11
Paramètres : 50 utilisateurs, montée de 1 par seconde, durée totale 6m
Cible : https://api.127.0.0.1.sslip.io (TLS vérifié) ; Keycloak : https://auth.127.0.0.1.sslip.io
Locust : locust 2.47.0
Commit du dépôt : d8eb5ec

Images déployées :
  catalog-service	ghcr.io/luucaaas/catalog-service:sha-9d2c96e@sha256:30c1e2826661ed12ce58b5e1e46ab433a6ec6bf5d858cf7ef7394b38095e2664
  notification-service	ghcr.io/luucaaas/notification-service:sha-9d2c96e@sha256:bcdee8e71b393be313cd9a2553d5e8d38f2c4a9781ea9401fc370774454b58d9
  frontend	ghcr.io/luucaaas/frontend:sha-9d2c96e@sha256:7d7671aa723dc8ecb51da4c1dfff2902990b56896961588537fc4369b585de34

Digests lus sur les pods :
  catalog-service-597f75fc48-hs2q4	ghcr.io/luucaaas/catalog-service@sha256:30c1e2826661ed12ce58b5e1e46ab433a6ec6bf5d858cf7ef7394b38095e2664
  catalog-service-597f75fc48-nj5jp	ghcr.io/luucaaas/catalog-service@sha256:30c1e2826661ed12ce58b5e1e46ab433a6ec6bf5d858cf7ef7394b38095e2664
  frontend-787656f4df-twzkj	ghcr.io/luucaaas/frontend@sha256:7d7671aa723dc8ecb51da4c1dfff2902990b56896961588537fc4369b585de34
  frontend-787656f4df-zqqk5	ghcr.io/luucaaas/frontend@sha256:7d7671aa723dc8ecb51da4c1dfff2902990b56896961588537fc4369b585de34
  notification-service-587d8ff55f-88bj5	ghcr.io/luucaaas/notification-service@sha256:bcdee8e71b393be313cd9a2553d5e8d38f2c4a9781ea9401fc370774454b58d9
  notification-service-587d8ff55f-vnt4z	ghcr.io/luucaaas/notification-service@sha256:bcdee8e71b393be313cd9a2553d5e8d38f2c4a9781ea9401fc370774454b58d9


HPA avant l'exécution (11:06:12) :
NAME                   REFERENCE                         TARGETS       MINPODS   MAXPODS   REPLICAS   AGE
catalog-service        Deployment/catalog-service        cpu: 6%/70%   2         5         2          57m
frontend               Deployment/frontend               cpu: 4%/70%   2         5         2          56m
notification-service   Deployment/notification-service   cpu: 6%/70%   2         5         2          57m


HPA après l'exécution (11:12:13) :
NAME                   REFERENCE                         TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
catalog-service        Deployment/catalog-service        cpu: 61%/70%   2         5         2          63m
frontend               Deployment/frontend               cpu: 4%/70%    2         5         2          62m
notification-service   Deployment/notification-service   cpu: 5%/70%    2         5         2          63m
```
