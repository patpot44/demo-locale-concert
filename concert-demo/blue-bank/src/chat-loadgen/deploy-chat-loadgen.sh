#!/bin/bash
#
# deploy-chat-loadgen.sh
#
# Builds the chat-loadgen image LOCALLY with podman and pushes it to the
# cluster's internal registry. The cluster never pulls from Docker Hub, so
# there is no rate-limit problem and no need for a UBI base image.
#
# Prerequisites:
#   - oc logged into the app cluster (oc login ...)
#   - podman installed and machine started (podman machine start)
#   - Run from the src/chat-loadgen directory (where the Dockerfile lives)
#
# Usage:
#   ./deploy-chat-loadgen.sh
#
set -e

NAMESPACE="demoapps-bank-anthos"
IMAGE_NAME="chat-loadgen"

echo "=========================================="
echo "  Deploying chat-loadgen (local podman build)"
echo "=========================================="

# --- Sanity checks -------------------------------------------------
if ! command -v podman &> /dev/null; then
    echo "ERROR: podman not found. Install it or start the podman machine."
    exit 1
fi

if ! oc whoami &> /dev/null; then
    echo "ERROR: not logged into OpenShift. Run 'oc login' first."
    exit 1
fi

if [ ! -f Dockerfile ]; then
    echo "ERROR: no Dockerfile here. cd into src/chat-loadgen first."
    exit 1
fi

# Confirm we're on the app cluster (the one with the bank app + registry)
SERVER=$(oc whoami --show-server)
echo "Logged into: $SERVER"
echo "Namespace:   $NAMESPACE"
echo ""

# --- Build locally (amd64 so it runs on the x86 cluster) -----------
echo ">> Building image locally with podman..."
podman build --platform linux/amd64 -t ${IMAGE_NAME}:latest .

# --- Resolve the internal registry route ---------------------------
echo ">> Resolving internal registry route..."
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}' 2>/dev/null)

if [ -z "$REGISTRY" ]; then
    echo "   Registry route not exposed. Exposing it now..."
    oc patch configs.imageregistry.operator.openshift.io/cluster \
        --type merge -p '{"spec":{"defaultRoute":true}}'
    echo "   Waiting 15s for the route to come up..."
    sleep 15
    REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}')
fi
echo "   Registry: $REGISTRY"

# --- Login, tag, push ----------------------------------------------
echo ">> Logging into internal registry..."
podman login --tls-verify=false -u kubeadmin -p "$(oc whoami -t)" "$REGISTRY"

echo ">> Tagging and pushing..."
podman tag ${IMAGE_NAME}:latest ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest
podman push --tls-verify=false ${REGISTRY}/${NAMESPACE}/${IMAGE_NAME}:latest

# --- Roll the deployment -------------------------------------------
echo ">> Restarting deployment to pull the new image..."
if oc get deployment ${IMAGE_NAME} -n ${NAMESPACE} &> /dev/null; then
    oc rollout restart deployment/${IMAGE_NAME} -n ${NAMESPACE}
    oc rollout status deployment/${IMAGE_NAME} -n ${NAMESPACE} --timeout=120s
else
    echo "   Deployment '${IMAGE_NAME}' not found in ${NAMESPACE}."
    echo "   Apply your deployment/service/route manifests first, then re-run."
fi

echo ""
echo "=========================================="
echo "  Done."
echo "=========================================="
echo "  Pods:"
oc get pods -n ${NAMESPACE} -l app=${IMAGE_NAME}
echo ""
ROUTE=$(oc get route ${IMAGE_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.host}' 2>/dev/null || true)
if [ -n "$ROUTE" ]; then
    echo "  Locust UI: https://${ROUTE}"
fi
