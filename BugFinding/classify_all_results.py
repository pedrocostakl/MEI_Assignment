import json
import argparse
import re
from pathlib import Path
'''
    python classify_all_results.py ChatGPT_results/all_results.json ChatGPT_results/classified_results.json
'''
def natural_sort_key(case):
    """Convert case_name to sort naturally (e.g., fastapi_1, fastapi_2, ..., fastapi_10)"""
    name = case.get("case_name", "")
    # Split into alternating non-numeric and numeric parts
    parts = re.split(r'(\d+)', name)
    # Convert numeric parts to integers, keep others as strings
    return [int(part) if part.isdigit() else part for part in parts]


def classify_cases(all_results_path):
    all_results_path = Path(all_results_path)

    cases = json.loads(
        all_results_path.read_text(encoding="utf-8")
    )

    cases = sorted(cases, key=natural_sort_key)
    
    classified_cases = []

    total_cases = 0
    true_cases = 0
    false_cases = 0

    for case in cases:
        num_real_bugs = case.get("num_real_bugs", 0)
        true_positives = case.get("true_positives", 0)

        classification = 1 if num_real_bugs == true_positives else 0

        classified_case = {
            **case,
            "classification": classification
        }

        classified_cases.append(classified_case)

        total_cases += 1
        if classification == 1:
            true_cases += 1
        else:
            false_cases += 1

    summary = {
        "total_cases": total_cases,
        "true_cases": true_cases,
        "false_cases": false_cases,
        "accuracy": true_cases / total_cases if total_cases > 0 else 0,
    }

    return {
        "summary": summary,
        "cases": classified_cases
    }


def main():
    parser = argparse.ArgumentParser(
        description="Classify cases as 1 if all real bugs were detected, otherwise 0."
    )

    parser.add_argument(
        "all_results_json",
        help="Path to all_results.json."
    )

    parser.add_argument(
        "output_json",
        help="Path where the classified JSON should be saved."
    )

    args = parser.parse_args()

    result = classify_cases(args.all_results_json)

    Path(args.output_json).write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(result["summary"], indent=2))
    print(f"Saved classified results to: {args.output_json}")


if __name__ == "__main__":
    main()