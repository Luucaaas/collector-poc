#!/usr/bin/env python3
"""Vérifie le guide du jury et le README racine.

Contrôles :
  1. chaque lien relatif de `README.md` et de `docs/07-soutenance/*.md` pointe vers un fichier
     ou un dossier qui existe, et chaque ancre vers un titre qui existe ;
  2. les liens entrants vers le README (ancres citées par d'autres documents) existent ;
  3. chaque chiffre de la liste FIGURES figure dans le guide (ou le README) ET dans son
     fichier source ;
  4. quelques comptages recoupés dans le dépôt (tests d'acceptation, captures, schémas) ;
  5. le guide traite les 10 critères, et aucun chemin de dossier personnel n'apparaît ;
  6. le support de présentation (`support.md`) : liens et visuels existants, chiffres recoupés
     avec leur source (SUPPORT_FIGURES), minutage de 20 minutes, structure de chaque
     diapositive, correspondance diapositive et critère, annexes.

Bibliothèque standard seulement. À lancer depuis n'importe où :
    python3 -I docs/07-soutenance/verifier-guide.py
    python3 -I docs/07-soutenance/verifier-guide.py --root <copie du dépôt>   (essais)
Code de sortie : 0 si tout passe, 1 sinon.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if len(sys.argv) == 3 and sys.argv[1] == "--root":
    ROOT = Path(sys.argv[2]).resolve()

CHECKED_FILES = [
    ROOT / "README.md",
    ROOT / "docs/07-soutenance/README.md",
    ROOT / "docs/07-soutenance/guide-jury.md",
    ROOT / "docs/07-soutenance/support.md",
]

# Liens entrants : (document qui cite, ancre du README qu'il vise).
INCOMING_LINKS = [
    ("docs/04-experimentations/04-deploiement/protocole.md", "README.md#déployer-sur-le-cluster-local"),
]

# (description, texte tel qu'écrit dans le guide ou le README, texte tel qu'écrit dans le
# fichier source, fichier source). La comparaison ignore le gras, les accents graves et les
# espaces insécables.
FIGURES: list[tuple[str, str, str, str]] = [
    ('RabbitMQ : aucun message perdu', '0 message perdu sur 2 × 1 000', '0 message perdu sur 2 × 1 000', 'docs/04-experimentations/README.md'),
    ('RabbitMQ : retour à Ready', '10 s au lieu de 54 s', '10 s au lieu de 54 s', 'docs/04-experimentations/README.md'),
    ("Keycloak : cas d'autorisation", "15 cas d'autorisation conformes", "15 cas d'autorisation conformes", 'docs/04-experimentations/README.md'),
    ('Déploiement à froid', '199 s depuis rien', '199 s depuis rien', 'docs/04-experimentations/README.md'),
    ('Auto-réparation', '7,1 s', '7,1 s', 'docs/04-experimentations/04-deploiement/protocole.md'),
    ('Délai du README sur cluster neuf', '174 s', '174 s', 'docs/suivi/taches/P10-01.md'),
    ('Parcours du README sur cluster neuf', '6 sur 6 en 9,6 s', '6 sur 6 en 9,6 s', 'docs/suivi/taches/P10-01.md'),
    ('Mémoire des pods', '1 938 Mi', '1 938 Mi', 'docs/04-experimentations/README.md'),
    ('Limites assumées L1 à L25', 'L1 à L25', 'L1 à L25', 'docs/02-architecture/architecture-poc.md'),
    ("Critères d'acceptation passés", '17 sur 17', '17 sur 17', 'docs/01-qualite/indicateurs.md'),
    ('Exigences fonctionnelles', 'EF-01 à EF-36', 'EF-01 à EF-36', 'docs/03-backlog/README.md'),
    ('Exigences non fonctionnelles', 'ENF-01 à ENF-31', 'ENF-01 à ENF-31', 'docs/03-backlog/README.md'),
    ('Règles métier', 'RM-01 à RM-09', 'RM-01 à RM-09', 'docs/03-backlog/README.md'),
    ('Points des stories', '17 points', 'Total | | **17** | **17**', 'docs/03-backlog/user-stories.md'),
    ('Durée des 17 tests', 'en 9,84 s', 'en 9,84 s', 'docs/01-qualite/indicateurs.md'),
    ('Parcours Playwright', '6 parcours sur 6', '6 parcours sur 6', 'docs/01-qualite/indicateurs.md'),
    ('Run backend de la phase 8', '11 jobs verts', '11 jobs verts', 'docs/01-qualite/indicateurs.md'),
    ('Run backend, identifiant', '42219458020', '42219458020', 'docs/01-qualite/indicateurs.md'),
    ('Run frontend, identifiant', '42219458005', '42219458005', 'docs/01-qualite/indicateurs.md'),
    ('Run frontend, jobs', '2 jobs verts', '2 jobs verts', 'docs/01-qualite/indicateurs.md'),
    ('Premier run de référence, durée', '5 min 47 s', 'Durée totale : 5 min 47 s', 'docs/01-qualite/conformite-pipeline.md'),
    ('Premier run de référence, jobs', '9 jobs verts', '9 jobs verts', 'docs/01-qualite/conformite-pipeline.md'),
    ('HPA de 2 à 5 réplicas', '2 à 5 réplicas prêts en 60 s', '2 à 5 réplicas prêts en 60 s', 'docs/04-experimentations/README.md'),
    ('Pod remplacé', 'remplacé en 4,9 s', 'pod supprimé remplacé en 4,9 s', 'docs/04-experimentations/README.md'),
    ('Aucun échec pendant la suppression', '0 échec sur 533 requêtes', '0 échec sur 533 requêtes', 'docs/04-experimentations/README.md'),
    ('Retour à 2 pods', '325 s', 'retour à 2 pods en 325 s', 'docs/04-experimentations/README.md'),
    ('Aucune 5xx sur le pic', '0 réponse 5xx sur 20 235 requêtes', '0 réponse 5xx sur 20 235 requêtes', 'docs/01-qualite/indicateurs.md'),
    ('Couverture catalog', '98,45 %', '98,45 %', 'docs/01-qualite/indicateurs.md'),
    ('Couverture notification', '97,66 %', '97,66 %', 'docs/01-qualite/indicateurs.md'),
    ('Dette SonarCloud', 'dette de 0 min', 'dette **0 min**', 'docs/01-qualite/indicateurs.md'),
    ('Duplication SonarCloud', 'duplication de 0,0 %', 'duplication **0,0 %**', 'docs/01-qualite/indicateurs.md'),
    ('p95 de lecture', 'p95 de 21 ms en lecture', 'p95 de `GET /articles` : **21 ms**', 'docs/01-qualite/indicateurs.md'),
    ('p95 de publication', 'de 23 ms en publication', 'p95 de `POST /articles` : **23 ms**', 'docs/01-qualite/indicateurs.md'),
    ('5xx à 50 utilisateurs', '0 sur 6 564 requêtes', '0 sur 6 564 requêtes', 'docs/01-qualite/indicateurs.md'),
    ('Vulnérabilités avec correctif', '0 vulnérabilité CRITICAL ou HIGH avec correctif', '0 vulnérabilité CRITICAL ou HIGH avec correctif', 'docs/01-qualite/indicateurs.md'),
    ('Duplication entre services', '34,6 %', '34,6 %', 'docs/01-qualite/indicateurs.md'),
    ('Lignes dupliquées', '531 lignes', '531 lignes', 'docs/01-qualite/indicateurs.md'),
    ('Erreurs mypy dans les tests', '15 erreurs', '15 erreurs', 'docs/01-qualite/indicateurs.md'),
    ('Bundle du front', '609,4 Ko', '609,4 Ko', 'docs/01-qualite/indicateurs.md'),
    ('Résultat de charge', 'tous les seuils respectés', 'Tous les seuils sont respectés', 'tests/load/resultats/20261106-1106/resume.md'),
    ('Tests catalog', '289 passed', '289 passed', 'docs/01-qualite/indicateurs.md'),
    ('Tests notification', '203 passed', '203 passed', 'docs/01-qualite/indicateurs.md'),
    ("Tests d'acceptation", '17 passed', '17 passed', 'docs/01-qualite/indicateurs.md'),
    ('Tests catalog relancés le 11/11', '294 passed', '294 passed', 'docs/suivi/taches/P10-01.md'),
    ('Couverture catalog relancée le 11/11', '98,66 %', '98,66 %', 'docs/suivi/taches/P10-01.md'),
    ('Tests Vitest', '62 tests passés', '62 tests passés', 'docs/01-qualite/indicateurs.md'),
    ('Décision Playwright hors CI', 'décision du 31/10/2026', 'décision du 31/10/2026', 'docs/01-qualite/processus-test.md'),
    ('Registre des risques', 'registre de 62 risques', 'registre de 62 risques', 'docs/06-securite/plan-remediation.md'),
    ('Risques critiques', '7 critiques et 30 élevés', '7 critiques, 30 élevés', 'docs/06-securite/plan-remediation.md'),
    ('Actions du plan', '**58 actions**', '**58 actions**', 'docs/06-securite/plan-remediation.md'),
    ('Charge du plan', '225,5 j', '225,5 j', 'docs/06-securite/plan-remediation.md'),
    ('Criticité cumulée', "de 650 aujourd'hui à 298", "de 650 aujourd'hui à 298", 'docs/06-securite/plan-remediation.md'),
    ('Bonnes pratiques prouvées', 'dix-sept', 'dix-sept', 'docs/06-securite/plan-remediation.md'),
    ("Constats de l'audit", '25 constats qualifiés', '25 constats qualifiés', 'docs/06-securite/README.md'),
    ('Lignes avec correctif avant et après', '11 lignes par service avant, 0 après', 'Lignes avec correctif | 11 | **0**', 'docs/06-securite/rapport-scans.md'),
    ('Lignes sans correctif', '**201 (89 CVE)**', '**201 (89 CVE)**', 'docs/06-securite/rapport-scans.md'),
    ('Durée de la formation', '28 heures', 'Durée totale : **28 heures**', 'docs/05-competences/plan-formation.md'),
    ('Modules de la formation', 'six modules', 'Six modules', 'docs/05-competences/plan-formation.md'),
    ('Durée en semaines', '6 semaines', 'réparties sur **6 semaines**', 'docs/05-competences/plan-formation.md'),
    ('Recrutements', 'trois profils', 'Trois profils', 'docs/05-competences/matrice.md'),
]

# Chiffres du support : (diapositive, description, texte tel qu'écrit dans le tableau « Chiffres et
# sources » de cette diapositive de support.md, texte tel qu'écrit
# dans le fichier source, fichier source). Même normalisation que FIGURES.
SUPPORT_FIGURES: list[tuple[str, str, str, str, str]] = [
    ('1', 'Commission', 'Commission de 5 %', 'commission de 5 %', 'docs/03-backlog/exigences.md'),
    ('1', 'Stories, points, critères', "5 user stories, 17 points, 17 critères d'acceptation", 'Total | | **17** | **17**', 'docs/03-backlog/user-stories.md'),
    ('2', 'Limites', 'L1 à L25', 'L1 à L25', 'docs/02-architecture/architecture-poc.md'),
    ('14', 'Limites', 'L1 à L25', 'L1 à L25', 'docs/02-architecture/architecture-poc.md'),
    ('3', 'Message relivré', '1 message relivré sur 1 000', '1 message relivré sur 1 000', 'docs/04-experimentations/README.md'),
    ('3', 'Aucun appel HTTP entre services', 'Aucun appel HTTP entre services', 'Aucun appel HTTP entre services', 'CLAUDE.md'),
    ('4', 'Jeton de 5 minutes', "Jeton d'accès de 5 minutes", "Jeton d'accès de 5 min", 'docs/02-architecture/architecture-poc.md'),
    ('4', 'HPA', 'HPA de 2 à 5 réplicas à 70 % de CPU', 'de 2 à 5 réplicas à 70 % de CPU', 'docs/02-architecture/architecture-poc.md'),
    ('4', 'Cluster', '1 server + 2 agents', '1 server + 2 agents', 'docs/02-architecture/architecture-poc.md'),
    ('5', 'Messages perdus', '0 message perdu sur 2 × 1 000', '0 message perdu sur 2 × 1 000', 'docs/04-experimentations/README.md'),
    ('5', 'Retour à Ready', '10 s au lieu de 54 s', '10 s au lieu de 54 s', 'docs/04-experimentations/README.md'),
    ('4', 'Cas Keycloak', "15 cas d'autorisation conformes", "15 cas d'autorisation conformes", 'docs/04-experimentations/README.md'),
    ('5', 'Cas Keycloak', "15 cas d'autorisation conformes", "15 cas d'autorisation conformes", 'docs/04-experimentations/README.md'),
    ('5', 'Mémoire observabilité', 'environ 600 Mi', 'environ 600 Mi', 'docs/04-experimentations/README.md'),
    ('5', 'Déploiement à froid', '199 s depuis rien', '199 s depuis rien', 'docs/04-experimentations/README.md'),
    ('14', 'Déploiement à froid', '199 s depuis rien', '199 s depuis rien', 'docs/04-experimentations/README.md'),
    ('5', 'HPA 2 à 5', '2 à 5 réplicas prêts en 60 s', '2 à 5 réplicas prêts en 60 s', 'docs/04-experimentations/README.md'),
    ('8', 'HPA 2 à 5', '2 à 5 réplicas prêts en 60 s', '2 à 5 réplicas prêts en 60 s', 'docs/04-experimentations/README.md'),
    ('6', 'Acceptation', "17 critères d'acceptation sur 17", '17 sur 17', 'docs/01-qualite/indicateurs.md'),
    ('6', 'Durée acceptation', 'en 9,84 s', 'en 9,84 s', 'docs/01-qualite/indicateurs.md'),
    ('6', 'Playwright', '6 parcours Playwright sur 6', '6 parcours sur 6', 'docs/01-qualite/indicateurs.md'),
    ('10', 'Playwright', '6 parcours sur 6 (Playwright)', '6 parcours sur 6', 'docs/01-qualite/indicateurs.md'),
    ('7', 'Run backend', '11 jobs verts, run 42219458020', '11 jobs verts', 'docs/01-qualite/indicateurs.md'),
    ('7', 'Run backend, identifiant', '42219458020', '42219458020', 'docs/01-qualite/indicateurs.md'),
    ('7', 'Premier run, durée', '5 min 47 s', 'Durée totale : 5 min 47 s', 'docs/01-qualite/conformite-pipeline.md'),
    ('7', 'Premier run, jobs', '9 jobs verts', '9 jobs verts', 'docs/01-qualite/conformite-pipeline.md'),
    ('7', 'Run de la démonstration', 'Run 43064777792 : 8 min 37 s', '8 min 37 s pour le run 43064777792', 'docs/07-soutenance/demo/script-demo.md'),
    ('7', 'Jobs par service', '6 jobs par service', '6 jobs', 'docs/01-qualite/cicd.md'),
    ('D', 'Étape 1 de la démonstration', '1 min 20', '1 min 20', 'docs/07-soutenance/demo/script-demo.md'),
    ('D', 'Étapes 2 et 3 de la démonstration', '1 min 55', '1 min 55', 'docs/07-soutenance/demo/script-demo.md'),
    ('D', 'Total de la démonstration', 'total 5 min 10 avec 50 s de marge', '5 min 10', 'docs/07-soutenance/demo/script-demo.md'),
    ('D', 'Marge', '50 s de marge', 'marge de 50 s', 'docs/07-soutenance/demo/script-demo.md'),
    ('8', "Réserve de l'ADR 0006", "sous réserve de la validation de l'intervenant", "sous réserve de la validation de l'intervenant", 'docs/02-architecture/adr/0006-kubernetes-local-k3d-argocd.md'),
    ('8', 'Repli OKE', 'Oracle OKE Always Free', 'Oracle OKE Always Free', 'docs/02-architecture/adr/0006-kubernetes-local-k3d-argocd.md'),
    ('8', 'Pod remplacé', 'Pod remplacé en 4,9 s', 'pod supprimé remplacé en 4,9 s', 'docs/04-experimentations/README.md'),
    ('8', 'Échecs pendant la suppression', '0 échec sur 533 requêtes', '0 échec sur 533 requêtes', 'docs/04-experimentations/README.md'),
    ('10', 'Échecs pendant la suppression', '0 échec sur 533 requêtes', '0 échec sur 533 requêtes', 'docs/04-experimentations/README.md'),
    ('8', 'Retour à 2 pods', 'Retour à 2 pods en 325 s', 'retour à 2 pods en 325 s', 'docs/04-experimentations/README.md'),
    ('8', 'Aucune 5xx sur le pic', '0 réponse 5xx sur 20 235 requêtes', '0 réponse 5xx sur 20 235 requêtes', 'docs/01-qualite/indicateurs.md'),
    ('8', 'Auto-réparation', 'Auto-réparation sans charge : 7,1 s', '7,1 s', 'docs/04-experimentations/04-deploiement/protocole.md'),
    ('9', 'Couverture catalog', '98,45 %', '98,45 %', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Couverture notification', '97,66 %', '97,66 %', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Dette Sonar', 'Dette de 0 min', 'dette **0 min**', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Duplication Sonar', 'duplication de 0,0 %', 'duplication **0,0 %**', 'docs/01-qualite/indicateurs.md'),
    ('9', 'p95 de lecture', 'p95 de 21 ms', 'p95 de `GET /articles` : **21 ms**', 'docs/01-qualite/indicateurs.md'),
    ('9', 'p95 de publication', 'de 23 ms en publication', 'p95 de `POST /articles` : **23 ms**', 'docs/01-qualite/indicateurs.md'),
    ('9', '5xx à 50 utilisateurs', '0 sur 6 564 requêtes', '0 sur 6 564 requêtes', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Vulnérabilités avec correctif', '0 vulnérabilité CRITICAL ou HIGH avec correctif', '0 vulnérabilité CRITICAL ou HIGH avec correctif', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Lignes dupliquées', '531 lignes dupliquées (34,6 %)', '531 lignes', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Part dupliquée', '34,6 %', '34,6 %', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Erreurs mypy', '15 erreurs mypy', '15 erreurs', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Bundle', '609,4 Ko', '609,4 Ko', 'docs/01-qualite/indicateurs.md'),
    ('10', 'Tests catalog', '289 passed', '289 passed', 'docs/01-qualite/indicateurs.md'),
    ('10', 'Tests notification', '203 passed', '203 passed', 'docs/01-qualite/indicateurs.md'),
    ('10', "Tests d'acceptation", '17 passed', '17 passed', 'docs/01-qualite/indicateurs.md'),
    ('10', 'Tests Vitest', '62 tests passés', '62 tests passés', 'docs/01-qualite/indicateurs.md'),
    ('10', 'Charge', 'Tous les seuils sont respectés', 'Tous les seuils sont respectés', 'tests/load/resultats/20261106-1106/resume.md'),
    ('10', 'Tests relancés le 11/11', '294 passed', '294 passed', 'docs/suivi/taches/P10-01.md'),
    ('14', 'Délai du README', '174 s', '174 s', 'docs/suivi/taches/P10-01.md'),
    ('11', 'Bonnes pratiques', 'Dix-sept bonnes pratiques', 'dix-sept', 'docs/06-securite/plan-remediation.md'),
    ('11', 'Lignes avec correctif', '11 lignes de rapport par service avec correctif avant les corrections, 0 après', 'Lignes avec correctif | 11 | **0**', 'docs/06-securite/rapport-scans.md'),
    ('11', 'ZAP', '0 constat de niveau moyen ou élevé', '0 constat de niveau moyen ou élevé', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Risques', '62 risques', '62 risques', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Critiques et élevés', '7 critiques, 30 élevés', '7 critiques, 30 élevés', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Actions', '58 actions', '**58 actions**', 'docs/06-securite/plan-remediation.md'),
    ('14', 'Actions', '58 actions', '**58 actions**', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Charge du plan', '225,5 j', '225,5 j', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Court terme', 'Court terme (0 à 3 mois) : 29 actions, 64 j', '| Court terme (0 à 3 mois) | 29 | 64 j |', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Moyen terme', 'moyen terme (3 à 6 mois) : 21 actions, 97,5 j', '| Moyen terme (3 à 6 mois) | 21 | 97,5 j |', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Long terme', 'long terme (6 à 12 mois et plus) : 8 actions, 64 j', '| Long terme (6 à 12 mois et plus) | 8 | 64 j |', 'docs/06-securite/plan-remediation.md'),
    ('12', 'Criticité cumulée', "de 650 aujourd'hui à 298", "de 650 aujourd'hui à 298", 'docs/06-securite/plan-remediation.md'),
    ('12', 'Risques critiques à 12 mois', 'risques critiques de 7 à 0', 'risques critiques de 7 à 0', 'docs/06-securite/plan-remediation.md'),
    ('13', 'Recrutements', 'Trois recrutements envisagés', 'Trois profils', 'docs/05-competences/matrice.md'),
    ('13', 'Formation', '28 heures', 'Durée totale : **28 heures**', 'docs/05-competences/plan-formation.md'),
    ('13', 'Modules', 'six modules', 'Six modules', 'docs/05-competences/plan-formation.md'),
    ('13', 'Semaines', '6 semaines', 'réparties sur **6 semaines**', 'docs/05-competences/plan-formation.md'),
    ('4', 'Trafic interne non chiffré', 'limite L10 (chiffrement du trafic interne, mTLS)', 'Chiffrement du trafic interne (mTLS)', 'docs/02-architecture/architecture-poc.md'),
    ('5', 'Kafka surdimensionné', 'surdimensionné pour la V1, empreinte mémoire JVM', 'Surdimensionné pour la V1', 'docs/02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md'),
    ('5', 'Kafka JVM', 'empreinte mémoire JVM', '(JVM)', 'docs/02-architecture/adr/0003-rabbitmq-plutot-que-kafka.md'),
    ('8', 'Protocole 5 : 200 utilisateurs', '(200 utilisateurs)', '200 utilisateurs', 'docs/04-experimentations/README.md'),
    ('8', 'Démonstration : 300 utilisateurs', '300 utilisateurs simulés', '300 utilisateurs simulés', 'docs/07-soutenance/demo/script-demo.md'),
    ('9', 'Règle absente de RM-01', 'règle absente de RM-01', 'absente de RM-01', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Plafond de frais de port', '1 000 000 €', '1 000 000 €', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Commit des images', '`22364bc`', '22364bc', 'docs/01-qualite/indicateurs.md'),
    ('9', 'Commit de la charge', '`9d2c96e`', '9d2c96e', 'docs/01-qualite/indicateurs.md'),
    ('11', 'MFA au plan', 'PA-02 et PA-40', 'PA-40', 'docs/06-securite/plan-remediation.md'),
    ('11', 'Limite L13', 'L13', 'Semgrep, Bandit, pip-audit, Gitleaks', 'docs/02-architecture/architecture-poc.md'),
    ('11', 'Limite L17', 'L17 et L18', 'L18 | Broker RabbitMQ démarré en root', 'docs/02-architecture/architecture-poc.md'),
    ('13', '26 compétences', '26 compétences cartographiées', 'Matrice', 'docs/05-competences/matrice.md'),
    ('14', 'Plan en 58 actions', '58 actions', '**58 actions**', 'docs/06-securite/plan-remediation.md'),
]


def normalize(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    text = text.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", text)


def github_slug(title: str) -> str:
    """Ancre GitHub d'un titre : minuscules, ponctuation retirée, espaces en tirets."""
    title = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", title)
    title = title.replace("`", "").replace("*", "").strip().lower()
    title = re.sub(r"[^\w\- ]", "", title, flags=re.UNICODE)
    return title.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    """Ancres d'un fichier Markdown (hors blocs de code), avec le suffixe -1, -2 des doublons."""
    seen: dict[str, int] = {}
    result: set[str] = set()
    in_code = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("```"):
            in_code = not in_code
            continue
        match = None if in_code else re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if match:
            base = github_slug(match.group(1))
            count = seen.get(base, 0)
            result.add(base if count == 0 else f"{base}-{count}")
            seen[base] = count + 1
    return result


