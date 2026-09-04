#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 0: RESET — Clean slate before demo

# Stop the load generator completely
oc set env deployment/loadgenerator USERS=0 -n $NS
oc scale deployment/loadgenerator --replicas=0 -n $NS

# Remove loadgen transactions (must drop prevent_delete rule first, then restore it)
oc exec ledger-db-0 -n demoapps-bank-anthos -- psql -U admin -d postgresdb -c "
DROP RULE prevent_delete ON transactions;
DELETE FROM transactions WHERE from_acct LIKE '1111%' OR to_acct LIKE '1111%';
CREATE RULE prevent_delete AS ON DELETE TO transactions DO INSTEAD NOTHING;
"

# Remove loadgen-created user accounts (lastname='LoadTest' set in our locustfile)
oc exec accounts-db-0 -n demoapps-bank-anthos -- psql -U accounts-admin -d accounts-db -c "DELETE FROM users WHERE lastname='LoadTest';"

# Flush Redis cache so stale balances/transactions don't persist
oc exec deployment/redis -n $NS -- redis-cli FLUSHALL

# Restart balancereader and transactionhistory to clear Guava in-memory cache
oc delete pod -l app=balancereader -n $NS
oc delete pod -l app=transactionhistory -n $NS

# Force all HPAs back to minimum replicas
oc scale deployment/frontend -n $NS --replicas=1
oc scale deployment/transaction-processor -n $NS --replicas=1
oc scale deployment/userservice -n $NS --replicas=1

# Wait for pods to stabilize
echo "Awaiting 45s for pods to restart..."
sleep 45

echo "Reset complete. Proceed."

# Made with Bob
