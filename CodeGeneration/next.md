1. Compute Correctness per model
-> converting your raw logs into a binary variable.
—> Compute accuracy
ChatGPT accuracy
Gemini accuracy


2. Build contingency table
for  statistical test (McNemar).

| Problem | ChatGPT   | Gemini    |
| ------- | --------- | --------- |
| P1      | Correct   | Correct   |
| P2      | Correct   | Incorrect |
| P3      | Incorrect | Correct   |
| P4      | Incorrect | Incorrect |

|                   | Gemini Correct | Gemini Incorrect |
| ----------------- | -------------- | ---------------- |
| ChatGPT Correct   | a              | b                |
| ChatGPT Incorrect | c              | d                |



3. (Run McNemar test) - used when comparing two models on the same exact items, and the outcome is binary, in our case  Same SQL problems, Two models (ChatGPT vs Gemini), Outcome: Correct / Incorrect


4. Extract execution times per model

Make some analysis and some graphs to have a better vision of the data

| Metric  | Why you need it         |
| ------- | ----------------------- |
| Mean    | overall performance     |
| Median  | robust to skew/outliers |
| Std dev | stability of model      |
| Min/Max | detect extreme cases    |

5. Check distribution (hist + Shapiro-Wilk)