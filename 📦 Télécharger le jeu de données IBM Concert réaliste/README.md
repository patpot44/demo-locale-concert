# Jeu de donnees synthetiques IBM Concert Protect

Ce package contient des donnees entierement synthetiques pour un POC. Il ne represente aucun environnement client reel.

## Volume
- Applications: 30
- Environnements: 2 par application
- Fichiers CycloneDX combines: 60
- Composants: 3876
- Findings CVE: 1127
- Taille maximale d'un SBOM: 0.07 MB

## Contenu
- `sbom/`: fichiers CycloneDX 1.5 JSON combinant composants et vulnerabilites
- `applications.csv`: catalogue applicatif
- `findings.csv`: vue tabulaire des findings et du scoring synthetique
- `import_manifest.csv`: ordre et controle des imports
- `concert_dataset_summary.xlsx`: tableau de bord du jeu de donnees

## Import recommande
1. Creer d'abord les applications dans Concert.
2. Importer un fichier SBOM a la fois, en commencant par la preproduction puis la production.
3. Utiliser la source `Image` ou `Source code` selon le scenario de demonstration.
4. Pour les reimports, regenerer le `serialNumber` et utiliser un timestamp plus recent.
5. Conserver le meme nom d'image pour les scans successifs et changer le digest afin d'eviter les doublons.

## Prudence de capacite
Le volume est volontairement modere pour un environnement de demonstration de 16 vCPU / 32 Go. Il ne constitue pas une certification de sizing IBM. La capacite reelle depend de la version Concert, du stockage, du nombre d'utilisateurs, des connecteurs et de la frequence d'ingestion.
