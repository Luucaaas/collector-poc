# 07 — Soutenance

| Document | Contenu |
| --- | --- |
| [guide-jury.md](guide-jury.md) | Pour chacun des 10 critères de la grille : ce qui est attendu pour 5/5, où trouver le livrable, les preuves mesurées avec leur source, les limites assumées ; parcours de lecture en 10 minutes |
| [verifier-guide.py](verifier-guide.py) | Contrôle que chaque lien et chaque ancre du guide et du [README racine](../../README.md) existent, et que les chiffres cités se retrouvent dans leur fichier source |

```bash
python3 -I docs/07-soutenance/verifier-guide.py     # code de sortie 0 : liens et chiffres conformes
```

Pour lancer le POC, voir le [README racine](../../README.md).
