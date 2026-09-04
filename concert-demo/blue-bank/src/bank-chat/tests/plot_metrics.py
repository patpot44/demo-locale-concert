"""
Generate demo metric graphs from vllm_metrics.csv
Usage: python3 plot_metrics.py [csv_file] [--scale-events 70,190,310]
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

CSV_FILE = sys.argv[1] if len(sys.argv) > 1 else "vllm_metrics.csv"

SCALE_EVENTS = []
scale_events_set = False
for arg in sys.argv:
    if arg.startswith("--scale-events="):
        scale_events_set = True
        val = arg.split("=")[1].strip()
        if val:
            SCALE_EVENTS = [(int(t.strip()), f"Scale to {i+2}")
                            for i, t in enumerate(val.split(",")) if t.strip()]
        else:
            SCALE_EVENTS = []
if not scale_events_set:
    SCALE_EVENTS = [(70, "Scale to 2"), (190, "Scale to 3"), (310, "Scale to 4")]

df = pd.read_csv(CSV_FILE)

fig, axes = plt.subplots(4, 1, figsize=(14, 18), sharex=True)
fig.suptitle("Blue Bank GPU Autoscaling Demo — Metrics", fontsize=16, fontweight="bold", y=0.98)

colors = {
    "red": "#da1e28",
    "blue": "#0f62fe",
    "green": "#198038",
    "purple": "#8a3ffc",
    "orange": "#ff832b",
    "teal": "#009d9a",
    "cyan": "#1192e8",
    "magenta": "#ee5396",
}

def add_scale_lines(ax):
    for t, label in SCALE_EVENTS:
        if t <= df["t"].max():
            ax.axvline(x=t, color="#6f6f6f", linestyle="--", linewidth=0.8, alpha=0.7)
            ax.text(t + 2, ax.get_ylim()[1] * 0.92, label, fontsize=8,
                    color="#6f6f6f", rotation=0, va="top")

ax1 = axes[0]
ax1.plot(df["t"], df["avg_ttft_s"], color=colors["red"], linewidth=1.5, label="Avg TTFT (s)")
ax1.plot(df["t"], df["avg_queue_time_s"], color=colors["orange"], linewidth=1.5, label="Avg Queue Time (s)", linestyle="--")
ax1.set_ylabel("Seconds")
ax1.set_title("User Experience — Time to First Token & Queue Wait", fontsize=12, fontweight="bold")
ax1.legend(loc="upper right", fontsize=9)
ax1.grid(True, alpha=0.2)
ax1.set_ylim(bottom=0)
add_scale_lines(ax1)

ax2 = axes[1]
ax2.plot(df["t"], df["queue_depth"], color=colors["red"], linewidth=1.5, label="Queue Depth")
ax2.plot(df["t"], df["concurrent_queries"], color=colors["blue"], linewidth=1.5, label="Concurrent Queries")
ax2.fill_between(df["t"], df["queue_depth"], alpha=0.15, color=colors["red"])
ax2.set_ylabel("Requests")
ax2.set_title("GPU Contention — Queue Depth vs Concurrent Queries", fontsize=12, fontweight="bold")
ax2.legend(loc="upper right", fontsize=9)
ax2.grid(True, alpha=0.2)
ax2.set_ylim(bottom=0)
add_scale_lines(ax2)

ax3 = axes[2]
ax3.plot(df["t"], df["agg_tokens_per_sec"], color=colors["green"], linewidth=1.5, label="Aggregate Tokens/sec")
ax3_right = ax3.twinx()
ax3_right.plot(df["t"], df["transactions_per_sec"], color=colors["purple"], linewidth=1.2, label="Transactions/sec", linestyle="--")
ax3.set_ylabel("Tokens/sec", color=colors["green"])
ax3_right.set_ylabel("Transactions/sec", color=colors["purple"])
ax3.set_title("Throughput & Recovery", fontsize=12, fontweight="bold")
lines1, labels1 = ax3.get_legend_handles_labels()
lines2, labels2 = ax3_right.get_legend_handles_labels()
ax3.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
ax3.grid(True, alpha=0.2)
ax3.set_ylim(bottom=0)
ax3_right.set_ylim(bottom=0)
add_scale_lines(ax3)

ax4 = axes[3]
gpu_colors = [colors["blue"], colors["teal"], colors["magenta"], colors["orange"]]
for i in range(4):
    col = f"gpu{i}_fb_used_mib"
    if col in df.columns:
        ax4.plot(df["t"], df[col] / 1024, color=gpu_colors[i], linewidth=1.5, label=f"GPU {i}")
ax4.set_ylabel("VRAM Used (GiB)")
ax4.set_xlabel("Time (seconds)")
ax4.set_title("GPU Memory — Scaling Across 4 H100s", fontsize=12, fontweight="bold")
ax4.legend(loc="center right", fontsize=9)
ax4.grid(True, alpha=0.2)
ax4.set_ylim(bottom=0)
add_scale_lines(ax4)

plt.tight_layout(rect=[0, 0, 1, 0.96])

output = CSV_FILE.replace(".csv", "_graphs.png")
plt.savefig(output, dpi=150, bbox_inches="tight")
print(f"Saved: {output}")
plt.show()