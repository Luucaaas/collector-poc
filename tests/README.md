# Tests transverses

- `acceptance/` : tests d'acceptation pytest-bdd issus des critères d'acceptation du backlog
  - `features/` : un fichier Gherkin par user story, en français (`# language: fr`), avec des tags de traçabilité (`@US-03`, `@RM-02`, `@ENF-03`…)
- `load/` : scénarios de charge Locust et résultats
