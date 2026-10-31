# 03 — Backlog

| Document | Contenu |
| --- | --- |
| [exigences.md](exigences.md) | Exigences fonctionnelles (EF-01 à EF-36) et non fonctionnelles (ENF-01 à ENF-31, ISO/IEC 25010:2023), règles métier (RM-01 à RM-09), périmètre POC ou cible |
| [user-stories.md](user-stories.md) | Les 5 user stories du POC : priorité MoSCoW, estimation, exigences couvertes, critères d'acceptation Given/When/Then, DoR et DoD |

Chaque critère d'acceptation devient un test pytest (client httpx) dans [`tests/acceptance/`](../../tests/acceptance/), nommé d'après la story et le critère.
