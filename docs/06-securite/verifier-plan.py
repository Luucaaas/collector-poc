#!/usr/bin/env python3
# ruff: noqa: E501  (documentation tool: long lines with French sentences, outside the services' lint)
"""Checks the consistency of the remediation plan (plan-remediation.md) with the risk register.

Standard library only. Exit code 0 if everything is consistent, 1 otherwise.

What the script checks, and what it does not prove. These are checks of **consistency and presence**:
every figure, link, file or line cited exists and agrees with the register; a sample of assertions
checks that an expected pattern appears on the cited line. It does **not** prove that the cited measure works (that is
the role of the tests, scans and runs the proofs refer to), nor that the effort or the cost
of an action is right.

Checks:
  1. every risk R-01 to R-62 of the register appears in the plan, with the same scores (impact, probability);
  2. every critical or high risk has at least one action, and every cited action exists;
  3. the list of actions of each risk is the one given by the action tables;
  4. the residual of an action (final or step) is the one of the per-risk table and of section 8.3; the 7 critical
     risks are the same as in the SVG matrix;
  5. every asset A, B, C, every limit L1 to L25 and every hypothesis H-S, H-P is cited in the intended section;
  6. the totals (actions, days) of section 1 are those of the action tables;
  7. at least 10 good practices cited: every file and every line cited exist, and a sample
     of assertions checks the content of the line;
  8. no GitHub action not pinned by a SHA in .github/workflows;
  9. the relative links of the plan, of its index and of the added cross-references exist (file and anchor);
 10. the SVG matrix matches the register (in-memory regeneration);
 11. every action whose horizon differs from the one that R1 to R4 give its lead risk carries the mention
     "Exception";
 12. the projection of section 8.3 and section 1 is the one computed by projeter-plan.py; the opening rule is
     stated identically everywhere it appears.

Usage: python3 docs/06-securite/verifier-plan.py
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
    (passes if ok else failures).append(label if ok else f"{label}: {detail}")


def rid(n: int) -> str:
    return f"R-{n:02d}"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def must(pattern: str, text: str) -> re.Match[str]:
    match = re.match(pattern, text)
    assert match is not None, f"pattern {pattern!r} not found in {text!r}"
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

# ---------------------------------------------------------------- register
reg: dict[int, tuple[int, int]] = {}
for line in registry.splitlines():
    if line.startswith("| **R-"):
        c = cells(line)
        reg[int(c[0].strip("*").removeprefix("R-"))] = (int(c[4]), int(c[5]))
check(len(reg) == 62, "register: 62 risks read", f"{len(reg)} read")
check(sorted(reg) == list(range(1, 63)), "register: numbers R-01 to R-62 consecutive")

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
check(len(actions) >= 40, "plan: at least 40 actions", str(len(actions)))
check(all(len(a.cells) == 8 for a in actions.values()), "plan: 8 columns per action")
empty = [p for p, a in actions.items() if any(not x for x in a.cells)]
check(not empty, "plan: no empty cell in the action tables", ", ".join(empty))
no_effort = [p for p, a in actions.items() if a.effort is None]
check(not no_effort, "plan: quantified effort for every action", ", ".join(no_effort))
for horizon_code in ("CT", "MT", "LT"):
    check(
        any(a.h == horizon_code for a in actions.values()),
        f"plan: actions at horizon {horizon_code}",
    )

# ---------------------------------------------------------------- per-risk table
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
    "plan: the 62 risks appear in the table of section 6.2",
    f"{len(table)} rows",
)
for n in range(1, 63):
    check(rid(n) in plan, f"{rid(n)} appears in the plan")
bad = [rid(n) for n in table if n in reg and table[n].before != reg[n]]
check(not bad, "\"before\" scores identical to those of the register", ", ".join(bad))
bad = [rid(n) for n, t in table.items() if t.score != t.before[0] * t.before[1]]
check(not bad, "scores = impact × probability", ", ".join(bad))
bad = [rid(n) for n, t in table.items() if not t.acts]
check(not bad, "every risk has at least one action or an explicit treatment", ", ".join(bad))
unknown = sorted({a for t in table.values() for a in t.acts if a not in actions})
check(not unknown, "every action cited by a risk exists", ", ".join(unknown))
bad = [rid(n) for n, t in table.items() if t.score >= 10 and not t.acts]
check(not bad, "every critical or high risk has at least one action", ", ".join(bad))
mismatch = []
for n, t in table.items():
    expected = sorted(p for p, a in actions.items() if n in a.risks)
    if sorted(t.acts) != expected:
        mismatch.append(rid(n))
check(
    not mismatch,
    "actions of each risk = actions whose \"Risques traités\" column cites it",
    ", ".join(mismatch),
)
bad = [rid(n) for n, t in table.items() if t.after[0] * t.after[1] > t.score]
check(not bad, "no residual above the current criticality", ", ".join(bad))
untreated = [
    rid(n)
    for n, t in table.items()
    if t.after == t.before and not str(t.treatment).startswith("Accepter")
]
check(
    not untreated,
    "a risk that is not reduced is explicitly accepted, with its reason",
    ", ".join(untreated),
)
bad = [rid(n) for n, t in table.items() if t.treatment != "Réduire" and len(str(t.treatment)) < 30]
check(not bad, "treatment other than \"Réduire\": reason given", ", ".join(bad))
for n, t in table.items():
    if t.score >= 15:
        horizons = {actions[a].h for a in t.acts}
        check("CT" in horizons, f"{rid(n)} (critical) has a short-term action")
mains: dict[int, list[tuple[str, int]]] = {n: [] for n in table}
for p, a in actions.items():
    for n_text, _before, after in re.findall(r"R-(\d+) : (\d+) → (\d+)", str(a.residual)):
        mains[int(n_text)].append((p, int(after)))
        n = int(n_text)
        check(
            table[n].after[0] * table[n].after[1] == int(after),
            f"{p}: residual of {rid(n)} identical to the per-risk table",
            f"{after} instead of {table[n].after}",
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
            f"{rid(n)} (critical or high) has a main action with a quantified residual",
        )

# ---------------------------------------------------------------- SVG matrix
spec = importlib.util.spec_from_file_location(
    "matrice_risques", HERE / "img" / "matrice-risques.py"
)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for n, target in module.TARGETS.items():
    check(
        table[n].after == target,
        f"SVG matrix: target position of {rid(n)} = plan",
        f"{target} / {table[n].after}",
    )
check(
    sorted(module.TARGETS) == sorted(n for n, t in table.items() if t.score >= 15),
    "SVG matrix: the 7 critical risks are those of the register",
)
check(
    (HERE / "img" / "matrice-risques.svg").read_text(encoding="utf-8") == module.build(),
    "SVG matrix up to date (regenerated = committed)",
)

# ---------------------------------------------------------------- coverage
for token in sorted(set(re.findall(r"\b([ABC]-\d\d)\b", registry.split("## 2.")[0]))):
    check(token in plan, f"asset {token} covered by the plan")
for n in range(1, 26):
    check(
        re.search(rf"\bL{n}\b", plan.split("### 5.3")[1].split("### 5.4")[0]) is not None,
        f"limit L{n} handled in section 5.3",
    )
for token in sorted(set(re.findall(r"\bH-[SP]\d\d\b", registry))):
    check(token in plan, f"hypothesis {token} cited in the plan")
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
    check(token in plan.split("### 5.4")[1].split("## 6.")[0], f"finding {token} handled in section 5.4")

# ---------------------------------------------------------------- totals
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
        f"section 1: number of actions and effort of {label.lower()} = tables",
        f"{len(mine)} actions, {total} j",
    )

# ---------------------------------------------------------------- proofs
proof = plan.split("### 7.1")[1].split("### 7.2")[0]
rows = [cells(line) for line in proof.splitlines() if line.startswith("| BP-")]
check(len(rows) >= 10, "at least 10 proven good practices", str(len(rows)))
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
                check((ROOT / token).exists(), f"{c[0]}: file {token} exists")
                last_path = token
            continue
        path = m.group(1) or last_path
        if m.group(1):
            last_path = path
        start = int(m.group(2))
        end = int(m.group(3) or m.group(2))
        target = ROOT / path
        if not target.exists():
            check(False, f"{c[0]}: {path}", "file not found")
            continue
        count = len(target.read_text(encoding="utf-8").splitlines())
        found += 1
        refs += 1
        check(
            1 <= start <= end <= count,
            f"{c[0]}: {path}:{start}-{end} exists ({count} lines)",
            f"{count} lines",
        )
    check(found > 0, f"{c[0]}: at least one proof cited")

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
    ("services/catalog-service/tests/test_security.py", 132, r"test_algorithm_none"),
    ("services/catalog-service/tests/test_security.py", 141, r"test_algorithm_hs256"),
    ("services/catalog-service/tests/test_security.py", 170, r"test_missing_role_gives_403"),
    ("services/catalog-service/tests/test_security.py", 260, r"test_body_with_unknown_field"),
    ("services/catalog-service/tests/test_security.py", 283, r"test_unexpected_error_gives_500"),
    ("services/catalog-service/tests/test_security.py", 323, r"test_no_token_nor_reason"),
    ("deploy/helm/collector-service/templates/_helpers.tpl", 28, r"readOnlyRootFilesystem: true"),
    ("deploy/helm/collector-service/templates/_helpers.tpl", 33, r'drop: \["ALL"\]'),
    (
        "deploy/helm/collector-service/templates/deployment.yaml",
        34,
        r"automountServiceAccountToken: false",
    ),
    ("deploy/helm/collector-service/templates/ingress.yaml", 29, r"stsSeconds"),
    ("services/catalog-service/Dockerfile", 31, r"USER 10001"),
    ("frontend/Dockerfile", 36, r"USER 101"),
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
    (".github/workflows/frontend.yml", 153, r"Trivy on the published digest \(arm64\)"),
    (".github/workflows/frontend.yml", 177, r"Guard: each tag"),
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
    check(ok, f"proof {path}:{line_no} contains /{pattern}/", "different content at this line")

# ---------------------------------------------------------------- GitHub actions pinned
for workflow in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
    for number, text in enumerate(read(workflow).splitlines(), 1):
        uses = re.match(r"\s*-?\s*uses:\s*(\S+)", text)
        if uses and not uses.group(1).startswith("./"):
            ref = uses.group(1).split("@")[-1]
            check(
                re.fullmatch(r"[0-9a-f]{40}", ref) is not None,
                f"{workflow.name}:{number} action pinned by SHA",
                uses.group(1),
            )


# ---------------------------------------------------------------- relative links
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
        check(ok, f"{path.name}: link {target}", "target not found")
        if ok and anchor and dest.suffix == ".md":
            check(anchor in slugs(dest), f"{path.name}: anchor {target}", "anchor not found")


for doc in (
    PLAN,
    HERE / "README.md",
    ROOT / "docs/02-architecture/architecture-poc.md",
    ROOT / "docs/01-qualite/devsecops.md",
):
    check_links(doc)

check(
    "plan-remediation.md" in read(HERE / "README.md"),
    "README of docs/06-securite: reference to the plan",
)
check(
    "plan-remediation.md" in read(ROOT / "docs/02-architecture/architecture-poc.md"),
    "architecture-poc.md section 8: reference to the plan",
)

# ---------------------------------------------------------------- horizon exceptions (rules R1 to R4, R9)
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
        f"{pid}: horizon {action.h} compliant with R1-R4 (expected {expected_h}) or 'Exception' mention",
        "gap without exception mention",
    )

# ---------------------------------------------------------------- projection, steps, opening rule
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
    check(ok, f"§ 8.3: milestone '{label}' = projeter-plan.py", f"{projection[key]}")
final_text = plan.split("## 1.")[1].split("## 2.")[0]
check(
    f"criticité cumulée de {projection['0'][2]} aujourd'hui à {projection['LT'][2]} au bout de 12 mois"
    in final_text,
    "section 1: cumulative criticality before and after = projeter-plan.py",
)
check(projection["MT"][0] == 0, "no critical risk left at 6 months", str(projection["MT"]))
check(projection["LT"][0] == 0, "no critical risk left at 12 months", str(projection["LT"]))
opening = re.findall(r"\*\*Règle d'ouverture de la plateforme\*\* : [^\n]*?vérifiés\.", plan)
check(
    len(opening) >= 3 and len(set(opening)) == 1,
    "opening rule stated identically (summary, section 1, section 6.1)",
    f"{len(opening)} occurrences, {len(set(opening))} wordings",
)
paliers = projeter.load(plan).paliers
for pid, action in actions.items():
    for n_text, shown in re.findall(r"R-(\d+) : \d+ → palier (\d+) \(", action.residual):
        n = int(n_text)
        check(
            paliers.get(n) == int(shown),
            f"{pid}: step of {rid(n)} = table of section 8.3",
            f"{shown} / {paliers.get(n)}",
        )
check(
    all(table[n].after[0] * table[n].after[1] <= paliers[n] <= table[n].score for n in paliers),
    "steps between the target and the current score",
)
check(
    "accepté par la direction" not in plan,
    "no residual presented as already accepted by management",
)
check(
    all("à faire accepter" in table[n].treatment for n in (1, 30, 34)),
    "R-01, R-30, R-34: high residual \"à faire accepter par la direction\"",
)
check(
    "R1 à R9" in read(ROOT / "docs/01-qualite/devsecops.md"), "devsecops.md cites rules R1 to R9"
)
check(
    "sauf L14" in read(ROOT / "docs/02-architecture/architecture-poc.md"),
    "architecture-poc.md section 8: exception L14 stated",
)

# ---------------------------------------------------------------- summary
for message in failures:
    print(f"FAILURE {message}")
print(
    f"{len(passes)} checks passed, {len(failures)} failure(s); {len(actions)} actions, {len(table)} risks, {len(rows)} good practices, {refs} proof references."
)
sys.exit(1 if failures else 0)
