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

chatgpt_f1 = {case["case_name"]: case["f1_score"] for case in chatgpt_data}
gemini_f1 = {case["case_name"]: case["f1_score"] for case in gemini_data}

common_cases = sorted(list(set(chatgpt_f1.keys()) & set(gemini_f1.keys())))

gpt_f1_arr = np.array([chatgpt_f1[c] for c in common_cases], dtype=float)
gem_f1_arr = np.array([gemini_f1[c] for c in common_cases], dtype=float)

# 1. ChatGPT
fig_gpt, ax_gpt = plt.subplots(figsize=(6, 6))
stats.probplot(gpt_f1_arr, dist="norm", plot=ax_gpt)
ax_gpt.set_title("Q-Q Plot of F1-Scores\n(ChatGPT Mini)", fontsize=13, fontweight="bold", pad=12)
ax_gpt.set_xlabel("Theoretical Quantiles", fontsize=11)
ax_gpt.set_ylabel("Sample Quantiles (F1-Score)", fontsize=11)

shapiro_gpt_stat, shapiro_gpt_p = stats.shapiro(gpt_f1_arr)
ax_gpt.annotate(
    f"Shapiro-Wilk: W={shapiro_gpt_stat:.4f}, p={shapiro_gpt_p:.4f}",
    xy=(0.05, 0.95), xycoords="axes fraction",
    fontsize=9, verticalalignment="top",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9),
)
fig_gpt.tight_layout()
qq_path_gpt = os.path.join(OUTPUT_DIR, "bugfinding_qq_plot_chatgpt.png")
fig_gpt.savefig(qq_path_gpt, bbox_inches="tight", dpi=150)
plt.close(fig_gpt)

# 2. Gemini
fig_gem, ax_gem = plt.subplots(figsize=(6, 6))
stats.probplot(gem_f1_arr, dist="norm", plot=ax_gem)
ax_gem.set_title("Q-Q Plot of F1-Scores\n(Gemini Flash)", fontsize=13, fontweight="bold", pad=12)
ax_gem.set_xlabel("Theoretical Quantiles", fontsize=11)
ax_gem.set_ylabel("Sample Quantiles (F1-Score)", fontsize=11)

shapiro_gem_stat, shapiro_gem_p = stats.shapiro(gem_f1_arr)
ax_gem.annotate(
    f"Shapiro-Wilk: W={shapiro_gem_stat:.4f}, p={shapiro_gem_p:.4f}",
    xy=(0.05, 0.95), xycoords="axes fraction",
    fontsize=9, verticalalignment="top",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="lightyellow", edgecolor="gray", alpha=0.9),
)
fig_gem.tight_layout()
qq_path_gem = os.path.join(OUTPUT_DIR, "bugfinding_qq_plot_gemini.png")
fig_gem.savefig(qq_path_gem, bbox_inches="tight", dpi=150)
plt.close(fig_gem)

print(f"Saved {qq_path_gpt} and {qq_path_gem}")
