from pathlib import Path
import argparse
# Example:
# For Bug 2, 
# python generate_llm_prompt.py --source fastapi/routing.py --tests tests/test_ws_router.py --failure-output failure.txt --out prompt_fastapi_bug_2.txt
# python generate_llm_prompt.py --source BugsInPy/workspace/fastapi/fastapi/applications.py  --tests BugsInPy/workspace/fastapi/tests/test_ws_router.py --out prompt_fastapi_bug_2.txt
def numbered_file(path: Path) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    width = len(str(len(lines)))

    numbered = []
    for i, line in enumerate(lines, start=1):
        numbered.append(f"{str(i).rjust(width)} | {line}")

    return "\n".join(numbered)


def build_prompt(source_files, test_files, failure_output=None):
    prompt = []

    prompt.append("""
You are given buggy source files, failing test files, and test execution output.

Your task is BUG LOCALIZATION ONLY.

Identify the source-code location(s) most likely responsible for the failing test.

Return only valid JSON using this exact format:

{
  "bug_locations": [
    {
      "file_id": "file_1",
      "file_path": "relative/path.py",
      "line_start": 1,
      "line_end": 1,
      "confidence": "low|medium|high",
      "reason": "Max 2 sentences."
    }
  ]
}

Rules:
- Do not propose fixes.
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
""".strip())

    prompt.append("\n\nSOURCE FILES:")

    file_counter = 1

    for path in source_files:
        path = Path(path)
        prompt.append(f"\n[file_{file_counter}] {path.as_posix()}")
        prompt.append("```python")
        prompt.append(numbered_file(path))
        prompt.append("```")
        file_counter += 1

    prompt.append("\n\nFAILING TEST FILES:")
    
    test_file_counter = 1

    for path in test_files:
        path = Path(path)
        prompt.append(f"\n[test_file_{test_file_counter}] {path.as_posix()}")
        prompt.append("```python")
        prompt.append(numbered_file(path))
        prompt.append("```")
        test_file_counter +=1

    if failure_output:
        failure_path = Path(failure_output)
        prompt.append("\n\nTEST EXECUTION OUTPUT:")
        prompt.append("```text")
        prompt.append(failure_path.read_text(encoding="utf-8", errors="replace"))
        prompt.append("```")

    return "\n".join(prompt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", nargs="+", required=True)
    parser.add_argument("--tests", nargs="+", required=True)
    parser.add_argument("--failure-output")
    parser.add_argument("--out", default="llm_prompt.txt")

    args = parser.parse_args()

    prompt = build_prompt(
        source_files=args.source,
        test_files=args.tests,
        failure_output=args.failure_output
    )

    Path(args.out).write_text(prompt, encoding="utf-8")
    print(f"Prompt written to {args.out}")


if __name__ == "__main__":
    main()