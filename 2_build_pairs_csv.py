"""
Labeling rule (based on the 1-3 / 4-6 convention):
    - Both files numbered 1-3 (within the same problem)      -> 0 (not plagiarized)
    - Either file numbered 4-6 (within the same problem)      -> 1 (plagiarized)
    - Files from different problem folders                    -> 0 (different problem)

If your files don't start with a leading number, pass --pattern to
control how the "plagiarized" group is detected (see NUMBER_RE below).

Usage:
    python build_pairs_csv.py <dataset_dir> <output.csv>
    python build_pairs_csv.py <dataset_dir> <output.csv> --plag-start 4
"""

import argparse
import csv
import re
from itertools import combinations
from pathlib import Path

NUMBER_RE = re.compile(r"^(\d+)")


def leading_number(filename: str) -> int | None:
    match = NUMBER_RE.match(filename)
    return int(match.group(1)) if match else None


def is_plagiarized_file(filename: str, plag_start: int) -> bool | None:
    """Returns True if this file is in the plagiarized range, False if in
    the non-plagiarized range, None if the number couldn't be determined."""
    num = leading_number(filename)
    if num is None:
        return None
    return num >= plag_start


def label_pair(file_a: str, file_b: str, plag_start: int) -> int | None:
    a_plag = is_plagiarized_file(file_a, plag_start)
    b_plag = is_plagiarized_file(file_b, plag_start)
    if a_plag is None or b_plag is None:
        return None  # couldn't determine -> caller should skip or flag
    return 1 if (a_plag or b_plag) else 0


def collect_problem_folders(dataset_dir: Path):
    """Returns {problem_name: [py_file_paths]} for every immediate
    subfolder of dataset_dir that contains .py files."""
    problems = {}
    for sub in sorted(dataset_dir.iterdir()):
        if sub.is_dir():
            py_files = sorted(sub.glob("*.py"))
            if py_files:
                problems[sub.name] = py_files
    return problems


def build_rows(problems: dict, plag_start: int):
    rows = []
    unresolved = []

    # Within-problem pairs (the ones that matter for training a detector)
    for problem_name, files in problems.items():
        for file_a, file_b in combinations(files, 2):
            label = label_pair(file_a.name, file_b.name, plag_start)
            if label is None:
                unresolved.append((file_a.name, file_b.name))
                continue
            rows.append(
                {
                    "file_a": str(file_a),
                    "file_b": str(file_b),
                    "problem_id": problem_name,
                    "is_plagiarized": label,
                }
            )

    return rows, unresolved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument(
        "--plag-start",
        type=int,
        default=4,
        help="Leading file number at which the plagiarized group begins (default: 4, i.e. 1-3 clean, 4+ plagiarized)",
    )
    args = parser.parse_args()

    problems = collect_problem_folders(args.dataset_dir)
    if not problems:
        print(f"No problem subfolders with .py files found under {args.dataset_dir}")
        return

    rows, unresolved = build_rows(problems, args.plag_start)

    with open(args.output_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["file_a", "file_b", "problem_id", "is_plagiarized"]
        )
        writer.writeheader()
        writer.writerows(rows)

    n_pos = sum(r["is_plagiarized"] for r in rows)
    n_neg = len(rows) - n_pos
    print(f"Wrote {len(rows)} labeled pairs to {args.output_csv}")
    print(f"  plagiarized (1): {n_pos}")
    print(f"  non-plagiarized (0): {n_neg}")
    print(f"  problems covered: {len(problems)}")

    if unresolved:
        print(f"\nWARNING: {len(unresolved)} pairs could not be labeled "
              f"(filenames didn't start with a number). First few:")
        for a, b in unresolved[:5]:
            print(f"    {a}  <->  {b}")


if __name__ == "__main__":
    main()