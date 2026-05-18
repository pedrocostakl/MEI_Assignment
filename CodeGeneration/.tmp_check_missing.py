import json
from pathlib import Path

root = Path("c:/Users/Luis Vaz/Documents/Universidade/MEI/2S/MEI/MEI_Assignment/CodeGeneration")
for dataset in ["ChatGPT_outputs", "Gemini_outputs"]:
    files = sorted((root / dataset).glob("*_results.json"))
    ok = 0
    bad = []
    for fp in files:
        try:
            with fp.open("r", encoding="utf-8") as f:
                d = json.load(f)
            _ = d["complexity"]["avg_complexity"]
            _ = d["complexity"]["maintainability_index"]
            _ = d["complexity"]["lines_of_code"]
            _ = d["functional"]["latency"]
            _ = d["execution_time"]
            ok += 1
        except Exception as e:
            bad.append((fp.name, str(e)))
    print(dataset, "total", len(files), "usable", ok, "bad", len(bad))
    for name, err in bad:
        print(" -", name, "=>", err)
