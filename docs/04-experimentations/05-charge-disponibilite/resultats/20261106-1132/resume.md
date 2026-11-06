# Résumé de l'exécution de charge et de disponibilité

Paramètres : charge nominale 50 utilisateurs pendant 240 s (montée de 1 par seconde), 
pic de 200 utilisateurs (montée de 5 par seconde), attente maximale des 5 réplicas 420 s,
maintien de 60 s à 5 réplicas puis de 60 s après le retour, observation de la réduction 900 s au plus.
Exécution du 06/11/2026 11:32, commit 9f04231, images sha-9d2c96e.

## Chronologie (instants locaux, secondes depuis le début du pic)

| Événement | Instant |
| --- | --- |
| Début de la charge nominale | 11:32:56 |
| Début du pic | 11:36:56 (0 s) |
| HPA demande 3 réplicas | 11:37:08 (+11 s) |
| HPA demande 4 réplicas | 11:37:42 (+45 s) |
| HPA demande 5 réplicas | 11:37:53 (+56 s) |
| 3 réplicas prêts | 11:37:14 (+17 s) |
| 4 réplicas prêts | 11:37:42 (+45 s) |
| 5 réplicas prêts | 11:37:56 (+60 s) |
| Suppression d'un pod | 11:38:56 (+120 s) |
| Ancien pod disparu | 11:39:03 (+126 s) |
| Pod de remplacement prêt | 11:39:01 (+125 s) |
| Tous les réplicas de nouveau prêts | 11:39:03 (+126 s) |
| Arrêt de la charge | 11:40:03 (+186 s) |
| HPA demande 2 réplicas | 11:45:23 (+506 s) |
| Il ne reste que 2 pods | 11:45:28 (+511 s) |

## Délais

- Suppression du pod : ancien pod disparu après 6,1 s, remplaçant prêt après 4,9 s, tous les réplicas de nouveau prêts après 6,2 s.
- Du début du pic à 3 réplicas demandés : 11 s, prêts après 17 s.
- Du début du pic à 4 réplicas demandés : 45 s, prêts après 45 s.
- Du début du pic à 5 réplicas demandés : 56 s, prêts après 60 s.
- De l'arrêt de la charge au retour à 2 réplicas : 325 s.
- CPU de `catalog-service` (moyenne des pods, % de leur requête de 100m) : maximum relevé 186 %.

## Latence et erreurs par phase (requêtes de charge, vues par Locust)

| Phase | Durée | Requêtes | 5xx | Taux de 5xx | Autres échecs | p95 liste | p95 publication | p95 toutes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Nominale (50 utilisateurs, hors montée) | 190 s | 4040 | 0 | 0,00 % | 0 | 20 ms | 23 ms | 19 ms |
| Pic, montée de l'HPA | 60 s | 4233 | 0 | 0,00 % | 0 | 84 ms | 127 ms | 104 ms |
| Pic, 5 réplicas prêts | 60 s | 5171 | 0 | 0,00 % | 0 | 13 ms | 16 ms | 13 ms |
| Suppression du pod, jusqu'au retour des réplicas | 6 s | 533 | 0 | 0,00 % | 0 | 12 ms | 16 ms | 12 ms |
| Pic après remplacement | 60 s | 5133 | 0 | 0,00 % | 0 | 13 ms | 20 ms | 13 ms |

## Échecs autour de la suppression du pod (de -5 s à +60 s)

- Aucun échec dans la fenêtre.

## Côté services (Prometheus, de la charge nominale à l'arrêt)

- 0 réponses 5xx sur 20235 requêtes (0,00 %).
