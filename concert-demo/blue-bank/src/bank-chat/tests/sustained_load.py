import asyncio
import aiohttp
import time
import sys
import random
import json

VLLM_URL = sys.argv[1] if len(sys.argv) > 1 else "https://vllm-route-bluebank.apps.bluebank-demo-2.cp.fyre.ibm.com"
NUM_USERS = int(sys.argv[2]) if len(sys.argv) > 2 else 120
DURATION = int(sys.argv[3]) if len(sys.argv) > 3 else 300
RAMP_SECONDS = int(sys.argv[4]) if len(sys.argv) > 4 else 45
MIN_DELAY = float(sys.argv[5]) if len(sys.argv) > 5 else 0.5
MAX_DELAY = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5

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

stats = {
    "requests": 0, "tokens": 0, "errors": 0,
    "total_latency": 0, "total_ttft": 0, "ttft_count": 0
}


async def stream_response(resp):
    tokens = 0
    first_token_time = None
    start = time.time()
    async for line in resp.content:
        decoded = line.decode("utf-8").strip()
        if not decoded or not decoded.startswith("data: "):
            continue
        payload = decoded[6:]
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
            delta = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
            if delta:
                if first_token_time is None:
                    first_token_time = time.time()
                tokens += 1
        except:
            pass
    elapsed = time.time() - start
    ttft = (first_token_time - start) if first_token_time else elapsed
    return tokens, elapsed, ttft


async def simulate_user(session, user_id, stop_event, test_start):
    conversation = CONVERSATIONS[user_id % len(CONVERSATIONS)]
    turn = 0

    while not stop_event.is_set():
        question = conversation[turn % len(conversation)]
        typing_time = random.uniform(MIN_DELAY, MAX_DELAY)
        await asyncio.sleep(typing_time)
        if stop_event.is_set():
            break

        # Send ONLY system + current question (no history):
        # This keeps input short (~50 tokens) and output long (200 tokens)
        # Each request takes 20+ seconds of GPU time instead of 5
        payload = {
            "model": "granite-chatbot",
            "messages": [
                {"role": "system", "content": "You are Blue Bank's helpful retail banking assistant. Provide detailed answers."},
                {"role": "user", "content": question}
            ],
            "max_tokens": 200,
            "stream": True
        }

        start = time.time()
        elapsed_since_start = start - test_start
        try:
            async with session.post(
                f"{VLLM_URL}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                ssl=False,
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                tokens, elapsed, ttft = await stream_response(resp)
                tps = tokens / elapsed if elapsed > 0 else 0
                stats["requests"] += 1
                stats["tokens"] += tokens
                stats["total_latency"] += elapsed
                stats["total_ttft"] += ttft
                stats["ttft_count"] += 1
                print(f"  t={elapsed_since_start:5.0f}s | User {user_id:2d} t{turn:1d} | ttft {ttft:5.2f}s | {elapsed:5.1f}s | {tokens:3d} tok | {tps:5.1f} tok/s")
        except Exception as e:
            elapsed = time.time() - start
            stats["errors"] += 1
            print(f"  t={elapsed_since_start:5.0f}s | User {user_id:2d} t{turn:1d} | ERROR: {str(e)[:60]}")
        turn += 1


async def main():
    print(f"\n{'='*70}")
    print(f"  Sustained Load: {NUM_USERS} users, {DURATION}s")
    print(f"  Ramp: {RAMP_SECONDS}s to reach full load")
    print(f"  Delay between turns: {MIN_DELAY}-{MAX_DELAY}s")
    print(f"  Target: {VLLM_URL}")
    print(f"{'='*70}\n")

    stop_event = asyncio.Event()
    connector = aiohttp.TCPConnector(limit=NUM_USERS + 10, ssl=False)
    test_start = time.time()

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        delay_per_user = RAMP_SECONDS / NUM_USERS

        for uid in range(NUM_USERS):
            await asyncio.sleep(delay_per_user)
            active = len(tasks) + 1
            if active % 20 == 0 or active == NUM_USERS:
                print(f"  >> {active}/{NUM_USERS} users active (t={time.time()-test_start:.0f}s)")
            tasks.append(asyncio.create_task(
                simulate_user(session, uid, stop_event, test_start)
            ))

        remaining = DURATION - (time.time() - test_start)
        if remaining > 0:
            await asyncio.sleep(remaining)
        stop_event.set()
        await asyncio.gather(*tasks, return_exceptions=True)

    avg_lat = stats["total_latency"] / stats["requests"] if stats["requests"] else 0
    avg_ttft = stats["total_ttft"] / stats["ttft_count"] if stats["ttft_count"] else 0
    agg_tps = stats["tokens"] / DURATION if DURATION else 0

    print(f"\n{'='*70}")
    print(f"  Results ({DURATION}s sustained):")
    print(f"  Total requests:    {stats['requests']}")
    print(f"  Total tokens:      {stats['tokens']}")
    print(f"  Errors:            {stats['errors']}")
    print(f"  Avg latency:       {avg_lat:.1f}s")
    print(f"  Avg TTFT:          {avg_ttft:.2f}s")
    print(f"  Aggregate tok/s:   {agg_tps:.1f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
