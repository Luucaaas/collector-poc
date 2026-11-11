# Script de la démonstration (6 minutes)

Démonstration du POC en direct devant le jury : **pipeline, déploiement, parcours métier, supervision, montée en charge et disponibilité**. Le déroulé est minuté (mesures dans le [journal de la fiche P10-02](../../suivi/taches/P10-02.md)), chaque étape a sa commande exacte, ce qu'on dit, ce que le jury doit voir et un plan de secours.

**Critères de la grille servis** : 10 (démonstration préparée), 3 (fonctionnalité métier), 4 (CI/CD), 5 (disponibilité et montée en charge).

## Vue d'ensemble

| # | Étape | Durée | Où | Critère |
| --- | --- | --- | --- | --- |
| 1 | Pipeline et déploiement (en parallèle) | 1 min 20 | GitHub Actions + terminal | 4 |
| 2 | Parcours métier | 1 min 55 | Navigateur (alice), fenêtre privée (chloe) | 3 |
| 3 | Pic de charge, Grafana et suppression d'un pod | 1 min 55 | Terminal + Grafana | 5 |
| | **Total** | **5 min 10**, marge de 50 s | | |

Les 50 secondes de marge servent à la saisie en direct (la partie la plus variable) et à une éventuelle lenteur d'une étape. Si tu es en avance, ne rajoute rien : garde le temps pour les questions.

**Le pipeline n'est pas joué en entier en direct** : un run de `backend` dure environ 8 min 30 (8 min 37 s pour le run 43064777792). Tu pousses un commit vide sur `main` **15 minutes avant la soutenance** (voir « 15 minutes avant » plus bas) et tu attends les deux workflows verts ; pendant la démonstration tu montres **ce run terminé** et tu déploies **son tag** (un tag nouveau : vrai remplacement des pods). Secours : le tag précédent déjà publié, en disant que le run montré est alors celui de ce tag.

## Minutage mesuré

Mesures du 11/11/2026 sur le cluster (deux répétitions complètes de la partie automatisable, détail dans le [journal de la fiche P10-02](../../suivi/taches/P10-02.md)) :

| Élément | Répétition 1 | Répétition 2 | Ce que ça fixe dans le script |
| --- | --- | --- | --- |
| `preparer.sh` (contrôle complet) | 5 s | 4 s | Se lance à 15 minutes de la démonstration, pas pendant |
| `donnees-demo.sh` (relance, sans création) | 1 s | 1 s | Création initiale : 2 s |
| `deploy.sh services <tag>` d'un tag nouveau (vrai remplacement des pods) | 41 s | 36 s | Étape 1 : de 36 à 57 s (57 s à la toute première mesure) ; on le lance **avant** de parler du pipeline pour que les deux se recouvrent |
| `deploy.sh services <tag>` du tag déjà déployé (rien à remplacer) | 19 s | | Repli si le run du commit du jour n'est pas prêt |
| Parcours Playwright des 6 scénarios en mode visible | 11 s (20 s à froid) | 11 s | Borne basse de l'étape 2 : la saisie humaine (5 champs par article) ajoute environ 1 minute, d'où 1 min 55 |
| `pic-charge.sh` (de bout en bout) | 73 s, 5 réplicas à 43 s | 85 s, 5 réplicas à 55 s | Étape 3 : de 73 à 87 s sur les 3 exécutions aux réglages définitifs (73, 85 et 87 s) |

La saisie en direct (étape 2) est la seule durée **estimée** : un automate ne se trompe pas de touche. Les 50 secondes de marge la couvrent.

## Disposition des fenêtres

