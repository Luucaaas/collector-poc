#!/usr/bin/env python3
# ruff: noqa: E501  (outil de documentation : phrases françaises longues, hors du lint des services)
"""Vérifie la cohérence du plan de remédiation (plan-remediation.md) avec le registre de risques.

Bibliothèque standard seulement. Code de sortie 0 si tout est conforme, 1 sinon.

Ce que le script contrôle, et ce qu'il ne prouve pas. Ce sont des contrôles de **cohérence et de présence** :
chaque chiffre, lien, fichier ou ligne cité existe et concorde avec le registre ; un échantillon d'assertions
vérifie qu'un motif attendu figure à la ligne citée. Il ne prouve **pas** que la mesure citée fonctionne (c'est
le rôle des tests, des scans et des exécutions auxquels les preuves renvoient), ni que l'effort ou le coût
d'une action est juste.

Contrôles :
  1. chaque risque R-01 à R-62 du registre apparaît dans le plan, avec les mêmes notes (impact, probabilité) ;
  2. chaque risque critique ou élevé a au moins une action, et chaque action citée existe ;
  3. la liste des actions de chaque risque est celle que donnent les tableaux d'actions ;
  4. le résiduel d'une action (final ou palier) est celui du tableau par risque et du § 8.3 ; les 7 critiques
     sont les mêmes que dans la matrice SVG ;
  5. chaque actif A, B, C, chaque limite L1 à L25 et chaque hypothèse H-S, H-P est cité dans la section prévue ;
  6. les totaux (actions, jours) du § 1 sont ceux des tableaux d'actions ;
  7. au moins 10 bonnes pratiques citées : chaque fichier et chaque ligne cités existent, et un échantillon
     d'assertions vérifie le contenu de la ligne ;
  8. aucune action GitHub non épinglée par un SHA dans .github/workflows ;
  9. les liens relatifs du plan, de son index et des renvois ajoutés existent (fichier et ancre) ;
 10. la matrice SVG correspond au registre (régénération en mémoire) ;
 11. toute action dont l'horizon diffère de celui que R1 à R4 donnent à son risque directeur porte la mention
     « Exception » ;
 12. la projection du § 8.3 et du § 1 est celle que calcule projeter-plan.py ; la règle d'ouverture est
     énoncée à l'identique à chaque endroit où elle figure.

Usage : python3 docs/06-securite/verifier-plan.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PLAN = HERE / "plan-remediation.md"
REGISTRY = HERE / "analyse-risques.md"

failures: list[str] = []
passes: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    (passes if ok else failures).append(label if ok else f"{label} : {detail}")


def rid(n: int) -> str:
    return f"R-{n:02d}"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def must(pattern: str, text: str) -> re.Match[str]:
    match = re.match(pattern, text)
    assert match is not None, f"motif {pattern!r} introuvable dans {text!r}"
    return match


@dataclass
class Action:
    h: str
    cells: list[str]
    risks: set[int]
    effort: float | None
    residual: str


@dataclass
class Row:
    before: tuple[int, int]
    score: int
    acts: list[str]
    after: tuple[int, int]
    treatment: str


plan = read(PLAN)
registry = read(REGISTRY)

# ---------------------------------------------------------------- registre
reg: dict[int, tuple[int, int]] = {}
for line in registry.splitlines():
    if line.startswith("| **R-"):
        c = cells(line)
        reg[int(c[0].strip("*").removeprefix("R-"))] = (int(c[4]), int(c[5]))
check(len(reg) == 62, "registre : 62 risques lus", f"{len(reg)} lus")
check(sorted(reg) == list(range(1, 63)), "registre : numéros R-01 à R-62 consécutifs")

# ---------------------------------------------------------------- actions
actions: dict[str, Action] = {}
horizon = ""
for line in plan.splitlines():
    if line.startswith("### 4.1"):
        horizon = "CT"
    elif line.startswith("### 4.2"):
        horizon = "MT"
    elif line.startswith("### 4.3"):
        horizon = "LT"
    elif line.startswith("## 5."):
        horizon = ""
    if horizon and line.startswith("| **PA-"):
        c = cells(line)
        pid = must(r"\*\*(PA-\d+)\*\*", c[0]).group(1)
        risks_text = c[2]
        listed: set[int] = set()
        for a, b in re.findall(r"R-(\d+) à R-(\d+)", risks_text):
            listed |= set(range(int(a), int(b) + 1))
        listed |= {int(x) for x in re.findall(r"R-(\d+)", re.sub(r"R-\d+ à R-\d+", "", risks_text))}
        effort = re.search(r"\*\*([\d,]+) j\*\*", c[4])
        actions[pid] = Action(
            h=horizon,
            cells=c,
            risks=listed,
            effort=float(effort.group(1).replace(",", ".")) if effort else None,
            residual=c[7],
        )
check(len(actions) >= 40, "plan : au moins 40 actions", str(len(actions)))
check(all(len(a.cells) == 8 for a in actions.values()), "plan : 8 colonnes par action")
empty = [p for p, a in actions.items() if any(not x for x in a.cells)]
check(not empty, "plan : aucune cellule vide dans les tableaux d'actions", ", ".join(empty))
no_effort = [p for p, a in actions.items() if a.effort is None]
check(not no_effort, "plan : effort chiffré pour chaque action", ", ".join(no_effort))
for horizon_code in ("CT", "MT", "LT"):
    check(
        any(a.h == horizon_code for a in actions.values()),
        f"plan : des actions à l'horizon {horizon_code}",
    )

# ---------------------------------------------------------------- tableau par risque
section = plan.split("### 6.2")[1].split("## 7.")[0]
table: dict[int, Row] = {}
for line in section.splitlines():
    if line.startswith("| **R-"):
        c = cells(line)
        n = int(c[0].strip("*").removeprefix("R-"))
        m_before = must(r"(\d)×(\d) = (\d+)", c[2])
        m_after = must(r"(\d)×(\d) = (\d+)", c[6])
        table[n] = Row(
            before=(int(m_before.group(1)), int(m_before.group(2))),
            score=int(m_before.group(3)),
            acts=[x.strip() for x in c[4].split(",") if x.strip()],
            after=(int(m_after.group(1)), int(m_after.group(2))),
            treatment=c[7],
        )

check(
    sorted(table) == list(range(1, 63)),
    "plan : les 62 risques figurent dans le tableau du § 6.2",
    f"{len(table)} lignes",
)
for n in range(1, 63):
    check(rid(n) in plan, f"{rid(n)} apparaît dans le plan")
bad = [rid(n) for n in table if n in reg and table[n].before != reg[n]]
check(not bad, "notes « avant » identiques à celles du registre", ", ".join(bad))
bad = [rid(n) for n, t in table.items() if t.score != t.before[0] * t.before[1]]
check(not bad, "scores = impact × probabilité", ", ".join(bad))
bad = [rid(n) for n, t in table.items() if not t.acts]
check(not bad, "chaque risque a au moins une action ou un traitement explicite", ", ".join(bad))
unknown = sorted({a for t in table.values() for a in t.acts if a not in actions})
check(not unknown, "chaque action citée par un risque existe", ", ".join(unknown))
bad = [rid(n) for n, t in table.items() if t.score >= 10 and not t.acts]
check(not bad, "chaque risque critique ou élevé a au moins une action", ", ".join(bad))
mismatch = []
for n, t in table.items():
    expected = sorted(p for p, a in actions.items() if n in a.risks)
    if sorted(t.acts) != expected:
        mismatch.append(rid(n))
check(
    not mismatch,
    "actions de chaque risque = actions dont la colonne « Risques traités » le cite",
    ", ".join(mismatch),
)
bad = [rid(n) for n, t in table.items() if t.after[0] * t.after[1] > t.score]
check(not bad, "aucun résiduel supérieur à la criticité actuelle", ", ".join(bad))
untreated = [
    rid(n)
    for n, t in table.items()
    if t.after == t.before and not str(t.treatment).startswith("Accepter")
]
check(
    not untreated,
    "un risque non réduit est explicitement accepté, avec sa raison",
    ", ".join(untreated),
)
bad = [rid(n) for n, t in table.items() if t.treatment != "Réduire" and len(str(t.treatment)) < 30]
check(not bad, "traitement autre que « Réduire » : raison donnée", ", ".join(bad))
for n, t in table.items():
    if t.score >= 15:
        horizons = {actions[a].h for a in t.acts}
        check("CT" in horizons, f"{rid(n)} (critique) a une action de court terme")
mains: dict[int, list[tuple[str, int]]] = {n: [] for n in table}
for p, a in actions.items():
    for n_text, _before, after in re.findall(r"R-(\d+) : (\d+) → (\d+)", str(a.residual)):
        mains[int(n_text)].append((p, int(after)))
        n = int(n_text)
        check(
            table[n].after[0] * table[n].after[1] == int(after),
            f"{p} : résiduel de {rid(n)} identique au tableau par risque",
            f"{after} au lieu de {table[n].after}",
        )
    for n_text, _before, _palier, cible in re.findall(
        r"R-(\d+) : (\d+) → palier (\d+) \(\d×\d\) après le court terme, cible (\d+)",
        str(a.residual),
    ):
        mains[int(n_text)].append((p, int(cible)))
for n, t in table.items():
    if t.score >= 10:
        check(
            bool(mains[n]),
            f"{rid(n)} (critique ou élevé) a une action principale avec résiduel chiffré",
        )

# ---------------------------------------------------------------- matrice SVG
spec = importlib.util.spec_from_file_location(
    "matrice_risques", HERE / "img" / "matrice-risques.py"
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for n, target in module.TARGETS.items():
    check(
        table[n].after == target,
        f"matrice SVG : position visée de {rid(n)} = plan",
        f"{target} / {table[n].after}",
    )
check(
    sorted(module.TARGETS) == sorted(n for n, t in table.items() if t.score >= 15),
    "matrice SVG : les 7 critiques sont ceux du registre",
)
check(
    (HERE / "img" / "matrice-risques.svg").read_text(encoding="utf-8") == module.build(),
    "matrice SVG à jour (régénérée = commitée)",
)

# ---------------------------------------------------------------- couverture
for token in sorted(set(re.findall(r"\b([ABC]-\d\d)\b", registry.split("## 2.")[0]))):
    check(token in plan, f"actif {token} couvert par le plan")
for n in range(1, 26):
    check(
        re.search(rf"\bL{n}\b", plan.split("### 5.3")[1].split("### 5.4")[0]) is not None,
        f"limite L{n} traitée au § 5.3",
    )
for token in sorted(set(re.findall(r"\bH-[SP]\d\d\b", registry))):
    check(token in plan, f"hypothèse {token} citée dans le plan")
for token in (
    "F-04",
    "F-06",
    "F-07",
    "F-09",
    "F-10",
    "F-14",
    "F-15",
    "F-12",
    "F-16",
    "F-21",
    "F-22",
    "F-24",
    "F-25",
    "F-26",
):
    check(token in plan.split("### 5.4")[1].split("## 6.")[0], f"constat {token} traité au § 5.4")

# ---------------------------------------------------------------- totaux
lecture = plan.split("## 1.")[1].split("## 2.")[0]
for code, label in (("CT", "Court terme"), ("MT", "Moyen terme"), ("LT", "Long terme")):
    row = re.search(rf"\| {label} \([^)]*\) \| (\d+) \| ([\d,]+) j \|", lecture)
    mine = [a for a in actions.values() if a.h == code]
    total = sum(a.effort or 0.0 for a in mine)
    ok = (
        row is not None
        and int(row.group(1)) == len(mine)
        and abs(float(row.group(2).replace(",", ".")) - total) < 1e-9
    )
    check(
        ok,
        f"§ 1 : nombre d'actions et effort du {label.lower()} = tableaux",
        f"{len(mine)} actions, {total} j",
    )

# ---------------------------------------------------------------- preuves
proof = plan.split("### 7.1")[1].split("### 7.2")[0]
rows = [cells(line) for line in proof.splitlines() if line.startswith("| BP-")]
check(len(rows) >= 10, "au moins 10 bonnes pratiques prouvées", str(len(rows)))
refs = 0
for c in rows:
    last_path = ""
    found = 0
    for token in re.findall(r"`([^`]+)`", c[3]):
        m = re.fullmatch(r"(?:(.+?))?:(\d+)(?:-(\d+))?", token)
        if m is None:
            m2 = re.fullmatch(r"[\w./-]+\.\w+", token)
            if m2 and "/" in token:
                found += 1
                check((ROOT / token).exists(), f"{c[0]} : fichier {token} existe")
                last_path = token
            continue
        path = m.group(1) or last_path
        if m.group(1):
            last_path = path
        start = int(m.group(2))
        end = int(m.group(3) or m.group(2))
        target = ROOT / path
        if not target.exists():
            check(False, f"{c[0]} : {path}", "fichier introuvable")
            continue
        count = len(target.read_text(encoding="utf-8").splitlines())
        found += 1
        refs += 1
        check(
            1 <= start <= end <= count,
            f"{c[0]} : {path}:{start}-{end} existe ({count} lignes)",
            f"{count} lignes",
        )
    check(found > 0, f"{c[0]} : au moins une preuve citée")

ASSERTIONS = [
    ("deploy/keycloak/collector-realm.json", 6, r'"bruteForceProtected": true'),
    ("deploy/keycloak/collector-realm.json", 7, r'"accessTokenLifespan": 300'),
    ("deploy/keycloak/collector-realm.json", 213, r'"directAccessGrantsEnabled": false'),
    ("deploy/keycloak/collector-realm.json", 214, r'"implicitFlowEnabled": false'),
    ("deploy/keycloak/collector-realm.json", 223, r'"pkce.code.challenge.method": "S256"'),
    ("frontend/src/auth/oidc.ts", 25, r"InMemoryWebStorage"),
    ("services/catalog-service/src/catalog/auth.py", 20, r'ALGORITHM = "RS256"'),
    (
        "services/catalog-service/src/catalog/auth.py",
        177,
        r'"require": \["exp", "iss", "aud", "sub"\]',
    ),
    (
        "services/notification-service/src/notification/auth.py",
        177,
        r'"require": \["exp", "iss", "aud", "sub"\]',
    ),
    ("services/catalog-service/src/catalog/auth.py", 219, r"def require_role"),
    ("services/catalog-service/src/catalog/schemas.py", 7, r'extra="forbid"'),
    ("services/catalog-service/tests/test_security.py", 132, r"test_algorithme_none"),
    ("services/catalog-service/tests/test_security.py", 141, r"test_algorithme_hs256"),
    ("services/catalog-service/tests/test_security.py", 170, r"test_role_manquant_donne_403"),
    ("services/catalog-service/tests/test_security.py", 260, r"test_corps_avec_champ_inconnu"),
    ("services/catalog-service/tests/test_security.py", 283, r"test_erreur_inattendue_donne_500"),
    ("services/catalog-service/tests/test_security.py", 323, r"test_aucun_jeton_ni_raison"),
    ("deploy/helm/collector-service/templates/_helpers.tpl", 28, r"readOnlyRootFilesystem: true"),
    ("deploy/helm/collector-service/templates/_helpers.tpl", 33, r'drop: \["ALL"\]'),
    (
        "deploy/helm/collector-service/templates/deployment.yaml",
        34,
        r"automountServiceAccountToken: false",
    ),
    ("deploy/helm/collector-service/templates/ingress.yaml", 29, r"stsSeconds"),
    ("services/catalog-service/Dockerfile", 31, r"USER 10001"),
    ("frontend/Dockerfile", 34, r"USER 101"),
    (".gitignore", 22, r"^\.env$"),
    ("deploy/local/deploy.sh", 69, r"umask 077"),
    ("deploy/local/deploy.sh", 140, r"--from-file=POSTGRES_PASSWORD"),
    ("deploy/local/deploy.sh", 304, r"image_digest\(\)"),
    ("deploy/local/smoke.sh", 54, r"/admin/"),
    ("deploy/infra/keycloak.yaml", 150, r"path: /realms/"),
    ("deploy/infra/keycloak.yaml", 157, r"path: /resources/"),
    ("deploy/compose/postgres-init/10-roles.sh", 13, r"NOSUPERUSER"),
    ("deploy/compose/postgres-init/10-roles.sh", 15, r"REVOKE ALL"),
    ("frontend/nginx/security-headers.inc.template", 8, r"img-src 'self' data:"),
    ("frontend/nginx/security-headers.inc.template", 15, r"Strict-Transport-Security"),
    ("frontend/e2e/helpers.ts", 62, r"securitypolicyviolation"),
    (".github/workflows/backend.yml", 22, r"contents: read"),
    (".github/workflows/backend.yml", 45, r"persist-credentials: false"),
    (".github/workflows/backend.yml", 171, r"sha256sum --check"),
    (".github/workflows/backend.yml", 181, r"--exit-code 1"),
    (".github/workflows/frontend.yml", 117, r"push-by-digest"),
    (".github/workflows/frontend.yml", 153, r"Trivy sur le digest publié \(arm64\)"),
    (".github/workflows/frontend.yml", 177, r"Garde-fou"),
    ("services/catalog-service/src/catalog/contact.py", 28, r"_EMAIL = re\.compile"),
    ("services/catalog-service/src/catalog/main.py", 35, r"finally:"),
    ("services/catalog-service/Dockerfile", 20, r"--only-upgrade zlib1g"),
    ("services/catalog-service/Dockerfile", 24, r"site-packages/pip"),
    ("services/catalog-service/uv.lock", 1645, r'name = "pyjwt"'),
    ("services/catalog-service/uv.lock", 1646, r'version = "2.15.0"'),
]
for path, line_no, pattern in ASSERTIONS:
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    ok = line_no <= len(lines) and re.search(pattern, lines[line_no - 1]) is not None
    check(ok, f"preuve {path}:{line_no} contient /{pattern}/", "contenu différent à cette ligne")

# ---------------------------------------------------------------- actions GitHub épinglées
for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    for number, text in enumerate(read(workflow).splitlines(), 1):
        uses = re.match(r"\s*-?\s*uses:\s*(\S+)", text)
        if uses and not uses.group(1).startswith("./"):
            ref = uses.group(1).split("@")[-1]
            check(
                re.fullmatch(r"[0-9a-f]{40}", ref) is not None,
                f"{workflow.name}:{number} action épinglée par SHA",
                uses.group(1),
            )


# ---------------------------------------------------------------- liens relatifs
def slugs(path: Path) -> set[str]:
    out = set()
    in_code = False
    for line in read(path).splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"#{1,6} ", line):
            title = re.sub(r"[`*_]", "", line.lstrip("#").strip()).lower()
            out.add(re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", title)))
    return out


def check_links(path: Path) -> None:
    text = read(path)
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        file_part, _, anchor = target.partition("#")
        dest = (path.parent / file_part).resolve() if file_part else path
        ok = dest.exists()
        check(ok, f"{path.name} : lien {target}", "cible introuvable")
        if ok and anchor and dest.suffix == ".md":
            check(anchor in slugs(dest), f"{path.name} : ancre {target}", "ancre introuvable")


for doc in (
    PLAN,
    HERE / "README.md",
    ROOT / "docs/02-architecture/architecture-poc.md",
    ROOT / "docs/01-qualite/devsecops.md",
):
    check_links(doc)

check(
    "plan-remediation.md" in read(HERE / "README.md"),
    "README de docs/06-securite : renvoi vers le plan",
)
check(
    "plan-remediation.md" in read(ROOT / "docs/02-architecture/architecture-poc.md"),
    "architecture-poc.md § 8 : renvoi vers le plan",
)

# ---------------------------------------------------------------- exceptions d'horizon (règles R1 à R4, R9)
for pid, action in actions.items():
    drivers = {int(x) for x in re.findall(r"R-(\d+) :", action.residual)} or action.risks
    drivers = {n for n in drivers if n in table}
    top = max(table[n].score for n in drivers)
    effort_days = action.effort or 0.0
    if top >= 15:
        expected_h = "CT"
    elif top >= 10:
        expected_h = "CT" if effort_days <= 3 else "MT"
    elif top >= 5:
        expected_h = "CT" if effort_days <= 2 else "MT" if effort_days <= 5 else "LT"
    else:
        expected_h = action.h
    check(
        expected_h == action.h or "Exception" in action.cells[3],
        f"{pid} : horizon {action.h} conforme à R1-R4 (attendu {expected_h}) ou mention « Exception »",
        "écart sans mention d'exception",
    )

# ---------------------------------------------------------------- projection, paliers, règle d'ouverture
spec_p = importlib.util.spec_from_file_location("projeter_plan", HERE / "projeter-plan.py")
assert spec_p is not None and spec_p.loader is not None
projeter = importlib.util.module_from_spec(spec_p)
spec_p.loader.exec_module(projeter)
projection = projeter.project(projeter.load(plan))
section_83 = plan.split("### 8.3")[1].split("## 9.")[0]
for key, label in (
    ("0", "Aujourd'hui"),
    ("CT", "Après le court terme"),
    ("MT", "Après le moyen terme"),
    ("LT", "Après le long terme"),
):
    row = re.search(rf"\| {label}[^|]*\| (\d+) \| (\d+) \| (\d+) \|", section_83)
    ok = row is not None and tuple(int(x) for x in row.groups()) == projection[key]
    check(ok, f"§ 8.3 : jalon « {label} » = projeter-plan.py", f"{projection[key]}")
final_text = plan.split("## 1.")[1].split("## 2.")[0]
check(
    f"criticité cumulée de {projection['0'][2]} aujourd'hui à {projection['LT'][2]} au bout de 12 mois"
    in final_text,
    "§ 1 : criticité cumulée avant et après = projeter-plan.py",
)
check(projection["MT"][0] == 0, "plus aucun risque critique à 6 mois", str(projection["MT"]))
check(projection["LT"][0] == 0, "plus aucun risque critique à 12 mois", str(projection["LT"]))
opening = re.findall(r"\*\*Règle d'ouverture de la plateforme\*\* : [^\n]*?vérifiés\.", plan)
check(
    len(opening) >= 3 and len(set(opening)) == 1,
    "règle d'ouverture énoncée à l'identique (synthèse, § 1, § 6.1)",
    f"{len(opening)} occurrences, {len(set(opening))} formulations",
)
paliers = projeter.load(plan).paliers
for pid, action in actions.items():
    for n_text, shown in re.findall(r"R-(\d+) : \d+ → palier (\d+) \(", action.residual):
        n = int(n_text)
        check(
            paliers.get(n) == int(shown),
            f"{pid} : palier de {rid(n)} = tableau du § 8.3",
            f"{shown} / {paliers.get(n)}",
        )
check(
    all(table[n].after[0] * table[n].after[1] <= paliers[n] <= table[n].score for n in paliers),
    "paliers compris entre la cible et la note actuelle",
)
check(
    "accepté par la direction" not in plan,
    "aucun résiduel présenté comme déjà accepté par la direction",
)
check(
    all("à faire accepter" in table[n].treatment for n in (1, 30, 34)),
    "R-01, R-30, R-34 : résiduel élevé « à faire accepter par la direction »",
)
check(
    "R1 à R9" in read(ROOT / "docs/01-qualite/devsecops.md"), "devsecops.md cite les règles R1 à R9"
)
check(
    "sauf L14" in read(ROOT / "docs/02-architecture/architecture-poc.md"),
    "architecture-poc.md § 8 : exception L14 dite",
)

# ---------------------------------------------------------------- bilan
for message in failures:
    print(f"ÉCHEC  {message}")
print(
    f"{len(passes)} contrôles réussis, {len(failures)} échec(s) ; {len(actions)} actions, {len(table)} risques, {len(rows)} bonnes pratiques, {refs} références de preuve."
)
sys.exit(1 if failures else 0)
