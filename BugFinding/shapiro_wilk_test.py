import json
import numpy as np
from scipy import stats
from pathlib import Path

def load_metrics_from_summary(json_path):
    """Load precision, recall, and F1 scores from summary.json"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    metrics = {
        'precision': [],
        'recall': [],
        'f1_score': []
    }
    
    for case in data.get("cases", []):
        metrics['precision'].append(case.get('precision', 0))
        metrics['recall'].append(case.get('recall', 0))
        metrics['f1_score'].append(case.get('f1_score', 0))
    
    return metrics

def shapiro_wilk_normality_test(json_path, alpha=0.05, name="Results"):
    """
    Perform Shapiro-Wilk normality test on metrics from summary.json
    
    Parameters:
    -----------
    json_path : str
        Path to the summary.json file
    alpha : float
        Significance level (default: 0.05)
    name : str
        Name of the dataset (for display)
    """
    
    metrics = load_metrics_from_summary(json_path)
    
    print(f"\n{'='*60}")
    print(f"Shapiro-Wilk Normality Test - {name}")
    print(f"{'='*60}")
    print(f"Alpha (significance level): {alpha}\n")
    
    results = {}
    
    for metric_name, values in metrics.items():
        if len(values) < 3:
            print(f"{metric_name.upper()}: Insufficient data (need at least 3 samples)")
            continue
        
        # Perform Shapiro-Wilk test
        statistic, p_value = stats.shapiro(values)
        
        # Determine normality
        is_normal = p_value > alpha
        result_text = "NORMAL" if is_normal else "NOT NORMAL"
        
        results[metric_name] = {
            'statistic': statistic,
            'p_value': p_value,
            'is_normal': is_normal,
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values)
        }
        
        print(f"{metric_name.upper()}:")
        print(f"  Test Statistic: {statistic:.6f}")
        print(f"  P-value: {p_value:.6f}")
        print(f"  Result: {result_text} (p {'>' if is_normal else '<='} {alpha})")
        print(f"  Mean: {np.mean(values):.6f}")
        print(f"  Std Dev: {np.std(values):.6f}")
        print(f"  Min: {np.min(values):.6f}")
        print(f"  Max: {np.max(values):.6f}")
        print()
    
    return results

def compare_both_models(alpha=0.05):
    """Compare normality tests for both ChatGPT and Gemini results"""
    
    chatgpt_path = "./ChatGPT_results/summary.json"
    gemini_path = "./Gemini_results/summary.json"
    
    print("\n" + "="*60)
    print("SHAPIRO-WILK NORMALITY TEST - BUG DETECTION RESULTS")
    print("="*60)
    
    chatgpt_results = shapiro_wilk_normality_test(chatgpt_path, alpha, "ChatGPT")
    gemini_results = shapiro_wilk_normality_test(gemini_path, alpha, "Gemini")
    
    # Summary comparison
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for metric in ['precision', 'recall', 'f1_score']:
        print(f"\n{metric.upper()}:")
        print(f"  ChatGPT: {'NORMAL' if chatgpt_results[metric]['is_normal'] else 'NOT NORMAL'} (p={chatgpt_results[metric]['p_value']:.6f})")
        print(f"  Gemini:  {'NORMAL' if gemini_results[metric]['is_normal'] else 'NOT NORMAL'} (p={gemini_results[metric]['p_value']:.6f})")

if __name__ == "__main__":
    # Test with default alpha=0.05
    compare_both_models(alpha=0.05)
    
    # Uncomment below to test with different alpha values
    # compare_both_models(alpha=0.01)  # More strict
    # compare_both_models(alpha=0.10)  # More lenient