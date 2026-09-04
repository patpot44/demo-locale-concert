# GPU Load Testing Service

Locust-based load generator for the Blue Bank AI chatbot endpoint. Provides web UI control for real-time load adjustment without terminal scripts.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  App Cluster (demoapps-bank-anthos)                                 │
│                                                                     │
│  ┌──────────────────┐     ┌──────────────────┐                     │
│  │  loadgenerator    │     │  chat-loadgen     │                    │
│  │  (existing)       │     │  (new)            │                    │
│  │  Locust → frontend│     │  Locust → chatbot │                    │
│  │  Port 8089 (UI)   │     │  Port 8090 (UI)   │                    │
│  └────────┬─────────┘     └────────┬──────────┘                    │
│           │                         │                               │
│           ▼                         ▼                               │
│  ┌──────────────────┐     ┌──────────────────┐                     │
│  │  frontend (Flask) │     │  bank-chat (Flask)│                    │
│  └──────────────────┘     └────────┬──────────┘                    │
│                                     │ HTTPS                         │
└─────────────────────────────────────┼───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GPU Cluster (bluebank-demo-2)                                      │
│  ┌────────────────────────────────────────────────────┐             │
│  │  vLLM Deployment (autoscaling 1-4 replicas)        │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │            │
│  │  │ vLLM     │  │ vLLM     │  │ vLLM     │  ...    │            │
│  │  │ GPU 0    │  │ GPU 1    │  │ GPU 2    │         │            │
│  │  └──────────┘  └──────────┘  └──────────┘         │            │
│  └────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

## Features

- **Web UI Control**: Adjust load in real-time via Locust dashboard
- **Dual-Mode Operation**: 
  - Mode 1 (chatbot): Tests full path through bank-chat Flask app
  - Mode 2 (vllm-direct): Direct GPU stress testing
- **SSE Streaming Support**: Properly handles Server-Sent Events from both endpoints
- **Custom Metrics**: Tracks TTFT (Time To First Token), tokens/sec, latency
- **Realistic Conversations**: 10 banking conversation templates with weighted tasks
- **SSL Support**: Handles self-signed Fyre certificates

## Deployment

### Prerequisites

- OpenShift cluster with namespace `demoapps-bank-anthos`
- `oc` CLI configured and logged in
- bank-chat service deployed and accessible

### Quick Deploy

```bash
# Deploy all resources
oc apply -f src/chat-loadgen/k8s/

# Verify deployment
oc get pods -n demoapps-bank-anthos -l app=chat-loadgen
oc get route chat-loadgen -n demoapps-bank-anthos
```

### Individual Resources

```bash
# 1. Create ConfigMap with locustfile
oc apply -f src/chat-loadgen/k8s/configmap.yaml

# 2. Deploy the load generator
oc apply -f src/chat-loadgen/k8s/deployment.yaml

# 3. Create Service
oc apply -f src/chat-loadgen/k8s/service.yaml

# 4. Create Route
oc apply -f src/chat-loadgen/k8s/route.yaml
```

### Verify Deployment

```bash
# Check pod status
oc get pods -n demoapps-bank-anthos -l app=chat-loadgen

# Check logs
oc logs -n demoapps-bank-anthos -l app=chat-loadgen -f

# Get Locust UI URL
oc get route chat-loadgen -n demoapps-bank-anthos -o jsonpath='{.spec.host}'
```

## Usage

### Access Locust Web UI

1. Get the route URL:
   ```bash
   echo "https://$(oc get route chat-loadgen -n demoapps-bank-anthos -o jsonpath='{.spec.host}')"
   ```

2. Open in browser: `https://chat-loadgen-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com`

### Running Load Tests

#### Baseline Traffic (5 users)
1. Open Locust UI
2. Set **Number of users**: `5`
3. Set **Spawn rate**: `1` (users per second)
4. Click **Start swarming**
5. Monitor metrics in real-time

#### Moderate Load (60 users)
1. In running test, adjust slider to `60` users
2. Locust automatically ramps up
3. Watch TTFT increase as GPU load grows

#### Stress Test (120+ users)
1. Adjust to `120` users
2. Observe degradation:
   - TTFT climbs to 10-15+ seconds
   - Queue depth increases
   - Error rate may rise
3. Watch for GPU autoscaling trigger
4. Observe recovery as new GPU pods come online

#### Stop Test
- Click **Stop** button in UI
- No need to kill processes or restart pods

### Switching Modes

#### Mode 1: Through Chatbot (Default)
Tests realistic user path: Locust → bank-chat → vLLM

```bash
oc set env deployment/chat-loadgen -n demoapps-bank-anthos TARGET_MODE=chatbot
```

#### Mode 2: Direct to vLLM
Pure GPU stress testing: Locust → vLLM directly

