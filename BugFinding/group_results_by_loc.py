import json
import numpy as np
from pathlib import Path
import re

def parse_loc_levels():
    """Parse LOC_levels.txt and create a mapping of test cases to LOC levels"""
    loc_mapping = {}
    loc_file = Path(__file__).parent / 'LOC_levels.txt'
    
    if not loc_file.exists():
        print(f"Error: LOC_levels.txt not found at {loc_file}")
        return loc_mapping
    
    with open(loc_file, 'r') as f:
        content = f.read()
    
    # Extract file names and LOC values
    pattern = r'`(prompt_[a-z_]+_\d+\.txt)`\s*\|\s*(\d+)'
    matches = re.findall(pattern, content)
    
    for filename, loc in matches:
        # Extract case name from filename (e.g., "fastapi_1" from "prompt_fastapi_bug_1.txt")
        case_match = re.search(r'prompt_([a-z]+)_bug_(\d+)\.txt', filename)
        if case_match:
            framework = case_match.group(1)
            bug_num = case_match.group(2)
            case_name = f"{framework}_{bug_num}"
            loc_mapping[case_name] = {
                'loc': int(loc),
                'level': get_loc_level(int(loc))
            }
    
    return loc_mapping

def get_loc_level(loc):
    """Determine LOC level based on lines of code"""
    if loc <= 330:
        return 'Low'
    elif loc <= 980:
        return 'Medium'
    else:
        return 'High'

def calculate_metrics(case):
    """Calculate Precision, Recall, and F1-score for a single case"""
    tp = case.get('true_positives', 0)
    fp = case.get('false_positives', 0)
    fn = case.get('false_negatives', 0)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1
    }

def group_by_loc_level(summary_file_path, loc_mapping):
    """Group test cases by LOC level and calculate metrics"""
    with open(summary_file_path, 'r') as f:
        data = json.load(f)
    
    # Initialize groups
    groups = {
        'Low': {'cases': [], 'precisions': [], 'recalls': [], 'f1s': []},
        'Medium': {'cases': [], 'precisions': [], 'recalls': [], 'f1s': []},
        'High': {'cases': [], 'precisions': [], 'recalls': [], 'f1s': []}
    }
    
    for case in data.get('cases', []):
        case_name = case['case_name']
        
        if case_name not in loc_mapping:
            print(f"Warning: {case_name} not found in LOC mapping")
            continue
        
        metrics = calculate_metrics(case)
        loc_level = loc_mapping[case_name]['level']
        loc_value = loc_mapping[case_name]['loc']
        
        groups[loc_level]['cases'].append({
            'name': case_name,
            'loc': loc_value,
            'metrics': metrics
        })
        groups[loc_level]['precisions'].append(metrics['precision'])
        groups[loc_level]['recalls'].append(metrics['recall'])
        groups[loc_level]['f1s'].append(metrics['f1'])
    
    return groups

def print_results(model_name, groups):
    """Print results for a model grouped by LOC level"""
    print(f"\n{'=' * 80}")
    print(f"{model_name} Results by LOC Level")
    print(f"{'=' * 80}")
    
    for level in ['Low', 'Medium', 'High']:
        group = groups[level]
        num_cases = len(group['cases'])
        
        if num_cases == 0:
            continue
        
        print(f"\n{level} LOC Level ({num_cases} cases):")
        print("-" * 80)
        
        # Calculate statistics
        precisions = np.array(group['precisions'])
        recalls = np.array(group['recalls'])
        f1s = np.array(group['f1s'])
        
        print(f"\nPrecision:")
        print(f"  Mean:    {np.mean(precisions):.4f}")
        print(f"  Std Dev: {np.std(precisions):.4f}")
        print(f"  Min:     {np.min(precisions):.4f}")
        print(f"  Max:     {np.max(precisions):.4f}")
        
        print(f"\nRecall:")
        print(f"  Mean:    {np.mean(recalls):.4f}")
        print(f"  Std Dev: {np.std(recalls):.4f}")
        print(f"  Min:     {np.min(recalls):.4f}")
        print(f"  Max:     {np.max(recalls):.4f}")
        
        print(f"\nF1-Score:")
        print(f"  Mean:    {np.mean(f1s):.4f}")
        print(f"  Std Dev: {np.std(f1s):.4f}")
        print(f"  Min:     {np.min(f1s):.4f}")
        print(f"  Max:     {np.max(f1s):.4f}")
        
        # List individual cases
        print(f"\nCases in this group:")
        for case in group['cases']:
            print(f"  {case['name']:20s} ({case['loc']:4d} LOC) - "
                  f"P: {case['metrics']['precision']:.4f}, "
                  f"R: {case['metrics']['recall']:.4f}, "
                  f"F1: {case['metrics']['f1']:.4f}")

