import json
import numpy as np
from pathlib import Path

def calculate_metrics(case):
    """Calculate Precision, Recall, and F1-score for a single case"""
    tp = case.get('true_positives', 0)
    fp = case.get('false_positives', 0)
    fn = case.get('false_negatives', 0)
    
    # Precision = TP / (TP + FP)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    
    # Recall = TP / (TP + FN)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    # F1 = 2 * (Precision * Recall) / (Precision + Recall)
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

def calculate_summary_stats(summary_file_path):
    """Calculate mean and std dev for metrics from a summary JSON file"""
    with open(summary_file_path, 'r') as f:
        data = json.load(f)
    
    cases = data.get('cases', [])
    
    precisions = []
    recalls = []
    f1_scores = []
    
    for case in cases:
        metrics = calculate_metrics(case)
        precisions.append(metrics['precision'])
        recalls.append(metrics['recall'])
        f1_scores.append(metrics['f1'])
    
    # Calculate statistics
    stats = {
        'precision': {
            'mean': np.mean(precisions),
            'std': np.std(precisions),
            'values': precisions
        },
        'recall': {
            'mean': np.mean(recalls),
            'std': np.std(recalls),
            'values': recalls
        },
        'f1': {
            'mean': np.mean(f1_scores),
            'std': np.std(f1_scores),
            'values': f1_scores
        }
    }
    
    return stats

def main():
    base_path = Path(__file__).parent
    
    chatgpt_summary = base_path / 'ChatGPT_results' / 'summary.json'
    gemini_summary = base_path / 'Gemini_results' / 'summary.json'
    
    print("=" * 70)
    print("MODEL METRICS COMPARISON")
    print("=" * 70)
    
    # ChatGPT Results
    if chatgpt_summary.exists():
        print("\nChatGPT Results:")
        print("-" * 70)
        chatgpt_stats = calculate_summary_stats(chatgpt_summary)
        
        print(f"\nPrecision:")
        print(f"  Mean: {chatgpt_stats['precision']['mean']:.4f}")
        print(f"  Std Dev: {chatgpt_stats['precision']['std']:.4f}")
        
        print(f"\nRecall:")
        print(f"  Mean: {chatgpt_stats['recall']['mean']:.4f}")
        print(f"  Std Dev: {chatgpt_stats['recall']['std']:.4f}")
        
        print(f"\nF1-Score:")
        print(f"  Mean: {chatgpt_stats['f1']['mean']:.4f}")
        print(f"  Std Dev: {chatgpt_stats['f1']['std']:.4f}")
    else:
        print(f"\nError: ChatGPT summary file not found at {chatgpt_summary}")
    
    # Gemini Results
    if gemini_summary.exists():
        print("\n" + "=" * 70)
        print("\nGemini Results:")
        print("-" * 70)
        gemini_stats = calculate_summary_stats(gemini_summary)
        
        print(f"\nPrecision:")
        print(f"  Mean: {gemini_stats['precision']['mean']:.4f}")
        print(f"  Std Dev: {gemini_stats['precision']['std']:.4f}")
        
        print(f"\nRecall:")
        print(f"  Mean: {gemini_stats['recall']['mean']:.4f}")
        print(f"  Std Dev: {gemini_stats['recall']['std']:.4f}")
        
        print(f"\nF1-Score:")
        print(f"  Mean: {gemini_stats['f1']['mean']:.4f}")
        print(f"  Std Dev: {gemini_stats['f1']['std']:.4f}")
    else:
        print(f"\nError: Gemini summary file not found at {gemini_summary}")
    
    # Comparison
    if chatgpt_summary.exists() and gemini_summary.exists():
        print("\n" + "=" * 70)
        print("\nComparison (ChatGPT vs Gemini):")
        print("-" * 70)
        
        print(f"\nPrecision:")
        print(f"  ChatGPT: {chatgpt_stats['precision']['mean']:.4f} ± {chatgpt_stats['precision']['std']:.4f}")
        print(f"  Gemini:  {gemini_stats['precision']['mean']:.4f} ± {gemini_stats['precision']['std']:.4f}")
        print(f"  Difference: {chatgpt_stats['precision']['mean'] - gemini_stats['precision']['mean']:.4f}")
        
        print(f"\nRecall:")
        print(f"  ChatGPT: {chatgpt_stats['recall']['mean']:.4f} ± {chatgpt_stats['recall']['std']:.4f}")
        print(f"  Gemini:  {gemini_stats['recall']['mean']:.4f} ± {gemini_stats['recall']['std']:.4f}")
        print(f"  Difference: {chatgpt_stats['recall']['mean'] - gemini_stats['recall']['mean']:.4f}")
        
        print(f"\nF1-Score:")
        print(f"  ChatGPT: {chatgpt_stats['f1']['mean']:.4f} ± {chatgpt_stats['f1']['std']:.4f}")
        print(f"  Gemini:  {gemini_stats['f1']['mean']:.4f} ± {gemini_stats['f1']['std']:.4f}")
        print(f"  Difference: {chatgpt_stats['f1']['mean'] - gemini_stats['f1']['mean']:.4f}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()