def links(path: Path) -> list[tuple[int, str]]:
    """Liens Markdown [texte](cible) hors blocs de code, avec leur numéro de ligne."""
    found: list[tuple[int, str]] = []
    in_code = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        without_code = re.sub(r"`[^`]*`", "", line)
        for match in re.finditer(r"\]\(([^)\s]+)\)", without_code):
            found.append((number, match.group(1)))
    return found


def check_links(failures: list[str]) -> int:
    total = 0
    for file in CHECKED_FILES:
        if not file.exists():
            failures.append(f"fichier absent : {file.relative_to(ROOT)}")
            continue
        for number, target in links(file):
            if re.match(r"^[a-z]+:", target):  # http:, https:, mailto:
                continue
            total += 1
            path_part, _, anchor = target.partition("#")
            destination = file if path_part == "" else (file.parent / path_part).resolve()
            name = f"{file.relative_to(ROOT)}:{number}"
            if not destination.exists():
                failures.append(f"{name} : lien cassé vers {target}")
                continue
            if anchor and destination.suffix == ".md" and anchor not in anchors(destination):
                failures.append(f"{name} : ancre introuvable #{anchor} dans {destination.relative_to(ROOT)}")
    return total


def check_incoming_links(failures: list[str]) -> int:
    for document, target in INCOMING_LINKS:
        path = ROOT / document
        readme_anchor = target.partition("#")[2]
        if not path.exists():
            failures.append(f"lien entrant : document absent {document}")
            continue
        if target not in path.read_text(encoding="utf-8"):
            failures.append(f"lien entrant : {document} ne cite plus {target}")
        if readme_anchor not in anchors(ROOT / "README.md"):
            failures.append(f"lien entrant : le README n'a plus l'ancre #{readme_anchor} (citée par {document})")
    return len(INCOMING_LINKS)


