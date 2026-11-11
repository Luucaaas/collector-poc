#!/usr/bin/env python3
"""Vérifie le guide du jury et le README racine.

Contrôles :
  1. chaque lien relatif de `README.md` et de `docs/07-soutenance/*.md` pointe vers un fichier
     ou un dossier qui existe, et chaque ancre vers un titre qui existe ;
  2. les liens entrants vers le README (ancres citées par d'autres documents) existent ;
  3. chaque chiffre de la liste FIGURES figure dans le guide (ou le README) ET dans son
     fichier source ;
  4. quelques comptages recoupés dans le dépôt (tests d'acceptation, captures, schémas) ;
  5. le guide traite les 10 critères, et aucun chemin de dossier personnel n'apparaît.

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
    check_privacy(failures)
    print(f"Liens relatifs contrôlés : {n_links}")
    print(f"Liens entrants contrôlés : {n_incoming}")
    print(f"Chiffres recoupés (guide et source) : {n_figures}")
    print(f"Comptages recoupés dans le dépôt : {n_counts}")
    if failures:
        print(f"\n{len(failures)} échec(s) :")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("\nTout est conforme : 0 échec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
