import json
import argparse
from pathlib import Path
'''
    python filter_single_bug_cases.py ChatGPT_results/classified_results.json ChatGPT_results/single_bug_results.json
'''

def filter_single_bug_cases(classified_results_path):
    classified_results_path = Path(classified_results_path)

    data = json.loads(
        classified_results_path.read_text(encoding="utf-8")
    )

    cases = data.get("cases", [])

    single_bug_cases = [
        case for case in cases
        if case.get("num_real_bugs") == 1
    ]

    total_cases = len(single_bug_cases)
    true_cases = sum(
        1 for case in single_bug_cases
        if case.get("classification") == 1
    )
    false_cases = total_cases - true_cases

    accuracy = true_cases / total_cases if total_cases > 0 else 0

    return {
        "summary": {
            "total_single_bug_cases": total_cases,
            "true_cases": true_cases,
            "false_cases": false_cases,
            "accuracy": accuracy
        },
        "cases": single_bug_cases
    }


def main():
    parser = argparse.ArgumentParser(
        description="Filter classified results to cases with exactly one real bug and compute accuracy."
    )

    parser.add_argument(
        "classified_results_json",
        help="Path to classified_results.json."
    )

    parser.add_argument(
        "output_json",
        help="Path where the filtered results should be saved."
    )

    args = parser.parse_args()

    result = filter_single_bug_cases(args.classified_results_json)

    Path(args.output_json).write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print(json.dumps(result["summary"], indent=2))
    print(f"Saved single-bug case results to: {args.output_json}")


if __name__ == "__main__":
    main()