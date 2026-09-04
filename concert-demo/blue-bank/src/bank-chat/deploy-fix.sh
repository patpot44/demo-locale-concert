#!/bin/bash
# Deploy bank-chat with Gunicorn fix

set -e

NAMESPACE="demoapps-bank-anthos"
APP_NAME="bank-chat"

echo "=========================================="
echo "  Deploying bank-chat Gunicorn Fix"
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

echo "Current project: $(oc project -q)"
echo ""

# Option 1: Build from source using OpenShift BuildConfig
echo "Building new image from source..."
cd "$(dirname "$0")"

# Check if BuildConfig exists
if oc get bc/$APP_NAME -n $NAMESPACE &> /dev/null; then
    echo "Using existing BuildConfig..."
    oc start-build $APP_NAME --from-dir=. --follow -n $NAMESPACE
else
    echo "BuildConfig not found. Creating new build..."
    echo ""
    echo "You need to create a BuildConfig first. Run:"
    echo ""
    echo "  oc new-build --name=$APP_NAME --binary=true --strategy=docker -n $NAMESPACE"
    echo "  oc start-build $APP_NAME --from-dir=. --follow -n $NAMESPACE"
    echo ""
    exit 1
fi

echo ""
echo "Build complete! Now restarting deployment..."
echo ""

# Restart the deployment to pick up new image
oc rollout restart deployment/$APP_NAME -n $NAMESPACE

echo "Waiting for rollout to complete..."
oc rollout status deployment/$APP_NAME -n $NAMESPACE --timeout=300s

echo ""
echo "=========================================="
echo "  Deployment Complete!"
echo "=========================================="
echo ""

# Show pod status
echo "Pod status:"
oc get pods -n $NAMESPACE -l app=$APP_NAME

echo ""
echo "Checking logs (last 20 lines):"
oc logs -n $NAMESPACE -l app=$APP_NAME --tail=20

echo ""
echo "To follow logs:"
echo "  oc logs -n $NAMESPACE -l app=$APP_NAME -f"
echo ""
echo "To test the health endpoint:"
echo "  curl -k https://bank-chat-$NAMESPACE.apps.o1-968455.cp.fyre.ibm.com/api/health"
echo ""

# Made with Bob