| Fenêtre | Contenu | État au moment de commencer |
| --- | --- | --- |
| **Terminal** (plein écran, police agrandie à 18 pt ou plus) | Dossier du dépôt, `clear` fait. Une seule fenêtre, un seul onglet | Prêt à taper |
| **Navigateur normal**, onglet 1 | https://github.com/Luucaaas/collector-poc/actions : liste des runs, celui du commit du jour en tête | Ouvert |
| Navigateur normal, onglet 2 | https://app.127.0.0.1.sslip.io, **connecté en `alice`**, page « Vendre », boutique « Le Comptoir d'Alice » et catégorie « Figurines » déjà choisies | Ouvert, **ne pas recharger** |
| Navigateur normal, onglet 3 | Grafana connecté : https://grafana.127.0.0.1.sslip.io/d/collector-service?var-service=catalog-service&from=now-10m&to=now&refresh=5s | Ouvert |
| **Fenêtre privée** | https://app.127.0.0.1.sslip.io, **connecté en `chloe`**, page « Mes centres d'intérêt » | Ouverte |

Pourquoi **ne pas recharger** les pages connectées : les jetons de connexion sont gardés en mémoire (choix de sécurité du POC), un rechargement les perd. Ce n'est pas grave (cliquer sur « Connexion » ramène sans mot de passe grâce à la session Keycloak), mais ça coûte 10 secondes.

Pourquoi **deux navigateurs** : alice et chloe ont chacune leur session ; la fenêtre privée évite que la session de l'une écrase celle de l'autre.

## Étape 1 : pipeline et déploiement (0:00 à 1:20)

**Principe** : tu lances le déploiement dans le terminal, puis tu parles du pipeline pendant qu'il tourne (il dure 40 à 60 secondes), puis tu reviens lire le résultat.

### 1a. Lancer le déploiement (terminal, 0:00 à 0:10)

```bash
deploy/local/deploy.sh services sha-XXXXXXX
```

(`sha-XXXXXXX` : les 7 premiers caractères du commit poussé 15 minutes avant, par exemple `sha-5975ca0` ; `git rev-parse --short=7 HEAD` les donne.)

**Ce qu'on dit.** « Je déploie sur Kubernetes l'image que la CI vient de publier. Le déploiement est automatisé par un script, qui utilise Helm, le gestionnaire de paquets de Kubernetes. Pendant qu'il tourne, je vous montre le pipeline. »

### 1b. Le pipeline (navigateur, onglet 1, 0:10 à 0:45)

Cliquer sur le run `backend` du commit du jour, puis montrer le graphe des jobs.

**Ce qu'on dit.** « À chaque push, GitHub Actions déroule le pipeline conforme au schéma de la page CI/CD : `lint` (Ruff, mypy), `test` (couverture d'au moins 80 %), `sonar` (analyse de qualité), `build-scan` (construction de l'image et scan Trivy, qui bloque sur les vulnérabilités CRITICAL et HIGH dont un correctif existe), `acceptance` (les 17 critères d'acceptation sur une pile docker compose), puis `publish` sur `main` : image amd64 et arm64 publiée sur GHCR avec le tag `sha-` suivi du commit. Un job rouge arrête tout, et j'ai des runs rouges qui le démontrent. »

**Ce que le jury doit voir** : le run **vert**, ses jobs de `lint` à `publish`, la durée totale, et le tag `sha-XXXXXXX` identique à celui tapé dans le terminal.

**Critère** : 4 (pipeline réel conforme au schéma).

### 1c. Lire le résultat du déploiement (terminal, 0:45 à 1:20)

Revenir au terminal : le déploiement est fini (ou presque). Montrer, de haut en bas, les blocs de la sortie.

**Ce qu'on dit.** « Le script vérifie d'abord que les trois images existent sur GHCR et note leur empreinte, le digest. Puis `helm upgrade` remplace les pods un par un : Kubernetes n'éteint l'ancien pod que quand le nouveau répond à sa sonde de santé, donc il n'y a pas d'interruption. Ensuite un test de fumée de 25 contrôles passe par l'Ingress, comme un vrai client. Et si un seul échoue, le script revient tout seul à la version précédente. Dernier point : le digest que le cluster exécute réellement, affiché dans le bloc « Images en cours d'exécution (imageID) » en fin de sortie, est celui publié par la CI : c'est la traçabilité du commit au pod. »

**Ce que le jury doit voir** : la ligne `smoke.sh` avec ses contrôles `OK` (25), les lignes `deployment ... successfully rolled out`, le bloc « Images en cours d'exécution (imageID) » avec les `sha256:...` des pods, puis la liste finale des pods en `Running` et `2/2` dans la colonne `READY` des trois composants.

