import re
import json
import argparse
from pathlib import Path

"""
Example usage:
    python extract_bug_locations.py bug_patch.txt BugsInPy/workspace/fastapi bug_locations.json
    python extract_bug_locations.py Bugs/fastapi/bugs/1/bug_patch.txt BugsInPy/workspace/fastapi fastapi_bug_1.json
    python extract_bug_locations.py Bugs/httpie/bugs/1/bug_patch.txt BugsInPy/workspace/httpie httpie_bug_1.json
    python extract_bug_locations.py Bugs/sanic/bugs/1/bug_patch.txt BugsInPy/workspace/sanic sanic_bug_1.json
    python extract_bug_locations.py Bugs/tornado/bugs/1/bug_patch.txt BugsInPy/workspace/tornado tornado_bug_1.json
"""

def extract_bug_locations(
    patch_path: str,
    repo_prefix: str
) -> dict:
    """
    Extract bug locations from a unified git diff patch file.

    Uses the OLD file hunk intervals (-start,count),
    since those correspond to the buggy version.
    """

    patch_text = Path(patch_path).read_text(
        encoding="utf-8",
        errors="replace"
    )

    bug_locations = []
    current_file = None

    file_pattern = re.compile(
        r"^diff --git a/(.*?) b/(.*?)$"
    )

    hunk_pattern = re.compile(
        r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@"
    )

    for line in patch_text.splitlines():

        # Detect file changes
        file_match = file_pattern.match(line)
        if file_match:
            current_file = file_match.group(1)
            continue

        # Detect hunks
        hunk_match = hunk_pattern.match(line)
        if hunk_match and current_file:

            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2) or 1)

            # Handle insertion-only hunks
            if old_count == 0:
                line_start = old_start
                line_end = old_start
            else:
                line_start = old_start
                line_end = old_start + old_count - 1

            bug_locations.append({
                "file_path": f"{repo_prefix}/{current_file}",
                "line_start": line_start,
                "line_end": line_end
            })

    return {
        "bug_locations": bug_locations
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract bug line intervals from a git patch."
    )

    parser.add_argument(
        "patch_file",
        help="Path to bug_patch.txt"
    )

    parser.add_argument(
        "repo_prefix",
        help="Repository prefix to prepend to file paths"
    )

    parser.add_argument(
        "output_file",
        help="Output JSON filename"
    )

    args = parser.parse_args()

    result = extract_bug_locations(
        patch_path=args.patch_file,
        repo_prefix=args.repo_prefix
    )

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"Saved output to: {args.output_file}")


if __name__ == "__main__":
    main()