# IBM ConcertDef 2.0.0 application SBOMs by environment

Synthetic POC dataset containing one complete Application SBOM for each application and environment.

- 30 base applications
- 2 environments: preproduction and production
- 60 ConcertDef 2.0.0 Application SBOM files

Each environment is represented by a distinct Concert application name because ConcertDef defines a complete application version and application/environment names cannot contain spaces or `/`.

## Import
1. Review `concertdef_import_manifest.csv`.
2. Upload each JSON file independently.
3. Start with preproduction, then production.
4. Each file is a complete application definition. A later partial replacement can remove earlier component definitions.
5. Import CycloneDX or SPDX scan files separately to add package and vulnerability findings.

All values are synthetic and intended only for demonstration or POC use.
