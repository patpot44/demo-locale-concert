# DevFleet Load Generator

Load testing service for the DevFleet coding agent workload on BlueBank's GPU cluster.

## Overview

This service simulates developer traffic to the vLLM coding assistant service, creating realistic GPU load alongside the existing chatbot workload. It uses Locust to replay pre-captured coding requests from `corpus.json`.

## Architecture

- **Locust**: Python-based load testing framework
- **Corpus**: Pre-captured vLLM API requests (complete payloads, not just prompts)
- **Target**: vLLM coding service on OpenShift GPU cluster
- **Metrics**: TTFT (Time To First Token), token counts, response times

## Local Testing

### Prerequisites

```bash
# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Locust
pip install locust
```

### Run Locally

```bash
# Make sure you're in the devfleet-loadgen directory
cd src/devfleet-loadgen

# Start Locust
locust -f locustfile.py --host=https://vllm-coding-route-bluebank.apps.bluebank-demo-2.cp.fyre.ibm.com

# Open browser to http://localhost:8089
# Configure: 5 users, 1/sec spawn rate
# Start test and verify green status
```

### Expected Results

- ✅ All requests succeed (green status)
- ✅ TTFT metrics appear
- ✅ Token counts > 0
- ✅ No "No tokens received" errors
- ✅ Median response time ~100ms

## OpenShift Deployment

### Prerequisites

1. **OpenShift CLI**: `oc` command installed and logged in
2. **Docker**: Docker daemon running
3. **Access**: Permissions to create namespace and push images

### Deploy to OpenShift

```bash
# Navigate to devfleet-loadgen directory
cd src/devfleet-loadgen

# Run deployment script
./deploy.sh
```

The script will:
1. Create `loadgen` namespace (if needed)
2. Build Docker image
3. Tag and push to OpenShift registry
4. Deploy Kubernetes resources
5. Wait for deployment to be ready
6. Display access URL

### Manual Deployment

If you prefer manual steps:

```bash
# 1. Create namespace
oc create namespace loadgen

# 2. Build and push image
docker build -t devfleet-loadgen:latest .
docker tag devfleet-loadgen:latest image-registry.openshift-image-registry.svc:5000/loadgen/devfleet-loadgen:latest
docker login -u $(oc whoami) -p $(oc whoami -t) image-registry.openshift-image-registry.svc:5000
docker push image-registry.openshift-image-registry.svc:5000/loadgen/devfleet-loadgen:latest

# 3. Deploy resources
oc apply -f k8s/deployment.yaml
oc apply -f k8s/service.yaml
oc apply -f k8s/route.yaml

# 4. Check status
oc get pods -n loadgen -l app=devfleet-loadgen
oc logs -f deployment/devfleet-loadgen -n loadgen
```

## Accessing the Locust UI

After deployment, get the route URL:

```bash
oc get route devfleet-loadgen -n loadgen -o jsonpath='{.spec.host}'
```

Open in browser: `https://devfleet-loadgen-loadgen.apps.bluebank-demo-2.cp.fyre.ibm.com`

## Configuration

### Environment Variables

Set in `k8s/deployment.yaml`:

- `LOCUST_WEB_PORT`: Web UI port (default: 8089)
- `VLLM_CODING_URL`: Target vLLM coding service URL

### Load Profile

Adjust in Locust UI or modify `locustfile.py`:

- **Users**: Number of concurrent simulated developers
- **Spawn Rate**: How fast to ramp up users
- **Wait Time**: Delay between requests (currently 1-5 seconds)

### Recommended Settings

**Baseline Load** (realistic):
- Users: 5-10
- Spawn Rate: 1/sec
- Wait Time: 1-5 seconds

**Stress Test** (heavy):
- Users: 20-50
- Spawn Rate: 2/sec
- Wait Time: 1-5 seconds

## Monitoring

### Check Pod Status

```bash
oc get pods -n loadgen -l app=devfleet-loadgen
```

### View Logs

```bash
oc logs -f deployment/devfleet-loadgen -n loadgen
```

### Metrics in Locust UI

- **Statistics**: Request counts, response times, failures
- **Charts**: RPS, response time percentiles, user count
- **Failures**: Error details if any
- **TTFT**: Custom metric for Time To First Token

## Troubleshooting

### Pod Not Starting

```bash
# Check pod events
oc describe pod -n loadgen -l app=devfleet-loadgen

# Check image pull status
oc get events -n loadgen --sort-by='.lastTimestamp'
```

### High Failure Rate

1. Check vLLM service is running:
   ```bash
   oc get pods -n bluebank -l app=vllm-coding
   ```

2. Verify route is accessible:
   ```bash
   curl -k https://vllm-coding-route-bluebank.apps.bluebank-demo-2.cp.fyre.ibm.com/health
   ```

3. Check Locust logs for errors:
   ```bash
   oc logs -f deployment/devfleet-loadgen -n loadgen
   ```

### No Tokens Received

- Verify `corpus.json` is included in the image
- Check CORPUS_PATH environment variable
- Ensure vLLM service is responding with SSE stream

## Verifying in Turbonomic

After deployment, verify both workloads appear in Turbonomic:

1. **Login to Turbonomic XL**: `https://<fyre-ip>:30089`
2. **Navigate to**: Supply Chain → Workload Controllers
3. **Search for**: `chat-loadgen` and `devfleet-loadgen`
4. **Check GPU metrics**: Both should show GPU utilization
5. **Review actions**: Turbonomic should generate optimization recommendations

## Files

```
devfleet-loadgen/
├── locustfile.py          # Locust load testing script
├── corpus.json            # Pre-captured vLLM requests
├── Dockerfile             # Container image definition
├── deploy.sh              # Automated deployment script
├── README.md              # This file
└── k8s/
    ├── deployment.yaml    # Kubernetes Deployment
    ├── service.yaml       # Kubernetes Service
    └── route.yaml         # OpenShift Route
```

## Next Steps

1. ✅ **Local testing complete** - Verified load generator works
2. 🔄 **Deploy to OpenShift** - Run `./deploy.sh`
3. ⏳ **Start load test** - Configure users in Locust UI
4. ⏳ **Verify in Turbonomic** - Check both workloads visible
5. ⏳ **Monitor GPU utilization** - Confirm resource contention
6. ⏳ **Review optimization actions** - Turbonomic recommendations

## Support

For issues or questions:
- Check logs: `oc logs -f deployment/devfleet-loadgen -n loadgen`
- Review pod status: `oc describe pod -n loadgen -l app=devfleet-loadgen`
- Verify vLLM service: `oc get pods -n bluebank -l app=vllm-coding`

---
