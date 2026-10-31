# Plan de formation : Kubernetes et Helm pour l'équipe Collector

Ce document répond à la consigne 1.1.3 (critère 9) : il détaille l'action de formation qui réduit l'écart n° 2 de [matrice.md](matrice.md) (section 4). Il suppose que le lecteur a lu cette matrice : les niveaux 0 à 4 et leur définition sont ceux de la section 1.

Les exercices portent sur les livrables prévus du POC (cluster k3d, chart Helm générique, `deploy/local/deploy.sh`, kube-prometheus-stack). **Ces livrables n'existent pas encore** : ils sont produits en phase 6. Chaque exercice est donc formulé comme une tâche à réaliser sur le livrable au moment où il est écrit.

## 1. Intitulé, écart ciblé, niveaux

**Intitulé** : « Déployer, exploiter et relire une application sur Kubernetes avec Helm » (Collector.shop, cluster k3d local, chart Helm générique).

**Écart ciblé** : écart n° 2 de la section 4 de la matrice, « Kubernetes et Helm », requis 3, maximum de l'équipe 1, criticité haute. C'est l'écart que la matrice désigne pour la formation (section 4, « Écart ciblé par l'action de formation »). Les écarts connexes de cette ligne (observabilité, exploitation de PostgreSQL) sont traités par le recrutement du DevOps/SRE ; l'action n'utilise Prometheus et Grafana que comme outils de diagnostic (module 6) et ne revendique aucun changement de niveau sur ces deux compétences.

**Niveaux de départ**, lus dans les lignes « Orchestration » de la section 3 de la matrice :

| Ligne de la matrice | Requis | Lead Dev | Dev 1 | Dev 2 |
| --- | --- | --- | --- | --- |
| Kubernetes : k3d, déploiement, sondes, HPA, ingress Traefik, TLS (mkcert) | 3 | 1 | 1 | 0 |
| Helm : chart, values, secrets | 3 | 1 | 0 | 0 |

**Niveaux visés.**

| Participant | Kubernetes : départ, fin de formation, après pratique | Helm : départ, fin de formation, après pratique |
| --- | --- | --- |
| Lead Dev (participant prioritaire) | 1, puis 2, puis 3 | 1, puis 2, puis 3 |
| Dev 1 | 1, puis 2 | 0, puis 1 |
| Dev 2 | 0, puis 1 | 0, puis 1 |

- Le **niveau 3 du Lead Dev** est celui de la section 6 de la matrice (« Formation du Lead Dev (3) »). Il s'atteint en **deux temps** : niveau 2 à la fin de la formation, niveau 3 après une **période de pratique encadrée de 3 mois** (section 9). Passer de 1 à 3 en quelques semaines n'est pas crédible (décision D6 de P2-05) : la définition du niveau 3 exige de diagnostiquer une panne, d'arbitrer et de former, ce qui demande des situations réelles.
- Les niveaux de Dev 1 et de Dev 2 sont des objectifs propres à cette action. La matrice cible ne les compte pas : elle ne retient que le Lead Dev et le DevOps. Ils servent à réduire la dépendance à une seule personne.

## 2. Public, prérequis, effectif

- **Public** : les trois membres de l'équipe IT (Lead Dev, Dev 1, Dev 2). Le Lead Dev suit la formation en priorité, car il supervise le déploiement et doit défendre le cluster à l'oral comme en production.
- **Effectif** : 3 personnes, un groupe assez petit pour que chacun manipule le cluster.
- **Prérequis** : savoir utiliser Docker (construire et lancer une image), lire du YAML, utiliser un terminal, comprendre les notions de HTTP et de certificat TLS.

**Auto-diagnostic** (à remplir avant la formation, 10 minutes). Répondre oui ou non.

1. Je sais écrire un Dockerfile et construire une image.
2. Je sais lancer un conteneur avec une variable d'environnement et un port publié.
3. Je sais lire un fichier YAML avec des listes et des blocs imbriqués.
4. Je sais dire à quoi sert un certificat TLS et ce qu'est une autorité de certification.
5. Je sais lire les logs d'un conteneur (`docker logs`).
6. Je sais utiliser `git` (branche, commit, diff).

Seuil : 5 oui sur 6. En dessous, un pré-travail de 2 heures au plus est fourni (documentation officielle de Docker et du format YAML). Ces 2 heures ne sont pas comptées dans la durée de la formation, mais le sont dans le budget (section 8).

