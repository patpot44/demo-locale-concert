# IBM ConcertDef 2.0.0 SBOMs corrigés

Ce package contient 60 Application SBOM synthétiques : 30 pour la préproduction et 30 pour la production.

## Correction appliquée

Pour chaque application, le nom et l’URL de chaque dépôt de code sont désormais strictement identiques entre préproduction et production. Seule la branche varie :

- préproduction : `develop`
- production : `main`

Exemple :

- dépôt principal : `app-0001-go` avec `https://git.example.local/integration/app-0001`
- dépôt worker : `app-0001-go-worker` avec `https://git.example.local/integration/app-0001-worker`

Les images, services, versions et noms d’applications restent différenciés par environnement.

Toutes les données sont synthétiques et destinées à un POC ou une démonstration.
