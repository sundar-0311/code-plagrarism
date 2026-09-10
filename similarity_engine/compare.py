"""
compare.py

Compares one pair of files using all available similarity signals
and returns a single combined result. This is the seam between the
individual similarity methods (token_similarity.py, winnowing.py)
and the full-dataset driver (main.py).
"""

from loader import dataset_path_to_tokens_path, load_tokens
from token_similarity import jaccard_similarity
from winnowing import fingerprint_similarity


def compare_pair(pair: dict) -> dict:
    """Takes one row from pairs.csv (as a dict) and returns a result
    dict with both similarity scores added."""
    tokens_a = load_tokens(dataset_path_to_tokens_path(pair["file_a"]))
    tokens_b = load_tokens(dataset_path_to_tokens_path(pair["file_b"]))

    jaccard = jaccard_similarity(tokens_a, tokens_b)
    winnow = fingerprint_similarity(tokens_a, tokens_b)

    return {
        "file_a": pair["file_a"],
        "file_b": pair["file_b"],
        "problem_id": pair["problem_id"],
        "is_plagiarized": pair["is_plagiarized"],
        "jaccard": round(jaccard, 4),
        "winnow": round(winnow, 4),
    }


if __name__ == "__main__":
    from loader import read_pairs

    pairs = read_pairs("pairs.csv")

    for pair in pairs[:6]:
        result = compare_pair(pair)
        print(result)