IBM Concert application SBOM package

Synthetic data for demonstration and POC use only.
Format: CycloneDX 1.5 JSON
Applications: 30
Environments per application: production and preproduction
SBOM files: 60
Components: 3876
Vulnerability findings: 1127

Import approach:
1. Create or identify the target application in Concert.
2. Use sbom_import_manifest.csv to associate each file with its application and environment.
3. Import one SBOM at a time.
4. Start with preproduction, then production.
5. These files contain both components and vulnerabilities.

Important:
All applications, components, exposure context, CVE mappings, CVSS values and EPSS values are synthetic. Do not use this package for production security decisions.
