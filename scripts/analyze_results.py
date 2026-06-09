from pathlib import Path
import re

base = Path('CodeGeneration')
files = {'chatgpt': base / 'results_chatgpt.md', 'gemini': base / 'results_gemini.md'}
pat = re.compile(r'^Problem\s+(\d+)\s*-\s*(\w+)\s*-\s*([^,]+)(?:,\s*Runtime:\s*(\d+)\s*ms)?', re.IGNORECASE)

def parse(fpath):
    data = {}
    cur_diff=None
    with open(fpath, encoding='utf-8') as f:
        for line in f:
            line=line.strip()
            if line.startswith('----Hard'):
                cur_diff='Hard'
                continue
            if line.startswith('----Medium'):
                cur_diff='Medium'
                continue
            if line.startswith('--------Easy'):
                cur_diff='Easy'
                continue
            m=pat.match(line)
            if m and cur_diff:
                pid=int(m.group(1))
                diff=cur_diff
                status=m.group(3).strip()
                runtime = int(m.group(4)) if m.group(4) else None
                data[pid]={'diff':diff,'status':status,'runtime':runtime}
    return data

chat=parse(files['chatgpt'])
gem=parse(files['gemini'])

# union of problem ids
pids = sorted(set(chat.keys()) | set(gem.keys()))
print('Total problems found (union):', len(pids))

# counts per difficulty per model
from collections import Counter
cc=Counter([v['diff'] for v in chat.values()])
gc=Counter([v['diff'] for v in gem.values()])
print('ChatGPT counts by diff:', cc)
print('Gemini counts by diff:', gc)

# ensure 20 each
for model,name in [(chat,'ChatGPT'),(gem,'Gemini')]:
    cnts=Counter([v['diff'] for v in model.values()])
    print(name, 'total parsed', sum(cnts.values()))

# build paired table for correctness (Accepted vs Not)

def accepted(status):
    return status.lower().startswith('accepted')

a=b=c=d=0
paired=[]
for pid in pids:
    c_stat = chat.get(pid)
    g_stat = gem.get(pid)
    c_acc = accepted(c_stat['status']) if c_stat else False
    g_acc = accepted(g_stat['status']) if g_stat else False
    if c_acc and g_acc:
        a+=1
    elif c_acc and not g_acc:
        b+=1
    elif not c_acc and g_acc:
        c+=1
    else:
        d+=1
    # collect runtimes if both accepted
    if c_acc and g_acc:
        paired.append((pid, c_stat.get('runtime'), g_stat.get('runtime')))

print('Contingency (a both, b ChatGPT only, c Gemini only, d none):', a,b,c,d)

# discordant pairs
n_disc = b+c
print('Discordant pairs n=', n_disc)

# exact McNemar p-value (two-sided) using binomial sum
import math
from math import comb

if n_disc>0:
    k=min(b,c)
    p=0
    for i in range(0,k+1):
        p += comb(n_disc,i)
    p = p / (2**n_disc)
    p = min(1.0, 2*p)
else:
    p=1.0
print('Exact McNemar two-sided p-value (approx):', p)

# Difficulty effect: combine both models per problem (two observations per pid)
# We'll count Accepted vs Not for NotHard vs Hard
hard_correct=hard_total=0
nothard_correct=nothard_total=0
for pid in pids:
    for model in (chat,gem):
        entry=model.get(pid)
        if not entry:
            continue
        diff = entry['diff']
        isacc = accepted(entry['status'])
        if diff=='Hard':
            hard_total +=1
            if isacc: hard_correct+=1
        else:
            nothard_total +=1
            if isacc: nothard_correct+=1
print('Hard correct/total:', hard_correct, hard_total)
print('NotHard correct/total:', nothard_correct, nothard_total)

# Fisher exact test for 2x2 table
not_incorrect = nothard_total - nothard_correct
hard_incorrect = hard_total - hard_correct
print('Contingency for difficulty: [[NotHard_correct, NotHard_incorrect],[Hard_correct,Hard_incorrect]]')
print([[nothard_correct, not_incorrect],[hard_correct, hard_incorrect]])

# compute Fisher's exact two-sided p-value (hypergeometric sum)
from math import comb

def fisher_two_sided(a,b,c,d):
    row1 = a+b
    row2 = c+d
    col1 = a+c
    col2 = b+d
    N = a+b+c+d
    def hyper(a_):
        return comb(row1,a_)*comb(row2,col1-a_)/comb(N,col1)
    obs = hyper(a)
    p=0
    min_k = max(0, col1-row2)
    max_k = min(col1, row1)
    for k in range(min_k, max_k+1):
        pk = hyper(k)
        if pk <= obs + 1e-12:
            p += pk
    return p

p_fisher = fisher_two_sided(nothard_correct, not_incorrect, hard_correct, hard_incorrect)
print('Fisher two-sided p-value (approx):', p_fisher)

# Wilcoxon: compute paired differences stats
paired_clean = [(pid,c_r,g_r) for pid,c_r,g_r in paired if c_r is not None and g_r is not None]
print('Paired accepted count:', len(paired_clean))
if paired_clean:
    diffs=[c-g for _,c,g in paired_clean]
    import statistics
    print('mean diff', statistics.mean(diffs))
    print('median diff', statistics.median(diffs))
    try:
        from scipy.stats import wilcoxon
        stat = wilcoxon([c for _,c,g in paired_clean],[g for _,c,g in paired_clean])
        print('Wilcoxon result', stat)
    except Exception as e:
        print('scipy not available or wilcoxon failed:', e)

    # Print problem ID lists per difficulty for each model to help normalization
    def ids_by_diff(model):
        bydiff={'Easy':[], 'Medium':[], 'Hard':[]}
        for pid,v in model.items():
            bydiff[v['diff']].append(pid)
        for k in bydiff:
            bydiff[k].sort()
        return bydiff

    chat_ids = ids_by_diff(chat)
    gem_ids = ids_by_diff(gem)
    print('\nChatGPT IDs by difficulty:')
    for k in ('Easy','Medium','Hard'):
        print(k, len(chat_ids[k]), chat_ids[k])
    print('\nGemini IDs by difficulty:')
    for k in ('Easy','Medium','Hard'):
        print(k, len(gem_ids[k]), gem_ids[k])

    # Find which IDs are missing in Gemini compared to ChatGPT
    missing_in_gem = sorted([pid for pid in chat.keys() if pid not in gem.keys()])
    missing_in_chat = sorted([pid for pid in gem.keys() if pid not in chat.keys()])
    print('\nIDs present in ChatGPT but missing in Gemini:', missing_in_gem)
    print('IDs present in Gemini but missing in ChatGPT:', missing_in_chat)

    # Also print accepted counts per difficulty for each model
    def accepted_counts(model):
        counts={'Easy':{'total':0,'accepted':0},'Medium':{'total':0,'accepted':0},'Hard':{'total':0,'accepted':0}}
        for pid,v in model.items():
            d=v['diff']; counts[d]['total']+=1
            if v['status'].lower().startswith('accepted'):
                counts[d]['accepted']+=1
        return counts

    print('\nAccepted counts by difficulty:')
    print('ChatGPT:', accepted_counts(chat))
    print('Gemini :', accepted_counts(gem))
