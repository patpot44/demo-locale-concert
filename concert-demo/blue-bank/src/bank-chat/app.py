"""
Blue Bank AI Assistant UI

=== WATSONX ===
    pip install flask langchain-ibm langchain-openai
    export LLM_PROVIDER=watsonx
    export WATSONX_API_KEY=your-api-key
    export WATSONX_PROJECT_ID=your-project-id
    export WATSONX_URL=https://us-south.ml.cloud.ibm.com
    export MODEL_NAME=ibm/granite-3-8b-instruct
    python app.py

=== VLLM ===
    pip install flask langchain-openai
    export LLM_PROVIDER=vllm
    export VLLM_API_BASE=http://your-vllm-cluster:8000/v1
    export VLLM_API_KEY=dummy
    export MODEL_NAME=granite-30b
    python app.py

Embed via iframe:
    <iframe src="http://localhost:5001" width="400" height="600"></iframe>
"""

import os
import json
from flask import Flask, request, Response, stream_with_context

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "watsonx")       # "watsonx" or "vllm"
MODEL_NAME     = os.getenv("MODEL_NAME", "ibm/granite-3-8b-instruct")
PORT           = int(os.getenv("PORT", "5001"))
SYSTEM_PROMPT  = os.getenv("SYSTEM_PROMPT",
    "You are Blue Bank's AI assistant. Help customers with account questions, "
    "transfers, and general banking inquiries. Be concise and professional."
)

# watsonx-specific
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")

# vLLM-specific
VLLM_API_BASE = os.getenv("VLLM_API_BASE", "http://localhost:8000/v1")
VLLM_API_KEY  = os.getenv("VLLM_API_KEY", "dummy")


# ---------------------------------------------------------------------------
# LLM Factory — single swap point
# ---------------------------------------------------------------------------
def create_llm():
    """
    Returns a LangChain BaseChatModel.
    Both ChatWatsonx and ChatOpenAI implement the same interface:
      .invoke(messages) -> AIMessage
      .stream(messages) -> Iterator[AIMessageChunk]
    """
    if LLM_PROVIDER == "watsonx":
        from langchain_ibm import ChatWatsonx
        return ChatWatsonx(
            model_id=MODEL_NAME,
            url=WATSONX_URL,
            api_key=WATSONX_API_KEY,
            project_id=WATSONX_PROJECT_ID,
            params={
                "temperature": 0.7,
                "max_tokens": 1024,
            },
        )
    elif LLM_PROVIDER == "vllm":
        import httpx
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=MODEL_NAME,
            openai_api_base=VLLM_API_BASE,
            openai_api_key=VLLM_API_KEY,
            temperature=0.7,
            max_tokens=1024,
            streaming=True,
            timeout=300,
            http_client=httpx.Client(verify=False, timeout=300),
            http_async_client=httpx.AsyncClient(verify=False, timeout=300),
        )
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Use 'watsonx' or 'vllm'.")


llm = create_llm()
app = Flask(__name__)


# ---------------------------------------------------------------------------
# Convert frontend messages to LangChain message objects
# ---------------------------------------------------------------------------
def to_langchain_messages(messages):
    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
    lc_messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))
    return lc_messages


# ---------------------------------------------------------------------------
# API — streaming chat
# ---------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    messages = data.get("messages", [])
    # Only send last 4 messages to avoid context overflow
    recent = messages[-4:] if len(messages) > 4 else messages
    lc_messages = to_langchain_messages(recent)

    def generate():
        try:
            for chunk in llm.stream(lc_messages):
                token = chunk.content
                if token:
                    yield f"data: {json.dumps({'content': token})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.route("/api/health")
def health():
    return {
        "status": "ok",
        "provider": LLM_PROVIDER,
        "model": MODEL_NAME,
    }


