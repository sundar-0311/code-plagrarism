"""
Adds a structural similarity signal to complement token-based Jaccard.

Why: Jaccard on n-gram token windows breaks when code is padded with dead
variables/statements or has a block swapped (every window touching the
change stops matching, even though the surrounding logic is identical).
This script instead compares the AST *node-type* sequence (pre-order,
ignoring identifier names and literal values entirely) via sequence
alignment (difflib.SequenceMatcher), which tolerates insertions/deletions
and only penalizes the actual inserted/changed subtree.

Reads pairs.csv (file_a, file_b, problem_id, is_plagiarized) produced by
2_build_pairs_csv.py. For each pair, recomputes token Jaccard from the
sibling .tokens files and computes the new structural ratio, then writes
both plus a combined score to a new CSV.

Usage:
    python 3_structural_similarity.py <pairs.csv> <output.csv> [--ngram 3]
"""

import argparse
import ast
import csv
from difflib import SequenceMatcher
from pathlib import Path


def load_tokens(py_path: Path) -> list[str]:
    tokens_path = py_path.with_suffix(".tokens")
    if not tokens_path.exists():
        return []
    return tokens_path.read_text(encoding="utf-8").split()


def ngram_set(tokens: list[str], n: int) -> set[tuple[str, ...]]:
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(tokens_a: list[str], tokens_b: list[str], n: int) -> float:
    set_a, set_b = ngram_set(tokens_a, n), ngram_set(tokens_b, n)
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def structural_sequence(node: ast.AST) -> list[str]:
    """Pre-order sequence of AST node type names. Identifier names, literal
    values, and constants are deliberately excluded -- only tree shape
    matters here."""
    seq = [type(node).__name__]
    for child in ast.iter_child_nodes(node):
        seq.extend(structural_sequence(child))
    return seq


def structural_similarity(py_path_a: Path, py_path_b: Path) -> float | None:
    try:
        tree_a = ast.parse(py_path_a.read_text(encoding="utf-8", errors="ignore"))
        tree_b = ast.parse(py_path_b.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return None
    seq_a = structural_sequence(tree_a)
    seq_b = structural_sequence(tree_b)
    return SequenceMatcher(None, seq_a, seq_b, autojunk=False).ratio()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pairs_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument(
        "--ngram", type=int, default=3, help="Token n-gram size for Jaccard (default: 3)"
    )
    args = parser.parse_args()

    with open(args.pairs_csv, newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print(f"No rows found in {args.pairs_csv}")
        return

    out_rows = []
    for row in rows:
        # pairs.csv may have been generated on a different OS (Windows
        # backslash paths read on Linux, or vice versa) -- normalize.
        path_a = Path(row["file_a"].replace("\\", "/"))
        path_b = Path(row["file_b"].replace("\\", "/"))

        tokens_a = load_tokens(path_a)
        tokens_b = load_tokens(path_b)
        jac = jaccard(tokens_a, tokens_b, args.ngram)

        struct = structural_similarity(path_a, path_b)
        struct_val = struct if struct is not None else 0.0

        combined = max(jac, struct_val)

        out_rows.append(
            {
                "file_a": row["file_a"],
                "file_b": row["file_b"],
                "problem_id": row["problem_id"],
                "is_plagiarized": row["is_plagiarized"],
                "jaccard": round(jac, 4),
                "structural": round(struct_val, 4),
                "combined": round(combined, 4),
            }
        )

    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_a",
                "file_b",
                "problem_id",
                "is_plagiarized",
                "jaccard",
                "structural",
                "combined",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} scored pairs to {args.output_csv}")

    # Quick sanity check: how many labeled-plagiarized (1) pairs score
    # LOW on jaccard but get rescued by structural similarity.
    rescued = [
        r
        for r in out_rows
        if r["is_plagiarized"] == "1" and r["jaccard"] < 0.3 and r["structural"] >= 0.5
    ]
    if rescued:
        print(f"\n{len(rescued)} plagiarized pairs had low Jaccard but high structural score:")
        for r in rescued[:10]:
            print(
                f"  {Path(r['file_a']).name} vs {Path(r['file_b']).name} "
                f"| jaccard={r['jaccard']} structural={r['structural']}"
            )


if __name__ == "__main__":
    main()
