# Export all current deployment configs
for dep in frontend ledgerwriter balancereader transactionhistory transaction-processor loadgenerator userservice contacts; do
  oc get deployment/$dep -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/${dep}-deployment.yaml
  echo "Exported $dep"
done

# Export statefulsets
for ss in ledger-db accounts-db; do
  oc get statefulset/$ss -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/${ss}-statefulset.yaml
  echo "Exported $ss"
done

# Export HPAs (includes the stabilization windows we just added)
oc get hpa -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/hpas.yaml

# Export services
oc get svc -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/services.yaml

# Export routes
oc get route -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/routes.yaml

# Export configmaps
oc get configmap -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/configmaps.yaml

# Export Kafka CRs (cluster, nodepool, topics)
oc get kafka concert-bank-kafka -n demoapps-bank-anthos -o yaml > kubernetes-manifests/kafka/kafka-cluster.yaml
oc get kafkanodepool dual-role -n demoapps-bank-anthos -o yaml > kubernetes-manifests/kafka/kafka-nodepool.yaml
oc get kafkatopic transactions -n demoapps-bank-anthos -o yaml > kubernetes-manifests/kafka/kafka-topic-transactions.yaml
oc get strimzipodset concert-bank-kafka-dual-role -n demoapps-bank-anthos -o yaml > kubernetes-manifests/kafka/kafka-strimzipodset.yaml

# Export Redis
oc get deployment/redis -n demoapps-bank-anthos -o yaml > kubernetes-manifests/redis/redis.yaml
oc get svc/redis -n demoapps-bank-anthos -o yaml > kubernetes-manifests/redis/redis-service.yaml

# Export PVCs (includes the Kafka tmp fix)
oc get pvc -n demoapps-bank-anthos -o yaml > kubernetes-manifests/exported/pvcs.yaml

echo "✅ All manifests exported to kubernetes-manifests/"