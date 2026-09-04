#!/bin/bash
# Deploy Blue Bank branding to chat-loadgen

set -e

NAMESPACE="demoapps-bank-anthos"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================="
echo "  Deploying Blue Bank Branding"
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

echo "1. Updating ConfigMap with branded locustfile..."
oc apply -f "$SCRIPT_DIR/k8s/configmap.yaml"

echo ""
echo "2. Restarting chat-loadgen deployment..."
oc rollout restart deployment/chat-loadgen -n $NAMESPACE

echo ""
echo "3. Waiting for rollout to complete..."
oc rollout status deployment/chat-loadgen -n $NAMESPACE --timeout=120s

echo ""
echo "=========================================="
echo "  Branding Deployed!"
echo "=========================================="
echo ""

ROUTE_URL=$(oc get route chat-loadgen -n $NAMESPACE -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

if [ -n "$ROUTE_URL" ]; then
    echo "Open Locust UI to see the new Blue Bank branding:"
    echo "  https://$ROUTE_URL"
    echo ""
    echo "You should see:"
    echo "  - Large 'Blue Bank' title"
    echo "  - 'GPU LOAD TESTING SUITE' subtitle"
    echo "  - No Locust logo"
    echo "  - Blue gradient header"
    echo ""
fi

# Made with Bob
