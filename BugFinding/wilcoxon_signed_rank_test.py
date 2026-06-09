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

# Alpha level and Bonferroni correction
alpha = 0.05
num_tests = 3  # Precision, Recall, F1-Score
alpha_bonferroni = alpha / num_tests

# Helper function to count differences
def count_differences(diffs):
    positive = np.sum(diffs > 0)  # ChatGPT better
    negative = np.sum(diffs < 0)  # Gemini better
    zero = np.sum(diffs == 0)     # Tie
    return positive, negative, zero

# Count differences for each metric
prec_pos, prec_neg, prec_zero = count_differences(precision_diffs)
rec_pos, rec_neg, rec_zero = count_differences(recall_diffs)
f1_pos, f1_neg, f1_zero = count_differences(f1_diffs)

# Perform one-tailed Wilcoxon signed rank tests (alternative='greater')
print("=" * 80)
print("WILCOXON SIGNED RANK TEST RESULTS (ONE-TAILED, WITH BONFERRONI CORRECTION)")
print(f"Original α = {alpha}, Bonferroni-corrected α = {alpha_bonferroni:.6f}")
print(f"Number of tests: {num_tests}")
print("H0: ChatGPT performance ≤ Gemini performance (or no difference)")
print("H1: ChatGPT performance > Gemini performance (ChatGPT is better)")
print("=" * 80)
print()

# Precision test
print("1. PRECISION")
print("-" * 80)
stat_prec, p_prec = wilcoxon(precision_diffs, alternative='greater')
print(f"   Test statistic: {stat_prec}")
print(f"   P-value (one-tailed): {p_prec:.6f}")
print(f"   Significant at α=0.05 (unadjusted): {'YES' if p_prec < alpha else 'NO'}")
print(f"   Significant at α={alpha_bonferroni:.6f} (Bonferroni-adjusted): {'YES' if p_prec < alpha_bonferroni else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(precision_diffs):.6f}")
print(f"   Median difference: {np.median(precision_diffs):.6f}")
print(f"   Difference counts:")
print(f"      - ChatGPT better (positive): {prec_pos}")
print(f"      - Gemini better (negative): {prec_neg}")
print(f"      - Tie (zero): {prec_zero}")
print()

# Recall test
print("2. RECALL")
print("-" * 80)
stat_rec, p_rec = wilcoxon(recall_diffs, alternative='greater')
print(f"   Test statistic: {stat_rec}")
print(f"   P-value (one-tailed): {p_rec:.6f}")
print(f"   Significant at α=0.05 (unadjusted): {'YES' if p_rec < alpha else 'NO'}")
print(f"   Significant at α={alpha_bonferroni:.6f} (Bonferroni-adjusted): {'YES' if p_rec < alpha_bonferroni else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(recall_diffs):.6f}")
print(f"   Median difference: {np.median(recall_diffs):.6f}")
print(f"   Difference counts:")
print(f"      - ChatGPT better (positive): {rec_pos}")
print(f"      - Gemini better (negative): {rec_neg}")
print(f"      - Tie (zero): {rec_zero}")
print()

# F1-score test
print("3. F1-SCORE")
print("-" * 80)
stat_f1, p_f1 = wilcoxon(f1_diffs, alternative='greater')
print(f"   Test statistic: {stat_f1}")
print(f"   P-value (one-tailed): {p_f1:.6f}")
print(f"   Significant at α=0.05 (unadjusted): {'YES' if p_f1 < alpha else 'NO'}")
print(f"   Significant at α={alpha_bonferroni:.6f} (Bonferroni-adjusted): {'YES' if p_f1 < alpha_bonferroni else 'NO'}")
print(f"   Mean difference (ChatGPT - Gemini): {np.mean(f1_diffs):.6f}")
print(f"   Median difference: {np.median(f1_diffs):.6f}")
print(f"   Difference counts:")
print(f"      - ChatGPT better (positive): {f1_pos}")
print(f"      - Gemini better (negative): {f1_neg}")
print(f"      - Tie (zero): {f1_zero}")
print()