**Plan de secours étape 1.**

| Problème | Que faire |
| --- | --- |
| Le run du commit du jour n'est pas terminé ou est rouge | Montrer le run de référence : [`backend` du relevé de la phase 8](https://github.com/Luucaaas/collector-poc/actions/runs/42219458020) (11 jobs verts) et déployer le tag déjà sur le cluster (`deploy/local/deploy.sh services sha-5975ca0` prend 19 s : aucun pod à remplacer) |
| Le déploiement traîne (plus de 70 s) | Ne pas attendre : passer à l'étape 2, la sortie se lit plus tard ; le cluster reste utilisable pendant le remplacement des pods |
| Le déploiement échoue | C'est une bonne démonstration : le script affiche « ÉCHEC : retour arrière » et remet la version précédente. Le dire, vérifier que les pods sont `Running` (`kubectl -n collector get pods`) et continuer |
| GitHub inaccessible | Schéma du pipeline : `docs/01-qualite/img/pipeline-cicd.svg` et [conformité du pipeline](../../01-qualite/conformite-pipeline.md) |

## Étape 2 : parcours métier (1:20 à 3:15)

**Ce que montre cette étape** : le cœur de la fonctionnalité de Collector : un vendeur publie, le contrôle automatique accepte ou rejette, un événement part dans RabbitMQ, l'acheteur intéressé est notifié.

### 2a. Le catalogue (navigateur normal, onglet 2, 1:20 à 1:30)

Ouvrir « Catalogue » : 11 articles de collection crédibles, 5 catégories.

**Ce qu'on dit.** « Voici le catalogue, public : figurines, cartes, jeux vidéo rétro. Chloe, une acheteuse, a choisi de suivre la catégorie Figurines. »

### 2b. Alice publie un article (onglet 2, page « Vendre », 1:30 à 2:10)

Formulaire « Mettre un article en vente » (boutique et catégorie « Figurines » déjà choisies). Saisir :

| Champ | Valeur à saisir |
| --- | --- |
| Titre | `Boba Fett Kenner 1979` |
| Description | `Figurine originale Kenner de 1979, complète, très bon état.` |
| Adresse de la photo | `https://images.example.com/boba.jpg` |
| Prix | `120,00` |
| Frais de port | `8,00` |

Cliquer « Mettre en vente » : le message **« Article publié »** apparaît.

**Ce qu'on dit.** « Alice, vendeuse, publie une figurine. Le service catalogue applique un contrôle automatique : champs obligatoires, prix positif, et aucun email ni numéro de téléphone dans le texte, pour empêcher de contourner la commission. Ici l'article est conforme : statut publié. »

### 2c. Le rejet (même formulaire, 2:10 à 2:30) — à sauter si tu es en retard

Titre `Annonce suspecte`, description `Appelez-moi au 06 12 34 56 78 pour traiter hors site.`, photo `https://images.example.com/x.jpg`, prix `50,00`, puis « Mettre en vente » : **« Article rejeté par le contrôle automatique »**, motif « le texte contient un numéro de téléphone ».

**Ce qu'on dit.** « Même formulaire avec un numéro de téléphone : l'article est rejeté, avec le motif. C'est la règle de gestion qui protège le modèle économique. »

### 2d. Le changement de prix (onglet 2, 2:30 à 2:45)

Descendre à « Mes articles publiés », ligne « Boba Fett Kenner 1979 », champ « Nouveau prix » : `95`, « Modifier le prix ».

**Ce qu'on dit.** « Alice baisse le prix à 95 euros. L'historique des prix est conservé, et un deuxième événement part. »

### 2e. Chloe est notifiée (fenêtre privée, 2:45 à 3:15)

Basculer sur la fenêtre privée de chloe, page « Mes centres d'intérêt », bouton **« Actualiser »** dans la liste des notifications : deux notifications apparaissent, « Nouvel article : Boba Fett Kenner 1979 » (120,00) et « Changement de prix » (de 120,00 à 95,00).

