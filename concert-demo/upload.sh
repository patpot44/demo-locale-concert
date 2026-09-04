#!/bin/bash
# upload.sh — Upload de fichiers vers IBM Concert via API
# Usage: ./upload.sh <data_type> <fichier>
# Exemples:
#   ./upload.sh application_sbom 01_application_sbom.json
#   ./upload.sh code_scan        04_code_scan_sast.csv
#   ./upload.sh certificate      06_certificate_sbom.json
#   ./upload.sh package_sbom     08_package_sbom_cyclonedx.json

CONCERT_HOST="https://172.22.147.223:12443"
API_KEY="C_API_KEY aWJtY29uY2VydDo0Y2Y1ZmFhYi04ZDEwLTRlNTEtOTZlYS1kNjUzY2QyM2QyOGM="
INSTANCE_ID="0000-0000-0000-0000"

DATA_TYPE="${1}"
FILE="${2}"

if [[ -z "$DATA_TYPE" || -z "$FILE" ]]; then
  echo "Usage: $0 <data_type> <fichier>"
  echo ""
  echo "data_types disponibles:"
  echo "  application_sbom   image_scan   code_scan   vm_scan"
  echo "  certificate        package_sbom compliance_posture"
  exit 1
fi

if [[ ! -f "$FILE" ]]; then
  echo "Erreur: fichier '$FILE' introuvable"
  exit 1
fi

echo "→ Upload: $FILE  (type: $DATA_TYPE)"
echo ""

curl -sk -X POST "${CONCERT_HOST}/ingestion/api/v1/upload_files" \
  -H "Authorization: ${API_KEY}" \
  -H "InstanceID: ${INSTANCE_ID}" \
  -F "data_type=${DATA_TYPE}" \
  -F "filename=@${FILE}" \
  | python3 -m json.tool --no-ensure-ascii

echo ""
