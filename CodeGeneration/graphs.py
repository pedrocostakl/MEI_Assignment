"""
LeetCode SQL – ChatGPT vs Gemini Runtime Analysis
Generates 5 publication-ready charts saved as PNG files.
Requirements: pip install matplotlib numpy
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

OUTPUT_DIR = "charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Data ────────────────────────────────────────────────────────────────────

chatgpt = {
    "hard": [
        (185,102,True),(262,126,True),(601,68,True),(3451,82,False),
        (3374,88,True),(3482,76,True),(3617,None,False),(3764,70,True),
        (3832,69,True),(3673,84,True),(1581,136,True),(2356,83,True),
        (1978,73,True),(1965,113,True),(1890,229,True),(1873,66,True),
        (1789,164,True),(1757,73,True),(1741,81,True),
    ],
    "medium": [
        (176,82,True),(177,86,True),(178,79,True),(180,75,True),
        (184,116,True),(550,69,True),(570,67,True),(585,82,True),
        (602,70,True),(608,102,True),(626,77,True),(1045,93,True),
        (1070,102,True),(1158,764,True),(1164,85,True),(1174,82,True),
        (1193,70,True),(1204,213,True),(1321,78,True),(1341,159,True),
        (1393,72,True),
    ],
    "easy": [
        (175,100,True),(181,67,True),(182,67,True),(183,103,True),
        (196,71,True),(197,79,True),(511,79,True),(577,118,True),
        (584,88,True),(586,88,True),(595,91,True),(596,70,True),
        (607,151,True),(610,96,True),(619,105,True),(620,79,True),
        (627,92,True),(1050,68,True),(1068,98,True),(1075,135,True),
        (1084,84,True),
    ],
}

gemini = {
    "hard": [
        (185,128,True),(262,94,True),(601,82,True),(3451,84,True),
        (3374,84,False),(3482,94,True),(3673,88,True),(3617,120,True),
        (3832,None,False),(3764,106,True),(1581,80,True),(2356,78,True),
        (1978,68,True),(1965,71,True),(1890,88,True),(1873,82,True),
        (1789,102,True),(1757,81,True),(1741,96,True),
    ],
    "medium": [
        (176,90,True),(177,103,True),(178,None,False),(180,74,True),
        (184,130,True),(550,80,True),(570,102,True),(585,71,True),
        (602,75,True),(608,83,True),(626,79,True),(1045,118,True),
        (1070,83,True),(1158,147,True),(1164,62,True),(1174,73,True),
        (1193,222,True),(1204,65,True),(1321,70,True),(1341,147,True),
        (1393,76,True),
    ],
    "easy": [
        (175,114,True),(181,80,True),(182,70,True),(183,94,True),
        (196,70,True),(197,68,True),(511,74,True),(577,644,True),
        (584,79,True),(586,79,True),(595,78,True),(596,67,True),
        (607,121,True),(610,80,True),(619,118,True),(620,75,True),
        (627,90,True),(1050,93,True),(1068,112,True),(1075,136,True),
        (1084,445,True),
    ],
}

# ── Helpers ─────────────────────────────────────────────────────────────────

BLUE   = "#3266AD"
CORAL  = "#D85A30"
BLUE_L = "#B5D4F4"
CORAL_L= "#F5C4B3"
GRID_C = "#E8E8E8"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRID_C,
    "grid.linewidth": 0.8,
    "figure.dpi": 150,
})

def rts(model, diff):
    return [rt for _, rt, ok in model[diff] if ok and rt is not None]

def acc_rate(model, diff):
    data = model[diff]
    return sum(1 for _, _, ok in data if ok) / len(data) * 100

def five_num(data):
    a = np.array(sorted(data))
    return a.min(), np.percentile(a,25), np.median(a), np.percentile(a,75), a.max()

DIFFS  = ["Easy", "Medium", "Hard"]
DIFFS_ = ["easy", "medium", "hard"]

# ── 1. Summary bar: average runtime by difficulty ───────────────────────────

def chart_avg_runtime():
    gpt_means = [np.mean(rts(chatgpt, d)) for d in DIFFS_]
    gem_means = [np.mean(rts(gemini,  d)) for d in DIFFS_]

    x = np.arange(len(DIFFS))
    w = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    b1 = ax.bar(x - w/2, gpt_means, w, color=BLUE,  label="ChatGPT", zorder=3)
    b2 = ax.bar(x + w/2, gem_means, w, color=CORAL, label="Gemini",  zorder=3)

    ax.bar_label(b1, fmt="%.0f ms", padding=3, fontsize=9, color=BLUE)
    ax.bar_label(b2, fmt="%.0f ms", padding=3, fontsize=9, color=CORAL)

    ax.set_xticks(x); ax.set_xticklabels(DIFFS, fontsize=11)
    ax.set_ylabel("Average runtime (ms)", fontsize=10)
    ax.set_title("Average runtime by difficulty", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    ax.set_ylim(0, max(max(gpt_means), max(gem_means)) * 1.25)

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "1_avg_runtime_by_difficulty.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── 2. Box plot by difficulty ────────────────────────────────────────────────

def chart_boxplot():
    fig, axes = plt.subplots(1, 3, figsize=(12, 5), sharey=False)

    for ax, diff, label in zip(axes, DIFFS_, DIFFS):
        gpt = rts(chatgpt, diff)
        gem = rts(gemini,  diff)

        bp = ax.boxplot(
            [gpt, gem],
            patch_artist=True,
            widths=0.45,
            medianprops=dict(color="white", linewidth=2.5),
            whiskerprops=dict(linewidth=1.5),
            capprops=dict(linewidth=1.5),
            flierprops=dict(marker="o", markersize=5, linestyle="none"),
        )

        colors = [BLUE, CORAL]
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)
        for flier, color in zip(bp["fliers"], colors):
            flier.set(markerfacecolor=color, markeredgecolor=color, alpha=0.6)
        for whisker, cap in zip(
            zip(bp["whiskers"][::2], bp["whiskers"][1::2]),
            zip(bp["caps"][::2],    bp["caps"][1::2])
        ):
            pass  # colors inherited from default

        ax.set_xticks([1, 2])
        ax.set_xticklabels(["ChatGPT", "Gemini"], fontsize=10)
        ax.set_title(label, fontsize=12, fontweight="bold")
        ax.set_ylabel("Runtime (ms)" if diff == "easy" else "", fontsize=10)
        ax.grid(axis="y", color=GRID_C, linewidth=0.8)
        ax.set_axisbelow(True)

    fig.suptitle("Runtime distribution by difficulty (box plots)", fontsize=13, fontweight="bold", y=1.01)
    handles = [mpatches.Patch(color=BLUE, label="ChatGPT"),
               mpatches.Patch(color=CORAL, label="Gemini")]
    fig.legend(handles=handles, loc="upper right", fontsize=10)

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "2_boxplot_by_difficulty.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── 3. Acceptance rate by difficulty ────────────────────────────────────────

def chart_acceptance():
    gpt_acc = [acc_rate(chatgpt, d) for d in DIFFS_]
    gem_acc = [acc_rate(gemini,  d) for d in DIFFS_]

    x = np.arange(len(DIFFS))
    w = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.5))
    b1 = ax.bar(x - w/2, gpt_acc, w, color=BLUE,  label="ChatGPT", zorder=3)
    b2 = ax.bar(x + w/2, gem_acc, w, color=CORAL, label="Gemini",  zorder=3)

    ax.bar_label(b1, fmt="%.0f%%", padding=3, fontsize=9, color=BLUE)
    ax.bar_label(b2, fmt="%.0f%%", padding=3, fontsize=9, color=CORAL)

    ax.set_xticks(x); ax.set_xticklabels(DIFFS, fontsize=11)
    ax.set_ylabel("Acceptance rate (%)", fontsize=10)
    ax.set_ylim(0, 115)
    ax.set_title("Acceptance rate by difficulty", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=10)

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "3_acceptance_rate.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── 4. Histogram – full runtime distribution ─────────────────────────────────

def chart_histogram():
    all_gpt = rts(chatgpt,"easy") + rts(chatgpt,"medium") + rts(chatgpt,"hard")
    all_gem = rts(gemini, "easy") + rts(gemini, "medium") + rts(gemini, "hard")

    combined = all_gpt + all_gem
    bins = np.arange(min(combined), max(combined) + 30, 30)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(all_gpt, bins=bins, color=BLUE,  alpha=0.65, label="ChatGPT", edgecolor="white", linewidth=0.5, zorder=3)
    ax.hist(all_gem, bins=bins, color=CORAL, alpha=0.65, label="Gemini",  edgecolor="white", linewidth=0.5, zorder=3)

    for val, color, name in [(np.mean(all_gpt), BLUE, "ChatGPT mean"),
                              (np.mean(all_gem), CORAL, "Gemini mean")]:
        ax.axvline(val, color=color, linestyle="--", linewidth=1.8, label=f"{name}: {val:.0f} ms")

    ax.set_xlabel("Runtime (ms)", fontsize=10)
    ax.set_ylabel("Count", fontsize=10)
    ax.set_title("Runtime histogram – all accepted submissions (30 ms bins)", fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=9)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "4_runtime_histogram.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── 5. Head-to-head per problem (vertical bars, sample of 15) ───────────────

def chart_head_to_head():
    rows = []
    for diff in DIFFS_:
        gpt_map = {pid: rt for pid, rt, ok in chatgpt[diff] if ok and rt is not None}
        gem_map = {pid: rt for pid, rt, ok in gemini[diff]  if ok and rt is not None}
        for pid in sorted(set(gpt_map) & set(gem_map)):
            rows.append((pid, diff, diff[0].upper(), gpt_map[pid], gem_map[pid]))

    rows.sort(key=lambda r: r[0])

    # Pick 5 problems from each difficulty for a balanced, readable sample
    sample = []
    for d in DIFFS_:
        subset = [r for r in rows if r[1] == d]
        sample.extend(subset[:5])

    labels   = [f"#{r[0]}\n({r[2]})" for r in sample]
    gpt_vals = [r[3] for r in sample]
    gem_vals = [r[4] for r in sample]

    n = len(sample)
    x = np.arange(n)
    w = 0.38

    fig, ax = plt.subplots(figsize=(13, 5))

    b1 = ax.bar(x - w/2, gpt_vals, w, color=BLUE,  label="ChatGPT", zorder=3)
    b2 = ax.bar(x + w/2, gem_vals, w, color=CORAL, label="Gemini",  zorder=3)

    # Value labels on top of each bar
    ax.bar_label(b1, fmt="%d", padding=2, fontsize=7.5, color=BLUE)
    ax.bar_label(b2, fmt="%d", padding=2, fontsize=7.5, color=CORAL)

    # Set ylim before drawing difficulty band labels
    y_max = max(max(gpt_vals), max(gem_vals)) * 1.22
    ax.set_ylim(0, y_max)

    # Shaded difficulty bands
    band_edges = [0, 5, 10, 15]
    band_labels = ["Easy", "Medium", "Hard"]
    band_colors = ["#f0f4ff", "#fff7f0", "#f5f5f5"]
    for i, (start, end) in enumerate(zip(band_edges, band_edges[1:])):
        ax.axvspan(start - 0.5, end - 0.5, color=band_colors[i], alpha=0.45, zorder=0)
        ax.text((start + end - 1) / 2, y_max * 0.97,
                band_labels[i], ha="center", va="top", fontsize=9,
                color="#888888", fontstyle="italic")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Runtime (ms)", fontsize=10)
    ax.set_title("Per-problem runtime — head-to-head sample (5 problems per difficulty)",
                 fontsize=13, fontweight="bold", pad=12)
    ax.legend(fontsize=10)
    ax.grid(axis="y", color=GRID_C, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(-0.5, n - 0.5)

    fig.tight_layout()
    path = os.path.join(OUTPUT_DIR, "5_head_to_head.png")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ── Run all ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Generating charts into ./{OUTPUT_DIR}/\n")
    chart_avg_runtime()
    chart_boxplot()
    chart_acceptance()
    chart_histogram()
    chart_head_to_head()
    print(f"\nDone. All 5 charts saved in ./{OUTPUT_DIR}/")