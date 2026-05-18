import json
from pathlib import Path
from scipy import stats

root = Path("c:/Users/Luis Vaz/Documents/Universidade/MEI/2S/MEI/MEI_Assignment/CodeGeneration")
sets = {
    "ChatGPT": sorted((root / "ChatGPT_outputs").glob("*_results.json")),
    "Gemini": sorted((root / "Gemini_outputs").glob("*_results.json")),
}

feature_getters = {
    "avg_complexity": lambda d: d["complexity"]["avg_complexity"],
    "maintainability_index": lambda d: d["complexity"]["maintainability_index"],
    "lines_of_code": lambda d: d["complexity"]["lines_of_code"],
    "functional_latency": lambda d: d["functional"]["latency"],
    "execution_time": lambda d: d["execution_time"],
}

alpha = 0.05
print(f"alpha={alpha}")
print("dataset,feature,n,shapiro_W,shapiro_p,shapiro_normal,dagostino_K2,dagostino_p,dagostino_normal")

for dataset, files in sets.items():
    rows = []
    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                rows.append(json.load(f))
        except Exception:
            pass

    for feature, getter in feature_getters.items():
        values = []
        for r in rows:
            try:
                v = getter(r)
                if v is not None:
                    values.append(float(v))
            except Exception:
                continue

        n = len(values)
        if n < 3:
            print(f"{dataset},{feature},{n},NA,NA,NA,NA,NA,NA")
            continue

        W, p_shap = stats.shapiro(values)
        shap_normal = p_shap > alpha

        if n >= 8:
            K2, p_dag = stats.normaltest(values)
            dag_normal = p_dag > alpha
            print(f"{dataset},{feature},{n},{W:.6f},{p_shap:.6g},{shap_normal},{K2:.6f},{p_dag:.6g},{dag_normal}")
        else:
            print(f"{dataset},{feature},{n},{W:.6f},{p_shap:.6g},{shap_normal},NA,NA,NA")
