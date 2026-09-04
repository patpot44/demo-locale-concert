#!/bin/bash
set -e
# Hard-fail: no silent fallback to built-in model (zero-GPU-load hazard)
[ -z "$VLLM_API_BASE" ] && { echo "FATAL: VLLM_API_BASE not set"; exit 1; }

# All LLM traffic goes through the local capture proxy
export OPENAI_BASE_URL="http://localhost:8080/v1"
export OPENAI_API_KEY="${VLLM_API_KEY:-dummy}"

export HOME=/tmp

# Pin provider/model explicitly so OpenCode can't pick anything else
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/opencode.json << 'EOF'
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "vllm": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://localhost:8080/v1" },
      "models": {
        "granite-coding": {
          "limit": { "context": 32768, "output": 2048 },
          "options": { "temperature": 0.1 }
        }
      }
    }
  },
  "model": "vllm/granite-coding"
}
EOF

cat > ~/.config/opencode/AGENTS.md << 'EOF'
# Tool calling rules
When calling tools, the arguments MUST be a valid JSON object using the exact
parameter names from the tool's schema. Example for the write tool:
{"filePath": "/path/to/file.txt", "content": "file contents"}
Never omit parameter names. Never pass values without keys.
EOF

# [PROVISIONAL] confirm config schema against installed opencode version
mitmdump --mode "reverse:${VLLM_API_BASE%/v1}" --listen-port 8080 \
  --ssl-insecure -w /captures/session.flows &
for i in $(seq 1 20); do
  (echo > /dev/tcp/127.0.0.1/8080) 2>/dev/null && break
  sleep 0.5
done
exec opencode serve --port 3000 --hostname 0.0.0.0