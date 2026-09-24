"""
embed_main.py

Driver for the embedding signal. Reads every pair in pairs.csv, embeds
each *unique* file once (48 files, not 240 file-slots), then looks up
the cosine similarity of each pair.

Run from the repo root (same convention as main.py):

    python similarity_engine/embed_main.py --backend tfidf           # quick test
    python similarity_engine/embed_main.py --backend codebert        # text-only semantic
    python similarity_engine/embed_main.py --backend graphcodebert   # + data-flow structure
    python similarity_engine/embed_main.py --backend codebert --source raw

--source preprocessed  (default) embeds preprocessed_output/**/*.py, where
                       identifiers are already VAR1, VAR2... and comments
                       are gone -- so renaming cannot fool the model.
--source raw           embeds dataset/**/*.py exactly as written. Real
                       variable names and comments carry meaning to
                       CodeBERT, so this is worth running as an experiment.
"""

import argparse
import csv
from pathlib import Path

import numpy as np

from loader import read_pairs, dataset_path_to_tokens_path
from embedding_similarity import make_embedder, cosine_matrix


def source_path(dataset_path: str, source: str) -> Path:
    """Map a path from pairs.csv to the .py file whose text we embed."""
    if source == "raw":
        return Path(dataset_path.replace("\\", "/"))
    return dataset_path_to_tokens_path(dataset_path).with_suffix(".py")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["codebert", "graphcodebert", "tfidf"], default="codebert")
    parser.add_argument("--source", choices=["preprocessed", "raw"], default="preprocessed")
    parser.add_argument("--pairs", default="pairs.csv")
    parser.add_argument("--out", default=None, help="default: results/embedding_<backend>[_raw].csv")
    args = parser.parse_args()

    out_path = Path(args.out) if args.out else Path(
        f"results/embedding_{args.backend}{'_raw' if args.source == 'raw' else ''}.csv"
    )

    pairs = read_pairs(args.pairs)
    print(f"Loaded {len(pairs)} pairs from {args.pairs}")

    # 1. Unique files, each embedded exactly once.
    unique_files = sorted({p["file_a"] for p in pairs} | {p["file_b"] for p in pairs})
    texts = [source_path(f, args.source).read_text(encoding="utf-8") for f in unique_files]
    print(f"Embedding {len(unique_files)} unique files with backend={args.backend}, source={args.source}")

    # 2. Files -> vectors -> N x N cosine matrix.
    embeddings = make_embedder(args.backend).embed(texts)
    print(f"Embedding matrix shape: {embeddings.shape}")
    sim = cosine_matrix(embeddings)
    index = {f: i for i, f in enumerate(unique_files)}

    # 3. Read the score for each labelled pair.
    rows = []
    for p in pairs:
        score = float(sim[index[p["file_a"]], index[p["file_b"]]])
        rows.append({
            "file_a": p["file_a"],
            "file_b": p["file_b"],
            "problem_id": p["problem_id"],
            "is_plagiarized": p["is_plagiarized"],
            "embedding": round(score, 4),
        })

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")

    # Sanity summary. Note the spread: CodeBERT cosines are usually all
    # high (0.9+); what matters is the *ranking*, not the absolute value.
    scores = np.array([r["embedding"] for r in rows])
    labels = np.array([r["is_plagiarized"] for r in rows])
    print(f"\nall pairs : min={scores.min():.3f}  max={scores.max():.3f}")
    print(f"label=0   : mean={scores[labels == 0].mean():.3f}")
    print(f"label=1   : mean={scores[labels == 1].mean():.3f}   "
          f"(label=1 includes the mislabelled cross pairs -- see composite.py)")


if __name__ == "__main__":
    main()