# Résumé de l'exécution de charge et de disponibilité

Paramètres : charge nominale 50 utilisateurs pendant 240 s (montée de 1 par seconde), 
pic de 200 utilisateurs (montée de 5 par seconde), attente maximale des 5 réplicas 420 s,
maintien de 60 s à 5 réplicas puis de 60 s après le retour, observation de la réduction 900 s au plus.
Exécution du 11/11/2026 19:30, commit e724741, images sha-5975ca0.

## Chronologie (instants locaux, secondes depuis le début du pic)

| Événement | Instant |
| --- | --- |
| Début de la charge nominale | 19:30:50 |
| Début du pic | 19:34:50 (0 s) |
| HPA demande 3 réplicas | 19:35:33 (+43 s) |
| HPA demande 4 réplicas | 19:35:33 (+43 s) |
| HPA demande 5 réplicas | 19:35:49 (+59 s) |
| 3 réplicas prêts | 19:35:39 (+49 s) |
| 4 réplicas prêts | 19:35:39 (+49 s) |
| 5 réplicas prêts | 19:35:49 (+59 s) |
| Suppression d'un pod | 19:36:50 (+120 s) |
| Ancien pod disparu | 19:36:57 (+127 s) |
| Pod de remplacement prêt | 19:36:56 (+126 s) |
| Tous les réplicas de nouveau prêts | 19:36:57 (+127 s) |
| Arrêt de la charge | 19:37:57 (+187 s) |
| HPA demande 2 réplicas | 19:43:21 (+511 s) |
| Il ne reste que 2 pods | 19:43:26 (+516 s) |

## Délais

- Suppression du pod : ancien pod disparu après 7,3 s, remplaçant prêt après 6,0 s, tous les réplicas de nouveau prêts après 7,5 s.
- Du début du pic à 3 réplicas demandés : 43 s, prêts après 49 s.
- Du début du pic à 4 réplicas demandés : 43 s, prêts après 49 s.
- Du début du pic à 5 réplicas demandés : 59 s, prêts après 59 s.
- De l'arrêt de la charge au retour à 2 réplicas : 328 s.
- CPU de `catalog-service` (moyenne des pods, % de leur requête de 100m) : maximum relevé 157 %.

## Latence et erreurs par phase (requêtes de charge, vues par Locust)

| Phase | Durée | Requêtes | 5xx | Taux de 5xx | Autres échecs | p95 liste | p95 publication | p95 toutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nominale (50 utilisateurs, hors montée) | 190 s | 4024 | 0 | 0,00 % | 0 | 10 ms | 14 ms | 10 ms |
| Pic, montée de l'HPA | 59 s | 4189 | 0 | 0,00 % | 0 | 18 ms | 21 ms | 16 ms |
| Pic, 5 réplicas prêts | 61 s | 5224 | 0 | 0,00 % | 0 | 12 ms | 14 ms | 12 ms |
| Suppression du pod, jusqu'au retour des réplicas | 7 s | 642 | 0 | 0,00 % | 0 | 21 ms | 22 ms | 20 ms |
| Pic après remplacement | 60 s | 5133 | 0 | 0,00 % | 0 | 11 ms | 14 ms | 11 ms |

## Échecs autour de la suppression du pod (de -5 s à +60 s)

- Aucun échec dans la fenêtre.

## Côté services (Prometheus, de la charge nominale à l'arrêt)

- 0 réponses 5xx sur 19831 requêtes (0,00 %).
