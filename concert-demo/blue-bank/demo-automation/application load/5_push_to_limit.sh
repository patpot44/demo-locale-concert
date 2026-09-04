#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 5: "PUSH TO THE LIMIT" — 5000 users (optional)

# Crank it to 5000 — maxes out all HPAs
oc set env deployment/loadgenerator USERS=5000 -n $NS

echo "⏳ Waiting 90s for full load to ramp..."
sleep 90

# Everything should be at max replicas, high CPU
oc adm top pods -n $NS
oc get hpa -n $NS

# Show Locust stats — higher failure rate, longer response times
oc logs deployment/loadgenerator -n $NS --tail=5

# Talk track:
#   "5000 concurrent users. Every HPA is maxed — frontend, transaction-processor, userservice."
#   "Response times climbing. Failure rate increasing."
#   "Without observability, you're blind to which layer is the bottleneck."
#   "Is it the frontend? The database? Kafka? Redis? Instana tells you in seconds."

echo "✅ System at maximum load."

# Made with Bob