# ---------------------------------------------------------------------------
# Frontend — single HTML page with Carbon Web Components
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return HTML_PAGE


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Blue Bank — AI Assistant</title>

  <!-- IBM Plex fonts (Carbon's typeface) -->
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />



  <style>
    /* ------------------------------------------------------------------ */
    /* Carbon g100 (dark) palette                                         */
    /* ------------------------------------------------------------------ */
    :root {
      --cds-background:           #161616;
      --cds-background-hover:     #1e1e1e;
      --cds-layer-01:             #262626;
      --cds-layer-02:             #393939;
      --cds-layer-hover:          #333333;
      --cds-text-primary:         #f4f4f4;
      --cds-text-secondary:       #c6c6c6;
      --cds-text-placeholder:     #6f6f6f;
      --cds-text-on-color:        #ffffff;
      --cds-link-primary:         #78a9ff;
      --cds-border-subtle:        #393939;
      --cds-border-strong:        #6f6f6f;
      --cds-button-primary:       #0f62fe;
      --cds-button-primary-hover: #0050e6;
      --cds-button-primary-active:#002d9c;
      --cds-support-error:        #ff8389;
      --cds-support-success:      #42be65;
      --cds-ai-aura:              #4589ff;

      --cds-spacing-03: 0.5rem;
      --cds-spacing-04: 0.75rem;
      --cds-spacing-05: 1rem;
      --cds-spacing-06: 1.5rem;
      --cds-spacing-07: 2rem;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    html, body {
      height: 100%;
      font-family: 'IBM Plex Sans', -apple-system, sans-serif;
      font-size: 14px;
      background: var(--cds-background);
      color: var(--cds-text-primary);
    }

    .shell {
      display: flex;
      flex-direction: column;
      height: 100vh;
      max-width: 900px;
      margin: 0 auto;
    }

    /* Header */
    .header {
      display: flex;
      align-items: center;
      gap: var(--cds-spacing-04);
      padding: var(--cds-spacing-04) var(--cds-spacing-05);
      border-bottom: 1px solid var(--cds-border-subtle);
      background: var(--cds-layer-01);
      flex-shrink: 0;
    }
    .header-icon {
      width: 32px; height: 32px;
      background: var(--cds-button-primary);
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
    }
    .header-icon svg { width: 18px; height: 18px; fill: #fff; }
    .header h1 { font-size: 14px; font-weight: 600; letter-spacing: 0.16px; }
    .header .tag {
      font-size: 12px;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--cds-text-secondary);
      background: var(--cds-layer-02);
      padding: 2px 8px;
      border-radius: 4px;
    }
    .header .provider-tag {
      font-size: 11px;
      font-family: 'IBM Plex Mono', monospace;
      color: var(--cds-ai-aura);
      background: rgba(69, 137, 255, 0.1);
      padding: 2px 8px;
      border-radius: 4px;
    }
    .header .status {
      margin-left: auto;
      display: flex; align-items: center; gap: 6px;
      font-size: 12px; color: var(--cds-text-secondary);
    }
    .status-dot {
      width: 8px; height: 8px; border-radius: 50%;
      background: var(--cds-support-success);
      animation: pulse 2s infinite;
    }
    .status-dot.error { background: var(--cds-support-error); animation: none; }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }

    /* Messages area */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: var(--cds-spacing-05);
      display: flex;
      flex-direction: column;
      gap: var(--cds-spacing-04);
      scroll-behavior: smooth;
    }

    .message {
      display: flex;
      gap: var(--cds-spacing-04);
      max-width: 85%;
      animation: fadeIn 0.2s ease-out;
    }
    .message.user { align-self: flex-end; flex-direction: row-reverse; }
    .message.assistant { align-self: flex-start; }

    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .avatar {
      width: 32px; height: 32px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; font-size: 14px; font-weight: 600;
    }
    .assistant .avatar {
      background: linear-gradient(135deg, var(--cds-ai-aura), var(--cds-button-primary));
      color: #fff;
    }
    .user .avatar { background: var(--cds-layer-02); color: var(--cds-text-secondary); }

    .bubble {
      padding: var(--cds-spacing-04) var(--cds-spacing-05);
      border-radius: 12px;
      line-height: 1.5;
      font-size: 14px;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .assistant .bubble {
      background: var(--cds-layer-01);
      border: 1px solid var(--cds-border-subtle);
      border-bottom-left-radius: 4px;
    }
    .user .bubble {
      background: var(--cds-button-primary);
      color: var(--cds-text-on-color);
      border-bottom-right-radius: 4px;
    }

    .typing { display: flex; gap: 4px; padding: 4px 0; }
    .typing span {
      width: 6px; height: 6px; border-radius: 50%;
      background: var(--cds-text-secondary);
      animation: blink 1.4s infinite;
    }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
      0%, 80%, 100% { opacity: 0.3; }
      40% { opacity: 1; }
    }

    /* Welcome state */
    .welcome {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: var(--cds-spacing-05);
      color: var(--cds-text-secondary);
      text-align: center;
      padding: var(--cds-spacing-07);
    }
    .welcome-icon {
      width: 64px; height: 64px;
      background: linear-gradient(135deg, var(--cds-ai-aura), var(--cds-button-primary));
      border-radius: 16px;
      display: flex; align-items: center; justify-content: center;
    }
    .welcome-icon svg { width: 32px; height: 32px; fill: #fff; }
    .welcome h2 { font-size: 20px; font-weight: 600; color: var(--cds-text-primary); }
    .welcome p { font-size: 14px; max-width: 360px; line-height: 1.5; }

    .suggestions {
      display: flex; flex-wrap: wrap; gap: 8px;
      justify-content: center; margin-top: var(--cds-spacing-03);
    }
    .suggestion {
      background: var(--cds-layer-01);
      border: 1px solid var(--cds-border-subtle);
      color: var(--cds-text-primary);
      padding: 8px 16px;
      border-radius: 20px;
      font-size: 13px;
      cursor: pointer;
      transition: all 0.15s;
      font-family: inherit;
    }
    .suggestion:hover {
      background: var(--cds-layer-hover);
      border-color: var(--cds-border-strong);
    }

    /* Input area */
    .input-area {
      padding: var(--cds-spacing-04) var(--cds-spacing-05);
      border-top: 1px solid var(--cds-border-subtle);
      background: var(--cds-layer-01);
      flex-shrink: 0;
    }
    .input-row {
      display: flex;
      gap: var(--cds-spacing-03);
      align-items: flex-end;
    }
    .input-row textarea {
      flex: 1;
      resize: none;
      border: 1px solid var(--cds-border-subtle);
      border-radius: 8px;
      background: var(--cds-background);
      color: var(--cds-text-primary);
      padding: 10px 14px;
      font-family: inherit;
      font-size: 14px;
      line-height: 1.5;
      min-height: 42px;
      max-height: 120px;
      outline: none;
      transition: border-color 0.15s;
    }
    .input-row textarea::placeholder { color: var(--cds-text-placeholder); }
    .input-row textarea:focus { border-color: var(--cds-button-primary); }

    .send-btn {
      width: 42px; height: 42px;
      background: var(--cds-button-primary);
      border: none; border-radius: 8px;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      transition: background 0.15s;
      flex-shrink: 0;
    }
    .send-btn:hover { background: var(--cds-button-primary-hover); }
    .send-btn:active { background: var(--cds-button-primary-active); }
    .send-btn:disabled { opacity: 0.3; cursor: not-allowed; }
    .send-btn svg { width: 18px; height: 18px; fill: #fff; }

    .input-meta {
      display: flex; justify-content: space-between;
      padding-top: 6px;
      font-size: 11px;
      color: var(--cds-text-placeholder);
      font-family: 'IBM Plex Mono', monospace;
    }

    .messages::-webkit-scrollbar { width: 6px; }
    .messages::-webkit-scrollbar-track { background: transparent; }
    .messages::-webkit-scrollbar-thumb { background: var(--cds-border-subtle); border-radius: 3px; }

    /* Token rate indicator */
    .token-rate {
      display: flex;
      align-items: center;
      gap: 6px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 12px;
      color: var(--cds-text-secondary);
      padding: 2px 10px;
      border-radius: 4px;
      background: var(--cds-layer-02);
      margin-left: 8px;
      transition: all 0.3s;
    }
    .token-rate .rate-dot {
      width: 8px; height: 8px; border-radius: 50%;
      transition: background 0.3s;
      background: var(--cds-text-placeholder);
    }
    .token-rate.healthy { color: var(--cds-support-success); }
    .token-rate.healthy .rate-dot { background: var(--cds-support-success); }
    .token-rate.slow { color: #f1c21b; }
    .token-rate.slow .rate-dot { background: #f1c21b; }
    .token-rate.degraded { color: var(--cds-support-error); }
    .token-rate.degraded .rate-dot { background: var(--cds-support-error); }
  
  </style>
</head>
<body>
  <div class="shell">

    <div class="header">
      <div class="header-icon">
        <svg viewBox="0 0 32 32"><path d="M16 2a14 14 0 1 0 14 14A14 14 0 0 0 16 2zm0 26a12 12 0 1 1 12-12 12 12 0 0 1-12 12z"/><path d="M16 10a2 2 0 1 0 2 2 2 2 0 0 0-2-2zm1 10h-2v-4h2z"/></svg>
      </div>
      <h1>Blue Bank Assistant</h1>
      <span class="tag" id="modelTag">—</span>
      <span class="provider-tag" id="providerTag">—</span>
      <div class="token-rate" id="tokenRate" style="display:none;">
        <div class="rate-dot"></div>
        <span id="rateValue">—</span>
      </div>
      <div class="status">
        <div class="status-dot" id="statusDot"></div>
        <span id="statusText">Connecting…</span>
      </div>
    </div>

    <div class="messages" id="messages">
      <div class="welcome" id="welcome">
        <div class="welcome-icon">
          <svg viewBox="0 0 32 32"><path d="M16 2a14 14 0 1 0 14 14A14 14 0 0 0 16 2zm0 26a12 12 0 1 1 12-12 12 12 0 0 1-12 12z"/><circle cx="11" cy="13" r="1.5"/><circle cx="21" cy="13" r="1.5"/><path d="M16 24a6 6 0 0 1-5.2-3h10.4a6 6 0 0 1-5.2 3z"/></svg>
        </div>
        <h2>How can I help you today?</h2>
        <p>Ask about your accounts, transfers, or anything related to Concert National Bank.</p>
        <div class="suggestions">
          <button class="suggestion" onclick="useSuggestion(this)">What's my balance?</button>
          <button class="suggestion" onclick="useSuggestion(this)">Show recent transactions</button>
          <button class="suggestion" onclick="useSuggestion(this)">Help me transfer funds</button>
          <button class="suggestion" onclick="useSuggestion(this)">What are your hours?</button>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div class="input-row">
        <textarea id="input" placeholder="Ask Blue Bank a question…" rows="1"
          onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
        <button class="send-btn" id="sendBtn" onclick="sendMessage()" disabled>
          <svg viewBox="0 0 32 32"><path d="M28 16L4 27l3-11L4 5zm-3 0L9.5 16H7l2.2-8z"/></svg>
        </button>
      </div>
      <div class="input-meta">
        <span>Press Enter to send · Shift+Enter for new line</span>
        <span id="charCount">0 / 2000</span>
      </div>
    </div>

  </div>

  <script>
  
  const history = [];
    let streaming = false;

    const $messages  = document.getElementById('messages');
    const $input     = document.getElementById('input');
    const $sendBtn   = document.getElementById('sendBtn');
    const $welcome   = document.getElementById('welcome');
    const $status    = document.getElementById('statusText');
    const $dot       = document.getElementById('statusDot');
    const $model     = document.getElementById('modelTag');
    const $provider  = document.getElementById('providerTag');
    const $charCount = document.getElementById('charCount');
    const $tokenRate = document.getElementById('tokenRate');
    const $rateValue = document.getElementById('rateValue');

    // Token rate tracker
    class TokenRateTracker {
      constructor(windowSize = 20) {
        this.windowSize = windowSize;
        this.timestamps = [];
        this.smoothedTps = 0;
        this.alpha = 0.3; // smoothing factor: lower = more stable
      }
      reset() { this.timestamps = []; this.smoothedTps = 0; }
      recordToken() {
        this.timestamps.push(Date.now());
        if (this.timestamps.length > this.windowSize) this.timestamps.shift();
      }
      getTokensPerSecond() {
        if (this.timestamps.length < 3) return 0;
        const now = Date.now();
        const lastToken = this.timestamps[this.timestamps.length - 1];
        // If no token in last 2 seconds, rate is effectively 0
        if (now - lastToken > 2000) {
          this.smoothedTps = 0;
          return 0;
        }
        const elapsed = (lastToken - this.timestamps[0]) / 1000;
        if (elapsed <= 0) return 0;
        const raw = (this.timestamps.length - 1) / elapsed;
        this.smoothedTps = this.smoothedTps === 0
          ? raw
          : this.alpha * raw + (1 - this.alpha) * this.smoothedTps;
        return this.smoothedTps;
      }

      getStatus() {
        const tps = this.getTokensPerSecond();
        if (tps === 0)  return { cls: '',         label: 'Waiting…',  tps: 0 };
        if (tps < 5)    return { cls: 'degraded',  label: 'Degraded',  tps };
        if (tps < 15)   return { cls: 'slow',      label: 'Slow',      tps };
        return                  { cls: 'healthy',   label: 'Healthy',   tps };
      }
    }


    const tracker = new TokenRateTracker();

    function updateRateDisplay(status) {
      $tokenRate.style.display = 'flex';
      $tokenRate.className = 'token-rate ' + status.cls;
      if (status.ttft && status.tps > 0) {
        $rateValue.textContent = status.ttft + ' wait · ' + status.tps.toFixed(1) + ' tok/s · ' + status.label;
      } else if (status.ttft) {
        $rateValue.textContent = status.ttft + ' · ' + status.label;
      } else if (status.tps > 0) {
        $rateValue.textContent = status.tps.toFixed(1) + ' tok/s · ' + status.label;
      } else {
        $rateValue.textContent = status.label;
      }
    }

    function hideRate() {
      $tokenRate.className = 'token-rate';
      $rateValue.textContent = 'Ready';
      $tokenRate.style.display = 'flex';
    }

    fetch('/api/health')
      .then(r => r.json())
      .then(d => {
        $status.textContent = 'Connected';
        $dot.classList.remove('error');
        $model.textContent = d.model || '—';
        $provider.textContent = d.provider || '—';
      })
      .catch(() => {
        $status.textContent = 'Disconnected';
        $dot.classList.add('error');
      });

    $input.addEventListener('input', () => {
      $sendBtn.disabled = !$input.value.trim() || streaming;
      $charCount.textContent = `${$input.value.length} / 2000`;
    });

    function autoResize(el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }

    function handleKey(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    }

    function useSuggestion(btn) {
      $input.value = btn.textContent;
      $input.dispatchEvent(new Event('input'));
      sendMessage();
    }

    function addMessage(role, content) {
      if ($welcome) $welcome.remove();
      const wrap = document.createElement('div');
      wrap.className = `message ${role}`;
      const avatar = document.createElement('div');
      avatar.className = 'avatar';
      avatar.textContent = role === 'user' ? 'You' : 'AI';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.textContent = content || '';
      wrap.appendChild(avatar);
      wrap.appendChild(bubble);
      $messages.appendChild(wrap);
      $messages.scrollTop = $messages.scrollHeight;
      return bubble;
    }

    function addTyping() {
      const wrap = document.createElement('div');
      wrap.className = 'message assistant';
      wrap.id = 'typing';
      const avatar = document.createElement('div');
      avatar.className = 'avatar';
      avatar.textContent = 'AI';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>';
      wrap.appendChild(avatar);
      wrap.appendChild(bubble);
      $messages.appendChild(wrap);
      $messages.scrollTop = $messages.scrollHeight;
    }

    function removeTyping() {
      const el = document.getElementById('typing');
      if (el) el.remove();
    }

    async function sendMessage() {
      const text = $input.value.trim();
      if (!text || streaming) return;
      $input.value = '';
      $input.style.height = 'auto';
      $sendBtn.disabled = true;
      $charCount.textContent = '0 / 2000';
      addMessage('user', text);
      history.push({ role: 'user', content: text });
      addTyping();
      streaming = true;
      tracker.reset();
      let firstTokenReceived = false;
      let ttftStart = Date.now();
      updateRateDisplay({ cls: '', label: 'Waiting…', tps: 0, ttft: null });

      // Watchdog: update display every 500ms with escalating severity
      const rateWatchdog = setInterval(() => {
        if (!streaming) { clearInterval(rateWatchdog); return; }
        const waitSec = ((Date.now() - ttftStart) / 1000).toFixed(1);
        const status = tracker.getStatus();
        if (!firstTokenReceived) {
          if (waitSec > 10) {
            updateRateDisplay({ cls: 'degraded', label: 'Service Degraded', tps: 0, ttft: waitSec + 's wait' });
          } else if (waitSec > 3) {
            updateRateDisplay({ cls: 'slow', label: 'Queued', tps: 0, ttft: waitSec + 's wait' });
          } else {
            updateRateDisplay({ cls: '', label: 'Waiting…', tps: 0, ttft: null });
          }
        } else {
          updateRateDisplay({ ...status, ttft: null });
        }
      }, 500);

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: history }),
        });
        removeTyping();
        const bubble = addMessage('assistant', '');
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop();
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const payload = line.slice(6);
            if (payload === '[DONE]') break;
            try {
              const data = JSON.parse(payload);
              if (data.error) {
                bubble.textContent = `Error: ${data.error}`;
                bubble.style.color = 'var(--cds-support-error)';
                break;
              }
              if (data.content) {
                if (!firstTokenReceived) {
                  firstTokenReceived = true;
                }
                fullContent += data.content;
                bubble.textContent = fullContent;
                $messages.scrollTop = $messages.scrollHeight;
                tracker.recordToken();
                if (tracker.timestamps.length % 4 === 0) {
                  updateRateDisplay(tracker.getStatus());
                }
              }
            } catch {}
          }
        }
        // After streaming completes, check for garbage
        const isGarbage = /(.)\1{20,}/.test(fullContent) || fullContent.length < 5;
        if (!isGarbage) {
          history.push({ role: 'assistant', content: fullContent });
        }
        // If garbage, skip adding to history so next request has clean context
      } catch (err) {
        removeTyping();
        const bubble = addMessage('assistant', `Connection error: ${err.message}`);
        bubble.style.color = 'var(--cds-support-error)';
      }
      streaming = false;
      $sendBtn.disabled = !$input.value.trim();
      clearInterval(rateWatchdog);
      streaming = false;
      $sendBtn.disabled = !$input.value.trim();
      hideRate();
    }
  
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    print(f"   Blue Bank AI Assistant")
    print(f"   Provider: {LLM_PROVIDER}")
    print(f"   Model:    {MODEL_NAME}")
    if LLM_PROVIDER == "watsonx":
        print(f"   URL:      {WATSONX_URL}")
    else:
        print(f"   API Base: {VLLM_API_BASE}")
    print(f"   Port:     {PORT}")
    print(f"   http://localhost:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)

# Made with Bob