import json
import os
import csv
from pathlib import Path

# Define paths
chatgpt_dir = r"C:\Users\Luis Vaz\Documents\Universidade\MEI\2S\MEI\MEI_Assignment\CodeGeneration\ChatGPT_outputs"
gemini_dir = r"C:\Users\Luis Vaz\Documents\Universidade\MEI\2S\MEI\MEI_Assignment\CodeGeneration\Gemini_outputs"
output_csv = r"C:\Users\Luis Vaz\Documents\Universidade\MEI\2S\MEI\MEI_Assignment\CodeGeneration\results_organized.csv"

# Collect data from both models
all_results = []

def process_results(directory, model_name):
    """Process all _results.json files in a directory"""
    results = []
    
    # Find all result files
    json_files = sorted([f for f in os.listdir(directory) if f.endswith('_results.json')])
    
    for json_file in json_files:
        file_path = os.path.join(directory, json_file)
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract output number from filename
            output_num = json_file.replace('_results.json', '').replace('ChatGPT_output', '').replace('Gemini_output', '')
            
            row = {
                'Model': model_name,
                'Output_Number': output_num,
                'Avg_Complexity': data.get('complexity', {}).get('avg_complexity', ''),
                'Maintainability_Index': data.get('complexity', {}).get('maintainability_index', ''),
                'Lines_of_Code': data.get('complexity', {}).get('lines_of_code', ''),
                'Success': data.get('functional', {}).get('success', ''),
                'Latency': data.get('functional', {}).get('latency', ''),
                'Execution_Time': data.get('execution_time', '')
            }
            results.append(row)
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    return results

# Process both models
print("Processing ChatGPT outputs...")
chatgpt_results = process_results(chatgpt_dir, "ChatGPT")

print("Processing Gemini outputs...")
gemini_results = process_results(gemini_dir, "Gemini")

# Combine results
all_results = chatgpt_results + gemini_results

# Write to CSV
if all_results:
    print(f"Writing {len(all_results)} results to CSV...")
    
    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['Model', 'Output_Number', 'Avg_Complexity', 'Maintainability_Index', 
                      'Lines_of_Code', 'Success', 'Latency', 'Execution_Time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(all_results)
    
    print(f"CSV file created successfully: {output_csv}")
    print(f"Total rows: {len(all_results)} (ChatGPT: {len(chatgpt_results)}, Gemini: {len(gemini_results)})")
else:
    print("No results found!")