## 3. Objectifs pédagogiques

À la fin de la formation, le participant sait, dans le cadre du POC Collector, faire ce qui suit. Chaque objectif est évalué à la section 7 (niveau 2 de Kirkpatrick).

| N° | Objectif (verbe observable) | Module |
| --- | --- | --- |
| O1 | **Expliquer** le rôle des composants d'un cluster k3d (server, agents, API, planificateur, kubelet) et **décrire** le trajet d'une requête de l'ingress jusqu'au pod | M1 |
| O2 | **Déployer** un service conteneurisé avec un Deployment, un Service, une ConfigMap, un Secret, des sondes et des limites de ressources | M2 |
| O3 | **Configurer** une route Traefik en HTTPS avec un certificat mkcert chargé comme Secret TLS | M3 |
| O4 | **Écrire** un chart Helm générique et **déployer** deux services différents avec deux fichiers de values | M4 |
| O5 | **Relire** un chart et **repérer** les défauts courants (absence de sonde ou de limites, secret en clair, tag `latest`) | M4 |
| O6 | **Configurer** un HPA et **vérifier** la montée de 2 à 5 réplicas sous charge | M5 |
| O7 | **Diagnostiquer** trois pannes courantes (image introuvable, sonde en échec, redémarrages en boucle) avec `kubectl` et Grafana, puis **restaurer** le service avec `helm rollback` | M5, M6 |

Le niveau 2 de la matrice décrit quelqu'un qui réalise seul une tâche courante déjà vue et demande de l'aide pour les cas inhabituels. O7 est donc limité aux pannes étudiées en formation. Le diagnostic de pannes inconnues relève du niveau 3, obtenu par la pratique.

## 4. Format et modalités

**Choix : format mixte, intra-entreprise.** L'animation des modules M1 à M4 par un formateur externe, la pratique de M5 et M6 en autonomie guidée sur le repo du POC.

| Option | Avis |
| --- | --- |
| Formation interne par un pair | Écartée : le meilleur niveau de l'équipe est 1 (matrice, section 3). Personne ne peut former, et la matrice rappelle qu'un niveau 3 « peut former » |
| Formation externe seule, sur un cas générique | Écartée : les exemples ne seraient pas ceux du POC, et le Lead Dev devrait ensuite transposer seul |
| **Mixte : formateur externe, exercices sur le repo du POC** | Retenue : l'apport d'expertise vient de l'extérieur, la pratique porte sur les livrables que le Lead Dev devra défendre à la soutenance |

- **Lieu** : présentiel chez Collector pour les modules animés (M1 à M4), distanciel possible pour M5 et M6, qui se font sur le Mac de chacun.
- **Part de pratique** : au moins 70 % de la durée, sous forme d'exercices sur le cluster k3d et sur le chart.
- **Animateur** : un formateur externe indépendant ou un organisme de formation, choisi sur devis. Aucun organisme n'est désigné dans ce document et aucun partenariat n'est supposé.
- **Reproductibilité** : chaque exercice se lance par script (`deploy/local/check-tools.sh`, `deploy/local/deploy.sh` ou une commande documentée dans le module), conformément à la convention du projet.

**Certification CKAD (option).** La CKAD (Certified Kubernetes Application Developer) est une certification de la CNCF centrée sur le travail d'un développeur d'applications sur Kubernetes. Elle est proposée comme **option pour le Lead Dev seul**, après la période de pratique encadrée.

- Justification : elle valide de façon externe le niveau 3 et rassure un recruteur ou un client. Elle est plus proche du rôle du Lead Dev (déployer et configurer des applications) que la certification d'administrateur.
- Elle n'est pas nécessaire à l'objectif de la formation. La décision est reportée à la fin de la période de pratique, en fonction de la charge du projet.
- Le format, la durée, le prix et le programme de l'examen évoluent : ils sont à vérifier sur le site de la CNCF avant toute inscription. Aucune de ces données n'est reprise ici ; le budget (section 8) ne contient que la préparation, en jours-homme.

## 5. Programme détaillé

Durée totale : **28 heures** (4 jours de 7 heures). Six modules.

