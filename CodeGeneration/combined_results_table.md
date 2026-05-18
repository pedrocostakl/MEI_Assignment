# Combined Results Table

The values below are the mean and sample standard deviation computed from the JSON result files in `Gemini_outputs` and `ChatGPT_outputs`.

| Metric | Gemini Mean | Gemini Std. Dev. | ChatGPT Mean | ChatGPT Std. Dev. |
| --- | ---: | ---: | ---: | ---: |
| Cyclomatic complexity | 1.440 | 0.049 | 1.627 | 0.107 |
| Maintainability index | 50.195 | 2.334 | 51.383 | 2.526 |
| Lines of code | 201.103 | 18.961 | 255.718 | 58.800 |
| Functional latency (seconds) | 0.094 | 0.036 | 0.065 | 0.009 |
| Execution time (seconds) | 1.757 | 0.410 | 2.358 | 4.243 |

Notes:
- Standard deviations are sample standard deviations.
- The execution time standard deviation for ChatGPT is large because the runs include a few much slower outliers.
