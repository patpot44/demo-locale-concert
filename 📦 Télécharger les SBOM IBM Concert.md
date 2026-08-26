## Téléchargement



[📦 Télécharger les SBOM IBM Concert.zip](blob:https://m365.cloud.microsoft/664fa557-6a4c-4db9-86d9-06d20c4507c7)





[📋 Télécharger le manifeste d’import séparément.csv](blob:https://m365.cloud.microsoft/984f9c37-df29-4fba-ac92-a66101810602)



## Contenu du package

- **30 applications**
- **2 environnements par application**
- **60 SBOM CycloneDX 1.5 JSON**
- **3 876 composants logiciels**
- **1 127 findings de vulnérabilité**
- Un fichier `sbom_import_manifest.csv`
- Un fichier `README.txt`

Chaque SBOM contient :

- les métadonnées de l’application ;
- l’environnement, production ou préproduction ;
- les composants et packages ;
- les versions ;
- les licences ;
- les dépendances ;
- les vulnérabilités ;
- les scores CVSS ;
- les scores EPSS synthétiques ;
- l’exposition Internet ;
- l’accessibilité à l’exécution, notamment pour les scénarios de dead code ;
- une priorité suggérée.

## Organisation







Plain Text

1

ibm_concert_application_sboms.zip

2

├── README.txt

3

├── sbom_import_manifest.csv

4

└── sbom/

5

​    ├── APP-0001_preproduction_cyclonedx.json

6

​    ├── APP-0001_production_cyclonedx.json

7

​    ├── APP-0002_preproduction_cyclonedx.json

8

​    ├── APP-0002_production_cyclonedx.json

9

​    └── ...

Show more lines

## Ordre d’import conseillé

1. Créer les applications correspondantes dans Concert.
2. Utiliser `sbom_import_manifest.csv` pour associer chaque fichier à son application.
3. Importer d’abord les SBOM de préproduction.
4. Importer ensuite les SBOM de production.
5. Procéder par lots limités, par exemple 5 à 10 fichiers.
6. Vérifier les composants et vulnérabilités après chaque lot.

Les données, les correspondances CVE/composants et les scores sont **entièrement synthétiques**. Elles sont adaptées à une démonstration ou à un POC, mais ne doivent pas servir à prendre des décisions de sécurité en production.