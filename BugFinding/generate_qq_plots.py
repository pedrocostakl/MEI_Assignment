import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import os
import json

OUTPUT_DIR = os.path.join("..", "Report", "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("ChatGPT_results/summary.json", "r") as f:
    chatgpt_data = json.load(f)["cases"]
    
with open("Gemini_results/summary.json", "r") as f:
    gemini_data = json.load(f)["cases"]

chatgpt_metrics = {case["case_name"]: {
    "f1_score": case.get("f1_score"),
    "precision": case.get("precision"),
    "recall": case.get("recall")
} for case in chatgpt_data}

gemini_metrics = {case["case_name"]: {
    "f1_score": case.get("f1_score"),
    "precision": case.get("precision"),
    "recall": case.get("recall")
} for case in gemini_data}

common_cases = sorted(list(set(chatgpt_metrics.keys()) & set(gemini_metrics.keys())))

# Metrics to plot
metrics = ["f1_score", "precision", "recall"]
metric_titles = {"f1_score": "F1-Score", "precision": "Precision", "recall": "Recall"}
metric_labels = {"f1_score": "F1-Score", "precision": "Precision", "recall": "Recall"}

for metric in metrics:
    gpt_data = np.array([chatgpt_metrics[c][metric] for c in common_cases if chatgpt_metrics[c][metric] is not None], dtype=float)
    gem_data = np.array([gemini_metrics[c][metric] for c in common_cases if gemini_metrics[c][metric] is not None], dtype=float)
    
    # ChatGPT Q-Q plot
    fig_gpt, ax_gpt = plt.subplots(figsize=(6, 6))
    stats.probplot(gpt_data, dist="norm", plot=ax_gpt)
    ax_gpt.set_title(f"Q-Q Plot of {metric_titles[metric]}\n(ChatGPT Mini)", fontsize=13, fontweight="bold", pad=12)
    ax_gpt.set_xlabel("Theoretical Quantiles", fontsize=11)
    ax_gpt.set_ylabel(f"Sample Quantiles ({metric_labels[metric]})", fontsize=11)
    
    shapiro_gpt_stat, shapiro_gpt_p = stats.shapiro(gpt_data)
    ax_gpt.annotate(
        f"Shapiro-Wilk: W={shapiro_gpt_stat:.4f}, p={shapiro_gpt_p:.4f}",
        xy=(0.05, 0.95), xycoords="axes fraction",
        fontsize=9, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9),
    )
    fig_gpt.tight_layout()
    qq_path_gpt = os.path.join(OUTPUT_DIR, f"bugfinding_qq_plot_chatgpt_{metric}.png")
    fig_gpt.savefig(qq_path_gpt, bbox_inches="tight", dpi=150)
    plt.close(fig_gpt)
    
    # Gemini Q-Q plot
    fig_gem, ax_gem = plt.subplots(figsize=(6, 6))
    stats.probplot(gem_data, dist="norm", plot=ax_gem)
    ax_gem.set_title(f"Q-Q Plot of {metric_titles[metric]}\n(Gemini Flash)", fontsize=13, fontweight="bold", pad=12)
    ax_gem.set_xlabel("Theoretical Quantiles", fontsize=11)
    ax_gem.set_ylabel(f"Sample Quantiles ({metric_labels[metric]})", fontsize=11)
    
    shapiro_gem_stat, shapiro_gem_p = stats.shapiro(gem_data)
    ax_gem.annotate(
        f"Shapiro-Wilk: W={shapiro_gem_stat:.4f}, p={shapiro_gem_p:.4f}",
        xy=(0.05, 0.95), xycoords="axes fraction",
        fontsize=9, verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9),
    )
    fig_gem.tight_layout()
    qq_path_gem = os.path.join(OUTPUT_DIR, f"bugfinding_qq_plot_gemini_{metric}.png")
    fig_gem.savefig(qq_path_gem, bbox_inches="tight", dpi=150)
    plt.close(fig_gem)
    
    print(f"Saved {qq_path_gpt} and {qq_path_gem}")