def check_figures(failures: list[str]) -> int:
    guide_text = normalize(
        (ROOT / "docs/07-soutenance/guide-jury.md").read_text(encoding="utf-8")
        + (ROOT / "README.md").read_text(encoding="utf-8")
    )
    for description, in_guide, in_source, source in FIGURES:
        if normalize(in_guide) not in guide_text:
            failures.append(f"chiffre « {in_guide} » ({description}) absent du guide et du README")
        path = ROOT / source
        if not path.exists():
            failures.append(f"chiffre « {in_source} » ({description}) : source absente {source}")
        elif normalize(in_source) not in normalize(path.read_text(encoding="utf-8")):
            failures.append(f"chiffre « {in_source} » ({description}) introuvable dans {source}")
    return len(FIGURES)


def check_counts(failures: list[str]) -> int:
    guide = (ROOT / "docs/07-soutenance/guide-jury.md").read_text(encoding="utf-8")
    checks = 0

    def expect(description: str, got: int, wanted: int) -> None:
        nonlocal checks
        checks += 1
        if got != wanted:
            failures.append(f"{description} : {got} trouvé(s), {wanted} attendu(s)")

    tests = sum(
        len(re.findall(r"^(?:async )?def test_us\d\d_ca\d_", f.read_text(encoding="utf-8"), re.M))
        for f in (ROOT / "tests/acceptance").glob("test_us*.py")
    )
    expect("tests d'acceptation (fonctions test_usXX_caY_)", tests, 17)
    expect("captures d'écran du parcours", len(list((ROOT / "frontend/e2e/resultats/captures").glob("*.png"))), 7)
    section10 = guide.split("## 10. Qualité de la présentation", 1)[1].split("**Démonstration.**", 1)[0]
    schemas = {m.group(1) for m in re.finditer(r"\]\(([^)]+\.svg)\)", section10)}
    expect("schémas SVG cités à la section 10 (le guide annonce 14)", len(schemas), 14)
    expect("sections de critères du guide", len(re.findall(r"^## (\d{1,2})\. ", guide, re.M)), 10)
    return checks


