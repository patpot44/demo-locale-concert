"""
Blue Bank - GPU Load Testing Service
Locust-based load generator for the AI chatbot endpoint
Supports dual-mode operation: through bank-chat or direct to vLLM
"""

import os
import json
import time
from locust import HttpUser, task, between, events

# Configuration from environment
TARGET_MODE = os.getenv("TARGET_MODE", "chatbot")  # "chatbot" or "vllm-direct"
CHATBOT_URL = os.getenv("CHATBOT_URL", "https://bank-chat-demoapps-bank-anthos.apps.o1-968455.cp.fyre.ibm.com")
VLLM_URL = os.getenv("VLLM_URL", "https://vllm-route-bluebank.apps.bluebank-demo-2.cp.fyre.ibm.com")

# Banking conversation templates
CONVERSATIONS = [
    [
        "What is my checking account balance?",
        "Can you show me the last 5 transactions on that account?",
        "I see a charge from Amazon for $47.99 that I don't recognize. Can you help me dispute it?",
        "What happens after I file the dispute?",
    ],
    [
        "How do I set up direct deposit?",
        "What is the routing number I need to give my employer?",
        "How long does it take for the first deposit to arrive?",
        "Can I split the deposit between checking and savings?",
    ],
    [
        "What are your current mortgage rates?",
        "What would the monthly payment be on a $350,000 30-year fixed?",
        "What about a 15-year fixed?",
        "What documents do I need to start the application?",
    ],
    [
        "I lost my debit card, what do I do?",
        "Can you freeze my card right now?",
        "Were there any charges after 3pm today?",
        "How long until I get the replacement card?",
    ],
    [
        "How do I transfer money to another bank?",
        "What is the fee for a wire transfer?",
        "How long does an ACH transfer take?",
        "Is there a daily limit on transfers?",
    ],
    [
        "Help me reset my online banking password",
        "I'm not receiving the verification code on my phone",
        "Can you send it to my email instead?",
        "While I'm here, can you also enable two-factor authentication?",
    ],
    [
        "What are your business checking options?",
        "What is the monthly fee for the premium business account?",
        "Is there a minimum balance to waive the fee?",
        "Can I add authorized signers to the account?",
    ],
    [
        "Can I increase my credit card limit?",
        "What is my current limit and utilization?",
        "What factors determine whether I get approved?",
        "How long does the review process take?",
    ],
    [
        "What are the requirements to open a CD?",
        "What is the penalty for early withdrawal?",
        "Can I set it up to auto-renew?",
        "What rate would I get on a 12-month CD for $10,000?",
    ],
    [
        "How do I set up automatic bill pay?",
        "Can I schedule payments for different amounts each month?",
        "What happens if there are insufficient funds on the payment date?",
        "Can I cancel a scheduled payment?",
    ],
]


def parse_sse_chunk(data, mode):
    """Parse SSE chunk based on target mode"""
    try:
        chunk = json.loads(data)
        if mode == "chatbot":
            # bank-chat format: {"content": "token"}
            return chunk.get('content', '')
        else:
            # vLLM OpenAI format: {"choices": [{"delta": {"content": "token"}}]}
            return chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
    except json.JSONDecodeError:
        return ''


