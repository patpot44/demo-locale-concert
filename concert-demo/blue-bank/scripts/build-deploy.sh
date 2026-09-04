#!/bin/bash
# Build and deploy Blue Bank frontend + bank-chat
# Usage: ./build-deploy.sh [frontend|chat|both]

NS="demoapps-bank-anthos"
REGISTRY="default-route-openshift-image-registry.apps.o1-968455.cp.fyre.ibm.com"
INTERNAL="image-registry.openshift-image-registry.svc:5000"

# Login to registry
SA_TOKEN=$(oc create token registry-pusher -n $NS)
podman login $REGISTRY -u registry-pusher -p $SA_TOKEN --tls-verify=false

TARGET=${1:-both}

if [ "$TARGET" = "frontend" ] || [ "$TARGET" = "both" ]; then
  echo "🔨 Building frontend..."
  podman build --no-cache --platform linux/amd64 -t $REGISTRY/$NS/frontend:latest ./src/frontend/
  podman push $REGISTRY/$NS/frontend:latest --tls-verify=false
  oc set image deployment/frontend front=$INTERNAL/$NS/frontend:latest -n $NS
  oc rollout restart deployment/frontend -n $NS
  echo "✅ Frontend deployed"
fi

if [ "$TARGET" = "chat" ] || [ "$TARGET" = "both" ]; then
  echo "🔨 Building bank-chat..."
  podman build --no-cache --platform linux/amd64 -t $REGISTRY/$NS/bank-chat:latest ./src/bank-chat/
  podman push $REGISTRY/$NS/bank-chat:latest --tls-verify=false
  oc set image deployment/bank-chat bank-chat=$INTERNAL/$NS/bank-chat:latest -n $NS
  oc rollout restart deployment/bank-chat -n $NS
  echo "✅ Bank-chat deployed"
fi

echo "⏳ Waiting for rollouts..."
[ "$TARGET" = "frontend" ] || [ "$TARGET" = "both" ] && oc rollout status deployment/frontend -n $NS --timeout=120s
[ "$TARGET" = "chat" ] || [ "$TARGET" = "both" ] && oc rollout status deployment/bank-chat -n $NS --timeout=120s
echo "🚀 Done"
