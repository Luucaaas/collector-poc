# 07 — Soutenance

| Document | Contenu |
| --- | --- |
| [guide-jury.md](guide-jury.md) | Pour chacun des 10 critères de la grille : ce qui est attendu pour 5/5, où trouver le livrable, les preuves mesurées avec leur source, les limites assumées ; parcours de lecture en 10 minutes |
| [support.md](support.md) | Contenu du support de présentation : plan minuté de 20 minutes (14 diapositives et la démonstration de 6 minutes), pour chaque diapositive le message, le contenu, le visuel, les chiffres sourcés, les critères, les notes orales et la transition ; correspondance diapositive et critère ; 6 annexes pour les questions |
| [questions.md](questions.md) | 68 questions probables du jury pour les 15 minutes d'échange, par critère (1 à 10) et par thème (choix techniques, limites, organisation, démonstration qui échoue) : réponse courte à dire, chiffres sourcés, document à montrer, limite à reconnaître avec son action du plan |
| [glossaire.md](glossaire.md) | Termes techniques à employer exactement (Kubernetes, livraison, sécurité et identité, messagerie, qualité, projet), avec leur définition et l'endroit où ils apparaissent dans le POC |
| [demo/script-demo.md](demo/script-demo.md) | Démonstration de 6 minutes : déroulé minuté, commande et phrases à dire par étape, ce que le jury doit voir, plan de secours, disposition des fenêtres, listes « la veille » et « 15 minutes avant » |
| [demo/](demo) (scripts) | `preparer.sh` (vérification d'avant-démo), `donnees-demo.sh` (jeu de données propre), `mot-de-passe.sh` (mot de passe en presse-papiers sans l'afficher), `pic-charge.sh` (pic de charge et suppression d'un pod en direct) |
| [verifier-guide.py](verifier-guide.py) | Contrôle que chaque lien et chaque ancre du guide, du [support](support.md) et du [README racine](../../README.md) existent, que les chiffres cités se retrouvent dans leur fichier source, et que le minutage du support totalise 20 minutes ; contrôle aussi `questions.md` (au moins 40 questions complètes, tous les critères couverts, chiffres recoupés) et `glossaire.md` (au moins 40 termes) |

```bash
python3 -I docs/07-soutenance/verifier-guide.py     # code de sortie 0 : liens et chiffres conformes
```

Pour lancer le POC, voir le [README racine](../../README.md).
