# 06 — Sécurité

- [Rapport des scans](rapport-scans.md) : audit du 10/11/2026 (OWASP ZAP, Trivy, SonarCloud, `npm audit`), 25 constats qualifiés, vulnérabilités sans correctif par image et par architecture
- [`scans/`](scans/) : script rejouable `run-scans.sh` (ZAP épinglé par digest, Trivy 0.76.0 vérifié par SHA-256) et rapports bruts versionnés dans `scans/resultats/<AAAAMMJJ-HHMM>/` (`resume.md` : synthèse chiffrée générée)
- [Analyse de risques](analyse-risques.md) : actifs, échelles, flux et STRIDE, correspondance OWASP Top 10:2025 et API Security Top 10:2023, reste du SI par hypothèses, conformité, registre de 62 risques notés (P9-03)
- [Plan de remédiation](plan-remediation.md) : méthode de priorisation, matrice impact × probabilité, 58 actions à court, moyen et long terme pour tout le SI, traitement des 62 risques, bonnes pratiques déjà prouvées dans le POC, budget et suivi (P9-04) ; [`img/matrice-risques.py`](img/matrice-risques.py) produit la matrice en SVG [`projeter-plan.py`](projeter-plan.py) calcule la projection du registre aux jalons 3, 6 et 12 mois et [`verifier-plan.py`](verifier-plan.py) contrôle la cohérence du plan avec le registre
- Rapports des tests de charge : `tests/load/` et `docs/04-experimentations/05-charge-disponibilite/`