SUPPORT = ROOT / "docs/07-soutenance/support.md"
SLIDE_LABELS = ["Minutes", "Message clé", "Contenu", "Visuel", "Chiffres et sources", "Critères", "Notes orales", "Transition"]


def to_seconds(text: str) -> int:
    minutes, seconds = text.split(":")
    return int(minutes) * 60 + int(seconds)


def sections(text: str) -> dict[str, str]:
    """Sections « ### titre » du support, hors blocs de code, dans l'ordre."""
    found: dict[str, str] = {}
    title = None
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("### "):
            if title is not None:
                found[title] = "\n".join(buffer)
            title, buffer = line[4:].strip(), []
        elif line.startswith("## "):
            if title is not None:
                found[title] = "\n".join(buffer)
            title, buffer = None, []
        elif title is not None:
            buffer.append(line)
    if title is not None:
        found[title] = "\n".join(buffer)
    return found


def field(body: str, label: str) -> str:
    """Texte d'un champ « **label** » jusqu'au champ suivant."""
    match = re.search(r"\*\*" + re.escape(label) + r"\*\*[^\n]*\n?(.*?)(?=\n\*\*[A-Za-zÀ-ÿ' ]+\*\*|\Z)", body, re.S)
    first = re.search(r"\*\*" + re.escape(label) + r"\*\*([^\n]*)", body)
    return ((first.group(1) if first else "") + "\n" + (match.group(1) if match else "")).strip()