**Ce qu'on dit.** « Chloe n'a rien fait : le service catalogue a publié deux événements dans RabbitMQ, le service notification les a consommés et lui a créé ses notifications. Les deux services ne s'appellent jamais directement : ils ne communiquent que par les événements. C'est aussi là que se branchera plus tard l'outil anti-fraude, sans toucher au catalogue. »

**Ce que le jury doit voir** : « Article publié », « Article rejeté » avec son motif, le prix modifié avec l'historique, puis les deux notifications chez chloe, **dans un autre navigateur, sans rechargement manuel du catalogue**.

**Critère** : 3 (la fonctionnalité répond au contexte : contrôle automatique, événement, notification) et, en filigrane, 2 (découpage, communication interservice, sécurité par authentification).

**Plan de secours étape 2.**

| Problème | Que faire |
| --- | --- |
| Une saisie se passe mal (champ refusé, faute de frappe) | Corriger sans commenter, ne pas recommencer tout le formulaire |
| La notification n'arrive pas | Recliquer sur « Actualiser » (l'événement est asynchrone, 1 à 2 s) ; au bout de 10 s, passer à l'étape suivante et dire « les notifications sont asynchrones, je reviens dessus à la fin » |
| Session expirée ou page perdue | Cliquer « Connexion » : la session Keycloak ramène sans mot de passe. Sinon, copier le mot de passe sans le montrer : `docs/07-soutenance/demo/mot-de-passe.sh alice` (ou `chloe`), puis Cmd+V dans le champ ; le presse-papiers est vidé après 30 s |
| Tout le parcours échoue | Montrer les 7 captures : `frontend/e2e/resultats/captures/` (catalogue, connexion, article publié, rejeté, historique des prix, notifications), et c'est tout. **Cas extrême seulement** : rejouer le parcours automatisé `frontend/e2e/run-cluster.sh --headed` (11 à 20 s, 6 parcours sur 6) **ajoute des données de test (« E2E ») au catalogue** : à réserver à une démonstration déjà perdue |
| Plus rien ne marche | Vidéo de secours (enregistrée par toi) |

## Étape 3 : pic de charge, Grafana et suppression d'un pod (3:15 à 5:10)

**Ce que montre cette étape** : le critère 5, la scalabilité (l'HPA ajoute des pods sous la charge) et la disponibilité (un pod supprimé en pleine charge est remplacé sans erreur).

### 3a. Lancer le pic (terminal, 3:15 à 3:35)

```bash
docs/07-soutenance/demo/pic-charge.sh
```

**Ce qu'on dit.** « Je lance maintenant un pic de charge : 300 utilisateurs simulés avec Locust (à froid, 200 n'atteignent pas toujours les 5 réplicas en 75 secondes ; la mesure de référence reste le protocole 5, à 200 utilisateurs), 80 % de lecteurs et 20 % de vendeurs qui publient, comme sur le vrai site. À l'écran, le terminal se rafraîchit toutes les 2 secondes : en haut l'HPA, l'autoscaler horizontal, qui regarde le processeur des pods ; en dessous les pods du service catalogue. Au départ il y en a 2. »

**Ce que le jury doit voir** : la ligne de l'HPA avec la colonne `TARGETS` (par exemple `135%/70%`, le processeur dépasse la cible de 70 %) puis la colonne `REPLICAS` qui monte, et de nouveaux pods en `ContainerCreating` puis `Running`.

### 3b. Grafana pendant la montée (navigateur, onglet 3, 3:35 à 4:05)

Basculer sur Grafana, tableau de bord « Collector - service » (service `catalog-service`), qui se rafraîchit toutes les 5 secondes.

**Ce qu'on dit.** « Pendant que Kubernetes réagit, voici la supervision : Prometheus collecte les métriques de chaque pod, Grafana les affiche. Le débit monte, la latence p95 reste sous notre seuil de 300 ms, le taux d'erreur reste à zéro, et le panneau Réplicas montre l'HPA qui passe de 2 à 4 ou 5 pods. »

