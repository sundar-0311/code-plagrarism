# Programming Assignment Similarity Detector — 4-Day Plan (2 People)

## Problem Statement
Build an AI system that detects highly similar or potentially copied programming assignments even when students change variable names, formatting, comments, or parts of the code structure. The system should produce similarity scores and identify suspicious pairs or groups. Simple exact text matching should not be the only method.

---

## Day 1 — Setup + Dataset + Baseline

### You (Person A): Dataset + Preprocessing
- Write 8–10 base solutions across 4–5 classic problems (bubble sort, factorial, palindrome, linked list reversal, binary search, matrix multiply)
- Generate 3–4 plagiarized variants per base (rename vars, reorder statements, for↔while, add dead code) — use Claude/ChatGPT to help mutate
- Generate 2–3 genuinely different solutions per problem (different algorithm/approach)
- Build labeled CSV: `file_a, file_b, problem_id, is_plagiarized`
- Target: ~40–50 files, ~150–200 labeled pairs
- Write preprocessing: strip comments, normalize whitespace, tokenize + replace identifiers (VAR1, VAR2...) using Python `ast`/`tokenize` module

### Partner (Person B): Core Similarity Engine (baseline)
- Implement token n-gram similarity (Jaccard/cosine on token sets)
- Implement Winnowing/k-gram fingerprinting (MOSS-style) — fallback if AST parsing gets messy
- Implement basic file loader + pairwise comparison loop (all-pairs O(n²))

**End of Day 1 checkpoint:** dataset exists, two independent similarity scores computable per pair.

---

## Day 2 — Structural/Semantic Layer + Scoring

### You: AST-based structural similarity
- Parse each file to AST (Python `ast` module)
- Serialize AST to a string/tree structure (strip identifier names, keep structure + operators + control flow)
- Compute tree similarity (simple: string diff/Levenshtein on serialized tree, or tree-edit-distance via `zss` library)

### Partner: Embedding-based similarity (the "novel feature")
- Load CodeBERT/GraphCodeBERT via HuggingFace (`microsoft/codebert-base`)
- Get embeddings per file, compute cosine similarity
- If GPU/time-constrained: fall back to `sentence-transformers` with a code-tuned model, or TF-IDF on tokens as a cheap embedding proxy

### Both together (end of day)
- Combine 3–4 signals (token, fingerprint, AST, embedding) into a weighted composite score
- Test weights against your labeled dataset — tune until precision/recall look reasonable
- Compute basic metrics: accuracy, precision, recall, F1 on your synthetic labels

**End of Day 2 checkpoint:** composite similarity score works end-to-end on your dataset, metrics computed.

---

## Day 3 — Group Detection + Explainability + UI

### You: Clustering + explainability
- Build similarity matrix (N×N) → threshold → graph (networkx)
- Connected components / community detection → flag groups, not just pairs
- Diff viewer: for flagged pairs, highlight matching code blocks (use `difflib.HtmlDiff` or side-by-side line diff)

### Partner: Dashboard/Frontend
- Streamlit app:
  - Upload folder of files
  - Show similarity heatmap (plotly/seaborn)
  - Show flagged pairs/groups table (sortable by score)
  - Click a pair → show diff view
  - Show cluster graph (networkx + plotly)

**End of Day 3 checkpoint:** working demo — upload files → get flagged results → visual proof.

---

## Day 4 — Polish, Novel Feature Push, Slides, Rehearsal

### Morning (both)
- Stress-test on edge cases: identical files, completely different files, boilerplate-heavy code (reduce false positives from starter code)
- Add confidence calibration (e.g. penalize matches that are >80% boilerplate/import statements)
- Bug fixes on UI/pipeline

### Afternoon split
- **You:** Write README, prepare metrics slide (precision/recall table, example detected case)
- **Partner:** Prepare live demo script (2–3 clear examples: obvious plagiarism, subtle renamed plagiarism, genuinely different code — show system gets all three right)

### Evening
- Full rehearsal, pitch deck (5–6 slides: problem, approach/architecture diagram, novel feature highlight, metrics, demo, future work)

---

## Division Summary

| Day | You | Partner |
|---|---|---|
| 1 | Dataset + preprocessing | Token + fingerprint similarity |
| 2 | AST structural similarity | Embedding similarity (novel feature) |
| 3 | Clustering + diff viewer | Streamlit dashboard |
| 4 | Docs + metrics slide | Demo script + pitch deck |

**Novel feature to emphasize in pitch:** semantic embedding similarity catching logic-equivalent-but-restructured code that pure text/AST methods miss — plus group/cluster detection instead of just pairs.
