#!/bin/bash
set -e

REGISTRY=default-route-openshift-image-registry.apps.o1-968455.cp.fyre.ibm.com
NAMESPACE=demoapps-bank-anthos
IMAGE=transaction-processor

LATEST_TAG=$(oc get imagestreamtag -n $NAMESPACE 2>/dev/null | grep "$IMAGE:" | sed 's/.*:v//' | sed 's/ .*//' | sort -n | tail -1)
if [ -z "$LATEST_TAG" ]; then
    NEXT_TAG="v1"
else
    NEXT_TAG="v$((LATEST_TAG + 1))"
fi
echo "🏷  Building as $IMAGE:$NEXT_TAG"

SA_TOKEN=$(oc create token registry-pusher -n $NAMESPACE)
podman login $REGISTRY -u registry-pusher -p $SA_TOKEN --tls-verify=false

podman build --platform linux/amd64 -t $REGISTRY/$NAMESPACE/$IMAGE:$NEXT_TAG ./src/ledger/transaction-processor/

podman push $REGISTRY/$NAMESPACE/$IMAGE:$NEXT_TAG --tls-verify=false

oc set image deployment/transaction-processor transaction-processor=image-registry.openshift-image-registry.svc:5000/$NAMESPACE/$IMAGE:$NEXT_TAG -n $NAMESPACE

oc rollout status deployment/transaction-processor -n $NAMESPACE
echo "✅ $IMAGE:$NEXT_TAG deployed"
