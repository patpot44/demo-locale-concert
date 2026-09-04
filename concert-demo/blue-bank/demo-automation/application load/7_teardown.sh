#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 7: TEARDOWN — Reset for next run

# Stop load generator
oc set env deployment/loadgenerator USERS=0 -n $NS
oc scale deployment/loadgenerator --replicas=0 -n $NS

# Clean loadgen data (preserves testuser transactions)
oc exec ledger-db-0 -n demoapps-bank-anthos -- psql -U admin -d postgresdb -c "
DROP RULE prevent_delete ON transactions;
DELETE FROM transactions WHERE from_acct LIKE '1111%' OR to_acct LIKE '1111%';
CREATE RULE prevent_delete AS ON DELETE TO transactions DO INSTEAD NOTHING;
"
# and clear accounts but keep the default
oc exec accounts-db-0 -n demoapps-bank-anthos -- psql -U accounts-admin -d accounts-db -c "DELETE FROM users WHERE lastname='LoadTest';"

# Flush caches
oc exec deployment/redis -n $NS -- redis-cli FLUSHALL
oc delete pod -l app=balancereader -n $NS
oc delete pod -l app=transactionhistory -n $NS

# Force replicas back to 1
oc scale deployment/frontend -n $NS --replicas=1
oc scale deployment/transaction-processor -n $NS --replicas=1
oc scale deployment/userservice -n $NS --replicas=1

echo "✅ Teardown complete. Ready for next demo run."

# Made with Bob