def print_comparison(chatgpt_groups, gemini_groups):
    """Print comparison between ChatGPT and Gemini by LOC level"""
    print(f"\n{'=' * 80}")
    print("Comparison: ChatGPT vs Gemini by LOC Level")
    print(f"{'=' * 80}")
    
    for level in ['Low', 'Medium', 'High']:
        cgpt_group = chatgpt_groups[level]
        gemi_group = gemini_groups[level]
        
        if len(cgpt_group['cases']) == 0 or len(gemi_group['cases']) == 0:
            continue
        
        cgpt_f1 = np.mean(cgpt_group['f1s'])
        gemi_f1 = np.mean(gemi_group['f1s'])
        
        print(f"\n{level} LOC Level:")
        print("-" * 80)
        print(f"ChatGPT - Precision: {np.mean(cgpt_group['precisions']):.4f} ± {np.std(cgpt_group['precisions']):.4f}")
        print(f"Gemini  - Precision: {np.mean(gemi_group['precisions']):.4f} ± {np.std(gemi_group['precisions']):.4f}")
        print(f"ChatGPT - Recall:    {np.mean(cgpt_group['recalls']):.4f} ± {np.std(cgpt_group['recalls']):.4f}")
        print(f"Gemini  - Recall:    {np.mean(gemi_group['recalls']):.4f} ± {np.std(gemi_group['recalls']):.4f}")
        print(f"ChatGPT - F1-Score:  {cgpt_f1:.4f} ± {np.std(cgpt_group['f1s']):.4f}")
        print(f"Gemini  - F1-Score:  {gemi_f1:.4f} ± {np.std(gemi_group['f1s']):.4f}")
        print(f"F1 Difference (ChatGPT - Gemini): {cgpt_f1 - gemi_f1:.4f}")

def main():
    base_path = Path(__file__).parent
    
    chatgpt_summary = base_path / 'ChatGPT_results' / 'summary.json'
    gemini_summary = base_path / 'Gemini_results' / 'summary.json'
    
    # Parse LOC levels
    print("Parsing LOC levels...")
    loc_mapping = parse_loc_levels()
    
    if not loc_mapping:
        print("Error: Could not parse LOC levels")
        return
    
    print(f"Successfully parsed LOC information for {len(loc_mapping)} test cases")
    
    # Process ChatGPT results
    if chatgpt_summary.exists():
        print(f"\nProcessing ChatGPT results from {chatgpt_summary}...")
        chatgpt_groups = group_by_loc_level(chatgpt_summary, loc_mapping)
        print_results("ChatGPT", chatgpt_groups)
    else:
        print(f"Error: ChatGPT summary file not found at {chatgpt_summary}")
        return
    
    # Process Gemini results
    if gemini_summary.exists():
        print(f"\nProcessing Gemini results from {gemini_summary}...")
        gemini_groups = group_by_loc_level(gemini_summary, loc_mapping)
        print_results("Gemini", gemini_groups)
    else:
        print(f"Error: Gemini summary file not found at {gemini_summary}")
        return
    
    # Print comparison
    print_comparison(chatgpt_groups, gemini_groups)
    
    print(f"\n{'=' * 80}")

if __name__ == "__main__":
    main()