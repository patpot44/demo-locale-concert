#!/bin/bash
# Regenerate ConfigMap from locustfile.py

cd "$(dirname "$0")"

cat > k8s/configmap.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: chat-loadgen-config
  namespace: demoapps-bank-anthos
data:
  locustfile.py: |
EOF

# Indent locustfile.py content by 4 spaces
sed 's/^/    /' locustfile.py >> k8s/configmap.yaml

echo "ConfigMap updated successfully!"

# Made with Bob
