# 07 — Soutenance

| Document | Contenu |
| --- | --- |
| [guide-jury.md](guide-jury.md) | Pour chacun des 10 critères de la grille : ce qui est attendu pour 5/5, où trouver le livrable, les preuves mesurées avec leur source, les limites assumées ; parcours de lecture en 10 minutes |
| [demo/script-demo.md](demo/script-demo.md) | Démonstration de 6 minutes : déroulé minuté, commande et phrases à dire par étape, ce que le jury doit voir, plan de secours, disposition des fenêtres, listes « la veille » et « 15 minutes avant » |
| [demo/](demo) (scripts) | `preparer.sh` (vérification d'avant-démo), `donnees-demo.sh` (jeu de données propre), `mot-de-passe.sh` (mot de passe en presse-papiers sans l'afficher), `pic-charge.sh` (pic de charge et suppression d'un pod en direct) |
| [verifier-guide.py](verifier-guide.py) | Contrôle que chaque lien et chaque ancre du guide et du [README racine](../../README.md) existent, et que les chiffres cités se retrouvent dans leur fichier source |

```bash
python3 -I docs/07-soutenance/verifier-guide.py     # code de sortie 0 : liens et chiffres conformes
```

Pour lancer le POC, voir le [README racine](../../README.md).
