"""Synthèse chiffrée d'une exécution de run-scans.sh (écrite dans resume.md).

Usage : python3 summarize.py <dossier des résultats>
Ne lit que les fichiers du dossier ; un fichier absent (étape non lancée) est simplement ignoré.
Sans dépendance : bibliothèque standard seulement.
"""

# ruff: noqa: E501  (phrases de rapport en français, volontairement non coupées)
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
ZAP_RISKS = {"3": "High", "2": "Medium", "1": "Low", "0": "Informational"}


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def trivy_images(results: Path) -> list[str]:
    files = sorted(results.glob("trivy-*-a*64.json"))
    if not files:
        return []
    out = ["## Trivy : images (toutes sévérités, sans --ignore-unfixed)", ""]
    out += [
        "| Image | Arch. | Système | "
        + " | ".join(SEVERITIES)
        + " | Total | CVE distinctes | Sans correctif | Secrets |",
        "| --- | --- | --- | "
        + " | ".join("---" for _ in SEVERITIES)
        + " | --- | --- | --- | --- |",
    ]
    per_image: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for file in files:
        data = load(file)
        if data is None:
            continue
        name, arch = file.stem[len("trivy-") :].rsplit("-", 1)
        vulns: list[dict[str, Any]] = []
        secrets = 0
        for result in data.get("Results") or []:
            vulns += result.get("Vulnerabilities") or []
            secrets += len(result.get("Secrets") or [])
        seen = {}
        for v in vulns:
            seen[(v["VulnerabilityID"], v["PkgName"], v.get("InstalledVersion", ""))] = v
        uniq = list(seen.values())
        per_image.setdefault(name, {})[arch] = uniq
        by = Counter(v["Severity"] for v in uniq)
        unfixed = [v for v in uniq if not v.get("FixedVersion")]
        by_unfixed = Counter(v["Severity"] for v in unfixed)
        os_name = (data.get("Metadata") or {}).get("OS") or {}
        system = f"{os_name.get('Family', '?')} {os_name.get('Name', '')}".strip()
        cells = " | ".join(f"{by.get(s, 0)} ({by_unfixed.get(s, 0)})" for s in SEVERITIES)
        distinct = len({v["VulnerabilityID"] for v in uniq})
        cve_unfixed = {
            s: len({v["VulnerabilityID"] for v in unfixed if v["Severity"] == s})
            for s in SEVERITIES
        }
        detail_unfixed = " ; ".join(f"{s[0]} {n}" for s, n in cve_unfixed.items() if n) or "0"
        out.append(
            f"| {name} | {arch} | {system} | {cells} | {len(uniq)} | {distinct} | "
            f"{len(unfixed)} (CVE distinctes : {detail_unfixed}) | {secrets} |"
        )
    out += [
        "",
        "Chaque cellule de sévérité : nombre total de lignes (paquet, version, CVE), dont sans correctif entre parenthèses.",
        "",
    ]

    def key(v: dict[str, Any]) -> tuple[str, str, str, str]:
        return (v["Severity"], v["VulnerabilityID"], v["PkgName"], v.get("InstalledVersion", ""))

    out += [
        "### Vulnérabilités avec correctif disponible (à corriger : mise à jour de paquet ou de dépendance)",
        "",
    ]
    for name, archs in sorted(per_image.items()):
        fixed: dict[tuple[str, str, str, str], tuple[dict[str, Any], set[str]]] = {}
        for arch, vulns in archs.items():
            for v in vulns:
                if v.get("FixedVersion"):
                    fixed.setdefault(key(v), (v, set()))[1].add(arch)
        out.append(f"- {name} : {len(fixed)} ligne(s)")
        for _key, (v, arches) in sorted(
            fixed.items(), key=lambda kv: (SEVERITIES.index(kv[0][0]), kv[0][1])
        ):
            out.append(
                f"  - {v['Severity']} {v['VulnerabilityID']} {v['PkgName']} {v.get('InstalledVersion', '')} "
                f"-> {v['FixedVersion']} ({'+'.join(sorted(arches))})"
            )
    out += [
        "",
        "### Sans correctif : CRITICAL et HIGH, regroupés par CVE (MEDIUM et LOW : voir les JSON)",
        "",
    ]
    for name, archs in sorted(per_image.items()):
        sets = {a: {key(v) for v in vs if not v.get("FixedVersion")} for a, vs in archs.items()}
        same = len({frozenset(x) for x in sets.values()}) == 1
        out.append(
            f"- {name} ({'identique en amd64 et arm64' if same else 'DIFFÉRENT selon l architecture'})"
        )
        arch0 = min(archs)
        groups: dict[tuple[str, str, str], list[str]] = {}
        for v in archs[arch0]:
            if not v.get("FixedVersion") and v["Severity"] in ("CRITICAL", "HIGH"):
                groups.setdefault(
                    (v["Severity"], v["VulnerabilityID"], v.get("Title", "")), []
                ).append(v["PkgName"])
        for (sev, cve, title), pkgs in sorted(
            groups.items(), key=lambda kv: (SEVERITIES.index(kv[0][0]), kv[0][1])
        ):
            out.append(
                f"  - {sev} {cve} : {title[:80]} ({len(pkgs)} paquet(s) : {', '.join(sorted(set(pkgs)))[:90]})"
            )
        if not same:
            for a, sset in sets.items():
                out.append(f"  - {a} : {len(sset)} ligne(s) sans correctif")
    return out + [""]


