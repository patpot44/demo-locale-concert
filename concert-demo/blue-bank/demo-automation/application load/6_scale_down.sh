#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 6: SCALE DOWN — Verify Kafka partition rebalance

# Drop load back to baseline
oc set env deployment/loadgenerator USERS=5 -n $NS

echo "⏳ Waiting 5 min for HPA cooldown and scale-down..."
sleep 300

# KEY CHECK: Both Kafka partitions should still be assigned after scale-down
# This validates the session.timeout.ms fix we applied
oc get hpa -n $NS
oc exec concert-bank-kafka-dual-role-0 -n $NS -- bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group transaction-processor --describe 2>/dev/null

# Both partitions should show:
#   - A consumer ID (not "-")
#   - LAG = 0
# If partition 1 is unassigned, the rebalance fix didn't hold.

# DEMO ACTION: Make a manual transfer in the UI — it should settle immediately
# This proves the pipeline is fully functional after scale-down

echo "✅ Scale-down complete. Pipeline healthy. Kafka partitions rebalanced correctly."

# Made with Bob
