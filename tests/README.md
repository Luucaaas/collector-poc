# Tests transverses

- `acceptance/` : tests d'acceptation en pytest avec le client httpx, un test par critère d'acceptation du backlog, nommé d'après la story et le critère (`test_us03_ca2_article_avec_coordonnees_rejete`). Ils s'exécutent contre l'API déployée.
- `load/` : scénarios de charge Locust et résultats
