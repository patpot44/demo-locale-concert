#!/bin/bash
# Deploy GPU Load Testing Service to OpenShift

set -e

NAMESPACE="demoapps-bank-anthos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  GPU Load Testing Service Deployment"
echo "=========================================="
echo ""

# Check if oc is available
if ! command -v oc &> /dev/null; then
    echo "Error: oc CLI not found. Please install OpenShift CLI."
    exit 1
fi

# Check if logged in
if ! oc whoami &> /dev/null; then
    echo "Error: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

# Check if namespace exists
if ! oc get namespace "$NAMESPACE" &> /dev/null; then
    echo "Error: Namespace '$NAMESPACE' does not exist."
    exit 1
fi

echo "Deploying to namespace: $NAMESPACE"
echo ""

# Deploy resources
echo "1. Creating ConfigMap..."
oc apply -f "$SCRIPT_DIR/k8s/configmap.yaml"

echo "2. Creating Deployment..."
oc apply -f "$SCRIPT_DIR/k8s/deployment.yaml"

echo "3. Creating Service..."
oc apply -f "$SCRIPT_DIR/k8s/service.yaml"

echo "4. Creating Route..."
oc apply -f "$SCRIPT_DIR/k8s/route.yaml"

echo ""
echo "Waiting for deployment to be ready..."
oc rollout status deployment/chat-loadgen -n "$NAMESPACE" --timeout=120s

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""

# Get route URL
ROUTE_URL=$(oc get route chat-loadgen -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

if [ -n "$ROUTE_URL" ]; then
    echo "Locust UI: https://$ROUTE_URL"
    echo ""
    echo "Quick Start:"
    echo "  1. Open the URL above in your browser"
    echo "  2. Set users to 5, spawn rate to 1"
    echo "  3. Click 'Start swarming'"
    echo ""
    echo "To view logs:"
    echo "  oc logs -n $NAMESPACE -l app=chat-loadgen -f"
    echo ""
    echo "To switch to vLLM direct mode:"
    echo "  oc set env deployment/chat-loadgen -n $NAMESPACE TARGET_MODE=vllm-direct"
    echo ""
else
    echo "Warning: Could not retrieve route URL"
fi

# Made with Bob
