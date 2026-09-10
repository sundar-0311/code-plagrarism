"""
winnowing.py

Implements the Winnowing algorithm (MOSS-style k-gram fingerprinting):
1. Turn token list into n-grams (via tokenizer.py).
2. Hash each n-gram to an integer.
3. Slide a window over the hash sequence; keep the minimum hash in
   each window as a "fingerprint" (with simple tie-breaking).
4. Compare two files by how many fingerprints they share.

This gives a second, independent similarity signal alongside the
plain Jaccard n-gram overlap in token_similarity.py.
"""

import hashlib
from tokenizer import get_ngrams


def hash_ngram(ngram: tuple[str, ...]) -> int:
    """Deterministically hashes an n-gram to an integer.

    We use hashlib (not Python's built-in hash()) because hash() is
    randomized per-process for strings unless PYTHONHASHSEED is fixed
    — that would make fingerprints non-reproducible between runs.
    """
    joined = " ".join(ngram)
    digest = hashlib.md5(joined.encode("utf-8")).hexdigest()
    return int(digest, 16)


def winnow(hashes: list[int], window_size: int = 4) -> set[int]:
    """Slides a window over the hash sequence and keeps the minimum
    hash from each window as a fingerprint. If several hashes tie for
    the minimum in a window, keeps the rightmost one (standard
    winnowing tie-breaking rule — avoids over-selecting fingerprints
    from repetitive code)."""
    if len(hashes) <= window_size:
        return set(hashes)

    fingerprints = set()
    for i in range(len(hashes) - window_size + 1):
        window = hashes[i:i + window_size]
        min_value = min(window)
        # rightmost index of the minimum within this window
        min_index = len(window) - 1 - window[::-1].index(min_value)
        fingerprints.add(window[min_index])
    return fingerprints


def get_fingerprints(tokens: list[str], n: int = 5, window_size: int = 4) -> set[int]:
    """Full pipeline: tokens -> n-grams -> hashes -> winnowed fingerprints."""
    ngrams = get_ngrams(tokens, n)
    hashes = [hash_ngram(g) for g in ngrams]
    return winnow(hashes, window_size)


def fingerprint_similarity(tokens_a: list[str], tokens_b: list[str],
                            n: int = 5, window_size: int = 4) -> float:
    """Jaccard similarity between two files' fingerprint sets."""
    fp_a = get_fingerprints(tokens_a, n, window_size)
    fp_b = get_fingerprints(tokens_b, n, window_size)

    if not fp_a and not fp_b:
        return 0.0

    intersection = fp_a & fp_b
    union = fp_a | fp_b
    return len(intersection) / len(union)


if __name__ == "__main__":
    from loader import read_pairs, dataset_path_to_tokens_path, load_tokens

    pairs = read_pairs("pairs.csv")

    for pair in pairs[:6]:
        tokens_a = load_tokens(dataset_path_to_tokens_path(pair["file_a"]))
        tokens_b = load_tokens(dataset_path_to_tokens_path(pair["file_b"]))
        score = fingerprint_similarity(tokens_a, tokens_b)
        print(f"{pair['file_a']} vs {pair['file_b']} "
              f"| label={pair['is_plagiarized']} | winnow={score:.3f}")