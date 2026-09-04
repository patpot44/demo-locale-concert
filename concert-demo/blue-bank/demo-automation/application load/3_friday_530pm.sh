#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 3: "FRIDAY 5:30 PM" — Traffic spike to 1000 users

# Spike the load — simulates payday rush
oc set env deployment/loadgenerator USERS=1000 -n $NS

# Watch HPAs scale in real time (runs for 2 minutes, prints every 15s)
for i in 1 2 3 4 5 6 7 8; do
  echo "=== $(date +%H:%M:%S) ==="
  oc get hpa -n $NS
  echo "Frontend pods: $(oc get pods -n $NS | grep frontend | grep Running | wc -l | xargs)"
  echo "Transaction-processor pods: $(oc get pods -n $NS | grep transaction-processor | grep Running | wc -l | xargs)"
  echo ""
  sleep 15
done

# Talk track as pods appear:
#   "Friday 5:30. Payday. Users flood in."
#   "Frontend CPU rising... HPA kicks in... 2 pods, 3, 4..."
#   "Transaction-processor scaling too — Kafka consumers rebalancing across partitions."
#   "The system is doing what it's designed to do — autoscaling."

# Show full resource picture
oc adm top pods -n $NS | grep -E "frontend|ledger|transaction-|balance|redis|userservice"

# Show Redis under load
oc exec deployment/redis -n $NS -- redis-cli DBSIZE
oc exec deployment/redis -n $NS -- redis-cli INFO stats | grep evicted

# Show Kafka partition assignment — both partitions should have consumers
oc exec concert-bank-kafka-dual-role-0 -n $NS -- bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group transaction-processor --describe 2>/dev/null

# Show Locust stats — request rate, failure rate
oc logs deployment/loadgenerator -n $NS --tail=5
