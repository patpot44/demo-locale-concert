#!/bin/bash
# DevFleet Load Generator Deployment Script (using buildah/oc)
# Deploys the coding agent load generator to OpenShift without Docker

set -e

echo "=========================================="
echo "DevFleet Load Generator Deployment"
echo "=========================================="
echo ""

# Configuration
NAMESPACE="loadgen"
APP_NAME="devfleet-loadgen"
IMAGE_NAME="devfleet-loadgen:latest"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Step 1: Creating namespace (if it doesn't exist)..."
oc create namespace $NAMESPACE --dry-run=client -o yaml | oc apply -f -
echo "✓ Namespace ready"
echo ""

echo "Step 2: Creating BuildConfig for OpenShift build..."
cd "$SCRIPT_DIR"

# Create BuildConfig if it doesn't exist
cat <<EOF | oc apply -f -
apiVersion: build.openshift.io/v1
kind: BuildConfig
metadata:
  name: $APP_NAME
  namespace: $NAMESPACE
spec:
  output:
    to:
      kind: ImageStreamTag
      name: $APP_NAME:latest
  source:
    type: Binary
  strategy:
    type: Docker
    dockerStrategy:
      dockerfilePath: Dockerfile
EOF

echo "✓ BuildConfig created"
echo ""

echo "Step 3: Creating ImageStream..."
cat <<EOF | oc apply -f -
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: $APP_NAME
  namespace: $NAMESPACE
spec:
  lookupPolicy:
    local: true
EOF

echo "✓ ImageStream created"
echo ""

echo "Step 4: Starting build from local directory..."
oc start-build $APP_NAME -n $NAMESPACE --from-dir=. --follow
echo "✓ Build complete"
echo ""

echo "Step 5: Deploying Kubernetes resources..."
oc apply -f k8s/deployment.yaml
oc apply -f k8s/service.yaml
oc apply -f k8s/route.yaml
echo "✓ Resources deployed"
echo ""

echo "Step 6: Waiting for deployment to be ready..."
oc rollout status deployment/$APP_NAME -n $NAMESPACE --timeout=5m
echo "✓ Deployment ready"
echo ""

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Access the Locust UI at:"
ROUTE=$(oc get route $APP_NAME -n $NAMESPACE -o jsonpath='{.spec.host}')
echo "https://$ROUTE"
echo ""
echo "Check pod status:"
echo "  oc get pods -n $NAMESPACE -l app=$APP_NAME"
echo ""
echo "View logs:"
echo "  oc logs -f deployment/$APP_NAME -n $NAMESPACE"
echo ""

# Made with Bob
