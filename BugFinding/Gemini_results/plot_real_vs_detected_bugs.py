import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def load_classified_results(json_path):
    """Load classified results from a JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("cases", [])

def plot_real_vs_detected_bugs():
    """Create scatter plot of real bugs vs detected bugs"""
    
    # Load data
    chatgpt_cases = load_classified_results("ChatGPT_results/classified_results.json")
    gemini_cases = load_classified_results("Gemini_results/classified_results.json")
    
    # Extract data for ChatGPT
    chatgpt_real_bugs = []
    chatgpt_true_positives = []
    
    for case in chatgpt_cases[1:]:
        chatgpt_real_bugs.append(case.get("num_real_bugs", 0))
        chatgpt_true_positives.append(case.get("true_positives", 0))
    
    # Extract data for Gemini
    gemini_real_bugs = []
    gemini_true_positives = []
    
    for case in gemini_cases[1:]:
        gemini_real_bugs.append(case.get("num_real_bugs", 0))
        gemini_true_positives.append(case.get("true_positives", 0))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot ChatGPT data (circles, blue)
    ax.scatter(chatgpt_real_bugs, chatgpt_true_positives, 
              marker='o', s=120, alpha=0.7, color='#3498db', 
              label='ChatGPT', edgecolors='black', linewidth=1.5)
    
    # Plot Gemini data (squares, red)
    ax.scatter(gemini_real_bugs, gemini_true_positives, 
              marker='s', s=120, alpha=0.7, color='#e74c3c', 
              label='Gemini', edgecolors='black', linewidth=1.5)
    
    # Add reference line y=x (perfect detection)
    all_bugs = chatgpt_real_bugs + gemini_real_bugs
    max_bugs = max(all_bugs) if all_bugs else 10
    perfect_line = np.linspace(0, max_bugs * 1.1, 100)
    ax.plot(perfect_line, perfect_line, 'g--', linewidth=2.5, 
           alpha=0.6, label='Perfect Detection (y=x)')
    
    # Customize plot
    ax.set_xlabel('Number of Real Bugs', fontsize=13, fontweight='bold')
    ax.set_ylabel('Number of True Positives (Detected)', fontsize=13, fontweight='bold')
    ax.set_title('Number of Real Bugs vs Number of Detected Bugs', 
                fontsize=15, fontweight='bold', pad=20)
    ax.legend(fontsize=12, loc='upper left', framealpha=0.95)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Set axis limits
    ax.set_xlim(left=-2)
    ax.set_ylim(bottom=-2)
    
    plt.tight_layout()
    plt.savefig('real_vs_detected_bugs.png', dpi=300, bbox_inches='tight')
    print("Chart saved as 'real_vs_detected_bugs.png'")
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*70)
    print("SCATTER PLOT SUMMARY".center(70))
    print("="*70)
    
    print("\nChatGPT Statistics:")
    print(f"  Total cases: {len(chatgpt_cases)}")
    print(f"  Average real bugs per case: {np.mean(chatgpt_real_bugs):.2f}")
    print(f"  Average true positives per case: {np.mean(chatgpt_true_positives):.2f}")
    total_cgpt_real = sum(chatgpt_real_bugs)
    total_cgpt_tp = sum(chatgpt_true_positives)
    print(f"  Overall detection rate: {total_cgpt_tp}/{total_cgpt_real} = {total_cgpt_tp/total_cgpt_real*100:.2f}%")
    
    print("\nGemini Statistics:")
    print(f"  Total cases: {len(gemini_cases)}")
    print(f"  Average real bugs per case: {np.mean(gemini_real_bugs):.2f}")
    print(f"  Average true positives per case: {np.mean(gemini_true_positives):.2f}")
    total_gmn_real = sum(gemini_real_bugs)
    total_gmn_tp = sum(gemini_true_positives)
    print(f"  Overall detection rate: {total_gmn_tp}/{total_gmn_real} = {total_gmn_tp/total_gmn_real*100:.2f}%")

if __name__ == "__main__":
    plot_real_vs_detected_bugs()