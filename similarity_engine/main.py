"""
main.py

Driver script for the similarity engine. Reads every pair in
pairs.csv, computes both similarity scores for each, and writes the
full results to results/similarity_results.csv.
"""

import csv
from pathlib import Path

from loader import read_pairs
from compare import compare_pair

OUTPUT_PATH = Path("results/similarity_results.csv")


def main():
    pairs = read_pairs("pairs.csv")
    print(f"Loaded {len(pairs)} pairs from pairs.csv")

    results = []
    for i, pair in enumerate(pairs, start=1):
        result = compare_pair(pair)
        results.append(result)
        if i % 20 == 0 or i == len(pairs):
            print(f"  processed {i}/{len(pairs)}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["file_a", "file_b", "problem_id", "is_plagiarized", "jaccard", "winnow"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nWrote {len(results)} rows to {OUTPUT_PATH}")

    # Quick sanity summary: average scores split by label
    label0 = [r for r in results if r["is_plagiarized"] == 0]
    label1 = [r for r in results if r["is_plagiarized"] == 1]

    def avg(rows, key):
        return sum(r[key] for r in rows) / len(rows) if rows else 0.0

    print(f"\nlabel=0 (n={len(label0)}): avg jaccard={avg(label0,'jaccard'):.3f}, avg winnow={avg(label0,'winnow'):.3f}")
    print(f"label=1 (n={len(label1)}): avg jaccard={avg(label1,'jaccard'):.3f}, avg winnow={avg(label1,'winnow'):.3f}")


if __name__ == "__main__":
    main()