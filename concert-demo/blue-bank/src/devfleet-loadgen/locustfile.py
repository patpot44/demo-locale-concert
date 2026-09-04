"""
Blue Bank - DevFleet GPU Load Testing Service
Locust-based load generator for the coding assistant endpoint
Sends pre-captured coding requests from corpus.json
"""

import os
import json
import time
from locust import HttpUser, task, between, events

# Configuration
VLLM_CODING_URL = os.getenv("VLLM_CODING_URL", "https://vllm-coding-route-bluebank.apps.bluebank-demo-2.cp.fyre.ibm.com")

class CodingAgentTasks:
    def __init__(self, user):
        self.user = user
        with open('corpus.json', 'r') as f:
            self.requests = json.load(f)
        self.current_index = 0  # Each user starts at beginning
        print(f"Loaded {len(self.requests)} coding requests from corpus")
    
    def stream_code_response(self, request_payload):
        """Stream SSE response from vLLM coding service"""
        start_time = time.time()
        first_token_time = None
        token_count = 0
        
        # Use the request payload directly from corpus
        # It already has model, messages, max_tokens, temperature, stream
        
        with self.user.client.post(
            "/v1/chat/completions",
            json=request_payload,
            stream=True,
            catch_response=True,
            name="code_generation"
        ) as response:
            try:
                for line in response.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode('utf-8').strip()
                    if decoded.startswith('data: '):
                        data = decoded[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get("choices", [])
                            content = choices[0].get("delta", {}).get("content", "") if choices else ""
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                token_count += 1
                        except json.JSONDecodeError:
                            continue
                
                total_time = time.time() - start_time
                ttft = (first_token_time - start_time) if first_token_time else total_time
                tokens_per_sec = token_count / total_time if total_time > 0 else 0
                
                if token_count == 0 or first_token_time is None:
                    if total_time < 5.0:  # If response came back quickly, it might be intentional
                        response.success()  # Mark as success
                        return {
                            'ttft': total_time,
                            'total_time': total_time,
                            'token_count': 0,
                            'tokens_per_sec': 0
                        }
                    else:
                        response.failure(f"No tokens received (duration: {total_time:.1f}s)")
                        return None
                
                # Log TTFT metric
                if hasattr(self.user.environment, 'runner') and self.user.environment.runner:
                    self.user.environment.runner.stats.log_request(
                        "TTFT",
                        "code_generation_ttft",
                        ttft * 1000,  # Convert to ms
                        0
                    )
                
                response.success()
                return {
                    'ttft': ttft,
                    'total_time': total_time,
                    'token_count': token_count,
                    'tokens_per_sec': tokens_per_sec
                }
            except Exception as e:
                response.failure(f"Stream error: {str(e)}")
                return None
    
    def generate_code(self):
        """Generate code from corpus requests sequentially"""
        # Get current request for this user
        request = self.requests[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.requests)
        self.stream_code_response(request)


class CodingAgentUser(HttpUser):
    """
    User that continuously sends coding requests to the AI assistant.
    Simulates realistic developer interactions using captured requests.
    """
    host = VLLM_CODING_URL  # Set the base URL for all requests
    wait_time = between(1, 5)  # Developers think longer than chatbot users
    
    def on_start(self):
        """Initialize user session"""
        # Disable SSL verification for self-signed Fyre certs
        self.client.verify = False
        
        # Initialize task handler
        self.tasks_handler = CodingAgentTasks(self)
        
        print(f"DevFleet user starting - Target: {VLLM_CODING_URL}")
    
    @task
    def execute_tasks(self):
        """Execute weighted tasks through the task handler"""
        self.tasks_handler.generate_code()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test configuration at start"""
    print(f"\n{'='*70}")
    print(f"  DevFleet GPU Load Test Starting")
    print(f"  Target: {VLLM_CODING_URL}")
    print(f"{'='*70}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test summary at stop"""
    print(f"\n{'='*70}")
    print(f"  DevFleet GPU Load Test Stopped")
    print(f"{'='*70}\n")


# Custom Web UI with DevFleet branding
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Inject DevFleet branding into Locust web UI"""
    if environment.web_ui:
        @environment.web_ui.app.after_request
        def inject_branding(response):
            """Inject JS/CSS into every HTML response after React app loads"""
            if response.content_type and "text/html" in response.content_type:
                injection = b"""
                <script>
                // Change browser tab title
                document.title = 'DevFleet GPU Load - Locust';
                
                // Function to replace Locust logo with DevFleet text
                function replaceLogo() {
                    var logoLink = document.querySelector('a[href="/"]');
                    if (logoLink && logoLink.querySelector('svg')) {
                        logoLink.innerHTML = '<span style="font-size: 24px; font-weight: 700; color: #ffffff;">DevFleet</span>';
                        return true;
                    }
                    return false;
                }
                
                // Try immediately
                if (!replaceLogo()) {
                    // If not found, use MutationObserver to watch for React render
                    var observer = new MutationObserver(function(mutations) {
                        if (replaceLogo()) {
                            observer.disconnect();
                        }
                    });
                    observer.observe(document.body, { childList: true, subtree: true });
                    
                    // Also try with timeouts as fallback
                    setTimeout(replaceLogo, 500);
                    setTimeout(replaceLogo, 1000);
                    setTimeout(replaceLogo, 2000);
                }
                
                // Inject DevFleet custom styles
                var style = document.createElement('style');
                style.textContent = `
                    /* DevFleet color scheme for header */
                    .MuiAppBar-root, header {
                        background: #8a3ffc !important;
                    }
                `;
                document.head.appendChild(style);
                </script>
                """
                response.data = response.data.replace(b"</body>", injection + b"</body>")
            return response

# Made with Bob

