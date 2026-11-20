#!/usr/bin/env python3
# ruff: noqa: E501  (documentation tool: long lines with French sentences, outside the services' lint)
"""Produces matrice-risques.svg: impact x probability matrix of the 62 risks of analyse-risques.md.

Standard library only. The scores are read from the register (docs/06-securite/analyse-risques.md),
never copied: the matrix therefore cannot diverge from the register. The positions aimed at after
treatment of the 7 critical risks (TARGETS) must stay identical to those of the plan
(plan-remediation.md, section 6); verifier-plan.py checks it.

Usage: python3 docs/06-securite/img/matrice-risques.py   (writes matrice-risques.svg next to the script)
"""

from __future__ import annotations

from html import escape
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE.parent / "analyse-risques.md"
OUT = HERE / "matrice-risques.svg"

# Target position (impact, probability) after treatment, for the 7 critical risks.
TARGETS = {1: (5, 2), 29: (5, 1), 31: (4, 2), 32: (5, 1), 34: (5, 2), 48: (4, 2), 55: (3, 2)}

CELL_W, CELL_H = 270, 170
LEFT, TOP = 150, 150


def read_registry() -> dict[int, tuple[int, int]]:
    """Returns {number: (impact, probability)} from the register lines (R-01 to R-62)."""
    risks: dict[int, tuple[int, int]] = {}
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| **R-"):
            continue
        cells = [c.strip() for c in line.split("|")]
        number = int(cells[1].strip("*").removeprefix("R-"))
        impact, probability, score = int(cells[5]), int(cells[6]), cells[7]
        assert str(impact * probability) in score, (
            f"R-{number:02d}: inconsistent score ({cells[5:8]})"
        )
        risks[number] = (impact, probability)
    return risks


def zone(score: int) -> tuple[str, str]:
    """Background colour and label of the zone according to the analysis thresholds (15, 10, 5)."""
    if score >= 15:
        return "#f4b6b0", "Critique"
    if score >= 10:
        return "#f9cf9c", "Élevé"
    if score >= 5:
        return "#f7ebaa", "Moyen"
    return "#cfe8c4", "Faible"


def pill(x: float, y: float, number: int, target: bool, critical: bool) -> str:
    label = f"R-{number:02d}"
    stroke = "#2b2b2b"
    dash = ' stroke-dasharray="5 3"' if target else ""
    fill = "#ffffff" if not target else "#eef4ff"
    width = 2.2 if critical or target else 1
    weight = "700" if critical or target else "400"
    style = ' font-style="italic"' if target else ""
    return (
        f'<rect x="{x:.0f}" y="{y:.0f}" width="58" height="22" rx="11" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="{width}"{dash}/>'
        f'<text x="{x + 29:.0f}" y="{y + 15:.0f}" text-anchor="middle" font-size="13" '
        f'font-weight="{weight}"{style} fill="#1a1a1a">{label}</text>'
    )


def build() -> str:
    risks = read_registry()
    assert len(risks) == 62, f"{len(risks)} risks read instead of 62"
    cells: dict[tuple[int, int], list[tuple[int, bool]]] = {}
    for number, (impact, probability) in sorted(risks.items()):
        cells.setdefault((impact, probability), []).append((number, False))
    for number, (impact, probability) in sorted(TARGETS.items()):
        assert risks[number][0] * risks[number][1] >= 15, f"R-{number:02d} is not critical"
        cells.setdefault((impact, probability), []).append((number, True))

    width = LEFT + 5 * CELL_W + 30
    height = TOP + 5 * CELL_H + 150
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
        f'height="{height}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text x="{width / 2:.0f}" y="48" text-anchor="middle" font-size="30" font-weight="700" fill="#1a1a1a">'
        "Matrice impact × probabilité des 62 risques de Collector</text>",
        f'<text x="{width / 2:.0f}" y="82" text-anchor="middle" font-size="18" fill="#444">'
        "Criticité = impact × probabilité. Pointillé : position visée après traitement des 7 risques critiques "
        "(plan de remédiation).</text>",
        f'<text x="{LEFT + 5 * CELL_W / 2:.0f}" y="{TOP - 22}" text-anchor="middle" font-size="20" '
        'font-weight="700" fill="#1a1a1a">Probabilité</text>',
        f'<text transform="translate(40 {TOP + 5 * CELL_H / 2:.0f}) rotate(-90)" text-anchor="middle" '
        'font-size="20" font-weight="700" fill="#1a1a1a">Impact</text>',
    ]
    prob_names = {
        1: "1 Très improbable",
        2: "2 Peu probable",
        3: "3 Plausible",
        4: "4 Probable",
        5: "5 Quasi certain",
    }
    imp_names = {
        5: "5 Critique",
        4: "4 Majeur",
        3: "3 Significatif",
        2: "2 Mineur",
        1: "1 Négligeable",
    }
    for p in range(1, 6):
        cx = LEFT + (p - 1) * CELL_W + CELL_W / 2
        out.append(
            f'<text x="{cx:.0f}" y="{TOP - 4}" text-anchor="middle" font-size="15" fill="#333">{prob_names[p]}</text>'
        )
    for row, impact in enumerate(range(5, 0, -1)):
        cy = TOP + row * CELL_H + CELL_H / 2
        out.append(
            f'<text x="{LEFT - 10}" y="{cy + 5:.0f}" text-anchor="end" font-size="15" fill="#333">{imp_names[impact]}</text>'
        )
        for p in range(1, 6):
            x0 = LEFT + (p - 1) * CELL_W
            y0 = TOP + row * CELL_H
            fill, label = zone(impact * p)
            out.append(
                f'<rect x="{x0}" y="{y0}" width="{CELL_W}" height="{CELL_H}" fill="{fill}" stroke="#ffffff" stroke-width="3"/>'
            )
            out.append(
                f'<text x="{x0 + CELL_W - 8}" y="{y0 + CELL_H - 8}" text-anchor="end" font-size="13" fill="#555">'
                f"{impact}×{p} = {impact * p}</text>"
            )
            for index, (number, is_target) in enumerate(cells.get((impact, p), [])):
                col, line = index % 4, index // 4
                out.append(
                    pill(
                        x0 + 10 + col * 64,
                        y0 + 10 + line * 28,
                        number,
                        is_target,
                        number in TARGETS,
                    )
                )
    ly = TOP + 5 * CELL_H + 40
    legend = [
        ("#f4b6b0", "Critique (≥ 15)"),
        ("#f9cf9c", "Élevé (10 à 14)"),
        ("#f7ebaa", "Moyen (5 à 9)"),
        ("#cfe8c4", "Faible (≤ 4)"),
    ]
    for i, (color, text) in enumerate(legend):
        lx = LEFT + i * 260
        out.append(f'<rect x="{lx}" y="{ly}" width="28" height="20" fill="{color}" stroke="#999"/>')
        out.append(
            f'<text x="{lx + 38}" y="{ly + 16}" font-size="16" fill="#222">{escape(text)}</text>'
        )
    out.append(
        f'<text x="{LEFT}" y="{ly + 52}" font-size="15" fill="#444">Trait plein : position actuelle (registre analyse-risques.md § 7). '
        "Gras : risque critique. Pointillé italique : position visée après traitement.</text>"
    )
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"written {OUT.relative_to(HERE.parent.parent.parent)}")
