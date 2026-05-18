import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_totals(json_path):
    """Load totals from a summary.json file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("totals", {})

def plot_stacked_results():
    """Plot stacked bar chart comparing ChatGPT and Gemini results"""
    
    # Load data from both summary files
    chatgpt_totals = load_totals("./ChatGPT_results/summary.json")
    gemini_totals = load_totals("./Gemini_results/summary.json")
    
    # Extract metrics
    labels = ["ChatGPT", "Gemini"]
    true_positives = [
        chatgpt_totals.get("true_positives", 0),
        gemini_totals.get("true_positives", 0)
    ]
    false_positives = [
        chatgpt_totals.get("false_positives", 0),
        gemini_totals.get("false_positives", 0)
    ]
    false_negatives = [
        chatgpt_totals.get("false_negatives", 0),
        gemini_totals.get("false_negatives", 0)
    ]
    
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Set up x-axis positions
    x = np.arange(len(labels))
    width = 0.6
    
    # Create stacked bars
    p1 = ax.bar(x, true_positives, width, label='True Positives', color='#2ecc71')
    p2 = ax.bar(x, false_positives, width, bottom=true_positives, 
                label='False Positives', color='#e74c3c')
    p3 = ax.bar(x, false_negatives, width,
                bottom=np.array(true_positives) + np.array(false_positives),
                label='False Negatives', color='#f39c12')
    
    # Customize chart
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Bug Detection Results: ChatGPT vs Gemini', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on each segment
    for i, (tp, fp, fn) in enumerate(zip(true_positives, false_positives, false_negatives)):
        ax.text(i, tp/2, str(tp), ha='center', va='center', fontweight='bold', color='white')
        ax.text(i, tp + fp/2, str(fp), ha='center', va='center', fontweight='bold', color='white')
        ax.text(i, tp + fp + fn/2, str(fn), ha='center', va='center', fontweight='bold', color='white')
    
    plt.tight_layout()
    plt.savefig('bug_detection_comparison.png', dpi=300, bbox_inches='tight')
    print("Chart saved as 'bug_detection_comparison.png'")
    plt.show()

if __name__ == "__main__":
    plot_stacked_results()