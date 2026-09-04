#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 2: "NORMAL DAY" — Baseline with light load

# Bring loadgenerator back with minimal traffic (5 users)
oc scale deployment/loadgenerator --replicas=1 -n $NS
oc set env deployment/loadgenerator USERS=5 -n $NS

# Wait for loadgen to start and generate some traffic
echo "⏳ Waiting 60s for baseline traffic to flow..."
sleep 60

# Show the system at rest: low CPU, 1 replica each, healthy
oc adm top pods -n $NS | grep -E "frontend|ledger|transaction-|balance|redis"
oc get hpa -n $NS

# Verify transactions are flowing end-to-end
oc logs deployment/ledgerwriter -n $NS --tail=3 | grep "Kafka"          # ledgerwriter → Kafka
oc logs deployment/transaction-processor -n $NS --tail=3                 # Kafka → Postgres
oc logs deployment/balancereader -n $NS | grep "loaded from" | tail -3   # Redis/DB reads

# Show Redis is populating
oc exec deployment/redis -n $NS -- redis-cli DBSIZE

# DEMO ACTION: Open browser, log in as testuser, show balance and transaction history
# URL: http://frontend-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com
# Talk track: "Normal day. System is coasting. Single-digit CPU. Transactions settle instantly."

echo "✅ Baseline established. System healthy and responsive."

# Made with Bob
