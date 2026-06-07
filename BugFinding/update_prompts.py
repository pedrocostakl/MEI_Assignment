import os
import re

# Define the directory path
prompts_dir = r"c:\Users\pedro\Documents\MEI\1 Ano\2 Semestre\MEI\Assignment\MEI_Assignment\BugFinding\prompts"

# Old task description section
old_task = """You are given buggy source files, failing test files, and failing test output.

Your task is BUG LOCALIZATION ONLY.

Identify the source-code location(s) most likely responsible for the failing test.

Return only valid JSON using this exact format:"""

# New task description section
new_task = """You are given buggy source files, failing test files, and test execution output.

Your task is BUG LOCALIZATION ONLY.

Identify the source-code location(s) most likely responsible for the failing test.

Return only valid JSON using this exact format:"""

# Old rules section
old_rules = """- Do not propose fixes.
- Do not rewrite code.
- Do not explain anything outside the JSON.
- Line numbers must refer to the numbered buggy source files, not the test files.
- Each entry should identify the likely origin of a bug, not every line affected by it.
- Prefer the smallest line range that is sufficient to identify the bug.
- Report only locations directly supported by the source code, failing test, and failing test output.
- There can be multiple bugs present.
- If no source-code location can be identified with reasonable confidence, return:
{
  "bug_locations": []
}"""

# New rules section
new_rules = """- Do not propose fixes.
- Do not rewrite code.
- Do not explain anything outside the JSON.
- Line numbers must refer to the numbered buggy source files, not the test files.

- A scenario may contain one or more bug locations.
- Do not stop after identifying the first likely bug location.
- After finding the most likely location, continue inspecting the buggy source files for additional independent locations that may also be responsible for the failing behaviour.

- Each entry should identify one source-code location that likely needs to be changed to fix the failure.
- Include separate entries for separate suspicious source-code regions, even if they contribute to the same failing test.
- Do not include duplicate locations, call sites, stack-trace propagation lines, or lines that are only affected by the bug.

- Prefer the smallest line range that is sufficient to identify each suspected bug location.
- Report locations supported by the source code and at least one of the following: failing test logic, failing output, traceback, assertion difference, or data flow from the failing behaviour.
- Medium-confidence locations are acceptable when the evidence suggests they may be part of the bug.
- Low-confidence locations should only be included when they are directly relevant to the failing behaviour.

- If no source-code location can be identified with reasonable confidence, return:
{
  "bug_locations": []
}
"""

def update_prompts():
    """Update all prompt files with new task and rules sections."""
    if not os.path.exists(prompts_dir):
        print(f"Error: Directory does not exist: {prompts_dir}")
        return
    
    files = [f for f in os.listdir(prompts_dir) if f.startswith("prompt_") and f.endswith(".txt")]
    
    if not files:
        print("No prompt files found.")
        return
    
    updated_count = 0
    task_updated = 0
    rules_updated = 0
    
    for filename in files:
        filepath = os.path.join(prompts_dir, filename)
        
        try:
            # Read the file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace task description (if old version exists)
            if old_task in content:
                content = content.replace(old_task, new_task)
                task_updated += 1
            
            # Replace rules section (if old version exists)
            if old_rules in content:
                content = content.replace(old_rules, new_rules)
                rules_updated += 1
            
            # Write back if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                updated_count += 1
                print(f"✓ Updated: {filename}")
            else:
                print(f"- No changes needed: {filename}")
        
        except Exception as e:
            print(f"✗ Error processing {filename}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"- Total files processed: {len(files)}")
    print(f"- Files updated: {updated_count}")
    print(f"- Task descriptions updated: {task_updated}")
    print(f"- Rules sections updated: {rules_updated}")
    print(f"{'='*60}")

if __name__ == "__main__":
    update_prompts()