# Summary statistics table
print("=" * 80)
print("SUMMARY TABLE")
print("=" * 80)
summary_df = pd.DataFrame({
    'Metric': ['Precision', 'Recall', 'F1-Score'],
    'Test Statistic': [stat_prec, stat_rec, stat_f1],
    'P-value': [p_prec, p_rec, p_f1],
    'Sig. (α=0.05)': ['Yes' if p_prec < alpha else 'No',
                      'Yes' if p_rec < alpha else 'No',
                      'Yes' if p_f1 < alpha else 'No'],
    'Sig. (Bonf.)': ['Yes' if p_prec < alpha_bonferroni else 'No',
                     'Yes' if p_rec < alpha_bonferroni else 'No',
                     'Yes' if p_f1 < alpha_bonferroni else 'No'],
    'ChatGPT Better': [prec_pos, rec_pos, f1_pos],
    'Gemini Better': [prec_neg, rec_neg, f1_neg],
    'Tie': [prec_zero, rec_zero, f1_zero],
    'Mean Diff': [np.mean(precision_diffs), np.mean(recall_diffs), np.mean(f1_diffs)],
    'Median Diff': [np.median(precision_diffs), np.median(recall_diffs), np.median(f1_diffs)]
})
print(summary_df.to_string(index=False))
print()

# Interpretation (using Bonferroni-corrected alpha)
print("=" * 80)
print("INTERPRETATION (Using Bonferroni-corrected α)")
print("=" * 80)
significant_count = sum([p_prec < alpha_bonferroni, p_rec < alpha_bonferroni, p_f1 < alpha_bonferroni])
print(f"Number of significant differences (ChatGPT better): {significant_count}/3")
print()
if significant_count > 0:
    print("Metrics where ChatGPT is significantly better:")
    if p_prec < alpha_bonferroni:
        print(f"  - Precision: ChatGPT is better (p={p_prec:.6f}, mean diff = {np.mean(precision_diffs):.6f})")
        print(f"    Cases: ChatGPT better in {prec_pos}/{len(common_cases)}, Gemini better in {prec_neg}/{len(common_cases)}, Tie in {prec_zero}/{len(common_cases)}")
    if p_rec < alpha_bonferroni:
        print(f"  - Recall: ChatGPT is better (p={p_rec:.6f}, mean diff = {np.mean(recall_diffs):.6f})")
        print(f"    Cases: ChatGPT better in {rec_pos}/{len(common_cases)}, Gemini better in {rec_neg}/{len(common_cases)}, Tie in {rec_zero}/{len(common_cases)}")
    if p_f1 < alpha_bonferroni:
        print(f"  - F1-Score: ChatGPT is better (p={p_f1:.6f}, mean diff = {np.mean(f1_diffs):.6f})")
        print(f"    Cases: ChatGPT better in {f1_pos}/{len(common_cases)}, Gemini better in {f1_neg}/{len(common_cases)}, Tie in {f1_zero}/{len(common_cases)}")
else:
    print("ChatGPT is NOT significantly better than Gemini for any metric (Bonferroni-corrected)")
print()
print("Metrics where ChatGPT is NOT significantly better (Bonferroni-corrected):")
if p_prec >= alpha_bonferroni:
    print(f"  - Precision (p={p_prec:.6f}, mean diff = {np.mean(precision_diffs):.6f})")
    print(f"    Cases: ChatGPT better in {prec_pos}/{len(common_cases)}, Gemini better in {prec_neg}/{len(common_cases)}, Tie in {prec_zero}/{len(common_cases)}")
if p_rec >= alpha_bonferroni:
    print(f"  - Recall (p={p_rec:.6f}, mean diff = {np.mean(recall_diffs):.6f})")
    print(f"    Cases: ChatGPT better in {rec_pos}/{len(common_cases)}, Gemini better in {rec_neg}/{len(common_cases)}, Tie in {rec_zero}/{len(common_cases)}")
if p_f1 >= alpha_bonferroni:
    print(f"  - F1-Score (p={p_f1:.6f}, mean diff = {np.mean(f1_diffs):.6f})")
    print(f"    Cases: ChatGPT better in {f1_pos}/{len(common_cases)}, Gemini better in {f1_neg}/{len(common_cases)}, Tie in {f1_zero}/{len(common_cases)}")
print()
print(f"Note: Bonferroni correction divides α by {num_tests} tests: {alpha} / {num_tests} = {alpha_bonferroni:.6f}")