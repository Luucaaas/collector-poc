#!/usr/bin/env python3
# ruff: noqa: E501  (documentation tool: long lines with French sentences, outside the services' lint)
"""Computes the register projection at the 3, 6 and 12 month milestones from plan-remediation.md.

Standard library only. Rule (that of section 8.3 of the plan): a risk is "treated" at a milestone when
all its actions are due at that milestone; it then takes its target score (column "I × P visé" of section 6.2).
Before that it keeps its step (table of section 8.3) if it has one, otherwise its current score. No credit is therefore
taken before an action is delivered.

Usage: python3 docs/06-securite/projeter-plan.py   (prints the table of section 8.3)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PLAN = Path(__file__).resolve().parent / "plan-remediation.md"
ORDER = {"CT": 0, "MT": 1, "LT": 2}
SCORE = re.compile(r"(\d)×(\d) = (\d+)")


@dataclass
class Plan:
    horizon: dict[str, str]
    before: dict[int, int]
    after: dict[int, int]
    actions: dict[int, list[str]]
    paliers: dict[int, int]


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def load(text: str) -> Plan:
    horizon: dict[str, str] = {}
    current = ""
    for line in text.splitlines():
        for marker, code in (("### 4.1", "CT"), ("### 4.2", "MT"), ("### 4.3", "LT")):
            if line.startswith(marker):
                current = code
        if line.startswith("## 5."):
            current = ""
        if current and line.startswith("| **PA-"):
            horizon[cells(line)[0].split("**")[1]] = current
    before: dict[int, int] = {}
    after: dict[int, int] = {}
    actions: dict[int, list[str]] = {}
    for line in text.split("### 6.2")[1].split("## 7.")[0].splitlines():
        if line.startswith("| **R-"):
            c = cells(line)
            number = int(c[0].strip("*").removeprefix("R-"))
            before_match, after_match = SCORE.match(c[2]), SCORE.match(c[6])
            assert before_match and after_match, line
            before[number] = int(before_match.group(3))
            after[number] = int(after_match.group(3))
            actions[number] = [x.strip() for x in c[4].split(",") if x.strip()]
    paliers: dict[int, int] = {}
    for line in text.split("### 8.3")[1].split("## 9.")[0].splitlines():
        if line.startswith("| R-"):
            c = cells(line)
            match = SCORE.match(c[1])
            if match:
                paliers[int(c[0].removeprefix("R-"))] = int(match.group(3))
    return Plan(horizon, before, after, actions, paliers)


def project(plan: Plan) -> dict[str, tuple[int, int, int]]:
    """Returns, per milestone ("0", "CT", "MT", "LT"), (critical, high, sum of I × P)."""
    out: dict[str, tuple[int, int, int]] = {}
    for milestone in ("0", "CT", "MT", "LT"):
        scores = []
        for number, base in plan.before.items():
            if milestone == "0":
                scores.append(base)
                continue
            due = max(ORDER[plan.horizon[a]] for a in plan.actions[number]) <= ORDER[milestone]
            if due:
                scores.append(plan.after[number])
            else:
                scores.append(plan.paliers.get(number, base))
        out[milestone] = (
            sum(1 for s in scores if s >= 15),
            sum(1 for s in scores if 10 <= s < 15),
            sum(scores),
        )
    return out


if __name__ == "__main__":
    result = project(load(PLAN.read_text(encoding="utf-8")))
    names = {"0": "Aujourd'hui", "CT": "3 mois", "MT": "6 mois", "LT": "12 mois et plus"}
    print("| Jalon | Critiques | Élevés | Criticité cumulée |")
    print("| --- | ---: | ---: | ---: |")
    for key, (critical, high, total) in result.items():
        print(f"| {names[key]} | {critical} | {high} | {total} |")
