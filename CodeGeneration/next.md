\subsection{Results and Correctness Analysis}

The generated SQL solutions were evaluated on 61 problems per model. Because each problem was submitted once and the platform returned a binary outcome (Accepted or Not Accepted), correctness and accuracy are equivalent in this setting and are computed as:

\[
	ext{Accuracy} = \frac{\text{Accepted Solutions}}{\text{Total Problems}}
\]

Table~\ref{tab:codegen-overall} summarises the overall correctness of both models.

\begin{table}[h]
\centering
\begin{tabular}{lccc}
\hline
	extbf{Model} & \textbf{Accepted} & \textbf{Total} & \textbf{Accuracy} \\
\hline
ChatGPT & 59 & 61 & 96.72\% \\
Gemini  & 58 & 61 & 95.08\% \\
\hline
\end{tabular}
\caption{Overall correctness of the SQL code generation models.}
\label{tab:codegen-overall}
\end{table}

The two models performed very similarly overall, with ChatGPT obtaining a slightly higher acceptance rate. The difference is driven by one additional rejected solution in Gemini's output. In both cases, the models achieved perfect performance on Easy problems and near-perfect performance on Medium problems.

Table~\ref{tab:codegen-difficulty} breaks down the results by problem difficulty.

\begin{table}[h]
\centering
\begin{tabular}{lccc}
\hline
	extbf{Difficulty} & \textbf{ChatGPT} & \textbf{Gemini} & \textbf{Total Problems} \\
\hline
Easy   & 21/21 (100.00\%) & 21/21 (100.00\%) & 21 \\
Medium & 21/21 (100.00\%) & 20/21 (95.24\%)  & 21 \\
Hard   & 17/19 (89.47\%)  & 17/19 (89.47\%)  & 19 \\
\hline
\end{tabular}
\caption{Correctness by difficulty level.}
\label{tab:codegen-difficulty}
\end{table}

The hardest problems produced the lowest acceptance rate for both models, indicating that problem complexity had a clear effect on performance. The Hard category accounts for both of the ChatGPT failures and for two of the three Gemini failures. One additional Gemini failure occurred in the Medium category.

\subsection{Statistical Comparison}

Since both models were evaluated on the same set of problems and the outcome is binary, the paired comparison can be tested using McNemar's test. For each problem, the result is classified into one of four cases:

\begin{itemize}
	\item both models correct,
	\item ChatGPT correct and Gemini incorrect,
	\item ChatGPT incorrect and Gemini correct,
	\item both models incorrect.
\end{itemize}

This contingency table provides the basis for testing whether the observed difference in correctness is statistically significant.