| Module | Durée | Contenu | Exercice sur le repo du POC | Livrable |
| --- | --- | --- | --- | --- |
| M1. Architecture Kubernetes et cluster k3d | 4 h | Pods, ReplicaSets, nœuds, API, planificateur, kubelet ; création d'un cluster k3d (1 server, 2 agents) ; lecture de `kubectl get`, `describe`, `logs` | Créer le cluster local avec le script de `deploy/local` et décrire le trajet d'une requête de l'ingress au pod du `catalog-service` | Schéma annoté du cluster et réponses à 5 questions de cours (O1) |
| M2. Déployer un service | 5 h | Deployment, Service, ConfigMap, Secret, sondes liveness et readiness, requêtes et limites de ressources, stratégie de mise à jour | Écrire à la main les manifestes du `catalog-service` : 2 réplicas, sondes `/health/live` et `/health/ready`, variables d'environnement, Secret pour les identifiants PostgreSQL | Manifestes du `catalog-service` appliqués avec `kubectl apply`, déploiement vérifié par `kubectl rollout status` (O2) |
| M3. Ingress Traefik et TLS | 3 h | Ingress, IngressRoute de Traefik, Secret TLS, certificat mkcert, hôtes `*.127.0.0.1.sslip.io` | Exposer le `catalog-service` sur l'hôte `api.127.0.0.1.sslip.io` en HTTPS avec le certificat mkcert chargé comme Secret | Route HTTPS fonctionnelle, vérifiée par `curl` sur `/health/ready` (O3) |
| M4. Helm : écrire et relire un chart | 6 h | Structure d'un chart, templates, `values.yaml`, helpers, `helm lint`, `helm template`, gestion des secrets, relecture d'un chart | Transformer les manifestes de M2 en chart générique pour les deux services (`catalog-service`, `notification-service`) ; relire un chart fourni contenant des défauts volontaires | Chart générique dans `deploy/helm`, deux fichiers de values, fiche de relecture avec les défauts repérés (O4, O5) |
| M5. Montée en charge et disponibilité | 5 h | HPA, metrics-server, rolling update, suppression d'un pod, `helm history` et `helm rollback` | Ajouter le HPA (2 à 5 réplicas) au chart, lancer un scénario Locust minimal et observer la montée ; supprimer un pod pendant la charge ; faire un `helm rollback` après une mauvaise version | Rapport d'une page avec relevé du nombre de réplicas et du taux d'erreur, tel qu'on le montrera à la démo de disponibilité (O6, O7) |
| M6. Diagnostic et observabilité de base | 5 h | `kubectl describe`, `events`, `logs`, tableau de bord Grafana (débit, latence p95, taux d'erreur), lecture des logs JSON corrélés par `X-Request-ID`, trois pannes types | Diagnostiquer trois pannes préparées sur le chart (image introuvable, sonde de disponibilité en échec, redémarrages en boucle) et restaurer le service ; passage de l'évaluation finale | Fiche de diagnostic par panne (symptôme, commande, cause, correction) et résultat de l'évaluation finale (O7) |

Vérification : 4 + 5 + 3 + 6 + 5 + 5 = **28 heures**.

Le scénario Locust de M5 est volontairement minimal. Le scénario complet, qui sert à l'indicateur I3 de [indicateurs.md](../01-qualite/indicateurs.md), est un livrable de la phase 8.

## 6. Planning

- **Durée** : 28 heures de formation réparties sur **6 semaines**, un module par semaine, soit au plus 6 heures par semaine pour chaque participant. Un module de plus de 4 heures est coupé en deux demi-journées.
- **Date** : au **début de la phase 6** du plan (déploiement sur le cluster local), après la mise en place des workflows de la phase 5. M1 à M3 précèdent l'écriture des manifestes et du chart de la phase 6 ; M4 à M6 accompagnent l'écriture et le test du chart, qui s'enrichit au fil des modules. Les exercices des modules deviennent ainsi le travail de la phase.
- **Compatibilité avec les sprints** : une charge de 6 heures au plus par semaine laisse l'essentiel du temps aux sprints. Les sessions animées sont placées en début de semaine, hors des jours de revue de sprint.
- **Après la formation** : période de pratique encadrée de **3 mois** (estimation) pour le Lead Dev, qui démarre à la fin de M6 (section 9).

| Semaine | Module | Durée |
| --- | --- | --- |
| 1 | M1 | 4 h |
| 2 | M2 | 5 h |
| 3 | M3 | 3 h |
| 4 | M4 | 6 h |
| 5 | M5 | 5 h |
| 6 | M6 | 5 h |
| Total | | 28 h |

## 7. Évaluation (modèle de Kirkpatrick)

### Niveau 1. Réaction

- **Indicateur** : note moyenne de satisfaction sur 5 (clarté, rythme, utilité pour le projet) et nombre de points signalés comme « inutiles ».
- **Moment** : questionnaire de 5 questions à la fin de chaque module.
- **Cible** : moyenne supérieure ou égale à 4 sur 5. En dessous, le programme du module est ajusté avant le suivant.

### Niveau 2. Apprentissage

Chaque objectif est évalué par une épreuve pratique ou un test, à un moment précis. L'évaluation finale a lieu à la fin de M6, sur le cluster, sans aide du formateur, avec la documentation officielle.

| Objectif | Épreuve | Moment | Réussi si |
| --- | --- | --- | --- |
| O1 Expliquer l'architecture et le trajet d'une requête | 5 questions orales ou écrites sur un schéma vierge du cluster | Fin de M1 | 4 réponses justes sur 5 |
| O2 Déployer un service avec sondes, Secret et limites | Déployer un service non vu en cours à partir d'une consigne | Fin de M2 | `kubectl rollout status` réussi, sondes et limites présentes |
| O3 Configurer une route HTTPS | Exposer le second service sur un nouvel hôte en HTTPS | Fin de M3 | `curl` en HTTPS sans erreur de certificat |
| O4 Écrire un chart et déployer deux services | Ajouter un troisième jeu de values au chart et déployer | Fin de M4 | `helm lint` sans erreur, déploiement réussi |
| O5 Relire un chart et repérer les défauts | Fiche de relecture d'un chart contenant 6 défauts volontaires | Fin de M4 | Au moins 5 défauts sur 6 repérés |
| O6 Configurer un HPA et vérifier la montée | Rejouer la charge et relever le nombre de réplicas | Fin de M5 | Passage de 2 à 5 réplicas observé et relevé |
| O7 Diagnostiquer trois pannes et restaurer | Évaluation finale : trois pannes préparées, une par type | Fin de M6 | 3 pannes sur 3 diagnostiquées avec la bonne commande, 2 sur 3 corrigées sans aide, service restauré par `helm rollback` pour au moins une |

**Seuil de passage au niveau 2** : tous les objectifs O1 à O7 réussis, ce qui est l'exigence pour le Lead Dev. Pour les deux autres participants, les niveaux visés sont plus bas (section 1) : Kubernetes niveau 1 (Dev 2) exige O1 et O2 ; Kubernetes niveau 2 (Dev 1) exige O1, O2, O3 et O6 ; Helm niveau 1 (Dev 1 et Dev 2) exige O4 réalisé en suivant l'exemple fourni. Un objectif non réussi donne lieu à un exercice de rattrapage dans le mois.

### Niveau 3. Comportement

- **Indicateur** : grille d'observation de 5 comportements sur le projet : le Lead Dev déploie seul une nouvelle version avec `deploy.sh`, relit un chart dans une pull request, diagnostique un incident sans demander d'aide, arbitre un choix (ressources, nombre de réplicas), forme un pair pendant 1 heure. Chaque comportement est coté « fait / pas fait ».
- **Moment** : à 1 mois et à 3 mois après la fin de M6. L'observateur est le formateur externe en revue de chart pour le premier relevé, puis le DevOps/SRE dès son arrivée.
- **Cible** : 3 comportements sur 5 à 1 mois, 5 sur 5 à 3 mois.

### Niveau 4. Résultats

- **Indicateurs reliés au projet** :
  1. Durée d'un déploiement de bout en bout (du tag `sha-<7 caractères>` à `rollout status` réussi), mesurée sur un déploiement fait par un membre de l'équipe autre que le Lead Dev.
  2. Taux de déploiements ayant exigé un `helm rollback`, calculé sur les déploiements de la phase.
  3. Niveau de Kubernetes et de Helm du Lead Dev dans la matrice : passage de 1 à 3.
- **Moment** : mesures 1 et 2 à chaque déploiement, relevées dans le compte rendu de déploiement ; mesure 3 à la fin des 3 mois de pratique.
- **Cible** : la valeur de départ est relevée au premier déploiement de la phase 6 ; l'objectif est de la diminuer à chaque déploiement suivant. Le niveau 3 est validé quand les 5 comportements du niveau 3 sont observés.

## 8. Budget estimatif

Toutes les valeurs sont des **estimations**, à confirmer par devis. Le coût interne n'est pas valorisé en euros : les salaires ne sont pas connus.

**Jours-homme internes** (1 jour = 7 heures).

| Poste | Calcul | Estimation |
| --- | --- | --- |
| Formation | 3 participants × 4 jours | 12 j-h |
| Pré-travail éventuel | 3 participants × 2 h au plus | 1 j-h |
| Préparation de l'environnement et des pannes par le Lead Dev | Estimation | 1 j-h |
| Pratique encadrée du Lead Dev | Environ 10 % de son temps sur 3 mois (environ 60 jours ouvrés) | 6 j-h |
| **Total sans certification** | | **20 j-h** |
| Option CKAD : préparation du Lead Dev | Estimation | 5 j-h |
| **Total avec l'option** | | **25 j-h** |

**Coût externe.**

| Poste | Hypothèse | Estimation |
| --- | --- | --- |
| Formateur externe, M1 à M4 (18 h, soit environ 3 jours avec la préparation) | De 1 200 à 1 800 € par jour (hypothèse de tarif d'un formateur indépendant) | 3 600 à 5 400 € |
| Revues de chart du formateur pendant la période de pratique | 1 jour, même hypothèse de tarif | 1 200 à 1 800 € |
| **Total externe** | | **de 4 800 à 7 200 €** |
| Option CKAD : frais d'examen | À vérifier sur le site de la CNCF | non chiffré ici |

**Financement.** Le coût externe peut être pris en charge en tout ou partie par l'OPCO de l'entreprise ou imputé sur son plan de développement des compétences, sous réserve de l'accord de l'OPCO.

## 9. Suivi après la formation

- **Mise à jour de la matrice** : à la fin de M6, les niveaux de Kubernetes et de Helm sont mis à jour dans `matrice.md` d'après les résultats de l'évaluation finale (niveau 2 pour le Lead Dev). À la fin de la période de pratique, la matrice est mise à jour une seconde fois (niveau 3 si les 5 comportements du niveau 3 sont observés). La matrice cible (section 6) suppose ce niveau 3.
- **Période de pratique encadrée du Lead Dev (3 mois, estimation)**, avec trois dispositifs.
  - **Binôme** : chaque évolution du chart est écrite avec Dev 1 ou revue par lui, ce qui lui permet de monter à son tour.
  - **Revue des charts** : chaque modification de `deploy/helm` passe par une pull request relue, d'abord par le formateur (1 jour de revue prévu au budget), puis par le DevOps/SRE à son arrivée.
  - **Astreinte accompagnée** : lors des tests de charge et de la démonstration de disponibilité, le Lead Dev est de permanence sur les incidents préparés, un pair l'accompagne.
- **Dépendance** : le DevOps/SRE est recruté après le POC (matrice, section 5.1). Si son arrivée dépasse les 3 mois, la revue externe prévue au budget assure l'encadrement, et la période est prolongée au besoin.
- **Capitalisation** : les fiches de diagnostic de M6, la fiche de relecture de chart de M4 et le rapport de M5 sont conservés dans le dépôt, sous `docs/04-experimentations` ou `deploy/README.md`, pour servir de documentation interne et d'aide à l'arrivée d'une nouvelle personne.
- **Transmission** : le Lead Dev anime une séance d'une heure pour Dev 2 à partir de ses fiches, ce qui compte comme comportement du niveau 3 (« forme les autres »).

## 10. Autres actions envisagées

Ces actions ne sont pas détaillées ici.

- **Keycloak** (realm, rôles, fédération) : montée en compétence par la pratique, avec l'appui du DevOps.
- **Sécurité applicative** : sensibilisation OWASP de l'équipe, en complément du recrutement et du test d'intrusion externe de l'écart n° 1.
- **Tests de bout en bout** (Playwright) : atelier pour Dev 1 et le Lead Dev, avec le QA à son arrivée.
- **WebSocket** pour le chat : binôme entre Dev 1 et Dev 2, avec revue du Lead Dev.
