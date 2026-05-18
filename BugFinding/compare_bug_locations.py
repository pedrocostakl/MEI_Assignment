import json
import argparse
from pathlib import Path

"""
Example usage: 
    python compare_bug_locations.py ChatGPT_outputs/ChatGPT_output_fastapi_1.json benchmarks/fastapi_bug_1.json --out ChatGPT_outputs/ChatGPT_result_fastapi_1.json
"""

def intervals_overlap(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end


def load_locations(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get("bug_locations", [])


def compare_locations(output_path, ground_truth_path):
    reported = load_locations(output_path)
    real = load_locations(ground_truth_path)

    matched_real_indices = set()
    matched_reported_indices = set()

    for reported_idx, reported_bug in enumerate(reported):
        for real_idx, real_bug in enumerate(real):
            if real_idx in matched_real_indices:
                continue

            same_file = reported_bug["file_path"] == real_bug["file_path"]

            overlap = intervals_overlap(
                reported_bug["line_start"],
                reported_bug["line_end"],
                real_bug["line_start"],
                real_bug["line_end"],
            )

            if same_file and overlap:
                matched_reported_indices.add(reported_idx)
                matched_real_indices.add(real_idx)
                break

    num_real_bugs = len(real)
    num_reported_bugs = len(reported)

    true_positives = len(matched_reported_indices)
    false_positives = num_reported_bugs - true_positives
    false_negatives = num_real_bugs - len(matched_real_indices)

    return {
        "num_real_bugs": num_real_bugs,
        "num_reported_bugs": num_reported_bugs,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compare LLM bug locations against ground-truth bug locations."
    )

    parser.add_argument(
        "output_json",
        help="Path to the LLM output JSON file."
    )

    parser.add_argument(
        "bug_locations_json",
        help="Path to the ground-truth bug_locations JSON file."
    )

    parser.add_argument(
        "--out",
        help="Optional path to save the metrics JSON."
    )

    args = parser.parse_args()

    results = compare_locations(
        output_path=args.output_json,
        ground_truth_path=args.bug_locations_json,
    )

    print(json.dumps(results, indent=2))

    if args.out:
        Path(args.out).write_text(
            json.dumps(results, indent=2),
            encoding="utf-8"
        )


if __name__ == "__main__":
    main()