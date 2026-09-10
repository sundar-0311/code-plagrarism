"""
loader.py

Reads pairs.csv and loads the preprocessed .tokens content for each
file referenced in a pair. Bridges dataset/ paths (used in pairs.csv)
to preprocessed_output/ paths (where the actual .tokens files live).
"""

import csv
from pathlib import Path

DATASET_ROOT = Path("dataset")
PREPROCESSED_ROOT = Path("preprocessed_output")


def read_pairs(csv_path):
    """Reads pairs.csv and returns a list of dicts:
    {file_a, file_b, problem_id, is_plagiarized}"""
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["is_plagiarized"] = int(row["is_plagiarized"])
            rows.append(row)
    return rows


def dataset_path_to_tokens_path(dataset_path: str) -> Path:
    """Converts a dataset/... .py path (as stored in pairs.csv) into the
    matching preprocessed_output/... .tokens path."""
    rel = Path(dataset_path).relative_to(DATASET_ROOT)
    tokens_rel = rel.with_suffix(".tokens")
    return PREPROCESSED_ROOT / tokens_rel


def load_tokens(tokens_path: Path) -> list[str]:
    """Reads a .tokens file and returns its tokens as a list of strings."""
    content = tokens_path.read_text(encoding="utf-8")
    return content.split()


if __name__ == "__main__":
    # Quick manual test: load the first pair and show token counts.
    pairs = read_pairs("pairs.csv")
    first = pairs[0]
    print("First pair:", first)

    path_a = dataset_path_to_tokens_path(first["file_a"])
    path_b = dataset_path_to_tokens_path(first["file_b"])
    print("Resolved token paths:", path_a, path_b)

    tokens_a = load_tokens(path_a)
    tokens_b = load_tokens(path_b)
    print(f"tokens_a: {len(tokens_a)} tokens")
    print(f"tokens_b: {len(tokens_b)} tokens")
    print("First 10 tokens of A:", tokens_a[:10])