# Questions probables du jury

Banque de questions pour les 15 minutes d'échange. Chaque réponse est faite pour être **dite** : 3 à 5 phrases courtes, vocabulaire exact, sans promettre ce que le POC ne fait pas. Chaque question donne aussi les **chiffres** utiles avec leur source, le **document à montrer** si le jury insiste, et, quand il y en a une, la **limite à reconnaître** avec l'action du plan qui la traite. Le vocabulaire est défini dans le [glossaire](glossaire.md).

Les chiffres viennent de fichiers du dépôt, cités en lien relatif ; `python3 -I docs/07-soutenance/verifier-guide.py` contrôle que les liens, les ancres et les chiffres de cette page existent dans leur source.

**Règles de réponse**

1. **Répondre d'abord, nuancer ensuite.** Une phrase qui répond (« Non, ce n'est pas un environnement managé au sens strict »), puis le pourquoi, puis le chiffre.
2. **Une limite dite par soi-même vaut mieux qu'une limite trouvée par le jury.** Chaque limite ci-dessous a un numéro (L1 à L25 dans l'[architecture du POC](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc)) et, presque toujours, une action du [plan de remédiation](../06-securite/plan-remediation.md) (PA-01 à PA-58).
3. **« Je ne l'ai pas mesuré » est une réponse acceptable** quand c'est vrai, à condition de dire ce qui est mesuré et ce qui ne l'est pas.
4. **Montrer le document, pas le chercher.** Les liens « À montrer » pointent vers le bon fichier ; le [support](support.md) a six annexes (A1 à A6) prévues pour les questions.

## Index des questions

