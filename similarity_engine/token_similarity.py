"""
token_similarity.py

Computes Jaccard similarity between two files' n-gram sets.
This is the simplest baseline similarity signal in the pipeline.
"""

from tokenizer import get_ngrams


def jaccard_similarity(tokens_a: list[str], tokens_b: list[str], n: int = 5) -> float:
    """Returns Jaccard similarity (intersection / union) between the
    n-gram sets of two token lists. Returns 0.0 if both sets are empty
    (avoids a divide-by-zero on empty files)."""
    set_a = set(get_ngrams(tokens_a, n))
    set_b = set(get_ngrams(tokens_b, n))

    if not set_a and not set_b:
        return 0.0

    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


if __name__ == "__main__":
    # Manual test with real data via loader.py
    from loader import read_pairs, dataset_path_to_tokens_path, load_tokens

    pairs = read_pairs("pairs.csv")

    # Test on the first few pairs so we can eyeball whether labeled
    # plagiarized pairs (1) score higher than non-plagiarized (0).
    for pair in pairs[:6]:
        tokens_a = load_tokens(dataset_path_to_tokens_path(pair["file_a"]))
        tokens_b = load_tokens(dataset_path_to_tokens_path(pair["file_b"]))
        score = jaccard_similarity(tokens_a, tokens_b)
        print(f"{pair['file_a']} vs {pair['file_b']} "
              f"| label={pair['is_plagiarized']} | jaccard={score:.3f}")