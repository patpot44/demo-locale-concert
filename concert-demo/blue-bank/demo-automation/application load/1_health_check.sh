#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 1: HEALTH CHECK — Verify everything is ready

# All pods should be 1/1 Running
oc get pods -n $NS

# HPAs should exist for frontend, transaction-processor, userservice
oc get hpa -n $NS

# Kafka brokers healthy, both partitions assigned with lag 0
oc exec concert-bank-kafka-dual-role-0 -n $NS -- bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group transaction-processor --describe 2>/dev/null

# Redis should be empty (just flushed)
echo "redis should be empty:"
oc exec deployment/redis -n $NS -- redis-cli DBSIZE

# Low resource usage across the board
# Under spike load, these services will hit their limits and start GC thrashing or OOMKilling. 
# Normal ~70% for the JVM services (JVM grab heap on start)
echo "We should see low resource usage across the board in our base case:"
echo "POD                          CPU    LIMIT  CPU%   MEM     LIMIT   MEM%"
echo "---                          ---    -----  ----   ---     -----   ----"
for dep in frontend ledgerwriter balancereader transactionhistory transaction-processor redis; do
  cpu_used=$(oc adm top pods -n demoapps-bank-anthos -l app=$dep --no-headers 2>/dev/null | awk '{print $2}' | head -1 | tr -d 'm')
  mem_used=$(oc adm top pods -n demoapps-bank-anthos -l app=$dep --no-headers 2>/dev/null | awk '{print $3}' | head -1 | tr -d 'Mi')
  cpu_limit=$(oc get deployment/$dep -n demoapps-bank-anthos -o jsonpath='{.spec.template.spec.containers[0].resources.limits.cpu}' 2>/dev/null | tr -d 'm')
  mem_limit=$(oc get deployment/$dep -n demoapps-bank-anthos -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}' 2>/dev/null | tr -d 'Mi')
  if [ -n "$cpu_used" ] && [ -n "$cpu_limit" ]; then
    cpu_pct=$((cpu_used * 100 / cpu_limit))
    mem_pct=$((mem_used * 100 / mem_limit))
    printf "%-28s %4sm  %5sm  %3d%%   %4sMi  %5sMi  %3d%%\n" "$dep" "$cpu_used" "$cpu_limit" "$cpu_pct" "$mem_used" "$mem_limit" "$mem_pct"
  fi
done

echo "Health check complete."