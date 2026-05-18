import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

def load_classified_results(json_path):
    """Load classified results from a JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("cases", [])

def extract_project_name(case_name):
    """Extract project name from case_name (e.g., 'fastapi_1' -> 'fastapi')"""
    parts = case_name.rsplit('_', 1)
    return parts[0] if parts else case_name

def aggregate_by_project(cases):
    """Aggregate metrics by project"""
    projects = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
    
    for case in cases:
        project = extract_project_name(case["case_name"])
        projects[project]["tp"] += case.get("true_positives", 0)
        projects[project]["fp"] += case.get("false_positives", 0)
        projects[project]["fn"] += case.get("false_negatives", 0)
    
    return projects

def plot_project_stacked_bars():
    """Plot stacked bar charts comparing ChatGPT and Gemini by project"""
    
    # Load data from both files
    chatgpt_cases = load_classified_results("ChatGPT_results/classified_results.json")
    gemini_cases = load_classified_results("Gemini_results/classified_results.json")
    
    # Aggregate by project
    chatgpt_projects = aggregate_by_project(chatgpt_cases)
    gemini_projects = aggregate_by_project(gemini_cases)
    
    # Define projects and their order
    projects = ["fastapi", "httpie", "sanic", "scrapy", "tornado"]
    
    # Create figure with subplots
    fig, axes = plt.subplots(1, 5, figsize=(20, 6), sharey=True)
    fig.suptitle('Bug Detection Results by Project: ChatGPT vs Gemini', 
                 fontsize=16, fontweight='bold', y=1.02)
    
    width = 0.35
    
    for idx, project in enumerate(projects):
        ax = axes[idx]
        
        # Get data for this project
        chatgpt_data = chatgpt_projects.get(project, {"tp": 0, "fp": 0, "fn": 0})
        gemini_data = gemini_projects.get(project, {"tp": 0, "fp": 0, "fn": 0})
        
        # Prepare data for stacking
        x = np.arange(2)  # Two bars: ChatGPT and Gemini
        labels = ["ChatGPT", "Gemini"]
        
        tp_values = [chatgpt_data["tp"], gemini_data["tp"]]
        fp_values = [chatgpt_data["fp"], gemini_data["fp"]]
        fn_values = [chatgpt_data["fn"], gemini_data["fn"]]
        
        # Create stacked bars
        p1 = ax.bar(x, tp_values, width, label='TP', color='#2ecc71')
        p2 = ax.bar(x, fp_values, width, bottom=tp_values, 
                    label='FP', color='#e74c3c')
        p3 = ax.bar(x, fn_values, width,
                    bottom=np.array(tp_values) + np.array(fp_values),
                    label='FN', color='#f39c12')
        
        # Customize subplot
        ax.set_title(project.capitalize(), fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=10)
        ax.grid(axis='y', alpha=0.3)
        
        # Add value labels on segments
        for i, (tp, fp, fn) in enumerate(zip(tp_values, fp_values, fn_values)):
            if tp > 0:
                ax.text(i, tp/2, str(tp), ha='center', va='center', 
                       fontweight='bold', color='white', fontsize=9)
            if fp > 0:
                ax.text(i, tp + fp/2, str(fp), ha='center', va='center', 
                       fontweight='bold', color='white', fontsize=9)
            if fn > 0:
                ax.text(i, tp + fp + fn/2, str(fn), ha='center', va='center', 
                       fontweight='bold', color='white', fontsize=9)
    
    # Add legend to the first subplot
    axes[0].legend(loc='upper left', fontsize=10)
    axes[0].set_ylabel('Count', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('project_level_comparison.png', dpi=300, bbox_inches='tight')
    print("Chart saved as 'project_level_comparison.png'")
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*70)
    print("PROJECT-LEVEL SUMMARY".center(70))
    print("="*70)
    for project in projects:
        print(f"\n{project.upper()}")
        print("-" * 70)
        cgpt = chatgpt_projects.get(project, {"tp": 0, "fp": 0, "fn": 0})
        gmn = gemini_projects.get(project, {"tp": 0, "fp": 0, "fn": 0})
        print(f"  ChatGPT: TP={cgpt['tp']}, FP={cgpt['fp']}, FN={cgpt['fn']}")
        print(f"  Gemini:  TP={gmn['tp']}, FP={gmn['fp']}, FN={gmn['fn']}")

if __name__ == "__main__":
    plot_project_stacked_bars()