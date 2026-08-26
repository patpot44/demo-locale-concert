# IBM ConcertDef 2.0.0 application SBOMs

Synthetic POC dataset containing one complete Application SBOM per application version.

## Import
1. Review `concertdef_import_manifest.csv`.
2. Upload one JSON file per application.
3. Application and environment names contain no spaces or `/`.
4. Each file is a full application definition. Replacing it with a partial file can remove prior component definitions.
5. `metadata.timestamp` precedes the synthetic build timestamp and should precede subsequent scan timestamps.

## Scope
ConcertDef defines application structure, repositories, images, libraries, services, dependencies and business metadata. Package vulnerability findings remain appropriate for CycloneDX/SPDX scan ingestion rather than this Application SBOM definition.

All values are synthetic and intended only for demonstration or POC use.
