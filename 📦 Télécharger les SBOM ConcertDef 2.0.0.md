J’ai généré les **Application SBOM des 30 applications au format IBM ConcertDef 2.0.0**, avec une définition complète par application et par version.

## Téléchargement



[📦 Télécharger les SBOM ConcertDef 2.0.0.zip](blob:https://m365.cloud.microsoft/32c2dc07-894f-485e-92c0-70cde6e372e0)



## Contenu de l’archive







Plain Text

1

ibm_concertdef_2.0.0_application_sboms.zip

2

├── README.md

3

├── concertdef_import_manifest.csv

4

└── sbom/

5

​    ├── APP-0001_Paiements-SEPA_concertdef-2.0.0.json

6

​    ├── APP-0002_Portail-Client_concertdef-2.0.0.json

7

​    ├── ...

8

​    └── APP-0030_Card-Authorization_concertdef-2.0.0.json

Show more lines

### Volumétrie

- **30 applications**
- **30 Application SBOM**
- **1 définition complète par application/version**
- Format : `ConcertDef`
- Version du schéma : `2.0.0`

IBM Concert recommande ConcertDef 2.0.0 pour les nouveaux Application SBOM. ConcertDef 1.0.2 est conservé essentiellement pour la compatibilité avec les anciennes intégrations. [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=sboms-application-sbom-schema-concertdef)

## Données présentes dans chaque SBOM

Chaque fichier contient :

- `bomFormat: ConcertDef`
- `specVersion: 2.0.0`
- nom et version de l’application ;
- date de début de développement ;
- numéro et date de build ;
- criticité métier de 1 à 5 ;
- sensibilité des données de 1 à 5 ;
- revenu horaire synthétique ;
- équipe et unité métier ;
- dépôts de code source ;
- branches Git ;
- images de conteneurs ;
- bibliothèques principales ;
- composants logiques ;
- services exposés ;
- endpoints HTTPS ou AMQPS ;
- exposition réseau publique ou privée ;
- dépendances entre images et services ;
- propriétés et tags applicatifs.

Ces champs correspondent aux capacités documentées du schéma ConcertDef 2.0.0, notamment les composants de type `code`, `image` et `library`, les services, les endpoints, les dépendances et les informations métier. [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=sboms-application-sbom-schema-concertdef)

## Différence avec les SBOM CycloneDX précédents

Les deux packages sont complémentaires :

| Type de SBOM         | Finalité                                                     |
| -------------------- | ------------------------------------------------------------ |
| **ConcertDef 2.0.0** | Définition complète de l’application, de ses repositories, images, services, dépendances et métadonnées métier |
| **CycloneDX**        | Inventaire détaillé des packages et ingestion des vulnérabilités |
| **Deploy SBOM**      | Description précise des composants réellement déployés dans Kubernetes ou OpenShift |

L’Application SBOM ConcertDef représente une **définition complète** de l’application. Lors d’une mise à jour, le fichier doit conserver les composants existants et ajouter les nouveaux. L’import d’une définition partielle peut remplacer la définition précédente et retirer les composants omis. [[ibm.com\]](https://www.ibm.com/docs/en/concert/2.2.x?topic=sboms-application-sbom-concertdef-schema), [[ibm.com\]](https://www.ibm.com/docs/en/concert/3.0.x?topic=sboms-application-sbom-schema-concertdef)

## Ordre d’import recommandé

1. Importer un fichier ConcertDef par application.
2. Vérifier la création de l’application et de sa version dans Concert.
3. Vérifier les composants logiques, repositories, images et services.
4. Importer ensuite les SBOM CycloneDX correspondants pour enrichir les applications avec les packages et les vulnérabilités.
5. Ajouter, si nécessaire, des Deploy SBOM pour représenter précisément les déploiements OpenShift ou Kubernetes.

Les noms d’applications et d’environnements ont été normalisés sans espaces ni caractères `/`, conformément aux contraintes ConcertDef. Les valeurs métier, dépôts, images, endpoints et relations sont synthétiques et destinés uniquement à un POC.