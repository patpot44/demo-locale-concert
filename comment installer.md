## Volumétrie générée

| Élément                   | Volume                          |
| ------------------------- | ------------------------------- |
| Applications métier       | 30                              |
| Environnements            | 60, production et préproduction |
| Fichiers CycloneDX JSON   | 60                              |
| Composants logiciels      | 3 876                           |
| Findings CVE              | 1 127                           |
| Taille maximale d’un SBOM | 0,067 Mo                        |
| Taille compressée totale  | Environ 0,31 Mo                 |

Le volume est suffisamment riche pour tester les écrans, la corrélation, la priorisation et les workflows, sans générer une charge d’ingestion excessive.

## Contenu de l’archive







Plain Text

1

ibm_concert_realistic_dataset.zip

2

├── README.md

3

├── applications.csv

4

├── findings.csv

5

├── import_manifest.csv

6

├── concert_dataset_summary.xlsx

7

└── sbom/

8

​    ├── APP-0001_production_cyclonedx.json

9

​    ├── APP-0001_preproduction_cyclonedx.json

10

​    ├── ...

11

​    └── APP-0030_preproduction_cyclonedx.json

Show more lines

### Fichiers CycloneDX

Les 60 fichiers SBOM utilisent le format **CycloneDX 1.5 JSON**. Chaque fichier combine :

- les composants logiciels ;
- les dépendances ;
- les licences open source ;
- les vulnérabilités ;
- les scores CVSS ;
- les scores EPSS synthétiques ;
- le contexte d’exposition Internet ;
- la notion de code atteignable ou non atteignable ;
- un score de risque contextuel ;
- une priorité suggérée P1, P2, P3 ou dépriorisée ;
- les métadonnées d’application et d’environnement.

IBM Concert 3.0 prend en charge les SBOM JSON aux formats CycloneDX et SPDX. Il sait également traiter un fichier CycloneDX combinant les composants et les vulnérabilités. [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=composition-uploading-sbom-file), [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=inventory-importing-data-concert)

### Applications simulées

Le catalogue inclut notamment :

- Paiements SEPA ;
- Portail Client ;
- API Sinistres ;
- Mobile Banking ;
- Open Banking API ;
- IAM Gateway ;
- Référentiel Client ;
- Fraud Detection ;
- KYC Service ;
- Loan Origination ;
- Card Authorization ;
- Reporting réglementaire.

Chaque application possède une criticité métier, une équipe propriétaire, une classification des données, une technologie dominante et un indicateur d’exposition Internet.

### Scénario dead code et runtime reachability

Certains composants vulnérables sont marqués comme :

- **runtime reachable** : le composant est supposé utilisé à l’exécution ;
- **Internet exposed** : le chemin vulnérable est associé à une application exposée ;
- **not affected / dead or unreachable code** : le package est présent dans le SBOM, mais aucun chemin d’exécution n’est simulé.

Cela permet de démontrer qu’une même CVE peut avoir une priorité différente selon son contexte applicatif.

## Ordre d’import recommandé

1. Créer les applications dans IBM Concert en utilisant `applications.csv`.
2. Consulter `import_manifest.csv` pour retrouver la correspondance entre application, environnement et fichier SBOM.
3. Importer d’abord les fichiers de préproduction.
4. Importer ensuite les fichiers de production.
5. Commencer par 5 à 10 SBOM afin de contrôler le résultat.
6. Poursuivre par lots de 10 fichiers.
7. Vérifier les applications, composants et vulnérabilités après chaque lot.

IBM recommande l’import d’un seul SBOM à la fois pour limiter les conflits de traitement. La limite d’upload manuel par l’interface est de **10 Mo par fichier**, très supérieure à la taille des fichiers générés ici. [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=composition-uploading-sbom-file), [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=inventory-importing-data-concert)

## Points d’attention

Toutes les données sont **synthétiques** :

- les CVE servent à produire un scénario vraisemblable ;
- les correspondances CVE/composants/version ne constituent pas une vérité issue de NVD ;
- les scores EPSS sont simulés ;
- les contextes d’exploitation et de dead code sont simulés ;
- les applications et URL de dépôts sont fictives.

Enfin, ce dataset est calibré de manière conservatrice pour un **POC**, mais il ne constitue pas une validation officielle du sizing IBM. La capacité réelle dépend aussi du stockage, de la version exacte de Concert, du nombre de connecteurs, des workflows, de la concurrence utilisateur et de la fréquence des ingestions.