| Question | Section |
| --- | --- |
| [Q1. Qu'est-ce qui distingue vos protocoles d'un guide d'installation ?](#q1-quest-ce-qui-distingue-vos-protocoles-dun-guide-dinstallation-) | Critère 1 — Fiabilité du protocole d'expérimentation |
| [Q2. Donnez un exemple où une expérimentation a changé une décision.](#q2-donnez-un-exemple-où-une-expérimentation-a-changé-une-décision) | Critère 1 — Fiabilité du protocole d'expérimentation |
| [Q3. Vos mesures sont-elles reproductibles et fiables ?](#q3-vos-mesures-sont-elles-reproductibles-et-fiables-) | Critère 1 — Fiabilité du protocole d'expérimentation |
| [Q4. Pourquoi n'avez-vous pas expérimenté Kafka ?](#q4-pourquoi-navez-vous-pas-expérimenté-kafka-) | Critère 1 — Fiabilité du protocole d'expérimentation |
| [Q5. Quelle difficulté vous a le plus appris ?](#q5-quelle-difficulté-vous-a-le-plus-appris-) | Critère 1 — Fiabilité du protocole d'expérimentation |
| [Q6. Comment les deux services communiquent-ils, et que se passe-t-il si `notification-service` tombe ?](#q6-comment-les-deux-services-communiquent-ils-et-que-se-passe-t-il-si-notification-service-tombe-) | Critère 2 — Qualité technique du prototype |
| [Q7. Que se passe-t-il si RabbitMQ est indisponible au moment de la publication ?](#q7-que-se-passe-t-il-si-rabbitmq-est-indisponible-au-moment-de-la-publication-) | Critère 2 — Qualité technique du prototype |
| [Q8. Pourquoi la sonde `/health/ready` ne teste-t-elle pas RabbitMQ ?](#q8-pourquoi-la-sonde-healthready-ne-teste-t-elle-pas-rabbitmq-) | Critère 2 — Qualité technique du prototype |
| [Q9. Où est la preuve que le POC se déploie depuis rien, et en combien de temps ?](#q9-où-est-la-preuve-que-le-poc-se-déploie-depuis-rien-et-en-combien-de-temps-) | Critère 2 — Qualité technique du prototype |
| [Q10. Pourquoi une seule instance PostgreSQL pour les deux services ?](#q10-pourquoi-une-seule-instance-postgresql-pour-les-deux-services-) | Critère 2 — Qualité technique du prototype |
| [Q11. Comment le contrôle automatique détecte-t-il un téléphone ou un email, et comment le contourner ?](#q11-comment-le-contrôle-automatique-détecte-t-il-un-téléphone-ou-un-email-et-comment-le-contourner-) | Critère 3 — Fonctionnalité métier |
| [Q12. Pourquoi le contrôle est-il synchrone et la notification asynchrone ? En combien de temps l'acheteur est-il prévenu ?](#q12-pourquoi-le-contrôle-est-il-synchrone-et-la-notification-asynchrone--en-combien-de-temps-lacheteur-est-il-prévenu-) | Critère 3 — Fonctionnalité métier |
| [Q13. Comment évitez-vous les notifications en double ?](#q13-comment-évitez-vous-les-notifications-en-double-) | Critère 3 — Fonctionnalité métier |
| [Q14. Le contexte demande de la détection de fraude. Qu'avez-vous fait ?](#q14-le-contexte-demande-de-la-détection-de-fraude-quavez-vous-fait-) | Critère 3 — Fonctionnalité métier |
| [Q15. Le POC répond-il au besoin du contexte ? Qu'est-ce qui est hors périmètre ?](#q15-le-poc-répond-il-au-besoin-du-contexte--quest-ce-qui-est-hors-périmètre-) | Critère 3 — Fonctionnalité métier |
| [Q16. Comment prouvez-vous que le pipeline réel est conforme au schéma, et qu'il bloque vraiment ?](#q16-comment-prouvez-vous-que-le-pipeline-réel-est-conforme-au-schéma-et-quil-bloque-vraiment-) | Critère 4 — Conformité du processus CI/CD |
| [Q17. Pourquoi `sonar` ne tourne-t-il que sur `main` et les pull requests ?](#q17-pourquoi-sonar-ne-tourne-t-il-que-sur-main-et-les-pull-requests-) | Critère 4 — Conformité du processus CI/CD |
| [Q18. Qu'est-ce qu'un digest, et comment remonte-t-on du pod au commit ?](#q18-quest-ce-quun-digest-et-comment-remonte-t-on-du-pod-au-commit-) | Critère 4 — Conformité du processus CI/CD |
| [Q19. Pourquoi Trivy en binaire vérifié et les actions épinglées par SHA ?](#q19-pourquoi-trivy-en-binaire-vérifié-et-les-actions-épinglées-par-sha-) | Critère 4 — Conformité du processus CI/CD |
| [Q20. Un cluster k3d local est-il un « environnement managé » ?](#q20-un-cluster-k3d-local-est-il-un--environnement-managé--) | Critère 5 — Validation de l'environnement d'exécution |
| [Q21. Comment fonctionne l'HPA, et pourquoi redescend-il lentement ?](#q21-comment-fonctionne-lhpa-et-pourquoi-redescend-il-lentement-) | Critère 5 — Validation de l'environnement d'exécution |
| [Q22. Que se passe-t-il si un nœud tombe ?](#q22-que-se-passe-t-il-si-un-nœud-tombe-) | Critère 5 — Validation de l'environnement d'exécution |
| [Q23. Pourquoi 300 utilisateurs en direct et 200 dans le protocole ?](#q23-pourquoi-300-utilisateurs-en-direct-et-200-dans-le-protocole-) | Critère 5 — Validation de l'environnement d'exécution |
| [Q24. Vos résultats de charge sont-ils transposables en production ?](#q24-vos-résultats-de-charge-sont-ils-transposables-en-production-) | Critère 5 — Validation de l'environnement d'exécution |
| [Q25. Pourquoi ces cinq indicateurs ?](#q25-pourquoi-ces-cinq-indicateurs-) | Critère 6 — Indicateurs de qualité |
| [Q26. Tout est dans les seuils : où est la dette technique ?](#q26-tout-est-dans-les-seuils--où-est-la-dette-technique-) | Critère 6 — Indicateurs de qualité |
| [Q27. La couverture à 98 % suffit-elle ? Le seuil de 80 % n'est-il pas trop bas ?](#q27-la-couverture-à-98--suffit-elle--le-seuil-de-80--nest-il-pas-trop-bas-) | Critère 6 — Indicateurs de qualité |
| [Q28. Pourquoi le p95 et pas la moyenne ?](#q28-pourquoi-le-p95-et-pas-la-moyenne-) | Critère 6 — Indicateurs de qualité |
| [Q29. Quels types de tests avez-vous, et lesquels sont hors CI ?](#q29-quels-types-de-tests-avez-vous-et-lesquels-sont-hors-ci-) | Critère 7 — Processus de test |
| [Q30. Pourquoi les tests d'acceptation tournent-ils sur `docker compose` et pas sur le cluster ?](#q30-pourquoi-les-tests-dacceptation-tournent-ils-sur-docker-compose-et-pas-sur-le-cluster-) | Critère 7 — Processus de test |
| [Q31. Comment testez-vous la sécurité des routes sans Keycloak dans les tests ?](#q31-comment-testez-vous-la-sécurité-des-routes-sans-keycloak-dans-les-tests-) | Critère 7 — Processus de test |
| [Q32. Que faites-vous d'un test intermittent ou d'une anomalie ?](#q32-que-faites-vous-dun-test-intermittent-ou-dune-anomalie-) | Critère 7 — Processus de test |
| [Q33. Comment fonctionne PKCE, et que protège-t-il ?](#q33-comment-fonctionne-pkce-et-que-protège-t-il-) | Critère 8 — Remédiation des risques de sécurité |
| [Q34. Pourquoi des jetons en mémoire, et que se passe-t-il en cas de XSS ?](#q34-pourquoi-des-jetons-en-mémoire-et-que-se-passe-t-il-en-cas-de-xss-) | Critère 8 — Remédiation des risques de sécurité |
| [Q35. Comment un service vérifie-t-il un JWT, et pourquoi deux URL de Keycloak ?](#q35-comment-un-service-vérifie-t-il-un-jwt-et-pourquoi-deux-url-de-keycloak-) | Critère 8 — Remédiation des risques de sécurité |
| [Q36. Qu'apporte STRIDE ?](#q36-quapporte-stride-) | Critère 8 — Remédiation des risques de sécurité |
| [Q37. Comment les risques sont-ils priorisés ?](#q37-comment-les-risques-sont-ils-priorisés-) | Critère 8 — Remédiation des risques de sécurité |
| [Q38. Que fait Trivy, et que se passe-t-il si une image vulnérable est publiée ?](#q38-que-fait-trivy-et-que-se-passe-t-il-si-une-image-vulnérable-est-publiée-) | Critère 8 — Remédiation des risques de sécurité |
| [Q39. Où sont les secrets ?](#q39-où-sont-les-secrets-) | Critère 8 — Remédiation des risques de sécurité |
| [Q40. Et l'authentification multifacteur ?](#q40-et-lauthentification-multifacteur-) | Critère 8 — Remédiation des risques de sécurité |
| [Q41. Qu'a donné l'audit OWASP ZAP ?](#q41-qua-donné-laudit-owasp-zap-) | Critère 8 — Remédiation des risques de sécurité |
| [Q42. Comment bâtir un plan pour tout le SI alors que l'état de l'existant est inconnu ?](#q42-comment-bâtir-un-plan-pour-tout-le-si-alors-que-létat-de-lexistant-est-inconnu-) | Critère 8 — Remédiation des risques de sécurité |
| [Q43. Pourquoi former sur Kubernetes et Helm plutôt que sur autre chose ?](#q43-pourquoi-former-sur-kubernetes-et-helm-plutôt-que-sur-autre-chose-) | Critère 9 — Gestion des compétences |
| [Q44. Pourquoi trois recrutements, et pas un profil qui fait tout ?](#q44-pourquoi-trois-recrutements-et-pas-un-profil-qui-fait-tout-) | Critère 9 — Gestion des compétences |
| [Q45. Comment saurez-vous que la formation a fonctionné ?](#q45-comment-saurez-vous-que-la-formation-a-fonctionné-) | Critère 9 — Gestion des compétences |
| [Q46. Les niveaux de vos deux développeurs sont-ils réels ?](#q46-les-niveaux-de-vos-deux-développeurs-sont-ils-réels-) | Critère 9 — Gestion des compétences |
| [Q47. Quel message faut-il retenir ?](#q47-quel-message-faut-il-retenir-) | Critère 10 — Qualité de la présentation |
| [Q48. Si vous aviez deux semaines de plus, que feriez-vous en premier ?](#q48-si-vous-aviez-deux-semaines-de-plus-que-feriez-vous-en-premier-) | Critère 10 — Qualité de la présentation |
| [Q49. Pourquoi RabbitMQ et pas Kafka ?](#q49-pourquoi-rabbitmq-et-pas-kafka-) | Thème — Choix techniques |
| [Q50. Pourquoi deux services, ni un monolithe ni davantage ?](#q50-pourquoi-deux-services-ni-un-monolithe-ni-davantage-) | Thème — Choix techniques |
| [Q51. Pourquoi FastAPI ?](#q51-pourquoi-fastapi-) | Thème — Choix techniques |
| [Q52. Pourquoi k3d plutôt qu'un cloud ?](#q52-pourquoi-k3d-plutôt-quun-cloud-) | Thème — Choix techniques |
| [Q53. Pourquoi Keycloak ?](#q53-pourquoi-keycloak-) | Thème — Choix techniques |
| [Q54. Pourquoi pas d'outbox ?](#q54-pourquoi-pas-doutbox-) | Thème — Choix techniques |
| [Q55. Pourquoi Helm avec un script de déploiement, sans Argo CD ?](#q55-pourquoi-helm-avec-un-script-de-déploiement-sans-argo-cd-) | Thème — Choix techniques |
| [Q56. Pourquoi avoir abandonné les opérateurs ?](#q56-pourquoi-avoir-abandonné-les-opérateurs-) | Thème — Choix techniques |
| [Q57. Pourquoi React et TypeScript alors que vous êtes plutôt Python ?](#q57-pourquoi-react-et-typescript-alors-que-vous-êtes-plutôt-python-) | Thème — Choix techniques |
| [Q58. Pourquoi Traefik et pas ingress-nginx ?](#q58-pourquoi-traefik-et-pas-ingress-nginx-) | Thème — Choix techniques |
| [Q59. Pourquoi avoir simplifié le POC ?](#q59-pourquoi-avoir-simplifié-le-poc-) | Thème — Choix techniques |
| [Q60. Quelles sont les limites les plus graves du POC ?](#q60-quelles-sont-les-limites-les-plus-graves-du-poc-) | Thème — Limites |
| [Q61. Ce POC est-il prêt pour la production ?](#q61-ce-poc-est-il-prêt-pour-la-production-) | Thème — Limites |
| [Q62. Pourquoi l'accessibilité et l'internationalisation sont-elles absentes ?](#q62-pourquoi-laccessibilité-et-linternationalisation-sont-elles-absentes-) | Thème — Limites |
| [Q63. Quel est votre rôle de Lead Developer, concrètement ?](#q63-quel-est-votre-rôle-de-lead-developer-concrètement-) | Thème — Organisation de l'équipe |
| [Q64. Comment travaillez-vous avec les deux développeurs, et comment garantissez-vous la qualité d'une fusion ?](#q64-comment-travaillez-vous-avec-les-deux-développeurs-et-comment-garantissez-vous-la-qualité-dune-fusion-) | Thème — Organisation de l'équipe |
| [Q65. Et si la démonstration plante ?](#q65-et-si-la-démonstration-plante-) | Thème — Si la démonstration échoue |
| [Q66. Et si GitHub ou le réseau est inaccessible ?](#q66-et-si-github-ou-le-réseau-est-inaccessible-) | Thème — Si la démonstration échoue |
| [Q67. Et si le pic n'atteint pas 5 réplicas, ou si une requête échoue pendant la suppression du pod ?](#q67-et-si-le-pic-natteint-pas-5-réplicas-ou-si-une-requête-échoue-pendant-la-suppression-du-pod-) | Thème — Si la démonstration échoue |
| [Q68. Et si le déploiement échoue pendant la démonstration ?](#q68-et-si-le-déploiement-échoue-pendant-la-démonstration-) | Thème — Si la démonstration échoue |


## Critère 1 — Fiabilité du protocole d'expérimentation

### Q1. Qu'est-ce qui distingue vos protocoles d'un guide d'installation ?

**Critères** : 1.

**À dire.** Chaque protocole pose une question à laquelle l'expérience répond par oui ou non, puis suit huit rubriques : la question, les technologies et leurs interactions, l'environnement avec les versions exactes, les étapes (une seule commande, `run.sh`), les résultats mesurés, les difficultés, les limites et la décision. Un guide d'installation s'arrête à « ça démarre ». Ici, chaque protocole finit par une décision, reprise dans une ADR : par exemple l'abandon des opérateurs dans l'ADR 0008. Tout se rejoue sur un cluster jetable.

**Chiffres.** Cinq protocoles exécutés (trois technologies, le déploiement du POC, la charge et la disponibilité) ; une sixième ligne, Kafka, est marquée « non réalisée » ([index des expérimentations](../04-experimentations/README.md)).

**À montrer.** [Modèle commun des protocoles](../04-experimentations/README.md#modèle-commun-des-protocoles) puis un protocole au choix, par exemple le [protocole 1](../04-experimentations/01-rabbitmq/protocole.md), section 5 (résultats) et section 8 (décision).

**Limite à reconnaître.** Une seule exécution de référence par expérience, sur un seul poste ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md), section Conséquences).

### Q2. Donnez un exemple où une expérimentation a changé une décision.

**Critères** : 1, 2.

**À dire.** Les opérateurs. Je les avais retenus d'abord, pour RabbitMQ, PostgreSQL et Keycloak, puis je les ai essayés et abandonnés le 3 novembre. L'opérateur RabbitMQ exige cert-manager, que j'avais écarté du POC, et celui de Keycloak 26.8.0 ne démarrait pas sans deux CRD manquantes. Surtout, la mesure est nette : le broker redevient prêt 10 secondes après la suppression de son pod sans opérateur, contre 54 avec, pour la même fiabilité, aucun message perdu sur 2 × 1 000.

**Chiffres.** 9,995 s sans opérateur contre 54,164 s avec ; 64 Mi de mémoire en moins ; 0 message perdu sur 2 × 1 000 ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md), protocole 1 sections 5 et 8).

**À montrer.** [ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md), section Décision ; [journal des décisions](../suivi/journal-decisions.md) des 02 et 03/11/2026.

**Limite à reconnaître.** Une exécution par version ; la cause du délai de 54 s n'est pas mesurée ([protocole 1](../04-experimentations/01-rabbitmq/protocole.md), section 7).

### Q3. Vos mesures sont-elles reproductibles et fiables ?

**Critères** : 1, 6.

**À dire.** Reproductibles, oui : versions figées, un script par protocole, un journal d'exécution versionné. Fiables au sens statistique, non, et je le dis. Chaque valeur vient d'une exécution de référence, sur le même Mac que le cluster, et la variabilité entre exécutions n'est pas mesurée. J'en ai la preuve : la première exécution de la charge (fiche P8-02) avait donné 21 ms en lecture et 28 ms en publication, la référence 21 et 23. Ce que je défends, c'est l'ordre de grandeur : un p95 de 21 ms face à un seuil de 300 ms.

**Chiffres.** p95 de 21 ms (lecture) et 23 ms (publication) à 50 utilisateurs, seuils de 300 et 500 ms ([indicateurs, relevé de la phase 8](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8) ; 28 ms : [fiche P8-02](../suivi/taches/P8-02.md)).

**À montrer.** [Limites de la mesure](../01-qualite/indicateurs.md#limites-de-la-mesure), puis l'axe d'amélioration d'I3.

**Limite à reconnaître.** Action prévue : répéter la mesure trois fois et lancer Locust depuis une autre machine ([axes d'amélioration](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique), ligne I3).

### Q4. Pourquoi n'avez-vous pas expérimenté Kafka ?

**Critères** : 1, 2.

**À dire.** Je l'ai décidé le 2 novembre : l'ADR 0003 le rejette déjà sur des critères écrits, trois protocoles couvraient déjà le critère et Kafka est lourd pour un Docker Desktop de 8 Go. Kafka est donc écarté sans essai, et la ligne 6 de l'index le dit. Le choix repose sur la documentation et sur une hypothèse de volume, quelques événements par seconde, que la direction doit encore confirmer. Si la relecture de l'historique devient nécessaire, par exemple pour l'analyse des ventes, Kafka reste envisagé dans la cible.

**Chiffres.** Hypothèse de dimensionnement : quelques milliers d'articles et de changements de prix par jour, soit quelques événements par seconde au pic ([ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md), contexte). Ordre de grandeur, pas une mesure.

**À montrer.** [Index des expérimentations](../04-experimentations/README.md), ligne 6 ; [ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md), section Avantages et inconvénients.

**Limite à reconnaître.** Kafka n'a pas été testé. Voir aussi la question [Q49](#q49-pourquoi-rabbitmq-et-pas-kafka-).

### Q5. Quelle difficulté vous a le plus appris ?

**Critères** : 1, 8.

**À dire.** Le broker qui ne redémarrait plus. Pour durcir RabbitMQ, j'avais posé un `fsGroup` : le cookie Erlang devenait lisible par le groupe, et le nœud refusait de démarrer à la recréation du pod, en `CrashLoopBackOff`. J'ai retiré le réglage. La conséquence, je l'assume : le broker tourne encore en root, c'est la limite L18. Autre leçon : Grafana était tué par manque de mémoire, je l'ai limité à 768 Mi. Et un premier scan de sécurité actif a saturé tout le cluster, je le raconte à la question sur ZAP.

**Chiffres.** Essai du 03/11/2026 18:41 ([protocole 1](../04-experimentations/01-rabbitmq/protocole.md), section 6).

**À montrer.** [Protocole 1, difficultés](../04-experimentations/01-rabbitmq/protocole.md) (section 6) et [protocole 5, difficultés](../04-experimentations/05-charge-disponibilite/protocole.md) (section 6).

**Limite à reconnaître.** L18 (broker en root) : action PA-31, conteneur d'initialisation pour les droits du volume puis exécution en non-root ([plan](../06-securite/plan-remediation.md)). Les pistes ne sont pas testées.

## Critère 2 — Qualité technique du prototype

### Q6. Comment les deux services communiquent-ils, et que se passe-t-il si `notification-service` tombe ?

**Critères** : 2.

**À dire.** Ils ne s'appellent jamais : `catalog-service` publie un événement dans l'exchange `article.events` de RabbitMQ, et `notification-service` le consomme dans sa propre file durable. L'événement transporte déjà l'état utile (catégorie, vendeur, titre, prix), donc le consommateur n'a rien à redemander. Si `notification-service` est arrêté, le catalogue continue de publier, les messages s'accumulent dans la file et sont traités au retour du service. Je l'ai mesuré en supprimant le consommateur : aucun message perdu sur 2 × 1 000.

**Chiffres.** 0 message perdu sur 2 × 1 000 ([index des expérimentations](../04-experimentations/README.md)).

**À montrer.** [Séquence de publication](../02-architecture/img/sequence-publication.svg) et [topologie RabbitMQ](../02-architecture/img/topologie-rabbitmq.svg) ; [ADR 0001](../02-architecture/adr/0001-microservices-evenements.md), conséquences.

**Limite à reconnaître.** Une seule file classique sur un seul nœud : L7, action PA-54 (quorum queues, dead-letter queue).

### Q7. Que se passe-t-il si RabbitMQ est indisponible au moment de la publication ?

**Critères** : 2, 8.

**À dire.** L'article est bien enregistré, car l'événement n'est publié qu'après le commit. Le service réessaie pendant un budget borné, 5 secondes par défaut, avec la confirmation du broker. Si le broker reste indisponible, l'événement est perdu et l'erreur est journalisée : l'acheteur n'est pas notifié. C'est la limite L2, que j'ai écrite : la cible ferme cette fenêtre avec une outbox transactionnelle. C'est le prix de la simplicité du POC (ADR 0007).

**Chiffres.** Budget de réessai de 5 s ([contrats, section 3.2](../02-architecture/contrats.md#32-garanties-et-limites)).

**À montrer.** [Contrats, garanties et limites](../02-architecture/contrats.md#32-garanties-et-limites) ; [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md), ligne « outbox ».

**Limite à reconnaître.** L2 : action PA-54 (outbox, long terme) et, en attendant, un compteur d'échecs et une alerte (PA-36), d'après le [plan, section 5.3](../06-securite/plan-remediation.md#53-limites-l1-à-l25-encore-ouvertes).

### Q8. Pourquoi la sonde `/health/ready` ne teste-t-elle pas RabbitMQ ?

**Critères** : 2, 5.

**À dire.** Une sonde de disponibilité (readiness) répond à : « ce pod peut-il servir une requête ? ». Le catalogue peut lire et écrire sans le broker, seule la publication échoue, et elle est journalisée. Si la sonde testait RabbitMQ, une panne du broker retirerait tous les pods du service du routage, et le catalogue deviendrait injoignable alors qu'il pourrait répondre. La reconnexion automatique d'aio-pika (`connect_robust`) suffit. La sonde ne teste donc que PostgreSQL.

**Chiffres.** Aucun chiffre propre ; décision issue du protocole 1.

**À montrer.** [Synthèse des expérimentations](../04-experimentations/README.md#synthèse-et-conséquences-pour-le-poc), ligne « Sonde `/health/ready` sans RabbitMQ ».

**Limite à reconnaître.** Pendant une panne du broker, la publication échoue (voir Q7, L2).

### Q9. Où est la preuve que le POC se déploie depuis rien, et en combien de temps ?

**Critères** : 2, 1.

**À dire.** J'ai suivi le README tel quel après avoir supprimé le cluster : le déploiement de l'ensemble prend 174 secondes, le test de fumée est vert et les six parcours Playwright passent. Le protocole 4 mesure 199 secondes depuis rien. Tout est scripté : `cluster.sh create`, puis `deploy.sh all <tag>`. Ce sont des mesures sur mon Mac, avec 10 CPU et 8 Go donnés à Docker Desktop.

**Chiffres.** 174 s, 6 parcours sur 6 en 9,6 s ([fiche P10-01, journal](../suivi/taches/P10-01.md)) ; 199 s depuis rien ([index des expérimentations](../04-experimentations/README.md)).

**À montrer.** [README, section Déployer sur le cluster local](../../README.md#déployer-sur-le-cluster-local) ; [protocole 4](../04-experimentations/04-deploiement/protocole.md).

**Limite à reconnaître.** Il faut 10 000 Mo de disque libres dans la VM Docker, et jusqu'à 3,2 Go d'images à télécharger si le cache est vide ([index des expérimentations](../04-experimentations/README.md), budget disque).

### Q10. Pourquoi une seule instance PostgreSQL pour les deux services ?

**Critères** : 2, 8.

**À dire.** Trois instances triplaient la mémoire sur un poste de 8 Go (ADR 0007). J'ai gardé l'essentiel : une base logique et un utilisateur PostgreSQL par service, sans droit de superutilisateur, qui ne peut pas se connecter à la base de l'autre. Les données restent donc cloisonnées par les droits. Mais je reconnais le risque : une seule instance est un point de défaillance unique, et si son compte d'administration est compromis, toutes les bases sont exposées, celle de Keycloak comprise.

**Chiffres.** Aucun chiffre ; preuves : `NOSUPERUSER` et `REVOKE ALL … FROM PUBLIC` dans `deploy/compose/postgres-init/10-roles.sh` ([plan de remédiation, BP-14](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** [Architecture du POC](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc), ligne L3 ; [schémas de données](../02-architecture/img/donnees-catalog.svg).

**Limite à reconnaître.** L3 : actions PA-23 (retirer le mot de passe administrateur des pods, base de Keycloak sur sa propre instance, court terme) et PA-53 (PostgreSQL managé et répliqué, long terme).

## Critère 3 — Fonctionnalité métier

### Q11. Comment le contrôle automatique détecte-t-il un téléphone ou un email, et comment le contourner ?

**Critères** : 3, 8.

**À dire.** Le contrôle lit le titre et la description. Il y a une adresse email quand un « @ » est précédé d'un caractère valide et suivi d'un domaine avec au moins un point. Pour un téléphone, il retire d'abord les dates, puis cherche des suites de chiffres et de séparateurs : dix chiffres commençant par 0 puis un chiffre de 1 à 9, quel que soit le découpage, ou un préfixe `+` ou `00` suivi de 9 à 15 chiffres. Un article non conforme est enregistré `REJECTED`, avec les motifs `CONTACT_EMAIL` ou `CONTACT_PHONE`, sans événement. Il n'est pas infaillible : « zéro six… », « arobase » ou un numéro dans une photo passent.

**Chiffres.** Temps linéaire, vérifié par un test (moins de 100 ms sur les pires cas) après la règle Sonar S8786 ([plan, BP-13](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** `services/catalog-service/src/catalog/contact.py` ; test d'acceptation `tests/acceptance/test_us03_publication.py` ; [séquence de publication](../02-architecture/img/sequence-publication.svg).

**Limite à reconnaître.** L15 (coordonnées obfusquées, texte dans les images) : actions PA-37 (étendre la détection) et PA-57 (service de modération, statut `PENDING_REVIEW`).

### Q12. Pourquoi le contrôle est-il synchrone et la notification asynchrone ? En combien de temps l'acheteur est-il prévenu ?

**Critères** : 3, 2.

**À dire.** Le vendeur doit connaître le statut de son article dès la réponse HTTP : le contrôle est donc synchrone. La diffusion, elle, ne doit ni allonger sa réponse ni dépendre de `notification-service` : elle est asynchrone. Le délai entre l'événement et la création de la notification, mesuré par la métrique `notification_delay_seconds`, est inférieur à 0,1 seconde pour un seuil de 2 secondes. Dans le POC, l'acheteur voit ses notifications en cliquant sur « Actualiser » : il n'y a pas de poussée en temps réel.

**Chiffres.** p95 de moins de 0,1 s (0,095 s, interpolé) pour un seuil de 2 s, ENF-14 ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8), ligne I3 ENF-14).

**À montrer.** [Architecture du POC, section 6](../02-architecture/architecture-poc.md#6-parcours-principal--publication-dun-article) ; page « Mes centres d'intérêt » de l'application.

**Limite à reconnaître.** Pas de WebSocket ni de Server-Sent Events dans le POC : c'est dans la cible.

### Q13. Comment évitez-vous les notifications en double ?

**Critères** : 3, 2.

**À dire.** RabbitMQ livre « au moins une fois » : un message peut donc arriver deux fois. Chaque événement porte un identifiant, `event_id`. La table des notifications a une contrainte `UNIQUE (user_id, source_event_id)` et on insère avec `ON CONFLICT DO NOTHING`. Le service n'acquitte le message qu'après le commit en base. Mesure : sur 1 000 messages, un a été relivré et aucun doublon n'a été traité. Pour le prix, la requête est un `PUT`, donc idempotente : un prix identique ne crée ni historique ni événement.

**Chiffres.** 1 message relivré sur 1 000, 0 doublon traité ([index des expérimentations](../04-experimentations/README.md)).

**À montrer.** [Contrats, section 3.2](../02-architecture/contrats.md#32-garanties-et-limites) ; [contrats, section 2.1](../02-architecture/contrats.md) (« Pourquoi `PUT` pour le prix »).

**Limite à reconnaître.** Pas de table `processed_events` : un futur consommateur devra gérer lui-même ses doublons (L7, action PA-54).

### Q14. Le contexte demande de la détection de fraude. Qu'avez-vous fait ?

**Critères** : 3, 2.

**À dire.** Je ne l'ai pas développée, et c'est un choix tracé : un second consommateur ne prouvait rien de plus qu'un premier sur le découpage (ADR 0007). Ce que j'ai fait, c'est le point d'extension : l'outil anti-fraude, interne ou acheté, s'abonnera à l'exchange `article.events` avec sa propre file, sans modifier `catalog-service`. Un test d'intégration le montre : une file temporaire liée à l'exchange reçoit les événements. Le contrôle des coordonnées protège déjà la commission de 5 %, mais ce n'est pas de la détection de fraude.

**Chiffres.** Aucun chiffre ; commission de 5 % (EF-19, [exigences](../03-backlog/exigences.md)).

**À montrer.** [Topologie RabbitMQ](../02-architecture/img/topologie-rabbitmq.svg) ; `services/catalog-service/tests/test_rabbitmq.py` ; [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md).

**Limite à reconnaître.** L1, priorité haute. Le point d'extension est testé en intégration, pas en direct sur le cluster ([protocole 1, limites](../04-experimentations/01-rabbitmq/protocole.md)). Actions : PA-27 (exigences), PA-36 (consommateur `fraud`), PA-41.

### Q15. Le POC répond-il au besoin du contexte ? Qu'est-ce qui est hors périmètre ?

**Critères** : 3.

**À dire.** Il répond à la chaîne essentielle : publier un article ou changer son prix, contrôler, notifier les acheteurs intéressés. Cela fait cinq user stories, dix-sept points d'estimation et dix-sept critères d'acceptation, tous passés. Sont hors périmètre, assumés par l'ADR 0007 : la détection de fraude, le paiement, le chat, la notation, les recommandations, la publicité, les enchères, l'internationalisation et le contrôle d'accessibilité. Ils figurent dans l'architecture cible, pas dans le POC.

**Chiffres.** 5 stories, 17 points (US-01 : 2, US-02 : 2, US-03 : 5, US-04 : 3, US-05 : 5), 17 critères d'acceptation (US-01 : 3, US-02 : 3, US-03 : 4, US-04 : 3, US-05 : 4) ; 17 sur 17 en 9,84 s ([user stories](../03-backlog/user-stories.md), [indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)).

**À montrer.** [User stories](../03-backlog/user-stories.md) ; [captures du parcours](../../frontend/e2e/resultats/captures/).

**Limite à reconnaître.** Le POC prouve la faisabilité de la chaîne, pas une plateforme complète : voir Q61.

## Critère 4 — Conformité du processus CI/CD

### Q16. Comment prouvez-vous que le pipeline réel est conforme au schéma, et qu'il bloque vraiment ?

**Critères** : 4, 7.

**À dire.** Le schéma de `cicd.md` est le contrat. Pour chaque élément, le document de conformité donne la ligne du fichier de workflow et un run qui le prouve. Les écarts trouvés (E1 à E14) ont été tranchés : soit le workflow corrigé, soit le contrat mis à jour. Les blocages sont démontrés par des runs rouges : `lint` en échec sur un import inutile, `build-scan` en échec sur une CVE CRITICAL, quality gate SonarCloud en échec sur du code sans test. Un test en échec ou une couverture sous 80 % n'ont pas de run rouge dédié : je le dis, le mécanisme est le même.

**Chiffres.** Run `backend` de référence : 11 jobs verts, run 42219458020 ; premier run : 5 min 47 s, 9 jobs verts ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8), [conformité](../01-qualite/conformite-pipeline.md)).

**À montrer.** [Tableau de conformité](../01-qualite/conformite-pipeline.md#2-tableau-de-conformité), [preuves de blocage](../01-qualite/conformite-pipeline.md#4-preuves-de-blocage) ; annexe A1 du [support](support.md).

**Limite à reconnaître.** Pas de run rouge pour `test` ni `acceptance` ([conformité, section 5](../01-qualite/conformite-pipeline.md)).

### Q17. Pourquoi `sonar` ne tourne-t-il que sur `main` et les pull requests ?

**Critères** : 4, 6.

**À dire.** C'est une limite du plan gratuit de SonarCloud : il n'analyse que la branche principale et les pull requests. Sur une branche de tâche, l'analyse échouait avec « Organization is not allowed to access data from non main branches ». Le quality gate s'applique donc là où le code entre dans `main`. Les jobs suivants portent `!failure() && !cancelled()` pour s'exécuter malgré un `sonar` sauté, mais ils sont sautés si un job précédent échoue.

**Chiffres.** Run 42034154273 (l'erreur) ; pull request n°1, run 42037655092 (`sonar` exécuté) ([conformité, E12 et E14](../01-qualite/conformite-pipeline.md)).

**À montrer.** [cicd.md, déclencheurs](../01-qualite/cicd.md#déclencheurs) ; `.github/workflows/backend.yml`.

**Limite à reconnaître.** Une branche de tâche n'a pas d'analyse Sonar ; la cible analyse chaque branche ([cicd.md, écarts](../01-qualite/cicd.md#5-écarts-entre-le-poc-et-la-cible)).

### Q18. Qu'est-ce qu'un digest, et comment remonte-t-on du pod au commit ?

**Critères** : 4, 8.

**À dire.** Un tag peut être déplacé par quiconque a le droit d'écriture ; un digest `sha256:…` est calculé sur le contenu de l'image, il est immuable. Le tag `sha-<7 caractères>` est propre à un commit et la CI ne le réécrit jamais. Le chemin : pod, `imageID` (digest), tag `sha-…`, commit, run de CI, avec ses rapports Trivy, JUnit et Sonar. Le script `deploy.sh` vérifie le digest sur GHCR avant tout changement et déploie `tag@digest`.

**Chiffres.** Chemin complet démontré au [protocole 4](../04-experimentations/04-deploiement/protocole.md).

**À montrer.** [cicd.md, traçabilité](../01-qualite/cicd.md#4-traçabilité) ; `kubectl -n collector get pod -o jsonpath` sur `imageID`.

**Limite à reconnaître.** Les images ne sont pas signées (pas de cosign) : la référence par digest suffit à garantir que l'image déployée est celle qui a passé les contrôles ([journal des décisions](../suivi/journal-decisions.md), 31/10/2026).

### Q19. Pourquoi Trivy en binaire vérifié et les actions épinglées par SHA ?

**Critères** : 4, 8.

**À dire.** En mars 2026, des tags de `trivy-action` ont été réécrits avec du code malveillant (avis GHSA-69fq-xp46-6x23). Une action référencée par tag aurait exécuté ce code avec le jeton du workflow. Je n'utilise donc aucune action tierce pour Trivy : le workflow télécharge la release officielle 0.76.0 et refuse tout fichier dont la somme SHA-256, écrite dans le dépôt, diffère. Les autres actions sont épinglées par SHA de commit, `persist-credentials: false`, permissions en lecture seule par défaut.

**Chiffres.** Trivy 0.76.0 ; la dernière version est la 0.76.2 ([indicateurs, I4](../01-qualite/indicateurs.md#limites-de-la-mesure)).

**À montrer.** [cicd.md, précisions](../01-qualite/cicd.md#3-détail-des-étapes) ; [plan, BP-11](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc).

**Limite à reconnaître.** La base de vulnérabilités est téléchargée à l'exécution ; Trivy a deux versions de retard (action d'I4 au plan).

## Critère 5 — Validation de l'environnement d'exécution

### Q20. Un cluster k3d local est-il un « environnement managé » ?

**Critères** : 5.

**À dire.** Au sens strict, non : le plan de contrôle tourne sur mon poste, pas chez un fournisseur. C'est écrit dans l'ADR 0006. En revanche c'est un vrai Kubernetes, k3s, distribution certifiée CNCF, à trois nœuds, avec un orchestrateur qui recrée les pods, un autoscaler et un routage par Ingress. Je l'ai choisi pour son coût nul, sa reproductibilité et parce qu'il fonctionne hors ligne. L'ADR est acceptée sous réserve de la validation de l'intervenant. Si un service managé est exigé, le repli est Oracle OKE Always Free avec le même chart, mais je ne l'ai pas testé.

**Chiffres.** 1 server + 2 agents ; images amd64 et arm64 ([architecture du POC](../02-architecture/architecture-poc.md)).

**À montrer.** [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), conséquences ; [placement des nœuds](../02-architecture/img/placement-noeuds.svg).

**Limite à reconnaître.** Repli non testé ; plan de contrôle unique (L16), migration vers un Kubernetes managé à PA-51.

### Q21. Comment fonctionne l'HPA, et pourquoi redescend-il lentement ?

**Critères** : 5.

**À dire.** L'HPA compare le CPU moyen des pods à leur requête (100m) : cible 70 %, entre 2 et 5 réplicas. Sous le pic de 200 utilisateurs, `catalog-service` passe de 2 à 5 réplicas prêts en 60 secondes. À la descente, Kubernetes applique par défaut une fenêtre de stabilisation de 300 secondes : c'est une protection contre les yoyos, des montées et descentes répétées. D'où 325 secondes pour retrouver 2 pods après l'arrêt de la charge.

**Chiffres.** 2 à 5 réplicas prêts en 60 s ; retour à 2 pods en 325 s ([index des expérimentations](../04-experimentations/README.md)).

**À montrer.** [Protocole 5](../04-experimentations/05-charge-disponibilite/protocole.md), section 6 ; capture [Grafana du retour](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-retour-catalog-service.png).

**Limite à reconnaître.** L'HPA ne regarde que le CPU et son plafond est atteint vers 200 utilisateurs (72 à 75 % à 5 réplicas) : relever `maxReplicas` ou régler le comportement de réduction ([indicateurs](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique)).

### Q22. Que se passe-t-il si un nœud tombe ?

**Critères** : 5, 2.

**À dire.** Je ne le démontre pas, et je le dis. Sans règle de placement, deux réplicas d'un service peuvent être sur le même nœud : j'ai relevé deux répartitions, chacune sur deux nœuds différents (`agent-0` et `agent-1` dans un déploiement, `server-0` et `agent-0` dans un autre), mais rien ne le garantit sans règle de placement (L8). Le résultat d'une panne serait donc aléatoire. Je démontre ce que le POC garantit : l'auto-réparation d'un pod et l'autoscaling. Plus grave, PostgreSQL et RabbitMQ sont en une seule instance, sur des volumes liés à un nœud : perdre ce nœud les rend indisponibles.

**Chiffres.** Pod remplacé en 4,9 s, 0 échec sur 533 requêtes ; 7,1 s sans charge ([index](../04-experimentations/README.md), [protocole 4](../04-experimentations/04-deploiement/protocole.md)).

**À montrer.** [Architecture du POC, section 2 et section 4](../02-architecture/architecture-poc.md#4-disponibilité-et-montée-en-charge).

**Limite à reconnaître.** L8 (placement, PodDisruptionBudget), L9 (stockage et services non redondants) : actions PA-31 et PA-53, qui inclut la démonstration de panne de nœud.

### Q23. Pourquoi 300 utilisateurs en direct et 200 dans le protocole ?

**Critères** : 5, 10.

**À dire.** La mesure de référence est celle du protocole 5, à 200 utilisateurs, environ 87 requêtes par seconde. En direct, le cluster part à froid et 200 utilisateurs n'atteignent pas toujours les 5 réplicas en 75 secondes. J'en lance donc 300 pour que la démonstration atteigne le plafond. Ce n'est pas une mesure : je cite toujours les chiffres du protocole. Si le bilan dit 4 réplicas au lieu de 5, je le dis tel quel, la montée est démontrée quand même.

**Chiffres.** 5 réplicas prêts entre 43 et 70 s dans les répétitions ; `pic-charge.sh` de 73 à 87 s ([script de démonstration](demo/script-demo.md)).

**À montrer.** [Script de démonstration, étape 3](demo/script-demo.md) ; [résumé du protocole 5](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/resume.md).

**Limite à reconnaître.** Une seule exécution de référence, sur le même Mac que le cluster.

### Q24. Vos résultats de charge sont-ils transposables en production ?

**Critères** : 5, 6.

**À dire.** Pas tels quels. Locust tourne sur le même Mac que le cluster, qui partage ses 10 CPU, à travers Traefik et TLS, sans réseau réel, avec une seule exécution par scénario. Le seuil vaut pour 50 utilisateurs ; le pic de 200 sert à franchir le seuil de l'HPA. Ce que cela prouve, ce sont les mécanismes, autoscaling et auto-réparation, et une marge : p95 de 21 ms pour un seuil de 300 ms.

**Chiffres.** 0 réponse 5xx sur 20 235 requêtes ; 0 sur 6 564 à 50 utilisateurs ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)).

**À montrer.** [Limites de la mesure](../01-qualite/indicateurs.md#limites-de-la-mesure) ; [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), conséquences.

**Limite à reconnaître.** Aucun essai au-delà de 200 utilisateurs ; action : relever le plafond et rejouer.

## Critère 6 — Indicateurs de qualité

### Q25. Pourquoi ces cinq indicateurs ?

**Critères** : 6.

**À dire.** La grille cite fonctionnalité, performance, maintenabilité et fiabilité. J'avais quatre indicateurs ; j'en ai ajouté un cinquième, le taux de critères d'acceptation, parce que l'adéquation fonctionnelle n'était pas couverte. Chacun est rattaché à l'ISO 25010, a un seuil repris des exigences non fonctionnelles sans modification, un outil, un moment de mesure et une action. I1 couverture, I2 dette technique, I3 latence p95 et erreurs, I4 vulnérabilités CRITICAL et HIGH, I5 critères d'acceptation.

**Chiffres.** Seuils : couverture ≥ 80 % ; note A et duplication < 3 % ; p95 < 300 ms en lecture et < 500 ms en publication, moins de 1 % de 5xx ; 0 vulnérabilité avec correctif ; 17 sur 17 ([indicateurs, synthèse](../01-qualite/indicateurs.md#synthèse)).

**À montrer.** [Synthèse des indicateurs](../01-qualite/indicateurs.md#synthèse) ; [journal des décisions](../suivi/journal-decisions.md), 31/10/2026.

**Limite à reconnaître.** La complexité cognitive par fonction n'est mesurée que par un indice, la complexité cyclomatique (maximum 10).

### Q26. Tout est dans les seuils : où est la dette technique ?

**Critères** : 6.

**À dire.** Elle existe, les seuils ne la voient pas. Un : 531 lignes de socle recopiées entre les deux services, 34,6 % des lignes de `src`, invisibles pour SonarCloud qui analyse un projet par service ; cible : un paquet partagé. Deux : 15 erreurs de `mypy --strict` dans les tests, que la CI ne contrôle pas. Trois : un bundle front de 609,4 Ko. Quatre : le plafond de l'HPA atteint vers 200 utilisateurs. J'ai aussi trouvé un plafond de frais de port à 1 000 000 € dans le code, absent des règles métier : à arbitrer avec le Product Owner.

**Chiffres.** 531 lignes (34,6 %) ; 15 erreurs ; 609,4 Ko ([axes d'amélioration](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique)).

**À montrer.** [Axes d'amélioration](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique).

**Limite à reconnaître.** Relevé du 06/11/2026 ; la CI ne contrôle toujours que `src` avec `mypy` (`.github/workflows/backend.yml`).

### Q27. La couverture à 98 % suffit-elle ? Le seuil de 80 % n'est-il pas trop bas ?

**Critères** : 6, 7.

**À dire.** Le seuil de 80 % est celui de l'exigence ENF-22, je l'ai repris. La mesure est bien au-dessus : 98,45 % et 97,66 %, branches comprises. Mais une baisse de 17 points passerait sans alerte : je propose de remonter le seuil à 95 %, décision à arbitrer puisque l'exigence dit 80 %. La couverture ne dit pas la qualité des assertions. J'ai classé les lignes non couvertes : des chemins d'erreur d'infrastructure, le cache JWKS, du code mort. Une seule portait une règle de validation, je l'ai testée.

**Chiffres.** Lignes 99,06 % et 98,47 %, branches 94,17 % et 91,49 % ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)).

**À montrer.** [Lignes et branches non couvertes](../01-qualite/indicateurs.md#mesures-nouvelles-qui-révèlent-de-la-dette).

**Limite à reconnaître.** Seuil de CI à 80 % : proposition à 95 %, à arbitrer.

### Q28. Pourquoi le p95 et pas la moyenne ?

**Critères** : 6.

**À dire.** Le p95 est la durée sous laquelle 95 % des requêtes se terminent. La moyenne cache les requêtes lentes, que l'utilisateur ressent. Le seuil d'I3 porte donc sur le p95. J'ai aligné les bornes d'histogramme de Prometheus sur les seuils de 300 et 500 ms : avec les bornes par défaut, un p95 réel de 200 ms était lu à 0,48 s, soit 140 % d'écart.

**Chiffres.** 0,4800 s lus pour 200 ms avec les bornes par défaut, contre 0,2474 s avec des bornes serrées ([synthèse](../04-experimentations/README.md#synthèse-et-conséquences-pour-le-poc)).

**À montrer.** [Protocole 3](../04-experimentations/03-observabilite/protocole.md) ; tableau de bord Grafana « Collector - service ».

**Limite à reconnaître.** Le p95 de Prometheus est interpolé dans un seau d'histogramme ; Locust mesure côté client.

## Critère 7 — Processus de test

### Q29. Quels types de tests avez-vous, et lesquels sont hors CI ?

**Critères** : 7.

**À dire.** Le processus formalise dix types, avec outil, emplacement, moment, responsable et critère de succès. Neuf sont appliqués avec des résultats, le dixième, la non-régression, est le rejeu de toute la suite à chaque push. Unitaires, intégration (testcontainers) et API en pytest : 289 tests pour le catalogue et 203 pour la notification au 06/11/2026 (run 42219458020) ; relancé le 11/11/2026, le catalogue en compte 294. Acceptation : 17 tests, un par critère. Front : 62 tests Vitest. Playwright et Locust tournent à la demande sur le cluster, hors CI, par décision du 31 octobre : le front n'est pas dans la pile `docker compose`.

**Chiffres.** 289 et 203 passed ; 17 passed ; 62 tests passés ; 6 parcours sur 6 ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)). Relancé le 11/11/2026 : 294 passed pour `catalog-service` ([fiche P10-01](../suivi/taches/P10-01.md)).

**À montrer.** [Tableau des types de tests](../01-qualite/processus-test.md#tableau-des-types-de-tests) ; [pyramide](../01-qualite/img/pyramide-tests.svg).

**Limite à reconnaître.** Playwright et Locust ne bloquent pas la livraison.

### Q30. Pourquoi les tests d'acceptation tournent-ils sur `docker compose` et pas sur le cluster ?

**Critères** : 7, 4.

**À dire.** Les critères traversent les deux services, RabbitMQ et Keycloak : seule une pile complète les teste. Le job `acceptance` démarre donc la pile `docker compose` avec les images exactes que Trivy vient de scanner, passées par une archive. Sur le cluster, j'ai refusé de créer un client Keycloak de test avec *Direct Access Grants* : il affaiblirait l'environnement qui joue la production. Les six parcours Playwright, avec une vraie connexion PKCE, vérifient le cluster à la place.

**Chiffres.** 17 sur 17 en 9,84 s ; 6 parcours sur 6 sur un cluster neuf ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8), [fiche P10-01](../suivi/taches/P10-01.md)).

**À montrer.** [Journal des décisions](../suivi/journal-decisions.md), 31/10 et 05/11/2026 ; [`tests/acceptance`](../../tests/acceptance/README.md).

**Limite à reconnaître.** Les 17 critères ne passent pas sur le cluster lui-même.

### Q31. Comment testez-vous la sécurité des routes sans Keycloak dans les tests ?

**Critères** : 7, 8.

**À dire.** Les tests du job `test` signent leurs jetons avec une clé RSA générée par la suite, avec un JWKS de test : c'est rapide et déterministe. Ils couvrent le jeton absent, expiré, mauvais `iss`, mauvaise `aud`, `alg: none`, HS256 signé avec la clé publique, `kid` inconnu, puis 403 pour un mauvais rôle et 422 pour un champ inconnu. La vraie validation contre Keycloak est dans le job `acceptance`.

**Chiffres.** Références : `services/catalog-service/tests/test_security.py` lignes 67, 74, 80, 132, 141, 170, 260 ([plan, BP-03 à BP-05](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** `services/catalog-service/tests/test_security.py`.

**Limite à reconnaître.** Pas de test systématique « chaque route de l'OpenAPI » : PA-33.

### Q32. Que faites-vous d'un test intermittent ou d'une anomalie ?

**Critères** : 7.

**À dire.** Un test intermittent n'est jamais relancé en boucle : il est corrigé ou supprimé. Pas de `sleep` arbitraire, pas de dépendance à l'ordre. Une anomalie suit toujours le même chemin : constat avec le journal, qualification par le Lead Developer, correction accompagnée d'un test qui échoue sans le correctif, vérification que toute la suite repasse, puis suivi à la revue de fin de sprint. Un test en échec bloque la publication des images ; il ne bloque pas techniquement la fusion, car `main` n'est pas protégé (PA-16, hors POC) : c'est la règle d'organisation, fusion par le seul Lead Developer après audit, qui l'empêche.

**Chiffres.** Aucun.

**À montrer.** [Processus de test, gestion des anomalies](../01-qualite/processus-test.md#5-gestion-des-anomalies).

**Limite à reconnaître.** Aucune limite particulière relevée dans le processus ; seule la revue de fin de sprint reste une pratique d'équipe, hors du dépôt.

## Critère 8 — Remédiation des risques de sécurité

### Q33. Comment fonctionne PKCE, et que protège-t-il ?

**Critères** : 8, 2.

**À dire.** Une application monopage est un client public : tout son code est lisible, elle ne peut pas garder de secret. PKCE lie la demande d'autorisation à l'échange du code par un secret à usage unique. Le navigateur génère un `code_verifier` aléatoire et envoie à Keycloak le `code_challenge`, qui est le SHA-256 du verifier, encodé en base64url. Pour échanger le code contre un jeton, il doit présenter le verifier : un attaquant qui intercepte le code ne peut pas l'échanger. C'est le flux recommandé par la RFC 9700, qui déconseille le flux implicite.

**Chiffres.** Jeton d'accès de 5 minutes ; 6 parcours Playwright avec connexion PKCE réelle ([architecture, section 7](../02-architecture/architecture-poc.md#7-authentification--flux-oidc-avec-pkce)).

**À montrer.** [Flux d'authentification](../02-architecture/img/sequence-authentification.svg) (annexe A6) ; [ADR 0004](../02-architecture/adr/0004-keycloak.md).

**Limite à reconnaître.** PKCE protège le code, pas le jeton une fois dans la page (voir Q34).

### Q34. Pourquoi des jetons en mémoire, et que se passe-t-il en cas de XSS ?

**Critères** : 8.

**À dire.** Par défaut, react-oidc-context range la session dans `sessionStorage`. J'ai configuré un `userStore` en mémoire (`InMemoryWebStorage`) : aucun jeton ne persiste dans le stockage du navigateur, un test le vérifie. Seul l'état de redirection de la connexion reste en `sessionStorage`. Soyons précis : la mémoire ne protège pas d'un XSS actif, un script injecté peut appeler l'API avec le jeton en cours. D'où le jeton court de 5 minutes, la CSP `script-src 'self'` et, dans la cible, un BFF qui garde les jetons côté serveur.

**Chiffres.** Jeton de 5 min (`accessTokenLifespan` : 300) ; test `frontend/src/auth/oidc.test.ts` ([plan, BP-02](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** [ADR 0005](../02-architecture/adr/0005-react-typescript.md), conséquences ; [architecture, section 7](../02-architecture/architecture-poc.md#7-authentification--flux-oidc-avec-pkce).

**Limite à reconnaître.** L5 (BFF) : action PA-56, long terme. L24 (`style-src 'unsafe-inline'`, imposé par Emotion) : PA-34.

### Q35. Comment un service vérifie-t-il un JWT, et pourquoi deux URL de Keycloak ?

**Critères** : 8, 2.

**À dire.** Chaque service vérifie lui-même le jeton, sans faire confiance au réseau interne : signature RS256 imposée (l'algorithme `none` et HS256 sont rejetés), émetteur `iss`, audience `aud = collector-api`, expiration `exp`, puis le rôle et la propriété de la ressource. Les clés publiques viennent du JWKS de Keycloak, mises en cache. Deux URL parce que, dans un pod, `127.0.0.1` désigne le pod lui-même : les clés sont téléchargées par l'URL interne du Service Kubernetes, mais `iss` est comparé à l'URL publique, celle qui figure dans le jeton. Tous les 401 ont le même titre, la raison du rejet reste dans les logs.

**Chiffres.** 15 cas d'autorisation conformes ; un seul appel JWKS pour 216 requêtes ([index](../04-experimentations/README.md), [synthèse](../04-experimentations/README.md#synthèse-et-conséquences-pour-le-poc)).

**À montrer.** [Architecture, encadré « le piège du nom de domaine »](../02-architecture/architecture-poc.md#5-points-de-sécurité) ; `services/catalog-service/src/catalog/auth.py`.

**Limite à reconnaître.** Pas d'introspection : un jeton révoqué reste valide jusqu'à son expiration, 5 minutes ([ADR 0004](../02-architecture/adr/0004-keycloak.md)). L'URL interne n'est pas chiffrée (L10, PA-55).

### Q36. Qu'apporte STRIDE ?

**Critères** : 8.

**À dire.** STRIDE classe les menaces en six familles : usurpation, falsification, répudiation, divulgation d'information, déni de service, élévation de privilèges. Je l'applique à chaque élément et à chaque flux du schéma, avec les frontières de confiance. Pour chacun, je note la mesure existante avec sa preuve et la menace résiduelle, rattachée à un risque du registre. Exemple : l'usurpation par un jeton forgé est couverte par les tests de sécurité ; le mouvement latéral d'un pod compromis ne l'est pas, faute de NetworkPolicy (R-04, L4). Le POC est noté comme s'il était en production, convention H-00.

**Chiffres.** 62 risques ([analyse de risques](../06-securite/analyse-risques.md)).

**À montrer.** [STRIDE du POC](../06-securite/analyse-risques.md#33-stride-poc) ; annexe A4 du [support](support.md).

**Limite à reconnaître.** L'analyse du reste du SI est documentaire et par hypothèses (voir Q42).

### Q37. Comment les risques sont-ils priorisés ?

**Critères** : 8.

**À dire.** Criticité égale impact de 1 à 5 fois probabilité de 1 à 5, la probabilité étant résiduelle, mesures existantes comprises. Seuils : critique à partir de 15, élevé de 10 à 14, moyen de 5 à 9, faible jusqu'à 4. Les règles R1 à R9 en tirent un horizon : chaque risque critique reçoit au moins une action à court terme, quel que soit l'effort ; un risque élevé à effort faible passe aussi à court terme ; les autres suivent leur effort. Mutualiser compte : une MFA protège plusieurs risques. La gravité d'un outil, un « HIGH » de Trivy, n'a pas de poids propre : seul compte le risque du registre.

**Chiffres.** 62 risques (7 critiques, 30 élevés) ; 58 actions : 29 à court terme (64 j), 21 à moyen terme (97,5 j), 8 à long terme (64 j) ; criticité cumulée de 650 à 298 en 12 mois, critiques de 7 à 0 ([plan, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide)).

**À montrer.** [Méthode de priorisation](../06-securite/plan-remediation.md#2-méthode-de-priorisation) ; [matrice](../06-securite/img/matrice-risques.svg) (annexe A2).

**Limite à reconnaître.** Les coûts sont des ordres de grandeur sans devis ; trois risques élevés restent à faire accepter par la direction (R-01, R-30, R-34).

### Q38. Que fait Trivy, et que se passe-t-il si une image vulnérable est publiée ?

**Critères** : 8, 4.

**À dire.** Trivy analyse l'image construite : paquets de l'OS, dépendances Python et secrets. Il bloque sur une vulnérabilité CRITICAL ou HIGH qui a un correctif, ou sur un secret. Mais une image publiée vieillit : une CVE publiée après la construction n'est pas vue. C'est arrivé : au scan du 10 novembre, `zlib1g` aurait donné 2 HIGH par service alors que la CI était verte. Je l'ai corrigé, puis proposé un scan quotidien des images déployées. Restent des vulnérabilités sans correctif, acceptées avec leur justification.

**Chiffres.** 11 lignes avec correctif par service avant corrections, 0 après ; sans correctif : 201 lignes (89 CVE), dont 11 CVE HIGH, système Debian ([rapport des scans, section 10](../06-securite/rapport-scans.md#10-après-corrections-p9-02)).

**À montrer.** [Rapport des scans, écart avec la CI](../06-securite/rapport-scans.md#43-écart-avec-les-contrôles-de-la-ci).

**Limite à reconnaître.** `--ignore-unfixed` écarte les vulnérabilités sans correctif ; le backend n'a pas de Trivy sur le digest publié ni d'arm64 scanné (le front, si). Actions : PA-21 (scan planifié), PA-35 (base d'image minimale).

### Q39. Où sont les secrets ?

**Critères** : 8, 2.

**À dire.** Aucun secret dans le dépôt : `.env.example` est versionné, `.env` ignoré. Le script `deploy.sh` génère les mots de passe manquants dans un `.env` local, créé en `umask 077`, puis crée les Secrets Kubernetes à partir de fichiers, jamais en argument de ligne de commande. Trivy cherche les secrets dans les images : zéro. Soyons honnêtes : un Secret Kubernetes est encodé, pas chiffré au repos, et les `.env` sont sur mon Mac, dans un dossier synchronisé par iCloud.

**Chiffres.** 0 secret dans les trois images ([plan, BP-07](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** `deploy/local/deploy.sh` ; `.gitignore` ; [analyse de risques, R-01](../06-securite/analyse-risques.md).

**Limite à reconnaître.** R-01 (poste du Lead Developer) : PA-15 (sortir secrets et dépôt d'iCloud, FileVault). Pas de Gitleaks sur l'historique (L13, PA-22). Chiffrement des Secrets au repos : PA-20.

### Q40. Et l'authentification multifacteur ?

**Critères** : 8.

**À dire.** Dans le POC, il n'y a pas de MFA dans le realm Keycloak. La détection de force brute est déclarée activée, avec les valeurs par défaut du produit, mais jamais éprouvée. Le plan traite la MFA à trois endroits : PA-02, MFA pour tous les comptes Microsoft 365, à court terme, car l'hameçonnage d'un dirigeant est le risque critique R-48 ; PA-17, régler et éprouver la force brute et imposer la MFA aux administrateurs de Keycloak ; PA-40, MFA obligatoire pour tout vendeur avant sa première vente, à moyen terme.

**Chiffres.** R-48 : criticité de 20 à 8 par PA-02 et PA-03 ([plan, synthèse](../06-securite/plan-remediation.md)).

**À montrer.** [Plan de remédiation, court terme](../06-securite/plan-remediation.md#41-court-terme-0-à-3-mois).

**Limite à reconnaître.** MFA absente du POC ; force brute non éprouvée.

### Q41. Qu'a donné l'audit OWASP ZAP ?

**Critères** : 8.

**À dire.** L'audit du 10 novembre a qualifié 25 constats. J'en ai corrigé sept le lendemain : `zlib1g`, PyJWT 2.15.0, `pip` retiré des images, console d'administration de Keycloak retirée de l'hôte public, en-têtes HSTS et `nosniff`, CSP `img-src`, un `try/finally`. Un second audit le prouve. Sur l'API, le scan actif complet ne trouve aucun constat de niveau moyen ou élevé. Une difficulté : mon premier scan actif a saturé la VM Docker, pods en `CrashLoopBackOff` pendant environ trois minutes ; le cluster est revenu seul. J'ai plafonné le conteneur ZAP.

**Chiffres.** 25 constats ; 0 constat de niveau moyen ou élevé sur l'API ([plan, BP-05](../06-securite/plan-remediation.md#7-déjà-appliqué-dans-le-poc)).

**À montrer.** [Rapport des scans](../06-securite/rapport-scans.md#3-difficultés-rencontrées-à-garder-pour-loral) ; [avant et après](../06-securite/plan-remediation.md#72-les-corrections-de-p9-02--avant-et-après).

**Limite à reconnaître.** Front et Keycloak : passif seulement ; pas de passe en tant qu'`admin`, ZAP absent de la CI (L13 : PA-33, PA-22).

### Q42. Comment bâtir un plan pour tout le SI alors que l'état de l'existant est inconnu ?

**Critères** : 8.

**À dire.** Par hypothèses explicites : 21 hypothèses numérotées, H-S01 à H-S18 et H-P01 à H-P03, notées au pire cas. La première action du plan, PA-01, est de les vérifier avant d'agir : confirmée, l'action est maintenue ; infirmée, la probabilité baisse. Exception, les actions peu coûteuses (MFA, chiffrement des postes, sauvegarde) démarrent sans attendre. Le plan couvre trois blocs : le POC, la plateforme cible et le système existant. La plateforme ne s'ouvre à de vrais utilisateurs qu'à deux conditions : aucun risque critique, et PA-39, PA-40, PA-41, PA-42 et PA-49 livrés et vérifiés.

**Chiffres.** 21 hypothèses ; 58 actions, 225,5 j ([plan, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide)).

**À montrer.** [Méthode, règle R6](../06-securite/plan-remediation.md#22-règles-qui-transforment-criticité-effort-et-dépendances-en-horizon) ; [couverture du SI](../06-securite/plan-remediation.md#5-couverture-de-tout-le-si).

**Limite à reconnaître.** L'état de l'existant est inconnu ; la fiabilité du plan sur ce bloc dépend de PA-01.

## Critère 9 — Gestion des compétences

### Q43. Pourquoi former sur Kubernetes et Helm plutôt que sur autre chose ?

**Critères** : 9.

**À dire.** Parce que c'est un écart de criticité haute que l'équipe doit tenir en interne en permanence : niveau requis 3, maximum de l'équipe 1. Je suis moi-même débutant en Kubernetes et Helm, et je dois pouvoir défendre et exploiter le cluster, même une fois le DevOps arrivé. La sécurité applicative est aussi haute, mais on achète ce niveau par un recrutement et un test d'intrusion externe. La formation : 28 heures, six modules, sur 6 semaines, avec des exercices sur le dépôt réel.

**Chiffres.** 28 heures, six modules, 6 semaines ; 12 j-h internes et de 4 800 à 7 200 € externes ([plan de formation](../05-competences/plan-formation.md)).

**À montrer.** [Matrice, analyse des écarts](../05-competences/matrice.md#4-analyse-des-écarts) ; [plan de formation, programme](../05-competences/plan-formation.md).

**Limite à reconnaître.** Le niveau 3 ne s'atteint pas en 28 heures : niveau 2 à la fin, niveau 3 après 3 mois de pratique encadrée (estimation).

### Q44. Pourquoi trois recrutements, et pas un profil qui fait tout ?

**Critères** : 9.

**À dire.** Chaque profil couvre un métier précis. DevOps/SRE : exploiter le Kubernetes managé, la CI/CD, l'observabilité, PostgreSQL. QA automaticien·ne : tests de bout en bout et de charge, validation de l'acceptation. UX/UI avec accessibilité : l'accessibilité RGAA est une exigence du contexte et ne s'acquiert pas en quelques semaines. Ce qui est ponctuel, test d'intrusion, RGPD, PCI DSS, est confié à un appui externe. Aucun profil ne cumule tout.

**Chiffres.** 26 compétences cartographiées ; 3 profils ([matrice](../05-competences/matrice.md)).

**À montrer.** [Recrutements envisagés](../05-competences/matrice.md#5-recrutements-envisagés).

**Limite à reconnaître.** Ce sont des recrutements envisagés, avec des dates d'arrivée conditionnelles au POC.

### Q45. Comment saurez-vous que la formation a fonctionné ?

**Critères** : 9.

**À dire.** Par les quatre niveaux de Kirkpatrick. Réaction : satisfaction moyenne d'au moins 4 sur 5 à chaque module. Apprentissage : sept épreuves pratiques, dont l'évaluation finale de trois pannes à diagnostiquer, sans aide, 7 sur 7 exigées pour le Lead Developer. Comportement : cinq comportements observés sur le projet, 3 sur 5 à un mois, 5 sur 5 à trois mois. Résultats : durée d'un déploiement par un autre membre de l'équipe, taux de retours arrière, niveau dans la matrice de 1 à 3.

**Chiffres.** 7 objectifs ; seuils 4/5, 3/5 puis 5/5 ([plan de formation, évaluation](../05-competences/plan-formation.md#7-évaluation-modèle-de-kirkpatrick)).

**À montrer.** [Évaluation](../05-competences/plan-formation.md#7-évaluation-modèle-de-kirkpatrick).

**Limite à reconnaître.** Les indicateurs de résultats reposent sur peu de déploiements : indicatifs.

### Q46. Les niveaux de vos deux développeurs sont-ils réels ?

**Critères** : 9.

**À dire.** Non, et la matrice le dit : le contexte ne décrit pas leurs profils. Dev 1 et Dev 2 sont des hypothèses, choisies crédibles et complémentaires : un back-end Python de cinq ans, un front React de cinq ans. Mon profil est réel. Conséquence assumée : le front repose sur une seule personne, c'est un risque de dépendance signalé dans l'analyse des écarts.

**Chiffres.** Aucun.

**À montrer.** [Hypothèses sur l'équipe](../05-competences/matrice.md#2-hypothèses-sur-léquipe).

**Limite à reconnaître.** Les niveaux de Dev 1 et Dev 2 sont des hypothèses.

## Critère 10 — Qualité de la présentation

### Q47. Quel message faut-il retenir ?

**Critères** : 10.

**À dire.** Le POC prouve qu'on peut livrer la chaîne complète, un besoin métier, deux services découplés par événements, un pipeline qui bloque sur les défauts, un cluster qui monte en charge et se répare, des indicateurs mesurés et un plan de sécurité, de façon reproductible : le README suivi sur un cluster neuf donne un déploiement en 174 secondes. Les limites, de L1 à L25, sont connues, numérotées et rattachées au plan.

**Chiffres.** 174 s ; 58 actions ; L1 à L25 ([guide du jury](guide-jury.md)).

**À montrer.** [Guide du jury](guide-jury.md), vue d'ensemble.

**Limite à reconnaître.** Voir les questions de la section « Limites ».

### Q48. Si vous aviez deux semaines de plus, que feriez-vous en premier ?

**Critères** : 10, 6, 8.

**À dire.** Je prendrais les actions de court terme du plan qui touchent le POC. D'abord PA-15 et PA-16 : sortir mes secrets du dossier synchronisé par iCloud, protéger GitHub (MFA, `main` protégée avec vérifications requises), parce que R-01 est un risque critique. Ensuite PA-21 et PA-22 : un scan quotidien des images publiées, Gitleaks et `pip-audit` dans la CI. Côté dette : un test qui compare les deux copies du socle, puis les 15 erreurs de `mypy` dans les tests.

**Chiffres.** R-01 : de 15 à 10 ; 15 erreurs `mypy` ; 531 lignes dupliquées ([plan](../06-securite/plan-remediation.md), [indicateurs](../01-qualite/indicateurs.md#axes-damélioration-contre-la-dette-technique)).

**À montrer.** [Plan, court terme](../06-securite/plan-remediation.md#41-court-terme-0-à-3-mois).

**Limite à reconnaître.** Ce sont des priorités du plan, pas des travaux commencés.

## Thème — Choix techniques

### Q49. Pourquoi RabbitMQ et pas Kafka ?

**Critères** : 2, 1.

**À dire.** Kafka est un journal distribué fait pour des volumes massifs et la relecture de l'historique. RabbitMQ est un broker qui route et acquitte message par message. Mon besoin en V1 : distribuer de façon fiable quelques événements par seconde à plusieurs consommateurs, avec gestion des échecs. C'est exactement le modèle exchange et files de RabbitMQ. Kafka est surdimensionné pour la V1, avec une empreinte mémoire JVM lourde sur un cluster local de 8 Go. Ce que je perds, c'est la relecture ; je la récupérerais avec les RabbitMQ Streams, ou Kafka pour la donnée.

**Chiffres.** RabbitMQ : 135 Mi mesurés ; volume visé : quelques événements par seconde, hypothèse ([ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md), [index](../04-experimentations/README.md)).

**À montrer.** [ADR 0003](../02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md) ; [topologie](../02-architecture/img/topologie-rabbitmq.svg).

**Limite à reconnaître.** Pas de relecture des événements passés ; Kafka non testé (Q4).

### Q50. Pourquoi deux services, ni un monolithe ni davantage ?

**Critères** : 2.

**À dire.** Le besoin est d'ajouter des fonctions qui réagissent aux mêmes faits métier sans modifier l'existant, et de pouvoir acheter l'anti-fraude. Un monolithe ne démontrait ni le découpage ni la communication interservice. Des appels REST synchrones créent un couplage : une panne de la fraude ralentirait la publication. J'ai choisi des services orientés événements. Mon premier découpage avait trois services ; j'ai retiré `fraud-service` : deux services démontrent déjà le découpage, et chaque composant doit servir un critère de la grille.

**Chiffres.** 2 services, 2 bases logiques ([ADR 0001](../02-architecture/adr/0001-microservices-evenements.md), [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md)).

**À montrer.** [ADR 0001](../02-architecture/adr/0001-microservices-evenements.md), options étudiées.

**Limite à reconnaître.** Cohérence à terme, broker à exploiter, débogage distribué ; atténué par `correlation_id` dans les logs et les événements. Socle recopié entre les deux services (Q26).

### Q51. Pourquoi FastAPI ?

**Critères** : 2.

**À dire.** Mon équipe est surtout en Python. FastAPI est asynchrone : un même processus sert HTTP et consomme AMQP avec aio-pika. Pydantic fait du contrat d'API une source unique de validation, de typage et de documentation OpenAPI. Le système de dépendances rend l'authentification remplaçable dans les tests. Django est monolithique et son ORM surtout synchrone ; Spring Boot est hors de nos compétences et plus lourd en mémoire.

**Chiffres.** p95 de 21 ms et 23 ms à 50 utilisateurs ([indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)).

**À montrer.** [ADR 0002](../02-architecture/adr/0002-fastapi.md).

**Limite à reconnaître.** Un appel bloquant dans une coroutine bloquerait la boucle d'événements ; atténué par des pilotes asynchrones uniquement (asyncpg, aio-pika).

### Q52. Pourquoi k3d plutôt qu'un cloud ?

**Critères** : 5, 2.

**À dire.** Trois contraintes : coût nul et durable, reproductibilité par script, démonstration possible hors ligne. Un cloud avec crédits d'essai peut disparaître avant la soutenance. k3d lance un vrai Kubernetes multi-nœuds où l'on démontre auto-réparation, HPA et Ingress, ce que docker-compose ne fait pas. Le chart Helm est indépendant du fournisseur et les images sont multi-architecture : le passage à un Kubernetes managé ne change pas le code.

**Chiffres.** 1 server + 2 agents ; déploiement en 174 s ([ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), [fiche P10-01](../suivi/taches/P10-01.md)).

**À montrer.** [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), options étudiées.

**Limite à reconnaître.** Ce n'est pas un environnement managé au sens strict (Q20) ; repli OKE non testé.

### Q53. Pourquoi Keycloak ?

**Critères** : 2, 8.

**À dire.** L'authentification est le dernier endroit où l'on veut écrire du code soi-même : hachage, rotation des clés, MFA, force brute. Keycloak apporte les standards OIDC, PKCE et JWT signés RS256, la fédération avec le Microsoft 365 déjà présent chez Collector (possible avec Keycloak, prévue dans la cible, non réalisée dans le POC), gratuitement et sans dépendance à un fournisseur, avec les données d'identité chez nous. Auth0 devient payant avec le succès, Cognito lie à AWS.

**Chiffres.** Keycloak : 581 Mi mesurés au repos ([index](../04-experimentations/README.md)).

**À montrer.** [ADR 0004](../02-architecture/adr/0004-keycloak.md).

**Limite à reconnaître.** Keycloak est un point critique : s'il tombe, plus de connexion, les jetons déjà émis vivent 5 minutes ; un seul réplica (L9, PA-53). Mises à jour de sécurité à notre charge.

### Q54. Pourquoi pas d'outbox ?

**Critères** : 2.

**À dire.** Une outbox demande une table, un relais et un verrouillage à écrire et à tester. La perte d'événement n'arrive que si le broker tombe entre le commit et la publication. Pour un POC, j'ai choisi la publication persistante, avec confirmation du broker et réessai borné, juste après le commit. Le risque est connu et écrit : L2, priorité haute. La cible écrit l'événement dans la même transaction, puis un relais le publie. Une transaction distribuée a été écartée : RabbitMQ ne la supporte pas.

**Chiffres.** Budget de réessai de 5 s ([contrats](../02-architecture/contrats.md#32-garanties-et-limites)).

**À montrer.** [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md) ; [ADR 0001](../02-architecture/adr/0001-microservices-evenements.md), « Plus d'informations ».

**Limite à reconnaître.** L2 : PA-54, long terme.

### Q55. Pourquoi Helm avec un script de déploiement, sans Argo CD ?

**Critères** : 4, 5.

**À dire.** Argo CD est un bon outil, mais sa valeur est en production. La consigne ne pénalise pas l'absence de déploiement automatique, et le cluster est sur mon Mac, inaccessible depuis GitHub : pousser depuis la CI exigerait un tunnel entrant et les identifiants d'administration dans la CI. Le script `deploy.sh` exécute `helm upgrade --install` après avoir vérifié l'image sur GHCR, avec retour arrière automatique. Un seul chart générique sert les services et le front.

**Chiffres.** Déploiement d'un nouveau tag : de 36 à 57 s (57 s à la toute première mesure) ([script de démonstration](demo/script-demo.md)).

**À montrer.** [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), « GitOps avec Argo CD » ; [cicd.md, écarts](../01-qualite/cicd.md#5-écarts-entre-le-poc-et-la-cible).

**Limite à reconnaître.** L12 : déploiement lancé depuis un poste, sans détection de dérive ; PA-52 (Argo CD) après la migration. Le retour arrière ne défait pas les migrations (L23, PA-38).

### Q56. Pourquoi avoir abandonné les opérateurs ?

**Critères** : 1, 2.

**À dire.** Bitnami ne publie plus gratuitement d'images maintenues depuis le 28 août 2025 : je suis parti des images officielles. J'ai d'abord pris des opérateurs, puis mesuré. L'opérateur RabbitMQ exige cert-manager, que je réserve à la cible ; Keycloak Operator demandait deux CRD de plus. Le broker sans opérateur est prêt en 10 s au lieu de 54, avec 64 Mi de moins, pour la même fiabilité. Les opérateurs servent la sauvegarde, la bascule et les mises à jour d'une base répliquée : c'est la cible. Une exception, kube-prometheus-stack, standard pour Prometheus et Grafana.

**Chiffres.** 10 s au lieu de 54 s ; environ 600 Mi pour la pile d'observabilité ([ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md)).

**À montrer.** [ADR 0008](../02-architecture/adr/0008-infrastructure-images-officielles.md).

**Limite à reconnaître.** Maintenance, sauvegarde et durcissement à la main : L3, L7, L17, L18. Cette pile ajoute un opérateur et des CRD : exception assumée.

### Q57. Pourquoi React et TypeScript alors que vous êtes plutôt Python ?

**Critères** : 2, 9.

**À dire.** Le front doit être crédible pour une vraie place de marché, et Collector recrutera : React avec TypeScript est la technologie la plus répandue. Une interface rendue côté serveur en Python aurait lié le front à un service, contre le découpage. C'est une compétence nouvelle pour moi, je l'assume, c'est l'objet de l'action de formation et j'ai réduit le périmètre à quatre pages.

**Chiffres.** 4 pages ; 62 tests Vitest ; 6 parcours Playwright ([ADR 0005](../02-architecture/adr/0005-react-typescript.md), [indicateurs](../01-qualite/indicateurs.md#mesures-du-06112026-phase-8)).

**À montrer.** [ADR 0005](../02-architecture/adr/0005-react-typescript.md) ; [captures](../../frontend/e2e/resultats/captures/).

**Limite à reconnaître.** La matrice note le front à niveau 1 pour moi ; la formation décrite porte sur Kubernetes et Helm, pas sur React.

### Q58. Pourquoi Traefik et pas ingress-nginx ?

**Critères** : 2, 8.

**À dire.** Traefik est fourni et maintenu par k3s : rien à installer. ingress-nginx est retiré : le SIG Network de Kubernetes a annoncé la fin de sa maintenance, sans correctifs de sécurité après mars 2026. Déployer un composant exposé et non maintenu serait une faute. Traefik gère l'Ingress standard et des middlewares utiles : `StripPrefix` dans le POC, en-têtes de sécurité, `RateLimit` pour la cible.

**Chiffres.** Traefik : 25 Mi mesurés ([index](../04-experimentations/README.md)).

**À montrer.** [ADR 0006](../02-architecture/adr/0006-kubernetes-local-k3d-argocd.md), « Traefik plutôt qu'ingress-nginx ».

**Limite à reconnaître.** Traefik ne génère pas `X-Request-ID` : les services le créent. Limitation de débit absente (L6, PA-18).

### Q59. Pourquoi avoir simplifié le POC ?

**Critères** : 2, 3.

**À dire.** La première version avait trois services, trois instances PostgreSQL, une outbox, des NetworkPolicies, Argo CD et cert-manager. Chacun se justifiait, la somme dépassait ce qu'un Lead Developer peut construire, tester et défendre en vingt minutes. Le risque principal pour la note n'est pas un composant absent, c'est une démo instable ou un choix qu'on ne sait pas expliquer. J'ai gardé le plus petit ensemble qui démontre chaque critère, et chaque retrait est une limite numérotée.

**Chiffres.** L1 à L25 ([ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md)).

**À montrer.** [ADR 0007](../02-architecture/adr/0007-simplification-perimetre-poc.md), tableau des retraits ; annexe A5 du [support](support.md).

**Limite à reconnaître.** Le POC s'éloigne de la cible ; la section 7 de `architecture-cible.md` les met en regard.

## Thème — Limites

### Q60. Quelles sont les limites les plus graves du POC ?

**Critères** : 2, 8.

**À dire.** Les cinq de priorité haute. L1 : pas de détection de fraude. L2 : un événement peut être perdu, faute d'outbox. L3 : une seule instance PostgreSQL. L4 : pas de NetworkPolicy, un pod compromis atteint la base, le broker et Keycloak. L5 : pas de BFF, un XSS actif peut appeler l'API avec le jeton. Ajoutons que le trafic interne n'est pas chiffré (L10) et que RabbitMQ tourne en root (L18). Chaque limite est rattachée à une action du plan.

**Chiffres.** L1 à L25 ; limites rattachées aux actions : L1 PA-27 et PA-36, L2 PA-54, L3 PA-23 et PA-53, L4 PA-30, L5 PA-56 ([plan, section 5.3](../06-securite/plan-remediation.md#53-limites-l1-à-l25-encore-ouvertes)).

**À montrer.** [Limites assumées](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc) ; annexe A5.

**Limite à reconnaître.** C'est la réponse elle-même.

### Q61. Ce POC est-il prêt pour la production ?

**Critères** : 2, 8, 10.

**À dire.** Non, et le plan le dit. Un POC démontre la faisabilité. La plateforme n'est ouverte à de vrais utilisateurs que lorsqu'aucun risque du registre n'est critique et que le paiement sécurisé, la protection des comptes vendeurs, l'anti-fraude, la protection des données et un test d'intrusion externe sont livrés : PA-39, PA-40, PA-41, PA-42 et PA-49. Sept risques sont critiques aujourd'hui, le plan les ramène à zéro en douze mois.

**Chiffres.** 7 critiques ; criticité de 650 à 298 ([plan, lecture rapide](../06-securite/plan-remediation.md#1-lecture-rapide)).

**À montrer.** [Synthèse projetable](../06-securite/plan-remediation.md) ; annexe A2.

**Limite à reconnaître.** Trois risques élevés restent acceptés par la direction, selon le plan.

### Q62. Pourquoi l'accessibilité et l'internationalisation sont-elles absentes ?

**Critères** : 3, 9.

**À dire.** Elles ne démontrent aucun critère de la grille : j'ai retenu des composants MUI qui respectent les patrons ARIA, mais aucun contrôle outillé. C'est la limite L14 : l'European Accessibility Act s'applique au commerce en ligne depuis juin 2025 et le RGAA vise la conformité. Je l'écarte du plan de sécurité parce qu'elle est sans effet de sécurité, mais pas du projet : la compétence RGAA est un écart de criticité haute dans la matrice, traité par le recrutement d'un·e UX/UI.

**Chiffres.** RGAA : requis 3, maximum de l'équipe 1 ([matrice](../05-competences/matrice.md)).

**À montrer.** [Architecture du POC](../02-architecture/architecture-poc.md#8-limites-assumées-du-poc), ligne L14 ; [recrutement UX/UI](../05-competences/matrice.md#5-recrutements-envisagés).

**Limite à reconnaître.** L14 : aucune action de sécurité ; recommandation : `react-i18next`, contrôle axe, audit RGAA.

## Thème — Organisation de l'équipe

### Q63. Quel est votre rôle de Lead Developer, concrètement ?

**Critères** : 9, 10.

**À dire.** Je supervise la conception, la qualité et la livraison. Concrètement : je décide l'architecture (ADR), je suis seul à fusionner sur `main`, après audit de la branche de la tâche ; j'exécute la validation d'acceptation, la charge et l'analyse de sécurité, dont je suis référent ; je tiens le plan de remédiation. Le Product Owner est l'un des deux dirigeants, anciens chefs de projet IT : aucun recrutement n'a été nécessaire pour ce rôle.

**Chiffres.** Aucun.

**À montrer.** [RACI](../01-qualite/processus-test.md#raci) ; [DevSecOps, étape Code](../01-qualite/devsecops.md).

**Limite à reconnaître.** La protection GitHub de `main` (pull request obligatoire, vérifications requises) est dans la cible, pas dans le POC (PA-16).

### Q64. Comment travaillez-vous avec les deux développeurs, et comment garantissez-vous la qualité d'une fusion ?

**Critères** : 7, 9.

**À dire.** Selon le RACI : les développeurs écrivent les tests et surveillent la CI, j'en rends compte ; je revois les tests. Une branche par tâche, un audit avant fusion, la CI à chaque push : un test en échec, un quality gate rouge ou un scan Trivy rouge bloque la publication. Les tests s'écrivent avec le code, aucune fonctionnalité n'est fusionnée sans test. Le risque d'équipe que je signale : le front repose sur Dev 2 seul.

**Chiffres.** Aucun.

**À montrer.** [RACI](../01-qualite/processus-test.md#raci) ; [matrice, hypothèses sur l'équipe](../05-competences/matrice.md#2-hypothèses-sur-léquipe).

**Limite à reconnaître.** Les profils des développeurs sont des hypothèses (Q46).

## Thème — Si la démonstration échoue

### Q65. Et si la démonstration plante ?

**Critères** : 10.

**À dire.** J'ai un plan de secours par étape, dans l'ordre : d'abord corriger sans commenter, puis les captures du parcours complet et la capture Grafana, puis la vidéo de secours. Pour chaque étape, le script de démonstration liste le problème possible et la réponse. J'ai répété la partie automatisable deux fois sur le cluster.

**Chiffres.** Démonstration : 5 min 10 prévues avec 50 s de marge, trois étapes de 1 min 20, 1 min 55 et 1 min 55 ([script](demo/script-demo.md)).

**À montrer.** [Plans de secours](demo/script-demo.md) de chaque étape ; [7 captures](../../frontend/e2e/resultats/captures/).

**Limite à reconnaître.** La saisie humaine de l'étape 2 est la seule durée estimée.

### Q66. Et si GitHub ou le réseau est inaccessible ?

**Critères** : 4, 10.

**À dire.** Le cluster est local et fonctionne hors ligne : application, Keycloak et Grafana tournent dessus. Seule l'étape 1 consulte GitHub pour le run de CI. Si GitHub est inaccessible, je montre le schéma du pipeline et la conformité écrite. Si le run du commit du jour n'est pas vert, je montre le run de référence et je redéploie le tag déjà sur le cluster, 19 secondes.

**Chiffres.** Run de référence 42219458020, 11 jobs verts ; redéploiement du tag existant : 19 s ([script, plan de secours étape 1](demo/script-demo.md)).

**À montrer.** [Schéma du pipeline](../01-qualite/img/pipeline-cicd.svg) ; [conformité](../01-qualite/conformite-pipeline.md).

**Limite à reconnaître.** Le déploiement d'un nouveau tag tire l'image sur GHCR : il exige le réseau.

### Q67. Et si le pic n'atteint pas 5 réplicas, ou si une requête échoue pendant la suppression du pod ?

**Critères** : 5, 10.

**À dire.** Je le dis tel quel. Si le bilan indique 4 réplicas, la montée dépend de la mesure du processeur : le protocole a mesuré 5 en 60 secondes, ici 4, et la suppression a eu lieu. Si une requête échoue, je donne le chiffre du bilan : le protocole en a mesuré zéro sur 533, mais un échec isolé serait cohérent avec les requêtes en cours sur le pod supprimé. Si Grafana est vide, je reste sur le terminal et j'ouvre la capture.

**Chiffres.** 0 échec sur 533 requêtes ; 4,9 s ([index](../04-experimentations/README.md)).

**À montrer.** [Plan de secours étape 3](demo/script-demo.md) ; [capture Grafana](../04-experimentations/05-charge-disponibilite/resultats/20261106-1132/grafana-pic-catalog-service.png).

**Limite à reconnaître.** Une seule suppression par exécution mesurée (ENF-16 conforme pour une suppression).

### Q68. Et si le déploiement échoue pendant la démonstration ?

**Critères** : 4, 5.

**À dire.** C'est une bonne démonstration : le script affiche « ÉCHEC : retour arrière » et remet la version précédente avec `helm rollback`. Je le dis, je vérifie que les pods sont `Running` et je continue. Le retour arrière d'une version défaillante a été mesuré au protocole 4, sans requête perdue. Si le déploiement traîne plus de 70 secondes, je passe à l'étape 2 : le cluster reste utilisable pendant le remplacement.

**Chiffres.** Retour arrière sans requête perdue ([index, protocole 4](../04-experimentations/README.md)).

**À montrer.** [Protocole 4](../04-experimentations/04-deploiement/protocole.md) ; [script, plan de secours étape 1](demo/script-demo.md).

**Limite à reconnaître.** Le retour arrière ne défait pas les migrations de base (L23, PA-38).
