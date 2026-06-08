import re, math
from pathlib import Path

p1 = Path('CodeGeneration/results_chatgpt.md')
p2 = Path('CodeGeneration/results_gemini.md')
pattern = re.compile(r'Problem\s+(\d+)\s+-.*Accepted.*Runtime:\s*([0-9]+)\s*ms', re.IGNORECASE)
pattern2 = re.compile(r'Problem\s+(\d+)\s+-.*Accepted.*Runtime:\s*([0-9]+)ms', re.IGNORECASE)


def parse(path):
    d={}
    s=path.read_text(encoding='utf-8')
    for m in pattern.finditer(s):
        d[int(m.group(1))]=int(m.group(2))
    for m in pattern2.finditer(s):
        d[int(m.group(1))]=int(m.group(2))
    return d

c=parse(p1)
g=parse(p2)
ids=sorted(set(c.keys()) & set(g.keys()))
print('paired_ids_count=',len(ids))

chat=[c[i] for i in ids]
gem=[g[i] for i in ids]

import numpy as np
arr_chat=np.array(chat)
arr_gem=np.array(gem)
d=arr_chat - arr_gem
mask = d!=0
d_nz=d[mask]
ids_nz=[ids[i] for i,ok in enumerate(mask) if ok]
print('nonzero_pairs=',len(d_nz))
if len(d_nz)==0:
    print('No non-zero pairs; cannot compute Wilcoxon')
    raise SystemExit(0)

absd = np.abs(d_nz)
order = np.argsort(absd)
ranks = np.empty_like(order, dtype=float)
vals=absd[order]
rank_vals = np.zeros(len(vals), dtype=float)
i=0
while i<len(vals):
    j=i+1
    while j<len(vals) and vals[j]==vals[i]: j+=1
    avg_rank = (i+1 + j)/2.0
    rank_vals[i:j]=avg_rank
    i=j
ranks[order]=rank_vals
signed = ranks * np.sign(d_nz)
W_plus = signed[signed>0].sum()
W_minus = -signed[signed<0].sum()
W = min(W_plus, W_minus)

n = len(d_nz)
meanW = n*(n+1)/4.0
varW = n*(n+1)*(2*n+1)/24.0
sign = 1 if W>meanW else (-1 if W<meanW else 0)
Z = (W - meanW - sign*0.5)/math.sqrt(varW)
# two-sided p
p = 2*(1 - 0.5*(1+math.erf(abs(Z)/math.sqrt(2))))
# effect size r
r = Z/math.sqrt(n) if n>0 else float('nan')

print(f"W_plus={W_plus:.3f}, W_minus={W_minus:.3f}, W={W:.3f}")
print(f"n'={n}, meanW={meanW:.3f}, varW={varW:.3f}")
print(f"Z={Z:.4f}, p(two-sided)={p:.4f}, r={r:.6f}")
print('example_pairs (id,chat,gem,d):')
for i in range(min(8,len(ids_nz))):
    idx=ids.index(ids_nz[i])
    print(ids_nz[i], int(arr_chat[idx]), int(arr_gem[idx]), int(d_nz[i]))

# print full lists lengths
print('total_paired_ids=',len(ids))
#print lists counts
print('total_chat_count=',len(chat),'total_gem_count=',len(gem))

# save results to file
out = Path('CodeGeneration/wilcoxon_results.txt')
with out.open('w', encoding='utf-8') as f:
    f.write(f"W_plus={W_plus:.3f}, W_minus={W_minus:.3f}, W={W:.3f}\n")
    f.write(f"n_nonzero={n}, Z={Z:.4f}, p={p:.6f}, r={r:.6f}\n")
    f.write('paired_ids_count='+str(len(ids))+"\n")
    f.write('nonzero_ids_count='+str(len(ids_nz))+"\n")
    f.write('example_pairs:\n')
    for i in range(min(20,len(ids_nz))):
        idx=ids.index(ids_nz[i])
        f.write(f"{ids_nz[i]} {int(arr_chat[idx])} {int(arr_gem[idx])} {int(d_nz[i])}\n")
print('results written to CodeGeneration/wilcoxon_results.txt')