**Ce que le jury doit voir** : les panneaux **Débit** en hausse, **Latence p95** sous 300 ms, **Taux d'erreur** à 0, **Réplicas** qui monte.

### 3c. La suppression d'un pod (terminal, 4:05 à 5:10)

Revenir au terminal **dès que le panneau Réplicas de Grafana montre 4 ou 5 pods, ou au plus tard 50 secondes après le lancement** (les 5 pods sont prêts entre 43 et 70 secondes). Le script supprime un pod tout seul 12 secondes après les 5 réplicas prêts (ou au bout de 75 secondes, même s'ils ne le sont pas). **Pour choisir le moment toi-même, appuie sur la touche « s »** (le terminal doit être la fenêtre active).

**Ce qu'on dit.** « Maintenant la disponibilité : le script supprime un pod du service catalogue en pleine charge. C'est l'équivalent d'un plantage. Regardez : le pod disparaît, Kubernetes en recrée un tout de suite pour retrouver le nombre de réplicas voulu, et pendant ce temps les 4 autres pods servent le trafic. Le bilan dit combien de temps ça a pris et combien de requêtes ont échoué. »

**Ce que le jury doit voir** : le message « Pod supprimé : catalog-service-... », un nouveau pod qui passe `Running`, puis le **bilan** : réplicas atteints, **remplaçant prêt en environ 5 secondes**, **0 échec pendant le remplacement**, 0 réponse 5xx au total.

**Ce qu'on dit pour finir.** « Le retour à 2 pods se fait ensuite tout seul, au bout de 5 à 10 minutes (mesuré au protocole 5 et pendant les répétitions) : c'est la fenêtre de stabilisation de l'HPA, une protection contre les yoyos. Les mesures complètes sont dans le protocole 5 : 200 utilisateurs, 2 à 5 réplicas en 60 secondes, 20 235 requêtes sans une réponse 5xx. »

**Critère** : 5 (environnement managé, montée en charge et disponibilité **démontrées**), avec le critère 6 en appui (latence p95 et taux d'erreur des indicateurs).

**Plan de secours étape 3.**

| Problème | Que faire |
| --- | --- |
| `pic-charge.sh` refuse de démarrer (« pas à 2 réplicas prêts ») | Le cluster sort d'une charge : attendre le retour à 2 (`kubectl -n collector get hpa`, 5 à 10 minutes), ou montrer directement le résultat versionné ci-dessous |
| Locust ne démarre pas ou le terminal se fige | Ctrl+C (Locust s'arrête proprement), puis montrer le [résumé du protocole 5](../../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/resume.md) et ses captures Grafana `grafana-pic-catalog-service.png` dans le même dossier |
| Les 5 réplicas ne sont pas atteints (le bilan dit « 2 à 4 ») | Ne pas s'en excuser : « la montée dépend de la mesure du processeur, le protocole 5 a mesuré 5 en 60 secondes, ici 4 ; la suppression a eu lieu quand même ». Ce n'est pas un échec du critère (la montée est démontrée) |
| Une requête échoue pendant la suppression | Le dire tel quel et donner le chiffre du bilan ; le protocole 5 en a mesuré 0 sur 533 |
| Grafana est vide ou ne répond pas | Rester sur le terminal, qui montre HPA et pods ; la capture Grafana de secours : `docs/04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-pic-catalog-service.png` |
| Tout échoue | Vidéo de secours |

## Listes de contrôle

### La veille

Le catalogue de la démonstration ne doit pas montrer les données de test (« E2E », « Charge », identifiants aléatoires). L'API n'a pas de suppression : **la solution la plus simple est de refaire un cluster neuf, puis de charger le jeu de données de la démonstration**. Environ 4 minutes en tout (246 s mesurées).

```bash
# 1. Cluster neuf : supprime l'ancien (et toutes ses données) puis recrée tout.
deploy/local/cluster.sh delete
deploy/local/cluster.sh create
deploy/local/deploy.sh all sha-XXXXXXX     # un tag déjà publié sur GHCR ; environ 3 min 30

# 2. Jeu de données : 5 catégories, 2 boutiques, 11 articles, chloe suit « Figurines ».
docs/07-soutenance/demo/donnees-demo.sh    # relançable sans doublon

# 3. Vérification de tout
docs/07-soutenance/demo/preparer.sh        # doit finir par « PRÊT »
```

- [ ] Cluster neuf créé, `donnees-demo.sh` lancé, `preparer.sh` répond « PRÊT ».
- [ ] **Ne plus lancer** de test de charge ni de parcours Playwright après (ils polluent le catalogue). Pour répéter la démonstration, recréer le cluster après.
- [ ] Mac branché sur secteur, mise à jour système et notifications désactivées (mode Ne pas déranger).
- [ ] Docker Desktop lancé, 10 CPU et 8 Go de mémoire (Settings, Resources).
- [ ] Vidéo de secours enregistrée et ouverte dans un lecteur.
- [ ] Répétition complète chronométrée au moins une fois (c'est elle qui rend le discours fluide).
- [ ] `gh auth status` : connecté (sinon `gh auth login`, par toi).

### 15 minutes avant

- [ ] **Pousser le commit du jour** (c'est lui que la démonstration déploie) :
  ```bash
  git commit --allow-empty -m "Démonstration de soutenance"   # sur main
  git push                                                    # lance la CI, qui dure environ 8 min 30
  ```
  Attendre que les **deux** workflows (`backend` et `frontend`) soient verts, puis noter le tag : `sha-$(git rev-parse --short=7 HEAD)`.
- [ ] `docs/07-soutenance/demo/preparer.sh --veille 3` : doit finir par « PRÊT » (l'option empêche la mise en veille du Mac pendant 3 heures). Si une ligne `MANQUE` apparaît, la commande à lancer est écrite dessous.
- [ ] HPA à 2 réplicas, aucun pod en échec (déjà contrôlé par `preparer.sh`).
- [ ] Ouvrir les fenêtres de la disposition ci-dessus, **se connecter** : alice dans le navigateur normal, chloe dans la fenêtre privée. Les mots de passe se copient sans les montrer : `docs/07-soutenance/demo/mot-de-passe.sh alice` puis Cmd+V (idem `chloe`, `grafana`) ; le presse-papiers est vidé après 30 s.
- [ ] Onglet 2 : page « Vendre », boutique et catégorie « Figurines » choisies. Fenêtre privée : page « Mes centres d'intérêt », liste des notifications **vide**.
- [ ] Terminal : agrandir la police, `clear`, se placer dans le dossier du dépôt (`cd "$HOME/Desktop/Cesi/BLOC S3"`).
- [ ] Fermer les autres applications (surtout celles qui consomment du processeur : le test de charge tourne sur le même Mac que le cluster).
- [ ] Le tag du jour noté sur un papier ou dans le terminal.

### Après la démonstration

- Le cluster revient seul à 2 réplicas 5 à 10 minutes après la charge.
- Les données créées en direct (article « Boba Fett », catégorie « Charge ... ») restent dans le catalogue : pour une autre démonstration, refaire la liste « La veille ».
- Presse-papiers vidé : `docs/07-soutenance/demo/mot-de-passe.sh --vider`.

## Les outils de cette démonstration

| Outil | Rôle |
| --- | --- |
| [`preparer.sh`](preparer.sh) | Vérifie que tout est prêt (Docker, cluster, `smoke.sh`, Grafana, Keycloak, Locust, Playwright, HPA, pods, CI de `main`, catalogue propre) sans rien modifier ; `--rapide` saute `smoke.sh`, `--veille [heures]` empêche la mise en veille |
| [`donnees-demo.sh`](donnees-demo.sh) | Crée le jeu de données propre par l'API (vrai flux de connexion PKCE), sans doublon si relancé |
| [`mot-de-passe.sh`](mot-de-passe.sh) | Copie un mot de passe de démo dans le presse-papiers sans l'afficher, puis le vide |
| [`pic-charge.sh`](pic-charge.sh) | Pic de charge, suivi à l'écran, suppression d'un pod, bilan (moins de 2 minutes) enregistré dans `resultats/pic-<date>.txt` |
