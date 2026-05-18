import json
import argparse
import re
from pathlib import Path

'''
    python compare_bug_locations_folder.py ChatGPT_outputs benchmarks ChatGPT_results
    python compare_bug_locations_folder.py Gemini_outputs benchmarks Gemini_results
'''

IGNORED_CASES = {
}

def intervals_overlap(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end


def load_locations(path):
    path = Path(path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

    return data.get("bug_locations", [])


def normalize_case_name(path):
    """
    Converts names like:
      ChatGPT_output_fastapi_1.json -> fastapi_1
      Claude_output_fastapi_1.json  -> fastapi_1
      fastapi_bug_1.json            -> fastapi_1
    """

    name = Path(path).stem

    name = re.sub(r"^(ChatGPT|Gemini|GPT|LLM)_output_", "", name)
    name = re.sub(r"_output_", "_", name)
    name = re.sub(r"_bug_", "_", name)
    name = re.sub(r"_result_", "_", name)

    return name


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


def compare_folders(outputs_dir, benchmarks_dir, results_dir):
    outputs_dir = Path(outputs_dir)
    benchmarks_dir = Path(benchmarks_dir)
    results_dir = Path(results_dir)

    results_dir.mkdir(parents=True, exist_ok=True)

    output_files = list(outputs_dir.glob("*.json"))
    benchmark_files = list(benchmarks_dir.glob("*.json"))

    benchmark_map = {
        normalize_case_name(path): path
        for path in benchmark_files
    }

    summary = {
        "cases": [],
        "totals": {
            "num_cases": 0,
            "num_real_bugs": 0,
            "num_reported_bugs": 0,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
        },
        "missing_benchmarks": [],
        "invalid_outputs": [],
    }

    for output_file in output_files:
        case_name = normalize_case_name(output_file)

        if case_name in IGNORED_CASES:
            continue

        benchmark_file = benchmark_map.get(case_name)

        if benchmark_file is None:
            summary["missing_benchmarks"].append(str(output_file))
            continue

        try:
            metrics = compare_locations(output_file, benchmark_file)
        except ValueError as e:
            summary["invalid_outputs"].append({
                "output_file": str(output_file),
                "error": str(e)
            })
            continue

        case_result = {
            "case_name": case_name,
            "output_file": str(output_file),
            "benchmark_file": str(benchmark_file),
            **metrics,
        }

        # Individual case file
        result_path = results_dir / f"result_{case_name}.json"
        result_path.write_text(
            json.dumps(case_result, indent=2),
            encoding="utf-8"
        )

        # Combined case list
        summary["cases"].append(case_result)

        # Totals
        summary["totals"]["num_cases"] += 1
        summary["totals"]["num_real_bugs"] += metrics["num_real_bugs"]
        summary["totals"]["num_reported_bugs"] += metrics["num_reported_bugs"]
        summary["totals"]["true_positives"] += metrics["true_positives"]
        summary["totals"]["false_positives"] += metrics["false_positives"]
        summary["totals"]["false_negatives"] += metrics["false_negatives"]

    # Summary with totals + cases
    summary_path = results_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    # Case-by-case only file
    all_results_path = results_dir / "all_results.json"
    all_results_path.write_text(
        json.dumps(summary["cases"], indent=2),
        encoding="utf-8"
    )

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Compare a folder of LLM outputs against benchmark bug locations."
    )

    parser.add_argument(
        "outputs_dir",
        help="Folder containing LLM output JSON files."
    )

    parser.add_argument(
        "benchmarks_dir",
        help="Folder containing benchmark bug_locations JSON files."
    )

    parser.add_argument(
        "results_dir",
        help="Folder where result JSON files will be saved."
    )

    args = parser.parse_args()

    summary = compare_folders(
        outputs_dir=args.outputs_dir,
        benchmarks_dir=args.benchmarks_dir,
        results_dir=args.results_dir,
    )

    print(json.dumps(summary["totals"], indent=2))
    print(f"Saved case results and summary to: {args.results_dir}")


if __name__ == "__main__":
    main()