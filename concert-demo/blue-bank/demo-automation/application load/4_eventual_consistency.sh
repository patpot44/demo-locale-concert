#!/bin/bash

# if this changes -- need to update!!!!
NS="demoapps-bank-anthos"

# PHASE 4: "EVENTUAL CONSISTENCY" — Show the async tradeoff

# DEMO ACTION: In the browser while under load:
#   1. Make a transfer for most of the starting balance
#   2. Immediately make another transfer
#   3. Both may succeed — because the first hasn't settled to Postgres yet
#   4. Refresh — balance may go negative
#
# Talk track:
#   "I transfer $100,000. It says success."
#   "immediately transfer another $50,000. Also succeeds."
#   "But wait — I only had $122,000. How?"
#   "The first transaction is still in the Kafka queue. Postgres still shows the old balance."
#   "This is eventual consistency. The balance check passes because the data hasn't settled yet."
#   "In production, you'd implement transaction holds or optimistic locking."
#   "Instana can flag — settlement latency as an SLI."

echo "COMPLETED: eventual consistency under load"