import json
import numpy as np
from scipy.stats import wilcoxon
import pandas as pd

# Load the summary files
with open('ChatGPT_results/summary.json', 'r') as f:
    chatgpt_data = json.load(f)

with open('Gemini_results/summary.json', 'r') as f:
    gemini_data = json.load(f)

# Create dictionaries mapping case_name to metrics for easy lookup
chatgpt_cases = {case['case_name']: case for case in chatgpt_data['cases']}
gemini_cases = {case['case_name']: case for case in gemini_data['cases']}

# Get all case names that are in both datasets
common_cases = set(chatgpt_cases.keys()) & set(gemini_cases.keys())
print(f"Number of common cases: {len(common_cases)}\n")

# Initialize lists to store differences
precision_diffs = []
recall_diffs = []
f1_diffs = []

# Calculate differences: di = ChatGPT_i - Gemini_i
for case_name in sorted(common_cases):
    chatgpt_case = chatgpt_cases[case_name]
    gemini_case = gemini_cases[case_name]
    
    precision_diff = chatgpt_case['precision'] - gemini_case['precision']
    recall_diff = chatgpt_case['recall'] - gemini_case['recall']
    f1_diff = chatgpt_case['f1_score'] - gemini_case['f1_score']
    
    precision_diffs.append(precision_diff)
    recall_diffs.append(recall_diff)
    f1_diffs.append(f1_diff)

# Convert to numpy arrays
precision_diffs = np.array(precision_diffs)
recall_diffs = np.array(recall_diffs)
f1_diffs = np.array(f1_diffs)

# Alpha level
alpha = 0.05

# Perform one-tailed Wilcoxon signed rank tests (alternative='greater')
print("=" * 70)
print("WILCOXON SIGNED RANK TEST RESULTS (ONE-TAILED, α = 0.05)")
print("H0: ChatGPT performance ≤ Gemini performance (or no difference)")
print("H1: ChatGPT performance > Gemini performance (ChatGPT is better)")
print("=" * 70)
print()

# Precision test
print("1. PRECISION")
print("-" * 70)
stat_prec, p_prec = wilcoxon(precision_diffs, alternative='greater')
print(f"   Test statistic: {stat_prec}")
print(f"   P-value (one-tailed): {p_prec:.6f}")
print(f"   Significant at α=0.05: {'YES' if p_prec < alpha else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(precision_diffs):.6f}")
print(f"   Median difference: {np.median(precision_diffs):.6f}")
print()

# Recall test
print("2. RECALL")
print("-" * 70)
stat_rec, p_rec = wilcoxon(recall_diffs, alternative='greater')
print(f"   Test statistic: {stat_rec}")
print(f"   P-value (one-tailed): {p_rec:.6f}")
print(f"   Significant at α=0.05: {'YES' if p_rec < alpha else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(recall_diffs):.6f}")
print(f"   Median difference: {np.median(recall_diffs):.6f}")
print()

# F1-score test
print("3. F1-SCORE")
print("-" * 70)
stat_f1, p_f1 = wilcoxon(f1_diffs, alternative='greater')
print(f"   Test statistic: {stat_f1}")
print(f"   P-value (one-tailed): {p_f1:.6f}")
print(f"   Significant at α=0.05: {'YES' if p_f1 < alpha else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(f1_diffs):.6f}")
print(f"   Median difference: {np.median(f1_diffs):.6f}")
print()

# Summary statistics table
print("=" * 70)
print("SUMMARY TABLE")
print("=" * 70)
summary_df = pd.DataFrame({
    'Metric': ['Precision', 'Recall', 'F1-Score'],
    'Test Statistic': [stat_prec, stat_rec, stat_f1],
    'P-value': [p_prec, p_rec, p_f1],
    'Significant (α=0.05)': ['Yes' if p_prec < alpha else 'No',
                              'Yes' if p_rec < alpha else 'No',
                              'Yes' if p_f1 < alpha else 'No'],
    'Mean Diff': [np.mean(precision_diffs), np.mean(recall_diffs), np.mean(f1_diffs)],
    'Median Diff': [np.median(precision_diffs), np.median(recall_diffs), np.median(f1_diffs)]
})
print(summary_df.to_string(index=False))
print()

# Interpretation
print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
significant_count = sum([p_prec < alpha, p_rec < alpha, p_f1 < alpha])
print(f"Number of significant differences (ChatGPT better): {significant_count}/3")
print()
if significant_count > 0:
    print("Metrics where ChatGPT is significantly better (α=0.05):")
    if p_prec < alpha:
        print(f"  - Precision: ChatGPT is better (mean diff = {np.mean(precision_diffs):.6f})")
    if p_rec < alpha:
        print(f"  - Recall: ChatGPT is better (mean diff = {np.mean(recall_diffs):.6f})")
    if p_f1 < alpha:
        print(f"  - F1-Score: ChatGPT is better (mean diff = {np.mean(f1_diffs):.6f})")
else:
    print("ChatGPT is NOT significantly better than Gemini for any metric at α=0.05")
print()
print("Metrics where ChatGPT is NOT significantly better:")
if p_prec >= alpha:
    print(f"  - Precision (p={p_prec:.6f}, mean diff = {np.mean(precision_diffs):.6f})")
if p_rec >= alpha:
    print(f"  - Recall (p={p_rec:.6f}, mean diff = {np.mean(recall_diffs):.6f})")
if p_f1 >= alpha:
    print(f"  - F1-Score (p={p_f1:.6f}, mean diff = {np.mean(f1_diffs):.6f})")