import subprocess
import time
import csv
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

DCGM_POD_LABEL = "app=nvidia-dcgm-exporter"
DCGM_NS = "nvidia-gpu-operator"
CSV_FILE = "vllm_metrics.csv"
INTERVAL = 1
NUM_GPUS = 4

COLUMNS = [
    "t",
    "concurrent_queries",
    "queue_depth",
    "kv_cache_usage_pct",
    "pods_ready",
    "avg_ttft_s",
    "avg_e2e_latency_s",
    "avg_queue_time_s",
    "avg_inference_time_s",
    "avg_inter_token_ms",
    "agg_tokens_per_sec",
    "transactions_per_sec",
    "total_transactions",
    "total_gen_tokens",
    "total_prompt_tokens",
]

for i in range(NUM_GPUS):
    COLUMNS.extend([
        f"gpu{i}_util_pct",
        f"gpu{i}_mem_util_pct",
        f"gpu{i}_fb_used_mib",
        f"gpu{i}_fb_free_mib",
    ])


def fetch_pod_metrics(pod_name):
    try:
        result = subprocess.run(
            ["oc", "exec", "-n", "bluebank", pod_name, "--",
             "curl", "-s", "localhost:8000/metrics"],
            capture_output=True, text=True, timeout=8
        )
        return pod_name, result.stdout
    except:
        return pod_name, ""


def fetch_dcgm(dcgm_pod):
    try:
        result = subprocess.run(
            ["oc", "exec", "-n", DCGM_NS, dcgm_pod,
             "--", "curl", "-s", "localhost:9400/metrics"],
            capture_output=True, text=True, timeout=8
        )
        return result.stdout
    except:
        return ""


def get_vllm_pod_names():
    try:
        result = subprocess.run(
            ["oc", "get", "pods", "-n", "bluebank", "-l", "app=vllm-granite",
             "--field-selector=status.phase=Running",
             "-o", "jsonpath={.items[*].metadata.name}"],
            capture_output=True, text=True, timeout=5
        )
        names = result.stdout.strip().split()
        return [n for n in names if n]
    except:
        return []


