import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Define the directory path
prompts_dir = r"c:\Users\pedro\Documents\MEI\1 Ano\2 Semestre\MEI\Assignment\MEI_Assignment\BugFinding\prompts"

def extract_source_files(prompt_content: str) -> Dict[str, str]:
    """Extract all source files from prompt content."""
    source_files = {}
    
    # Find the SOURCE FILES: section
    source_start = prompt_content.find("SOURCE FILES:")
    if source_start == -1:
        return source_files
    
    # Find where source files section ends (usually at FAILING TEST or TEST EXECUTION)
    test_start = prompt_content.find("FAILING TEST", source_start)
    if test_start == -1:
        test_start = prompt_content.find("TEST EXECUTION", source_start)
    if test_start == -1:
        test_end = len(prompt_content)
    else:
        test_end = test_start
    
    source_section = prompt_content[source_start:test_end]
    
    # Extract individual files using regex
    # Pattern: [file_N] path/to/file or [test_file] path/to/file
    file_pattern = r'\[(?:file|test_file)_\d+\]\s+([^\n]+)\n```(?:python)?\n(.*?)```'
    
    matches = re.finditer(file_pattern, source_section, re.DOTALL)
    for match in matches:
        file_path = match.group(1)
        file_content = match.group(2)
        source_files[file_path] = file_content
    
    return source_files

def count_lines_of_code(code: str) -> int:
    """Count lines of code (excluding empty lines and comments)."""
    lines = code.split('\n')
    loc = 0
    for line in lines:
        stripped = line.strip()
        # Count non-empty lines that are not just comments
        if stripped and not stripped.startswith('#'):
            loc += 1
    return loc

def calculate_cyclomatic_complexity(code: str) -> int:
    """
    Calculate cyclomatic complexity.
    Counts: if, elif, else, for, while, except, and, or, case statements
    Base complexity is 1.
    """
    complexity = 1
    
    # Count decision points
    keywords = [
        r'\bif\b',
        r'\belif\b',
        r'\belse\b(?=:)',  # else followed by colon
        r'\bfor\b',
        r'\bwhile\b',
        r'\bexcept\b',
        r'\band\b',
        r'\bor\b',
        r'\btry\b',
        r'\bwith\b',
        r'\blambda\b',
    ]
    
    for keyword_pattern in keywords:
        matches = re.findall(keyword_pattern, code)
        if keyword_pattern == r'\belse\b(?=:)':
            # Only count 'else' followed by colon to avoid matching variable names
            complexity += len(re.findall(r'else:', code))
        else:
            complexity += len(matches)
    
    return complexity

def process_prompts():
    """Process all prompt files and calculate metrics."""
    if not os.path.exists(prompts_dir):
        print(f"Error: Directory does not exist: {prompts_dir}")
        return
    
    files = sorted([f for f in os.listdir(prompts_dir) if f.startswith("prompt_") and f.endswith(".txt")])
    
    if not files:
        print("No prompt files found.")
        return
    
    # Store results
    results = []
    
    print(f"{'='*120}")
    print(f"{'Prompt File':<40} {'Source File':<50} {'LOC':<10} {'Complexity':<10}")
    print(f"{'='*120}")
    
    for filename in files:
        prompt_path = os.path.join(prompts_dir, filename)
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            source_files = extract_source_files(content)
            
            if not source_files:
                print(f"{filename:<40} {'[No source files found]':<50}")
                continue
            
            for file_path, file_content in source_files.items():
                loc = count_lines_of_code(file_content)
                complexity = calculate_cyclomatic_complexity(file_content)
                
                # Extract just the filename from the path for cleaner output
                short_name = Path(file_path).name
                
                print(f"{filename:<40} {short_name:<50} {loc:<10} {complexity:<10}")
                
                results.append({
                    'prompt_file': filename,
                    'source_file': file_path,
                    'loc': loc,
                    'complexity': complexity
                })
        
        except Exception as e:
            print(f"✗ Error processing {filename}: {str(e)}")
    
    print(f"{'='*120}")
    
    # Save to CSV
    try:
        import csv
        output_csv = os.path.join(prompts_dir, "metrics.csv")
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['prompt_file', 'source_file', 'loc', 'complexity'])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n✓ Metrics saved to: {output_csv}")
    except Exception as e:
        print(f"\n✗ Error saving CSV: {str(e)}")
    
    # Print summary statistics
    if results:
        total_files = len(results)
        avg_loc = sum(r['loc'] for r in results) / total_files
        avg_complexity = sum(r['complexity'] for r in results) / total_files
        
        print(f"\nSummary Statistics:")
        print(f"- Total source files analyzed: {total_files}")
        print(f"- Average LOC: {avg_loc:.1f}")
        print(f"- Average Cyclomatic Complexity: {avg_complexity:.1f}")
        print(f"- Total LOC: {sum(r['loc'] for r in results)}")
        print(f"- Total Complexity: {sum(r['complexity'] for r in results)}")

if __name__ == "__main__":
    process_prompts()