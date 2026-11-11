# 06 — Sécurité

- [Rapport des scans](rapport-scans.md) : audit du 10/11/2026 (OWASP ZAP, Trivy, SonarCloud, `npm audit`), 25 constats qualifiés, vulnérabilités sans correctif par image et par architecture
- [`scans/`](scans/) : script rejouable `run-scans.sh` (ZAP épinglé par digest, Trivy 0.76.0 vérifié par SHA-256) et rapports bruts versionnés dans `scans/resultats/<AAAAMMJJ-HHMM>/` (`resume.md` : synthèse chiffrée générée)
- [Analyse de risques](analyse-risques.md) : actifs, échelles, flux et STRIDE, correspondance OWASP Top 10:2025 et API Security Top 10:2023, reste du SI par hypothèses, conformité, registre de 62 risques notés (P9-03)
- Plan de remédiation priorisé (impact × probabilité) : à venir (P9-04)
- Rapports des tests de charge : `tests/load/` et `docs/04-experimentations/05-charge-disponibilite/`