def get_pods_ready():
    try:
        result = subprocess.run(
            ["oc", "get", "deployment", "vllm-granite", "-n", "bluebank",
             "-o", "jsonpath={.status.readyReplicas}"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() or "0"
    except:
        return "0"


def extract_gauge(raw, metric_name):
    for line in raw.split("\n"):
        if line.startswith(f"{metric_name}{{") or line.startswith(f"{metric_name} "):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return float(parts[-1])
                except:
                    pass
    return 0.0


def extract_counter(raw, metric_name):
    for line in raw.split("\n"):
        if line.startswith(f"{metric_name}{{"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    return float(parts[-1])
                except:
                    pass
    return 0.0


def extract_dcgm_per_gpu(raw, metric_name, num_gpus):
    values = [0.0] * num_gpus
    for line in raw.split("\n"):
        if line.startswith(f"{metric_name}{{"):
            for i in range(num_gpus):
                if f'gpu="{i}"' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            values[i] = float(parts[-1])
                        except:
                            pass
    return values


def main():
    start_time = time.time()
    prev = {}
    prev_time = None

    try:
        result = subprocess.run(
            ["oc", "get", "pods", "-n", DCGM_NS, "-l", DCGM_POD_LABEL,
             "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True, timeout=5
        )
        dcgm_pod = result.stdout.strip()
    except:
        dcgm_pod = None

    print(f"DCGM pod: {dcgm_pod}")
    print(f"Logging to {CSV_FILE}")
    print(f"Columns: {len(COLUMNS)}")
    print(f"Fetches run in parallel for ~1s resolution")
    time.sleep(1)

    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()

        while True:
            loop_start = time.time()
            t = int(loop_start - start_time)

            pod_names = get_vllm_pod_names()
            pods = get_pods_ready()

            # Fetch ALL metrics in parallel
            vllm_results = {}
            dcgm_raw = ""

            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {}
                for name in pod_names:
                    futures[executor.submit(fetch_pod_metrics, name)] = "vllm"
                if dcgm_pod:
                    futures[executor.submit(fetch_dcgm, dcgm_pod)] = "dcgm"

                for future in as_completed(futures):
                    kind = futures[future]
                    if kind == "vllm":
                        pod_name, raw = future.result()
                        vllm_results[pod_name] = raw
                    elif kind == "dcgm":
                        dcgm_raw = future.result()

            # Aggregate vLLM metrics
            total_running = 0.0
            total_waiting = 0.0
            total_cache = 0.0
            cache_count = 0
            total_ttft_sum = 0.0
            total_ttft_count = 0.0
            total_e2e_sum = 0.0
            total_e2e_count = 0.0
            total_queue_sum = 0.0
            total_queue_count = 0.0
            total_infer_sum = 0.0
            total_infer_count = 0.0
            total_itl_sum = 0.0
            total_itl_count = 0.0
            total_gen_tokens = 0.0
            total_prompt_tokens = 0.0
            total_req_success = 0.0

            for name, raw in vllm_results.items():
                if not raw:
                    continue
                total_running += extract_gauge(raw, "vllm:num_requests_running")
                total_waiting += extract_gauge(raw, "vllm:num_requests_waiting")
                c = extract_gauge(raw, "vllm:gpu_cache_usage_perc")
                if c > 0 or total_running > 0 or cache_count == 0:
                    total_cache += c
                    cache_count += 1
                total_ttft_sum += extract_counter(raw, "vllm:time_to_first_token_seconds_sum")
                total_ttft_count += extract_counter(raw, "vllm:time_to_first_token_seconds_count")
                total_e2e_sum += extract_counter(raw, "vllm:e2e_request_latency_seconds_sum")
                total_e2e_count += extract_counter(raw, "vllm:e2e_request_latency_seconds_count")
                total_queue_sum += extract_counter(raw, "vllm:request_queue_time_seconds_sum")
                total_queue_count += extract_counter(raw, "vllm:request_queue_time_seconds_count")
                total_infer_sum += extract_counter(raw, "vllm:request_inference_time_seconds_sum")
                total_infer_count += extract_counter(raw, "vllm:request_inference_time_seconds_count")
                total_itl_sum += extract_counter(raw, "vllm:time_per_output_token_seconds_sum")
                total_itl_count += extract_counter(raw, "vllm:time_per_output_token_seconds_count")
                total_gen_tokens += extract_counter(raw, "vllm:generation_tokens_total")
                total_prompt_tokens += extract_counter(raw, "vllm:prompt_tokens_total")
                total_req_success += extract_counter(raw, "vllm:request_success_total")

            avg_cache = (total_cache / cache_count) if cache_count > 0 else 0.0

            gpu_util = extract_dcgm_per_gpu(dcgm_raw, "DCGM_FI_DEV_GPU_UTIL", NUM_GPUS)
            mem_util = extract_dcgm_per_gpu(dcgm_raw, "DCGM_FI_DEV_MEM_COPY_UTIL", NUM_GPUS)
            fb_used = extract_dcgm_per_gpu(dcgm_raw, "DCGM_FI_DEV_FB_USED", NUM_GPUS)
            fb_free = extract_dcgm_per_gpu(dcgm_raw, "DCGM_FI_DEV_FB_FREE", NUM_GPUS)

            # Windowed rates
            now = time.time()
            avg_ttft = avg_e2e = avg_queue = avg_infer = avg_itl_ms = 0
            tok_per_sec = txn_per_sec = 0

            if prev and prev_time:
                dt = now - prev_time
                if dt > 0:
                    def delta(key, current):
                        p = prev.get(key, current)
                        d = current - p
                        return max(d, 0)

                    dc = delta("ttft_count", total_ttft_count)
                    avg_ttft = (delta("ttft_sum", total_ttft_sum) / dc) if dc > 0 else 0

                    dc = delta("e2e_count", total_e2e_count)
                    avg_e2e = (delta("e2e_sum", total_e2e_sum) / dc) if dc > 0 else 0

                    dc = delta("queue_count", total_queue_count)
                    avg_queue = (delta("queue_sum", total_queue_sum) / dc) if dc > 0 else 0

                    dc = delta("infer_count", total_infer_count)
                    avg_infer = (delta("infer_sum", total_infer_sum) / dc) if dc > 0 else 0

                    dc = delta("itl_count", total_itl_count)
                    avg_itl_ms = (delta("itl_sum", total_itl_sum) / dc * 1000) if dc > 0 else 0

                    tok_per_sec = delta("gen_tokens", total_gen_tokens) / dt
                    txn_per_sec = delta("req_success", total_req_success) / dt

            prev = {
                "ttft_sum": total_ttft_sum, "ttft_count": total_ttft_count,
                "e2e_sum": total_e2e_sum, "e2e_count": total_e2e_count,
                "queue_sum": total_queue_sum, "queue_count": total_queue_count,
                "infer_sum": total_infer_sum, "infer_count": total_infer_count,
                "itl_sum": total_itl_sum, "itl_count": total_itl_count,
                "gen_tokens": total_gen_tokens, "req_success": total_req_success,
            }
            prev_time = now

            row = {
                "t": t,
                "concurrent_queries": total_running,
                "queue_depth": total_waiting,
                "kv_cache_usage_pct": round(avg_cache * 100, 1),
                "pods_ready": pods,
                "avg_ttft_s": round(avg_ttft, 3),
                "avg_e2e_latency_s": round(avg_e2e, 3),
                "avg_queue_time_s": round(avg_queue, 3),
                "avg_inference_time_s": round(avg_infer, 3),
                "avg_inter_token_ms": round(avg_itl_ms, 1),
                "agg_tokens_per_sec": round(tok_per_sec, 1),
                "transactions_per_sec": round(txn_per_sec, 1),
                "total_transactions": int(total_req_success),
                "total_gen_tokens": int(total_gen_tokens),
                "total_prompt_tokens": int(total_prompt_tokens),
            }
            for i in range(NUM_GPUS):
                row[f"gpu{i}_util_pct"] = gpu_util[i]
                row[f"gpu{i}_mem_util_pct"] = mem_util[i]
                row[f"gpu{i}_fb_used_mib"] = fb_used[i]
                row[f"gpu{i}_fb_free_mib"] = fb_free[i]

            writer.writerow(row)
            f.flush()

            # Display
            elapsed = time.time() - loop_start
            print(f"\033[2J\033[H", end="")
            print(f"=== vLLM + GPU Metrics (t={t}s) | loop: {elapsed:.1f}s | Pods: {len(pod_names)} scraped, {pods} ready ===")
            print(f"  Concurrent:     {total_running:.0f}")
            print(f"  Queue depth:    {total_waiting:.0f}")
            print(f"  KV Cache:       {avg_cache*100:.1f}%")
            print(f"  Pods Ready:     {pods}")
            print(f"  Pods:           {', '.join(pod_names) if pod_names else 'none'}")
            print(f"  ---")
            print(f"  Avg TTFT:       {avg_ttft:.3f}s")
            print(f"  Avg E2E:        {avg_e2e:.3f}s")
            print(f"  Avg Queue:      {avg_queue:.3f}s")
            print(f"  Avg Inference:  {avg_infer:.3f}s")
            print(f"  Avg ITL:        {avg_itl_ms:.1f}ms")
            print(f"  ---")
            print(f"  Tok/s:          {tok_per_sec:.1f}")
            print(f"  Txn/s:          {txn_per_sec:.1f}")
            print(f"  Total Txns:     {int(total_req_success)}")
            print(f"  Total Tokens:   {int(total_gen_tokens)}")
            print(f"  --- GPUs ---")
            for i in range(NUM_GPUS):
                status = "vLLM" if fb_used[i] > 1000 else "idle"
                print(f"  GPU{i}: {gpu_util[i]:3.0f}% util | {mem_util[i]:3.0f}% mem | {fb_used[i]:.0f}/{fb_used[i]+fb_free[i]:.0f} MiB [{status}]")
            print(f"\n  Logging to {CSV_FILE}")

            # Sleep remaining time to hit ~INTERVAL
            sleep_time = max(0, INTERVAL - (time.time() - loop_start))
            time.sleep(sleep_time)


if __name__ == "__main__":
    main()