```bash
oc set env deployment/chat-loadgen -n demoapps-bank-anthos TARGET_MODE=vllm-direct
```

After changing mode, wait for pod to restart (~30 seconds).

## Metrics

### Locust Built-in Metrics
- **Requests/sec**: Overall throughput
- **Response time**: P50, P95, P99 latencies
- **Failures**: Error count and rate
- **Users**: Current concurrent users

### Custom GPU Metrics
- **TTFT (Time To First Token)**: Latency until first response token
- **Tokens/sec**: Token generation throughput
- **Stream duration**: Total time to complete response

### Viewing Metrics

1. **Charts Tab**: Real-time graphs of RPS, response times, users
2. **Statistics Tab**: Detailed breakdown by request type
3. **Failures Tab**: Error details and stack traces
4. **Download Data**: Export CSV for analysis

## Demo Procedure

### Two-Browser Demo Setup

**Browser 1 (Left)**: Chatbot UI
- URL: `https://bank-chat-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com`
- Shows user experience

**Browser 2 (Right)**: Locust Dashboard
- URL: `https://chat-loadgen-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com`
- Shows load metrics

### Demo Timeline

```
0:00 - Start with 5 users (baseline)
       "This is normal traffic - 5 concurrent users"
       Show TTFT ~2s, smooth experience

1:00 - Ramp to 60 users
       "Black Friday traffic spike - 60 users"
       TTFT climbs to 5-8s, still acceptable

2:00 - Ramp to 120 users (breaking point)
       "Viral social media post - 120 users"
       TTFT >15s, degraded experience visible
       Queue depth rises, users wait

3:00 - GPU autoscaler triggers
       "Instana detects degradation, triggers autoscale"
       Show new GPU pod starting in OpenShift console

3:30 - New GPU pod comes online
       "Additional GPU capacity available"
       Queue drains, TTFT starts dropping

4:00 - Recovery complete
       "System recovered, TTFT back to 3-4s"
       All 120 users served with good performance
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_MODE` | `chatbot` | Target mode: `chatbot` or `vllm-direct` |
| `CHATBOT_URL` | `https://bank-chat-...` | Bank-chat service URL |
| `VLLM_URL` | `https://vllm-route-...` | vLLM service URL |
| `LOCUST_WEB_PORT` | `8090` | Locust web UI port |

### Adjusting Wait Times

Edit the ConfigMap to change user behavior:

```python
# Baseline (realistic)
wait_time = between(2, 8)

# Stress testing (aggressive)
wait_time = between(0.3, 1.0)
```

Then reload:
```bash
oc apply -f src/chat-loadgen/k8s/configmap.yaml
oc rollout restart deployment/chat-loadgen -n demoapps-bank-anthos
```

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
oc describe pod -n demoapps-bank-anthos -l app=chat-loadgen

# Check logs
oc logs -n demoapps-bank-anthos -l app=chat-loadgen
```

### SSL Certificate Errors

The locustfile includes `client.verify = False` for self-signed Fyre certs. If you see SSL errors, verify this is set in the `on_start` method.

### Connection Timeouts

Increase timeout in locustfile if needed:
```python
with self.user.client.post(
    url,
    json=payload,
    stream=True,
    timeout=300,  # 5 minutes
    ...
)
```

### No Metrics Showing

1. Verify target service is accessible:
   ```bash
   curl -k https://bank-chat-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com/api/health
   ```

2. Check Locust logs for errors:
   ```bash
   oc logs -n demoapps-bank-anthos -l app=chat-loadgen -f
   ```

### High Error Rate

- Check if target service is healthy
- Verify GPU pods are running
- Reduce user count if overwhelming the system
- Check for rate limiting

## Comparison with Existing Load Generator

| Aspect | Bank loadgenerator | Chat loadgenerator |
|--------|-------------------|-------------------|
| **Target** | Frontend (banking transactions) | Chatbot (GPU inference) |
| **Port** | 8089 | 8090 |
| **Protocol** | HTTP form submissions | SSE streaming |
| **Metrics** | Transaction throughput | TTFT, tokens/sec |
| **Bottleneck** | Kafka/Redis/Postgres | GPU compute + KV cache |
| **Purpose** | Test banking pipeline | Test AI inference capacity |

Both can run simultaneously for comprehensive system testing.

## Files

```
src/chat-loadgen/
├── README.md                 # This file
├── locustfile.py            # Load test script (for reference)
└── k8s/
    ├── configmap.yaml       # ConfigMap with locustfile
    ├── deployment.yaml      # Deployment manifest
    ├── service.yaml         # Service manifest
    └── route.yaml           # OpenShift Route
```

## Support

For issues or questions:
1. Check logs: `oc logs -n demoapps-bank-anthos -l app=chat-loadgen`
2. Verify connectivity to target services
3. Review Locust documentation: https://docs.locust.io/