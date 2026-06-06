import os
import re

# Define the base directory
base_dir = r"c:\Users\pedro\Documents\MEI\1 Ano\2 Semestre\MEI\Assignment\MEI_Assignment\BugFinding"
prompts_dir = os.path.join(base_dir, "prompts")
bugs_dir = os.path.join(base_dir, "Bugs")

def extract_failing_test_output(bug_buggy_path):
    """Extract the FAILURES section from bug_buggy.txt file."""
    try:
        with open(bug_buggy_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the start of FAILURES section
        failures_start = content.find("=================================== FAILURES ===================================")
        if failures_start == -1:
            return None
        
        # Find the end of FAILURES section (warnings summary)
        warnings_start = content.find("=============================== warnings summary ===============================", failures_start)
        if warnings_start == -1:
            # If warnings not found, look for short test summary
            short_summary_start = content.find("=========================== short test summary info ============================", failures_start)
            if short_summary_start == -1:
                # If neither found, take from FAILURES to end
                failing_output = content[failures_start:].rstrip()
            else:
                failing_output = content[failures_start:short_summary_start].rstrip()
        else:
            failing_output = content[failures_start:warnings_start].rstrip()
        
        return failing_output
    except Exception as e:
        print(f"Error reading {bug_buggy_path}: {str(e)}")
        return None

def parse_prompt_filename(filename):
    """Parse prompt filename to extract project and bug number.
    Example: prompt_fastapi_bug_4.txt -> ('fastapi', '4')
    """
    match = re.match(r"prompt_(\w+)_bug_(\d+)\.txt", filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def add_failing_test_output():
    """Add TEST EXECUTION OUTPUT: section to all prompt files."""
    if not os.path.exists(prompts_dir):
        print(f"Error: Prompts directory does not exist: {prompts_dir}")
        return
    
    if not os.path.exists(bugs_dir):
        print(f"Error: Bugs directory does not exist: {bugs_dir}")
        return
    
    files = sorted([f for f in os.listdir(prompts_dir) if f.startswith("prompt_") and f.endswith(".txt")])
    
    if not files:
        print("No prompt files found.")
        return
    
    updated_count = 0
    skipped_count = 0
    error_count = 0
    
    for filename in files:
        prompt_path = os.path.join(prompts_dir, filename)
        project, bug_num = parse_prompt_filename(filename)
        
        if not project or not bug_num:
            print(f"- Skipped: {filename} (could not parse filename)")
            skipped_count += 1
            continue
        
        # Construct the bug_buggy.txt path
        bug_buggy_path = os.path.join(bugs_dir, project, "bugs", bug_num, "bug_buggy.txt")
        
        if not os.path.exists(bug_buggy_path):
            print(f"✗ Skipped: {filename} (bug file not found at {bug_buggy_path})")
            skipped_count += 1
            continue
        
        try:
            # Extract failing test output
            failing_output = extract_failing_test_output(bug_buggy_path)
            
            if failing_output is None:
                print(f"- Skipped: {filename} (no FAILURES section found)")
                skipped_count += 1
                continue
            
            # Read the prompt file
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            
            # Check if TEST EXECUTION OUTPUT: or FAILING TEST OUTPUT already exists
            test_exec_index = prompt_content.find("TEST EXECUTION OUTPUT:")
            failing_test_index = prompt_content.find("FAILING TEST  OUTPUT")
            
            # Determine where to truncate
            truncate_index = -1
            if test_exec_index != -1:
                truncate_index = test_exec_index
                print(f"✓ Replacing: {filename} (found TEST EXECUTION OUTPUT:)")
            elif failing_test_index != -1:
                truncate_index = failing_test_index
                print(f"✓ Replacing: {filename} (found FAILING TEST OUTPUT)")
            else:
                print(f"✓ Updated: {filename}")
            
            # If existing output found, truncate at that point
            if truncate_index != -1:
                prompt_content = prompt_content[:truncate_index].rstrip()
            
            # Append the new TEST EXECUTION OUTPUT section
            updated_content = prompt_content + "\n\nTEST EXECUTION OUTPUT:\n\n" + failing_output + "\n"
            
            # Write back to the prompt file
            with open(prompt_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            updated_count += 1
        
        except Exception as e:
            error_count += 1
            print(f"✗ Error processing {filename}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"- Total files processed: {len(files)}")
    print(f"- Files updated: {updated_count}")
    print(f"- Files skipped: {skipped_count}")
    print(f"- Errors: {error_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    add_failing_test_output()