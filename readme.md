PROGRAMMING ASSIGNMENT SIMILARITY AND PLAGRARISM CHECKER

*WHY SIMPLE MATCHING FAILS*

A student who copies usually disguises the code in the form of
  1. renaming variables
  2. changing formatting, removing or adding comments
  3. insert unused variables or dead statements
  4. use same logic but in different style or order
  5. switch up for and while loops and so on

and all the above cases will bypass an exact text matching machine.


*PIPELINE STAGE BY STAGE*

We parsed the file with pythons ast module and we also delted the comment lines
All the user defined variables were given a common name such as VAR1, VAR2.... and the keywords, builtin were left alone
White space was normalized using ast.unparse and the blank lines were dropped

renaming is the single most common disguise. After canonicalization, two files that differ only by naming, comments or formatting become identical strings. We verified this using a fully renamed and reformatted copy that scores exactly 1.000 on every signal.

Working on the AST rather than regexes means renaming is scope-safe and cannot corrupt strings or keywords.

*Signal 1: token n-gram Jaccard (similarity_engine/token_similarity.py)*

We Slided a window of 5 tokens over each file to compute the Jaccard overlap of the two n-gram sets.

We did this to get the simplest possible baseline as it is fast and easy to explain, and it shows how much overlap survives canonicalization. 

Weakness: every window that touches an inserted line stops matching, so dead-code padding hurts it badly. This motivates the other signals.

*Signal 2: winnowing fingerprints (similarity_engine/winnowing.py)*

MOSS-style winnowing: hash every 5-gram (MD5, so results are reproducible across runs), slide a window of 4 hashes, keep the minimum in each window (rightmost on ties), and compare fingerprint sets.

Why: winnowing is the classic algorithm behind Stanford's MOSS. It guarantees that any sufficiently long shared run of tokens produces at least one shared fingerprint, while storing far fewer hashes than full n-grams.

*Signal 3: AST structural similarity (3_structural_similarity.py)*

Serialize each AST as a pre-order sequence of node type names only (identifier names and literal values are ignored), then compare the two sequences with difflib.SequenceMatcher.

Why: sequence alignment tolerates insertions and deletions, so it only penalizes the inserted or changed subtree rather than everything around it. It survives dead-code padding, literal changes and renames. It was the strongest single signal in our evaluation (ROC-AUC 0.907). Caveat: it has a high baseline, because all Python programs share many node types, so an unrelated pair still scores around 0.5. That is why we min-max normalize before combining.

*Signal 4: semantic embeddings (similarity_engine/embedding_similarity.py)*

Each file is passed through CodeBERT (microsoft/codebert-base), mean-pooled over real tokens into one 768-dimensional vector, and two files are compared by cosine similarity. Embeddings are computed on the preprocessed source, so renaming cannot influence them.

*Score fusion (similarity_engine/composite.py)*

Min-max normalize each signal to [0, 1] using the range seen in training.
Weighted sum with weights chosen by grid search (step 0.1 over all weight vectors summing to 1), maximizing ROC-AUC. A tiny sum-of-squares penalty breaks ties in favour of balanced weights.
Threshold chosen to maximize F1, placed in the gap just below the lowest score it flags.

*Dataset and labels*

48 Python files: 8 classic problems (binary search, bubble sort, factorial, Fibonacci, matrix multiply, palindrome, prime check, reverse linked list) x 6 files each.
Files 1-3 of each problem are meant as independent solutions; files 4-6 are disguised variants (renames, dead code, reordering, loop rewrites).
120 labelled pairs (all within-problem pairs).

*Novel features*

1. Semantic embedding signal (CodeBERT), with an optional data-flow variant (GraphCodeBERT). Adds a meaning-level view on top of three syntactic signals, and we quantify its contribution with confidence intervals rather than asserting it.
2. Group-level detection. Reports suspicion groups, not just pairs, so a cheating ring is one finding.
3. Label-correction analysis. We identified and measured a flaw in our own ground truth (52 mislabelled pairs) and built the evaluation on corrected labels, keeping the raw numbers only as a diagnostic.
4. Leakage-free evaluation. Weights, normalization ranges and thresholds are all tuned inside each cross-validation fold.
5. Consistent dual-mode scoring. A calibrated fallback when embeddings are unavailable, routed through the same function as the full model.
6. Evidence, not just a number. Per-signal breakdown, side-by-side diffs, heatmap and cluster graph.


*HOW TO SET UP THE PROJECT*
1. pip install -r requirements.txt
2. streamlit app.py
3. For the user files, upload any 2 files of the same program that needs to be checked