class ChatbotTasks:
    """Task set for chatbot load testing"""
    
    def __init__(self, user):
        self.user = user
        self.conversation_index = 0
        self.current_conversation = CONVERSATIONS[0]
    
    def stream_chat_response(self, question):
        """Stream SSE response and collect metrics"""
        start_time = time.time()
        first_token_time = None
        token_count = 0
        
        if TARGET_MODE == "chatbot":
            endpoint = "/api/chat"
            payload = {"message": question, "stream": True}
            url = CHATBOT_URL + endpoint
        else:
            endpoint = "/v1/chat/completions"
            payload = {
                "model": "granite-chatbot",
                "messages": [
                    {"role": "system", "content": "You are Blue Bank's helpful retail banking assistant. Provide detailed answers."},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 150,
                "stream": True
            }
            url = VLLM_URL + endpoint
        
        with self.user.client.post(
            url,
            json=payload,
            stream=True,
            catch_response=True,
            name=f"chat_stream_{TARGET_MODE}"
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
                        
                        content = parse_sse_chunk(data, TARGET_MODE)
                        if content:
                            if first_token_time is None:
                                first_token_time = time.time()
                            token_count += 1
                
                total_time = time.time() - start_time
                ttft = (first_token_time - start_time) if first_token_time else total_time
                tokens_per_sec = token_count / total_time if total_time > 0 else 0
                
                # Validate that we actually received tokens
                if token_count == 0 or first_token_time is None:
                    response.failure(f"No tokens received - possible timeout or connection closed (duration: {total_time:.1f}s)")
                    return None
                
                # Log custom TTFT metric using stats API (non-recursive)
                if hasattr(self.user.environment, 'runner') and self.user.environment.runner:
                    self.user.environment.runner.stats.log_request(
                        "TTFT",
                        f"{endpoint}_ttft",
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
    
    @task(10)
    def ask_banking_question(self):
        """Ask a random banking question"""
        import random
        conversation = random.choice(CONVERSATIONS)
        question = random.choice(conversation)
        self.stream_chat_response(question)
    
    @task(5)
    def ask_followup(self):
        """Ask a follow-up question from the same conversation"""
        import random
        if not hasattr(self, 'current_conversation'):
            self.current_conversation = random.choice(CONVERSATIONS)
        
        question = random.choice(self.current_conversation)
        self.stream_chat_response(question)
    
    @task(3)
    def long_form_request(self):
        """Request a detailed explanation (heavier GPU load)"""
        questions = [
            "Write a detailed explanation of your mortgage options",
            "Explain all the different types of savings accounts you offer",
            "Describe the complete process for opening a business account",
            "What are all the benefits of your premium checking account?",
        ]
        import random
        question = random.choice(questions)
        
        # Override max_tokens for longer response
        if TARGET_MODE == "chatbot":
            # bank-chat doesn't expose max_tokens, so just send the question
            self.stream_chat_response(question)
        else:
            # For vLLM direct, we can control max_tokens
            start_time = time.time()
            first_token_time = None
            token_count = 0
            
            payload = {
                "model": "granite-chatbot",
                "messages": [
                    {"role": "system", "content": "You are Blue Bank's helpful retail banking assistant. Provide detailed answers."},
                    {"role": "user", "content": question}
                ],
                "max_tokens": 200,
                "stream": True
            }
            
            with self.user.client.post(
                VLLM_URL + "/v1/chat/completions",
                json=payload,
                stream=True,
                catch_response=True,
                name="chat_stream_long_form"
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
                            content = parse_sse_chunk(data, "vllm-direct")
                            if content:
                                if first_token_time is None:
                                    first_token_time = time.time()
                                token_count += 1
                    
                    total_time = time.time() - start_time
                    ttft = (first_token_time - start_time) if first_token_time else total_time
                    
                    # Validate that we actually received tokens
                    if token_count == 0 or first_token_time is None:
                        response.failure(f"No tokens received - possible timeout or connection closed (duration: {total_time:.1f}s)")
                        return
                    
                    if hasattr(self.user.environment, 'runner') and self.user.environment.runner:
                        self.user.environment.runner.stats.log_request(
                            "TTFT",
                            "long_form_ttft",
                            ttft * 1000,
                            0
                        )
                    
                    response.success()
                except Exception as e:
                    response.failure(f"Stream error: {str(e)}")
    
    @task(1)
    def health_check(self):
        """Check service health"""
        if TARGET_MODE == "chatbot":
            self.user.client.get(CHATBOT_URL + "/api/health", name="health_check")
        else:
            self.user.client.get(VLLM_URL + "/health", name="health_check")


class ChatbotUser(HttpUser):
    """
    User that continuously sends chat requests to the AI assistant.
    Simulates realistic banking customer interactions.
    """
    wait_time = between(2, 8)  # Baseline: 2-8 seconds between requests
    # For stress testing, change to: wait_time = between(0.3, 1.0)
    
    def on_start(self):
        """Initialize user session"""
        # Disable SSL verification for self-signed Fyre certs
        self.client.verify = False
        
        # Initialize task handler
        self.tasks_handler = ChatbotTasks(self)
        
        # Send greeting to establish session
        print(f"User starting - Mode: {TARGET_MODE}")
        self.tasks_handler.stream_chat_response("Hello, I'm a new customer")
    
    @task
    def execute_tasks(self):
        """Execute weighted tasks through the task handler"""
        import random
        
        # Weighted task selection
        rand = random.random()
        if rand < 0.5:  # 50% - ask_banking_question (task weight 10)
            self.tasks_handler.ask_banking_question()
        elif rand < 0.75:  # 25% - ask_followup (task weight 5)
            self.tasks_handler.ask_followup()
        elif rand < 0.90:  # 15% - long_form_request (task weight 3)
            self.tasks_handler.long_form_request()
        else:  # 10% - health_check (task weight 1)
            self.tasks_handler.health_check()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Log test configuration at start"""
    print(f"\n{'='*70}")
    print(f"  GPU Load Test Starting")
    print(f"  Mode: {TARGET_MODE}")
    print(f"  Target: {CHATBOT_URL if TARGET_MODE == 'chatbot' else VLLM_URL}")
    print(f"{'='*70}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Log test summary at stop"""
    print(f"\n{'='*70}")
    print(f"  GPU Load Test Stopped")
    print(f"{'='*70}\n")


# Custom Web UI with Blue Bank branding
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Inject Blue Bank branding into Locust web UI"""
    if environment.web_ui:
        @environment.web_ui.app.after_request
        def inject_branding(response):
            """Inject JS/CSS into every HTML response after React app loads"""
            if response.content_type and "text/html" in response.content_type:
                injection = b"""
                <script>
                // Change browser tab title
                document.title = 'Blue Bank GPU Load - Locust';
                
                // Function to replace Locust logo with Blue Bank text
                function replaceLogo() {
                    var logoLink = document.querySelector('a[href="/"]');
                    if (logoLink && logoLink.querySelector('svg')) {
                        logoLink.innerHTML = '<span style="font-size: 24px; font-weight: 700; color: #ffffff;">Blue Bank</span>';
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
                
                // Inject Blue Bank custom styles
                var style = document.createElement('style');
                style.textContent = `
                    /* Blue Bank color scheme for header */
                    .MuiAppBar-root, header {
                        background: #0f62fe !important;
                    }
                `;
                document.head.appendChild(style);
                </script>
                """
                response.data = response.data.replace(b"</body>", injection + b"</body>")
            return response

# Made with Bob
# Build timestamp: Wed May  6 15:57:26 EDT 2026