def check_support_figures(failures: list[str]) -> int:
    """Chaque chiffre est cherché dans le tableau « Chiffres et sources » de SA diapositive."""
    all_sections = sections(SUPPORT.read_text(encoding="utf-8"))
    blocks: dict[str, str] = {}
    for title, body in all_sections.items():
        match = re.match(r"Diapositive (\d+) ", title)
        if match:
            blocks[match.group(1)] = normalize(field(body, "Chiffres et sources"))
        elif title.startswith("Démonstration en direct"):
            blocks["D"] = normalize(field(body, "Chiffres et sources"))
    for slide, description, in_support, in_source, source in SUPPORT_FIGURES:
        if normalize(in_support) not in blocks.get(slide, ""):
            failures.append(f"support, diapositive {slide} : chiffre « {in_support} » ({description}) absent de son tableau « Chiffres et sources »")
        path = ROOT / source
        if not path.exists():
            failures.append(f"support : source absente {source} ({description})")
        elif normalize(in_source) not in normalize(path.read_text(encoding="utf-8")):
            failures.append(f"support : « {in_source} » ({description}) introuvable dans {source}")
    return len(SUPPORT_FIGURES)


def check_support_structure(failures: list[str]) -> int:
    text = SUPPORT.read_text(encoding="utf-8")
    checks = 0
    all_sections = sections(text)

    # Plan minuté : tableau « N° | Titre | Durée | Cumul ».
    plan = text.split("## Plan minuté", 1)[1].split("###", 1)[0]
    rows = re.findall(r"^\| (\d+|D) \| (.+?) \| (\d+:\d\d) \| (\d+:\d\d) \|$", plan, re.M)
    durations: dict[str, int] = {}
    total = 0
    for number, title, duration, cumulative in rows:
        total += to_seconds(duration)
        durations[number] = to_seconds(duration)
        checks += 1
        if to_seconds(cumulative) != total:
            failures.append(f"plan minuté : cumul de la ligne {number} = {cumulative}, attendu {total // 60}:{total % 60:02d}")
    checks += 1
    if total != 20 * 60:
        failures.append(f"plan minuté : total {total // 60}:{total % 60:02d}, attendu 20:00")
    slide_numbers = [n for n, *_ in rows if n != "D"]
    checks += 1
    if not 14 <= len(slide_numbers) <= 18:
        failures.append(f"plan minuté : {len(slide_numbers)} diapositives hors démonstration, 14 à 18 attendues")
    checks += 1
    if durations.get("D") != 6 * 60:
        failures.append("plan minuté : la démonstration doit durer 6:00")
    checks += 1
    if [int(n) for n in slide_numbers] != list(range(1, len(slide_numbers) + 1)):
        failures.append("plan minuté : numéros de diapositives non consécutifs")

    # Chaque diapositive : champs, contenu, notes, chiffres sourcés.
    slide_criteria: dict[str, set[int]] = {}
    for number in [*slide_numbers, "D"]:
        key = next((t for t in all_sections if (t.startswith(f"Diapositive {number} ") if number != "D" else t.startswith("Démonstration en direct"))), None)
        checks += 1
        if key is None:
            failures.append(f"diapositive {number} : section absente")
            continue
        body = all_sections[key]
        for label in SLIDE_LABELS:
            checks += 1
            if f"**{label}**" not in body:
                failures.append(f"diapositive {number} : champ « {label} » absent")
        minutes = re.search(r"\*\*Minutes\*\* : (\d+:\d\d)", body)
        checks += 1
        if not minutes or to_seconds(minutes.group(1)) != durations.get(number):
            failures.append(f"diapositive {number} : durée du champ Minutes différente de celle du plan")
        content = field(body, "Contenu")
        bullets = len(re.findall(r"^- ", content, re.M))
        table_rows = max(0, len(re.findall(r"^\|", content, re.M)) - 2)
        checks += 1
        if bullets > 4 or table_rows > 4:
            failures.append(f"diapositive {number} : contenu trop long ({bullets} puces, {table_rows} lignes de tableau, 4 au plus)")
        visual = field(body, "Visuel")
        checks += 1
        if "](" not in visual and "à dessiner" not in visual.lower():
            failures.append(f"diapositive {number} : visuel sans lien ni mention « à dessiner »")
        figures_block = field(body, "Chiffres et sources")
        data_rows = [r for r in figures_block.splitlines() if r.startswith("|")][2:]
        checks += 1
        if not data_rows:
            failures.append(f"diapositive {number} : aucun chiffre sourcé")
        for row in data_rows:
            checks += 1
            if "](" not in row.split("|")[-2]:
                failures.append(f"diapositive {number} : chiffre sans lien de source : {row[:70]}")
        notes = re.sub(r"\s+", " ", field(body, "Notes orales"))
        words = len(notes.split())
        checks += 1
        if number != "D" and not 100 <= words <= 160:
            failures.append(f"diapositive {number} : notes orales de {words} mots (100 à 160 attendus, soit 45 à 80 s)")
        criteria_text = re.sub(r"\([^)]*\)", "", field(body, "Critères"))
        slide_criteria[number] = {int(c) for c in re.findall(r"\b(10|[1-9])\b", criteria_text)}

    # Correspondance diapositive et critère.
    table = text.split("## Correspondance diapositive et critère", 1)[1].split("\n## ", 1)[0]
    covered: set[int] = set()
    for row in re.findall(r"^\| (\d+)\. [^|]+\| ([^|]+) \|", table, re.M):
        criterion = int(row[0])
        cells = re.sub(r"annexes? [A-Z]\d( et [A-Z]\d)*", "", re.sub(r"\([^)]*\)", "", row[1]))
        cited = re.findall(r"\b\d{1,2}\b", cells)
        if "démonstration" in cells.lower():
            cited.append("D")
        covered.add(criterion)
        checks += 1
        if not cited:
            failures.append(f"correspondance : critère {criterion} sans diapositive")
        for slide in cited:
            checks += 1
            if criterion not in slide_criteria.get(slide, set()):
                failures.append(f"correspondance : le critère {criterion} cite la diapositive {slide}, qui ne le déclare pas")
    checks += 1
    if covered != set(range(1, 11)):
        failures.append(f"correspondance : critères présents {sorted(covered)}, 1 à 10 attendus")

    # Annexes : 4 à 6, chacune avec une source liée.
    annexes = {t: b for t, b in all_sections.items() if t.startswith("Annexe ")}
    checks += 1
    if not 4 <= len(annexes) <= 6:
        failures.append(f"annexes : {len(annexes)} trouvées, 4 à 6 attendues")
    for title, body in annexes.items():
        checks += 1
        if not re.search(r"\*\*Source\*\* : .*\]\(", body):
            failures.append(f"{title.split(' — ')[0]} : source sans lien")
    return checks


