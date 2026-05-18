import json
import glob
from statistics import mean

paths = glob.glob("c:/Users/Luis Vaz/Documents/Universidade/MEI/2S/MEI/MEI_Assignment/CodeGeneration/ChatGPT_outputs/*_results.json")
paths += [p for p in glob.glob("c:/Users/Luis Vaz/Documents/Universidade/MEI/2S/MEI/MEI_Assignment/CodeGeneration/ChatGPT_outputs/*.json") if p.endswith('ChatGPT_results1.json')]

complexities = []
maintainabilities = []
locs = []
exec_times = []
latencies = []
success_count = 0
total = 0

for p in sorted(set(paths)):
    try:
        with open(p, 'r', encoding='utf-8') as f:
            j = json.load(f)
    except Exception:
        continue
    total += 1
    c = j.get('complexity', {})
    if 'avg_complexity' in c:
        complexities.append(c['avg_complexity'])
    if 'maintainability_index' in c:
        maintainabilities.append(c['maintainability_index'])
    if 'lines_of_code' in c:
        locs.append(c['lines_of_code'])
    et = j.get('execution_time')
    if isinstance(et, (int, float)):
        exec_times.append(et)
    func = j.get('functional', {})
    if func.get('success'):
        success_count += 1
        lat = func.get('latency')
        if isinstance(lat, (int, float)):
            latencies.append(lat)

def fmt(x):
    return round(x, 3)

out = {
    'total_files': total,
    'average_complexity': fmt(mean(complexities)) if complexities else None,
    'maintainability_index': fmt(mean(maintainabilities)) if maintainabilities else None,
    'lines_of_code': fmt(mean(locs)) if locs else None,
    'execution_time_sec': fmt(mean(exec_times)) if exec_times else None,
    'functional_latency_sec': fmt(mean(latencies)) if latencies else None,
    'functional_success_rate': f"{(success_count/total*100):.1f}%" if total else None,
}

print(json.dumps(out, indent=2))