def trivy_config(results: Path) -> list[str]:
    files = sorted(results.glob("trivy-config-*.json"))
    if not files:
        return []
    out = ["## Trivy : configuration (Dockerfiles, manifestes, chart rendu)", ""]
    out += [
        "| Cible | Sévérité | Identifiant | Constat | Lignes |",
        "| --- | --- | --- | --- | --- |",
    ]
    for file in files:
        data = load(file)
        for result in (data or {}).get("Results") or []:
            for m in result.get("Misconfigurations") or []:
                if m.get("Status") != "FAIL":
                    continue
                meta = m.get("CauseMetadata") or {}
                lines = f"{meta.get('StartLine', '?')}-{meta.get('EndLine', '?')}"
                out.append(
                    f"| {result['Target']} | {m['Severity']} | {m['ID']} | {m['Title']} | {lines} |"
                )
    return out + [""]


def zap(results: Path) -> list[str]:
    files = sorted(results.glob("zap-*.json"))
    if not files:
        return []
    out = ["## ZAP", ""]
    for file in files:
        data = load(file)
        if data is None:
            continue
        out.append(f"### {file.stem[len('zap-') :]}")
        out.append("")
        alerts = [a for site in data.get("site", []) for a in site.get("alerts", [])]
        by = Counter(ZAP_RISKS.get(str(a.get("riskcode")), "?") for a in alerts)
        out.append(
            "Alertes par niveau : " + (", ".join(f"{k} {v}" for k, v in by.items()) or "aucune")
        )
        out.append("")
        out.append("| Niveau | Identifiant | Alerte | Instances |")
        out.append("| --- | --- | --- | --- |")
        for a in sorted(alerts, key=lambda a: (-int(a.get("riskcode", 0)), a.get("pluginid", ""))):
            out.append(
                f"| {ZAP_RISKS.get(str(a.get('riskcode')), '?')} | {a.get('pluginid')} | {a.get('name')} | "
                f"{a.get('count', len(a.get('instances', [])))} |"
            )
        out.append("")
    return out


def sonar(results: Path) -> list[str]:
    files = sorted(results.glob("sonar-*-issues.json"))
    if not files:
        return []
    out = ["## SonarCloud (API publique)", ""]
    for file in files:
        svc = file.stem[len("sonar-") : -len("-issues")]
        issues = (load(file) or {}).get("issues", [])
        hotspots = (load(results / f"sonar-{svc}-hotspots.json") or {}).get("hotspots", [])
        gate = (
            (load(results / f"sonar-{svc}-quality-gate.json") or {}).get("projectStatus") or {}
        ).get("status")
        out.append(
            f"- {svc} : quality gate {gate}, {len(issues)} issue(s) ouverte(s), {len(hotspots)} security hotspot(s)"
        )
        for i in issues:
            out.append(
                f"  - {i['rule']} {i['severity']} ({i['type']}) {i['component'].split(':', 1)[-1]}:{i.get('line', '?')} : {i['message']}"
            )
        for h in hotspots:
            out.append(f"  - hotspot {h.get('ruleKey')} {h.get('status')} : {h.get('message')}")
    return out + [""]


def npm(results: Path) -> list[str]:
    out = []
    for label, name in (
        ("complet (développement compris)", "npm-audit-complet.json"),
        ("embarqué (--omit=dev)", "npm-audit-prod.json"),
    ):
        data = load(results / name)
        if data is None:
            continue
        meta = (data.get("metadata") or {}).get("vulnerabilities", {})
        out.append(f"- npm audit {label} : " + ", ".join(f"{k} {v}" for k, v in meta.items()))
        for pkg, v in sorted((data.get("vulnerabilities") or {}).items()):
            via = [x["title"] if isinstance(x, dict) else x for x in v.get("via", [])]
            out.append(
                f"  - {pkg} {v.get('severity')} (direct : {v.get('isDirect')}) : {'; '.join(map(str, via))[:110]}"
            )
    return ["## npm audit", ""] + out + [""] if out else []


def main() -> int:
    results = Path(sys.argv[1])
    print(f"# Synthèse de l'exécution {results.name}\n")
    for part in (trivy_images, trivy_config, zap, sonar, npm):
        lines = part(results)
        if lines:
            print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
