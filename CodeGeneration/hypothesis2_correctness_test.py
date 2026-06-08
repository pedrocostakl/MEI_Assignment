import numpy as np
from statsmodels.stats.contingency_tables import mcnemar
import os

# ── Data ────────────────────────────────────────────────────────────────────

chatgpt = {
    "hard": [
        (185,102,True),(262,126,True),(601,68,True),(3451,82,False),
        (3374,88,True),(3482,76,True),(3617,None,False),(3764,70,True),
        (3832,69,True),(3673,84,True),(1581,136,True),(2356,83,True),
        (1978,73,True),(1965,113,True),(1890,229,True),(1873,66,True),
        (1789,164,True),(1757,73,True),(1741,81,True),
    ],
    "medium": [
        (176,82,True),(177,86,True),(178,79,True),(180,75,True),
        (184,116,True),(550,69,True),(570,67,True),(585,82,True),
        (602,70,True),(608,102,True),(626,77,True),(1045,93,True),
        (1070,102,True),(1158,764,True),(1164,85,True),(1174,82,True),
        (1193,70,True),(1204,213,True),(1321,78,True),(1341,159,True),
        (1393,72,True),
    ],
    "easy": [
        (175,100,True),(181,67,True),(182,67,True),(183,103,True),
        (196,71,True),(197,79,True),(511,79,True),(577,118,True),
        (584,88,True),(586,88,True),(595,91,True),(596,70,True),
        (607,151,True),(610,96,True),(619,105,True),(620,79,True),
        (627,92,True),(1050,68,True),(1068,98,True),(1075,135,True),
        (1084,84,True),
    ],
}

gemini = {
    "hard": [
        (185,128,True),(262,94,True),(601,82,True),(3451,84,True),
        (3374,84,False),(3482,94,True),(3673,88,True),(3617,120,True),
        (3832,None,False),(3764,106,True),(1581,80,True),(2356,78,True),
        (1978,68,True),(1965,71,True),(1890,88,True),(1873,82,True),
        (1789,102,True),(1757,81,True),(1741,96,True),
    ],
    "medium": [
        (176,90,True),(177,103,True),(178,None,False),(180,74,True),
        (184,130,True),(550,80,True),(570,102,True),(585,71,True),
        (602,75,True),(608,83,True),(626,79,True),(1045,118,True),
        (1070,83,True),(1158,147,True),(1164,62,True),(1174,73,True),
        (1193,222,True),(1204,65,True),(1321,70,True),(1341,147,True),
        (1393,76,True),
    ],
    "easy": [
        (175,114,True),(181,80,True),(182,70,True),(183,94,True),
        (196,70,True),(197,68,True),(511,74,True),(577,644,True),
        (584,79,True),(586,79,True),(595,78,True),(596,67,True),
        (607,121,True),(610,80,True),(619,118,True),(620,75,True),
        (627,90,True),(1050,93,True),(1068,112,True),(1075,136,True),
        (1084,445,True),
    ],
}

# ── 1. Build paired data ────────────────────────────────────────────────────

diffs_list = ["easy", "medium", "hard"]

gpt_map = {}
gem_map = {}

for diff in diffs_list:
    for pid, rt, ok in chatgpt[diff]:
        gpt_map[pid] = ok
    for pid, rt, ok in gemini[diff]:
        gem_map[pid] = ok

shared_pids = sorted(set(gpt_map.keys()) & set(gem_map.keys()))

both_correct = 0
both_incorrect = 0
gpt_only = 0
gem_only = 0

for pid in shared_pids:
    gpt_ok = gpt_map[pid]
    gem_ok = gem_map[pid]
    
    if gpt_ok and gem_ok:
        both_correct += 1
    elif not gpt_ok and not gem_ok:
        both_incorrect += 1
    elif gpt_ok and not gem_ok:
        gpt_only += 1
    elif not gpt_ok and gem_ok:
        gem_only += 1

# Contingency table
#                Gemini Correct    Gemini Incorrect
# GPT Correct          a (both)        b (gpt only)
# GPT Incorrect        c (gem only)    d (neither)

contingency_table = [[both_correct, gpt_only],
                     [gem_only, both_incorrect]]

print("=" * 65)
print("HYPOTHESIS 2 - CORRECTNESS STATISTICAL ANALYSIS")
print("=" * 65)
print(f"Total problems: {len(shared_pids)}")
print("\nContingency Table:")
print(f"Both Correct: {both_correct}")
print(f"Both Incorrect: {both_incorrect}")
print(f"ChatGPT Only: {gpt_only}")
print(f"Gemini Only: {gem_only}")

# Exact McNemar's test is used when frequencies in discordant cells are small
# Given the high accuracy, they will be small
res = mcnemar(contingency_table, exact=True)

print(f"\nMcNemar's test (Exact):")
print(f"Statistic: {res.statistic}")
print(f"p-value: {res.pvalue:.6f}")

alpha = 0.05
if res.pvalue <= alpha:
    print(f"p = {res.pvalue:.6f} <= {alpha} => REJECT H0")
else:
    print(f"p = {res.pvalue:.6f} > {alpha} => FAIL TO REJECT H0")
