# Fiches de tâche

Chaque tâche confiée à un agent a sa fiche `docs/suivi/taches/<id>.md` (ex. `P2-01.md`). La fiche est la mémoire de la tâche : elle permet à n'importe quelle session de reprendre le travail là où il s'est arrêté.

Qui écrit quoi :

| Section | Rédigée par | Quand |
| --- | --- | --- |
| Brief | Chef | Avant la délégation, commitée sur main avec `ETAT.md` |
| Journal du développeur | Développeur | Après chaque étape terminée, commitée sur la branche de la tâche |
| Rapport d'audit | Chef (recopie du rapport de l'auditeur) | Après chaque audit |
| Décision finale du chef | Chef | Au moment de fusionner, de renvoyer ou d'abandonner |

## Modèle

Copier le bloc ci-dessous dans `docs/suivi/taches/<id>.md`.

```markdown
# <id> — <titre>

## Brief

- **Objectif** : <ce qui doit exister à la fin, en une ou deux phrases>
- **Contexte** : <phase du plan, user story ou critère de la grille visé, liens vers la doc>
- **Fichiers concernés** : <chemins créés ou modifiés>
- **Hors périmètre** : <ce qu'il ne faut pas faire>
- **Critères de fin** (vérifiables) :
  - [ ] <critère 1, avec la commande ou le fichier qui le prouve>
  - [ ] <critère 2>
  - [ ] Tests, `ruff check` et `mypy` passent (si du code est concerné)
- **Branche** : `phase-<N>/<nom-tache>`
- **Agent** : developpeur

## Journal du développeur

### <date heure> — <étape>

- Fait : <...>
- Commandes lancées : `<commande>` → <résultat>
- Commit : `<hash court>` <message>
- Reste à faire : <...>

## Rapport d'audit

### Audit n° <1, 2, 3> — <date heure>

- Verdict : CONFORME / NON CONFORME / DOUTE

| Point vérifié | Statut | Preuve |
| --- | --- | --- |
| <...> | <...> | <commande, fichier:ligne> |

- Écarts à corriger : <...>
- Doutes : <...>

## Décision finale du chef

- Date : <date heure>
- Décision : fusionnée sur main (`<hash>`) / renvoyée au développeur (aller-retour n° <1 ou 2>) / tranchée par le chef / abandonnée
- Contre-vérification du chef : <oui (tâche critique) ou non, avec les commandes lancées>
- Justification : <...>
```
