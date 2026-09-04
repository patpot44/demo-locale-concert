#!/bin/bash
# Deploy updated chat-loadgen with error reporting fix

set -e

NAMESPACE="demoapps-bank-anthos"

echo "=========================================="
echo "  Deploying Error Reporting Fix"
echo "=========================================="
echo ""

# Check if logged in
if ! oc whoami &> /dev/null; then
    echo "Error: Not logged into OpenShift. Please run 'oc login' first."
    exit 1
fi

echo "Building updated image..."
oc start-build chat-loadgen --from-dir=. --follow -n "$NAMESPACE"

echo ""
echo "Restarting deployment to use new image..."
oc rollout restart deployment/chat-loadgen -n "$NAMESPACE"

echo ""
echo "Waiting for rollout to complete..."
oc rollout status deployment/chat-loadgen -n "$NAMESPACE" --timeout=120s

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""
echo "Changes applied:"
echo "  - Requests with 0 tokens now reported as failures"
echo "  - Timeout errors will appear in Locust failure stats"
echo "  - Error message includes duration for debugging"
echo ""
echo "To view logs:"
echo "  oc logs -n $NAMESPACE -l app=chat-loadgen -f"
echo ""

# Made with Bob