def check_support_counts(failures: list[str]) -> int:
    """Comptages annoncés dans le support : 26 compétences, 10 types de tests formalisés."""
    text = SUPPORT.read_text(encoding="utf-8")
    matrix = (ROOT / "docs/05-competences/matrice.md").read_text(encoding="utf-8")
    section = matrix.split("## 3. Matrice", 1)[1].split("## 4.", 1)[0]
    rows = [r for r in section.splitlines() if r.startswith("|")][2:]
    if len(rows) != 26 or "26 compétences cartographiées" not in text:
        failures.append(f"support : la matrice compte {len(rows)} compétences, le support en annonce 26")
    tests = (ROOT / "docs/01-qualite/processus-test.md").read_text(encoding="utf-8")
    table = tests.split("### Tableau des types de tests", 1)[1].split("\n###", 1)[0]
    types = [r for r in table.splitlines() if r.startswith("|")][2:]
    if len(types) != 10 or "Dix types de tests formalisés" not in text:
        failures.append(f"support : le processus de test compte {len(types)} types, le support en annonce 10")
    return 2


def check_privacy(failures: list[str]) -> None:
    pattern = "/" + "Users" + "/"  # écrit en deux morceaux pour ne pas se contenir lui-même
    for file in CHECKED_FILES:
        if file.exists() and pattern in file.read_text(encoding="utf-8"):
            failures.append(f"{file.relative_to(ROOT)} : chemin personnel ({pattern}) présent")


def main() -> int:
    failures: list[str] = []
    n_links = check_links(failures)
    n_incoming = check_incoming_links(failures)
    n_figures = check_figures(failures)
    n_counts = check_counts(failures)
    n_support = check_support_figures(failures)
    n_structure = check_support_structure(failures) + check_support_counts(failures)
    check_privacy(failures)
    print(f"Liens relatifs contrôlés : {n_links}")
    print(f"Liens entrants contrôlés : {n_incoming}")
    print(f"Chiffres recoupés (guide et source) : {n_figures}")
    print(f"Comptages recoupés dans le dépôt : {n_counts}")
    print(f"Support : chiffres recoupés avec leur source : {n_support}")
    print(f"Support : contrôles de structure (minutage, champs, critères, annexes) : {n_structure}")
    if failures:
        print(f"\n{len(failures)} échec(s) :")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nTout est conforme : 0 échec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
