import json
import argparse
import random
from pathlib import Path
from statistics import mean

'''
    python paired_bootstrap_llm.py ./ChatGPT_results ./Gemini_results bootstrap_results.json
'''

def load_cases(results_dir):
    """
    Loads all_results.json from a results folder.

    Expected format:
    [
      {
        "case_name": "fastapi_2",
        "num_real_bugs": 1,
        "num_reported_bugs": 2,
        "true_positives": 1,
        "false_positives": 1,
        "false_negatives": 0
      }
    ]
    """

    results_dir = Path(results_dir)
    all_results_path = results_dir / "all_results.json"

    if not all_results_path.exists():
        raise FileNotFoundError(f"Could not find {all_results_path}")

    data = json.loads(all_results_path.read_text(encoding="utf-8"))

    # Supports either:
    # 1. all_results.json = [...]
    # 2. all_results.json = {"cases": [...]}
    if isinstance(data, dict):
        cases = data.get("cases", [])
    else:
        cases = data

    case_map = {}

    for case in cases:
        case_name = case["case_name"]
        case_map[case_name] = case

    return case_map


def aggregate_metrics(cases):
    """
    Calculates micro-averaged recall and F1 over a list of cases.
    """

    tp = sum(case.get("true_positives", 0) for case in cases)
    fp = sum(case.get("false_positives", 0) for case in cases)
    fn = sum(case.get("false_negatives", 0) for case in cases)
    real = sum(case.get("num_real_bugs", 0) for case in cases)
    reported = sum(case.get("num_reported_bugs", 0) for case in cases)

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (2 * tp) / ((2 * tp) + fp + fn) if ((2 * tp) + fp + fn) > 0 else 0.0

    return {
        "num_cases": len(cases),
        "num_real_bugs": real,
        "num_reported_bugs": reported,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def percentile(values, p):
    """
    Calculates percentile without requiring numpy.
    """

    if not values:
        return None

    values = sorted(values)
    k = (len(values) - 1) * p
    lower = int(k)
    upper = min(lower + 1, len(values) - 1)
    weight = k - lower

    return values[lower] * (1 - weight) + values[upper] * weight


def paired_bootstrap(
    model_a_cases,
    model_b_cases,
    n_bootstrap=10000,
    seed=42
):
    """
    Performs paired scenario-level bootstrap.

    Each bootstrap sample resamples case names with replacement.
    For each sampled case, both Model A and Model B results are included.
    """

    rng = random.Random(seed)

    model_a_map = load_cases(model_a_cases)
    model_b_map = load_cases(model_b_cases)

    common_case_names = sorted(set(model_a_map.keys()) & set(model_b_map.keys()))

    if not common_case_names:
        raise ValueError("No matching case_name values found between the two folders.")

    missing_from_a = sorted(set(model_b_map.keys()) - set(model_a_map.keys()))
    missing_from_b = sorted(set(model_a_map.keys()) - set(model_b_map.keys()))

    if missing_from_a or missing_from_b:
        raise ValueError(
            f"Case mismatch.\n"
            f"Missing from model A: {missing_from_a}\n"
            f"Missing from model B: {missing_from_b}"
        )
    
    observed_a_cases = [model_a_map[name] for name in common_case_names]
    observed_b_cases = [model_b_map[name] for name in common_case_names]

    observed_a = aggregate_metrics(observed_a_cases)
    observed_b = aggregate_metrics(observed_b_cases)

    observed_diff = {
        "recall_diff": observed_a["recall"] - observed_b["recall"],
        "f1_diff": observed_a["f1"] - observed_b["f1"],
    }

    recall_diffs = []
    f1_diffs = []

    recall_a_values = []
    recall_b_values = []
    f1_a_values = []
    f1_b_values = []

    n_cases = len(common_case_names)

    for _ in range(n_bootstrap):
        sampled_names = [
            rng.choice(common_case_names)
            for _ in range(n_cases)
        ]

        sample_a = [model_a_map[name] for name in sampled_names]
        sample_b = [model_b_map[name] for name in sampled_names]

        metrics_a = aggregate_metrics(sample_a)
        metrics_b = aggregate_metrics(sample_b)

        recall_a = metrics_a["recall"]
        recall_b = metrics_b["recall"]
        f1_a = metrics_a["f1"]
        f1_b = metrics_b["f1"]

        recall_a_values.append(recall_a)
        recall_b_values.append(recall_b)
        f1_a_values.append(f1_a)
        f1_b_values.append(f1_b)

        recall_diffs.append(recall_a - recall_b)
        f1_diffs.append(f1_a - f1_b)

    result = {
        "bootstrap_settings": {
            "n_bootstrap": n_bootstrap,
            "seed": seed,
            "paired_unit": "case_name",
            "statistic_type": "micro_averaged_over_resampled_cases",
        },
        "matched_cases": {
            "num_common_cases": len(common_case_names),
            "case_names": common_case_names,
            "missing_from_model_a": missing_from_a,
            "missing_from_model_b": missing_from_b,
        },
        "observed": {
            "model_a": observed_a,
            "model_b": observed_b,
            "difference_model_a_minus_model_b": observed_diff,
        },
        "bootstrap": {
            "recall": {
                "model_a_mean": mean(recall_a_values),
                "model_b_mean": mean(recall_b_values),
                "diff_mean": mean(recall_diffs),
                "diff_ci_95": {
                    "lower": percentile(recall_diffs, 0.025),
                    "upper": percentile(recall_diffs, 0.975),
                },
            },
            "f1": {
                "model_a_mean": mean(f1_a_values),
                "model_b_mean": mean(f1_b_values),
                "diff_mean": mean(f1_diffs),
                "diff_ci_95": {
                    "lower": percentile(f1_diffs, 0.025),
                    "upper": percentile(f1_diffs, 0.975),
                },
            },
        },
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Paired scenario-level bootstrap comparing two LLM bug detection result folders."
    )

    parser.add_argument(
        "model_a_results_dir",
        help="First model results folder, e.g. ChatGPT_results"
    )

    parser.add_argument(
        "model_b_results_dir",
        help="Second model results folder, e.g. Gemini_results"
    )

    parser.add_argument(
        "output_json",
        help="Output JSON file, e.g. bootstrap_results.json"
    )

    parser.add_argument(
        "--n_bootstrap",
        type=int,
        default=10000,
        help="Number of bootstrap resamples. Default: 10000"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed. Default: 42"
    )

    args = parser.parse_args()

    result = paired_bootstrap(
        model_a_cases=args.model_a_results_dir,
        model_b_cases=args.model_b_results_dir,
        n_bootstrap=args.n_bootstrap,
        seed=args.seed,
    )

    Path(args.output_json).write_text(
        json.dumps(result, indent=2),
        encoding="utf-8"
    )

    print("Observed comparison:")
    print(json.dumps(result["observed"], indent=2))

    print("\nBootstrap 95% confidence intervals:")
    print(json.dumps(result["bootstrap"], indent=2))

    print(f"\nSaved results to: {args.output_json}")


if __name__ == "__main__":
    main()