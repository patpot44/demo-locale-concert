# GPU Load Testing Demo - Quick Reference

## Pre-Demo Setup

### 1. Deploy the Service
```bash
cd src/chat-loadgen
./deploy.sh
```

### 2. Open Two Browser Windows

**Left Window**: Chatbot UI
```
https://bank-chat-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com
```

**Right Window**: Locust Dashboard
```
https://chat-loadgen-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com
```

### 3. Verify Services
```bash
# Check chat-loadgen is running
oc get pods -n demoapps-bank-anthos -l app=chat-loadgen

# Check bank-chat is running
oc get pods -n demoapps-bank-anthos -l app=bank-chat

# Check vLLM pods on GPU cluster
oc get pods -n bluebank -l app=vllm-granite
```

---

## Demo Script

### Phase 1: Baseline (0:00 - 1:00)

**Action**: Start with 5 users
1. In Locust UI, set:
   - Number of users: `5`
   - Spawn rate: `1`
2. Click **Start swarming**

**Talking Points**:
- "This represents normal traffic - 5 concurrent users asking banking questions"
- "Notice the Time to First Token (TTFT) is around 2 seconds"
- "The chatbot responds quickly and smoothly"
- Point to the chatbot UI showing fast responses

**Expected Metrics**:
- TTFT: ~2s
- Requests/sec: ~0.5-1
- No errors
- GPU utilization: ~25%

---

### Phase 2: Moderate Load (1:00 - 2:00)

**Action**: Ramp to 60 users
1. Adjust slider or type `60` in the user field
2. Locust automatically ramps up

**Talking Points**:
- "Now we're simulating a Black Friday traffic spike - 60 concurrent users"
- "TTFT is climbing to 5-8 seconds as the GPU gets busier"
- "Still acceptable, but users are starting to notice the delay"
- "The single GPU is handling the load but approaching capacity"

**Expected Metrics**:
- TTFT: 5-8s
- Requests/sec: 5-8
- Queue depth: 5-10
- GPU utilization: ~80%

---

### Phase 3: Breaking Point (2:00 - 3:00)

**Action**: Ramp to 120 users
1. Adjust to `120` users
2. Watch degradation happen

**Talking Points**:
- "A viral social media post drives 120 concurrent users to the chatbot"
- "TTFT has jumped to 15+ seconds - this is a poor user experience"
- "Look at the queue depth climbing - requests are backing up"
- "The GPU is maxed out at 100% utilization"
- "This is where traditional monitoring would alert, but we have autoscaling"

**Expected Metrics**:
- TTFT: 15-20s
- Queue depth: 30-50
- GPU utilization: 100%
- Possible errors starting

**Switch to Instana/OpenShift Console**:
- Show GPU metrics spiking
- Show autoscaler triggering
- Show new pod being created

---

### Phase 4: Recovery (3:00 - 4:00)

**Action**: Watch automatic recovery
1. Keep 120 users running
2. Wait for new GPU pod to come online

**Talking Points**:
- "Instana detected the degradation and triggered the autoscaler"
- "A new GPU pod is spinning up - this takes about 60 seconds"
- "Watch as the new capacity comes online..."
- "The queue is draining, TTFT is dropping"
- "Now with 2 GPUs, we're handling all 120 users with good performance"

**Expected Metrics**:
- TTFT: drops from 15s → 3-4s
- Queue depth: drops to near 0
- Requests/sec: increases
- GPU utilization: ~50% per GPU (load balanced)

---

### Phase 5: Wrap-Up (4:00+)

**Action**: Stop the test
1. Click **Stop** in Locust UI
2. Show final statistics

**Talking Points**:
- "The system automatically scaled to meet demand"
- "Users experienced degradation for about 60 seconds during scale-up"
- "Once scaled, performance returned to normal"
- "When traffic drops, the system will scale back down to save costs"
- "All controlled through Instana's AI-powered observability"

**Show Final Stats**:
- Total requests processed
- Average TTFT across the test
- Error rate (should be low)
- Total tokens generated

---

## Troubleshooting During Demo

### Locust UI Not Loading
```bash
oc get route chat-loadgen -n demoapps-bank-anthos
oc logs -n demoapps-bank-anthos -l app=chat-loadgen
```

### High Error Rate
- Reduce user count temporarily
- Check if bank-chat or vLLM pods are healthy
- Verify network connectivity

### No Autoscaling Happening
- Verify HPA is configured on vLLM deployment
- Check GPU metrics are being collected
- May need to wait longer (up to 2 minutes)

### Chatbot Not Responding
```bash
# Check bank-chat
oc get pods -n demoapps-bank-anthos -l app=bank-chat

# Check vLLM
oc get pods -n bluebank -l app=vllm-granite

# Test directly
curl -k https://bank-chat-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com/api/health
```

---

## Alternative Demo: Direct vLLM Mode

For pure GPU stress testing without the Flask layer:

```bash
# Switch to vLLM direct mode
oc set env deployment/chat-loadgen -n demoapps-bank-anthos TARGET_MODE=vllm-direct

# Wait for pod restart
oc rollout status deployment/chat-loadgen -n demoapps-bank-anthos

# Run same demo script
# Metrics will be slightly different (lower latency, higher throughput)
```

---

## Post-Demo Cleanup

```bash
# Stop the load test (click Stop in UI)

# Optional: Delete the load generator
oc delete -f src/chat-loadgen/k8s/

# Or just scale to 0
oc scale deployment/chat-loadgen -n demoapps-bank-anthos --replicas=0
```

---

## Key Metrics to Highlight

| Metric | Baseline | Under Load | After Scale |
|--------|----------|------------|-------------|
| TTFT | 2s | 15-20s | 3-4s |
| Queue Depth | 0 | 30-50 | 0-5 |
| GPU Utilization | 25% | 100% | 50% each |
| Requests/sec | 1 | 8-10 | 15-20 |
| Error Rate | 0% | 0-5% | 0% |

---

## Talking Points Summary

1. **Problem**: GPU inference is expensive and unpredictable
2. **Challenge**: Traditional scaling doesn't work (can't split a GPU)
3. **Solution**: Instana monitors GPU metrics and triggers pod-level autoscaling
4. **Result**: Automatic capacity adjustment based on real user experience
5. **Value**: Cost optimization + performance guarantee

---

## Questions to Anticipate

**Q: How long does scale-up take?**
A: About 60 seconds for a new GPU pod to be ready and serving traffic.

**Q: What triggers the autoscaling?**
A: Instana monitors TTFT, queue depth, and GPU utilization. When thresholds are exceeded, it triggers the HPA.

**Q: Does this work with other LLM providers?**
A: Yes, the pattern works with any GPU-based inference service (vLLM, TGI, TensorRT-LLM, etc.)

**Q: What about scale-down?**
A: After traffic drops, the system waits 5 minutes then scales down to save costs.

**Q: Can you show the cost savings?**
A: Each H100 GPU costs ~$3/hour. Autoscaling from 1→4→1 saves ~$18/hour during off-peak times.