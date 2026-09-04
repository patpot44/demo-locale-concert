#!/bin/bash
# DevFleet Load Generator Deployment Script
# Deploys the coding agent load generator to OpenShift

set -e

echo "=========================================="
echo "DevFleet Load Generator Deployment"
echo "=========================================="
echo ""

# Configuration
NAMESPACE="loadgen"
APP_NAME="devfleet-loadgen"
IMAGE_NAME="devfleet-loadgen:latest"
REGISTRY="image-registry.openshift-image-registry.svc:5000"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Step 1: Creating namespace (if it doesn't exist)..."
oc create namespace $NAMESPACE --dry-run=client -o yaml | oc apply -f -
echo "✓ Namespace ready"
echo ""

echo "Step 2: Building Docker image..."
cd "$SCRIPT_DIR"
docker build -t $APP_NAME:latest .
echo "✓ Image built"
echo ""

echo "Step 3: Tagging image for OpenShift registry..."
docker tag $APP_NAME:latest $REGISTRY/$NAMESPACE/$IMAGE_NAME
echo "✓ Image tagged"
echo ""

echo "Step 4: Logging into OpenShift registry..."
# Get the registry token
TOKEN=$(oc whoami -t)
docker login -u $(oc whoami) -p $TOKEN $REGISTRY
echo "✓ Logged in"
echo ""

echo "Step 5: Pushing image to OpenShift registry..."
docker push $REGISTRY/$NAMESPACE/$IMAGE_NAME
echo "✓ Image pushed"
echo ""

echo "Step 6: Deploying Kubernetes resources..."
oc apply -f k8s/deployment.yaml
oc apply -f k8s/service.yaml
oc apply -f k8s/route.yaml
echo "✓ Resources deployed"
echo ""

echo "Step 7: Waiting for deployment to be ready..."
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
