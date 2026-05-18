"""
LLM Comparison Graphics: ChatGPT vs Gemini
Generates scatterplots, boxplots, violin plots, bar charts,
and a correlation heatmap for statistical comparison.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Patch
from scipy import stats
import warnings
warnings.filterwarnings("ignore")

# ── Config ──────────────────────────────────────────────────────────────────
DATA_PATH   = "results_organized.csv"
OUTPUT_DIR  = "."          # change to a folder if you prefer
PALETTE     = {"ChatGPT": "#10A37F", "Gemini": "#4285F4"}
ALPHA       = 0.72
FIGSIZE_SM  = (10, 5)
FIGSIZE_MD  = (14, 10)
NUMERIC_FEATURES = [
    "Avg_Complexity",
    "Maintainability_Index",
    "Lines_of_Code",
    "Latency",
    "Execution_Time",
]
FEATURE_LABELS = {
    "Avg_Complexity":       "Avg Complexity",
    "Maintainability_Index":"Maintainability Index",
    "Lines_of_Code":        "Lines of Code",
    "Latency":              "Latency (s)",
    "Execution_Time":       "Execution Time (s)",
}

# ── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=NUMERIC_FEATURES)
models = df["Model"].unique()
colors = [PALETTE[m] for m in models]

print(f"Loaded {len(df)} rows — models: {list(models)}")
print(df.groupby("Model")[NUMERIC_FEATURES].describe().round(3).to_string())
print()


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 1 — Scatterplot matrix (pairs plot)
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 1: Scatterplot matrix …")
n = len(NUMERIC_FEATURES)
fig, axes = plt.subplots(n, n, figsize=(14, 13))
fig.suptitle("Scatterplot Matrix — ChatGPT vs Gemini", fontsize=15, y=1.01)

for i, feat_y in enumerate(NUMERIC_FEATURES):
    for j, feat_x in enumerate(NUMERIC_FEATURES):
        ax = axes[i][j]
        if i == j:
            # Diagonal — KDE
            for model, grp in df.groupby("Model"):
                grp[feat_x].plot.kde(ax=ax, color=PALETTE[model],
                                     lw=2, label=model)
            ax.set_yticks([])
        else:
            for model, grp in df.groupby("Model"):
                ax.scatter(grp[feat_x], grp[feat_y],
                           color=PALETTE[model], alpha=ALPHA,
                           s=22, label=model)
        # Labels only on edges
        if i == n - 1:
            ax.set_xlabel(FEATURE_LABELS[feat_x], fontsize=7)
        else:
            ax.set_xticklabels([])
        if j == 0:
            ax.set_ylabel(FEATURE_LABELS[feat_y], fontsize=7)
        else:
            ax.set_yticklabels([])
        ax.tick_params(labelsize=6)

legend_handles = [Patch(color=PALETTE[m], label=m) for m in models]
fig.legend(handles=legend_handles, loc="upper right",
           bbox_to_anchor=(1.0, 1.0), fontsize=10, title="Model")
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig1_scatterplot_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig1_scatterplot_matrix.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Box plots (all features, side-by-side)
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 2: Box plots …")
fig, axes = plt.subplots(1, len(NUMERIC_FEATURES), figsize=(16, 5))
fig.suptitle("Feature Distributions — Box Plots", fontsize=13)

for ax, feat in zip(axes, NUMERIC_FEATURES):
    data_by_model = [df[df["Model"] == m][feat].values for m in models]
    bp = ax.boxplot(data_by_model, patch_artist=True,
                    medianprops=dict(color="white", lw=2),
                    whiskerprops=dict(lw=1.2),
                    capprops=dict(lw=1.2),
                    flierprops=dict(marker="o", markersize=4, alpha=0.5))
    for patch, model in zip(bp["boxes"], models):
        patch.set_facecolor(PALETTE[model])
        patch.set_alpha(0.8)
    for flier, model in zip(bp["fliers"], models):
        flier.set_markerfacecolor(PALETTE[model])

    # Mann-Whitney U p-value annotation
    u_stat, p_val = stats.mannwhitneyu(*data_by_model, alternative="two-sided")
    ax.set_title(f"{FEATURE_LABELS[feat]}\np={p_val:.3f}{'*' if p_val < 0.05 else ''}",
                 fontsize=9)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(models, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

legend_handles = [Patch(color=PALETTE[m], label=m) for m in models]
fig.legend(handles=legend_handles, loc="upper right", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig2_boxplots.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig2_boxplots.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Violin plots
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 3: Violin plots …")
fig, axes = plt.subplots(1, len(NUMERIC_FEATURES), figsize=(16, 5))
fig.suptitle("Feature Distributions — Violin Plots", fontsize=13)

for ax, feat in zip(axes, NUMERIC_FEATURES):
    data_by_model = [df[df["Model"] == m][feat].values for m in models]
    parts = ax.violinplot(data_by_model, positions=[1, 2],
                          showmedians=True, showextrema=True)
    for i, (pc, model) in enumerate(zip(parts["bodies"], models)):
        pc.set_facecolor(PALETTE[model])
        pc.set_alpha(0.75)
    parts["cmedians"].set_color("white")
    parts["cmedians"].set_lw(2)
    parts["cmins"].set_color("grey")
    parts["cmaxes"].set_color("grey")
    parts["cbars"].set_color("grey")

    ax.set_title(FEATURE_LABELS[feat], fontsize=9)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(models, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

legend_handles = [Patch(color=PALETTE[m], label=m) for m in models]
fig.legend(handles=legend_handles, loc="upper right", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig3_violinplots.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig3_violinplots.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 4 — Mean bar chart with 95 % CI error bars
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 4: Mean bar chart with CI …")
fig, axes = plt.subplots(1, len(NUMERIC_FEATURES), figsize=(16, 5))
fig.suptitle("Mean ± 95 % CI per Feature", fontsize=13)

x = np.array([0, 1])
bar_w = 0.35

for ax, feat in zip(axes, NUMERIC_FEATURES):
    means, cis = [], []
    for model in models:
        vals = df[df["Model"] == model][feat].dropna()
        m = vals.mean()
        se = stats.sem(vals)
        ci = se * stats.t.ppf(0.975, df=len(vals)-1)
        means.append(m)
        cis.append(ci)

    bars = ax.bar(x, means, width=bar_w, yerr=cis,
                  color=[PALETTE[m] for m in models],
                  alpha=0.85, capsize=5, error_kw=dict(lw=1.5))
    ax.set_title(FEATURE_LABELS[feat], fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

legend_handles = [Patch(color=PALETTE[m], label=m) for m in models]
fig.legend(handles=legend_handles, loc="upper right", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig4_mean_ci_bars.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig4_mean_ci_bars.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — Success rate bar chart
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 5: Success rate …")
success_rate = df.groupby("Model")["Success"].mean() * 100

fig, ax = plt.subplots(figsize=(6, 5))
bars = ax.bar(success_rate.index, success_rate.values,
              color=[PALETTE[m] for m in success_rate.index],
              alpha=0.85, width=0.45)
for bar, val in zip(bars, success_rate.values):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.5,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=11)
ax.set_title("Success Rate by Model", fontsize=13)
ax.set_ylabel("Success (%)")
ax.set_ylim(0, 115)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig5_success_rate.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig5_success_rate.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 6 — Scatter: Latency vs Execution Time (coloured by model)
#            with linear regression lines
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 6: Latency vs Execution Time scatter …")
fig, ax = plt.subplots(figsize=(8, 6))

for model, grp in df.groupby("Model"):
    ax.scatter(grp["Latency"], grp["Execution_Time"],
               color=PALETTE[model], alpha=ALPHA, s=55, label=model, zorder=3)
    # Regression line
    slope, intercept, r, p, _ = stats.linregress(grp["Latency"], grp["Execution_Time"])
    x_line = np.linspace(grp["Latency"].min(), grp["Latency"].max(), 100)
    ax.plot(x_line, slope * x_line + intercept,
            color=PALETTE[model], lw=2, linestyle="--",
            label=f"{model} fit (r={r:.2f})")

ax.set_xlabel("Latency (s)", fontsize=11)
ax.set_ylabel("Execution Time (s)", fontsize=11)
ax.set_title("Latency vs Execution Time — with Regression", fontsize=13)
ax.legend(fontsize=9)
ax.grid(linestyle="--", alpha=0.35)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig6_scatter_latency_exectime.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig6_scatter_latency_exectime.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 7 — Scatter: Avg Complexity vs Maintainability Index
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 7: Complexity vs Maintainability scatter …")
fig, ax = plt.subplots(figsize=(8, 6))

for model, grp in df.groupby("Model"):
    ax.scatter(grp["Avg_Complexity"], grp["Maintainability_Index"],
               color=PALETTE[model], alpha=ALPHA, s=55, label=model, zorder=3)
    slope, intercept, r, p, _ = stats.linregress(
        grp["Avg_Complexity"], grp["Maintainability_Index"])
    x_line = np.linspace(grp["Avg_Complexity"].min(),
                         grp["Avg_Complexity"].max(), 100)
    ax.plot(x_line, slope * x_line + intercept,
            color=PALETTE[model], lw=2, linestyle="--",
            label=f"{model} fit (r={r:.2f})")

ax.set_xlabel("Avg Complexity", fontsize=11)
ax.set_ylabel("Maintainability Index", fontsize=11)
ax.set_title("Avg Complexity vs Maintainability Index", fontsize=13)
ax.legend(fontsize=9)
ax.grid(linestyle="--", alpha=0.35)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig7_scatter_complexity_maintainability.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("  → fig7_scatter_complexity_maintainability.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 8 — Correlation heatmap per model
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 8: Correlation heatmaps …")
try:
    import seaborn as sns
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Correlation Heatmap per Model", fontsize=13)

    for ax, model in zip(axes, models):
        corr = df[df["Model"] == model][NUMERIC_FEATURES].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, ax=ax, annot=True, fmt=".2f",
                    cmap="coolwarm", center=0, vmin=-1, vmax=1,
                    square=True, linewidths=0.5,
                    xticklabels=[FEATURE_LABELS[f] for f in NUMERIC_FEATURES],
                    yticklabels=[FEATURE_LABELS[f] for f in NUMERIC_FEATURES])
        ax.set_title(model, fontsize=11)
        ax.tick_params(axis="x", rotation=30, labelsize=8)
        ax.tick_params(axis="y", rotation=0,  labelsize=8)

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/fig11_correlation_heatmaps.png",
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  → fig11_correlation_heatmaps.png")
except ImportError:
    print("  seaborn not found — skipping Figure 11 (install with: pip install seaborn)")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 12 — Strip + Box overlay (jitter plot)
# ════════════════════  

rng = np.random.default_rng(42)

for ax, feat in zip(axes, NUMERIC_FEATURES):
    for pos, model in enumerate([models[0], models[1]], start=1):
        vals = df[df["Model"] == model][feat].values
        jitter = rng.uniform(-0.12, 0.12, size=len(vals))
        ax.scatter(pos + jitter, vals,
                   color=PALETTE[model], alpha=0.55, s=18, zorder=3)

    data_by_model = [df[df["Model"] == m][feat].values for m in models]
    bp = ax.boxplot(data_by_model, positions=[1, 2],
                    patch_artist=True, widths=0.28,
                    medianprops=dict(color="white", lw=2),
                    whiskerprops=dict(lw=1.2, linestyle="--"),
                    capprops=dict(lw=1.2),
                    flierprops=dict(marker=""))
    for patch, model in zip(bp["boxes"], models):
        patch.set_facecolor(PALETTE[model])
        patch.set_alpha(0.3)

    ax.set_title(FEATURE_LABELS[feat], fontsize=9)
    ax.set_xticks([1, 2])
    ax.set_xticklabels(models, fontsize=9)
    ax.grid(axis="y", linestyle="--", alpha=0.35)

legend_handles = [Patch(color=PALETTE[m], label=m) for m in models]
fig.legend(handles=legend_handles, loc="upper right", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig12_strip_box_overlay.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig12_strip_box_overlay.png")


# ════════════════════════════════════════════════════════════════════════════
# FIGURE 14 — Radar / Spider chart (mean-normalised)
# ════════════════════════════════════════════════════════════════════════════
print("Generating Figure 14: Radar chart …")          

# Normalise 0-1 per feature (min–max across both models)
means = df.groupby("Model")[NUMERIC_FEATURES].mean()
feat_min = means.min()
feat_max = means.max()
norm = (means - feat_min) / (feat_max - feat_min + 1e-9)

labels = [FEATURE_LABELS[f] for f in NUMERIC_FEATURES]
num_vars = len(labels)
angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
angles += angles[:1]   # close polygon

fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
fig.suptitle("Radar Chart — Normalised Means\n(higher = better/larger value)",
             fontsize=12, y=1.02)

for model in models:
    vals = norm.loc[model].tolist() + [norm.loc[model].tolist()[0]]
    ax.plot(angles, vals, color=PALETTE[model], lw=2, label=model)
    ax.fill(angles, vals, color=PALETTE[model], alpha=0.18)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels, size=9)
ax.set_yticks([0.25, 0.5, 0.75, 1.0])
ax.set_yticklabels(["0.25", "0.50", "0.75", "1.00"], size=7, color="grey")
ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=10)
plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/fig14_radar_chart.png", dpi=150, bbox_inches="tight")
plt.close()
print("  → fig14_radar_chart.png")


# ════════════════════════════════════════════════════════════════════════════
# Summary statistics + Mann-Whitney U table
# ════════════════════════════════════════════════════════════════════════════
print()
print("═" * 60)
print("Mann-Whitney U test (two-sided) — feature significance")
print("═" * 60)
for feat in NUMERIC_FEATURES:
    a = df[df["Model"] == models[0]][feat].dropna()
    b = df[df["Model"] == models[1]][feat].dropna()
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    sig = "**" if p < 0.01 else ("*" if p < 0.05 else "ns")
    print(f"  {FEATURE_LABELS[feat]:<28}  U={u:.0f}  p={p:.4f}  {sig}")

print()
print("All figures saved. Done ✓")